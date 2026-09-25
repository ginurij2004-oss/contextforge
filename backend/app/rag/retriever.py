from qdrant_client import (
    QdrantClient,
    models,
)

from app.core.config import settings

from app.rag.embeddings import (
    create_embeddings,
)


# ==========================================================
# Qdrant Client
# ==========================================================

client = QdrantClient(
    url=settings.QDRANT_URL
)


# ==========================================================
# Retrieve Relevant Document Chunks
# ==========================================================

def retrieve_chunks(
    query: str,
    user_id: int,
    limit: int | None = None,
    score_threshold: float | None = None,
    document_id: int | None = None,
):

    # ======================================================
    # 1. Resolve Retrieval Settings
    # ======================================================

    top_k = (
        limit
        if limit is not None
        else settings.RAG_TOP_K
    )

    threshold = (
        score_threshold
        if score_threshold is not None
        else settings.RAG_SCORE_THRESHOLD
    )


    # ======================================================
    # 2. Create Query Embedding
    # ======================================================

    embeddings = create_embeddings(
        [query]
    )

    if not embeddings:
        return []

    query_vector = embeddings[0]


    # ======================================================
    # 3. Build Qdrant Security Filter
    # ======================================================

    filter_conditions = [

        models.FieldCondition(
            key="user_id",
            match=models.MatchValue(
                value=user_id
            ),
        )

    ]


    # ------------------------------------------------------
    # If document_id is provided,
    # restrict retrieval to that document.
    # ------------------------------------------------------

    if document_id is not None:

        filter_conditions.append(

            models.FieldCondition(
                key="document_id",
                match=models.MatchValue(
                    value=document_id
                ),
            )

        )


    # ======================================================
    # 4. Search Qdrant
    # ======================================================

    response = client.query_points(

        collection_name=
            settings.QDRANT_COLLECTION,

        query=
            query_vector,

        query_filter=models.Filter(
            must=filter_conditions
        ),

        limit=
            top_k,

        score_threshold=
            threshold,

        with_payload=
            True,
    )


    # ======================================================
    # 5. Normalize Results
    # ======================================================

    results = []


    for point in response.points:

        payload = (
            point.payload
            or {}
        )


        results.append({

            "score":
                float(point.score),

            "document_id":
                payload.get(
                    "document_id"
                ),

            "filename":
                payload.get(
                    "filename",
                    "Unknown document",
                ),

            "page":
                payload.get(
                    "page"
                ),

            "chunk_index":
                payload.get(
                    "chunk_index"
                ),

            "text":
                payload.get(
                    "text",
                    "",
                ),
        })


    return results