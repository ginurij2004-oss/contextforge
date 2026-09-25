from datetime import (
    datetime,
    timezone,
)

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import (
    get_current_user,
)

from app.db.database import (
    get_db,
)

from app.models.action_request import (
    ActionRequest,
)

from app.models.automation_run import (
    AutomationRun,
)

from app.models.automation import (
    Automation,
)

from app.models.conversation import (
    Conversation,
)

from app.models.message import (
    Message,
)

from app.models.user import User

from app.schemas.action import (
    ActionCreate,
    ActionResponse,
    ActionStatus,
    ActionUpdate,
)

from app.services.automation_action_execution import (
    execute_automation_action,
)

from app.services.automation_audit import (
    get_automation_run_for_action,
    record_action_audit,
    record_audit_event,
)

from app.services.n8n_service import (
    N8NExecutionError,
    execute_n8n_action,
)


router = APIRouter(
    prefix="/actions",
    tags=["Actions"],
)


# ==========================================================
# Helpers
# ==========================================================

def utc_now() -> datetime:

    return datetime.now(
        timezone.utc
    )


def sync_automation_run(
    db: Session,
    action: ActionRequest,
    run_status: str,
    *,
    completed: bool = False,
    error_message: str | None = None,
):

    statement = (
        select(
            AutomationRun
        )
        .where(
            AutomationRun.action_request_id
            == action.id,

            AutomationRun.user_id
            == action.user_id,
        )
        .order_by(
            AutomationRun.id.desc()
        )
    )

    automation_run = db.scalar(
        statement
    )

    if not automation_run:

        return


    automation_run.status = (
        run_status
    )

    automation_run.error_message = (
        error_message
    )


    if (
        run_status == "executing"
        and automation_run.started_at
        is None
    ):

        automation_run.started_at = (
            utc_now()
        )


    if completed:

        if (
            automation_run.started_at
            is None
        ):

            automation_run.started_at = (
                utc_now()
            )

        automation_run.completed_at = (
            utc_now()
        )


def get_owned_action(
    db: Session,
    action_id: int,
    user_id: int,
) -> ActionRequest:

    statement = select(
        ActionRequest
    ).where(
        ActionRequest.id
        == action_id,

        ActionRequest.user_id
        == user_id,
    )


    action = db.scalar(
        statement
    )


    if not action:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Action not found",
        )


    return action


def validate_message_ownership(
    db: Session,
    message_id: int | None,
    user_id: int,
):

    if message_id is None:
        return


    statement = (
        select(
            Message
        )
        .join(
            Conversation,
            Conversation.id
            == Message.conversation_id,
        )
        .where(
            Message.id
            == message_id,

            Conversation.user_id
            == user_id,
        )
    )


    message = db.scalar(
        statement
    )


    if not message:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Message not found",
        )


