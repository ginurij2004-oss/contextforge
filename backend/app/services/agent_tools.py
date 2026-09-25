from pydantic import (
    BaseModel,
    Field,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import (
    Document,
)

from app.rag.retriever import (
    retrieve_chunks,
)


# ==========================================================
# Tool Argument Validation
# ==========================================================

class SearchKnowledgeBaseArgs(
    BaseModel
):

    query: str = Field(
        min_length=1,
        max_length=2000,
    )

    document_id: int | None = None

    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
    )


# ==========================================================
# TOOL:
# List User Documents
# ==========================================================

def list_user_documents(
    db: Session,
    user_id: int,
):

    statement = (

        select(Document)

        .where(
            Document.user_id
            == user_id
        )

        .order_by(
            Document.id.desc()
        )
    )


    documents = list(

        db.scalars(
            statement
        ).all()
    )


    return {

        "documents": [

            {
                "id":
                    document.id,

                "filename":
                    document.filename,

                "status":
                    document.status,

                "indexed_chunk_size":
                    document.indexed_chunk_size,

                "indexed_chunk_overlap":
                    document.indexed_chunk_overlap,
            }

            for document
            in documents
        ]
    }


# ==========================================================
# TOOL:
# Search Knowledge Base
# ==========================================================

def search_knowledge_base(
    query: str,
    user_id: int,
    document_id: int | None,
    top_k: int,
):

    results = retrieve_chunks(

        query=query,

        user_id=user_id,

        limit=top_k,

        document_id=document_id,
    )


    return {

        "query":
            query,

        "results": [

            {
                "document_id":
                    result.get(
                        "document_id"
                    ),

                "filename":
                    result.get(
                        "filename"
                    ),

                "page":
                    result.get(
                        "page"
                    ),

                "score":
                    result.get(
                        "score"
                    ),

                "text":
                    result.get(
                        "text"
                    ),
            }

            for result
            in results
        ],
    }