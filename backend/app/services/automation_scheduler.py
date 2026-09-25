from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.database import SessionLocal
from app.models.action_request import ActionRequest
from app.models.automation import Automation
from app.models.automation_run import AutomationRun
from app.schemas.automation import validate_automation_config
from app.services.automation_schedule import calculate_next_run
from app.services.automation_action_execution import execute_automation_action
from app.services.automation_audit import record_audit_event


logger = logging.getLogger(__name__)

POLL_SECONDS = 30
MAX_DUE_PER_TICK = 50

_scheduler_task: asyncio.Task | None = None
_stop_event: asyncio.Event | None = None


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def _process_one_due_automation(
    automation_id: int,
    now: datetime,
) -> None:

    db = SessionLocal()
    auto_execute_action_id: int | None = None
    auto_execute_user_id: int | None = None

    try:
        with db.begin():

            statement = (
                select(
                    Automation
                )
                .where(
                    Automation.id
                    == automation_id
                )
                .with_for_update()
            )

            automation = db.scalar(
                statement
            )

            if not automation:
                return

            if not automation.is_enabled:
                return

            if automation.trigger_type == "manual":
                return

            due_at = automation.next_run_at

            if due_at is None:
                return

            if due_at > now:
                return

            auto_execute = not automation.requires_approval

            action_payload = validate_automation_config(
                action_type=
                    automation.action_type,
                config=
                    automation.config,
            )

            action = ActionRequest(
                user_id=
                    automation.user_id,
                message_id=
                    None,
                action_type=
                    automation.action_type,
                status=
                    "approved" if auto_execute else "pending",
                title=
                    automation.name,
                payload=
                    action_payload,
                approved_at=
                    utc_now() if auto_execute else None,
            )

            db.add(
                action
            )
            db.flush()

            run = AutomationRun(
                automation_id=
                    automation.id,
                user_id=
                    automation.user_id,
                action_request_id=
                    action.id,
                status=
                    "approved" if auto_execute else "pending_approval",
                trigger_source=
                    "schedule",
                scheduled_for=
                    due_at,
                error_message=
                    None,
            )

            db.add(
                run
            )

            record_audit_event(
                db,
                user_id=automation.user_id,
                automation_id=automation.id,
                action_request_id=action.id,
                event_type="schedule.triggered",
                status="info",
                message=f"Scheduled automation '{automation.name}' triggered.",
                details={
                    "scheduled_for": due_at.isoformat(),
                    "execution_mode": (
                        "auto" if auto_execute else "approval_required"
                    ),
                },
            )

            if auto_execute:
                auto_execute_action_id = action.id
                auto_execute_user_id = automation.user_id

            automation.last_triggered_at = (
                due_at
            )

            if automation.trigger_type == "once":
                automation.next_run_at = None
                # The one-time schedule has fired. Disable it so the UI
                # clearly shows that it will not fire again.
                automation.is_enabled = False
            else:
                # Compute from "now" instead of the stale due time so an
                # app restart does not generate a backlog storm.
                automation.next_run_at = (
                    calculate_next_run(
                        automation.trigger_type,
                        automation.schedule_config,
                        after=now,
                    )
                )

        if (
            auto_execute_action_id is not None
            and auto_execute_user_id is not None
        ):
            execute_automation_action(
                action_id=auto_execute_action_id,
                user_id=auto_execute_user_id,
            )

    except Exception:
        logger.exception(
            "Scheduled automation %s failed to trigger.",
            automation_id,
        )
        db.rollback()
    finally:
        db.close()


def process_due_automations_once() -> None:

    now = utc_now()
    db = SessionLocal()

    try:
        statement = (
            select(
                Automation.id
            )
            .where(
                Automation.is_enabled
                .is_(True),
                Automation.trigger_type
                != "manual",
                Automation.next_run_at
                .is_not(None),
                Automation.next_run_at
                <= now,
            )
            .order_by(
                Automation.next_run_at.asc()
            )
            .limit(
                MAX_DUE_PER_TICK
            )
        )

        due_ids = list(
            db.scalars(
                statement
            ).all()
        )
    finally:
        db.close()

    for automation_id in due_ids:
        _process_one_due_automation(
            automation_id,
            now,
        )


async def _scheduler_loop() -> None:

    global _stop_event

    assert _stop_event is not None

    while not _stop_event.is_set():

        try:
            await asyncio.to_thread(
                process_due_automations_once
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(
                "Automation scheduler tick failed."
            )

        try:
            await asyncio.wait_for(
                _stop_event.wait(),
                timeout=POLL_SECONDS,
            )
        except asyncio.TimeoutError:
            pass


def scheduler_is_running() -> bool:
    return (
        _scheduler_task is not None
        and not _scheduler_task.done()
    )


async def start_automation_scheduler() -> None:

    global _scheduler_task
    global _stop_event

    if (
        _scheduler_task is not None
        and not _scheduler_task.done()
    ):
        return

    _stop_event = asyncio.Event()
    _scheduler_task = asyncio.create_task(
        _scheduler_loop(),
        name="contextforge-automation-scheduler",
    )


async def stop_automation_scheduler() -> None:

    global _scheduler_task
    global _stop_event

    if _stop_event is not None:
        _stop_event.set()

    if _scheduler_task is not None:
        try:
            await _scheduler_task
        except asyncio.CancelledError:
            pass

    _scheduler_task = None
    _stop_event = None
