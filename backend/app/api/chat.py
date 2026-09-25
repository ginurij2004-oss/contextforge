from fastapi import APIRouter
from pydantic import BaseModel

from app.services.llm_service import generate_response


router = APIRouter()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    result = generate_response(
        request.message
    )

    return {
        "response": result
    }