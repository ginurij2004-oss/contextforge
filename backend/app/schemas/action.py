from datetime import datetime
from typing import (
    Any,
    Literal,
)

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


ActionType = Literal[
    "email",
    "calendar",
    "reminder",
    "webhook",
    "notification",
]


ActionStatus = Literal[
    "pending",
    "approved",
    "rejected",
    "executing",
    "completed",
    "failed",
]


class ActionCreate(BaseModel):

    action_type: ActionType

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    payload: dict[str, Any] = Field(
        default_factory=dict
    )

    message_id: int | None = None


    @field_validator("title")
    @classmethod
    def clean_title(
        cls,
        value: str,
    ) -> str:

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Title cannot be empty"
            )

        return cleaned


class ActionUpdate(BaseModel):

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    payload: dict[str, Any] | None = None


    @field_validator("title")
    @classmethod
    def clean_title(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Title cannot be empty"
            )

        return cleaned


class ActionResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    user_id: int
    message_id: int | None

    action_type: ActionType
    status: ActionStatus

    title: str
    payload: dict[str, Any]

    error_message: str | None

    created_at: datetime
    updated_at: datetime

    approved_at: datetime | None
    rejected_at: datetime | None
    executed_at: datetime | None
