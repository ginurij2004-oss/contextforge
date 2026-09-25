from datetime import datetime

from sqlalchemy import ForeignKey, String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIRequest(Base):
    __tablename__ = "ai_requests"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    prompt_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
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

    status: Mapped[str] = mapped_column(
        String(50),
        default="success"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )