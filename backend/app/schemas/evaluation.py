from datetime import datetime

from pydantic import BaseModel


class EvaluationCaseResult(BaseModel):
    id: str

    question: str

    expect_answer: bool

    answer: str

    sources_count: int

    retrieval_hit: bool

    document_correct: bool | None = None

    page_correct: bool | None = None

    keyword_match: float | None = None

    no_answer_correct: bool | None = None

    top_score: float | None = None

    latency_ms: int


class EvaluationSummary(BaseModel):
    run_id: int | None = None

    total_questions: int

    answerable_questions: int

    no_answer_questions: int

    retrieval_hit_rate: float | None = None

    document_accuracy: float | None = None

    page_accuracy: float | None = None

    keyword_accuracy: float | None = None

    no_answer_accuracy: float | None = None

    average_top_score: float | None = None

    average_latency_ms: float

    overall_score: float | None = None

    results: list[EvaluationCaseResult]


class EvaluationRunListItem(BaseModel):
    id: int

    total_questions: int

    retrieval_hit_rate: float | None = None

    document_accuracy: float | None = None

    page_accuracy: float | None = None

    keyword_accuracy: float | None = None

    no_answer_accuracy: float | None = None

    overall_score: float | None = None

    average_latency_ms: float

    rag_score_threshold: float | None = None

    rag_top_k: int | None = None

    rag_chunk_size: int | None = None

    rag_chunk_overlap: int | None = None

    label: str | None = None

    created_at: datetime