from typing import (
    Annotated,
    Literal,
)

from pydantic import (
    BaseModel,
    Field,
)


# ==========================================================
# Agent Request
# ==========================================================

class AgentRequest(BaseModel):

    message: str = Field(
        min_length=1,
        max_length=10000,
    )

    document_id: int | None = Field(
        default=None,
        ge=1,
    )


# ==========================================================
# Source
# ==========================================================

class AgentSource(BaseModel):

    document_id: int | None = None

    filename: str

    page: int | None = None

    score: float | None = None


# ==========================================================
# Informational Action Item
#
# These are recommendations/tasks shown in the chat.
# They do NOT represent executable external actions.
# ==========================================================

class AgentActionItem(BaseModel):

    title: str

    description: str

    priority: Literal[
        "low",
        "medium",
        "high",
    ]


# ==========================================================
# Proposed Executable Actions
#
# Phase 5 supports:
# - email
# - calendar
# - webhook
#
# These are drafts only. The backend stores them as PENDING
# ActionRequest rows. Nothing is executed here.
# ==========================================================

class AgentEmailPayload(BaseModel):

    to: str = Field(
        min_length=1,
        max_length=320,
    )

    subject: str = Field(
        min_length=1,
        max_length=500,
    )

    body: str = Field(
        min_length=1,
        max_length=20000,
    )


class AgentCalendarPayload(BaseModel):

    title: str = Field(
        min_length=1,
        max_length=500,
    )

    start_time: str = Field(
        min_length=1,
        max_length=100,
    )

    end_time: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str = Field(
        default="",
        max_length=20000,
    )

    timezone: str = Field(
        min_length=1,
        max_length=100,
    )


class AgentWebhookPayload(BaseModel):

    target: Literal[
        "demo_echo",
    ]

    data_json: str = Field(
        min_length=2,
        max_length=20000,
    )


class AgentEmailProposedAction(BaseModel):

    action_type: Literal[
        "email",
    ]

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    payload: AgentEmailPayload


class AgentCalendarProposedAction(BaseModel):

    action_type: Literal[
        "calendar",
    ]

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    payload: AgentCalendarPayload


class AgentWebhookProposedAction(BaseModel):

    action_type: Literal[
        "webhook",
    ]

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    payload: AgentWebhookPayload


AgentProposedAction = Annotated[
    AgentEmailProposedAction
    | AgentCalendarProposedAction
    | AgentWebhookProposedAction,
    Field(
        discriminator="action_type"
    ),
]


# ==========================================================
# Agent Response
# ==========================================================

class AgentResponse(BaseModel):

    answer: str

    used_tools: list[str]

    sources: list[
        AgentSource
    ]

    action_items: list[
        AgentActionItem
    ]

    proposed_actions: list[
        AgentProposedAction
    ] = Field(
        default_factory=list
    )

    confidence: Literal[
        "low",
        "medium",
        "high",
    ]
