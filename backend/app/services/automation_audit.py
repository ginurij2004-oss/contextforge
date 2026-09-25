from __future__ import annotations

from sqlalchemy import select

from app.models.action_request import ActionRequest
from app.models.automation_audit_log import AutomationAuditLog
from app.models.automation_run import AutomationRun


def get_automation_run_for_action(
    db,
    action: ActionRequest,
) -> AutomationRun | None:
    return db.scalar(
        select(AutomationRun)
        .where(
            AutomationRun.action_request_id == action.id,
            AutomationRun.user_id == action.user_id,
        )
        .order_by(AutomationRun.id.desc())
    )


def record_audit_event(
    db,
    *,
    user_id: int,
    event_type: str,
    message: str,
    status: str = "info",
    automation_id: int | None = None,
    action_request_id: int | None = None,
    details: dict | None = None,
) -> AutomationAuditLog:
    event = AutomationAuditLog(
        user_id=user_id,
        automation_id=automation_id,
        action_request_id=action_request_id,
        event_type=event_type,
        status=status,
        message=message,
        details=details or {},
    )
    db.add(event)
    return event


def record_action_audit(
    db,
    *,
    action: ActionRequest,
    event_type: str,
    message: str,
    status: str = "info",
    details: dict | None = None,
) -> AutomationAuditLog | None:
    run = get_automation_run_for_action(
        db,
        action,
    )

    if run is None:
        return None

    return record_audit_event(
        db,
        user_id=action.user_id,
        automation_id=run.automation_id,
        action_request_id=action.id,
        event_type=event_type,
        status=status,
        message=message,
        details=details,
    )
