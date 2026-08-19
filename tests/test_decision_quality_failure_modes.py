import pytest

from roberta.evidence_aware import (
    CMISEvidenceMetadataError,
    compare_chain_evidence,
    evidence_context,
    validate_evidence_metadata,
)
from roberta.prompts import ORACLE_SYSTEM_PROMPT


def _envelope(
    *,
    chain="x1",
    risk_level=None,
    recommendation="WARN",
    proof_strength="STRONG",
    verification_status="AGREEMENT",
    freshness_verified=True,
    disagreements=None,
    unresolved_fields=None,
):
    return {
        "service": "risk_check",
        "chain": chain,
        "risk": {
            "level": risk_level,
            "recommendation": recommendation,
        },
        "evidence_receipt": {
            "receipt_id": f"er_{chain}_decision_failure_mode",
            "schema_version": 1,
            "chain": chain,
            "service": "risk_check",
            "verification": {
                "status": verification_status,
                "code": "DECISION_QUALITY_TEST",
                "independently_verified": verification_status == "AGREEMENT",
                "provider_assertion_promoted": False,
            },
            "evidence_scope": {"explicit_scope_available": True},
            "freshness": {"verified": freshness_verified},
            "sources": [{"source": f"{chain}_provider"}],
            "disagreements": disagreements or [],
            "limitations": [],
            "unresolved_fields": unresolved_fields or [],
        },
        "proof_score": {
            "schema_version": 1,
            "proof_strength": proof_strength,
            "proof_percent": {"STRONG": 95, "MODERATE": 65, "WEAK": 25}[proof_strength],
            "category_coverage_percent": 100 if proof_strength == "STRONG" else 50,
            "categories": {
                "identity": {
                    "state": "VERIFIED" if proof_strength != "WEAK" else "UNKNOWN",
                    "score": 100 if proof_strength != "WEAK" else None,
                    "reasons": [],
                    "evidence_paths": [],
                }
            },
            "unknown_categories": [] if proof_strength == "STRONG" else ["freshness"],
            "risk_considered": False,
            "risk_separate": True,
        },
    }


@pytest.mark.parametrize("recommendation", ["PASS", "WARN", "BLOCK"])
def test_recommendation_tokens_never_become_a_risk_level(recommendation):
    context = evidence_context(
        _envelope(risk_level=None, recommendation=recommendation)
    )

    assert context["risk_level"] == "UNKNOWN"
    assert context["risk_recommendation"] == recommendation
    assert context["risk_separate_from_proof"] is True


def test_stale_evidence_remains_stale_without_changing_risk_or_proof():
    context = evidence_context(
        _envelope(
            risk_level="HIGH",
            recommendation="BLOCK",
            proof_strength="STRONG",
            freshness_verified=False,
        )
    )

    assert context["risk_level"] == "HIGH"
    assert context["risk_recommendation"] == "BLOCK"
    assert context["proof_strength"] == "STRONG"
    assert context["freshness_verified"] is False


def test_source_conflict_is_preserved_and_not_reconciled():
    disagreements = [
        {
            "field": "liquidity_usd",
            "source_a": "provider_a",
            "source_b": "provider_b",
        }
    ]
    context = evidence_context(
        _envelope(
            risk_level=None,
            recommendation="UNKNOWN",
            proof_strength="WEAK",
            verification_status="CONFLICT",
            disagreements=disagreements,
            unresolved_fields=["liquidity_usd", "risk_level"],
        )
    )

    assert context["verification_status"] == "CONFLICT"
    assert context["disagreements"] == disagreements
    assert context["risk_level"] == "UNKNOWN"
    assert "liquidity_usd" in context["unresolved_fields"]


def test_cross_chain_unequal_proof_quality_remains_isolated():
    comparison = compare_chain_evidence(
        {
            "x1": _envelope(
                chain="x1",
                risk_level="HIGH",
                recommendation="WARN",
                proof_strength="STRONG",
            ),
            "solana": _envelope(
                chain="solana",
                risk_level=None,
                recommendation="UNKNOWN",
                proof_strength="WEAK",
                verification_status="INSUFFICIENT_EVIDENCE",
                freshness_verified=False,
                unresolved_fields=["risk_level"],
            ),
        }
    )

    assert comparison["chain_isolation_preserved"] is True
    assert comparison["market_values_compared"] is False
    assert comparison["risk_values_recomputed"] is False
    assert comparison["proof_values_recomputed"] is False
    assert comparison["chains"]["x1"]["proof_strength"] == "STRONG"
    assert comparison["chains"]["solana"]["proof_strength"] == "WEAK"
    assert comparison["chains"]["solana"]["risk_level"] == "UNKNOWN"


def test_tampered_provider_assertion_promotion_fails_closed():
    envelope = _envelope()
    envelope["evidence_receipt"]["verification"]["provider_assertion_promoted"] = True

    with pytest.raises(CMISEvidenceMetadataError, match="provider assertion promotion"):
        validate_evidence_metadata(envelope, required=True)


def test_tampered_receipt_chain_fails_closed():
    envelope = _envelope(chain="x1")
    envelope["evidence_receipt"]["chain"] = "solana"

    with pytest.raises(CMISEvidenceMetadataError, match="chain mismatch"):
        validate_evidence_metadata(envelope, required=True)


def test_oracle_prompt_contract_requires_answer_first_progressive_disclosure():
    prompt = ORACLE_SYSTEM_PROMPT

    assert "Lead with the answer or blocker immediately" in prompt
    assert "risk and evidence quality as separate dimensions" in prompt
    assert "important missing evidence" in prompt
    assert "Do not dump every returned field" in prompt
    assert "Technical/diagnostic detail is progressive disclosure" in prompt


def test_oracle_prompt_contract_rejects_memory_or_checkpoint_as_current_market_truth():
    prompt = ORACLE_SYSTEM_PROMPT

    assert "Treat those snapshots as historical context only" in prompt
    assert "A record marked `authority=historical_context` never establishes a current market" in prompt
    assert "Fresh deterministic specialist/CMIS/provider evidence always overrides" in prompt


def test_oracle_prompt_contract_preserves_execution_boundary():
    prompt = ORACLE_SYSTEM_PROMPT

    assert "Roberta has no signing, transaction construction, broadcasting, custody" in prompt
    assert "Deterministic policy cannot be overridden by LLM prose" in prompt
    assert "Analysis or recommendation text is non-authorizing" in prompt
