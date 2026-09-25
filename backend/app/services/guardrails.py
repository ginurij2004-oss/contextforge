import re

from openai import OpenAI

from app.core.config import settings


client = OpenAI(
    api_key=settings.OPENAI_API_KEY
)


# ----------------------------------
# Prompt injection detection
# ----------------------------------

INJECTION_PATTERNS = [

    r"ignore\s+(all\s+)?previous\s+instructions",

    r"ignore\s+(all\s+)?prior\s+instructions",

    r"disregard\s+(all\s+)?previous\s+instructions",

    r"forget\s+(all\s+)?previous\s+instructions",

    r"reveal\s+(your\s+)?system\s+prompt",

    r"show\s+(me\s+)?your\s+system\s+prompt",

    r"print\s+(your\s+)?system\s+prompt",

    r"developer\s+message",

    r"override\s+your\s+instructions",
]


def detect_prompt_injection(
    text: str
) -> bool:

    normalized = text.lower()

    for pattern in INJECTION_PATTERNS:

        if re.search(
            pattern,
            normalized,
        ):

            return True

    return False


# ----------------------------------
# OpenAI moderation
# ----------------------------------

def is_flagged_content(
    text: str
) -> bool:

    response = (
        client.moderations.create(
            model="omni-moderation-latest",
            input=text,
        )
    )

    return response.results[0].flagged