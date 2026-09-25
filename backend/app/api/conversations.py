import json
from datetime import datetime
from time import perf_counter

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)

from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.orm import Session

from app.api.auth import (
    get_current_user,
)

from app.core.config import settings
from app.core.rate_limit import limiter

from app.db.database import get_db

from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.ai_request import AIRequest
from app.models.message_source import MessageSource

from app.models.message_metadata import (
    MessageMetadata,
)

from app.models.message_tool_call import (
    MessageToolCall,
)

from app.models.message_action_item import (
    MessageActionItem,
)

from app.models.action_request import (
    ActionRequest,
)

from app.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    SendMessageResponse,
    
)

from app.services.llm_service import (
    generate_chat_response,
)

from app.services.guardrails import (
    detect_prompt_injection,
    is_flagged_content,
)

from app.services.agent_service import (
    run_agent,
)

from app.rag.pipeline import (
    generate_rag_answer,
)


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)


# ==========================================================
# Get Owned Conversation
# ==========================================================

def get_owned_conversation(
    db: Session,
    conversation_id: int,
    user_id: int,
):

    statement = select(
        Conversation
    ).where(
        Conversation.id
        == conversation_id,

        Conversation.user_id
        == user_id,
    )


    conversation = db.scalar(
        statement
    )


    if not conversation:

        raise HTTPException(
            status_code=
                status.HTTP_404_NOT_FOUND,

            detail=
                "Conversation not found",
        )


    return conversation


# ==========================================================
# Get Message Metadata
# ==========================================================

def get_message_metadata(
    db: Session,
    message_id: int,
):

    statement = select(
        MessageMetadata
    ).where(
        MessageMetadata.message_id
        == message_id
    )


    return db.scalar(
        statement
    )


# ==========================================================
# Serialize Message
# ==========================================================

def serialize_message(
    db: Session,
    message: Message,
):

    # ======================================================
    # Sources
    # ======================================================

    source_statement = (

        select(
            MessageSource
        )

        .where(
            MessageSource.message_id
            == message.id
        )

        .order_by(
            MessageSource.id.asc()
        )
    )


    source_rows = list(
        db.scalars(
            source_statement
        ).all()
    )


    sources = [

        {
            "document_id":
                source.document_id,

            "filename":
                source.filename,

            "page":
                source.page,

            "score":
                source.score,
        }

        for source
        in source_rows
    ]


    # ======================================================
    # Metadata
    # ======================================================

    metadata = get_message_metadata(
        db,
        message.id,
    )


    if metadata:

        mode = metadata.mode

        document_id = (
            metadata.document_id
        )

        confidence = (
            metadata.confidence
        )

    else:

        # ----------------------------------------------
        # Legacy messages created before metadata
        # existed.
        # ----------------------------------------------

        mode = (
            "documents"
            if sources
            else "chat"
        )

        document_id = None

        confidence = None


    # ======================================================
    # Agent Tool Calls
    # ======================================================

    tool_statement = (

        select(
            MessageToolCall
        )

        .where(
            MessageToolCall.message_id
            == message.id
        )

        .order_by(
            MessageToolCall.id.asc()
        )
    )


    tool_rows = list(
        db.scalars(
            tool_statement
        ).all()
    )


    used_tools = [

        row.tool_name

        for row
        in tool_rows
    ]


    # ======================================================
    # Agent Action Items
    # ======================================================

    action_statement = (

        select(
            MessageActionItem
        )

        .where(
            MessageActionItem.message_id
            == message.id
        )

        .order_by(
            MessageActionItem.id.asc()
        )
    )


    action_rows = list(
        db.scalars(
            action_statement
        ).all()
    )


    action_items = [

        {
            "title":
                row.title,

            "description":
                row.description,

            "priority":
                row.priority,
        }

        for row
        in action_rows
    ]


    # ======================================================
    # Response
    # ======================================================

    return {

        "id":
            message.id,

        "conversation_id":
            message.conversation_id,

        "role":
            message.role,

        "content":
            message.content,

        "model":
            message.model,

        "input_tokens":
            message.input_tokens,

        "output_tokens":
            message.output_tokens,

        "latency_ms":
            message.latency_ms,

        "created_at":
            message.created_at,

        "mode":
            mode,

        "document_id":
            document_id,

        "confidence":
            confidence,

        "sources":
            sources,

        "used_tools":
            used_tools,

        "action_items":
            action_items,
    }


# ==========================================================
# Validate Optional Document Scope
# ==========================================================

