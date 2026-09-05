from __future__ import annotations

from copy import deepcopy

import pytest

from roberta.cmis.bridge_to_xdex import (
    CMISBridgeToXdexContractError,
    SERVICE_CONTRACT_VERSION,
    normalize_bridge_to_xdex_request,
    validate_bridge_to_xdex_response,
)
from roberta.cmis.capabilities import (
    BRIDGE_TO_XDEX_MIN_CMIS_CONTRACT_VERSION,
    BRIDGE_TO_XDEX_REQUIRED_LIMITATIONS,
    BRIDGE_TO_XDEX_REQUIRED_REQUIREMENTS,
    CMISCapabilityContractError,
    require_bridge_to_xdex_utilization_capability,
    validate_capability_manifest,
)
from roberta.cmis.http import CMISHTTPClient
from roberta.x1_scout.bridge_to_xdex_utilization import (
    build_x1_bridge_to_xdex_utilization,
)
from tests.test_cmis_http_client import _Server, _capabilities


ROUTE = "warp-solana-x1-wsol"
SOURCE = "So11111111111111111111111111111111111111112"
DEST = "JDqX4vau2P5zJmLpuNitvR6vMURr9kYjex6oZQXz3Ja8"
EVIDENCE = "a" * 64
AS_OF = 1_788_600_000.0


def _promoted_capabilities():
    value = deepcopy(_capabilities())
    value["contract_version"] = "1.19.0"
    value["supported_services"].append("bridge_to_xdex_utilization")
    x1 = value["chains"]["x1"]
    x1["services"]["bridge_to_xdex_utilization"] = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": SERVICE_CONTRACT_VERSION,
        "requirements": list(BRIDGE_TO_XDEX_REQUIRED_REQUIREMENTS),
        "limitations": list(BRIDGE_TO_XDEX_REQUIRED_LIMITATIONS),
        "execution_authorized": False,
    }
    x1["callable_services"].append("bridge_to_xdex_utilization")
    solana = value["chains"]["solana"]
    solana["services"]["bridge_to_xdex_utilization"] = {
        "state": "unavailable",
        "callable": False,
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "service_contract_version": SERVICE_CONTRACT_VERSION,
        "requirements": [],
        "limitations": ["bridge_to_xdex_utilization_not_available_for_chain"],
        "execution_authorized": False,
    }
    return value


def _request():
    return normalize_bridge_to_xdex_request(
        evidence_sha256=EVIDENCE,
        route_id=ROUTE,
        source_mint=SOURCE,
        destination_mint=DEST,
        evaluated_at=AS_OF + 10,
        max_evidence_age_seconds=300,
    )


def _canonical():
    return {
        "service": "bridge_to_xdex_utilization",
        "contract": SERVICE_CONTRACT_VERSION,
        "route_id": ROUTE,
        "source_chain": "solana",
        "source_mint": SOURCE,
        "destination_chain": "x1",
        "destination_mint": DEST,
        "representation_mint": DEST,
        "as_of": AS_OF,
        "xdex_pool_universe_scope": "verified_xdex_program_family",
        "recognized_program_registry_globally_exhaustive": False,
        "global_onchain_pool_discovery_proven": False,
        "verified_zero_pool_set": True,
        "current_liquidity_zero_verified": True,
        "volume_24h_window_coverage_verified": True,
        "verified_xdex_liquidity_value": "0",
        "verified_xdex_volume_24h_value": "0",
        "issue_410_acceptance_verified": True,
        "source_independence_verified": False,
        "causal_bridge_to_xdex_claim_authorized": False,
        "adoption_claim_authorized": False,
        "risk_promotion_authorized": False,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "read_only": True,
        "execution_authorized": False,
        "evidence_sha256": EVIDENCE,
    }


def _envelope():
    canonical = _canonical()
    return {
        "service": "bridge_to_xdex_utilization",
        "chain": "x1",
        "status": "ok",
        "asset": {"canonical_id": DEST, "mint": DEST},
        "data": {
            "contract_version": SERVICE_CONTRACT_VERSION,
            "public_service_promoted": True,
            "scout_reliance_promoted": True,
            "read_only": True,
            "route": {
                "route_id": ROUTE,
                "source_chain": "solana",
                "source_mint": SOURCE,
                "destination_chain": "x1",
                "destination_mint": DEST,
            },
            "scope": {
                "xdex_pool_universe_scope": "verified_xdex_program_family",
                "recognized_program_registry_globally_exhaustive": False,
                "global_onchain_pool_discovery_proven": False,
            },
            "bridge": {
                "bridged_supply_raw": 10000000000,
                "bridged_supply_decimals": 9,
                "bridged_supply_token_amount": "10",
                "bridged_supply_value": "1000",
                "flow_24h": {
                    "inflow_raw": 2000000000,
                    "outflow_raw": 1000000000,
                    "net_flow_raw": 1000000000,
                    "inflow_value": "200",
                    "outflow_value": "100",
                    "net_flow_value": "100",
                    "gross_flow_value": "300",
                    "value_unit": "USD",
                },
            },
            "xdex_market": {
                "pool_count": 0,
                "pool_addresses": [],
                "verified_zero_pool_set": True,
                "current_liquidity_zero_verified": True,
                "volume_24h_window_coverage_verified": True,
                "liquidity_value": "0",
                "volume_24h_value": "0",
                "value_unit": "USD",
            },
            "utilization": {
                "bridge_to_xdex_liquidity_ratio": "0",
                "bridge_to_xdex_liquidity_ratio_state": "verified",
                "bridge_gross_flow_24h_to_xdex_volume_24h_ratio": None,
                "bridge_net_flow_24h_to_xdex_volume_24h_ratio": None,
                "bridge_flow_to_xdex_volume_ratio_state": "undefined_zero_xdex_volume",
            },
            "freshness": {
                "fact_time": AS_OF,
                "evaluated_at": AS_OF + 10,
                "age_seconds": 10,
                "max_evidence_age_seconds": 300,
                "freshness_verified": True,
            },
            "evidence": {
                "evidence_sha256": EVIDENCE,
                "value_basis_evidence_id": "basis",
                "comparable_value_basis_verified": True,
                "issue_410_acceptance_verified": True,
                "source_independence_verified": False,
            },
            "canonical_utilization": canonical,
            "causal_bridge_to_xdex_claim_authorized": False,
            "adoption_claim_authorized": False,
            "risk_promotion_authorized": False,
            "execution_authorized": False,
        },
        "risk": None,
        "confidence": {
            "canonical_issue_410_record_validated": True,
            "identity_verified": True,
            "scope_verified": True,
            "freshness_verified": True,
            "unit_compatibility_verified": True,
        },
        "sources": [{
            "source": "CMIS accepted #410 evidence",
            "observed_at": AS_OF,
            "scope": "verified_xdex_program_family",
        }],
        "observed_at": AS_OF,
        "warnings": [{
            "code": "bounded_xdex_program_family_scope",
            "message": "bounded",
        }],
        "errors": [],
        "execution_authorized": False,
    }


