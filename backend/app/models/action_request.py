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

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class ActionRequest(Base):

    __tablename__ = "action_requests"


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


    message_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "messages.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )


    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )


    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
    )


    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )


    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )


    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
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


    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    rejected_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


    executed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
