from datetime import datetime, timezone

import app.api.documents as documents_api

from app.db.database import SessionLocal
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
# DB Helper
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
            indexed_at=datetime.now(
                timezone.utc
            ).replace(
                tzinfo=None
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
# Mock External Document Processing
#
# These tests must NOT call real OpenAI or Qdrant.
# ==========================================================

def mock_document_processing(
    monkeypatch,
):

    monkeypatch.setattr(
        documents_api,
        "extract_pdf_pages",
        lambda file_path: [
            {
                "page": 1,
                "text":
                    "ContextForge document test content.",
            }
        ],
    )


    monkeypatch.setattr(
        documents_api,
        "chunk_text",
        lambda text, chunk_size, overlap: [
            text
        ],
    )


    monkeypatch.setattr(
        documents_api,
        "create_embeddings",
        lambda texts: [
            [0.1, 0.2, 0.3]
            for _ in texts
        ],
    )


    monkeypatch.setattr(
        documents_api,
        "store_chunks",
        lambda chunks, embeddings: None,
    )


# ==========================================================
# Authentication
# ==========================================================

def test_documents_require_authentication(
    client,
):

    response = client.get(
        "/api/documents"
    )

    assert response.status_code in {
        401,
        403,
    }


# ==========================================================
# Invalid Extension
# ==========================================================

def test_upload_rejects_non_pdf_extension(
    client,
):

    _, token = create_user(
        client,
        "documents.extension@example.com",
    )


    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "notes.txt",
                b"hello world",
                "text/plain",
            )
        },
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 400

    assert (
        "PDF"
        in response.json()[
            "detail"
        ]
    )


# ==========================================================
# Invalid PDF Signature
# ==========================================================

def test_upload_rejects_fake_pdf(
    client,
):

    _, token = create_user(
        client,
        "documents.fakepdf@example.com",
    )


    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "fake.pdf",
                b"This is not actually a PDF.",
                "application/pdf",
            )
        },
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 400

    assert (
        "valid PDF"
        in response.json()[
            "detail"
        ]
    )


# ==========================================================
# Successful Upload
# ==========================================================

