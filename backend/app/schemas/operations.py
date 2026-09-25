from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OperationsDailyPoint(BaseModel):
    date: str
    completed: int
    failed: int
    other: int


class OperationsSummaryResponse(BaseModel):
    automations_total: int
    automations_enabled: int
    scheduled_automations: int
    upcoming_runs: int
    runs_total: int
    runs_completed: int
    runs_failed: int
    runs_pending: int
    success_rate: float
    pending_actions: int
    failed_actions: int
    daily_runs: list[OperationsDailyPoint]


class AutomationAuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    automation_id: int | None
    action_request_id: int | None
    event_type: str
    status: str
    message: str
    details: dict
    created_at: datetime


class OperationsHealthResponse(BaseModel):
    status: str
    database: str
    scheduler: str
    n8n_configured: bool
    checked_at: datetime
