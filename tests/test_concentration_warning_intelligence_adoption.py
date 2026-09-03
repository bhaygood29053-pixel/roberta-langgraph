from __future__ import annotations

from copy import deepcopy
import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    CMISCapabilityUnavailable,
    CONCENTRATION_WARNING_CONTRACT_VERSION,
    CONCENTRATION_WARNING_DELIVERY_MODE,
    CONCENTRATION_WARNING_MIN_CMIS_CONTRACT_VERSION,
    CONCENTRATION_WARNING_REQUIRED_LIMITATIONS,
    CONCENTRATION_WARNING_REQUIRED_REQUIREMENTS,
    require_concentration_warning_capability,
    validate_capability_manifest,
)
from roberta.cmis.concentration_warning import (
    SERVICE,
    validate_concentration_warning_response,
)
from roberta.cmis.http import CMISHTTPClient
from roberta.x1_scout.concentration_warning_intelligence import (
    build_x1_concentration_warning_intelligence,
)
from tests.test_cmis_http_client import _Server, _capabilities


ID1 = "ie_" + "1" * 64
ID2 = "ie_" + "2" * 64
WARNING_ID = "cw_" + "a" * 64
POLICY = {
    "policy_id": "x1-concentration-watch",
    "policy_version": "1.0.0",
    "absolute_delta_threshold_bps": "100",
}


def _promoted_capabilities() -> dict[str, object]:
    manifest = deepcopy(_capabilities())
    manifest["contract_version"] = "1.18.0"
    services = manifest["supported_services"]
    services.append(SERVICE)

    x1 = manifest["chains"]["x1"]
    x1["services"][SERVICE] = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": CONCENTRATION_WARNING_CONTRACT_VERSION,
        "delivery_mode": CONCENTRATION_WARNING_DELIVERY_MODE,
        "push_delivery_authorized": False,
        "requirements": list(CONCENTRATION_WARNING_REQUIRED_REQUIREMENTS),
        "limitations": list(CONCENTRATION_WARNING_REQUIRED_LIMITATIONS),
        "execution_authorized": False,
    }
    x1["callable_services"].append(SERVICE)

    solana = manifest["chains"]["solana"]
    solana["services"][SERVICE] = {
        "state": "unavailable",
        "callable": False,
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "service_contract_version": CONCENTRATION_WARNING_CONTRACT_VERSION,
        "delivery_mode": CONCENTRATION_WARNING_DELIVERY_MODE,
        "push_delivery_authorized": False,
        "requirements": [],
        "limitations": ["concentration_warning_intelligence_not_available_for_chain"],
        "execution_authorized": False,
    }
    return manifest


def _proof(receipt: str) -> dict[str, object]:
    return {
        "receipt_id": receipt,
        "proof_strength": "STRONG",
        "proof_percent": 100,
        "method": "verified_evidence_ratio_v1",
    }