def validate_document_scope(
    db: Session,
    user_id: int,
    document_id: int | None,
):

    if document_id is None:

        return None


    statement = select(
        Document
    ).where(
        Document.id
        == document_id,

        Document.user_id
        == user_id,
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
                "before it can be queried"
            ),
        )


    return document


# ==========================================================
# Create Conversation
# ==========================================================

@router.post(
    "",
    response_model=
        ConversationResponse,

    status_code=
        status.HTTP_201_CREATED,
)
def create_conversation(

    data: ConversationCreate,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    title = (

        data.title.strip()

        if data.title

        else "New Conversation"
    )


    if not title:

        title = (
            "New Conversation"
        )


    conversation = Conversation(

        user_id=
            current_user.id,

        title=
            title,
    )


    db.add(
        conversation
    )

    db.commit()

    db.refresh(
        conversation
    )


    return conversation


# ==========================================================
# Get Conversations
# ==========================================================

@router.get(
    "",
    response_model=list[
        ConversationResponse
    ],
)
def get_conversations(

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    statement = (

        select(
            Conversation
        )

        .where(
            Conversation.user_id
            == current_user.id
        )

        .order_by(
            Conversation.id.desc()
        )
    )


    return list(
        db.scalars(
            statement
        ).all()
    )


# ==========================================================
# Get Conversation Messages
# ==========================================================

@router.get(
    "/{conversation_id}/messages",

    response_model=list[
        MessageResponse
    ],
)
def get_messages(

    conversation_id: int,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    get_owned_conversation(

        db,

        conversation_id,

        current_user.id,
    )


    statement = (

        select(
            Message
        )

        .where(
            Message.conversation_id
            == conversation_id
        )

        .order_by(
            Message.id.asc()
        )
    )


    messages = list(
        db.scalars(
            statement
        ).all()
    )


    return [

        serialize_message(
            db,
            message,
        )

        for message
        in messages
    ]


# ==========================================================
# Rename Conversation
# ==========================================================

@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
def rename_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    # ------------------------------------------------------
    # Find conversation owned by current user
    # ------------------------------------------------------

    statement = (
        select(Conversation)
        .where(
            Conversation.id
            == conversation_id,
            Conversation.user_id
            == current_user.id,
        )
    )


    conversation = db.scalar(
        statement
    )


    if not conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )


    # ------------------------------------------------------
    # Clean title
    # ------------------------------------------------------

    new_title = (
        data.title
        .strip()
    )


    if not new_title:

        raise HTTPException(
            status_code=400,
            detail=(
                "Conversation title "
                "cannot be empty"
            ),
        )


    # ------------------------------------------------------
    # Update
    # ------------------------------------------------------

    conversation.title = (
        new_title
    )


    db.commit()

    db.refresh(
        conversation
    )


    return conversation

# ==========================================================
# Delete Conversation
# ==========================================================

@router.delete(
    "/{conversation_id}",
)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    # ------------------------------------------------------
    # 1. Find conversation owned by current user
    # ------------------------------------------------------

    conversation_statement = (
        select(Conversation)
        .where(
            Conversation.id
            == conversation_id,
            Conversation.user_id
            == current_user.id,
        )
    )


    conversation = db.scalar(
        conversation_statement
    )


    if not conversation:

        raise HTTPException(
            status_code=404,
            detail="Conversation not found",
        )


    # ------------------------------------------------------
    # 2. Find all messages in conversation
    # ------------------------------------------------------

    message_ids_statement = (
        select(Message.id)
        .where(
            Message.conversation_id
            == conversation_id
        )
    )


    message_ids = list(
        db.scalars(
            message_ids_statement
        ).all()
    )


    try:

        # --------------------------------------------------
        # 3. Delete message source citations
        # --------------------------------------------------

        if message_ids:

            db.execute(
                delete(
                    MessageSource
                )
                .where(
                    MessageSource.message_id
                    .in_(
                        message_ids
                    )
                )
            )


        # --------------------------------------------------
        # 4. Delete conversation messages
        # --------------------------------------------------

        db.execute(
            delete(
                Message
            )
            .where(
                Message.conversation_id
                == conversation_id
            )
        )


        # --------------------------------------------------
        # 5. Delete conversation
        # --------------------------------------------------

        db.delete(
            conversation
        )


        # --------------------------------------------------
        # 6. Commit transaction
        # --------------------------------------------------

        db.commit()


    except Exception as exc:

        db.rollback()


        print(
            "CONVERSATION DELETE ERROR:",
            type(exc).__name__,
            str(exc),
        )


        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to delete "
                "conversation"
            ),
        )


    return {
        "message":
            "Conversation deleted successfully",

        "conversation_id":
            conversation_id,
    }

