from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.db.database import SessionLocal
from app.models.ai_request import AIRequest


TEST_PASSWORD = "StrongPass123!"


# ==========================================================
# Authentication Helpers
# ==========================================================

def register_user(
    client,
    email: str,
):

    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code in {
        200,
        201,
    }

    return response.json()


def login_user(
    client,
    email: str,
) -> str:

    response = client.post(
        "/api/auth/token",
        data={
            "username": email,
            "password": TEST_PASSWORD,
        },
        headers={
            "Content-Type":
                "application/x-www-form-urlencoded",
        },
    )

    assert response.status_code == 200

    return response.json()[
        "access_token"
    ]


def create_user(
    client,
    email: str,
):

    user = register_user(
        client,
        email,
    )

    token = login_user(
        client,
        email,
    )

    return user, token


def auth_headers(
    token: str,
):

    return {
        "Authorization":
            f"Bearer {token}",
    }


# ==========================================================
# AI Request DB Helper
# ==========================================================

def insert_ai_request(
    user_id: int,
    prompt_version: str | None,
    status: str = "success",
    latency_ms: int | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    created_at: datetime | None = None,
):

    db = SessionLocal()

    try:

        request = AIRequest(
            user_id=user_id,
            model="pytest-model",
            prompt_version=prompt_version,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            status=status,
        )


        if created_at is not None:

            request.created_at = (
                created_at
            )


        db.add(
            request
        )

        db.commit()

        db.refresh(
            request
        )

        return request.id

    finally:

        db.close()


# ==========================================================
# 1. Authentication Required
# ==========================================================

def test_analytics_requires_authentication(
    client,
):

    response = client.get(
        "/api/analytics/dashboard"
    )

    assert response.status_code in {
        401,
        403,
    }


# ==========================================================
# 2. Empty Dashboard
# ==========================================================

