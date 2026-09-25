from datetime import datetime, timezone

from app.services.automation_schedule import calculate_next_run


def test_manual_has_no_next_run():
    assert calculate_next_run(
        "manual",
        None,
        after=datetime(
            2026,
            9,
            25,
            4,
            0,
            tzinfo=timezone.utc,
        ),
    ) is None


def test_daily_colombo_schedule():
    next_run = calculate_next_run(
        "daily",
        {
            "time": "09:00",
            "timezone": "Asia/Colombo",
        },
        after=datetime(
            2026,
            9,
            25,
            4,
            0,
            tzinfo=timezone.utc,
        ),
    )

    # 09:00 Asia/Colombo = 03:30 UTC. At 04:00 UTC,
    # the next run should be the following day.
    assert next_run == datetime(
        2026,
        9,
        26,
        3,
        30,
        tzinfo=timezone.utc,
    )


def test_weekly_schedule():
    next_run = calculate_next_run(
        "weekly",
        {
            "weekday": "monday",
            "time": "10:00",
            "timezone": "Asia/Colombo",
        },
        after=datetime(
            2026,
            9,
            25,
            6,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert next_run is not None
    assert next_run > datetime(
        2026,
        9,
        25,
        6,
        0,
        tzinfo=timezone.utc,
    )


def test_interval_schedule():
    next_run = calculate_next_run(
        "interval",
        {
            "hours": 6,
            "start_at": "2026-09-25T06:00:00+00:00",
        },
        after=datetime(
            2026,
            9,
            25,
            13,
            0,
            tzinfo=timezone.utc,
        ),
    )

    assert next_run == datetime(
        2026,
        9,
        25,
        18,
        0,
        tzinfo=timezone.utc,
    )
