from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import (
    get_current_user,
)

from app.core.rate_limit import (
    limiter,
)

from app.db.database import (
    get_db,
)

from app.evaluation.evaluator import (
    run_evaluation,
)

from app.models.user import User

from app.models.document import (
    Document,
)

from app.models.evaluation_run import (
    EvaluationRun,
)

from app.models.evaluation_result import (
    EvaluationResult,
)

from app.schemas.experiment import (
    RAGExperimentRequest,
)


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/experiments",
    tags=["RAG Experiments"],
)


# ==========================================================
# Run RAG Experiment
#
# This endpoint:
#
# 1. Finds the selected document
# 2. Verifies document ownership
# 3. Reads the ACTUAL chunk configuration used to index it
# 4. Runs RAG evaluation using supplied Top-K + threshold
# 5. Saves experiment configuration
# 6. Saves question-by-question results
# ==========================================================

@router.post(
    "/run",
)
@limiter.limit(
    "10/minute"
)
def run_experiment(
    request: Request,
    data: RAGExperimentRequest,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    # ======================================================
    # 1. Find Selected Document
    # ======================================================

    statement = select(
        Document
    ).where(
        Document.id
        == data.document_id,

        Document.user_id
        == current_user.id,
    )


    document = db.scalar(
        statement
    )


    # ======================================================
    # 2. Confirm Document Exists
    # ======================================================

    if not document:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Document not found",
        )


    # ======================================================
    # 3. Confirm Document Is Ready
    # ======================================================

    if document.status != "ready":

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=(
                "Document must be ready "
                "before running an experiment"
            ),
        )


    # ======================================================
    # 4. Confirm Index Configuration Metadata Exists
    #
    # Older documents may not have these values until
    # they are re-indexed.
    # ======================================================

    if (
        document.indexed_chunk_size
        is None
        or
        document.indexed_chunk_overlap
        is None
    ):

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=(
                "Document does not have "
                "index configuration metadata. "
                "Please re-index the document first."
            ),
        )


    try:

        # ==================================================
        # 5. Run Evaluation
        #
        # top_k and score_threshold are temporary
        # experiment settings.
        #
        # They do NOT modify .env.
        # ==================================================

        result = run_evaluation(

    user_id=
        current_user.id,

    top_k=
        data.top_k,

    score_threshold=
        data.score_threshold,

    document_id=
        document.id,
)


        # ==================================================
        # 6. Create Evaluation Run
        #
        # IMPORTANT:
        # Chunk settings come from Document metadata,
        # not settings.RAG_CHUNK_SIZE.
        # ==================================================

        evaluation_run = EvaluationRun(

            user_id=
                current_user.id,


            # ----------------------------------------------
            # Question counts
            # ----------------------------------------------

            total_questions=
                result[
                    "total_questions"
                ],

            answerable_questions=
                result[
                    "answerable_questions"
                ],

            no_answer_questions=
                result[
                    "no_answer_questions"
                ],


            # ----------------------------------------------
            # Evaluation metrics
            # ----------------------------------------------

            retrieval_hit_rate=
                result[
                    "retrieval_hit_rate"
                ],

            document_accuracy=
                result[
                    "document_accuracy"
                ],

            page_accuracy=
                result[
                    "page_accuracy"
                ],

            keyword_accuracy=
                result[
                    "keyword_accuracy"
                ],

            no_answer_accuracy=
                result[
                    "no_answer_accuracy"
                ],

            average_top_score=
                result[
                    "average_top_score"
                ],

            average_latency_ms=
                result[
                    "average_latency_ms"
                ],

            overall_score=
                result[
                    "overall_score"
                ],


            # ----------------------------------------------
            # Retrieval experiment settings
            # ----------------------------------------------

            rag_score_threshold=
                data.score_threshold,

            rag_top_k=
                data.top_k,


            # ----------------------------------------------
            # ACTUAL indexing settings
            # from selected document
            # ----------------------------------------------

            rag_chunk_size=
                document.indexed_chunk_size,

            rag_chunk_overlap=
                document.indexed_chunk_overlap,


            # ----------------------------------------------
            # Experiment label
            # ----------------------------------------------

            label=
                data.label,
        )


        db.add(
            evaluation_run
        )


        # --------------------------------------------------
        # Flush gives us evaluation_run.id
        # before the final commit.
        # --------------------------------------------------

        db.flush()


        # ==================================================
        # 7. Save Question-by-Question Results
        # ==================================================

        for item in result[
            "results"
        ]:

            evaluation_result = (
                EvaluationResult(

                    evaluation_run_id=
                        evaluation_run.id,


                    # --------------------------------------
                    # Question
                    # --------------------------------------

                    question_id=
                        item[
                            "id"
                        ],

                    question=
                        item[
                            "question"
                        ],

                    expect_answer=
                        item[
                            "expect_answer"
                        ],


                    # --------------------------------------
                    # Generated answer
                    # --------------------------------------

                    answer=
                        item[
                            "answer"
                        ],


                    # --------------------------------------
                    # Retrieval results
                    # --------------------------------------

                    sources_count=
                        item[
                            "sources_count"
                        ],

                    retrieval_hit=
                        item[
                            "retrieval_hit"
                        ],

                    document_correct=
                        item[
                            "document_correct"
                        ],

                    page_correct=
                        item[
                            "page_correct"
                        ],


                    # --------------------------------------
                    # Answer evaluation
                    # --------------------------------------

                    keyword_match=
                        item[
                            "keyword_match"
                        ],

                    no_answer_correct=
                        item[
                            "no_answer_correct"
                        ],


                    # --------------------------------------
                    # Retrieval score
                    # --------------------------------------

                    top_score=
                        item[
                            "top_score"
                        ],


                    # --------------------------------------
                    # Performance
                    # --------------------------------------

                    latency_ms=
                        item[
                            "latency_ms"
                        ],
                )
            )


            db.add(
                evaluation_result
            )


        # ==================================================
        # 8. Commit Experiment
        # ==================================================

        db.commit()


        db.refresh(
            evaluation_run
        )


        # ==================================================
        # 9. Return Complete Experiment Result
        # ==================================================

        return {

            "run_id":
                evaluation_run.id,

            "label":
                evaluation_run.label,


            # ----------------------------------------------
            # Document used for configuration tracking
            # ----------------------------------------------

            "document": {

                "id":
                    document.id,

                "filename":
                    document.filename,

                "status":
                    document.status,
            },


            # ----------------------------------------------
            # Complete experiment configuration
            # ----------------------------------------------

            "configuration": {

                "document_id":
                    document.id,

                "filename":
                    document.filename,

                "top_k":
                    data.top_k,

                "score_threshold":
                    data.score_threshold,

                "chunk_size":
                    document.indexed_chunk_size,

                "chunk_overlap":
                    document.indexed_chunk_overlap,

                "indexed_at":
                    document.indexed_at,
            },


            # ----------------------------------------------
            # Evaluation report
            # ----------------------------------------------

            "evaluation":
                result,
        }


    # ======================================================
    # Dataset / Evaluation Configuration Error
    # ======================================================

    except ValueError as exc:

        db.rollback()


        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                str(exc),
        )


    # ======================================================
    # Preserve Existing HTTP Errors
    # ======================================================

    except HTTPException:

        db.rollback()

        raise


    # ======================================================
    # Unexpected Error
    # ======================================================

    except Exception as exc:

        db.rollback()


        print(
            "EXPERIMENT ERROR:",
            type(exc).__name__,
            str(exc),
        )


        raise HTTPException(
            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                "RAG experiment failed",
        )