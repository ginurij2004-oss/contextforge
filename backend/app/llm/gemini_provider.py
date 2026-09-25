from time import perf_counter

from google import genai
from google.genai import types

from app.core.config import settings


# ==========================================================
# Gemini Client
# ==========================================================

def get_gemini_client():

    if not settings.GEMINI_API_KEY:

        raise RuntimeError(
            "GEMINI_API_KEY is not configured"
        )


    return genai.Client(
        api_key=
            settings.GEMINI_API_KEY
    )


# ==========================================================
# Convert ContextForge Roles → Gemini Roles
# ==========================================================

def convert_messages(
    messages: list[dict],
):

    contents = []


    for message in messages:

        role = message.get(
            "role"
        )

        content = message.get(
            "content",
            "",
        )


        if not content:
            continue


        # Gemini uses "model"
        # instead of "assistant".

        if role == "assistant":

            gemini_role = "model"

        else:

            gemini_role = "user"


        contents.append(

            types.Content(

                role=
                    gemini_role,

                parts=[
                    types.Part(
                        text=
                            str(content)
                    )
                ],
            )
        )


    return contents


# ==========================================================
# Generate Using Gemini
# ==========================================================

def generate_gemini_response(
    messages: list[dict],
    system_prompt: str,
):

    client = (
        get_gemini_client()
    )


    contents = convert_messages(
        messages
    )


    start_time = (
        perf_counter()
    )


    response = (
        client.models.generate_content(

            model=
                settings.GEMINI_CHAT_MODEL,

            contents=
                contents,

            config=
                types.GenerateContentConfig(

                    system_instruction=
                        system_prompt
                ),
        )
    )


    latency_ms = int(

        (
            perf_counter()
            - start_time
        )

        * 1000
    )


    # ======================================================
    # Token usage
    # ======================================================

    usage = getattr(
        response,
        "usage_metadata",
        None,
    )


    input_tokens = None
    output_tokens = None


    if usage is not None:

        input_tokens = getattr(
            usage,
            "prompt_token_count",
            None,
        )

        output_tokens = getattr(
            usage,
            "candidates_token_count",
            None,
        )


    return {

        "text":
            (
                response.text
                or ""
            ).strip(),

        "provider":
            "gemini",

        "model":
            settings.GEMINI_CHAT_MODEL,

        "input_tokens":
            input_tokens,

        "output_tokens":
            output_tokens,

        "latency_ms":
            latency_ms,
    }