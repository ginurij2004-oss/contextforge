from datetime import datetime, timezone

import app.api.conversations as conversations_api

from app.db.database import SessionLocal
from app.models.ai_request import AIRequest
from app.models.document import Document


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
# Conversation Helper
# ==========================================================

def create_conversation(
    client,
    token: str,
    title: str = "RAG Test Conversation",
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
# Document DB Helper
# ==========================================================

def insert_document(
    user_id: int,
    filename: str,
    status: str = "ready",
):

    db = SessionLocal()

    try:

        document = Document(
            user_id=user_id,
            filename=filename,
            file_type="pdf",
            status=status,
            indexed_chunk_size=2500,
            indexed_chunk_overlap=300,
            indexed_at=(
                datetime.now(
                    timezone.utc
                ).replace(
                    tzinfo=None
                )
                if status == "ready"
                else None
            ),
            created_at=datetime.now(
                timezone.utc
            ).replace(
                tzinfo=None
            ),
        )

        db.add(
            document
        )

        db.commit()

        db.refresh(
            document
        )

        return document.id

    finally:

        db.close()


# ==========================================================
# Mock Guardrails
# ==========================================================

def mock_safe_guardrails(
    monkeypatch,
):

    monkeypatch.setattr(
        conversations_api,
        "detect_prompt_injection",
        lambda content: False,
    )

    monkeypatch.setattr(
        conversations_api,
        "is_flagged_content",
        lambda content: False,
    )


# ==========================================================
# Send Knowledge Message Helper
# ==========================================================

def send_knowledge_message(
    client,
    token: str,
    conversation_id: int,
    content: str,
    document_id=None,
):

    return client.post(
        (
            "/api/conversations/"
            f"{conversation_id}"
            "/messages"
        ),
        json={
            "content": content,
            "mode": "documents",
            "document_id": document_id,
        },
        headers=auth_headers(
            token
        ),
    )


# ==========================================================
# 1. RAG Works Across All User Documents
# ==========================================================

def test_knowledge_mode_uses_current_user_scope(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "rag.scope@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )

    document_id = insert_document(
        user[
            "id"
        ],
        "knowledge.pdf",
    )


    mock_safe_guardrails(
        monkeypatch
    )


    captured = {}


    def fake_generate_rag_answer(
        question,
        user_id,
        document_id=None,
    ):

        captured[
            "question"
        ] = question

        captured[
            "user_id"
        ] = user_id

        captured[
            "document_id"
        ] = document_id

        return {
            "answer":
                "ContextForge uses grounded retrieval.",

            "sources": [
                {
                    "document_id":
                        document_id_for_source,

                    "filename":
                        "knowledge.pdf",

                    "page": 1,

                    "score": 0.91,
                }
            ],
        }


    document_id_for_source = (
        document_id
    )


    monkeypatch.setattr(
        conversations_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )


    response = send_knowledge_message(
        client,
        token,
        conversation[
            "id"
        ],
        "How does ContextForge work?",
        document_id=None,
    )


    assert response.status_code == 200

    payload = response.json()

    assistant = payload[
        "assistant_message"
    ]


    assert captured[
        "question"
    ] == "How does ContextForge work?"

    assert captured[
        "user_id"
    ] == user[
        "id"
    ]

    # None means search across this user's
    # whole knowledge base.
    assert captured[
        "document_id"
    ] is None


    assert assistant[
        "mode"
    ] == "documents"

    assert assistant[
        "confidence"
    ] == "high"

    assert assistant[
        "content"
    ] == (
        "ContextForge uses grounded retrieval."
    )

    assert len(
        assistant[
            "sources"
        ]
    ) == 1

    assert assistant[
        "sources"
    ][0][
        "document_id"
    ] == document_id


# ==========================================================
# 2. Selected Document Scope Is Forwarded Exactly
# ==========================================================

def test_selected_document_is_forwarded_to_rag(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "rag.selected@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )

    selected_document_id = insert_document(
        user[
            "id"
        ],
        "selected.pdf",
    )


    mock_safe_guardrails(
        monkeypatch
    )


    captured = {}


    def fake_generate_rag_answer(
        question,
        user_id,
        document_id=None,
    ):

        captured[
            "user_id"
        ] = user_id

        captured[
            "document_id"
        ] = document_id

        return {
            "answer":
                "Answer from selected document.",

            "sources": [
                {
                    "document_id":
                        selected_document_id,

                    "filename":
                        "selected.pdf",

                    "page": 3,

                    "score": 0.95,
                }
            ],
        }


    monkeypatch.setattr(
        conversations_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )


    response = send_knowledge_message(
        client,
        token,
        conversation[
            "id"
        ],
        "Use only my selected PDF.",
        document_id=
            selected_document_id,
    )


    assert response.status_code == 200


    assert captured[
        "user_id"
    ] == user[
        "id"
    ]

    assert captured[
        "document_id"
    ] == selected_document_id


    assistant = response.json()[
        "assistant_message"
    ]


    assert assistant[
        "document_id"
    ] == selected_document_id

    assert assistant[
        "sources"
    ][0][
        "document_id"
    ] == selected_document_id


# ==========================================================
# 3. User Cannot Query Another User's Document
# ==========================================================

def test_user_cannot_query_another_users_document(
    client,
    monkeypatch,
):

    owner, _ = create_user(
        client,
        "rag.owner@example.com",
    )

    _, attacker_token = create_user(
        client,
        "rag.attacker@example.com",
    )

    attacker_conversation = (
        create_conversation(
            client,
            attacker_token,
        )
    )


    private_document_id = insert_document(
        owner[
            "id"
        ],
        "private-owner.pdf",
    )


    mock_safe_guardrails(
        monkeypatch
    )


    rag_called = {
        "value": False,
    }


    def fake_generate_rag_answer(
        question,
        user_id,
        document_id=None,
    ):

        rag_called[
            "value"
        ] = True

        return {
            "answer": "Should not run.",
            "sources": [],
        }


    monkeypatch.setattr(
        conversations_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )


    response = send_knowledge_message(
        client,
        attacker_token,
        attacker_conversation[
            "id"
        ],
        "Read another user's PDF.",
        document_id=
            private_document_id,
    )


    assert response.status_code == 404

    assert response.json()[
        "detail"
    ] == "Document not found"

    # Ownership validation must happen before RAG.
    assert rag_called[
        "value"
    ] is False


# ==========================================================
# 4. Non-ready Document Cannot Be Queried
# ==========================================================

def test_non_ready_document_is_rejected_before_rag(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "rag.processing@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )


    processing_document_id = (
        insert_document(
            user[
                "id"
            ],
            "processing.pdf",
            status="processing",
        )
    )


    mock_safe_guardrails(
        monkeypatch
    )


    rag_called = {
        "value": False,
    }


    def fake_generate_rag_answer(
        question,
        user_id,
        document_id=None,
    ):

        rag_called[
            "value"
        ] = True

        return {
            "answer": "Should not run.",
            "sources": [],
        }


    monkeypatch.setattr(
        conversations_api,
        "generate_rag_answer",
        fake_generate_rag_answer,
    )


    response = send_knowledge_message(
        client,
        token,
        conversation[
            "id"
        ],
        "Can I query this now?",
        document_id=
            processing_document_id,
    )


    assert response.status_code == 400

    assert (
        "must be ready"
        in response.json()[
            "detail"
        ].lower()
    )

    assert rag_called[
        "value"
    ] is False


# ==========================================================
# 5. No Retrieved Sources Produces Low Confidence
# ==========================================================

def test_rag_without_sources_returns_low_confidence(
    client,
    monkeypatch,
):

    _, token = create_user(
        client,
        "rag.nosources@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )


    mock_safe_guardrails(
        monkeypatch
    )


    monkeypatch.setattr(
        conversations_api,
        "generate_rag_answer",
        lambda question, user_id, document_id=None: {
            "answer":
                "I could not find enough grounded context.",

            "sources": [],
        },
    )


    response = send_knowledge_message(
        client,
        token,
        conversation[
            "id"
        ],
        "Tell me something not in my documents.",
        document_id=None,
    )


    assert response.status_code == 200

    assistant = response.json()[
        "assistant_message"
    ]


    assert assistant[
        "mode"
    ] == "documents"

    assert assistant[
        "confidence"
    ] == "low"

    assert assistant[
        "sources"
    ] == []


# ==========================================================
# 6. RAG Sources Persist in Conversation History
# ==========================================================

def test_rag_sources_are_persisted(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "rag.sources@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )

    document_id = insert_document(
        user[
            "id"
        ],
        "source.pdf",
    )


    mock_safe_guardrails(
        monkeypatch
    )


    monkeypatch.setattr(
        conversations_api,
        "generate_rag_answer",
        lambda question, user_id, document_id=None: {
            "answer":
                "Grounded answer with citation.",

            "sources": [
                {
                    "document_id":
                        document_id_for_source,

                    "filename":
                        "source.pdf",

                    "page": 7,

                    "score": 0.88,
                }
            ],
        },
    )


    document_id_for_source = (
        document_id
    )


    send_response = send_knowledge_message(
        client,
        token,
        conversation[
            "id"
        ],
        "Give me the cited answer.",
        document_id=document_id,
    )


    assert send_response.status_code == 200


    history_response = client.get(
        (
            "/api/conversations/"
            f"{conversation['id']}"
            "/messages"
        ),
        headers=auth_headers(
            token
        ),
    )


    assert history_response.status_code == 200

    messages = history_response.json()

    assert len(
        messages
    ) == 2


    assistant = messages[1]

    assert assistant[
        "role"
    ] == "assistant"

    assert assistant[
        "mode"
    ] == "documents"

    assert assistant[
        "document_id"
    ] == document_id

    assert assistant[
        "confidence"
    ] == "high"

    assert assistant[
        "sources"
    ] == [
        {
            "document_id":
                document_id,

            "filename":
                "source.pdf",

            "page": 7,

            "score": 0.88,
        }
    ]


# ==========================================================
# 7. Successful Knowledge Request Is Logged As RAG
# ==========================================================

def test_successful_knowledge_request_logs_rag_version(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "rag.analytics@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )


    mock_safe_guardrails(
        monkeypatch
    )


    monkeypatch.setattr(
        conversations_api,
        "generate_rag_answer",
        lambda question, user_id, document_id=None: {
            "answer": "Logged RAG answer.",
            "sources": [],
        },
    )


    response = send_knowledge_message(
        client,
        token,
        conversation[
            "id"
        ],
        "Log this knowledge request.",
        document_id=None,
    )


    assert response.status_code == 200


    db = SessionLocal()

    try:

        rows = (
            db.query(
                AIRequest
            )
            .filter(
                AIRequest.user_id
                == user[
                    "id"
                ]
            )
            .all()
        )


        assert len(
            rows
        ) == 1

        request_row = rows[0]


        assert request_row.prompt_version == (
            "rag-v1"
        )

        assert request_row.status == (
            "success"
        )

    finally:

        db.close()
