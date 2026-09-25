from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone


def calculate_success_rate(
    completed: int,
    failed: int,
) -> float:
    total = completed + failed
    if total <= 0:
        return 0.0
    return round((completed / total) * 100.0, 1)


def build_daily_run_series(
    rows: list[tuple[datetime, str]],
    *,
    days: int = 7,
    now: datetime | None = None,
) -> list[dict]:
    current = now or datetime.now(timezone.utc)
    first_day = (current - timedelta(days=days - 1)).date()

    buckets: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "completed": 0,
            "failed": 0,
            "other": 0,
        }
    )

    for created_at, status in rows:
        key = created_at.astimezone(timezone.utc).date().isoformat()
        if key < first_day.isoformat():
            continue

        if status == "completed":
            buckets[key]["completed"] += 1
        elif status == "failed":
            buckets[key]["failed"] += 1
        else:
            buckets[key]["other"] += 1

    series: list[dict] = []
    for offset in range(days):
        day = first_day + timedelta(days=offset)
        key = day.isoformat()
        series.append(
            {
                "date": key,
                **buckets[key],
            }
        )

    return series
