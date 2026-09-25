from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.database import get_db
from app.models.action_request import ActionRequest
from app.models.automation import Automation
from app.models.automation_run import AutomationRun
from app.models.user import User
from app.schemas.automation import (
    AutomationCreate,
    AutomationResponse,
    AutomationRunResponse,
    AutomationUpdate,
    validate_automation_config,
    validate_schedule_config,
)
from app.services.automation_schedule import calculate_next_run
from app.services.automation_action_execution import execute_automation_action
from app.services.automation_audit import record_audit_event


router = APIRouter(
    prefix="/automations",
    tags=["Automations"],
)


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def get_owned_automation(
    db: Session,
    automation_id: int,
    user_id: int,
) -> Automation:

    automation = db.scalar(
        select(
            Automation
        ).where(
            Automation.id
            == automation_id,
            Automation.user_id
            == user_id,
        )
    )

    if not automation:
        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,
            detail=
                "Automation not found",
        )

    return automation


def serialize_automation(
    automation: Automation,
) -> dict:

    return {
        "id": automation.id,
        "user_id": automation.user_id,
        "name": automation.name,
        "description": automation.description,
        "trigger_type": automation.trigger_type,
        "schedule": automation.schedule_config,
        "action_type": automation.action_type,
        "config": automation.config,
        "is_enabled": automation.is_enabled,
        "requires_approval": automation.requires_approval,
        "next_run_at": automation.next_run_at,
        "last_triggered_at": automation.last_triggered_at,
        "created_at": automation.created_at,
        "updated_at": automation.updated_at,
    }


def serialize_run(
    run: AutomationRun,
    automation: Automation,
) -> dict:

    return {
        "id": run.id,
        "automation_id": run.automation_id,
        "automation_name": automation.name,
        "user_id": run.user_id,
        "action_request_id": run.action_request_id,
        "action_type": automation.action_type,
        "status": run.status,
        "trigger_source": run.trigger_source,
        "scheduled_for": run.scheduled_for,
        "error_message": run.error_message,
        "created_at": run.created_at,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }


def calculate_saved_next_run(
    trigger_type: str,
    schedule: dict | None,
) -> datetime | None:

    next_run = calculate_next_run(
        trigger_type,
        schedule,
        after=utc_now(),
    )

    if (
        trigger_type == "once"
        and next_run is None
    ):
        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "One-time automation run_at must be in the future."
            ),
        )

    return next_run


# ==========================================================
# Create
# ==========================================================

