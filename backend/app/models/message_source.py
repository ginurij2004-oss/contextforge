from sqlalchemy import (
    ForeignKey,
    String,
    Integer,
    Float,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class MessageSource(Base):
    __tablename__ = "message_sources"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id"),
        nullable=False,
        index=True,
    )

    document_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    page: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )