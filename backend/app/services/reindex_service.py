from pathlib import Path

from app.core.config import settings

from app.models.document import Document

from app.services.document_service import (
    extract_pdf_pages,
)

from app.rag.chunker import (
    chunk_text,
)

from app.rag.embeddings import (
    create_embeddings,
)

from app.rag.qdrant_store import (
    delete_document_vectors,
    store_chunks,
)


# ==========================================================
# Re-index Document Vectors
# ==========================================================

def rebuild_document_index(
    document: Document,
    user_id: int,
    chunk_size: int,
    chunk_overlap: int,
):

    # ======================================================
    # 1. Validate Configuration
    # ======================================================

    if chunk_size <= 0:

        raise ValueError(
            "chunk_size must be greater than 0"
        )


    if chunk_overlap < 0:

        raise ValueError(
            "chunk_overlap cannot be negative"
        )


    if chunk_overlap >= chunk_size:

        raise ValueError(
            "chunk_overlap must be smaller than chunk_size"
        )


    # ======================================================
    # 2. Find Physical PDF
    # ======================================================

    file_path = (
        Path(settings.UPLOAD_DIR)
        / str(user_id)
        / f"{document.id}.pdf"
    )


    if not file_path.exists():

        raise FileNotFoundError(
            "Original PDF file was not found"
        )


    # ======================================================
    # 3. Extract Pages
    # ======================================================

    pages = extract_pdf_pages(
        file_path
    )


    if not pages:

        raise ValueError(
            "No pages could be extracted from the PDF"
        )


    # ======================================================
    # 4. Build New Chunks
    # ======================================================

    new_chunks = []


    for page in pages:

        page_chunks = chunk_text(
            page["text"],

            chunk_size=
                chunk_size,

            overlap=
                chunk_overlap,
        )


        for (
            index,
            text
        ) in enumerate(
            page_chunks
        ):

            new_chunks.append({

                "user_id":
                    user_id,

                "document_id":
                    document.id,

                "filename":
                    document.filename,

                "page":
                    page["page"],

                "chunk_index":
                    index,

                "text":
                    text,
            })


    if not new_chunks:

        raise ValueError(
            "No extractable text was found in the PDF"
        )


    # ======================================================
    # 5. Generate Embeddings
    #
    # Do this BEFORE deleting existing vectors.
    # ======================================================

    texts = [

        chunk["text"]

        for chunk
        in new_chunks
    ]


    embeddings = create_embeddings(
        texts
    )


    if (
        len(embeddings)
        != len(new_chunks)
    ):

        raise ValueError(
            "Embedding count does not match chunk count"
        )


    # ======================================================
    # 6. Delete Old Vectors
    # ======================================================

    delete_document_vectors(
        user_id=user_id,
        document_id=document.id,
    )


    # ======================================================
    # 7. Store New Vectors
    # ======================================================

    store_chunks(
        new_chunks,
        embeddings,
    )


    # ======================================================
    # 8. Result
    # ======================================================

    return {

        "pages":
            len(pages),

        "chunks":
            len(new_chunks),

        "chunk_size":
            chunk_size,

        "chunk_overlap":
            chunk_overlap,
    }