from pydantic import (
    BaseModel,
    Field,
)


class RAGExperimentRequest(
    BaseModel
):

    label: str | None = Field(
        default=None,
        max_length=100,
    )

    document_id: int = Field(
        ge=1,
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    score_threshold: float = Field(
        default=0.45,
        ge=0.0,
        le=1.0,
    )