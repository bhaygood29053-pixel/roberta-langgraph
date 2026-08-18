import pytest

from roberta.evidence_aware import (
    CMISEvidenceMetadataError,
    compare_chain_evidence,
    evidence_context,
    validate_evidence_metadata,
)
from roberta.pretrade_ux import build_pretrade_presentation
from roberta.recommendation_policy import (
    recommendation_evidence_plan,
    recommendation_intent,
)
from roberta.wallet_interpretation import (
    WalletInterpretationContractError,
    assert_classification_allowed,
    build_wallet_interpretation_contract,
)
from roberta.x1_scout.planner import required_operations


def _proof_categories(*, state="VERIFIED", score=100):
    return {
        name: {
            "state": state,
            "score": score,
            "reasons": [f"{name} reason"],
            "evidence_paths": [f"confidence.{name}_verified"],
        }
        for name in (
            "identity",
            "semantics",
            "freshness",
            "source_independence",
            "agreement",
            "scope",
            "historical_coverage",
            "source_traceability",
        )
    }


def _envelope(
    *,
    chain="x1",
    service="market_report",
    risk_level="HIGH",
    recommendation="WARN",
    proof_strength="STRONG",
):
    return {
        "service": service,
        "chain": chain,
        "status": "partial",
        "asset": {"symbol": "AGI", "mint": "agi-mint"},
        "data": {},
        "risk": {
            "level": risk_level,
            "recommendation": recommendation,
            "reasons": ["Liquidity is thin for the requested trade size."],
            "flags": ["THIN_LIQUIDITY"],
        },
        "confidence": {},
        "sources": [
            {"source": "provider-a", "role": "primary"},
            {"source": "x1_rpc", "role": "verifier"},
        ],
        "observed_at": "2026-08-18T09:00:00Z",
        "warnings": [],
        "errors": [],
        "evidence_receipt": {
            "receipt_id": f"er_{chain}_{service}_test",
            "schema_version": 1,
            "chain": chain,
            "service": service,
            "service_status": "partial",
            "asset": {"symbol": "AGI"},
            "observation": {
                "envelope_observed_at": "2026-08-18T09:00:00Z",
                "observed_times": ["2026-08-18T09:00:00Z"],
                "chain_positions": [{"path": "data.slot", "value": 123}],
            },
            "verification": {
                "status": "AGREEMENT",
                "code": "VALUES_AGREE",
                "independently_verified": True,
                "provider_assertion_promoted": False,
            },
            "evidence_scope": {
                "claims": [{"path": "data.scope", "value": "asset"}],
                "explicit_scope_available": True,
            },
            "freshness": {"verified": True, "flags": {"freshness_verified": True}},
            "sources": [
                {
                    "evidence_class": "reported_observation",
                    "source": "provider-a",
                    "source_role": "provider_report",
                },
                {
                    "evidence_class": "verifier_observation",
                    "source": "x1_rpc",
                    "source_role": "independent_chain_verifier",
                },
            ],
            "evidence_flags": {"identity_verified": True},
            "disagreements": [],
            "limitations": [],
            "unresolved_fields": [],
            "risk_included_in_proof": False,
        },
        "proof_score": {
            "schema_version": 1,
            "proof_strength": proof_strength,
            "proof_percent": 100,
            "category_coverage_percent": 100,
            "categories": _proof_categories(),
            "unknown_categories": [],
            "risk_considered": False,
            "risk_separate": True,
            "method": "deterministic_category_evidence_v1",
        },
    }


def test_evidence_context_preserves_risk_and_proof_as_independent_dimensions():
    context = evidence_context(_envelope())

    assert context["risk_level"] == "HIGH"
    assert context["risk_recommendation"] == "WARN"
    assert context["proof_strength"] == "STRONG"
    assert context["verification_status"] == "AGREEMENT"
    assert context["risk_separate_from_proof"] is True
    assert context["independently_verified"] is True


def test_pass_recommendation_does_not_become_a_risk_level():
    context = evidence_context(
        _envelope(risk_level="", recommendation="PASS", proof_strength="STRONG")
    )
    assert context["risk_level"] == "UNKNOWN"
    assert context["risk_recommendation"] == "PASS"
    assert context["proof_strength"] == "STRONG"


