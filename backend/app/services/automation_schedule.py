from __future__ import annotations

from datetime import (
    datetime,
    time,
    timedelta,
    timezone,
)
from zoneinfo import ZoneInfo


WEEKDAY_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def utc_now() -> datetime:
    return datetime.now(
        timezone.utc
    )


def parse_aware_datetime(
    value: str,
) -> datetime:
    parsed = datetime.fromisoformat(
        value.replace(
            "Z",
            "+00:00",
        )
    )

    if parsed.utcoffset() is None:
        raise ValueError(
            "Scheduled date-time must include a UTC offset."
        )

    return parsed


def parse_clock(
    value: str,
) -> time:
    return time.fromisoformat(
        value
    )


def _to_utc(
    value: datetime,
) -> datetime:
    return value.astimezone(
        timezone.utc
    )


def _next_daily(
    schedule: dict,
    after: datetime,
) -> datetime:
    zone = ZoneInfo(
        schedule["timezone"]
    )
    local_after = after.astimezone(
        zone
    )
    clock = parse_clock(
        schedule["time"]
    )

    candidate = datetime.combine(
        local_after.date(),
        clock,
        tzinfo=zone,
    )

    if candidate <= local_after:
        candidate += timedelta(
            days=1
        )

    return _to_utc(
        candidate
    )


def _next_weekdays(
    schedule: dict,
    after: datetime,
) -> datetime:
    zone = ZoneInfo(
        schedule["timezone"]
    )
    local_after = after.astimezone(
        zone
    )
    clock = parse_clock(
        schedule["time"]
    )

    candidate = datetime.combine(
        local_after.date(),
        clock,
        tzinfo=zone,
    )

    while (
        candidate <= local_after
        or candidate.weekday() >= 5
    ):
        candidate += timedelta(
            days=1
        )

    return _to_utc(
        candidate
    )


def _next_weekly(
    schedule: dict,
    after: datetime,
) -> datetime:
    zone = ZoneInfo(
        schedule["timezone"]
    )
    local_after = after.astimezone(
        zone
    )
    clock = parse_clock(
        schedule["time"]
    )
    target_weekday = WEEKDAY_INDEX[
        schedule["weekday"]
    ]

    days_ahead = (
        target_weekday
        - local_after.weekday()
    ) % 7

    candidate_date = (
        local_after.date()
        + timedelta(
            days=days_ahead
        )
    )

    candidate = datetime.combine(
        candidate_date,
        clock,
        tzinfo=zone,
    )

    if candidate <= local_after:
        candidate += timedelta(
            days=7
        )

    return _to_utc(
        candidate
    )


def _next_interval(
    schedule: dict,
    after: datetime,
) -> datetime:
    start = parse_aware_datetime(
        schedule["start_at"]
    ).astimezone(
        timezone.utc
    )
    hours = int(
        schedule["hours"]
    )
    step = timedelta(
        hours=hours
    )

    if start > after:
        return start

    elapsed = after - start
    intervals = (
        int(
            elapsed.total_seconds()
            // step.total_seconds()
        )
        + 1
    )

    return start + (
        step * intervals
    )


def calculate_next_run(
    trigger_type: str,
    schedule: dict | None,
    *,
    after: datetime | None = None,
) -> datetime | None:

    if trigger_type == "manual":
        return None

    if schedule is None:
        return None

    reference = (
        after
        or utc_now()
    ).astimezone(
        timezone.utc
    )

    if trigger_type == "once":
        run_at = parse_aware_datetime(
            schedule["run_at"]
        ).astimezone(
            timezone.utc
        )

        if run_at <= reference:
            return None

        return run_at

    if trigger_type == "daily":
        return _next_daily(
            schedule,
            reference,
        )

    if trigger_type == "weekdays":
        return _next_weekdays(
            schedule,
            reference,
        )

    if trigger_type == "weekly":
        return _next_weekly(
            schedule,
            reference,
        )

    if trigger_type == "interval":
        return _next_interval(
            schedule,
            reference,
        )

    return None


def schedule_label(
    trigger_type: str,
    schedule: dict | None,
) -> str:

    if trigger_type == "manual":
        return "Manual"

    if not schedule:
        return trigger_type.title()

    if trigger_type == "once":
        return f"Once at {schedule.get('run_at', '—')}"

    if trigger_type == "daily":
        return (
            f"Daily at {schedule.get('time', '—')} "
            f"({schedule.get('timezone', 'UTC')})"
        )

    if trigger_type == "weekdays":
        return (
            f"Weekdays at {schedule.get('time', '—')} "
            f"({schedule.get('timezone', 'UTC')})"
        )

    if trigger_type == "weekly":
        return (
            f"Every {schedule.get('weekday', 'week').title()} "
            f"at {schedule.get('time', '—')} "
            f"({schedule.get('timezone', 'UTC')})"
        )

    if trigger_type == "interval":
        return (
            f"Every {schedule.get('hours', '—')} hour(s)"
        )

    return trigger_type.title()
