from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


# ==========================================================
# Re-index Request
# ==========================================================

class ReindexDocumentRequest(
    BaseModel
):

    chunk_size: int = Field(
        default=2500,
        ge=500,
        le=8000,
    )

    chunk_overlap: int = Field(
        default=300,
        ge=0,
        le=2000,
    )


    @model_validator(
        mode="after"
    )
    def validate_chunk_settings(
        self,
    ):

        if (
            self.chunk_overlap
            >= self.chunk_size
        ):

            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )


        return self


# ==========================================================
# Re-index Response
# ==========================================================

class ReindexDocumentResponse(
    BaseModel
):

    document_id: int

    filename: str

    status: str

    pages: int

    chunks: int

    chunk_size: int

    chunk_overlap: int