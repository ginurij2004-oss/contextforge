import re


# ==========================================================
# Clean extracted PDF text
# ==========================================================

def clean_text(
    text: str,
) -> str:

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ==========================================================
# Chunk Text
# ==========================================================

def chunk_text(
    text: str,
    chunk_size: int = 2500,
    overlap: int = 300,
) -> list[str]:

    text = clean_text(
        text
    )

    if not text:
        return []


    # ------------------------------------------------------
    # Validate configuration
    # ------------------------------------------------------

    if chunk_size <= 0:

        raise ValueError(
            "chunk_size must be greater than 0"
        )


    if overlap < 0:

        raise ValueError(
            "overlap cannot be negative"
        )


    if overlap >= chunk_size:

        raise ValueError(
            "overlap must be smaller than chunk_size"
        )


    # ------------------------------------------------------
    # Small text = one chunk
    # ------------------------------------------------------

    if len(text) <= chunk_size:

        return [
            text
        ]


    chunks = []

    start = 0


    while start < len(text):

        end = min(
            start + chunk_size,
            len(text),
        )


        chunk = text[
            start:end
        ]


        # --------------------------------------------------
        # Try to stop on a sentence boundary
        # --------------------------------------------------

        if end < len(text):

            sentence_end = max(
                chunk.rfind(". "),
                chunk.rfind("? "),
                chunk.rfind("! "),
            )


            # Don't cut too early.
            # Sentence boundary must be at least 60%
            # into the current chunk.

            if (
                sentence_end
                > chunk_size * 0.60
            ):

                end = (
                    start
                    + sentence_end
                    + 1
                )

                chunk = text[
                    start:end
                ]


        chunk = chunk.strip()


        if chunk:

            chunks.append(
                chunk
            )


        # --------------------------------------------------
        # Reached end of text
        # --------------------------------------------------

        if end >= len(text):

            break


        # --------------------------------------------------
        # Move forward with overlap
        # --------------------------------------------------

        next_start = (
            end - overlap
        )


        # Safety protection
        # against infinite loops

        if next_start <= start:

            next_start = end


        start = next_start


    return chunks