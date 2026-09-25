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


class MessageToolCall(Base):
    __tablename__ = "message_tool_calls"

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
        index=True,
    )

    tool_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )