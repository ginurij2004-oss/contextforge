import traceback
from datetime import datetime, timezone
from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    UploadFile,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_current_user

from app.core.config import settings
from app.core.rate_limit import limiter

from app.db.database import get_db

from app.models.user import User
from app.models.document import Document

from app.schemas.document import (
    DocumentUploadResponse,
    DocumentResponse,
)

from app.schemas.reindex import (
    ReindexDocumentRequest,
    ReindexDocumentResponse,
)

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
    store_chunks,
    delete_document_vectors,
)


# ==========================================================
# Configuration
# ==========================================================

MAX_PDF_BYTES = (
    settings.MAX_PDF_SIZE_MB
    * 1024
    * 1024
)


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ==========================================================
# Helper:
# Create indexing timestamp
# ==========================================================

def get_indexed_timestamp() -> datetime:
    return (
        datetime.now(
            timezone.utc
        )
        .replace(
            tzinfo=None
        )
    )


# ==========================================================
# Upload Document
# ==========================================================

@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("5/minute")
def upload_document(
    request: Request,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    # Keep these defined from the beginning so error cleanup
    # works even if the failure happens very early.
    document = None
    file_path = None
    stage = "starting upload"

    try:

        # ==================================================
        # 1. Validate Filename
        # ==================================================

        stage = "validating filename"

        if not file.filename:

            raise HTTPException(
                status_code=400,
                detail="Missing filename",
            )


        # ==================================================
        # 2. Validate File Extension
        # ==================================================

        stage = "validating file extension"

        extension = (
            Path(file.filename)
            .suffix
            .lower()
        )


        if extension != ".pdf":

            raise HTTPException(
                status_code=400,
                detail=(
                    "Only PDF files are supported"
                ),
            )


        # ==================================================
        # 3. Validate MIME Type
        # ==================================================

        stage = "validating MIME type"

        if (
            file.content_type
            != "application/pdf"
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid PDF MIME type",
            )


        # ==================================================
        # 4. Validate Reported File Size
        # ==================================================

        stage = "validating reported file size"

        if (
            file.size is not None
            and file.size > MAX_PDF_BYTES
        ):

            raise HTTPException(
                status_code=413,
                detail=(
                    f"PDF must be smaller than "
                    f"{settings.MAX_PDF_SIZE_MB} MB"
                ),
            )


        # ==================================================
        # 5. Validate PDF Signature
        # ==================================================

        stage = "validating PDF signature"

        file.file.seek(0)

        header = file.file.read(5)

        file.file.seek(0)


        if header != b"%PDF-":

            raise HTTPException(
                status_code=400,
                detail=(
                    "Uploaded file is not "
                    "a valid PDF"
                ),
            )


        # ==================================================
        # 6. Create PostgreSQL Document Record
        # ==================================================

        stage = "creating PostgreSQL document record"

        document = Document(
            user_id=current_user.id,
            filename=file.filename,
            file_type="pdf",
            status="processing",

            indexed_chunk_size=None,
            indexed_chunk_overlap=None,
            indexed_at=None,
        )


        db.add(document)

        db.commit()

        db.refresh(document)


        # ==================================================
        # 7. Create User Upload Directory
        # ==================================================

        stage = "creating upload directory"

        upload_directory = (
            Path(settings.UPLOAD_DIR)
            / str(current_user.id)
        )


        upload_directory.mkdir(
            parents=True,
            exist_ok=True,
        )


        # ==================================================
        # 8. Build Physical PDF Path
        # ==================================================

        stage = "building PDF file path"

        file_path = (
            upload_directory
            / f"{document.id}.pdf"
        )


        # ==================================================
        # 9. Save PDF With Actual Size Protection
        # ==================================================

        stage = "saving PDF to disk"

        total_size = 0


        with open(
            file_path,
            "wb"
        ) as buffer:

            while True:

                file_chunk = (
                    file.file.read(
                        1024 * 1024
                    )
                )


                if not file_chunk:
                    break


                total_size += len(
                    file_chunk
                )


                if (
                    total_size
                    > MAX_PDF_BYTES
                ):

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"PDF must be smaller "
                            f"than "
                            f"{settings.MAX_PDF_SIZE_MB} MB"
                        ),
                    )


                buffer.write(
                    file_chunk
                )


        # ==================================================
        # 10. Extract PDF Pages
        # ==================================================

        stage = "extracting PDF pages"

        pages = extract_pdf_pages(
            file_path
        )


        # ==================================================
        # 11. Chunk Extracted Text
        # ==================================================

        stage = "chunking extracted text"

        all_chunks = []


        for page in pages:

            page_chunks = chunk_text(
                page["text"],

                chunk_size=
                    settings.RAG_CHUNK_SIZE,

                overlap=
                    settings.RAG_CHUNK_OVERLAP,
            )


            for (
                index,
                text
            ) in enumerate(
                page_chunks
            ):

                all_chunks.append({

                    "user_id":
                        current_user.id,

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


        # ==================================================
        # 12. Ensure PDF Contains Extractable Text
        # ==================================================

        stage = "checking extracted text"

        if not all_chunks:

            raise ValueError(
                "No extractable text "
                "was found in the PDF"
            )


        # ==================================================
        # 13. Prepare Texts
        # ==================================================

        stage = "preparing embedding texts"

        texts = [

            chunk["text"]

            for chunk
            in all_chunks
        ]


        # ==================================================
        # 14. Generate Embeddings
        # ==================================================

        stage = "generating embeddings"

        embeddings = create_embeddings(
            texts
        )


        if (
            len(embeddings)
            != len(all_chunks)
        ):

            raise ValueError(
                "Embedding count does not "
                "match chunk count"
            )


        # ==================================================
        # 15. Store Vectors in Qdrant
        # ==================================================

        stage = "storing vectors in Qdrant"

        store_chunks(
            all_chunks,
            embeddings,
        )


        # ==================================================
        # 16. Save Actual Index Configuration
        # ==================================================

        stage = "saving final document status"

        document.status = "ready"

        document.indexed_chunk_size = (
            settings.RAG_CHUNK_SIZE
        )

        document.indexed_chunk_overlap = (
            settings.RAG_CHUNK_OVERLAP
        )

        document.indexed_at = (
            get_indexed_timestamp()
        )


        db.commit()

        db.refresh(document)


        # ==================================================
        # 17. Return Upload Result
        # ==================================================

        stage = "returning upload response"

        return {

            "document_id":
                document.id,

            "filename":
                document.filename,

            "status":
                document.status,

            "pages":
                len(pages),

            "chunks":
                len(all_chunks),
        }


    # ======================================================
    # Preserve Expected HTTP Errors
    # ======================================================

    except HTTPException as exc:

        # Make sure a failed transaction does not leave
        # the SQLAlchemy session unusable.
        db.rollback()


        # Only mark a row as failed if it was actually
        # inserted and received an ID.
        if (
            document is not None
            and getattr(
                document,
                "id",
                None
            ) is not None
        ):

            try:

                document.status = "failed"

                db.add(document)

                db.commit()

            except Exception:

                db.rollback()


        # Remove partially written file if one exists.
        if (
            file_path is not None
            and file_path.exists()
        ):

            try:

                file_path.unlink()

            except Exception:

                pass


        print("\n")
        print("=" * 80)
        print("DOCUMENT UPLOAD HTTP ERROR")
        print("=" * 80)
        print("Stage:", stage)
        print("Status code:", exc.status_code)
        print("Detail:", exc.detail)
        print("=" * 80)
        print("\n")


        raise


    # ======================================================
    # Handle Unexpected Upload / Processing Errors
    # ======================================================

    except Exception as exc:

        # Preserve the original exception first.
        original_error_type = (
            type(exc).__name__
        )

        original_error_message = (
            str(exc)
        )


        # A failed commit can leave the session in a
        # pending rollback state.
        try:

            db.rollback()

        except Exception:

            pass


        # If the document row exists, mark it as failed.
        if (
            document is not None
            and getattr(
                document,
                "id",
                None
            ) is not None
        ):

            try:

                document.status = "failed"

                db.add(document)

                db.commit()

            except Exception as status_exc:

                db.rollback()

                print(
                    "FAILED TO MARK DOCUMENT AS FAILED:",
                    type(status_exc).__name__,
                    str(status_exc),
                )


            # Clean up vectors if they were partially stored.
            try:

                delete_document_vectors(
                    user_id=current_user.id,
                    document_id=document.id,
                )

            except Exception as vector_cleanup_exc:

                print(
                    "VECTOR CLEANUP WARNING:",
                    type(vector_cleanup_exc).__name__,
                    str(vector_cleanup_exc),
                )


        # Clean up partially written PDF.
        if (
            file_path is not None
            and file_path.exists()
        ):

            try:

                file_path.unlink()

            except Exception as file_cleanup_exc:

                print(
                    "FILE CLEANUP WARNING:",
                    type(file_cleanup_exc).__name__,
                    str(file_cleanup_exc),
                )


        print("\n")
        print("=" * 80)
        print("DOCUMENT UPLOAD CRASH")
        print("=" * 80)

        print(
            "Stage:",
            stage,
        )

        print(
            "Exception type:",
            original_error_type,
        )

        print(
            "Exception message:",
            original_error_message,
        )

        print("-" * 80)

        traceback.print_exc()

        print("=" * 80)
        print("\n")


        # Development-only detailed error.
        # Replace with a generic message before production.
        raise HTTPException(
            status_code=500,
            detail=(
                f"Document upload failed during "
                f"'{stage}': "
                f"{original_error_type}: "
                f"{original_error_message}"
            ),
        )


# ==========================================================
# Get Documents
# ==========================================================

@router.get(
    "",
    response_model=list[
        DocumentResponse
    ],
)
def get_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    statement = (
        select(Document)

        .where(
            Document.user_id
            == current_user.id
        )

        .order_by(
            Document.id.desc()
        )
    )


    documents = list(

        db.scalars(
            statement
        ).all()
    )


    return documents


# ==========================================================
# Re-index Document
# ==========================================================

@router.post(
    "/{document_id}/reindex",
    response_model=
        ReindexDocumentResponse,
)
@limiter.limit("5/minute")
def reindex_document(
    request: Request,

    document_id: int,

    data: ReindexDocumentRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(
        get_current_user
    ),
):

    # ======================================================
    # 1. Find Document Owned By Current User
    # ======================================================

    statement = select(
        Document
    ).where(
        Document.id == document_id,

        Document.user_id
        == current_user.id,
    )


    document = db.scalar(
        statement
    )


    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )


    # ======================================================
    # 2. Find Original Physical PDF
    # ======================================================

    file_path = (

        Path(
            settings.UPLOAD_DIR
        )

        / str(
            current_user.id
        )

        / f"{document.id}.pdf"
    )


    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail=(
                "Original PDF file "
                "was not found"
            ),
        )


    # ======================================================
    # 3. Mark Document as Processing
    # ======================================================

    document.status = (
        "processing"
    )


    db.commit()


    try:

        # ==================================================
        # 4. Extract Original PDF
        # ==================================================

        pages = extract_pdf_pages(
            file_path
        )


        # ==================================================
        # 5. Build New Chunks
        # ==================================================

        new_chunks = []


        for page in pages:

            page_chunks = chunk_text(
                page["text"],

                chunk_size=
                    data.chunk_size,

                overlap=
                    data.chunk_overlap,
            )


            for (
                index,
                text
            ) in enumerate(
                page_chunks
            ):

                new_chunks.append({

                    "user_id":
                        current_user.id,

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


        # ==================================================
        # 6. Ensure PDF Has Extractable Text
        # ==================================================

        if not new_chunks:

            raise ValueError(
                "No extractable text "
                "was found in the PDF"
            )


        # ==================================================
        # 7. Generate New Embeddings
        #
        # Do this BEFORE deleting old vectors.
        # ==================================================

        texts = [

            chunk["text"]

            for chunk
            in new_chunks
        ]


        new_embeddings = (
            create_embeddings(
                texts
            )
        )


        if (
            len(new_embeddings)
            != len(new_chunks)
        ):

            raise ValueError(
                "Embedding count does not "
                "match chunk count"
            )


        # ==================================================
        # 8. Delete Previous Vectors
        # ==================================================

        delete_document_vectors(

            user_id=
                current_user.id,

            document_id=
                document.id,
        )


        # ==================================================
        # 9. Store New Vectors
        # ==================================================

        store_chunks(
            new_chunks,
            new_embeddings,
        )


        # ==================================================
        # 10. Save New Index Configuration
        # ==================================================

        document.status = (
            "ready"
        )

        document.indexed_chunk_size = (
            data.chunk_size
        )

        document.indexed_chunk_overlap = (
            data.chunk_overlap
        )

        document.indexed_at = (
            get_indexed_timestamp()
        )


        db.commit()

        db.refresh(document)


        # ==================================================
        # 11. Return Result
        # ==================================================

        return {

            "document_id":
                document.id,

            "filename":
                document.filename,

            "status":
                document.status,

            "pages":
                len(pages),

            "chunks":
                len(new_chunks),

            "chunk_size":
                data.chunk_size,

            "chunk_overlap":
                data.chunk_overlap,
        }


    # ======================================================
    # Preserve HTTP Errors
    # ======================================================

    except HTTPException:

        document.status = (
            "failed"
        )

        db.commit()

        raise


    # ======================================================
    # Handle Unexpected Re-index Errors
    # ======================================================

    except Exception as exc:

        document.status = (
            "failed"
        )


        db.commit()


        print(
            "REINDEX ERROR:",
            type(exc).__name__,
            str(exc),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Document re-indexing failed"
            ),
        )


# ==========================================================
# Delete Document
# ==========================================================

@router.delete(
    "/{document_id}",
)
def delete_document(
    document_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    # ======================================================
    # 1. Find Document Owned By Current User
    # ======================================================

    statement = select(
        Document
    ).where(
        Document.id == document_id,

        Document.user_id
        == current_user.id,
    )


    document = db.scalar(
        statement
    )


    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )


    # ======================================================
    # 2. Delete Qdrant Vectors
    # ======================================================

    try:

        delete_document_vectors(

            user_id=
                current_user.id,

            document_id=
                document.id,
        )


    except Exception as exc:

        print(
            "QDRANT DELETE ERROR:",
            type(exc).__name__,
            str(exc),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to delete "
                "document vectors"
            ),
        )


    # ======================================================
    # 3. Delete Physical PDF
    # ======================================================

    file_path = (

        Path(
            settings.UPLOAD_DIR
        )

        / str(
            current_user.id
        )

        / f"{document.id}.pdf"
    )


    if file_path.exists():

        file_path.unlink()


    # ======================================================
    # 4. Delete PostgreSQL Record
    # ======================================================

    db.delete(
        document
    )


    db.commit()


    # ======================================================
    # 5. Return Response
    # ======================================================

    return {

        "message":
            "Document deleted successfully"
    }