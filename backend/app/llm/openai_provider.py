from time import perf_counter

from openai import OpenAI

from app.core.config import settings


# ==========================================================
# OpenAI Client
# ==========================================================

client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


# ==========================================================
# Generate Using OpenAI
# ==========================================================

def generate_openai_response(
    messages: list[dict],
    system_prompt: str,
):

    input_messages = [

        {
            "role":
                "developer",

            "content":
                system_prompt,
        },

        *messages,
    ]


    start_time = (
        perf_counter()
    )


    response = client.responses.create(

        model=
            settings.OPENAI_CHAT_MODEL,

        input=
            input_messages,
    )


    latency_ms = int(

        (
            perf_counter()
            - start_time
        )

        * 1000
    )


    usage = (
        response.usage
    )


    return {

        "text":
            (
                response.output_text
                or ""
            ).strip(),

        "provider":
            "openai",

        "model":
            settings.OPENAI_CHAT_MODEL,

        "input_tokens": (
            usage.input_tokens
            if usage
            else None
        ),

        "output_tokens": (
            usage.output_tokens
            if usage
            else None
        ),

        "latency_ms":
            latency_ms,
    }