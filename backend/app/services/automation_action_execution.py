from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.action_request import ActionRequest
from app.models.automation_run import AutomationRun
from app.services.automation_audit import record_action_audit
from app.services.n8n_service import (
    N8NExecutionError,
    execute_n8n_action,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_run(
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


def execute_automation_action(
    action_id: int,
    user_id: int,
) -> str:
    """
    Execute an automation-created ActionRequest that is already approved.

    This is used only when the saved automation has requires_approval=False.
    The same n8n execution layer used by Action Center is preserved.

    Returns the final action status: completed or failed.
    """

    db = SessionLocal()

    try:
        action = db.scalar(
            select(ActionRequest).where(
                ActionRequest.id == action_id,
                ActionRequest.user_id == user_id,
            )
        )

        if not action:
            return "failed"

        if action.status != "approved":
            return action.status

        run = _get_run(db, action)

        action.status = "executing"
        action.error_message = None

        if run:
            run.status = "executing"
            run.error_message = None
            if run.started_at is None:
                run.started_at = utc_now()

        record_action_audit(
            db,
            action=action,
            event_type="action.execution_started",
            status="info",
            message=f"Execution started for '{action.title}'.",
        )

        db.commit()
        db.refresh(action)

        try:
            result = execute_n8n_action(
                action_id=action.id,
                action_type=action.action_type,
                user_id=action.user_id,
                payload=action.payload,
            )

            if not result.get("success", False):
                raise N8NExecutionError(
                    result.get(
                        "message",
                        "n8n reported that the action failed.",
                    )
                )

        except N8NExecutionError as exc:
            action.status = "failed"
            action.error_message = str(exc)
            action.executed_at = utc_now()

            if run:
                run.status = "failed"
                run.error_message = str(exc)
                if run.started_at is None:
                    run.started_at = utc_now()
                run.completed_at = utc_now()

            record_action_audit(
                db,
                action=action,
                event_type="action.execution_failed",
                status="failed",
                message=f"Execution failed for '{action.title}'.",
                details={"error": str(exc)},
            )

            db.commit()
            return "failed"

        except Exception:
            message = "Unexpected automation execution failure."

            action.status = "failed"
            action.error_message = message
            action.executed_at = utc_now()

            if run:
                run.status = "failed"
                run.error_message = message
                if run.started_at is None:
                    run.started_at = utc_now()
                run.completed_at = utc_now()

            record_action_audit(
                db,
                action=action,
                event_type="action.execution_failed",
                status="failed",
                message=f"Execution failed for '{action.title}'.",
                details={"error": message},
            )

            db.commit()
            return "failed"

        action.status = "completed"
        action.error_message = None
        action.executed_at = utc_now()

        if run:
            run.status = "completed"
            run.error_message = None
            if run.started_at is None:
                run.started_at = utc_now()
            run.completed_at = utc_now()

        record_action_audit(
            db,
            action=action,
            event_type="action.execution_completed",
            status="success",
            message=f"Execution completed for '{action.title}'.",
        )

        db.commit()
        return "completed"

    finally:
        db.close()
