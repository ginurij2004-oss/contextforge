from app.llm.router import (
    generate_llm_response,
)


# ==========================================================
# General Chat System Prompt
# ==========================================================

CHAT_SYSTEM_PROMPT = """
You are ContextForge, a professional enterprise AI assistant.

Provide clear, accurate and useful answers.

Be concise unless the user asks for detail.

Do not invent facts when information is uncertain.
"""


# ==========================================================
# Generate General Chat Response
# ==========================================================

def generate_chat_response(
    messages: list[dict],
):

    return generate_llm_response(

        messages=
            messages,

        system_prompt=
            CHAT_SYSTEM_PROMPT,
    )