def test_malformed_cross_chain_receipt_fails_closed():
    envelope = _envelope(chain="x1")
    envelope["evidence_receipt"]["chain"] = "solana"
    with pytest.raises(CMISEvidenceMetadataError, match="chain mismatch"):
        validate_evidence_metadata(envelope, required=True)


def test_cross_chain_comparison_keeps_evidence_isolated_and_does_not_recompute_market():
    x1 = _envelope(chain="x1")
    solana = _envelope(chain="solana", risk_level="UNKNOWN", proof_strength="WEAK")
    comparison = compare_chain_evidence({"x1": x1, "solana": solana})

    assert comparison["chain_isolation_preserved"] is True
    assert comparison["market_values_compared"] is False
    assert comparison["risk_values_recomputed"] is False
    assert comparison["proof_values_recomputed"] is False
    assert comparison["chains"]["x1"]["proof_strength"] == "STRONG"
    assert comparison["chains"]["solana"]["proof_strength"] == "WEAK"


def test_answer_first_pretrade_shows_risk_and_evidence_quality_separately():
    result = _envelope(service="pre_trade_check")
    result["data"] = {
        "trade": {"side": "buy", "notional_usd": 500},
        "market": {
            "verified_liquidity_usd": "3380",
            "verified_volume_24h_usd": "123.62",
        },
        "trade_size": {
            "assessment": "WARN",
            "notional_to_liquidity_ratio": "0.1479289940828402",
        },
        "route_analysis": {
            "status": "unavailable",
            "estimated_price_impact_percent": None,
            "estimated_slippage_percent": None,
            "estimated_fees": None,
        },
    }

    presentation = build_pretrade_presentation(result)
    assert presentation is not None
    text = presentation["user_text"]
    assert text.startswith("I would be cautious about buying $500 of AGI.")
    assert "Why:" in text
    assert "Risk: HIGH" in text
    assert "Evidence quality: STRONG" in text
    assert "14.8%" in text
    assert "not fully evaluated" in text
    assert presentation["risk_level"] == "HIGH"
    assert presentation["evidence_quality"] == "STRONG"


def test_technical_pretrade_exposes_receipt_and_proof_without_changing_them():
    result = _envelope(service="pre_trade_check")
    result["data"] = {"trade": {"side": "buy", "notional_usd": 500}}
    presentation = build_pretrade_presentation(
        result,
        objective="Show me the technical details.",
    )
    assert presentation is not None
    assert presentation["mode"] == "technical"
    text = presentation["user_text"]
    assert '"evidence_receipt"' in text
    assert '"proof_score"' in text
    assert '"proof_strength": "STRONG"' in text
    assert '"risk_level": "HIGH"' in text


@pytest.mark.parametrize(
    ("question", "intent", "required"),
    [
        ("Should I buy AGI?", "trade_decision", {"market_report", "risk_check", "historical_compare"}),
        ("Is $500 too much?", "trade_size", {"market_report", "risk_check"}),
        ("Is this liquidity dangerous?", "liquidity_risk", {"market_report", "risk_check"}),
        ("Should I add LP?", "lp_decision", {"market_report", "risk_check", "tokenomics"}),
        ("Why is the price falling?", "price_move_reason", {"historical_compare", "market_report"}),
    ],
)
def test_recommendation_policy_deterministically_selects_evidence_needs(
    question, intent, required
):
    assert recommendation_intent(question) == intent
    plan = recommendation_evidence_plan(question)
    assert plan["read_only"] is True
    assert plan["execution_authorized"] is False
    assert required.issubset(set(required_operations(question)))


def test_wallet_contract_preserves_facts_but_blocks_behavioral_labels():
    contract = build_wallet_interpretation_contract(
        chain="x1",
        wallet="wallet-1",
        facts={
            "asset_outflow": {"amount": "3200000", "window": "14d"},
            "deployer_originated_transfer": {"amount": "4000000"},
            "circulating_supply_share": "0.011",
        },
    )
    assert contract["facts"]["circulating_supply_share"] == "0.011"
    assert contract["classifications"] == []
    assert contract["classification_status"].startswith("UNAVAILABLE")
    assert contract["execution_authorized"] is False

    for label in ("insider", "whale", "bot", "accumulator", "distributor"):
        with pytest.raises(WalletInterpretationContractError):
            assert_classification_allowed(label)