def _canonical_warning() -> dict[str, object]:
    observations = [
        {
            "intelligence_evidence_id": ID1,
            "after_observed_at": "2026-09-03T06:50:00Z",
            "source": "X1.Ninja",
            "scope": "observed_top_token_accounts",
            "requested_account_limit": 20,
            "observed_account_count": 20,
            "direction": "INCREASE",
            "delta_bps": "125",
            "absolute_delta_bps": "125",
            "threshold_status": "EXCEEDS_THRESHOLD",
            "condition_satisfied": True,
            "receipt_ids": ["er-first"],
            "proof_records": [_proof("er-first")],
            "freshness_verified": True,
        },
        {
            "intelligence_evidence_id": ID2,
            "after_observed_at": "2026-09-03T07:00:00Z",
            "source": "X1.Ninja",
            "scope": "observed_top_token_accounts",
            "requested_account_limit": 20,
            "observed_account_count": 20,
            "direction": "INCREASE",
            "delta_bps": "125",
            "absolute_delta_bps": "125",
            "threshold_status": "EXCEEDS_THRESHOLD",
            "condition_satisfied": True,
            "receipt_ids": ["er-second"],
            "proof_records": [_proof("er-second")],
            "freshness_verified": True,
        },
    ]
    policy = {
        **POLICY,
        "metric": "absolute_delta_bps",
        "unit": "basis_points",
        "comparator": "GTE",
        "comparison_symbol": ">=",
        "hidden_default_threshold": False,
    }
    freshness = {
        "max_latest_age_seconds": 300,
        "latest_age_seconds": "300",
        "latest_evidence_freshness_verified": True,
        "receipt_freshness_verified": True,
    }
    persistence = {
        "mode": "two_distinct_compatible_observations",
        "required_observations": 2,
        "satisfied_observations": 2,
        "evaluated_evidence_ids": [ID1, ID2],
        "condition_satisfying_evidence_ids": [ID1, ID2],
        "triggering_evidence_ids": [ID1, ID2],
        "duplicate_evidence_can_inflate_count": False,
        "strict_order_verified": True,
        "compatibility_verified": True,
        "window_seconds": "600",
        "max_window_seconds": 600,
    }
    evidence = {
        "intelligence_evidence_ids": [ID1, ID2],
        "receipt_ids": ["er-first", "er-second"],
        "proof_lineage": [
            {
                "intelligence_evidence_id": ID1,
                "receipt_ids": ["er-first"],
                "proof_records": [_proof("er-first")],
            },
            {
                "intelligence_evidence_id": ID2,
                "receipt_ids": ["er-second"],
                "proof_records": [_proof("er-second")],
            },
        ],
        "freshness_verified": True,
        "unresolved_fields": [],
    }
    return {
        "warning_id": WARNING_ID,
        "schema": "cmis_persistent_concentration_warning.v1",
        "chain": "x1",
        "asset_id": "AGI",
        "evaluated_at": "2026-09-03T07:05:00Z",
        "policy": policy,
        "freshness_policy": freshness,
        "persistence": persistence,
        "observations": observations,
        "evidence": evidence,
        "warning_active": True,
        "warning_level": "WATCH",
        "warning_level_is_risk_severity": False,
        "risk_interpretation": None,
        "risk_interpretation_verified": False,
        "behavioral_interpretation_verified": False,
        "ownership_interpretation_verified": False,
        "proof_strength_separate_from_risk": True,
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "cmis_promotable": False,
        "delivery_authorized": False,
        "execution_authorized": False,
        "limitations": [
            "watch_is_not_risk_severity",
            "warning_delivery_is_not_authorized",
        ],
    }


def _envelope() -> dict[str, object]:
    warning = _canonical_warning()
    return {
        "service": SERVICE,
        "chain": "x1",
        "status": "ok",
        "asset": {"canonical_id": "AGI"},
        "data": {
            "contract_version": CONCENTRATION_WARNING_CONTRACT_VERSION,
            "delivery_mode": "pull_only",
            "push_delivery_authorized": False,
            "public_service_promoted": True,
            "scout_reliance_promoted": True,
            "warning_id": WARNING_ID,
            "warning_level": "WATCH",
            "warning_active": True,
            "warning_level_is_risk_severity": False,
            "policy": deepcopy(warning["policy"]),
            "freshness_policy": deepcopy(warning["freshness_policy"]),
            "persistence": deepcopy(warning["persistence"]),
            "observations": deepcopy(warning["observations"]),
            "evidence": deepcopy(warning["evidence"]),
            "limitations": deepcopy(warning["limitations"]),
            "canonical_warning": warning,
            "risk_interpretation": None,
            "risk_interpretation_verified": False,
            "behavioral_interpretation_verified": False,
            "ownership_interpretation_verified": False,
            "proof_strength_separate_from_risk": True,
            "execution_authorized": False,
        },
        "risk": None,
        "confidence": {
            "canonical_warning_validated": True,
            "receipt_lineage_preserved": True,
            "proof_lineage_preserved": True,
            "freshness_verified": True,
        },
        "sources": [{"source": "X1.Ninja", "observed_at": "2026-09-03T07:00:00Z"}],
        "observed_at": "2026-09-03T07:00:00Z",
        "warnings": [],
        "errors": [],
        "execution_authorized": False,
    }


def _request_kwargs() -> dict[str, object]:
    return {
        "intelligence_evidence_ids": [ID1, ID2],
        "threshold_policy": deepcopy(POLICY),
        "threshold_unit": "basis_points",
        "comparator": "GTE",
        "evaluated_at": "2026-09-03T07:05:00Z",
        "max_latest_age_seconds": 300,
        "max_persistence_window_seconds": 600,
    }


def test_cmis_118_warning_capability_is_exact_and_pull_only() -> None:
    manifest = validate_capability_manifest(_promoted_capabilities())
    capability = require_concentration_warning_capability(manifest)
    assert CONCENTRATION_WARNING_MIN_CMIS_CONTRACT_VERSION == "1.18.0"
    assert capability["service_contract_version"] == "concentration_warning_intelligence/v1"
    assert capability["delivery_mode"] == "pull_only"
    assert capability["push_delivery_authorized"] is False
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["execution_authorized"] is False


def test_warning_capability_fails_closed_on_old_weakened_or_solana_contract() -> None:
    old = _promoted_capabilities()
    old["contract_version"] = "1.17.9"
    with pytest.raises(CMISCapabilityContractError, match="requires contract"):
        require_concentration_warning_capability(validate_capability_manifest(old))

    weakened = _promoted_capabilities()
    weakened["chains"]["x1"]["services"][SERVICE]["push_delivery_authorized"] = True
    with pytest.raises(CMISCapabilityContractError, match="push_delivery_authorized"):
        require_concentration_warning_capability(
            validate_capability_manifest(weakened)
        )

    with pytest.raises(CMISCapabilityUnavailable, match="solana"):
        require_concentration_warning_capability(
            validate_capability_manifest(_promoted_capabilities()),
            chain="solana",
        )


def test_http_client_posts_exact_pull_only_warning_request() -> None:
    expected = _envelope()
    with _Server(expected, capabilities=_promoted_capabilities()) as running:
        result = CMISHTTPClient(
            base_url=running.base_url, timeout_seconds=2
        ).concentration_warning_intelligence(
            chain="x1",
            asset="AGI",
            **_request_kwargs(),
        )

    assert result == expected
    assert running.requests == [
        {
            "service": SERVICE,
            "chain": "x1",
            "asset": "AGI",
            "params": {
                "asset_id": "AGI",
                **_request_kwargs(),
            },
        }
    ]


def test_response_validator_preserves_canonical_warning_without_recomputation() -> None:
    source = _envelope()
    accepted = validate_concentration_warning_response(source, requested_asset="AGI")
    assert accepted == source
    assert accepted is not source
    data = accepted["data"]
    assert data["canonical_warning"]["warning_id"] == data["warning_id"]
    assert data["canonical_warning"]["persistence"] == data["persistence"]
    assert data["canonical_warning"]["evidence"] == data["evidence"]
    assert data["warning_level"] == "WATCH"
    assert data["warning_level_is_risk_severity"] is False
    assert accepted["risk"] is None


def test_response_validator_rejects_risk_delivery_or_canonical_drift() -> None:
    for mutate, match in (
        (lambda x: x["data"].__setitem__("push_delivery_authorized", True), "push_delivery"),
        (lambda x: x.__setitem__("risk", {"level": "HIGH"}), "must not promote risk"),
        (
            lambda x: x["data"]["canonical_warning"].__setitem__("warning_level", "CLEAR"),
            "warning_level must preserve canonical warning exactly",
        ),
    ):
        bad = _envelope()
        mutate(bad)
        with pytest.raises(Exception, match=match):
            validate_concentration_warning_response(bad, requested_asset="AGI")



def test_x1_warning_product_preserves_validated_cmis_data_exactly() -> None:
    source = _envelope()
    product = build_x1_concentration_warning_intelligence(
        source,
        requested_asset="AGI",
    )
    assert product["contract_version"] == "x1_concentration_warning_intelligence/v1"
    assert product["product"] == "x1_concentration_warning_intelligence"
    assert product["chain"] == "x1"
    assert product["status"] == "ok"
    assert product["warning"] == source["data"]
    assert product["warning"]["canonical_warning"] == _canonical_warning()
    assert product["delivery_mode"] == "pull_only"
    assert product["push_delivery_authorized"] is False
    assert product["warning_level_is_risk_severity"] is False
    assert product["risk_interpretation"] is None
    assert product["proof_score_separate_from_risk"] is True
    assert product["execution_authorized"] is False
