from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class Automation(Base):

    __tablename__ = "automations"

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

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    trigger_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
        server_default="manual",
        index=True,
    )

    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Phase 7 schedule settings are stored separately from
    # the external action payload so scheduled actions never
    # leak scheduler metadata to n8n/Gmail/Calendar/Webhook.
    schedule_config: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True,
    )

    requires_approval: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