def validate_action_payload(
    action_type: str,
    payload: dict,
):

    # ------------------------------------------------------
    # Email
    # ------------------------------------------------------

    if action_type == "email":

        required_fields = (
            "to",
            "subject",
            "body",
        )


        missing_fields = [
            field
            for field in required_fields
            if not str(
                payload.get(
                    field,
                    "",
                )
            ).strip()
        ]


        if missing_fields:

            raise HTTPException(
                status_code=
                    status.HTTP_422_UNPROCESSABLE_ENTITY,

                detail=(
                    "Email action requires: "
                    + ", ".join(
                        missing_fields
                    )
                ),
            )


        return


    # ------------------------------------------------------
    # Calendar
    # ------------------------------------------------------

    if action_type == "calendar":

        required_fields = (
            "title",
            "start_time",
            "end_time",
            "timezone",
        )


        missing_fields = [
            field
            for field in required_fields
            if not str(
                payload.get(
                    field,
                    "",
                )
            ).strip()
        ]


        if missing_fields:

            raise HTTPException(
                status_code=
                    status.HTTP_422_UNPROCESSABLE_ENTITY,

                detail=(
                    "Calendar action requires: "
                    + ", ".join(
                        missing_fields
                    )
                ),
            )


        start_time = str(
            payload.get(
                "start_time",
                "",
            )
        ).strip()

        end_time = str(
            payload.get(
                "end_time",
                "",
            )
        ).strip()

        timezone_name = str(
            payload.get(
                "timezone",
                "",
            )
        ).strip()


        try:

            parsed_start = (
                datetime.fromisoformat(
                    start_time.replace(
                        "Z",
                        "+00:00",
                    )
                )
            )

            parsed_end = (
                datetime.fromisoformat(
                    end_time.replace(
                        "Z",
                        "+00:00",
                    )
                )
            )


        except ValueError as exc:

            raise HTTPException(
                status_code=
                    status.HTTP_422_UNPROCESSABLE_ENTITY,

                detail=(
                    "Calendar start_time and end_time "
                    "must be valid ISO 8601 date-times."
                ),
            ) from exc


        if (
            parsed_start.utcoffset()
            is None
            or parsed_end.utcoffset()
            is None
        ):

            raise HTTPException(
                status_code=
                    status.HTTP_422_UNPROCESSABLE_ENTITY,

                detail=(
                    "Calendar start_time and end_time "
                    "must include a UTC offset."
                ),
            )


        if parsed_end <= parsed_start:

            raise HTTPException(
                status_code=
                    status.HTTP_422_UNPROCESSABLE_ENTITY,

                detail=(
                    "Calendar end_time must be after "
                    "start_time."
                ),
            )


        if "/" not in timezone_name and timezone_name != "UTC":

            raise HTTPException(
                status_code=
                    status.HTTP_422_UNPROCESSABLE_ENTITY,

                detail=(
                    "Calendar timezone must use an IANA "
                    "name such as Asia/Colombo or UTC."
                ),
            )


        return


    # ------------------------------------------------------
    # Generic Webhook
    #
    # Security boundary:
    # - only the fixed, allowlisted demo target is accepted
    # - arbitrary URLs are never accepted from the model/user
    # - payload data must be a JSON object
    # ------------------------------------------------------

    if action_type == "webhook":

        target = str(
            payload.get(
                "target",
                "",
            )
        ).strip()

        data = payload.get(
            "data"
        )


        if target != "demo_echo":

            raise HTTPException(
                status_code=
                    status.HTTP_422_UNPROCESSABLE_ENTITY,

                detail=(
                    "Webhook target must be the approved "
                    "target: demo_echo"
                ),
            )


        if not isinstance(
            data,
            dict,
        ):

            raise HTTPException(
                status_code=
                    status.HTTP_422_UNPROCESSABLE_ENTITY,

                detail=(
                    "Webhook action requires data to be "
                    "a JSON object."
                ),
            )


        return


    # ------------------------------------------------------
    # Other action types remain reserved for future phases.
    # ------------------------------------------------------

    return



def ensure_pending(
    action: ActionRequest,
):

    if action.status != "pending":

        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,

            detail=(
                "Only pending actions "
                "can be changed"
            ),
        )


def ensure_approved_for_execution(
    action: ActionRequest,
):

    if action.status != "approved":

        raise HTTPException(
            status_code=
                status.HTTP_409_CONFLICT,

            detail=(
                "Only approved actions "
                "can be executed"
            ),
        )


def ensure_supported_execution_type(
    action: ActionRequest,
):

    if action.action_type not in {
        "email",
        "calendar",
        "webhook",
    }:

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=(
                "Execution is currently supported "
                "for email, calendar and webhook actions"
            ),
        )


# ==========================================================
# Create Pending Action
# ==========================================================

