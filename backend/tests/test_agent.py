from datetime import datetime, timezone

import app.api.conversations as conversations_api

from app.db.database import SessionLocal
from app.models.ai_request import AIRequest
from app.models.document import Document
from app.models.action_request import ActionRequest


TEST_PASSWORD = "StrongPass123!"


# ==========================================================
# Small Fake Agent Result
#
# The real run_agent() returns a Pydantic model and the
# conversation endpoint calls .model_dump().
# This fake gives us the same interface without OpenAI.
# ==========================================================

class FakeAgentResult:

    def __init__(
        self,
        *,
        answer: str,
        used_tools=None,
        sources=None,
        action_items=None,
        proposed_actions=None,
        confidence: str = "high",
    ):

        self.payload = {
            "answer":
                answer,

            "used_tools":
                used_tools or [],

            "sources":
                sources or [],

            "action_items":
                action_items or [],

            "proposed_actions":
                proposed_actions or [],

            "confidence":
                confidence,
        }


    def model_dump(
        self,
    ):

        return self.payload


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
# Conversation Helper
# ==========================================================

def create_conversation(
    client,
    token: str,
    title: str = "Agent Test Conversation",
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
# Document Helper
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
# Guardrails Helper
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
# Send Agent Message Helper
# ==========================================================

def send_agent_message(
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
            "content":
                content,

            "mode":
                "agent",

            "document_id":
                document_id,
        },
        headers=auth_headers(
            token
        ),
    )


# ==========================================================
# 1. Agent Receives Correct User + Selected Document Scope
# ==========================================================