def test_upload_pdf_with_mocked_ai_services(
    client,
    monkeypatch,
    tmp_path,
):

    user, token = create_user(
        client,
        "documents.upload@example.com",
    )


    upload_root = (
        tmp_path
        / "uploads"
    )


    monkeypatch.setattr(
        documents_api.settings,
        "UPLOAD_DIR",
        str(
            upload_root
        ),
    )


    mock_document_processing(
        monkeypatch
    )


    pdf_bytes = (
        b"%PDF-1.4\n"
        b"% ContextForge pytest PDF\n"
    )


    response = client.post(
        "/api/documents/upload",
        files={
            "file": (
                "knowledge.pdf",
                pdf_bytes,
                "application/pdf",
            )
        },
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 201

    payload = response.json()


    assert payload[
        "filename"
    ] == "knowledge.pdf"

    assert payload[
        "status"
    ] == "ready"

    assert payload[
        "pages"
    ] == 1

    assert payload[
        "chunks"
    ] == 1


    document_id = payload[
        "document_id"
    ]


    stored_pdf = (
        upload_root
        / str(
            user[
                "id"
            ]
        )
        / f"{document_id}.pdf"
    )


    assert stored_pdf.exists()


    list_response = client.get(
        "/api/documents",
        headers=auth_headers(
            token
        ),
    )


    assert list_response.status_code == 200

    documents = list_response.json()

    assert len(
        documents
    ) == 1

    assert documents[0][
        "id"
    ] == document_id

    assert documents[0][
        "status"
    ] == "ready"


# ==========================================================
# List Isolation
# ==========================================================

def test_user_only_sees_own_documents(
    client,
):

    owner, owner_token = create_user(
        client,
        "documents.owner@example.com",
    )

    other, other_token = create_user(
        client,
        "documents.other@example.com",
    )


    owner_document_id = insert_document(
        owner[
            "id"
        ],
        "owner.pdf",
    )


    insert_document(
        other[
            "id"
        ],
        "other.pdf",
    )


    owner_response = client.get(
        "/api/documents",
        headers=auth_headers(
            owner_token
        ),
    )


    assert owner_response.status_code == 200

    owner_documents = owner_response.json()

    assert len(
        owner_documents
    ) == 1

    assert owner_documents[0][
        "id"
    ] == owner_document_id

    assert owner_documents[0][
        "filename"
    ] == "owner.pdf"


    other_response = client.get(
        "/api/documents",
        headers=auth_headers(
            other_token
        ),
    )


    assert other_response.status_code == 200

    other_documents = other_response.json()

    assert len(
        other_documents
    ) == 1

    assert other_documents[0][
        "filename"
    ] == "other.pdf"


# ==========================================================
# Delete Own Document
# ==========================================================

def test_user_can_delete_own_document(
    client,
    monkeypatch,
    tmp_path,
):

    user, token = create_user(
        client,
        "documents.delete@example.com",
    )


    document_id = insert_document(
        user[
            "id"
        ],
        "delete-me.pdf",
    )


    monkeypatch.setattr(
        documents_api.settings,
        "UPLOAD_DIR",
        str(
            tmp_path
            / "uploads"
        ),
    )


    monkeypatch.setattr(
        documents_api,
        "delete_document_vectors",
        lambda user_id, document_id: None,
    )


    response = client.delete(
        (
            "/api/documents/"
            f"{document_id}"
        ),
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 200

    assert response.json()[
        "message"
    ] == "Document deleted successfully"


    list_response = client.get(
        "/api/documents",
        headers=auth_headers(
            token
        ),
    )


    assert list_response.status_code == 200

    assert list_response.json() == []


# ==========================================================
# Delete Isolation
# ==========================================================

def test_user_cannot_delete_another_users_document(
    client,
):

    owner, _ = create_user(
        client,
        "documents.delete.owner@example.com",
    )

    _, attacker_token = create_user(
        client,
        "documents.delete.attacker@example.com",
    )


    document_id = insert_document(
        owner[
            "id"
        ],
        "private.pdf",
    )


    response = client.delete(
        (
            "/api/documents/"
            f"{document_id}"
        ),
        headers=auth_headers(
            attacker_token
        ),
    )


    assert response.status_code == 404


# ==========================================================
# Re-index Isolation
# ==========================================================

def test_user_cannot_reindex_another_users_document(
    client,
):

    owner, _ = create_user(
        client,
        "documents.reindex.owner@example.com",
    )

    _, attacker_token = create_user(
        client,
        "documents.reindex.attacker@example.com",
    )


    document_id = insert_document(
        owner[
            "id"
        ],
        "private-reindex.pdf",
    )


    response = client.post(
        (
            "/api/documents/"
            f"{document_id}"
            "/reindex"
        ),
        json={
            "chunk_size": 1200,
            "chunk_overlap": 150,
        },
        headers=auth_headers(
            attacker_token
        ),
    )


    assert response.status_code == 404


# ==========================================================
# Re-index Missing Original PDF
# ==========================================================

def test_reindex_requires_original_pdf(
    client,
    monkeypatch,
    tmp_path,
):

    user, token = create_user(
        client,
        "documents.reindex.missing@example.com",
    )


    document_id = insert_document(
        user[
            "id"
        ],
        "missing-original.pdf",
    )


    monkeypatch.setattr(
        documents_api.settings,
        "UPLOAD_DIR",
        str(
            tmp_path
            / "uploads"
        ),
    )


    response = client.post(
        (
            "/api/documents/"
            f"{document_id}"
            "/reindex"
        ),
        json={
            "chunk_size": 1200,
            "chunk_overlap": 150,
        },
        headers=auth_headers(
            token
        ),
    )


    assert response.status_code == 404

    assert (
        "Original PDF"
        in response.json()[
            "detail"
        ]
    )
