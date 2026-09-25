from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AutomationAuditLog(Base):
    __tablename__ = "automation_audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    automation_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "automations.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    action_request_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "action_requests.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="info",
        server_default="info",
        index=True,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
