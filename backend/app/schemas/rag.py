from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=2000
    )


class SearchResult(BaseModel):
    score: float
    filename: str | None
    page: int | None
    text: str | None


class SourceItem(BaseModel):
    filename: str | None
    page: int | None
    score: float


class RAGAnswerResponse(BaseModel):
    answer: str
    sources: list[SourceItem]