def test_cmis_119_bridge_capability_is_exact_and_bounded():
    manifest = validate_capability_manifest(_promoted_capabilities())
    capability = require_bridge_to_xdex_utilization_capability(manifest)
    assert BRIDGE_TO_XDEX_MIN_CMIS_CONTRACT_VERSION == "1.19.0"
    assert capability["service_contract_version"] == SERVICE_CONTRACT_VERSION
    assert capability["state"] == "bounded"
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["execution_authorized"] is False


def test_bridge_capability_rejects_scope_guardrail_drift():
    raw = _promoted_capabilities()
    raw["chains"]["x1"]["services"]["bridge_to_xdex_utilization"][
        "limitations"
    ].remove("verified_xdex_program_family_is_not_every_x1_dex")
    manifest = validate_capability_manifest(raw)
    with pytest.raises(CMISCapabilityContractError, match="missing accepted limitations"):
        require_bridge_to_xdex_utilization_capability(manifest)


def test_bridge_response_preserves_scope_identity_and_no_risk():
    accepted = validate_bridge_to_xdex_response(
        _envelope(),
        expected_request=_request(),
    )
    assert accepted["risk"] is None
    assert accepted["data"]["scope"]["xdex_pool_universe_scope"] == (
        "verified_xdex_program_family"
    )
    assert accepted["data"]["xdex_market"]["liquidity_value"] == "0"
    assert accepted["data"]["xdex_market"]["volume_24h_value"] == "0"
    assert accepted["data"]["causal_bridge_to_xdex_claim_authorized"] is False
    assert accepted["data"]["adoption_claim_authorized"] is False
    assert accepted["data"]["risk_promotion_authorized"] is False


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda x: x["data"]["scope"].__setitem__(
                "xdex_pool_universe_scope", "all_x1_dexes"
            ),
            "scope must remain",
        ),
        (
            lambda x: x["data"].__setitem__(
                "adoption_claim_authorized", True
            ),
            "adoption_claim_authorized",
        ),
        (
            lambda x: x.__setitem__("risk", {"level": "LOW"}),
            "must not promote",
        ),
    ],
)
def test_bridge_response_fails_closed_on_scope_adoption_or_risk_drift(
    mutate,
    match,
):
    bad = _envelope()
    mutate(bad)
    with pytest.raises(CMISBridgeToXdexContractError, match=match):
        validate_bridge_to_xdex_response(bad, expected_request=_request())


def test_http_client_posts_only_selector_identity_and_freshness_inputs():
    expected = _envelope()
    with _Server(expected, capabilities=_promoted_capabilities()) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).bridge_to_xdex_utilization(
            chain="x1",
            evidence_sha256=EVIDENCE,
            route_id=ROUTE,
            source_mint=SOURCE,
            destination_mint=DEST,
            evaluated_at=AS_OF + 10,
            max_evidence_age_seconds=300,
        )

    assert result == expected
    assert running.requests == [{
        "service": "bridge_to_xdex_utilization",
        "chain": "x1",
        "asset": DEST,
        "params": _request(),
    }]


def test_http_client_blocks_bridge_service_before_cmis_119_without_post():
    capabilities = _promoted_capabilities()
    capabilities["contract_version"] = "1.18.0"
    with _Server(_envelope(), capabilities=capabilities) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).bridge_to_xdex_utilization(
            chain="x1",
            evidence_sha256=EVIDENCE,
            route_id=ROUTE,
            source_mint=SOURCE,
            destination_mint=DEST,
            evaluated_at=AS_OF + 10,
            max_evidence_age_seconds=300,
        )
    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == (
        "cmis_bridge_to_xdex_contract_unavailable"
    )
    assert running.requests == []


def test_x1_bridge_product_preserves_validated_cmis_projection():
    product = build_x1_bridge_to_xdex_utilization(
        _envelope(),
        expected_request=_request(),
    )
    assert product["contract_version"] == "x1_bridge_to_xdex_utilization/v1"
    assert product["bridge_to_xdex"] == _envelope()["data"]
    assert product["verified_xdex_program_family_is_global_x1_dex_scope"] is False
    assert product["bridge_activity_is_adoption"] is False
    assert product["liquidity_is_volume"] is False
    assert product["causal_inference_authorized"] is False
    assert product["automatic_risk_conclusion_authorized"] is False
    assert product["risk_interpretation"] is None
    assert product["execution_authorized"] is False
