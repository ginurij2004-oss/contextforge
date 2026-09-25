from typing import Any


# ==========================================================
# Normalize filename
# ==========================================================

def normalize_filename(
    filename: str | None,
) -> str:

    if not filename:
        return ""

    return (
        filename
        .strip()
        .lower()
    )


# ==========================================================
# Calculate keyword match
#
# Example:
#
# expected:
# ["annual leave", "20 days"]
#
# If answer contains both:
# score = 1.0
#
# If answer contains one:
# score = 0.5
# ==========================================================

def calculate_keyword_match(
    answer: str,
    expected_keywords: list[str],
) -> float | None:

    if not expected_keywords:
        return None


    normalized_answer = (
        answer
        .lower()
        .strip()
    )


    matches = 0


    for keyword in expected_keywords:

        normalized_keyword = (
            keyword
            .lower()
            .strip()
        )


        if (
            normalized_keyword
            in normalized_answer
        ):

            matches += 1


    return (
        matches
        / len(expected_keywords)
    )


# ==========================================================
# Check whether correct document was retrieved
# ==========================================================

def document_was_retrieved(
    sources: list[dict[str, Any]],
    expected_document: str | None,
) -> bool | None:

    if not expected_document:
        return None


    expected = normalize_filename(
        expected_document
    )


    for source in sources:

        actual = normalize_filename(
            source.get(
                "filename"
            )
        )


        if actual == expected:

            return True


    return False


# ==========================================================
# Check whether expected page was retrieved
# ==========================================================

def page_was_retrieved(
    sources: list[dict[str, Any]],
    expected_document: str | None,
    expected_page: int | None,
) -> bool | None:

    if expected_page is None:
        return None


    expected_filename = (
        normalize_filename(
            expected_document
        )
    )


    for source in sources:

        source_page = source.get(
            "page"
        )

        source_filename = (
            normalize_filename(
                source.get(
                    "filename"
                )
            )
        )


        # If document name was supplied,
        # make sure both document and page match.

        if expected_filename:

            if (
                source_filename
                == expected_filename
                and source_page
                == expected_page
            ):

                return True


        # Otherwise check page only.

        elif (
            source_page
            == expected_page
        ):

            return True


    return False


# ==========================================================
# Get highest retrieval score
# ==========================================================

def get_top_score(
    sources: list[dict[str, Any]],
) -> float | None:

    scores = []


    for source in sources:

        score = source.get(
            "score"
        )


        if isinstance(
            score,
            (int, float),
        ):

            scores.append(
                float(score)
            )


    if not scores:

        return None


    return max(
        scores
    )


# ==========================================================
# Mean helper
# ==========================================================

def calculate_average(
    values: list[
        float | int | bool | None
    ],
) -> float | None:

    cleaned = [

        float(value)

        for value in values

        if value is not None
    ]


    if not cleaned:

        return None


    return (
        sum(cleaned)
        / len(cleaned)
    )


# ==========================================================
# Percentage helper
# ==========================================================

def to_percentage(
    value: float | None,
) -> float | None:

    if value is None:
        return None


    return round(
        value * 100,
        2,
    )