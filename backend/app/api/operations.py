from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.core.config import settings
from app.models.action_request import ActionRequest
from app.models.automation import Automation
from app.models.automation_audit_log import AutomationAuditLog
from app.models.automation_run import AutomationRun
from app.models.user import User
from app.schemas.operations import (
    AutomationAuditLogResponse,
    OperationsHealthResponse,
    OperationsSummaryResponse,
)
from app.services.automation_scheduler import scheduler_is_running
from app.services.operations_metrics import (
    build_daily_run_series,
    calculate_success_rate,
)


router = APIRouter(
    prefix="/operations",
    tags=["Operations"],
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@router.get(
    "/summary",
    response_model=OperationsSummaryResponse,
)
def get_operations_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = current_user.id

    automations_total = db.scalar(
        select(func.count(Automation.id)).where(
            Automation.user_id == uid
        )
    ) or 0

    automations_enabled = db.scalar(
        select(func.count(Automation.id)).where(
            Automation.user_id == uid,
            Automation.is_enabled.is_(True),
        )
    ) or 0

    scheduled_automations = db.scalar(
        select(func.count(Automation.id)).where(
            Automation.user_id == uid,
            Automation.trigger_type != "manual",
        )
    ) or 0

    upcoming_runs = db.scalar(
        select(func.count(Automation.id)).where(
            Automation.user_id == uid,
            Automation.is_enabled.is_(True),
            Automation.next_run_at.is_not(None),
            Automation.next_run_at > utc_now(),
        )
    ) or 0

    runs_total = db.scalar(
        select(func.count(AutomationRun.id)).where(
            AutomationRun.user_id == uid
        )
    ) or 0

    runs_completed = db.scalar(
        select(func.count(AutomationRun.id)).where(
            AutomationRun.user_id == uid,
            AutomationRun.status == "completed",
        )
    ) or 0

    runs_failed = db.scalar(
        select(func.count(AutomationRun.id)).where(
            AutomationRun.user_id == uid,
            AutomationRun.status == "failed",
        )
    ) or 0

    runs_pending = db.scalar(
        select(func.count(AutomationRun.id)).where(
            AutomationRun.user_id == uid,
            AutomationRun.status.in_(
                ["created", "pending_approval", "approved", "executing"]
            ),
        )
    ) or 0

    pending_actions = db.scalar(
        select(func.count(ActionRequest.id)).where(
            ActionRequest.user_id == uid,
            ActionRequest.status == "pending",
        )
    ) or 0

    failed_actions = db.scalar(
        select(func.count(ActionRequest.id)).where(
            ActionRequest.user_id == uid,
            ActionRequest.status == "failed",
        )
    ) or 0

    since = utc_now() - timedelta(days=6)
    daily_rows = db.execute(
        select(
            AutomationRun.created_at,
            AutomationRun.status,
        ).where(
            AutomationRun.user_id == uid,
            AutomationRun.created_at >= since,
        )
    ).all()

    return {
        "automations_total": automations_total,
        "automations_enabled": automations_enabled,
        "scheduled_automations": scheduled_automations,
        "upcoming_runs": upcoming_runs,
        "runs_total": runs_total,
        "runs_completed": runs_completed,
        "runs_failed": runs_failed,
        "runs_pending": runs_pending,
        "success_rate": calculate_success_rate(
            runs_completed,
            runs_failed,
        ),
        "pending_actions": pending_actions,
        "failed_actions": failed_actions,
        "daily_runs": build_daily_run_series(
            [(row[0], row[1]) for row in daily_rows],
            days=7,
        ),
    }


@router.get(
    "/audit-logs",
    response_model=list[AutomationAuditLogResponse],
)
def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list(
        db.scalars(
            select(AutomationAuditLog)
            .where(
                AutomationAuditLog.user_id == current_user.id
            )
            .order_by(
                AutomationAuditLog.id.desc()
            )
            .limit(limit)
        ).all()
    )


@router.get(
    "/health",
    response_model=OperationsHealthResponse,
)
def get_operations_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Authentication is intentionally required so operational details are
    # not exposed through the public /health endpoint.
    _ = current_user.id

    database_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        database_status = "unhealthy"

    scheduler_status = (
        "running"
        if scheduler_is_running()
        else "stopped"
    )

    n8n_configured = bool(
        str(
            settings.N8N_ACTION_WEBHOOK_URL
            or ""
        ).strip()
        and str(
            settings.N8N_WEBHOOK_SECRET
            or ""
        ).strip()
    )

    overall = "healthy"
    if database_status != "healthy" or scheduler_status != "running":
        overall = "degraded"

    return {
        "status": overall,
        "database": database_status,
        "scheduler": scheduler_status,
        "n8n_configured": n8n_configured,
        "checked_at": utc_now(),
    }