def test_agent_receives_user_and_document_scope(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "agent.scope@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )

    document_id = insert_document(
        user[
            "id"
        ],
        "agent-source.pdf",
    )


    mock_safe_guardrails(
        monkeypatch
    )


    captured = {}


    def fake_run_agent(
        message,
        user_id,
        db,
        document_id=None,
    ):

        captured[
            "message"
        ] = message

        captured[
            "user_id"
        ] = user_id

        captured[
            "document_id"
        ] = document_id

        return FakeAgentResult(
            answer=(
                "I analyzed the selected "
                "document and created a plan."
            ),
            used_tools=[
                "search_knowledge_base",
            ],
            sources=[
                {
                    "document_id":
                        document_id,

                    "filename":
                        "agent-source.pdf",

                    "page":
                        2,

                    "score":
                        0.94,
                }
            ],
            action_items=[
                {
                    "title":
                        "Review finding",

                    "description":
                        "Validate the first recommendation.",

                    "priority":
                        "high",
                }
            ],
            confidence="high",
        )


    monkeypatch.setattr(
        conversations_api,
        "run_agent",
        fake_run_agent,
    )


    response = send_agent_message(
        client,
        token,
        conversation[
            "id"
        ],
        "Analyze this document and make a plan.",
        document_id=document_id,
    )


    assert response.status_code == 200

    assert captured[
        "message"
    ] == (
        "Analyze this document and make a plan."
    )

    assert captured[
        "user_id"
    ] == user[
        "id"
    ]

    assert captured[
        "document_id"
    ] == document_id


    assistant = response.json()[
        "assistant_message"
    ]


    assert assistant[
        "mode"
    ] == "agent"

    assert assistant[
        "document_id"
    ] == document_id

    assert assistant[
        "confidence"
    ] == "high"


# ==========================================================
# 2. Agent Can Work Across All Current User Documents
# ==========================================================

def test_agent_all_documents_scope_passes_none(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "agent.all@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )


    mock_safe_guardrails(
        monkeypatch
    )


    captured = {}


    def fake_run_agent(
        message,
        user_id,
        db,
        document_id=None,
    ):

        captured[
            "user_id"
        ] = user_id

        captured[
            "document_id"
        ] = document_id

        return FakeAgentResult(
            answer="Cross-document analysis complete.",
            used_tools=[
                "list_documents",
                "search_knowledge_base",
            ],
            confidence="medium",
        )


    monkeypatch.setattr(
        conversations_api,
        "run_agent",
        fake_run_agent,
    )


    response = send_agent_message(
        client,
        token,
        conversation[
            "id"
        ],
        "Compare my knowledge base.",
        document_id=None,
    )


    assert response.status_code == 200

    assert captured[
        "user_id"
    ] == user[
        "id"
    ]

    assert captured[
        "document_id"
    ] is None


    assistant = response.json()[
        "assistant_message"
    ]


    assert assistant[
        "mode"
    ] == "agent"

    assert assistant[
        "document_id"
    ] is None

    assert assistant[
        "confidence"
    ] == "medium"


# ==========================================================
# 3. Tools, Sources and Action Items Persist
# ==========================================================

def test_agent_metadata_is_persisted_in_history(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "agent.persistence@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )

    document_id = insert_document(
        user[
            "id"
        ],
        "persisted-source.pdf",
    )


    mock_safe_guardrails(
        monkeypatch
    )


    monkeypatch.setattr(
        conversations_api,
        "run_agent",
        lambda message, user_id, db, document_id=None:
            FakeAgentResult(
                answer="Persistent agent result.",
                used_tools=[
                    "list_documents",
                    "search_knowledge_base",
                    # Duplicate is intentional.
                    # Backend should save each tool once.
                    "search_knowledge_base",
                ],
                sources=[
                    {
                        "document_id":
                            document_id_for_source,

                        "filename":
                            "persisted-source.pdf",

                        "page":
                            4,

                        "score":
                            0.89,
                    }
                ],
                action_items=[
                    {
                        "title":
                            "Confirm requirement",

                        "description":
                            "Check the cited requirement.",

                        "priority":
                            "high",
                    },
                    {
                        "title":
                            "Prepare implementation",

                        "description":
                            "Create the implementation plan.",

                        "priority":
                            "medium",
                    },
                ],
                confidence="high",
            ),
    )


    document_id_for_source = (
        document_id
    )


    send_response = send_agent_message(
        client,
        token,
        conversation[
            "id"
        ],
        "Analyze and create action items.",
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
    ] == "agent"

    assert assistant[
        "document_id"
    ] == document_id

    assert assistant[
        "confidence"
    ] == "high"


    assert assistant[
        "used_tools"
    ] == [
        "list_documents",
        "search_knowledge_base",
    ]


    assert assistant[
        "sources"
    ] == [
        {
            "document_id":
                document_id,

            "filename":
                "persisted-source.pdf",

            "page":
                4,

            "score":
                0.89,
        }
    ]


    assert assistant[
        "action_items"
    ] == [
        {
            "title":
                "Confirm requirement",

            "description":
                "Check the cited requirement.",

            "priority":
                "high",
        },
        {
            "title":
                "Prepare implementation",

            "description":
                "Create the implementation plan.",

            "priority":
                "medium",
        },
    ]


# ==========================================================
# 4. User Cannot Run Agent Against Another User's Document
# ==========================================================

def test_agent_cannot_use_another_users_document(
    client,
    monkeypatch,
):

    owner, _ = create_user(
        client,
        "agent.owner@example.com",
    )

    _, attacker_token = create_user(
        client,
        "agent.attacker@example.com",
    )

    conversation = create_conversation(
        client,
        attacker_token,
    )


    private_document_id = insert_document(
        owner[
            "id"
        ],
        "owner-private.pdf",
    )


    mock_safe_guardrails(
        monkeypatch
    )


    agent_called = {
        "value":
            False,
    }


    def fake_run_agent(
        message,
        user_id,
        db,
        document_id=None,
    ):

        agent_called[
            "value"
        ] = True

        return FakeAgentResult(
            answer="This must never execute."
        )


    monkeypatch.setattr(
        conversations_api,
        "run_agent",
        fake_run_agent,
    )


    response = send_agent_message(
        client,
        attacker_token,
        conversation[
            "id"
        ],
        "Analyze the private document.",
        document_id=
            private_document_id,
    )


    assert response.status_code == 404

    assert response.json()[
        "detail"
    ] == "Document not found"

    # Ownership validation must stop execution
    # before run_agent() is called.
    assert agent_called[
        "value"
    ] is False


# ==========================================================
# 5. Non-ready Document Is Rejected Before Agent Runs
# ==========================================================

def test_agent_rejects_non_ready_document(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "agent.processing@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )


    document_id = insert_document(
        user[
            "id"
        ],
        "processing.pdf",
        status="processing",
    )


    mock_safe_guardrails(
        monkeypatch
    )


    agent_called = {
        "value":
            False,
    }


    def fake_run_agent(
        message,
        user_id,
        db,
        document_id=None,
    ):

        agent_called[
            "value"
        ] = True

        return FakeAgentResult(
            answer="Should not execute."
        )


    monkeypatch.setattr(
        conversations_api,
        "run_agent",
        fake_run_agent,
    )


    response = send_agent_message(
        client,
        token,
        conversation[
            "id"
        ],
        "Analyze this document.",
        document_id=document_id,
    )


    assert response.status_code == 400

    assert (
        "must be ready"
        in response.json()[
            "detail"
        ].lower()
    )

    assert agent_called[
        "value"
    ] is False


# ==========================================================
# 6. Successful Agent Request Logs agent-v1
# ==========================================================

def test_successful_agent_request_logs_agent_version(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "agent.logging@example.com",
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
        "run_agent",
        lambda message, user_id, db, document_id=None:
            FakeAgentResult(
                answer="Agent request completed.",
                confidence="high",
            ),
    )


    response = send_agent_message(
        client,
        token,
        conversation[
            "id"
        ],
        "Create a plan.",
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
            "agent-v1"
        )

        assert request_row.status == (
            "success"
        )

    finally:

        db.close()


# ==========================================================
# 7. Agent Failure Returns 502 + Logs Failed agent-v1
# ==========================================================

def test_agent_failure_is_logged(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "agent.failure@example.com",
    )

    conversation = create_conversation(
        client,
        token,
    )


    mock_safe_guardrails(
        monkeypatch
    )


    def failing_run_agent(
        message,
        user_id,
        db,
        document_id=None,
    ):

        raise RuntimeError(
            "Simulated agent provider failure"
        )


    monkeypatch.setattr(
        conversations_api,
        "run_agent",
        failing_run_agent,
    )


    response = send_agent_message(
        client,
        token,
        conversation[
            "id"
        ],
        "This request should fail safely.",
    )


    assert response.status_code == 502

    assert response.json()[
        "detail"
    ] == "AI provider request failed"


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


        failed_request = rows[0]


        assert failed_request.prompt_version == (
            "agent-v1"
        )

        assert failed_request.status == (
            "failed"
        )

    finally:

        db.close()


# ==========================================================
# 8. Agent Email Proposal Creates Pending Action Request
# ==========================================================

def test_agent_email_proposal_creates_pending_action_request(
    client,
    monkeypatch,
):

    user, token = create_user(
        client,
        "agent.email.action@example.com",
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
        "run_agent",
        lambda message, user_id, db, document_id=None:
            FakeAgentResult(

                answer=(
                    "I prepared the email draft. "
                    "It is waiting for approval "
                    "in the Action Center."
                ),

                proposed_actions=[
                    {
                        "action_type":
                            "email",

                        "title":
                            "Supplier delivery follow-up",

                        "payload": {
                            "to":
                                "supplier@example.com",

                            "subject":
                                "Delivery Confirmation",

                            "body": (
                                "Hi, could you please "
                                "confirm the delivery "
                                "date by Friday?"
                            ),
                        },
                    }
                ],

                confidence="high",
            ),
    )


    response = send_agent_message(
        client,
        token,
        conversation[
            "id"
        ],
        (
            "Draft an email to "
            "supplier@example.com "
            "asking them to confirm "
            "delivery by Friday."
        ),
    )


    assert response.status_code == 200


    assistant = response.json()[
        "assistant_message"
    ]


    db = SessionLocal()

    try:

        rows = (
            db.query(
                ActionRequest
            )
            .filter(
                ActionRequest.user_id
                == user[
                    "id"
                ]
            )
            .all()
        )


        assert len(
            rows
        ) == 1


        action = rows[0]


        assert action.status == (
            "pending"
        )


        assert action.action_type == (
            "email"
        )


        assert action.message_id == (
            assistant[
                "id"
            ]
        )


        assert action.title == (
            "Supplier delivery follow-up"
        )


        assert action.payload[
            "to"
        ] == (
            "supplier@example.com"
        )


        assert action.payload[
            "subject"
        ] == (
            "Delivery Confirmation"
        )


        assert (
            "confirm the delivery"
            in action.payload[
                "body"
            ].lower()
        )

    finally:

        db.close()


    # ------------------------------------------------------
    # Also prove the Action Center API can see the new draft.
    # ------------------------------------------------------

    actions_response = client.get(
        "/api/actions",
        params={
            "status":
                "pending",
        },
        headers=auth_headers(
            token
        ),
    )


    assert actions_response.status_code == 200


    pending_actions = (
        actions_response.json()
    )


    assert any(

        action[
            "title"
        ]
        == "Supplier delivery follow-up"

        and action[
            "status"
        ]
        == "pending"

        for action
        in pending_actions
    )
