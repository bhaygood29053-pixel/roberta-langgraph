"""Public-boundary regression matrix for canonical X1 asset-context routing."""

from __future__ import annotations

import sys
from types import ModuleType


# recommendation_policy is protected/private and intentionally absent from the
# public-shell CI checkout. Supply only the two narrow planner dependencies so
# this test can verify public X1 Scout routing without weakening that boundary.
if "roberta.recommendation_policy" not in sys.modules:
    policy = ModuleType("roberta.recommendation_policy")

    def recommendation_intent(objective: object) -> str:
        normalized = " ".join(str(objective or "").lower().split())
        if "full assessment" in normalized or "due diligence" in normalized:
            return "full_assessment"
        return "none"

    def autonomous_x1_operations_for_recommendation(objective: object) -> list[str]:
        return []

    policy.recommendation_intent = recommendation_intent
    policy.autonomous_x1_operations_for_recommendation = (
        autonomous_x1_operations_for_recommendation
    )
    sys.modules["roberta.recommendation_policy"] = policy

from roberta.x1_scout.planner import enforce_plan  # noqa: E402


MINT = "EFPkbXTdr3c7aRbCEKoJDYdbbzgzVDBShYGybP3gQwmy"


def _plan(objective: str, proposed: list[str], **request_overrides):
    request = {"asset": MINT, "objective": objective, **request_overrides}
    return enforce_plan(request, {"operations": proposed})["operations"]


def test_market_tokenomics_and_risk_share_one_canonical_scan() -> None:
    assert _plan(
        "Assess this token's current market, supply authorities, and risk",
        ["market_report", "tokenomics", "risk_check"],
    ) == ["instant_x1_scan"]


def test_market_only_question_uses_canonical_scan() -> None:
    assert _plan(
        "What is the current market state for this asset?",
        ["market_report"],
    ) == ["instant_x1_scan"]


def test_tokenomics_only_question_uses_canonical_scan() -> None:
    assert _plan(
        "What is the mint authority and total supply?",
        ["tokenomics"],
    ) == ["instant_x1_scan"]


def test_risk_only_question_uses_canonical_scan() -> None:
    assert _plan(
        "Is this token risky?",
        ["risk_check"],
    ) == ["instant_x1_scan"]


def test_burn_intelligence_enriches_canonical_scan() -> None:
    assert _plan(
        "Show burn intelligence for this token",
        ["burn_intelligence"],
    ) == ["instant_x1_scan", "burn_intelligence"]


def test_discovery_intelligence_enriches_canonical_scan() -> None:
    assert _plan(
        "When was this token first observed?",
        ["discovery_intelligence"],
    ) == ["instant_x1_scan", "discovery_intelligence"]


def test_single_asset_history_enriches_canonical_scan() -> None:
    assert _plan(
        "How has this token changed over the last week?",
        ["historical_compare"],
    ) == ["instant_x1_scan", "historical_compare"]


def test_rank_only_request_remains_rank_only() -> None:
    assert _plan(
        "Rank the top 10 X1 tokens by liquidity",
        ["rank", "market_report"],
    ) == ["rank"]


def test_pair_history_comparison_does_not_force_single_asset_scan() -> None:
    assert _plan(
        "Compare AGI and XNT over their full history",
        ["historical_compare"],
        compare_asset="XNT",
    ) == ["historical_compare"]


def test_explicit_pretrade_remains_explicit_specialist_operation() -> None:
    plan = enforce_plan(
        {
            "asset": MINT,
            "objective": "Check a $500 BUY before I trade",
            "operation": "pre_trade_check",
            "action": "BUY",
            "amount_usd": 500.0,
        },
        {"operations": ["instant_x1_scan"]},
    )
    assert plan["operations"] == ["pre_trade_check"]
    assert plan["source"] == "explicit"
