import app.api.actions as actions_api

from app.db.database import SessionLocal
from app.models.action_request import (
    ActionRequest,
)


TEST_PASSWORD = "StrongPass123!"


# ==========================================================
# Auth Helpers
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
# Action Helpers
# ==========================================================

def create_email_action(
    client,
    token: str,
    *,
    title: str = "Supplier follow-up",
    recipient: str = "supplier@example.com",
):

    return client.post(
        "/api/actions",
        json={
            "action_type":
                "email",

            "title":
                title,

            "payload": {
                "to":
                    recipient,

                "subject":
                    "Delivery Confirmation",

                "body":
                    "Please confirm delivery by Friday.",
            },

            "message_id":
                None,
        },
        headers=auth_headers(
            token
        ),
    )


def approve_action(
    client,
    token: str,
    action_id: int,
):

    return client.post(
        (
            f"/api/actions/"
            f"{action_id}"
            "/approve"
        ),
        headers=auth_headers(
            token
        ),
    )


# ==========================================================
# 1. Actions Require Authentication
# ==========================================================

def test_actions_require_authentication(
    client,
):

    response = client.get(
        "/api/actions"
    )

    assert response.status_code in {
        401,
        403,
    }


# ==========================================================
# 2. Create Email Action -> Pending
# ==========================================================

def test_create_email_action_is_pending(
    client,
):

    _, token = create_user(
        client,
        "actions.create@example.com",
    )


    response = create_email_action(
        client,
        token,
    )


    assert response.status_code == 201

    payload = response.json()

    assert payload[
        "action_type"
    ] == "email"

    assert payload[
        "status"
    ] == "pending"

    assert payload[
        "payload"
    ][
        "to"
    ] == "supplier@example.com"


# ==========================================================
# 3. Cannot Execute Before Approval
# ==========================================================

def test_pending_action_cannot_execute(
    client,
    monkeypatch,
):

    _, token = create_user(
        client,
        "actions.pending@example.com",
    )


    create_response = (
        create_email_action(
            client,
            token,
        )
    )

    action_id = (
        create_response.json()[
            "id"
        ]
    )


    send_called = {
        "value":
            False,
    }


    def fake_send_email(
        payload,
    ):

        send_called[
            "value"
        ] = True


    monkeypatch.setattr(
        actions_api,
        "send_email_action",
        fake_send_email,
    )


    response = client.post(
        (
            f"/api/actions/"
            f"{action_id}"
            "/execute"
        ),
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 409

    assert send_called[
        "value"
    ] is False


# ==========================================================
# 4. Approved Email Executes Successfully
# ==========================================================

def test_approved_email_execution_completes(
    client,
    monkeypatch,
):

    _, token = create_user(
        client,
        "actions.execute@example.com",
    )


    create_response = (
        create_email_action(
            client,
            token,
        )
    )

    action_id = (
        create_response.json()[
            "id"
        ]
    )


    approval_response = (
        approve_action(
            client,
            token,
            action_id,
        )
    )

    assert (
        approval_response
        .status_code
        == 200
    )

    assert (
        approval_response
        .json()[
            "status"
        ]
        == "approved"
    )


    captured = {}


    def fake_send_email(
        payload,
    ):

        captured[
            "payload"
        ] = payload


    monkeypatch.setattr(
        actions_api,
        "send_email_action",
        fake_send_email,
    )


    response = client.post(
        (
            f"/api/actions/"
            f"{action_id}"
            "/execute"
        ),
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "status"
    ] == "completed"

    assert payload[
        "executed_at"
    ] is not None

    assert payload[
        "error_message"
    ] is None

    assert captured[
        "payload"
    ][
        "to"
    ] == "supplier@example.com"


# ==========================================================
# 5. Delivery Failure Is Audited
# ==========================================================

def test_email_delivery_failure_is_recorded(
    client,
    monkeypatch,
):

    _, token = create_user(
        client,
        "actions.failure@example.com",
    )


    create_response = (
        create_email_action(
            client,
            token,
        )
    )

    action_id = (
        create_response.json()[
            "id"
        ]
    )


    approve_action(
        client,
        token,
        action_id,
    )


    def failing_send_email(
        payload,
    ):

        raise (
            actions_api
            .EmailDeliveryError(
                "Simulated SMTP failure."
            )
        )


    monkeypatch.setattr(
        actions_api,
        "send_email_action",
        failing_send_email,
    )


    response = client.post(
        (
            f"/api/actions/"
            f"{action_id}"
            "/execute"
        ),
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "status"
    ] == "failed"

    assert payload[
        "error_message"
    ] == "Simulated SMTP failure."

    assert payload[
        "executed_at"
    ] is not None


# ==========================================================
# 6. Completed Action Cannot Execute Twice
# ==========================================================

def test_completed_action_cannot_execute_twice(
    client,
    monkeypatch,
):

    _, token = create_user(
        client,
        "actions.once@example.com",
    )


    create_response = (
        create_email_action(
            client,
            token,
        )
    )

    action_id = (
        create_response.json()[
            "id"
        ]
    )


    approve_action(
        client,
        token,
        action_id,
    )


    send_count = {
        "value":
            0,
    }


    def fake_send_email(
        payload,
    ):

        send_count[
            "value"
        ] += 1


    monkeypatch.setattr(
        actions_api,
        "send_email_action",
        fake_send_email,
    )


    first_response = client.post(
        (
            f"/api/actions/"
            f"{action_id}"
            "/execute"
        ),
        headers=auth_headers(
            token
        ),
    )

    assert first_response.status_code == 200

    assert first_response.json()[
        "status"
    ] == "completed"


    second_response = client.post(
        (
            f"/api/actions/"
            f"{action_id}"
            "/execute"
        ),
        headers=auth_headers(
            token
        ),
    )


    assert second_response.status_code == 409

    assert send_count[
        "value"
    ] == 1


# ==========================================================
# 7. User Cannot Execute Another User's Action
# ==========================================================

def test_user_cannot_execute_another_users_action(
    client,
    monkeypatch,
):

    _, owner_token = create_user(
        client,
        "actions.owner@example.com",
    )

    _, attacker_token = create_user(
        client,
        "actions.attacker@example.com",
    )


    create_response = (
        create_email_action(
            client,
            owner_token,
        )
    )

    action_id = (
        create_response.json()[
            "id"
        ]
    )


    approve_action(
        client,
        owner_token,
        action_id,
    )


    send_called = {
        "value":
            False,
    }


    def fake_send_email(
        payload,
    ):

        send_called[
            "value"
        ] = True


    monkeypatch.setattr(
        actions_api,
        "send_email_action",
        fake_send_email,
    )


    response = client.post(
        (
            f"/api/actions/"
            f"{action_id}"
            "/execute"
        ),
        headers=auth_headers(
            attacker_token
        ),
    )


    assert response.status_code == 404

    assert send_called[
        "value"
    ] is False


# ==========================================================
# 8. Database Shows Final Completed State
# ==========================================================

def test_completed_state_is_persisted(
    client,
    monkeypatch,
):

    _, token = create_user(
        client,
        "actions.persist@example.com",
    )


    create_response = (
        create_email_action(
            client,
            token,
        )
    )

    action_id = (
        create_response.json()[
            "id"
        ]
    )


    approve_action(
        client,
        token,
        action_id,
    )


    monkeypatch.setattr(
        actions_api,
        "send_email_action",
        lambda payload: None,
    )


    execute_response = client.post(
        (
            f"/api/actions/"
            f"{action_id}"
            "/execute"
        ),
        headers=auth_headers(
            token
        ),
    )

    assert execute_response.status_code == 200


    db = SessionLocal()

    try:

        row = db.get(
            ActionRequest,
            action_id,
        )

        assert row is not None

        assert row.status == (
            "completed"
        )

        assert row.executed_at is not None

    finally:

        db.close()
