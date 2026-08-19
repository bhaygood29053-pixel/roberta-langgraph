from roberta.prompts import ORACLE_SYSTEM_PROMPT
from roberta.x1_scout.graph import _summarize_cmis_result


def _result(
    *,
    status="partial",
    data=None,
    risk=None,
    warnings=None,
    errors=None,
    unresolved_fields=None,
    proof_strength="WEAK",
    verification_status="INSUFFICIENT_EVIDENCE",
    freshness_verified=True,
):
    return {
        "service": "market_report",
        "chain": "x1",
        "status": status,
        "asset": {"symbol": "AGI", "mint": "agi-test-mint"},
        "data": data or {},
        "risk": risk,
        "confidence": {"verified_checks": 1, "total_checks": 2},
        "sources": [{"source": "x1_provider"}],
        "observed_at": "2026-08-19T03:40:00Z",
        "warnings": warnings or [],
        "errors": errors or [],
        "evidence_receipt": {
            "receipt_id": "er_x1_unknowns",
            "schema_version": 1,
            "chain": "x1",
            "service": "market_report",
            "verification": {
                "status": verification_status,
                "code": "DECISION_QUALITY_UNKNOWNS",
                "independently_verified": verification_status == "AGREEMENT",
                "provider_assertion_promoted": False,
            },
            "evidence_scope": {"explicit_scope_available": True},
            "freshness": {"verified": freshness_verified},
            "sources": [{"source": "x1_provider"}],
            "disagreements": [],
            "limitations": [],
            "unresolved_fields": unresolved_fields or [],
        },
        "proof_score": {
            "schema_version": 1,
            "proof_strength": proof_strength,
            "proof_percent": 25 if proof_strength == "WEAK" else 95,
            "category_coverage_percent": 50 if proof_strength == "WEAK" else 100,
            "categories": {
                "identity": {
                    "state": "UNKNOWN" if proof_strength == "WEAK" else "VERIFIED",
                    "score": None if proof_strength == "WEAK" else 100,
                    "reasons": [],
                    "evidence_paths": [],
                }
            },
            "unknown_categories": ["activity"] if proof_strength == "WEAK" else [],
            "risk_considered": False,
            "risk_separate": True,
        },
    }


def test_missing_verified_activity_amount_stays_null_not_zero_through_scout_summary():
    investigation = _summarize_cmis_result(
        _result(
            data={
                "verified_transaction_count": 4,
                "verified_activity_amount_usd": None,
            },
            unresolved_fields=["verified_activity_amount_usd"],
        ),
        objective="What changed today?",
    )

    assert investigation["findings"]["data"]["verified_activity_amount_usd"] is None
    assert investigation["findings"]["data"]["verified_transaction_count"] == 4
    assert "verified_activity_amount_usd" in investigation["evidence_context"]["unresolved_fields"]
    assert investigation["evidence_context"]["proof_strength"] == "WEAK"


def test_verified_zero_activity_remains_distinguishable_from_missing_activity():
    missing = _summarize_cmis_result(
        _result(
            data={"verified_activity_amount_usd": None},
            unresolved_fields=["verified_activity_amount_usd"],
        )
    )
    zero = _summarize_cmis_result(
        _result(
            status="ok",
            data={"verified_activity_amount_usd": 0},
            unresolved_fields=[],
            proof_strength="STRONG",
            verification_status="AGREEMENT",
        )
    )

    assert missing["findings"]["data"]["verified_activity_amount_usd"] is None
    assert zero["findings"]["data"]["verified_activity_amount_usd"] == 0
    assert missing["findings"]["data"]["verified_activity_amount_usd"] != zero["findings"]["data"]["verified_activity_amount_usd"]


def test_ambiguous_asset_identity_stays_a_blocker_not_a_single_asset_assumption():
    investigation = _summarize_cmis_result(
        _result(
            status="ambiguous",
            data={
                "candidates": [
                    {"symbol": "AGI", "mint": "mint-a"},
                    {"symbol": "AGI", "mint": "mint-b"},
                ],
                "price_usd": None,
            },
            unresolved_fields=["asset_identity", "price_usd"],
        ),
        objective="Should I buy AGI?",
    )

    assert investigation["cmis_status"] == "ambiguous"
    assert investigation["findings"]["data"]["price_usd"] is None
    assert len(investigation["findings"]["data"]["candidates"]) == 2
    assert "could not uniquely resolve" in investigation["cmis_status_help"]["meaning"]
    assert "asset_identity" in investigation["evidence_context"]["unresolved_fields"]
    assert investigation["findings"]["risk"] is None


def test_unavailable_provider_field_preserves_null_warning_error_and_evidence_state():
    warning = {"code": "PROVIDER_FIELD_UNAVAILABLE", "field": "liquidity_usd"}
    error = {"code": "UPSTREAM_UNAVAILABLE", "source": "x1_provider"}
    investigation = _summarize_cmis_result(
        _result(
            status="unavailable",
            data={"liquidity_usd": None, "volume_24h_usd": None},
            warnings=[warning],
            errors=[error],
            unresolved_fields=["liquidity_usd", "volume_24h_usd"],
            freshness_verified=False,
        ),
        objective="Is the liquidity dangerous?",
    )

    assert investigation["cmis_status"] == "unavailable"
    assert investigation["findings"]["data"]["liquidity_usd"] is None
    assert investigation["findings"]["data"]["volume_24h_usd"] is None
    assert investigation["warnings"] == [warning]
    assert investigation["errors"] == [error]
    assert investigation["evidence_context"]["freshness_verified"] is False
    assert investigation["evidence_context"]["verification_status"] == "INSUFFICIENT_EVIDENCE"


def test_oracle_contract_requires_unknowns_and_ambiguity_to_be_user_visible_without_raw_dump():
    prompt = ORACLE_SYSTEM_PROMPT

    assert "If an asset name is ambiguous, say so plainly" in prompt
    assert "Do not overwhelm the user with all candidate internals" in prompt
    assert "Missing evidence means unknown or unproven" in prompt
    assert "must never be treated as zero" in prompt
    assert "important missing evidence" in prompt
    assert "Do not dump every returned field" in prompt


def test_oracle_contract_forbids_inferred_risk_from_missing_market_fields():
    prompt = ORACLE_SYSTEM_PROMPT

    assert "If `findings.risk` is null or unavailable" in prompt
    assert "do not infer a risk level" in prompt
    assert "liquidity" in prompt
    assert "provider safety-grade" in prompt
