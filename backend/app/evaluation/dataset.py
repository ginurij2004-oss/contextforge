EVALUATION_DATASET = [

    # ======================================================
    # Q1
    # Case Study 1: High Employee Turnover
    # PDF Page 1
    # ======================================================

    {
        "id": "q1",

        "question":
            "What would a stay interview look like for employees?",

        "expected_document":
            "HRM_Workshop_Case_Study_QA(1).pdf",

        "expected_page":
            1,

        "expected_keywords": [
            "quarterly",
            "leave",
            "keeping",
        ],

        "expect_answer":
            True,
    },


    # ======================================================
    # Q2
    # Case Study 2: Poor Recruitment Decisions
    # PDF Page 1
    # ======================================================

    {
        "id": "q2",

        "question":
            "How could a paid two-week trial project improve hiring decisions?",

        "expected_document":
            "HRM_Workshop_Case_Study_QA(1).pdf",

        "expected_page":
            1,

        "expected_keywords": [
            "fit",
            "competence",
            "permanent",
        ],

        "expect_answer":
            True,
    },


    # ======================================================
    # Q3
    # Case Study 5: Weak Reward System
    # PDF Page 2
    # ======================================================

    {
        "id": "q3",

        "question":
            "How does the point-based cafeteria rewards system work?",

        "expected_document":
            "HRM_Workshop_Case_Study_QA(1).pdf",

        "expected_page":
            2,

        "expected_keywords": [
            "points",
            "performance",
            "rewards",
        ],

        "expect_answer":
            True,
    },


    # ======================================================
    # Q4
    # Case Study 7: Conflict in Project Teams
    # PDF Page 3
    # ======================================================

    {
        "id": "q4",

        "question":
            "How could a shared Definition of Done reduce disputes between developers and QA?",

        "expected_document":
            "HRM_Workshop_Case_Study_QA(1).pdf",

        "expected_page":
            3,

        "expected_keywords": [
            "checklist",
            "quality",
            "ambiguity",
        ],

        "expect_answer":
            True,
    },


    # ======================================================
    # Q5
    # Case Study 8: Lack of Skills Development
    # PDF Page 3
    # ======================================================

    {
        "id": "q5",

        "question":
            "How could a buddy learning system help employees develop new skills?",

        "expected_document":
            "HRM_Workshop_Case_Study_QA(1).pdf",

        "expected_page":
            3,

        "expected_keywords": [
            "peer",
            "skills",
            "relationships",
        ],

        "expect_answer":
            True,
    },


    # ======================================================
    # Q6
    # Case Study 11:
    # Employee Burnout Due to Continuous Project Deadlines
    # PDF Page 4
    # ======================================================

    {
        "id": "q6",

        "question":
            "How can a traffic-light workload self-check help prevent employee burnout?",

        "expected_document":
            "HRM_Workshop_Case_Study_QA(1).pdf",

        "expected_page":
            4,

        "expected_keywords": [
            "green",
            "amber",
            "red",
        ],

        "expect_answer":
            True,
    },


    # ======================================================
    # Q7
    # Case Study 14: Resistance to Organizational Change
    # PDF Page 5
    # ======================================================

    {
        "id": "q7",

        "question":
            "How can a change champions network help employees adopt a new system?",

        "expected_document":
            "HRM_Workshop_Case_Study_QA(1).pdf",

        "expected_page":
            5,

        "expected_keywords": [
            "peer",
            "champions",
            "adopt",
        ],

        "expect_answer":
            True,
    },


    # ======================================================
    # Q8
    # Case Study 16:
    # Ethical Issues in Human Resource Management
    # PDF Page 6
    # ======================================================

    {
        "id": "q8",

        "question":
            "How could an anonymous independently reviewed ethics hotline rebuild employee trust?",

        "expected_document":
            "HRM_Workshop_Case_Study_QA(1).pdf",

        "expected_page":
            6,

        "expected_keywords": [
            "neutral",
            "third party",
            "trust",
        ],

        "expect_answer":
            True,
    },


    # ======================================================
    # Q9
    # NO-ANSWER TEST
    # This information does NOT exist in the HRM PDF.
    # ======================================================

    {
        "id": "q9",

        "question":
            "What is the population of Mars in 2026?",

        "expected_document":
            None,

        "expected_page":
            None,

        "expected_keywords":
            [],

        "expect_answer":
            False,
    },


    # ======================================================
    # Q10
    # NO-ANSWER TEST
    # This information does NOT exist in the HRM PDF.
    # ======================================================

    {
        "id": "q10",

        "question":
            "Who won the FIFA World Cup in 2030?",

        "expected_document":
            None,

        "expected_page":
            None,

        "expected_keywords":
            [],

        "expect_answer":
            False,
    },

]