from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.db.base import Base


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    evaluation_run_id: Mapped[int] = mapped_column(
        ForeignKey(
            "evaluation_runs.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    question_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    expect_answer: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sources_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    retrieval_hit: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    document_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    page_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    keyword_match: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    no_answer_correct: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    top_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    latency_ms: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )