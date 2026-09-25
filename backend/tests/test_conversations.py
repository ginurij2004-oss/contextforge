TEST_PASSWORD = "StrongPass123!"


# ==========================================================
# Helpers
# ==========================================================

def register_user(
    client,
    email: str,
    password: str = TEST_PASSWORD,
):

    response = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": password,
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
    password: str = TEST_PASSWORD,
) -> str:

    response = client.post(
        "/api/auth/token",
        data={
            "username": email,
            "password": password,
        },
        headers={
            "Content-Type":
                "application/x-www-form-urlencoded",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload.get(
        "access_token"
    )

    return payload[
        "access_token"
    ]


def auth_headers(
    token: str,
):

    return {
        "Authorization":
            f"Bearer {token}",
    }


def create_user_and_token(
    client,
    email: str,
) -> str:

    register_user(
        client,
        email,
    )

    return login_user(
        client,
        email,
    )


def create_conversation(
    client,
    token: str,
    title: str = "Test Conversation",
):

    response = client.post(
        "/api/conversations",
        json={
            "title": title,
        },
        headers=auth_headers(
            token
        ),
    )

    assert response.status_code == 201

    return response.json()


# ==========================================================
# Create Conversation
# ==========================================================

def test_create_conversation(
    client,
):

    token = create_user_and_token(
        client,
        "conversation.create@example.com",
    )


    conversation = create_conversation(
        client,
        token,
        "Project Notes",
    )


    assert isinstance(
        conversation[
            "id"
        ],
        int,
    )

    assert conversation[
        "title"
    ] == "Project Notes"


# ==========================================================
# List Conversations
# ==========================================================

def test_list_conversations(
    client,
):

    token = create_user_and_token(
        client,
        "conversation.list@example.com",
    )


    first = create_conversation(
        client,
        token,
        "First Conversation",
    )

    second = create_conversation(
        client,
        token,
        "Second Conversation",
    )


    response = client.get(
        "/api/conversations",
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 200

    conversations = response.json()

    assert len(
        conversations
    ) == 2


    # Backend orders newest first.
    assert conversations[0][
        "id"
    ] == second[
        "id"
    ]

    assert conversations[1][
        "id"
    ] == first[
        "id"
    ]


# ==========================================================
# Rename Conversation
# ==========================================================

def test_rename_conversation(
    client,
):

    token = create_user_and_token(
        client,
        "conversation.rename@example.com",
    )


    conversation = create_conversation(
        client,
        token,
        "Old Name",
    )


    response = client.patch(
        (
            "/api/conversations/"
            f"{conversation['id']}"
        ),
        json={
            "title":
                "Renamed Conversation",
        },
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 200

    updated = response.json()

    assert updated[
        "id"
    ] == conversation[
        "id"
    ]

    assert updated[
        "title"
    ] == "Renamed Conversation"


# ==========================================================
# Empty Rename Is Rejected
# ==========================================================

def test_empty_conversation_title_is_rejected(
    client,
):

    token = create_user_and_token(
        client,
        "conversation.emptyrename@example.com",
    )


    conversation = create_conversation(
        client,
        token,
        "Original Title",
    )


    response = client.patch(
        (
            "/api/conversations/"
            f"{conversation['id']}"
        ),
        json={
            "title": "   ",
        },
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 400


# ==========================================================
# Delete Conversation
# ==========================================================

def test_delete_conversation(
    client,
):

    token = create_user_and_token(
        client,
        "conversation.delete@example.com",
    )


    conversation = create_conversation(
        client,
        token,
        "Delete Me",
    )


    response = client.delete(
        (
            "/api/conversations/"
            f"{conversation['id']}"
        ),
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "conversation_id"
    ] == conversation[
        "id"
    ]


    list_response = client.get(
        "/api/conversations",
        headers=auth_headers(
            token
        ),
    )

    assert list_response.status_code == 200

    assert list_response.json() == []


# ==========================================================
# Authentication Required
# ==========================================================

def test_conversation_list_requires_authentication(
    client,
):

    response = client.get(
        "/api/conversations"
    )

    assert response.status_code in {
        401,
        403,
    }


# ==========================================================
# User Isolation - Messages
# ==========================================================

def test_user_cannot_read_another_users_conversation(
    client,
):

    owner_token = create_user_and_token(
        client,
        "conversation.owner@example.com",
    )

    other_token = create_user_and_token(
        client,
        "conversation.other@example.com",
    )


    conversation = create_conversation(
        client,
        owner_token,
        "Owner Private Conversation",
    )


    response = client.get(
        (
            "/api/conversations/"
            f"{conversation['id']}"
            "/messages"
        ),
        headers=auth_headers(
            other_token
        ),
    )


    assert response.status_code == 404


# ==========================================================
# User Isolation - Rename
# ==========================================================

def test_user_cannot_rename_another_users_conversation(
    client,
):

    owner_token = create_user_and_token(
        client,
        "rename.owner@example.com",
    )

    attacker_token = create_user_and_token(
        client,
        "rename.other@example.com",
    )


    conversation = create_conversation(
        client,
        owner_token,
        "Private Conversation",
    )


    response = client.patch(
        (
            "/api/conversations/"
            f"{conversation['id']}"
        ),
        json={
            "title":
                "I Should Not Be Able To Rename This",
        },
        headers=auth_headers(
            attacker_token
        ),
    )


    assert response.status_code == 404


# ==========================================================
# User Isolation - Delete
# ==========================================================

def test_user_cannot_delete_another_users_conversation(
    client,
):

    owner_token = create_user_and_token(
        client,
        "delete.owner@example.com",
    )

    attacker_token = create_user_and_token(
        client,
        "delete.other@example.com",
    )


    conversation = create_conversation(
        client,
        owner_token,
        "Owner Conversation",
    )


    response = client.delete(
        (
            "/api/conversations/"
            f"{conversation['id']}"
        ),
        headers=auth_headers(
            attacker_token
        ),
    )


    assert response.status_code == 404


    # Confirm the owner's conversation still exists.
    owner_list = client.get(
        "/api/conversations",
        headers=auth_headers(
            owner_token
        ),
    )


    assert owner_list.status_code == 200

    conversations = owner_list.json()

    assert len(
        conversations
    ) == 1

    assert conversations[0][
        "id"
    ] == conversation[
        "id"
    ]