def test_empty_analytics_dashboard(
    client,
):

    _, token = create_user(
        client,
        "analytics.empty@example.com",
    )


    response = client.get(
        "/api/analytics/dashboard",
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 200

    payload = response.json()

    overview = payload[
        "overview"
    ]


    assert overview[
        "total_requests"
    ] == 0

    assert overview[
        "successful_requests"
    ] == 0

    assert overview[
        "failed_requests"
    ] == 0

    assert overview[
        "success_rate"
    ] == 0.0

    assert overview[
        "average_latency_ms"
    ] == 0.0

    assert overview[
        "total_input_tokens"
    ] == 0

    assert overview[
        "total_output_tokens"
    ] == 0

    assert overview[
        "total_tokens"
    ] == 0

    assert overview[
        "chat_requests"
    ] == 0

    assert overview[
        "document_requests"
    ] == 0

    assert overview[
        "agent_requests"
    ] == 0


    # Dashboard always provides seven days,
    # even if there is no activity.
    assert len(
        payload[
            "daily_activity"
        ]
    ) == 7

    assert payload[
        "recent_requests"
    ] == []

    assert payload[
        "evaluation_runs"
    ] == []


# ==========================================================
# 3. Metrics + Mode Classification
# ==========================================================

def test_analytics_calculates_metrics_and_modes(
    client,
):

    user, token = create_user(
        client,
        "analytics.metrics@example.com",
    )


    insert_ai_request(
        user_id=user[
            "id"
        ],
        prompt_version="chat-v1",
        status="success",
        latency_ms=100,
        input_tokens=10,
        output_tokens=20,
    )


    insert_ai_request(
        user_id=user[
            "id"
        ],
        prompt_version="rag-v1",
        status="success",
        latency_ms=200,
        input_tokens=None,
        output_tokens=None,
    )


    insert_ai_request(
        user_id=user[
            "id"
        ],
        prompt_version="agent-v1",
        status="success",
        latency_ms=300,
        input_tokens=None,
        output_tokens=None,
    )


    insert_ai_request(
        user_id=user[
            "id"
        ],
        prompt_version="chat-v1",
        status="failed",
        latency_ms=None,
        input_tokens=None,
        output_tokens=None,
    )


    response = client.get(
        "/api/analytics/dashboard",
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 200

    payload = response.json()

    overview = payload[
        "overview"
    ]


    assert overview[
        "total_requests"
    ] == 4

    assert overview[
        "successful_requests"
    ] == 3

    assert overview[
        "failed_requests"
    ] == 1

    assert overview[
        "success_rate"
    ] == 75.0


    # Average only uses non-null latencies:
    # (100 + 200 + 300) / 3 = 200
    assert overview[
        "average_latency_ms"
    ] == 200.0


    assert overview[
        "total_input_tokens"
    ] == 10

    assert overview[
        "total_output_tokens"
    ] == 20

    assert overview[
        "total_tokens"
    ] == 30


    assert overview[
        "chat_requests"
    ] == 2

    assert overview[
        "document_requests"
    ] == 1

    assert overview[
        "agent_requests"
    ] == 1


    modes = {
        item[
            "mode"
        ]
        for item
        in payload[
            "recent_requests"
        ]
    }


    assert "chat" in modes

    assert "documents" in modes

    assert "agent" in modes


# ==========================================================
# 4. User Isolation
# ==========================================================

def test_analytics_only_contains_current_users_requests(
    client,
):

    user_a, token_a = create_user(
        client,
        "analytics.usera@example.com",
    )

    user_b, token_b = create_user(
        client,
        "analytics.userb@example.com",
    )


    insert_ai_request(
        user_id=user_a[
            "id"
        ],
        prompt_version="chat-v1",
        status="success",
        latency_ms=100,
        input_tokens=5,
        output_tokens=10,
    )


    insert_ai_request(
        user_id=user_a[
            "id"
        ],
        prompt_version="agent-v1",
        status="success",
        latency_ms=150,
    )


    insert_ai_request(
        user_id=user_b[
            "id"
        ],
        prompt_version="rag-v1",
        status="failed",
        latency_ms=999,
        input_tokens=500,
        output_tokens=500,
    )


    response_a = client.get(
        "/api/analytics/dashboard",
        headers=auth_headers(
            token_a
        ),
    )


    assert response_a.status_code == 200

    overview_a = response_a.json()[
        "overview"
    ]


    assert overview_a[
        "total_requests"
    ] == 2

    assert overview_a[
        "successful_requests"
    ] == 2

    assert overview_a[
        "failed_requests"
    ] == 0

    assert overview_a[
        "chat_requests"
    ] == 1

    assert overview_a[
        "agent_requests"
    ] == 1

    assert overview_a[
        "document_requests"
    ] == 0

    assert overview_a[
        "total_tokens"
    ] == 15


    response_b = client.get(
        "/api/analytics/dashboard",
        headers=auth_headers(
            token_b
        ),
    )


    assert response_b.status_code == 200

    overview_b = response_b.json()[
        "overview"
    ]


    assert overview_b[
        "total_requests"
    ] == 1

    assert overview_b[
        "successful_requests"
    ] == 0

    assert overview_b[
        "failed_requests"
    ] == 1

    assert overview_b[
        "document_requests"
    ] == 1

    assert overview_b[
        "chat_requests"
    ] == 0

    assert overview_b[
        "agent_requests"
    ] == 0

    assert overview_b[
        "total_tokens"
    ] == 1000


# ==========================================================
# 5. Daily Activity + Old Request Exclusion
# ==========================================================

def test_analytics_daily_activity_tracks_last_seven_days(
    client,
):

    user, token = create_user(
        client,
        "analytics.daily@example.com",
    )


    now = datetime.now(
        timezone.utc
    ).replace(
        tzinfo=None
    )


    # Today: success
    insert_ai_request(
        user_id=user[
            "id"
        ],
        prompt_version="chat-v1",
        status="success",
        latency_ms=120,
        input_tokens=12,
        output_tokens=18,
        created_at=now,
    )


    # Yesterday: failed
    insert_ai_request(
        user_id=user[
            "id"
        ],
        prompt_version="rag-v1",
        status="failed",
        latency_ms=240,
        input_tokens=3,
        output_tokens=7,
        created_at=(
            now
            - timedelta(
                days=1
            )
        ),
    )


    # Older than the 7-day chart window.
    # It counts in overall metrics but must not
    # appear in daily_activity.
    insert_ai_request(
        user_id=user[
            "id"
        ],
        prompt_version="agent-v1",
        status="success",
        latency_ms=500,
        input_tokens=100,
        output_tokens=100,
        created_at=(
            now
            - timedelta(
                days=10
            )
        ),
    )


    response = client.get(
        "/api/analytics/dashboard",
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 200

    payload = response.json()

    daily = payload[
        "daily_activity"
    ]


    assert len(
        daily
    ) == 7


    total_chart_requests = sum(
        item[
            "requests"
        ]
        for item in daily
    )


    # Only today + yesterday are inside
    # the 7-day chart.
    assert total_chart_requests == 2


    total_daily_success = sum(
        item[
            "successful_requests"
        ]
        for item in daily
    )

    total_daily_failed = sum(
        item[
            "failed_requests"
        ]
        for item in daily
    )


    assert total_daily_success == 1

    assert total_daily_failed == 1


    # Overall metrics still include all 3.
    assert payload[
        "overview"
    ][
        "total_requests"
    ] == 3


# ==========================================================
# 6. Recent Requests Are Newest First
# ==========================================================

def test_recent_analytics_requests_are_newest_first(
    client,
):

    user, token = create_user(
        client,
        "analytics.recent@example.com",
    )


    first_id = insert_ai_request(
        user_id=user[
            "id"
        ],
        prompt_version="chat-v1",
        status="success",
        latency_ms=100,
    )


    second_id = insert_ai_request(
        user_id=user[
            "id"
        ],
        prompt_version="agent-v1",
        status="success",
        latency_ms=200,
    )


    response = client.get(
        "/api/analytics/dashboard",
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 200

    recent = response.json()[
        "recent_requests"
    ]


    assert len(
        recent
    ) == 2

    assert recent[0][
        "id"
    ] == second_id

    assert recent[1][
        "id"
    ] == first_id


    assert recent[0][
        "mode"
    ] == "agent"

    assert recent[1][
        "mode"
    ] == "chat"
