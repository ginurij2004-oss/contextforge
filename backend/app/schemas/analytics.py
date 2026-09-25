from datetime import datetime

from pydantic import BaseModel


# ==========================================================
# Overview Cards
# ==========================================================

class AnalyticsOverview(BaseModel):
    total_requests: int

    successful_requests: int

    failed_requests: int

    success_rate: float

    average_latency_ms: float

    total_input_tokens: int

    total_output_tokens: int

    total_tokens: int

    chat_requests: int

    document_requests: int

    agent_requests: int


# ==========================================================
# Daily Activity
# ==========================================================

class DailyAnalytics(BaseModel):
    date: str

    requests: int

    successful_requests: int

    failed_requests: int

    average_latency_ms: float

    input_tokens: int

    output_tokens: int


# ==========================================================
# Recent AI Request
# ==========================================================

class RecentAIRequest(BaseModel):
    id: int

    model: str

    prompt_version: str | None = None

    mode: str

    latency_ms: int | None = None

    input_tokens: int | None = None

    output_tokens: int | None = None

    total_tokens: int

    status: str

    created_at: datetime


# ==========================================================
# Evaluation Run Analytics
# ==========================================================

class AnalyticsEvaluationRun(BaseModel):
    id: int

    overall_score: float | None = None

    retrieval_hit_rate: float | None = None

    document_accuracy: float | None = None

    page_accuracy: float | None = None

    keyword_accuracy: float | None = None

    no_answer_accuracy: float | None = None

    average_latency_ms: float

    rag_score_threshold: float | None = None

    rag_top_k: int | None = None

    rag_chunk_size: int | None = None

    rag_chunk_overlap: int | None = None

    created_at: datetime


# ==========================================================
# Complete Dashboard Response
# ==========================================================

class AnalyticsDashboardResponse(BaseModel):
    overview: AnalyticsOverview

    daily_activity: list[DailyAnalytics]

    recent_requests: list[RecentAIRequest]

    evaluation_runs: list[AnalyticsEvaluationRun]