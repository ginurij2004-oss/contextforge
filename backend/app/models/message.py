from datetime import datetime

from sqlalchemy import ForeignKey, Text, String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=False,
        index=True
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    input_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    output_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )