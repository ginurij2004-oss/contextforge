from contextlib import asynccontextmanager
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.db.database import engine
from app.core.config import settings
from app.db.base import Base
from app.db.phase7_migration import ensure_phase7_schema

# ==========================================================
# Models
# ==========================================================

from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document
from app.models.ai_request import AIRequest
from app.models.message_source import MessageSource
from app.models.evaluation_run import EvaluationRun
from app.models.evaluation_result import EvaluationResult
from app.models.message_metadata import MessageMetadata
from app.models.message_tool_call import MessageToolCall
from app.models.message_action_item import MessageActionItem
from app.models.action_request import ActionRequest
from app.models.automation import Automation
from app.models.automation_run import AutomationRun
from app.models.automation_audit_log import AutomationAuditLog

# ==========================================================
# Routers
# ==========================================================

from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.rag import router as rag_router
from app.api.conversations import router as conversations_router
from app.api.voice import router as voice_router
from app.api.actions import router as actions_router
from app.api.automations import router as automations_router
from app.api.operations import router as operations_router

from app.api import evaluation
from app.api import analytics
from app.api import experiments
from app.api import optimization
from app.api import agent

from app.core.rate_limit import limiter
from app.services.automation_scheduler import (
    start_automation_scheduler,
    stop_automation_scheduler,
)


# ==========================================================
# Database tables
# ==========================================================

Base.metadata.create_all(
    bind=engine
)

# Existing Phase 6 tables need new Phase 7 columns. This
# migration is idempotent and preserves existing automation data.
ensure_phase7_schema()


# ==========================================================
# Lifespan
# ==========================================================

@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    await start_automation_scheduler()

    try:
        yield
    finally:
        await stop_automation_scheduler()


# ==========================================================
# App
# ==========================================================

app = FastAPI(
    title="ContextForge API",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)


# ==========================================================
# CORS
#
# Development keeps the existing localhost behavior.
# Production can set CONTEXTFORGE_ALLOWED_ORIGINS as a comma-
# separated list, for example:
# https://app.example.com,https://admin.example.com
# ==========================================================

_allowed_origins_raw = str(
    settings.CONTEXTFORGE_ALLOWED_ORIGINS
    or ""
).strip()

_allowed_origins = [
    origin.strip()
    for origin in _allowed_origins_raw.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_origin_regex=(
        None
        if _allowed_origins
        else (
            r"^http://"
            r"(localhost|127\.0\.0\.1)"
            r":\d+$"
        )
    ),
    allow_credentials=True,
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],
    allow_headers=["*"],
    expose_headers=[
        "X-Request-ID",
    ],
)


@app.middleware("http")
async def phase8_security_headers(
    request,
    call_next,
):
    request_id = (
        request.headers.get("X-Request-ID")
        or str(uuid.uuid4())
    )

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    return response


# ==========================================================
# Routers
# ==========================================================

app.include_router(auth_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
app.include_router(evaluation.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(experiments.router, prefix="/api")
app.include_router(optimization.router, prefix="/api")
app.include_router(agent.router, prefix="/api")
app.include_router(voice_router, prefix="/api")
app.include_router(actions_router, prefix="/api")
app.include_router(automations_router, prefix="/api")
app.include_router(operations_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "ContextForge API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