# ==========================================================
# Send Message
#
# Modes:
#
# chat
# documents
# agent
# ==========================================================

@router.post(
    "/{conversation_id}/messages",
    response_model=
        SendMessageResponse,
)
@limiter.limit(
    "20/minute"
)
def send_message(

    request: Request,

    conversation_id: int,

    data: MessageCreate,

    db: Session = Depends(
        get_db
    ),

    current_user: User = Depends(
        get_current_user
    ),
):

    # ======================================================
    # 1. Conversation Ownership
    # ======================================================

    conversation = (
        get_owned_conversation(

            db,

            conversation_id,

            current_user.id,
        )
    )


    # ======================================================
    # 2. Clean Message
    # ======================================================

    content = (
        data.content
        .strip()
    )


    if not content:

        raise HTTPException(

            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Message cannot be empty",
        )


    # ======================================================
    # 3. Prompt Injection Guardrail
    # ======================================================

    if detect_prompt_injection(
        content
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
    # 4. Moderation
    # ======================================================

    try:

        flagged = (
            is_flagged_content(
                content
            )
        )


    except Exception as exc:

        print(
            "MODERATION ERROR:",
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
    # 5. Validate Document Scope
    # ======================================================

    if (
        data.mode
        in {
            "documents",
            "agent",
        }
    ):

        validate_document_scope(

            db=
                db,

            user_id=
                current_user.id,

            document_id=
                data.document_id,
        )


    # ======================================================
    # 6. Save User Message
    # ======================================================

    user_message = Message(

        conversation_id=
            conversation.id,

        role=
            "user",

        content=
            content,
    )


    db.add(
        user_message
    )


    # Need message ID before metadata row

    db.flush()


    user_metadata = (
        MessageMetadata(

            message_id=
                user_message.id,

            mode=
                data.mode,

            document_id=
                data.document_id,

            confidence=
                None,
        )
    )


    db.add(
        user_metadata
    )


    # ------------------------------------------------------
    # Automatic Conversation Title
    # ------------------------------------------------------

    if (
        conversation.title
        == "New Conversation"
    ):

        conversation.title = (
            content[:60]
        )


    db.commit()

    db.refresh(
        user_message
    )


    # ======================================================
    # 7. Load Recent Conversation History
    # ======================================================

    statement = (

        select(
            Message
        )

        .where(
            Message.conversation_id
            == conversation.id
        )

        .order_by(
            Message.id.desc()
        )

        .limit(
            20
        )
    )


    history = list(
        db.scalars(
            statement
        ).all()
    )


    history.reverse()


    model_messages = [

        {
            "role":
                message.role,

            "content":
                message.content,
        }

        for message
        in history

        if message.role
        in {
            "user",
            "assistant",
        }
    ]


    # ======================================================
    # 8. Generate Response
    # ======================================================

    try:

        # ==================================================
        # DOCUMENTS MODE
        # ==================================================

        if data.mode == "documents":

            start_time = (
                perf_counter()
            )


            rag_result = (
                generate_rag_answer(

                    question=
                        content,

                    user_id=
                        current_user.id,

                    document_id=
                        data.document_id,
                )
            )


            latency_ms = int(

                (
                    perf_counter()
                    - start_time
                )

                * 1000
            )


            rag_sources = (
                rag_result.get(
                    "sources",
                    [],
                )
            )


            result = {

                "text":
                    rag_result[
                        "answer"
                    ],

                "input_tokens":
                    None,

                "output_tokens":
                    None,

                "latency_ms":
                    latency_ms,

                "sources":
                    rag_sources,

                "used_tools":
                    [],

                "action_items":
                    [],

                "proposed_actions":
                    [],

                "confidence": (
                    "high"
                    if rag_sources
                    else "low"
                ),
            }


            prompt_version = (
                "rag-v1"
            )


        # ==================================================
        # AGENT MODE
        # ==================================================

        elif data.mode == "agent":

            start_time = (
                perf_counter()
            )


            agent_result = run_agent(

                message=
                    content,

                user_id=
                    current_user.id,

                db=
                    db,

                document_id=
                    data.document_id,
            )


            latency_ms = int(

                (
                    perf_counter()
                    - start_time
                )

                * 1000
            )


            agent_payload = (
                agent_result
                .model_dump()
            )


            result = {

                "text":
                    agent_payload[
                        "answer"
                    ],

                "input_tokens":
                    None,

                "output_tokens":
                    None,

                "latency_ms":
                    latency_ms,

                "sources":
                    agent_payload[
                        "sources"
                    ],

                "used_tools":
                    agent_payload[
                        "used_tools"
                    ],

                "action_items":
                    agent_payload[
                        "action_items"
                    ],

                "proposed_actions":
                    agent_payload.get(
                        "proposed_actions",
                        [],
                    ),

                "confidence":
                    agent_payload[
                        "confidence"
                    ],
            }


            prompt_version = (
                "agent-v1"
            )


        # ==================================================
        # GENERAL CHAT MODE
        # ==================================================

        else:

            chat_result = (
                generate_chat_response(
                    model_messages
                )
            )


            result = {

                "text":
                    chat_result[
                        "text"
                    ],

                "input_tokens":
                    chat_result[
                        "input_tokens"
                    ],

                "output_tokens":
                    chat_result[
                        "output_tokens"
                    ],

                "latency_ms":
                    chat_result[
                        "latency_ms"
                    ],

                "sources":
                    [],

                "used_tools":
                    [],

                "action_items":
                    [],

                "proposed_actions":
                    [],

                "confidence":
                    None,
            }


            prompt_version = (
                "chat-v1"
            )


    # ======================================================
    # AI Failure
    # ======================================================

    except Exception as exc:

        print(
            "AI ERROR:",
            type(exc).__name__,
            str(exc),
        )


        failed_request = (
            AIRequest(

                user_id=
                    current_user.id,

                model=
                    settings.OPENAI_CHAT_MODEL,

                prompt_version=(

                    "agent-v1"

                    if data.mode
                    == "agent"

                    else (
                        "rag-v1"

                        if data.mode
                        == "documents"

                        else "chat-v1"
                    )
                ),

                status=
                    "failed",
            )
        )


        db.add(
            failed_request
        )

        db.commit()


        raise HTTPException(

            status_code=
                status.HTTP_502_BAD_GATEWAY,

            detail=(
                "AI provider request failed"
            ),
        )


    # ======================================================
    # 9. Save Assistant Message
    # ======================================================

    assistant_message = Message(

        conversation_id=
            conversation.id,

        role=
            "assistant",

        content=
            result[
                "text"
            ],

        model=
            settings.OPENAI_CHAT_MODEL,

        input_tokens=
            result[
                "input_tokens"
            ],

        output_tokens=
            result[
                "output_tokens"
            ],

        latency_ms=
            result[
                "latency_ms"
            ],
    )


    db.add(
        assistant_message
    )


    db.flush()


    # ======================================================
    # 10. Save Assistant Metadata
    # ======================================================

    assistant_metadata = (
        MessageMetadata(

            message_id=
                assistant_message.id,

            mode=
                data.mode,

            document_id=
                data.document_id,

            confidence=
                result[
                    "confidence"
                ],
        )
    )


    db.add(
        assistant_metadata
    )


    # ======================================================
    # 11. Save Sources
    # ======================================================

    for source in result[
        "sources"
    ]:

        filename = (
            source.get(
                "filename"
            )
        )


        if not filename:
            continue


        row = MessageSource(

            message_id=
                assistant_message.id,

            document_id=
                source.get(
                    "document_id"
                ),

            filename=
                filename,

            page=
                source.get(
                    "page"
                ),

            score=
                source.get(
                    "score"
                ),
        )


        db.add(
            row
        )


    # ======================================================
    # 12. Save Agent Tool Calls
    # ======================================================

    seen_tools = set()


    for tool_name in result[
        "used_tools"
    ]:

        if tool_name in seen_tools:
            continue


        seen_tools.add(
            tool_name
        )


        row = MessageToolCall(

            message_id=
                assistant_message.id,

            tool_name=
                tool_name,
        )


        db.add(
            row
        )


    # ======================================================
    # 13. Save Agent Action Items
    # ======================================================

    for action in result[
        "action_items"
    ]:

        row = MessageActionItem(

            message_id=
                assistant_message.id,

            title=
                action[
                    "title"
                ],

            description=
                action[
                    "description"
                ],

            priority=
                action[
                    "priority"
                ],
        )


        db.add(
            row
        )


    # ======================================================
    # 14. Save Proposed Executable Actions
    #
    # IMPORTANT:
    # These are stored only as PENDING ActionRequest rows.
    # The agent never executes an external side effect.
    # Human approval + explicit execution are still required.
    # ======================================================

    for proposed_action in result.get(
        "proposed_actions",
        [],
    ):

        action_type = str(
            proposed_action.get(
                "action_type",
                "",
            )
        ).strip()


        title = str(
            proposed_action.get(
                "title",
                "",
            )
        ).strip()


        payload = (
            proposed_action.get(
                "payload"
            )
            or {}
        )


        if not title:

            continue


        # --------------------------------------------------
        # Email draft
        # --------------------------------------------------

        if action_type == "email":

            recipient = str(
                payload.get(
                    "to",
                    "",
                )
            ).strip()


            subject = str(
                payload.get(
                    "subject",
                    "",
                )
            ).strip()


            body = str(
                payload.get(
                    "body",
                    "",
                )
            ).strip()


            if not (
                recipient
                and subject
                and body
            ):

                continue


            clean_payload = {
                "to":
                    recipient,

                "subject":
                    subject,

                "body":
                    body,
            }


        # --------------------------------------------------
        # Calendar draft
        # --------------------------------------------------

        elif action_type == "calendar":

            event_title = str(
                payload.get(
                    "title",
                    "",
                )
            ).strip()


            start_time = str(
                payload.get(
                    "start_time",
                    "",
                )
            ).strip()


            end_time = str(
                payload.get(
                    "end_time",
                    "",
                )
            ).strip()


            description = str(
                payload.get(
                    "description",
                    "",
                )
            ).strip()


            timezone_name = str(
                payload.get(
                    "timezone",
                    "",
                )
            ).strip()


            if not (
                event_title
                and start_time
                and end_time
                and timezone_name
            ):

                continue


            try:

                parsed_start = (
                    datetime.fromisoformat(
                        start_time.replace(
                            "Z",
                            "+00:00",
                        )
                    )
                )

                parsed_end = (
                    datetime.fromisoformat(
                        end_time.replace(
                            "Z",
                            "+00:00",
                        )
                    )
                )


                if (
                    parsed_start.utcoffset()
                    is None
                    or parsed_end.utcoffset()
                    is None
                    or parsed_end
                    <= parsed_start
                ):

                    continue


                if (
                    "/" not in timezone_name
                    and timezone_name != "UTC"
                ):

                    continue


            except ValueError:

                continue


            clean_payload = {
                "title":
                    event_title,

                "start_time":
                    start_time,

                "end_time":
                    end_time,

                "description":
                    description,

                "timezone":
                    timezone_name,
            }


        # --------------------------------------------------
        # Generic webhook draft
        #
        # The agent may only propose the fixed demo_echo
        # target. data_json is parsed here so ActionRequest
        # stores a real JSON object for n8n.
        # --------------------------------------------------

        elif action_type == "webhook":

            target = str(
                payload.get(
                    "target",
                    "",
                )
            ).strip()


            data_json = str(
                payload.get(
                    "data_json",
                    "",
                )
            ).strip()


            if target != "demo_echo":

                continue


            try:

                data_object = json.loads(
                    data_json
                )


            except json.JSONDecodeError:

                continue


            if not isinstance(
                data_object,
                dict,
            ):

                continue


            clean_payload = {
                "target":
                    "demo_echo",

                "data":
                    data_object,
            }


        else:

            continue


        action_row = ActionRequest(

            user_id=
                current_user.id,

            message_id=
                assistant_message.id,

            action_type=
                action_type,

            status=
                "pending",

            title=
                title[:255],

            payload=
                clean_payload,
        )


        db.add(
            action_row
        )


    # ======================================================
    # 15. AI Request Log
    # ======================================================

    ai_request = AIRequest(

        user_id=
            current_user.id,

        model=
            settings.OPENAI_CHAT_MODEL,

        prompt_version=
            prompt_version,

        latency_ms=
            result[
                "latency_ms"
            ],

        input_tokens=
            result[
                "input_tokens"
            ],

        output_tokens=
            result[
                "output_tokens"
            ],

        status=
            "success",
    )


    db.add(
        ai_request
    )


    # ======================================================
    # 16. Commit
    # ======================================================

    db.commit()


    db.refresh(
        user_message
    )

    db.refresh(
        assistant_message
    )


    # ======================================================
    # 17. Response
    # ======================================================

    return {

        "user_message":
            serialize_message(
                db,
                user_message,
            ),

        "assistant_message":
            serialize_message(
                db,
                assistant_message,
            ),
    }