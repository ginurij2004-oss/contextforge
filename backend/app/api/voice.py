from io import BytesIO

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from openai import OpenAI

from app.api.auth import (
    get_current_user,
)

from app.core.config import (
    settings,
)

from app.models.user import User


# ==========================================================
# Router
# ==========================================================

router = APIRouter(
    prefix="/voice",
    tags=["Voice"],
)


# ==========================================================
# OpenAI Client
# ==========================================================

client = OpenAI(
    api_key=
        settings.OPENAI_API_KEY
)


# ==========================================================
# Allowed Audio Types
# ==========================================================

ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/x-m4a",
    "audio/wav",
    "audio/wave",
    "audio/x-wav",
    "application/octet-stream",
}


MAX_AUDIO_SIZE_BYTES = (
    10
    * 1024
    * 1024
)


# ==========================================================
# Speech-to-Text
# ==========================================================

@router.post(
    "/transcribe",
)
async def transcribe_voice(

    file: UploadFile = File(...),

    current_user: User = Depends(
        get_current_user
    ),
):

    # Authentication is intentionally required.
    # We do not need to use the user object further here.
    del current_user


    # ======================================================
    # Normalize Content Type
    #
    # Browser MediaRecorder can return:
    #
    # audio/webm;codecs=opus
    #
    # We only need the base type:
    #
    # audio/webm
    # ======================================================

    raw_content_type = (
        file.content_type
        or ""
    ).lower().strip()


    base_content_type = (
        raw_content_type
        .split(
            ";",
            1,
        )[0]
        .strip()
    )


    print(
        "VOICE UPLOAD CONTENT TYPE:",
        raw_content_type,
    )


    if (
        base_content_type
        and base_content_type
        not in ALLOWED_AUDIO_TYPES
    ):

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=(
                "Unsupported audio format: "
                f"{raw_content_type}"
            ),
        )


    # ======================================================
    # Read Audio
    # ======================================================

    audio_bytes = (
        await file.read()
    )


    if (
        not audio_bytes
    ):

        raise HTTPException(
            status_code=
                status.HTTP_400_BAD_REQUEST,

            detail=
                "Audio file is empty",
        )


    # ======================================================
    # Size Validation
    # ======================================================

    if (
        len(
            audio_bytes
        )
        > MAX_AUDIO_SIZE_BYTES
    ):

        raise HTTPException(
            status_code=
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,

            detail=
                "Audio file is too large",
        )


    # ======================================================
    # Prepare File for OpenAI
    # ======================================================

    filename = (
        file.filename
        or "voice-input.webm"
    )


    audio_file = BytesIO(
        audio_bytes
    )


    audio_file.name = (
        filename
    )


    # ======================================================
    # OpenAI Transcription
    # ======================================================

    try:

        transcription = (
            client.audio
            .transcriptions
            .create(

                model=
                    settings
                    .OPENAI_TRANSCRIPTION_MODEL,

                file=
                    audio_file,
            )
        )


    except Exception as error:

        print(
            "VOICE TRANSCRIPTION ERROR:",
            type(
                error
            ).__name__,
        )


        print(
            "VOICE TRANSCRIPTION DETAIL:",
            str(
                error
            ),
        )


        raise HTTPException(
            status_code=
                status.HTTP_502_BAD_GATEWAY,

            detail=(
                "Speech transcription "
                "service failed"
            ),
        ) from error


    # ======================================================
    # Extract Text
    # ======================================================

    text = (
        getattr(
            transcription,
            "text",
            "",
        )
        or ""
    ).strip()


    if (
        not text
    ):

        raise HTTPException(
            status_code=
                status.HTTP_422_UNPROCESSABLE_ENTITY,

            detail=
                "No speech was detected",
        )


    # ======================================================
    # Response
    # ======================================================

    return {
        "text":
            text,
    }