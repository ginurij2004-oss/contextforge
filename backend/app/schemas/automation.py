from datetime import datetime, time
from typing import Any, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


AutomationTriggerType = Literal[
    "manual",
    "once",
    "daily",
    "weekdays",
    "weekly",
    "interval",
]

AutomationActionType = Literal[
    "email",
    "calendar",
    "webhook",
]

WEEKDAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}


def _required_text(
    config: dict[str, Any],
    key: str,
) -> str:

    value = str(
        config.get(
            key,
            "",
        )
    ).strip()

    if not value:
        raise ValueError(
            f"Automation config requires '{key}'."
        )

    return value


def _parse_aware_datetime(
    value: str,
    field_name: str,
) -> datetime:

    try:
        parsed = datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a valid ISO 8601 date-time."
        ) from exc

    if parsed.utcoffset() is None:
        raise ValueError(
            f"{field_name} must include a UTC offset."
        )

    return parsed


def _validate_timezone(
    value: str,
) -> str:

    cleaned = value.strip()

    if not cleaned:
        cleaned = "Asia/Colombo"

    try:
        ZoneInfo(cleaned)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            "Timezone must be a valid IANA name such as Asia/Colombo."
        ) from exc

    return cleaned


def _validate_clock_time(
    value: str,
) -> str:

    cleaned = value.strip()

    try:
        time.fromisoformat(cleaned)
    except ValueError as exc:
        raise ValueError(
            "Schedule time must use HH:MM or HH:MM:SS."
        ) from exc

    return cleaned


def validate_automation_config(
    action_type: str,
    config: dict[str, Any],
) -> dict[str, Any]:

    cleaned = dict(
        config or {}
    )

    if action_type == "email":

        cleaned["to"] = _required_text(
            cleaned,
            "to",
        )

        cleaned["subject"] = _required_text(
            cleaned,
            "subject",
        )

        cleaned["body"] = _required_text(
            cleaned,
            "body",
        )

        return cleaned

    if action_type == "calendar":

        cleaned["title"] = _required_text(
            cleaned,
            "title",
        )

        start_time = _required_text(
            cleaned,
            "start_time",
        )

        end_time = _required_text(
            cleaned,
            "end_time",
        )

        parsed_start = _parse_aware_datetime(
            start_time,
            "Calendar start_time",
        )

        parsed_end = _parse_aware_datetime(
            end_time,
            "Calendar end_time",
        )

        if parsed_end <= parsed_start:
            raise ValueError(
                "Calendar end_time must be after start_time."
            )

        cleaned["start_time"] = start_time
        cleaned["end_time"] = end_time
        cleaned["timezone"] = _validate_timezone(
            str(
                cleaned.get(
                    "timezone",
                    "Asia/Colombo",
                )
            )
        )
        cleaned["description"] = str(
            cleaned.get(
                "description",
                "",
            )
        )

        return cleaned

    if action_type == "webhook":

        target = _required_text(
            cleaned,
            "target",
        )

        if target != "demo_echo":
            raise ValueError(
                "Webhook target is not allowed. "
                "Phase 7 currently supports only 'demo_echo'."
            )

        data = cleaned.get(
            "data",
            {},
        )

        if not isinstance(
            data,
            dict,
        ):
            raise ValueError(
                "Webhook config 'data' must be a JSON object."
            )

        cleaned["target"] = target
        cleaned["data"] = data

        return cleaned

    raise ValueError(
        "Unsupported automation action type."
    )


def validate_schedule_config(
    trigger_type: str,
    schedule: dict[str, Any] | None,
) -> dict[str, Any] | None:

    if trigger_type == "manual":
        return None

    cleaned = dict(
        schedule or {}
    )

    if trigger_type == "once":
        run_at = _required_text(
            cleaned,
            "run_at",
        )
        _parse_aware_datetime(
            run_at,
            "Schedule run_at",
        )
        return {
            "run_at": run_at,
        }

    if trigger_type in {
        "daily",
        "weekdays",
    }:
        clock = _validate_clock_time(
            _required_text(
                cleaned,
                "time",
            )
        )
        timezone_name = _validate_timezone(
            str(
                cleaned.get(
                    "timezone",
                    "Asia/Colombo",
                )
            )
        )
        return {
            "time": clock,
            "timezone": timezone_name,
        }

    if trigger_type == "weekly":
        weekday = _required_text(
            cleaned,
            "weekday",
        ).lower()

        if weekday not in WEEKDAYS:
            raise ValueError(
                "Weekly schedule weekday must be monday through sunday."
            )

        clock = _validate_clock_time(
            _required_text(
                cleaned,
                "time",
            )
        )

        timezone_name = _validate_timezone(
            str(
                cleaned.get(
                    "timezone",
                    "Asia/Colombo",
                )
            )
        )

        return {
            "weekday": weekday,
            "time": clock,
            "timezone": timezone_name,
        }

    if trigger_type == "interval":
        hours_raw = cleaned.get(
            "hours"
        )

        try:
            hours = int(
                hours_raw
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "Interval schedule requires an integer number of hours."
            ) from exc

        if hours < 1 or hours > 720:
            raise ValueError(
                "Interval hours must be between 1 and 720."
            )

        start_at = _required_text(
            cleaned,
            "start_at",
        )

        _parse_aware_datetime(
            start_at,
            "Interval start_at",
        )

        return {
            "hours": hours,
            "start_at": start_at,
        }

    raise ValueError(
        "Unsupported automation trigger type."
    )


class AutomationCreate(BaseModel):

    name: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    trigger_type: AutomationTriggerType = "manual"

    schedule: dict[str, Any] | None = None

    action_type: AutomationActionType

    config: dict[str, Any] = Field(
        default_factory=dict
    )

    is_enabled: bool = True
    requires_approval: bool = True

    @field_validator("name")
    @classmethod
    def clean_name(
        cls,
        value: str,
    ) -> str:

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Automation name cannot be empty."
            )

        return cleaned

    @model_validator(mode="after")
    def validate_values(
        self,
    ):

        self.config = validate_automation_config(
            action_type=self.action_type,
            config=self.config,
        )

        self.schedule = validate_schedule_config(
            trigger_type=self.trigger_type,
            schedule=self.schedule,
        )

        return self


class AutomationUpdate(BaseModel):

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    trigger_type: AutomationTriggerType | None = None
    schedule: dict[str, Any] | None = None
    config: dict[str, Any] | None = None
    is_enabled: bool | None = None
    requires_approval: bool | None = None

    @field_validator("name")
    @classmethod
    def clean_name(
        cls,
        value: str | None,
    ) -> str | None:

        if value is None:
            return None

        cleaned = value.strip()

        if not cleaned:
            raise ValueError(
                "Automation name cannot be empty."
            )

        return cleaned


class AutomationResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    user_id: int
    name: str
    description: str | None
    trigger_type: AutomationTriggerType
    schedule: dict[str, Any] | None
    action_type: AutomationActionType
    config: dict[str, Any]
    is_enabled: bool
    requires_approval: bool
    next_run_at: datetime | None
    last_triggered_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AutomationRunResponse(BaseModel):

    id: int
    automation_id: int
    automation_name: str
    user_id: int
    action_request_id: int | None
    action_type: AutomationActionType
    status: str
    trigger_source: str
    scheduled_for: datetime | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
