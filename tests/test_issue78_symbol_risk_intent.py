from roberta.decision_synthesis import decision_response_violation
from roberta.recommendation_policy import (
    recommendation_evidence_plan,
    recommendation_intent,
)


QUESTION = (
    "On Solana, what is the verified risk for JUP? "
    "Do not guess a mint if the symbol is insufficient."
)


def test_symbol_only_verified_risk_question_is_risk_assessment() -> None:
    assert recommendation_intent(QUESTION) == "risk_assessment"
    assert recommendation_evidence_plan(QUESTION)["required_services"] == [
        "risk_check",
        "market_report",
        "tokenomics",
    ]


def test_symbol_only_unavailable_risk_answer_still_requires_evidence_quality() -> None:
    answer = (
        "I can't produce a verified risk assessment for JUP on Solana. "
        "The symbol alone is insufficient; provide the exact mint address."
    )

    assert (
        decision_response_violation(QUESTION, answer)
        == "risk_evidence_separation_not_disclosed"
    )


def test_symbol_only_unavailable_risk_answer_passes_with_separate_dimensions() -> None:
    answer = (
        "I can't produce a verified risk assessment for JUP on Solana because "
        "the symbol alone is insufficient.\n\n"
        "Risk: unavailable until an exact mint is supplied.\n"
        "Evidence quality: insufficient for canonical asset identity."
    )

    assert decision_response_violation(QUESTION, answer) is None
