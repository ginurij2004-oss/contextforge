from uuid import uuid4

from qdrant_client import (
    QdrantClient,
    models,
)

from app.core.config import settings


client = QdrantClient(
    url=settings.QDRANT_URL,
    api_key=settings.QDRANT_API_KEY or None,
    timeout=20,
)


def ensure_collection(
    vector_size: int
):

    exists = client.collection_exists(
        collection_name=(
            settings.QDRANT_COLLECTION
        )
    )

    if exists:
        return

    client.create_collection(
        collection_name=(
            settings.QDRANT_COLLECTION
        ),
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )
def ensure_payload_indexes():
    collection_name = settings.QDRANT_COLLECTION

    info = client.get_collection(
        collection_name=collection_name
    )

    payload_schema = (
        info.payload_schema or {}
    )

    if "user_id" not in payload_schema:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="user_id",
            field_schema=models.PayloadSchemaType.INTEGER,
            wait=True,
        )

    if "document_id" not in payload_schema:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="document_id",
            field_schema=models.PayloadSchemaType.INTEGER,
            wait=True,
        )

def store_chunks(
    chunks: list[dict],
    embeddings: list[list[float]],
):

    if not chunks:
        return

    if not embeddings:
        return

    ensure_collection(
        vector_size=len(
            embeddings[0]
        )
    )

    points = []

    for chunk, embedding in zip(
        chunks,
        embeddings
    ):

        points.append(
            models.PointStruct(
                id=str(uuid4()),
                vector=embedding,
                payload=chunk,
            )
        )

    client.upsert(
        collection_name=(
            settings.QDRANT_COLLECTION
        ),
        points=points,
        wait=True,
    )

def delete_document_vectors(
    user_id: int,
    document_id: int,
):

    client.delete(
        collection_name=(
            settings.QDRANT_COLLECTION
        ),

        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(
                            value=user_id
                        ),
                    ),

                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(
                            value=document_id
                        ),
                    ),
                ]
            )
        ),

        wait=True,
    )