@router.post(
    "",
    response_model=AutomationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_automation(
    data: AutomationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    next_run_at = calculate_saved_next_run(
        data.trigger_type,
        data.schedule,
    )

    automation = Automation(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
        trigger_type=data.trigger_type,
        action_type=data.action_type,
        config=data.config,
        schedule_config=data.schedule,
        next_run_at=next_run_at,
        last_triggered_at=None,
        is_enabled=data.is_enabled,
        requires_approval=data.requires_approval,
    )

    db.add(
        automation
    )
    db.flush()

    record_audit_event(
        db,
        user_id=current_user.id,
        automation_id=automation.id,
        event_type="automation.created",
        status="success",
        message=f"Automation '{automation.name}' was created.",
        details={
            "trigger_type": automation.trigger_type,
            "action_type": automation.action_type,
            "requires_approval": automation.requires_approval,
        },
    )

    db.commit()
    db.refresh(
        automation
    )

    return serialize_automation(
        automation
    )


# ==========================================================
# List
# ==========================================================

@router.get(
    "",
    response_model=list[AutomationResponse],
)
def list_automations(
    enabled: bool | None = Query(
        default=None,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    statement = (
        select(
            Automation
        )
        .where(
            Automation.user_id
            == current_user.id
        )
        .order_by(
            Automation.id.desc()
        )
    )

    if enabled is not None:
        statement = statement.where(
            Automation.is_enabled
            == enabled
        )

    automations = list(
        db.scalars(
            statement
        ).all()
    )

    return [
        serialize_automation(
            automation
        )
        for automation in automations
    ]


# ==========================================================
# Recent Run History
# Keep static route before /{automation_id}
# ==========================================================

@router.get(
    "/runs",
    response_model=list[AutomationRunResponse],
)
def list_automation_runs(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    rows = db.execute(
        select(
            AutomationRun,
            Automation,
        )
        .join(
            Automation,
            Automation.id
            == AutomationRun.automation_id,
        )
        .where(
            AutomationRun.user_id
            == current_user.id
        )
        .order_by(
            AutomationRun.id.desc()
        )
        .limit(
            limit
        )
    ).all()

    return [
        serialize_run(
            run,
            automation,
        )
        for run, automation in rows
    ]


# ==========================================================
# Upcoming schedules
# ==========================================================

@router.get(
    "/upcoming",
    response_model=list[AutomationResponse],
)
def list_upcoming_automations(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    automations = list(
        db.scalars(
            select(
                Automation
            )
            .where(
                Automation.user_id
                == current_user.id,
                Automation.is_enabled
                .is_(True),
                Automation.trigger_type
                != "manual",
                Automation.next_run_at
                .is_not(None),
            )
            .order_by(
                Automation.next_run_at.asc()
            )
            .limit(
                limit
            )
        ).all()
    )

    return [
        serialize_automation(
            automation
        )
        for automation in automations
    ]


# ==========================================================
# Get One
# ==========================================================

@router.get(
    "/{automation_id}",
    response_model=AutomationResponse,
)
def get_automation(
    automation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return serialize_automation(
        get_owned_automation(
            db=db,
            automation_id=automation_id,
            user_id=current_user.id,
        )
    )


# ==========================================================
# Update
# ==========================================================

@router.patch(
    "/{automation_id}",
    response_model=AutomationResponse,
)
def update_automation(
    automation_id: int,
    data: AutomationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    automation = get_owned_automation(
        db=db,
        automation_id=automation_id,
        user_id=current_user.id,
    )

    fields = data.model_fields_set

    if data.name is not None:
        automation.name = data.name

    if "description" in fields:
        automation.description = data.description

    if data.config is not None:
        automation.config = validate_automation_config(
            action_type=automation.action_type,
            config=data.config,
        )

    effective_trigger = (
        data.trigger_type
        if data.trigger_type is not None
        else automation.trigger_type
    )

    effective_schedule = (
        data.schedule
        if "schedule" in fields
        else automation.schedule_config
    )

    schedule_changed = (
        data.trigger_type is not None
        or "schedule" in fields
    )

    if schedule_changed:
        cleaned_schedule = validate_schedule_config(
            trigger_type=effective_trigger,
            schedule=effective_schedule,
        )

        automation.trigger_type = effective_trigger
        automation.schedule_config = cleaned_schedule
        automation.next_run_at = calculate_saved_next_run(
            effective_trigger,
            cleaned_schedule,
        )

    if data.is_enabled is not None:
        automation.is_enabled = data.is_enabled

        if (
            data.is_enabled
            and automation.trigger_type != "manual"
            and automation.next_run_at is None
            and automation.schedule_config is not None
        ):
            automation.next_run_at = calculate_saved_next_run(
                automation.trigger_type,
                automation.schedule_config,
            )

    if data.requires_approval is not None:
        automation.requires_approval = data.requires_approval

    record_audit_event(
        db,
        user_id=current_user.id,
        automation_id=automation.id,
        event_type="automation.updated",
        status="success",
        message=f"Automation '{automation.name}' was updated.",
        details={
            "changed_fields": sorted(fields),
            "enabled": automation.is_enabled,
            "requires_approval": automation.requires_approval,
        },
    )

    db.commit()
    db.refresh(
        automation
    )

    return serialize_automation(
        automation
    )


# ==========================================================
# Run Now -> create an ActionRequest.
# Approval-required automations stop at pending.
# Auto-execute automations continue through n8n immediately.
# Saved schedule timing is not changed.
# ==========================================================

@router.post(
    "/{automation_id}/run",
    response_model=AutomationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_automation(
    automation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    automation = get_owned_automation(
        db=db,
        automation_id=automation_id,
        user_id=current_user.id,
    )

    if not automation.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Automation is disabled",
        )

    action_payload = validate_automation_config(
        action_type=automation.action_type,
        config=automation.config,
    )

    auto_execute = not automation.requires_approval

    action = ActionRequest(
        user_id=current_user.id,
        message_id=None,
        action_type=automation.action_type,
        status="approved" if auto_execute else "pending",
        title=automation.name,
        payload=action_payload,
        approved_at=utc_now() if auto_execute else None,
    )

    db.add(
        action
    )
    db.flush()

    automation_run = AutomationRun(
        automation_id=automation.id,
        user_id=current_user.id,
        action_request_id=action.id,
        status="approved" if auto_execute else "pending_approval",
        trigger_source="manual",
        scheduled_for=None,
        error_message=None,
    )

    db.add(
        automation_run
    )

    record_audit_event(
        db,
        user_id=current_user.id,
        automation_id=automation.id,
        action_request_id=action.id,
        event_type="automation.run_now",
        status="info",
        message=f"Manual run created for '{automation.name}'.",
        details={
            "execution_mode": (
                "auto" if auto_execute else "approval_required"
            ),
        },
    )

    db.commit()
    db.refresh(automation_run)

    if auto_execute:
        execute_automation_action(
            action_id=action.id,
            user_id=current_user.id,
        )
        db.refresh(automation_run)

    return serialize_run(
        automation_run,
        automation,
    )


# ==========================================================
# Runs For One Automation
# ==========================================================

@router.get(
    "/{automation_id}/runs",
    response_model=list[AutomationRunResponse],
)
def list_runs_for_automation(
    automation_id: int,
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    automation = get_owned_automation(
        db=db,
        automation_id=automation_id,
        user_id=current_user.id,
    )

    runs = list(
        db.scalars(
            select(
                AutomationRun
            )
            .where(
                AutomationRun.automation_id
                == automation.id,
                AutomationRun.user_id
                == current_user.id,
            )
            .order_by(
                AutomationRun.id.desc()
            )
            .limit(
                limit
            )
        ).all()
    )

    return [
        serialize_run(
            run,
            automation,
        )
        for run in runs
    ]


# ==========================================================
# Delete
# ==========================================================

@router.delete(
    "/{automation_id}",
    status_code=status.HTTP_200_OK,
)
def delete_automation(
    automation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    automation = get_owned_automation(
        db=db,
        automation_id=automation_id,
        user_id=current_user.id,
    )

    record_audit_event(
        db,
        user_id=current_user.id,
        automation_id=automation.id,
        event_type="automation.deleted",
        status="success",
        message=f"Automation '{automation.name}' was deleted.",
        details={
            "action_type": automation.action_type,
            "trigger_type": automation.trigger_type,
        },
    )

    db.delete(
        automation
    )
    db.commit()

    return {
        "message": "Automation deleted successfully",
        "automation_id": automation_id,
    }
