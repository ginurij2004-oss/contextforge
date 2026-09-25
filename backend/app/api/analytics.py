
from datetime import (
    datetime,
    timedelta,
)

from fastapi import (
    APIRouter,
    Depends,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import (
    get_current_user,
)

from app.db.database import (
    get_db,
)

from app.models.user import User

from app.models.ai_request import (
    AIRequest,
)

from app.models.evaluation_run import (
    EvaluationRun,
)

from app.schemas.analytics import (
    AnalyticsDashboardResponse,
)


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


# ==========================================================
# Helper:
# Determine AI request mode
# ==========================================================

def get_request_mode(
    prompt_version: str | None,
) -> str:

    if not prompt_version:
        return "chat"

    normalized = (
        prompt_version
        .lower()
        .strip()
    )

    if normalized.startswith("agent"):
        return "agent"

    if normalized.startswith("rag"):
        return "documents"

    return "chat"


# ==========================================================
# Analytics Dashboard
# ==========================================================

@router.get(
    "/dashboard",
    response_model=AnalyticsDashboardResponse,
)
def get_analytics_dashboard(

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    # ======================================================
    # 1. Load AI requests for current user
    # ======================================================

    requests_statement = (

        select(
            AIRequest
        )

        .where(
            AIRequest.user_id
            == current_user.id
        )

        .order_by(
            AIRequest.id.desc()
        )
    )


    all_requests = list(

        db.scalars(
            requests_statement
        ).all()
    )


    # ======================================================
    # 2. Main Overview Metrics
    # ======================================================

    total_requests = len(
        all_requests
    )


    successful_requests = sum(

        1

        for request in all_requests

        if request.status == "success"
    )


    failed_requests = sum(

        1

        for request in all_requests

        if request.status == "failed"
    )


    if total_requests > 0:

        success_rate = round(
            (
                successful_requests
                / total_requests
            )
            * 100,
            2,
        )

    else:

        success_rate = 0.0


    # ------------------------------------------------------
    # Latency
    # ------------------------------------------------------

    latency_values = [

        request.latency_ms

        for request in all_requests

        if request.latency_ms
        is not None
    ]


    if latency_values:

        average_latency_ms = round(
            sum(latency_values)
            / len(latency_values),
            2,
        )

    else:

        average_latency_ms = 0.0


    # ------------------------------------------------------
    # Token Usage
    # ------------------------------------------------------

    total_input_tokens = sum(

        request.input_tokens or 0

        for request in all_requests
    )


    total_output_tokens = sum(

        request.output_tokens or 0

        for request in all_requests
    )


    total_tokens = (
        total_input_tokens
        + total_output_tokens
    )


    # ------------------------------------------------------
    # Chat vs RAG
    # ------------------------------------------------------

    chat_requests = 0

    document_requests = 0

    agent_requests = 0


    for request in all_requests:

        mode = get_request_mode(
            request.prompt_version
        )

        if mode == "documents":

            document_requests += 1

        elif mode == "agent":

            agent_requests += 1

        else:

            chat_requests += 1


    # ======================================================
    # 3. Last 7 Days Activity
    # ======================================================

    today = datetime.now().date()

    start_date = (
        today
        - timedelta(
            days=6
        )
    )


    # ------------------------------------------------------
    # Create empty entries first
    # so days with no requests still appear.
    # ------------------------------------------------------

    daily_data = {}


    for day_offset in range(7):

        current_date = (
            start_date
            + timedelta(
                days=day_offset
            )
        )


        date_key = (
            current_date.isoformat()
        )


        daily_data[
            date_key
        ] = {

            "requests":
                0,

            "successful_requests":
                0,

            "failed_requests":
                0,

            "latencies":
                [],

            "input_tokens":
                0,

            "output_tokens":
                0,
        }


    # ------------------------------------------------------
    # Fill daily metrics
    # ------------------------------------------------------

    for request in all_requests:

        if not request.created_at:
            continue


        request_date = (
            request.created_at.date()
        )


        if (
            request_date
            < start_date
        ):

            continue


        if (
            request_date
            > today
        ):

            continue


        date_key = (
            request_date.isoformat()
        )


        if date_key not in daily_data:
            continue


        item = daily_data[
            date_key
        ]


        item[
            "requests"
        ] += 1


        if request.status == "success":

            item[
                "successful_requests"
            ] += 1


        elif request.status == "failed":

            item[
                "failed_requests"
            ] += 1


        if (
            request.latency_ms
            is not None
        ):

            item[
                "latencies"
            ].append(
                request.latency_ms
            )


        item[
            "input_tokens"
        ] += (
            request.input_tokens
            or 0
        )


        item[
            "output_tokens"
        ] += (
            request.output_tokens
            or 0
        )


    daily_activity = []


    for date_key, item in (
        daily_data.items()
    ):

        latencies = item[
            "latencies"
        ]


        average_daily_latency = (

            round(
                sum(latencies)
                / len(latencies),
                2,
            )

            if latencies

            else 0.0
        )


        daily_activity.append({

            "date":
                date_key,

            "requests":
                item[
                    "requests"
                ],

            "successful_requests":
                item[
                    "successful_requests"
                ],

            "failed_requests":
                item[
                    "failed_requests"
                ],

            "average_latency_ms":
                average_daily_latency,

            "input_tokens":
                item[
                    "input_tokens"
                ],

            "output_tokens":
                item[
                    "output_tokens"
                ],
        })


    # ======================================================
    # 4. Recent AI Requests
    # ======================================================

    recent_requests = []


    for request in all_requests[
        :20
    ]:

        input_tokens = (
            request.input_tokens
            or 0
        )

        output_tokens = (
            request.output_tokens
            or 0
        )


        recent_requests.append({

            "id":
                request.id,

            "model":
                request.model,

            "prompt_version":
                request.prompt_version,

            "mode":
                get_request_mode(
                    request.prompt_version
                ),

            "latency_ms":
                request.latency_ms,

            "input_tokens":
                request.input_tokens,

            "output_tokens":
                request.output_tokens,

            "total_tokens":
                input_tokens
                + output_tokens,

            "status":
                request.status,

            "created_at":
                request.created_at,
        })


    # ======================================================
    # 5. Latest Evaluation Runs
    # ======================================================

    evaluations_statement = (

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

        .limit(
            10
        )
    )


    evaluation_rows = list(

        db.scalars(
            evaluations_statement
        ).all()
    )


    evaluation_runs = []


    for run in evaluation_rows:

        evaluation_runs.append({

            "id":
                run.id,

            "overall_score":
                run.overall_score,

            "retrieval_hit_rate":
                run.retrieval_hit_rate,

            "document_accuracy":
                run.document_accuracy,

            "page_accuracy":
                run.page_accuracy,

            "keyword_accuracy":
                run.keyword_accuracy,

            "no_answer_accuracy":
                run.no_answer_accuracy,

            "average_latency_ms":
                run.average_latency_ms,

            "rag_score_threshold":
                run.rag_score_threshold,

            "rag_top_k":
                run.rag_top_k,

            "rag_chunk_size":
                run.rag_chunk_size,

            "rag_chunk_overlap":
                run.rag_chunk_overlap,

            "created_at":
                run.created_at,
        })


    # ======================================================
    # 6. Final Response
    # ======================================================

    return {

        "overview": {

            "total_requests":
                total_requests,

            "successful_requests":
                successful_requests,

            "failed_requests":
                failed_requests,

            "success_rate":
                success_rate,

            "average_latency_ms":
                average_latency_ms,

            "total_input_tokens":
                total_input_tokens,

            "total_output_tokens":
                total_output_tokens,

            "total_tokens":
                total_tokens,

            "chat_requests":
                chat_requests,

            "document_requests":
                document_requests,

            "agent_requests":
                agent_requests,
        },


        "daily_activity":
            daily_activity,


        "recent_requests":
            recent_requests,


        "evaluation_runs":
            evaluation_runs,
    }