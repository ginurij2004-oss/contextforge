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

from app.schemas.agent import (
    AgentRequest,
    AgentResponse,
)

from app.services.agent_service import (
    run_agent,
)

from app.services.guardrails import (
    detect_prompt_injection,
    is_flagged_content,
)


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/agent",
    tags=["AI Agent"],
)


# ==========================================================
# Run Agent
# ==========================================================

@router.post(
    "/run",
    response_model=AgentResponse,
)
@limiter.limit(
    "10/minute"
)
def run_contextforge_agent(

    request: Request,

    data: AgentRequest,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    # ======================================================
    # 1. Clean Message
    # ======================================================

    message = (
        data.message
        .strip()
    )


    if not message:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Message cannot be empty",
        )


    # ======================================================
    # 2. Prompt Injection Guardrail
    # ======================================================

    if detect_prompt_injection(
        message
    ):

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=(
                "Potential prompt "
                "injection detected."
            ),
        )


    # ======================================================
    # 3. Content Moderation
    # ======================================================

    try:

        flagged = is_flagged_content(
            message
        )

    except Exception as exc:

        print(
            "AGENT MODERATION ERROR:",
            type(exc).__name__,
            str(exc),
        )

        flagged = False


    if flagged:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=(
                "Message blocked by "
                "safety policy."
            ),
        )


    # ======================================================
    # 4. Validate Optional Document Scope
    # ======================================================

    if (
        data.document_id
        is not None
    ):

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


        if document.status != "ready":

            raise HTTPException(

                status_code=
                    status.HTTP_400_BAD_REQUEST,

                detail=(
                    "Document must be ready "
                    "before using the agent"
                ),
            )


    # ======================================================
    # 5. Run Agent
    # ======================================================

    try:

        result = run_agent(

            message=
                message,

            user_id=
                current_user.id,

            db=
                db,

            document_id=
                data.document_id,
        )


        return result


    except Exception as exc:

        print(
            "AGENT ERROR:",
            type(exc).__name__,
            str(exc),
        )


        raise HTTPException(

            status_code=
                status.HTTP_500_INTERNAL_SERVER_ERROR,

            detail=
                "Agent request failed",
        )