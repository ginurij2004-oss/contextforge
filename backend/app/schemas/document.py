from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
)


# ==========================================================
# Document Upload Response
# ==========================================================

class DocumentUploadResponse(BaseModel):
    document_id: int
    filename: str
    status: str
    pages: int
    chunks: int


# ==========================================================
# Document List / Detail Response
# ==========================================================

class DocumentResponse(BaseModel):
    id: int
    user_id: int
    filename: str
    file_type: str
    status: str

    indexed_chunk_size: int | None = None
    indexed_chunk_overlap: int | None = None
    indexed_at: datetime | None = None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )