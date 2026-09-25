from fastapi import APIRouter, Depends

from app.api.auth import get_current_user
from app.models.user import User

from app.schemas.rag import (
    SearchRequest,
    SearchResult,
    RAGAnswerResponse,
)

from app.rag.retriever import retrieve_chunks
from app.rag.pipeline import generate_rag_answer

router = APIRouter(
    prefix="/rag",
    tags=["RAG"],
)


@router.post(
    "/search",
    response_model=list[SearchResult],
)
def semantic_search(
    data: SearchRequest,
    current_user: User = Depends(get_current_user),
):
    return retrieve_chunks(
        query=data.query,
        user_id=current_user.id,
        limit=5,
    )

@router.post(
    "/ask",
    response_model=RAGAnswerResponse,
)
def ask_documents(
    data: SearchRequest,
    current_user: User = Depends(
        get_current_user
    ),
):

    return generate_rag_answer(
        question=data.query,
        user_id=current_user.id,
    )