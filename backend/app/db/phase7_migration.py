from sqlalchemy import text

from app.db.database import engine


PHASE7_STATEMENTS = [
    """
    ALTER TABLE automations
    ADD COLUMN IF NOT EXISTS schedule_config JSON
    """,
    """
    ALTER TABLE automations
    ADD COLUMN IF NOT EXISTS next_run_at TIMESTAMPTZ
    """,
    """
    ALTER TABLE automations
    ADD COLUMN IF NOT EXISTS last_triggered_at TIMESTAMPTZ
    """,
    """
    ALTER TABLE automation_runs
    ADD COLUMN IF NOT EXISTS trigger_source VARCHAR(30)
    NOT NULL DEFAULT 'manual'
    """,
    """
    ALTER TABLE automation_runs
    ADD COLUMN IF NOT EXISTS scheduled_for TIMESTAMPTZ
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_automations_next_run_at
    ON automations (next_run_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_automation_runs_trigger_source
    ON automation_runs (trigger_source)
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_automation_runs_scheduled_for
    ON automation_runs (scheduled_for)
    """,
]


def ensure_phase7_schema() -> None:
    """
    Small idempotent development migration for the portfolio project.
    Existing Phase 6 data is preserved.
    """

    with engine.begin() as connection:
        for statement in PHASE7_STATEMENTS:
            connection.execute(
                text(
                    statement
                )
            )
