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

from app.core.config import settings

from app.core.rate_limit import (
    limiter,
)

from app.db.database import get_db

from app.models.user import User

from app.models.evaluation_run import (
    EvaluationRun,
)

from app.models.evaluation_result import (
    EvaluationResult,
)

from app.evaluation.dataset import (
    EVALUATION_DATASET,
)

from app.evaluation.evaluator import (
    run_evaluation,
)

from app.schemas.evaluation import (
    EvaluationRunListItem,
    EvaluationSummary,
)


router = APIRouter(
    prefix="/evaluation",
    tags=["Evaluation"],
)


# ==========================================================
# Get Evaluation Dataset
# ==========================================================

@router.get(
    "/dataset",
)
def get_evaluation_dataset(
    current_user: User = Depends(
        get_current_user
    ),
):

    return {
        "total_questions":
            len(EVALUATION_DATASET),

        "questions":
            EVALUATION_DATASET,
    }


# ==========================================================
# Run + Save Evaluation
# ==========================================================

@router.post(
    "/run",
    response_model=EvaluationSummary,
)
@limiter.limit(
    "10/minute"
)
def run_rag_evaluation(
    request: Request,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    try:

        # --------------------------------------------------
        # Run actual evaluation
        # --------------------------------------------------

        result = run_evaluation(
            user_id=current_user.id
        )


        # --------------------------------------------------
        # Create evaluation run
        # --------------------------------------------------

        evaluation_run = EvaluationRun(

            user_id=
                current_user.id,

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

            rag_score_threshold=
                settings.RAG_SCORE_THRESHOLD,

            rag_top_k=
                settings.RAG_TOP_K,

            rag_chunk_size=
                settings.RAG_CHUNK_SIZE,

            rag_chunk_overlap=
                settings.RAG_CHUNK_OVERLAP,
        )


        db.add(
            evaluation_run
        )


        # Need ID before creating
        # child result rows.
        db.flush()


        # --------------------------------------------------
        # Save each question result
        # --------------------------------------------------

        for item in result[
            "results"
        ]:

            evaluation_result = (
                EvaluationResult(

                    evaluation_run_id=
                        evaluation_run.id,

                    question_id=
                        item["id"],

                    question=
                        item["question"],

                    expect_answer=
                        item[
                            "expect_answer"
                        ],

                    answer=
                        item["answer"],

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

                    keyword_match=
                        item[
                            "keyword_match"
                        ],

                    no_answer_correct=
                        item[
                            "no_answer_correct"
                        ],

                    top_score=
                        item[
                            "top_score"
                        ],

                    latency_ms=
                        item[
                            "latency_ms"
                        ],
                )
            )


            db.add(
                evaluation_result
            )


        db.commit()

        db.refresh(
            evaluation_run
        )


        # --------------------------------------------------
        # Return same report
        # plus saved run ID
        # --------------------------------------------------

        result[
            "run_id"
        ] = evaluation_run.id


        return result


    except ValueError as exc:

        db.rollback()

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=str(exc),
        )


    except Exception as exc:

        db.rollback()

        print(
            "EVALUATION ERROR:",
            type(exc).__name__,
            str(exc),
        )


        raise HTTPException(
            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                "Evaluation failed",
        )


# ==========================================================
# List Previous Evaluation Runs
# ==========================================================

@router.get(
    "/runs",
    response_model=list[
        EvaluationRunListItem
    ],
)
def get_evaluation_runs(

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    statement = (

        select(
            EvaluationRun
        )

        .where(
            EvaluationRun.user_id
            == current_user.id
        )

        .order_by(
            EvaluationRun.id.desc()
        )
    )


    runs = list(
        db.scalars(
            statement
        ).all()
    )


    return runs


# ==========================================================
# Get One Evaluation Run
# ==========================================================

@router.get(
    "/runs/{run_id}",
)
def get_evaluation_run(

    run_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    statement = select(
        EvaluationRun
    ).where(
        EvaluationRun.id == run_id,
        EvaluationRun.user_id
        == current_user.id,
    )


    evaluation_run = db.scalar(
        statement
    )


    if not evaluation_run:

        raise HTTPException(
            status_code=404,
            detail=(
                "Evaluation run not found"
            ),
        )


    result_statement = (

        select(
            EvaluationResult
        )

        .where(
            EvaluationResult.evaluation_run_id
            == evaluation_run.id
        )

        .order_by(
            EvaluationResult.id.asc()
        )
    )


    results = list(

        db.scalars(
            result_statement
        ).all()
    )


    return {

        "run": {
            "id":
                evaluation_run.id,

            "overall_score":
                evaluation_run.overall_score,

            "retrieval_hit_rate":
                evaluation_run.retrieval_hit_rate,

            "document_accuracy":
                evaluation_run.document_accuracy,

            "page_accuracy":
                evaluation_run.page_accuracy,

            "keyword_accuracy":
                evaluation_run.keyword_accuracy,

            "no_answer_accuracy":
                evaluation_run.no_answer_accuracy,

            "average_top_score":
                evaluation_run.average_top_score,

            "average_latency_ms":
                evaluation_run.average_latency_ms,

            "rag_score_threshold":
                evaluation_run.rag_score_threshold,

            "rag_top_k":
                evaluation_run.rag_top_k,

            "rag_chunk_size":
                evaluation_run.rag_chunk_size,

            "rag_chunk_overlap":
                evaluation_run.rag_chunk_overlap,

            "created_at":
                evaluation_run.created_at,
        },

        "results": [

            {
                "question_id":
                    item.question_id,

                "question":
                    item.question,

                "answer":
                    item.answer,

                "retrieval_hit":
                    item.retrieval_hit,

                "document_correct":
                    item.document_correct,

                "page_correct":
                    item.page_correct,

                "keyword_match":
                    item.keyword_match,

                "no_answer_correct":
                    item.no_answer_correct,

                "top_score":
                    item.top_score,

                "latency_ms":
                    item.latency_ms,
            }

            for item in results
        ],
    }