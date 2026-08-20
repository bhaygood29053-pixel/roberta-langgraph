from roberta.decision_synthesis import (
    build_decision_synthesis_system_message,
    decision_response_violation,
)
from roberta.recommendation_policy import recommendation_intent


SOLANA_MINT = "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN"


def test_exact_mint_solana_risk_question_is_recognized():
    objective = f"On Solana, is exact mint {SOLANA_MINT} risky?"

    assert recommendation_intent(objective) == "risk_assessment"


def test_exact_mint_solana_safety_question_is_recognized():
    objective = f"On Solana, is exact mint {SOLANA_MINT} safe?"

    assert recommendation_intent(objective) == "risk_assessment"


def test_exact_mint_risk_question_receives_decision_contract():
    objective = f"On Solana, is exact mint {SOLANA_MINT} risky?"

    message = build_decision_synthesis_system_message(objective)

    assert message is not None
    assert "recognized_intent: risk_assessment" in message
    assert "Risk and Evidence quality as separate dimensions" in message


def test_exact_mint_risk_answer_without_dimensions_is_rejected():
    objective = f"On Solana, is exact mint {SOLANA_MINT} risky?"

    assert (
        decision_response_violation(
            objective,
            "I cannot verify the current risk from the available evidence.",
        )
        == "risk_evidence_separation_not_disclosed"
    )


def test_nonrisk_exact_mint_question_remains_general():
    objective = f"On Solana, describe exact mint {SOLANA_MINT}."

    assert recommendation_intent(objective) == "general"
