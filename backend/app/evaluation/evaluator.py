from time import perf_counter

from app.evaluation.dataset import (
    EVALUATION_DATASET,
)

from app.evaluation.metrics import (
    calculate_average,
    calculate_keyword_match,
    document_was_retrieved,
    get_top_score,
    page_was_retrieved,
    to_percentage,
)

from app.rag.pipeline import (
    generate_rag_answer,
)


# ==========================================================
# Check that dataset was actually configured
# ==========================================================

def validate_dataset():

    if not EVALUATION_DATASET:

        raise ValueError(
            "Evaluation dataset is empty."
        )


    for case in EVALUATION_DATASET:

        question = case.get(
            "question",
            "",
        )


        if (
            "REPLACE WITH QUESTION"
            in question
        ):

            raise ValueError(
                "Please configure "
                "backend/app/evaluation/"
                "dataset.py before running "
                "the evaluation."
            )


        expected_document = (
            case.get(
                "expected_document"
            )
        )


        if (
            expected_document
            and expected_document
            == "YOUR_DOCUMENT.pdf"
        ):

            raise ValueError(
                "Please replace "
                "YOUR_DOCUMENT.pdf in "
                "the evaluation dataset."
            )


# ==========================================================
# Run complete evaluation
# ==========================================================

def run_evaluation(
    user_id: int,
    top_k: int | None = None,
    score_threshold: float | None = None,
    document_id: int | None = None,
):
    validate_dataset()


    case_results = []


    # ======================================================
    # Run every evaluation question
    # ======================================================

    for case in EVALUATION_DATASET:

        question = case[
            "question"
        ]

        expect_answer = case[
            "expect_answer"
        ]


        # --------------------------------------------------
        # Measure complete RAG latency
        # --------------------------------------------------

        start_time = (
            perf_counter()
        )


        rag_result = (
    generate_rag_answer(
        question=question,
        user_id=user_id,
        top_k=top_k,
        score_threshold=score_threshold,
        document_id=document_id,
    )
)


        latency_ms = int(
            (
                perf_counter()
                - start_time
            )
            * 1000
        )


        # --------------------------------------------------
        # Get answer + sources
        # --------------------------------------------------

        answer = (
            rag_result.get(
                "answer",
                "",
            )
        )


        sources = (
            rag_result.get(
                "sources",
                [],
            )
        )


        # --------------------------------------------------
        # Was anything retrieved?
        # --------------------------------------------------

        retrieval_hit = (
            len(sources) > 0
        )


        # --------------------------------------------------
        # Correct document
        # --------------------------------------------------

        document_correct = None


        if expect_answer:

            document_correct = (
                document_was_retrieved(

                    sources,

                    case.get(
                        "expected_document"
                    ),
                )
            )


        # --------------------------------------------------
        # Correct page
        # --------------------------------------------------

        page_correct = None


        if expect_answer:

            page_correct = (
                page_was_retrieved(

                    sources,

                    case.get(
                        "expected_document"
                    ),

                    case.get(
                        "expected_page"
                    ),
                )
            )


        # --------------------------------------------------
        # Keyword answer score
        # --------------------------------------------------

        keyword_match = None


        if expect_answer:

            keyword_match = (
                calculate_keyword_match(

                    answer,

                    case.get(
                        "expected_keywords",
                        [],
                    ),
                )
            )


        # --------------------------------------------------
        # No-answer correctness
        #
        # Correct behavior:
        # no relevant RAG sources
        # --------------------------------------------------

        no_answer_correct = None


        if not expect_answer:

            no_answer_correct = (
                len(sources) == 0
            )


        # --------------------------------------------------
        # Highest similarity score
        # --------------------------------------------------

        top_score = (
            get_top_score(
                sources
            )
        )


        # --------------------------------------------------
        # Save result
        # --------------------------------------------------

        case_results.append({

            "id":
                case["id"],

            "question":
                question,

            "expect_answer":
                expect_answer,

            "answer":
                answer,

            "sources_count":
                len(sources),

            "retrieval_hit":
                retrieval_hit,

            "document_correct":
                document_correct,

            "page_correct":
                page_correct,

            "keyword_match":
                keyword_match,

            "no_answer_correct":
                no_answer_correct,

            "top_score":
                top_score,

            "latency_ms":
                latency_ms,
        })


    # ======================================================
    # Separate answerable questions
    # ======================================================

    answerable_results = [

        result

        for result in case_results

        if result[
            "expect_answer"
        ]
    ]


    no_answer_results = [

        result

        for result in case_results

        if not result[
            "expect_answer"
        ]
    ]


    # ======================================================
    # Retrieval Hit Rate
    #
    # Only measured for questions that SHOULD have answers.
    # ======================================================

    retrieval_hit_rate = (
        calculate_average([

            result[
                "retrieval_hit"
            ]

            for result
            in answerable_results
        ])
    )


    # ======================================================
    # Document Accuracy
    # ======================================================

    document_accuracy = (
        calculate_average([

            result[
                "document_correct"
            ]

            for result
            in answerable_results
        ])
    )


    # ======================================================
    # Page Accuracy
    # ======================================================

    page_accuracy = (
        calculate_average([

            result[
                "page_correct"
            ]

            for result
            in answerable_results
        ])
    )


    # ======================================================
    # Keyword Accuracy
    # ======================================================

    keyword_accuracy = (
        calculate_average([

            result[
                "keyword_match"
            ]

            for result
            in answerable_results
        ])
    )


    # ======================================================
    # No-answer Accuracy
    # ======================================================

    no_answer_accuracy = (
        calculate_average([

            result[
                "no_answer_correct"
            ]

            for result
            in no_answer_results
        ])
    )


    # ======================================================
    # Average Retrieval Score
    # ======================================================

    average_top_score = (
        calculate_average([

            result[
                "top_score"
            ]

            for result
            in answerable_results
        ])
    )


    # ======================================================
    # Average End-to-End RAG Latency
    # ======================================================

    average_latency_ms = (
        calculate_average([

            result[
                "latency_ms"
            ]

            for result
            in case_results
        ])
        or 0
    )


    # ======================================================
    # Overall Evaluation Score
    #
    # Average only the actual accuracy metrics.
    # Retrieval similarity score is NOT included because
    # similarity score is not an accuracy metric.
    # ======================================================

    overall_score = (
        calculate_average([

            retrieval_hit_rate,

            document_accuracy,

            page_accuracy,

            keyword_accuracy,

            no_answer_accuracy,
        ])
    )


    # ======================================================
    # Final report
    # ======================================================

    return {

        "total_questions":
            len(
                case_results
            ),

        "answerable_questions":
            len(
                answerable_results
            ),

        "no_answer_questions":
            len(
                no_answer_results
            ),

        "retrieval_hit_rate":
            to_percentage(
                retrieval_hit_rate
            ),

        "document_accuracy":
            to_percentage(
                document_accuracy
            ),

        "page_accuracy":
            to_percentage(
                page_accuracy
            ),

        "keyword_accuracy":
            to_percentage(
                keyword_accuracy
            ),

        "no_answer_accuracy":
            to_percentage(
                no_answer_accuracy
            ),

        "average_top_score": (
            round(
                average_top_score,
                4,
            )

            if average_top_score
            is not None

            else None
        ),

        "average_latency_ms":
            round(
                average_latency_ms,
                2,
            ),

        "overall_score":
            to_percentage(
                overall_score
            ),

        "results":
            case_results,
    }