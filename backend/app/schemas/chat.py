from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)


# ==========================================================
# Conversation
# ==========================================================

class ConversationCreate(BaseModel):
    title: str | None = None

class ConversationUpdate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=120,
    )

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )



# ==========================================================
# Source Citation
# ==========================================================

class MessageSourceResponse(BaseModel):
    document_id: int | None = None
    filename: str
    page: int | None = None
    score: float | None = None


# ==========================================================
# Agent Action Item
# ==========================================================

class MessageActionItemResponse(BaseModel):
    title: str
    description: str

    priority: Literal[
        "low",
        "medium",
        "high",
    ]


# ==========================================================
# Create Message
# ==========================================================

class MessageCreate(BaseModel):

    content: str = Field(
        min_length=1,
        max_length=10000,
    )

    mode: Literal[
        "chat",
        "documents",
        "agent",
    ] = "chat"

    document_id: int | None = Field(
        default=None,
        ge=1,
    )


# ==========================================================
# Message Response
# ==========================================================

class MessageResponse(BaseModel):
    id: int

    conversation_id: int

    role: str

    content: str

    model: str | None = None

    input_tokens: int | None = None

    output_tokens: int | None = None

    latency_ms: int | None = None

    created_at: datetime

    # ------------------------------------------------------
    # Persistent mode metadata
    # ------------------------------------------------------

    mode: Literal[
        "chat",
        "documents",
        "agent",
    ] = "chat"

    document_id: int | None = None

    confidence: Literal[
        "low",
        "medium",
        "high",
    ] | None = None

    # ------------------------------------------------------
    # RAG / Agent metadata
    # ------------------------------------------------------

    sources: list[
        MessageSourceResponse
    ] = Field(
        default_factory=list
    )

    used_tools: list[
        str
    ] = Field(
        default_factory=list
    )

    action_items: list[
        MessageActionItemResponse
    ] = Field(
        default_factory=list
    )

    model_config = ConfigDict(
        from_attributes=True
    )


# ==========================================================
# Send Message Response
# ==========================================================

class SendMessageResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse