from datetime import (
    datetime,
    timezone,
)

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

from app.schemas.optimization import (
    RAGOptimizationRequest,
)

from app.evaluation.evaluator import (
    run_evaluation,
)

from app.services.reindex_service import (
    rebuild_document_index,
)


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/optimization",
    tags=["RAG Optimization"],
)


# ==========================================================
# Helper:
# Current UTC timestamp
# ==========================================================

def get_timestamp():

    return (
        datetime.now(
            timezone.utc
        )
        .replace(
            tzinfo=None
        )
    )


# ==========================================================
# Helper:
# Save Evaluation Run
# ==========================================================

def save_evaluation_run(
    db: Session,
    user_id: int,
    result: dict,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
    threshold: float,
):

    label = (
        f"AUTO "
        f"C{chunk_size} "
        f"O{chunk_overlap} "
        f"K{top_k} "
        f"T{threshold}"
    )


    evaluation_run = EvaluationRun(

        user_id=
            user_id,

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
            threshold,

        rag_top_k=
            top_k,

        rag_chunk_size=
            chunk_size,

        rag_chunk_overlap=
            chunk_overlap,

        label=
            label,
    )


    db.add(
        evaluation_run
    )

    db.flush()


    # ======================================================
    # Save Per-question Results
    # ======================================================

    for item in result[
        "results"
    ]:

        row = EvaluationResult(

            evaluation_run_id=
                evaluation_run.id,

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

            answer=
                item[
                    "answer"
                ],

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


        db.add(
            row
        )


    db.commit()

    db.refresh(
        evaluation_run
    )


    return evaluation_run


# ==========================================================
# Helper:
# Ranking Key
#
# Priority:
#
# 1. Overall score
# 2. No-answer accuracy
# 3. Page accuracy
# 4. Lower latency
# ==========================================================

def ranking_key(
    experiment: dict,
):

    overall = (
        experiment.get(
            "overall_score"
        )
        or 0
    )

    no_answer = (
        experiment.get(
            "no_answer_accuracy"
        )
        or 0
    )

    page = (
        experiment.get(
            "page_accuracy"
        )
        or 0
    )

    latency = (
        experiment.get(
            "average_latency_ms"
        )
        or 999999999
    )


    return (
        overall,
        no_answer,
        page,
        -latency,
    )


# ==========================================================
# Automated RAG Optimization
# ==========================================================

@router.post(
    "/run",
)
@limiter.limit(
    "2/hour"
)
def run_optimization(
    request: Request,

    data:
        RAGOptimizationRequest,

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


    if not document:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Document not found",
        )


    # ======================================================
    # 2. Make Sure Document Is Ready
    # ======================================================

    if document.status != "ready":

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=(
                "Document must be ready "
                "before optimization"
            ),
        )


    total_combinations = (

        len(
            data.chunk_configs
        )

        * len(
            data.top_k_values
        )

        * len(
            data.threshold_values
        )
    )


    completed_experiments = []


    try:

        # ==================================================
        # 3. Loop Through Chunk Configurations
        # ==================================================

        for chunk_config in (
            data.chunk_configs
        ):

            chunk_size = (
                chunk_config.chunk_size
            )

            chunk_overlap = (
                chunk_config.chunk_overlap
            )


            # ==============================================
            # 4. Re-index PDF
            # ==============================================

            document.status = (
                "processing"
            )

            db.commit()


            index_result = (
                rebuild_document_index(

                    document=
                        document,

                    user_id=
                        current_user.id,

                    chunk_size=
                        chunk_size,

                    chunk_overlap=
                        chunk_overlap,
                )
            )


            document.status = (
                "ready"
            )

            document.indexed_chunk_size = (
                chunk_size
            )

            document.indexed_chunk_overlap = (
                chunk_overlap
            )

            document.indexed_at = (
                get_timestamp()
            )


            db.commit()

            db.refresh(
                document
            )


            # ==============================================
            # 5. Try Each Top-K
            # ==============================================

            for top_k in (
                data.top_k_values
            ):


                # ==========================================
                # 6. Try Each Threshold
                # ==========================================

                for threshold in (
                    data.threshold_values
                ):


                    # ======================================
                    # 7. Run Evaluation
                    # ======================================

                    evaluation = (
                        run_evaluation(

                            user_id=
                                current_user.id,

                            top_k=
                                top_k,

                            score_threshold=
                                threshold,

                            document_id=
                                document.id,
                        )
                    )


                    # ======================================
                    # 8. Save Experiment
                    # ======================================

                    saved_run = (
                        save_evaluation_run(

                            db=
                                db,

                            user_id=
                                current_user.id,

                            result=
                                evaluation,

                            chunk_size=
                                chunk_size,

                            chunk_overlap=
                                chunk_overlap,

                            top_k=
                                top_k,

                            threshold=
                                threshold,
                        )
                    )


                    # ======================================
                    # 9. Add To Ranking Results
                    # ======================================

                    completed_experiments.append({

                        "run_id":
                            saved_run.id,

                        "chunk_size":
                            chunk_size,

                        "chunk_overlap":
                            chunk_overlap,

                        "top_k":
                            top_k,

                        "score_threshold":
                            threshold,

                        "overall_score":
                            evaluation[
                                "overall_score"
                            ],

                        "retrieval_hit_rate":
                            evaluation[
                                "retrieval_hit_rate"
                            ],

                        "document_accuracy":
                            evaluation[
                                "document_accuracy"
                            ],

                        "page_accuracy":
                            evaluation[
                                "page_accuracy"
                            ],

                        "keyword_accuracy":
                            evaluation[
                                "keyword_accuracy"
                            ],

                        "no_answer_accuracy":
                            evaluation[
                                "no_answer_accuracy"
                            ],

                        "average_top_score":
                            evaluation[
                                "average_top_score"
                            ],

                        "average_latency_ms":
                            evaluation[
                                "average_latency_ms"
                            ],

                        "chunks":
                            index_result[
                                "chunks"
                            ],
                    })


        # ==================================================
        # 10. Make Sure At Least One Experiment Completed
        # ==================================================

        if not completed_experiments:

            raise ValueError(
                "No experiments were completed"
            )


        # ==================================================
        # 11. Rank Best Configuration
        # ==================================================

        ranked_results = sorted(

            completed_experiments,

            key=
                ranking_key,

            reverse=
                True,
        )


        best = ranked_results[
            0
        ]


        # ==================================================
        # 12. Restore / Apply Best Chunk Index
        # ==================================================

        if (
            data.restore_best_index
        ):

            current_chunk_size = (
                document.indexed_chunk_size
            )

            current_overlap = (
                document.indexed_chunk_overlap
            )


            if (
                current_chunk_size
                != best[
                    "chunk_size"
                ]

                or

                current_overlap
                != best[
                    "chunk_overlap"
                ]
            ):

                document.status = (
                    "processing"
                )

                db.commit()


                rebuild_document_index(

                    document=
                        document,

                    user_id=
                        current_user.id,

                    chunk_size=
                        best[
                            "chunk_size"
                        ],

                    chunk_overlap=
                        best[
                            "chunk_overlap"
                        ],
                )


            document.status = (
                "ready"
            )

            document.indexed_chunk_size = (
                best[
                    "chunk_size"
                ]
            )

            document.indexed_chunk_overlap = (
                best[
                    "chunk_overlap"
                ]
            )

            document.indexed_at = (
                get_timestamp()
            )


            db.commit()

            db.refresh(
                document
            )


        # ==================================================
        # 13. Return Optimization Report
        # ==================================================

        return {

            "document": {

                "id":
                    document.id,

                "filename":
                    document.filename,
            },


            "total_combinations":
                total_combinations,


            "experiments_completed":
                len(
                    completed_experiments
                ),


            "best_configuration": {

                "run_id":
                    best[
                        "run_id"
                    ],

                "chunk_size":
                    best[
                        "chunk_size"
                    ],

                "chunk_overlap":
                    best[
                        "chunk_overlap"
                    ],

                "top_k":
                    best[
                        "top_k"
                    ],

                "score_threshold":
                    best[
                        "score_threshold"
                    ],

                "overall_score":
                    best[
                        "overall_score"
                    ],

                "retrieval_hit_rate":
                    best[
                        "retrieval_hit_rate"
                    ],

                "document_accuracy":
                    best[
                        "document_accuracy"
                    ],

                "page_accuracy":
                    best[
                        "page_accuracy"
                    ],

                "keyword_accuracy":
                    best[
                        "keyword_accuracy"
                    ],

                "no_answer_accuracy":
                    best[
                        "no_answer_accuracy"
                    ],

                "average_latency_ms":
                    best[
                        "average_latency_ms"
                    ],
            },


            "document_index_restored_to_best":
                data.restore_best_index,


            "ranked_results":
                ranked_results,
        }


    # ======================================================
    # Known Validation Errors
    # ======================================================

    except (
        ValueError,
        FileNotFoundError,
    ) as exc:

        db.rollback()


        document.status = (
            "failed"
        )

        db.commit()


        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                str(exc),
        )


    # ======================================================
    # Preserve HTTP Exceptions
    # ======================================================

    except HTTPException:

        db.rollback()

        raise


    # ======================================================
    # Unexpected Failure
    # ======================================================

    except Exception as exc:

        db.rollback()


        try:

            document.status = (
                "failed"
            )

            db.commit()

        except Exception:

            db.rollback()


        print(
            "OPTIMIZATION ERROR:",
            type(exc).__name__,
            str(exc),
        )


        raise HTTPException(

            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=(
                "Automated RAG optimization failed"
            ),
        )