@router.post(
    "",
    response_model=
        ActionResponse,
    status_code=
        status.HTTP_201_CREATED,
)
def create_action(
    data: ActionCreate,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    validate_message_ownership(
        db=
            db,

        message_id=
            data.message_id,

        user_id=
            current_user.id,
    )


    validate_action_payload(
        action_type=
            data.action_type,

        payload=
            data.payload,
    )


    action = ActionRequest(

        user_id=
            current_user.id,

        message_id=
            data.message_id,

        action_type=
            data.action_type,

        status=
            "pending",

        title=
            data.title,

        payload=
            data.payload,
    )


    db.add(
        action
    )

    db.commit()

    db.refresh(
        action
    )


    return action


# ==========================================================
# List Current User Actions
# ==========================================================

@router.get(
    "",
    response_model=
        list[ActionResponse],
)
def list_actions(
    status_filter:
        ActionStatus | None = Query(
            default=None,
            alias="status",
        ),

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    statement = (
        select(
            ActionRequest
        )
        .where(
            ActionRequest.user_id
            == current_user.id
        )
        .order_by(
            ActionRequest.id.desc()
        )
    )


    if status_filter is not None:

        statement = statement.where(
            ActionRequest.status
            == status_filter
        )


    return list(
        db.scalars(
            statement
        ).all()
    )


# ==========================================================
# Get One Action
# ==========================================================

@router.get(
    "/{action_id}",
    response_model=
        ActionResponse,
)
def get_action(
    action_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    return get_owned_action(
        db=
            db,

        action_id=
            action_id,

        user_id=
            current_user.id,
    )


# ==========================================================
# Edit Pending Action
# ==========================================================

@router.patch(
    "/{action_id}",
    response_model=
        ActionResponse,
)
def update_action(
    action_id: int,
    data: ActionUpdate,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    action = get_owned_action(
        db=
            db,

        action_id=
            action_id,

        user_id=
            current_user.id,
    )


    ensure_pending(
        action
    )


    if data.title is not None:

        action.title = (
            data.title
        )


    if data.payload is not None:

        validate_action_payload(
            action_type=
                action.action_type,

            payload=
                data.payload,
        )

        action.payload = (
            data.payload
        )


    db.commit()

    db.refresh(
        action
    )


    return action


# ==========================================================
# Approve Pending Action
#
# IMPORTANT:
# Phase 1 approval does NOT execute/send anything.
# It only records human approval.
# ==========================================================

@router.post(
    "/{action_id}/approve",
    response_model=
        ActionResponse,
)
def approve_action(
    action_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    action = get_owned_action(
        db=
            db,

        action_id=
            action_id,

        user_id=
            current_user.id,
    )


    ensure_pending(
        action
    )


    action.status = (
        "approved"
    )

    action.approved_at = (
        utc_now()
    )

    action.error_message = (
        None
    )


    sync_automation_run(
        db,
        action,
        "approved",
        error_message=None,
    )

    record_action_audit(
        db,
        action=action,
        event_type="action.approved",
        status="success",
        message=f"Action '{action.title}' was approved.",
    )


    db.commit()

    db.refresh(
        action
    )


    return action


# ==========================================================
# Reject Pending Action
# ==========================================================

@router.post(
    "/{action_id}/reject",
    response_model=
        ActionResponse,
)
def reject_action(
    action_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    action = get_owned_action(
        db=
            db,

        action_id=
            action_id,

        user_id=
            current_user.id,
    )


    ensure_pending(
        action
    )


    action.status = (
        "rejected"
    )

    action.rejected_at = (
        utc_now()
    )


    sync_automation_run(
        db,
        action,
        "rejected",
        completed=True,
        error_message=None,
    )

    record_action_audit(
        db,
        action=action,
        event_type="action.rejected",
        status="warning",
        message=f"Action '{action.title}' was rejected.",
    )


    db.commit()

    db.refresh(
        action
    )


    return action

# ==========================================================
# Execute Approved Action
#
# Human approval and execution are deliberately separate.
#
# pending -> approved -> executing -> completed / failed
#
# Phase 5 n8n execution:
# ContextForge -> n8n webhook -> action router
# -> Gmail / Google Calendar / allowlisted webhook -> result
# ==========================================================

@router.post(
    "/{action_id}/execute",
    response_model=
        ActionResponse,
)
def execute_action(
    action_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    # ------------------------------------------------------
    # 1. Ownership
    # ------------------------------------------------------

    action = get_owned_action(
        db=
            db,

        action_id=
            action_id,

        user_id=
            current_user.id,
    )


    # ------------------------------------------------------
    # 2. Explicit human approval is mandatory
    # ------------------------------------------------------

    ensure_approved_for_execution(
        action
    )


    # ------------------------------------------------------
    # 3. Phase 5 executes email + calendar + webhook through n8n
    # ------------------------------------------------------

    ensure_supported_execution_type(
        action
    )


    validate_action_payload(
        action_type=
            action.action_type,

        payload=
            action.payload,
    )


    # ------------------------------------------------------
    # 4. Record execution start BEFORE external side effect
    # ------------------------------------------------------

    action.status = (
        "executing"
    )

    action.error_message = (
        None
    )


    sync_automation_run(
        db,
        action,
        "executing",
        error_message=None,
    )

    record_action_audit(
        db,
        action=action,
        event_type="action.execution_started",
        status="info",
        message=f"Execution started for '{action.title}'.",
    )


    db.commit()

    db.refresh(
        action
    )


    # ------------------------------------------------------
    # 5. Execute through self-hosted n8n
    # ------------------------------------------------------

    try:

        result = execute_n8n_action(
            action_id=action.id,
            action_type=action.action_type,
            user_id=current_user.id,
            payload=action.payload,
        )


        # n8n should return success=true.
        # Any other result is treated as a safe failure.
        if not result.get("success", False):

            raise N8NExecutionError(
                result.get(
                    "message",
                    "n8n reported that the action failed.",
                )
            )


    except N8NExecutionError as exc:

        action.status = (
            "failed"
        )

        action.error_message = (
            str(exc)
        )

        action.executed_at = (
            utc_now()
        )


        sync_automation_run(
            db,
            action,
            "failed",
            completed=True,
            error_message=str(exc),
        )

        record_action_audit(
            db,
            action=action,
            event_type="action.execution_failed",
            status="failed",
            message=f"Execution failed for '{action.title}'.",
            details={"error": str(exc)},
        )


        db.commit()

        db.refresh(
            action
        )


        return action


    except Exception:

        # Never expose raw unexpected exception details.
        action.status = (
            "failed"
        )

        action.error_message = (
            "Unexpected automation execution failure."
        )

        action.executed_at = (
            utc_now()
        )


        sync_automation_run(
            db,
            action,
            "failed",
            completed=True,
            error_message=(
                "Unexpected automation execution failure."
            ),
        )

        record_action_audit(
            db,
            action=action,
            event_type="action.execution_failed",
            status="failed",
            message=f"Execution failed for '{action.title}'.",
            details={
                "error": "Unexpected automation execution failure."
            },
        )


        db.commit()

        db.refresh(
            action
        )


        return action


    # ------------------------------------------------------
    # 6. Success
    # ------------------------------------------------------

    action.status = (
        "completed"
    )

    action.error_message = (
        None
    )

    action.executed_at = (
        utc_now()
    )


    sync_automation_run(
        db,
        action,
        "completed",
        completed=True,
        error_message=None,
    )

    record_action_audit(
        db,
        action=action,
        event_type="action.execution_completed",
        status="success",
        message=f"Execution completed for '{action.title}'.",
    )


    db.commit()

    db.refresh(
        action
    )


    return action

# ==========================================================
# Retry Failed Action
#
# A retry always creates a NEW ActionRequest instead of
# mutating execution history. If the failed action came from
# an automation, that automation's approval mode is preserved.
# Standalone actions return to pending approval.
# ==========================================================

@router.post(
    "/{action_id}/retry",
    response_model=ActionResponse,
    status_code=status.HTTP_201_CREATED,
)
def retry_failed_action(
    action_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    original = get_owned_action(
        db=db,
        action_id=action_id,
        user_id=current_user.id,
    )

    if original.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only failed actions can be retried.",
        )

    validate_action_payload(
        action_type=original.action_type,
        payload=original.payload,
    )

    original_run = get_automation_run_for_action(
        db,
        original,
    )

    automation = None
    if original_run is not None:
        automation = db.scalar(
            select(Automation).where(
                Automation.id == original_run.automation_id,
                Automation.user_id == current_user.id,
            )
        )

    auto_execute = bool(
        automation is not None
        and automation.requires_approval is False
    )

    retry_action = ActionRequest(
        user_id=current_user.id,
        message_id=original.message_id,
        action_type=original.action_type,
        status="approved" if auto_execute else "pending",
        title=f"Retry: {original.title}"[:255],
        payload=dict(original.payload),
        approved_at=utc_now() if auto_execute else None,
    )

    db.add(retry_action)
    db.flush()

    if automation is not None:
        retry_run = AutomationRun(
            automation_id=automation.id,
            user_id=current_user.id,
            action_request_id=retry_action.id,
            status=(
                "approved"
                if auto_execute
                else "pending_approval"
            ),
            trigger_source="retry",
            scheduled_for=None,
            error_message=None,
        )
        db.add(retry_run)

        record_audit_event(
            db,
            user_id=current_user.id,
            automation_id=automation.id,
            action_request_id=retry_action.id,
            event_type="action.retry_created",
            status="info",
            message=f"Retry created for failed action #{original.id}.",
            details={
                "original_action_id": original.id,
                "execution_mode": (
                    "auto" if auto_execute else "approval_required"
                ),
            },
        )

    db.commit()

    if auto_execute:
        execute_automation_action(
            action_id=retry_action.id,
            user_id=current_user.id,
        )
        db.expire_all()

    return get_owned_action(
        db=db,
        action_id=retry_action.id,
        user_id=current_user.id,
    )

