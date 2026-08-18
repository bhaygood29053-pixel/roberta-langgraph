from copy import deepcopy

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    CMISCapabilityUnavailable,
    MIN_CMIS_CONTRACT_VERSION,
    require_service_capability,
    validate_capability_manifest,
)


def _capability(state: str) -> dict[str, object]:
    return {
        "state": state,
        "callable": state != "unavailable",
        "requirements": [],
        "limitations": [],
    }


def _manifest() -> dict[str, object]:
    services = [
        "asset_lookup",
        "market_report",
        "rank",
        "historical_compare",
        "tokenomics",
        "risk_check",
        "pre_trade_check",
        "trade_verification",
        "verified_asset_activity",
        "verification_evidence",
    ]
    x1 = {service: _capability("supported") for service in services}
    x1["pre_trade_check"] = _capability("bounded")
    x1["trade_verification"] = _capability("bounded")
    x1["verified_asset_activity"] = _capability("bounded")
    x1["verification_evidence"] = _capability("bounded")

    solana = {service: _capability("unavailable") for service in services}
    solana["asset_lookup"] = _capability("bounded")
    solana["market_report"] = _capability("partial")
    solana["historical_compare"] = _capability("partial")
    solana["tokenomics"] = _capability("partial")
    solana["risk_check"] = _capability("partial")

    return {
        "service": "cmis_gateway",
        "version": 1,
        "schema_version": 1,
        "contract_version": MIN_CMIS_CONTRACT_VERSION,
        "request_path": "/v1/cmis",
        "evidence_quality": {
            "evidence_receipt_schema_version": 1,
            "proof_score_schema_version": 1,
            "proof_strength_values": ["STRONG", "MODERATE", "WEAK"],
            "risk_separate_from_proof": True,
            "missing_evidence_is_unknown": True,
        },
        "supported_services": services,
        "supported_chains": ["x1"],
        "known_chains": ["x1", "solana"],
        "chains": {
            "x1": {
                "services": x1,
                "callable_services": [
                    service for service in services if x1[service]["callable"] is True
                ],
            },
            "solana": {
                "services": solana,
                "callable_services": [
                    service for service in services if solana[service]["callable"] is True
                ],
            },
        },
    }


def test_valid_manifest_preserves_chain_specific_capability_states() -> None:
    manifest = validate_capability_manifest(_manifest())

    assert manifest["contract_version"] == MIN_CMIS_CONTRACT_VERSION
    assert MIN_CMIS_CONTRACT_VERSION == "1.7.0"
    assert manifest["evidence_quality"]["risk_separate_from_proof"] is True
    assert manifest["evidence_quality"]["missing_evidence_is_unknown"] is True
    assert manifest["chains"]["x1"]["services"]["risk_check"]["state"] == "supported"
    assert manifest["chains"]["solana"]["services"]["risk_check"]["state"] == "partial"
    assert manifest["chains"]["solana"]["services"]["pre_trade_check"]["state"] == "unavailable"


def test_stale_contract_version_fails_closed() -> None:
    manifest = deepcopy(_manifest())
    manifest["contract_version"] = "1.6.9"

    with pytest.raises(CMISCapabilityContractError, match="older than the minimum"):
        validate_capability_manifest(manifest)


def test_missing_or_weakened_evidence_contract_fails_closed() -> None:
    missing = deepcopy(_manifest())
    del missing["evidence_quality"]
    with pytest.raises(CMISCapabilityContractError, match="evidence_quality"):
        validate_capability_manifest(missing)

    weakened = deepcopy(_manifest())
    weakened["evidence_quality"]["risk_separate_from_proof"] = False
    with pytest.raises(CMISCapabilityContractError, match="separate from proof"):
        validate_capability_manifest(weakened)


def test_missing_service_classification_fails_closed() -> None:
    manifest = deepcopy(_manifest())
    del manifest["chains"]["solana"]["services"]["risk_check"]

    with pytest.raises(CMISCapabilityContractError, match="solana/risk_check is missing"):
        validate_capability_manifest(manifest)


def test_callable_state_mismatch_fails_closed() -> None:
    manifest = deepcopy(_manifest())
    capability = manifest["chains"]["solana"]["services"]["pre_trade_check"]
    capability["callable"] = True

    with pytest.raises(CMISCapabilityContractError, match="inconsistent callable/state"):
        validate_capability_manifest(manifest)


def test_require_service_capability_allows_partial_but_blocks_unavailable() -> None:
    manifest = validate_capability_manifest(_manifest())

    market = require_service_capability(
        manifest,
        chain="solana",
        service="market_report",
    )
    assert market["state"] == "partial"
    assert market["callable"] is True

    with pytest.raises(CMISCapabilityUnavailable, match="solana/pre_trade_check"):
        require_service_capability(
            manifest,
            chain="solana",
            service="pre_trade_check",
        )


def test_unknown_chain_never_falls_back_to_another_chain() -> None:
    manifest = validate_capability_manifest(_manifest())

    with pytest.raises(CMISCapabilityUnavailable, match="ethereum/market_report"):
        require_service_capability(
            manifest,
            chain="ethereum",
            service="market_report",
        )
