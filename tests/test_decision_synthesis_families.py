import pytest

from roberta.decision_synthesis import build_decision_synthesis_system_message


@pytest.mark.parametrize(
    ("objective", "intent"),
    [
        ("Full assessment of XNT", "full_assessment"),
        ("Should I buy AGI?", "trade_decision"),
        ("Can I buy $500 of AGI?", "trade_size"),
        ("Is AGI risky?", "risk_assessment"),
        ("Which token is safer?", "safer_asset"),
        ("Is this liquidity too thin?", "liquidity_risk"),
        ("Should I provide liquidity to this pool?", "lp_decision"),
        ("What changed since yesterday?", "market_change"),
        ("Why is the price dropping?", "price_move_reason"),
    ],
)
def test_every_decision_family_gets_the_same_trust_contract(objective, intent):
    message = build_decision_synthesis_system_message(objective)

    assert message is not None
    assert f"recognized_intent: {intent}" in message
    assert "Lead with the recommendation, conclusion, or blocker immediately" in message
    assert "Risk and Evidence quality as separate dimensions" in message
    assert "Missing evidence remains unknown, never zero" in message
    assert "never recalculate, reconcile, strengthen, weaken, or replace" in message
    assert "read-only and non-authorizing" in message


def test_trade_size_brief_names_pretrade_requirement_without_authorizing_it():
    message = build_decision_synthesis_system_message("Can I buy $500 of AGI?")

    assert message is not None
    assert "required_evidence_services: pre_trade_check, market_report, risk_check" in message
    assert "does not grant pre_trade_check" in message


def test_lp_brief_keeps_lp_specific_unknowns_as_evidence_not_inference():
    message = build_decision_synthesis_system_message("Should I add liquidity?")

    assert message is not None
    assert "lp_specific_evidence_when_available" in message
    assert "unavailable, or insufficient evidence" in message


def test_price_move_brief_requires_historical_context_but_cannot_invent_causality():
    message = build_decision_synthesis_system_message("Why is the price falling?")

    assert message is not None
    assert "historical_context" in message
    assert "recent_verified_activity_when_available" in message
    assert "never recalculate, reconcile, strengthen, weaken, or replace" in message


def test_full_assessment_brief_requires_complete_structured_coverage():
    message = build_decision_synthesis_system_message("Full assessment of XNT")

    assert message is not None
    assert (
        "required_evidence_services: market_report, rank, tokenomics, "
        "historical_compare, risk_check"
    ) in message
    assert "structured full assessment" in message
    assert "all-available verified history" in message
    assert "Do not compress the assessment into only 2-4 reasons" in message
