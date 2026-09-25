TEST_EMAIL = (
    "pytest.user@example.com"
)

TEST_PASSWORD = (
    "StrongPass123!"
)


def register_user(
    client,
):

    return client.post(
        "/api/auth/register",
        json={
            "email":
                TEST_EMAIL,

            "password":
                TEST_PASSWORD,
        },
    )


def login_user(
    client,
):

    return client.post(
        "/api/auth/token",
        data={
            "username":
                TEST_EMAIL,

            "password":
                TEST_PASSWORD,
        },
        headers={
            "Content-Type":
                "application/x-www-form-urlencoded",
        },
    )


def test_register_user(
    client,
):

    response = register_user(
        client
    )

    assert response.status_code in {
        200,
        201,
    }

    payload = response.json()

    assert payload[
        "email"
    ] == TEST_EMAIL

    assert isinstance(
        payload[
            "id"
        ],
        int,
    )


def test_duplicate_registration_is_rejected(
    client,
):

    first = register_user(
        client
    )

    assert first.status_code in {
        200,
        201,
    }


    second = register_user(
        client
    )

    assert second.status_code in {
        400,
        409,
    }


def test_login_returns_access_token(
    client,
):

    register_user(
        client
    )


    response = login_user(
        client
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "token_type"
    ].lower() == "bearer"

    assert isinstance(
        payload[
            "access_token"
        ],
        str,
    )

    assert payload[
        "access_token"
    ]


def test_current_user_requires_authentication(
    client,
):

    response = client.get(
        "/api/auth/me"
    )

    assert response.status_code in {
        401,
        403,
    }


def test_current_user_with_valid_token(
    client,
):

    register_user(
        client
    )


    login_response = login_user(
        client
    )

    assert login_response.status_code == 200


    token = (
        login_response
        .json()[
            "access_token"
        ]
    )


    response = client.get(
        "/api/auth/me",
        headers={
            "Authorization":
                f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload[
        "email"
    ] == TEST_EMAIL


def test_login_rejects_wrong_password(
    client,
):

    register_user(
        client
    )


    response = client.post(
        "/api/auth/token",
        data={
            "username":
                TEST_EMAIL,

            "password":
                "DefinitelyWrong123!",
        },
        headers={
            "Content-Type":
                "application/x-www-form-urlencoded",
        },
    )

    assert response.status_code in {
        400,
        401,
    }
