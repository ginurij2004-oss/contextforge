from datetime import datetime, timezone

from app.services.operations_metrics import (
    build_daily_run_series,
    calculate_success_rate,
)


def test_success_rate():
    assert calculate_success_rate(9, 1) == 90.0
    assert calculate_success_rate(0, 0) == 0.0


def test_daily_run_series():
    now = datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc)
    rows = [
        (datetime(2026, 9, 25, 10, 0, tzinfo=timezone.utc), "completed"),
        (datetime(2026, 9, 25, 11, 0, tzinfo=timezone.utc), "failed"),
        (datetime(2026, 9, 24, 11, 0, tzinfo=timezone.utc), "pending_approval"),
    ]

    series = build_daily_run_series(
        rows,
        days=2,
        now=now,
    )

    assert series[0]["date"] == "2026-09-24"
    assert series[0]["other"] == 1
    assert series[1]["completed"] == 1
    assert series[1]["failed"] == 1
