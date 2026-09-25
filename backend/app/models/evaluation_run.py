from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    answerable_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    no_answer_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    retrieval_hit_rate: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    document_accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    page_accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    keyword_accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    no_answer_accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_top_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    average_latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    overall_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rag_score_threshold: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rag_top_k: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    rag_chunk_size: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    rag_chunk_overlap: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    label: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )