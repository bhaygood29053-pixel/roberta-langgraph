from copy import deepcopy

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    CMISCapabilityUnavailable,
    HISTORICAL_ALL_AVAILABLE_MIN_CMIS_CONTRACT_VERSION,
    HISTORICAL_ALL_AVAILABLE_REQUIRED_LIMITATIONS,
    HISTORICAL_PAIR_REQUIRED_LIMITATION,
    HISTORICAL_PROVIDER_BACKFILL_MIN_CMIS_CONTRACT_VERSION,
    HISTORICAL_PROVIDER_BACKFILL_REQUIRED_LIMITATIONS,
    INTELLIGENCE_FOUNDATION_CAPABILITIES,
    MIN_CMIS_CONTRACT_VERSION,
    X1_ASSET_IDENTITY_CONTRACT_VERSION,
    X1_ASSET_IDENTITY_MIN_CMIS_CONTRACT_VERSION,
    X1_ASSET_IDENTITY_REQUIRED_LIMITATIONS,
    require_historical_all_available_capability,
    require_service_capability,
    require_x1_normalized_asset_identity_capability,
    validate_capability_manifest,
)


def _capability(state: str) -> dict[str, object]:
    return {
        "state": state,
        "callable": state != "unavailable",
        "requirements": [],
        "limitations": [],
    }


def _intelligence_capability() -> dict[str, object]:
    return {
        "state": "bounded",
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
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
        "intelligence_foundation": {
            "schema_version": 1,
            "phase": "phase_11_verified_intelligence_foundation",
            "read_only": True,
            "public_service_promoted": False,
            "scout_reliance_promoted": False,
            "promotion_rule": "new_accepted_public_service_contract_required",
            "intelligence_evidence_schema_version": 1,
            "capabilities": {
                name: _intelligence_capability()
                for name in INTELLIGENCE_FOUNDATION_CAPABILITIES
            },
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


def test_valid_manifest_preserves_chain_and_intelligence_boundaries() -> None:
    manifest = validate_capability_manifest(_manifest())

    assert manifest["contract_version"] == MIN_CMIS_CONTRACT_VERSION
    assert MIN_CMIS_CONTRACT_VERSION == "1.8.0"
    assert manifest["evidence_quality"]["risk_separate_from_proof"] is True
    assert manifest["evidence_quality"]["missing_evidence_is_unknown"] is True
    assert manifest["intelligence_foundation"]["read_only"] is True
    assert manifest["intelligence_foundation"]["public_service_promoted"] is False
    assert manifest["intelligence_foundation"]["scout_reliance_promoted"] is False
    assert set(manifest["intelligence_foundation"]["capabilities"]) == set(
        INTELLIGENCE_FOUNDATION_CAPABILITIES
    )
    assert manifest["chains"]["x1"]["services"]["risk_check"]["state"] == "supported"
    assert manifest["chains"]["solana"]["services"]["risk_check"]["state"] == "partial"
    assert manifest["chains"]["solana"]["services"]["pre_trade_check"]["state"] == "unavailable"


def test_stale_contract_version_fails_closed() -> None:
    manifest = deepcopy(_manifest())
    manifest["contract_version"] = "1.7.9"

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


def test_missing_or_promoted_intelligence_foundation_fails_closed() -> None:
    missing = deepcopy(_manifest())
    del missing["intelligence_foundation"]
    with pytest.raises(CMISCapabilityContractError, match="intelligence_foundation"):
        validate_capability_manifest(missing)

    public = deepcopy(_manifest())
    public["intelligence_foundation"]["public_service_promoted"] = True
    with pytest.raises(CMISCapabilityContractError, match="public service"):
        validate_capability_manifest(public)

    relied_on = deepcopy(_manifest())
    relied_on["intelligence_foundation"]["scout_reliance_promoted"] = True
    with pytest.raises(CMISCapabilityContractError, match="Scout reliance"):
        validate_capability_manifest(relied_on)


def test_intelligence_capability_drift_or_promotion_fails_closed() -> None:
    missing = deepcopy(_manifest())
    del missing["intelligence_foundation"]["capabilities"]["wallet_activity_facts"]
    with pytest.raises(CMISCapabilityContractError, match="classification drift"):
        validate_capability_manifest(missing)

    extra = deepcopy(_manifest())
    extra["intelligence_foundation"]["capabilities"]["future_behavior_label"] = (
        _intelligence_capability()
    )
    with pytest.raises(CMISCapabilityContractError, match="classification drift"):
        validate_capability_manifest(extra)

    promoted = deepcopy(_manifest())
    promoted["intelligence_foundation"]["capabilities"]["top_account_concentration"][
        "scout_reliance_promoted"
    ] = True
    with pytest.raises(CMISCapabilityContractError, match="Scout-reliance promoted"):
        validate_capability_manifest(promoted)


def test_intelligence_foundation_cannot_become_supported_service_silently() -> None:
    manifest = deepcopy(_manifest())
    manifest["supported_services"].append("top_account_concentration")
    for chain in ("x1", "solana"):
        manifest["chains"][chain]["services"]["top_account_concentration"] = _capability(
            "bounded"
        )
        manifest["chains"][chain]["callable_services"].append("top_account_concentration")

    with pytest.raises(CMISCapabilityContractError, match="outside supported_services"):
        validate_capability_manifest(manifest)


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


def _cmis_1_11_identity_manifest() -> dict[str, object]:
    manifest = deepcopy(_manifest())
    manifest["contract_version"] = X1_ASSET_IDENTITY_MIN_CMIS_CONTRACT_VERSION
    lookup = manifest["chains"]["x1"]["services"]["asset_lookup"]
    lookup["limitations"] = list(X1_ASSET_IDENTITY_REQUIRED_LIMITATIONS)
    lookup["identity_contract_version"] = X1_ASSET_IDENTITY_CONTRACT_VERSION
    lookup["exact_mint_normalization"] = True
    lookup["normalized_identity_root"] = "mint"
    lookup["metaplex_xdex_reconciliation"] = True
    return manifest


def test_normalized_x1_identity_requires_exact_cmis_1_11_contract() -> None:
    validated = validate_capability_manifest(_cmis_1_11_identity_manifest())
    lookup = require_x1_normalized_asset_identity_capability(validated)

    assert lookup["identity_contract_version"] == "x1_asset_identity/v1"
    assert lookup["exact_mint_normalization"] is True
    assert lookup["normalized_identity_root"] == "mint"
    assert lookup["metaplex_xdex_reconciliation"] is True


def test_normalized_x1_identity_fails_closed_on_old_or_weakened_contract() -> None:
    old = _cmis_1_11_identity_manifest()
    old["contract_version"] = "1.10.0"
    with pytest.raises(CMISCapabilityContractError, match="requires contract"):
        require_x1_normalized_asset_identity_capability(
            validate_capability_manifest(old)
        )

    weakened = _cmis_1_11_identity_manifest()
    weakened["chains"]["x1"]["services"]["asset_lookup"]["limitations"].remove(
        "xdex_unavailable_is_not_metaplex_only"
    )
    with pytest.raises(CMISCapabilityContractError, match="missing accepted"):
        require_x1_normalized_asset_identity_capability(
            validate_capability_manifest(weakened)
        )


def test_all_available_history_requires_cmis_1_10_and_exact_limitations() -> None:
    manifest = _manifest()
    manifest["contract_version"] = HISTORICAL_ALL_AVAILABLE_MIN_CMIS_CONTRACT_VERSION
    history = manifest["chains"]["x1"]["services"]["historical_compare"]
    history["requirements"] = ["verified_current_market_snapshot"]
    history["limitations"] = [
        *HISTORICAL_ALL_AVAILABLE_REQUIRED_LIMITATIONS,
        HISTORICAL_PAIR_REQUIRED_LIMITATION,
    ]

    validated = validate_capability_manifest(manifest)
    capability = require_historical_all_available_capability(
        validated,
        chain="x1",
        pair=True,
    )
    assert capability["callable"] is True


def test_all_available_history_accepts_cmis_1_12_verified_provider_backfill_contract() -> None:
    manifest = _manifest()
    manifest["contract_version"] = HISTORICAL_PROVIDER_BACKFILL_MIN_CMIS_CONTRACT_VERSION
    history = manifest["chains"]["x1"]["services"]["historical_compare"]
    history["requirements"] = ["verified_current_market_snapshot"]
    history["limitations"] = [
        "window_mode_requires_supported_period",
        *HISTORICAL_PROVIDER_BACKFILL_REQUIRED_LIMITATIONS,
        HISTORICAL_PAIR_REQUIRED_LIMITATION,
    ]

    validated = validate_capability_manifest(manifest)
    capability = require_historical_all_available_capability(
        validated,
        chain="x1",
        pair=True,
    )
    assert capability["callable"] is True


def test_all_available_history_cmis_1_12_fails_closed_if_backfill_boundary_weakens() -> None:
    manifest = _manifest()
    manifest["contract_version"] = HISTORICAL_PROVIDER_BACKFILL_MIN_CMIS_CONTRACT_VERSION
    history = manifest["chains"]["x1"]["services"]["historical_compare"]
    history["limitations"] = list(HISTORICAL_PROVIDER_BACKFILL_REQUIRED_LIMITATIONS)
    history["limitations"].remove("provider_archive_completeness_not_verified")

    validated = validate_capability_manifest(manifest)
    with pytest.raises(CMISCapabilityContractError, match="missing accepted"):
        require_historical_all_available_capability(
            validated,
            chain="x1",
        )


def test_all_available_history_fails_closed_on_old_or_weakened_contract() -> None:
    old = _manifest()
    old["contract_version"] = "1.9.0"
    validated_old = validate_capability_manifest(old)
    with pytest.raises(CMISCapabilityContractError, match="requires contract"):
        require_historical_all_available_capability(
            validated_old,
            chain="x1",
        )

    weakened = _manifest()
    weakened["contract_version"] = HISTORICAL_ALL_AVAILABLE_MIN_CMIS_CONTRACT_VERSION
    history = weakened["chains"]["x1"]["services"]["historical_compare"]
    history["limitations"] = list(HISTORICAL_ALL_AVAILABLE_REQUIRED_LIMITATIONS)
    validated_weakened = validate_capability_manifest(weakened)
    with pytest.raises(CMISCapabilityContractError, match="missing accepted"):
        require_historical_all_available_capability(
            validated_weakened,
            chain="x1",
            pair=True,
        )


def test_unknown_chain_never_falls_back_to_another_chain() -> None:
    manifest = validate_capability_manifest(_manifest())

    with pytest.raises(CMISCapabilityUnavailable, match="ethereum/market_report"):
        require_service_capability(
            manifest,
            chain="ethereum",
            service="market_report",
        )
