from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class MessageMetadata(Base):
    __tablename__ = "message_metadata"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    message_id: Mapped[int] = mapped_column(
        ForeignKey(
            "messages.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="chat",
    )

    # We intentionally don't make this a FK.
    # Chat history can survive even if a
    # document is later deleted.
    document_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    confidence: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )