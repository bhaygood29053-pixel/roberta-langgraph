from __future__ import annotations

from copy import deepcopy

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    CROSS_CHAIN_PROVENANCE_MIN_CMIS_CONTRACT_VERSION,
    CROSS_CHAIN_PROVENANCE_REQUIRED_LIMITATIONS,
    CROSS_CHAIN_PROVENANCE_REQUIRED_REQUIREMENTS,
    require_cross_chain_provenance_capability,
    validate_capability_manifest,
)
from roberta.cmis.cross_chain_provenance import (
    CMISCrossChainProvenanceContractError,
    SERVICE_CONTRACT_VERSION,
    normalize_cross_chain_provenance_request,
    validate_cross_chain_provenance_response,
)
from roberta.cmis.http import CMISHTTPClient
from roberta.x1_scout.cross_chain_provenance import (
    build_x1_cross_chain_provenance,
)
from roberta.x1_scout.graph import build_x1_scout_graph
from tests.test_cmis_http_client import _Server, _capabilities


SOL = "So11111111111111111111111111111111111111112"
CURRENT = "JDqX4vau2P5zJmLpuNitvR6vMURr9kYjex6oZQXz3Ja8"
EVIDENCE = "b" * 64


def _promoted_capabilities():
    value = deepcopy(_capabilities())
    value["contract_version"] = "1.20.0"
    value["supported_services"].append("cross_chain_asset_provenance")
    x1 = value["chains"]["x1"]
    x1["services"]["cross_chain_asset_provenance"] = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": SERVICE_CONTRACT_VERSION,
        "requirements": list(CROSS_CHAIN_PROVENANCE_REQUIRED_REQUIREMENTS),
        "limitations": list(CROSS_CHAIN_PROVENANCE_REQUIRED_LIMITATIONS),
        "execution_authorized": False,
    }
    x1["callable_services"].append("cross_chain_asset_provenance")
    solana = value["chains"]["solana"]
    solana["services"]["cross_chain_asset_provenance"] = {
        "state": "unavailable",
        "callable": False,
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "service_contract_version": SERVICE_CONTRACT_VERSION,
        "requirements": [],
        "limitations": ["cross_chain_asset_provenance_not_available_for_chain"],
        "execution_authorized": False,
    }
    return value


def _request():
    return normalize_cross_chain_provenance_request(
        evidence_sha256=EVIDENCE,
        current_asset_id=CURRENT,
        current_asset_id_kind="mint",
    )


def _canonical():
    lineage = [{
        "source": {
            "chain": "solana",
            "asset_id": SOL,
            "asset_id_kind": "mint",
        },
        "destination": {
            "chain": "x1",
            "asset_id": CURRENT,
            "asset_id_kind": "mint",
        },
        "bridge": "Warp",
        "representation_type": "wrapped",
        "custody_model": "bridge_custody_dependency",
        "backing_asset_id": SOL,
        "bridge_route_id": "warp-solana-x1-wsol",
    }]
    return {
        "contract": SERVICE_CONTRACT_VERSION,
        "canonical_asset_id": "wSOL",
        "origin": {
            "chain": "solana",
            "asset_id": SOL,
            "asset_id_kind": "mint",
        },
        "current": {
            "chain": "x1",
            "asset_id": CURRENT,
            "asset_id_kind": "mint",
        },
        "representation_depth": 1,
        "lineage": lineage,
        "dependencies": [{
            "bridge": "Warp",
            "custody_model": "bridge_custody_dependency",
        }],
        "verification": {
            "structural_continuity_verified": True,
            "exact_chain_scoped_identifiers_required": True,
            "symbol_equivalence_authorized": False,
            "live_bridge_state_verified": False,
            "backing_verified": False,
            "custody_verified": False,
            "source_independence_verified": False,
        },
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "execution_authorized": False,
    }


def _envelope():
    canonical = _canonical()
    return {
        "service": "cross_chain_asset_provenance",
        "chain": "x1",
        "status": "ok",
        "asset": {
            "canonical_id": CURRENT,
            "asset_id": CURRENT,
            "asset_id_kind": "mint",
        },
        "data": {
            "contract_version": SERVICE_CONTRACT_VERSION,
            "public_service_promoted": True,
            "scout_reliance_promoted": True,
            "read_only": True,
            "canonical_asset_id": canonical["canonical_asset_id"],
            "origin": deepcopy(canonical["origin"]),
            "current": deepcopy(canonical["current"]),
            "representation_depth": canonical["representation_depth"],
            "lineage": deepcopy(canonical["lineage"]),
            "dependencies": deepcopy(canonical["dependencies"]),
            "verification": deepcopy(canonical["verification"]),
            "evidence": {
                "evidence_sha256": EVIDENCE,
                "source_independence_verified": False,
            },
            "canonical_provenance": canonical,
            "symbol_or_name_identity_inference_authorized": False,
            "bridge_dependency_is_risk": False,
            "custody_dependency_is_risk": False,
            "backing_claim_authorized": False,
            "solvency_claim_authorized": False,
            "safety_claim_authorized": False,
            "adoption_claim_authorized": False,
            "causal_inference_authorized": False,
            "current_bridge_state_claim_authorized": False,
            "risk_promotion_authorized": False,
            "execution_authorized": False,
        },
        "risk": None,
        "confidence": {
            "structural_continuity_verified": True,
            "exact_chain_scoped_identifiers_required": True,
            "source_independence_verified": False,
        },
        "sources": [],
        "observed_at": None,
        "warnings": [{
            "code": "structural_provenance_only",
            "message": "bounded structural identity continuity",
        }],
        "errors": [],
        "execution_authorized": False,
    }


def test_cmis_120_provenance_capability_is_exact_and_bounded():
    manifest = validate_capability_manifest(_promoted_capabilities())
    capability = require_cross_chain_provenance_capability(manifest)
    assert CROSS_CHAIN_PROVENANCE_MIN_CMIS_CONTRACT_VERSION == "1.20.0"
    assert capability["service_contract_version"] == SERVICE_CONTRACT_VERSION
    assert capability["state"] == "bounded"
    assert capability["public_service_promoted"] is True
    assert capability["scout_reliance_promoted"] is True
    assert capability["execution_authorized"] is False


def test_provenance_capability_rejects_identity_guardrail_drift():
    raw = _promoted_capabilities()
    raw["chains"]["x1"]["services"]["cross_chain_asset_provenance"][
        "limitations"
    ].remove("symbol_or_name_equality_is_not_identity_proof")
    manifest = validate_capability_manifest(raw)
    with pytest.raises(CMISCapabilityContractError, match="missing accepted limitations"):
        require_cross_chain_provenance_capability(manifest)


def test_provenance_response_preserves_ordered_lineage_and_no_risk():
    accepted = validate_cross_chain_provenance_response(
        _envelope(),
        expected_request=_request(),
    )
    data = accepted["data"]
    assert accepted["risk"] is None
    assert data["origin"]["chain"] == "solana"
    assert data["current"]["chain"] == "x1"
    assert data["representation_depth"] == 1
    assert [hop["bridge"] for hop in data["lineage"]] == ["Warp"]
    assert data["verification"]["symbol_equivalence_authorized"] is False
    assert data["verification"]["live_bridge_state_verified"] is False
    assert data["verification"]["backing_verified"] is False
    assert data["bridge_dependency_is_risk"] is False
    assert data["risk_promotion_authorized"] is False


@pytest.mark.parametrize(
    ("mutate", "match"),
    [
        (
            lambda x: x["data"]["current"].__setitem__("asset_id_kind", "symbol"),
            "symbol/name labels",
        ),
        (
            lambda x: x["data"].__setitem__("representation_depth", 2),
            "ordered lineage length",
        ),
        (
            lambda x: x["data"]["lineage"][0].__setitem__("bridge", "Other"),
            "canonical provenance lineage diverged",
        ),
        (
            lambda x: x["data"].__setitem__("bridge_dependency_is_risk", True),
            "bridge_dependency_is_risk",
        ),
        (
            lambda x: x.__setitem__("risk", {"level": "LOW"}),
            "must not promote a risk conclusion",
        ),
    ],
)
def test_provenance_response_fails_closed_on_identity_lineage_or_risk_drift(
    mutate,
    match,
):
    bad = _envelope()
    mutate(bad)
    with pytest.raises(CMISCrossChainProvenanceContractError, match=match):
        validate_cross_chain_provenance_response(
            bad,
            expected_request=_request(),
        )


def test_http_client_posts_only_selector_and_exact_current_identity():
    expected = _envelope()
    with _Server(expected, capabilities=_promoted_capabilities()) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).cross_chain_asset_provenance(
            chain="x1",
            evidence_sha256=EVIDENCE,
            current_asset_id=CURRENT,
            current_asset_id_kind="mint",
        )

    assert result == expected
    assert running.requests == [{
        "service": "cross_chain_asset_provenance",
        "chain": "x1",
        "asset": CURRENT,
        "params": _request(),
    }]


def test_http_client_blocks_provenance_before_cmis_120_without_post():
    capabilities = _promoted_capabilities()
    capabilities["contract_version"] = "1.19.0"
    with _Server(_envelope(), capabilities=capabilities) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).cross_chain_asset_provenance(
            chain="x1",
            evidence_sha256=EVIDENCE,
            current_asset_id=CURRENT,
            current_asset_id_kind="mint",
        )
    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == (
        "cmis_cross_chain_provenance_contract_unavailable"
    )
    assert running.requests == []


def test_x1_provenance_product_preserves_validated_cmis_projection():
    product = build_x1_cross_chain_provenance(
        _envelope(),
        expected_request=_request(),
    )
    assert product["contract_version"] == "x1_cross_chain_asset_provenance/v1"
    assert product["provenance"] == _envelope()["data"]
    assert product["symbol_or_name_identity_inference_authorized"] is False
    assert product["bridge_dependency_is_risk"] is False
    assert product["automatic_risk_conclusion_authorized"] is False
    assert product["risk_interpretation"] is None
    assert product["execution_authorized"] is False


class _GraphClient:
    def __init__(self):
        self.asset_lookup_calls = 0
        self.provenance_calls = []

    def capabilities(self):
        return validate_capability_manifest(_promoted_capabilities())

    def asset_lookup(self, *, chain, asset):
        self.asset_lookup_calls += 1
        raise AssertionError("provenance operation must not issue identity preflight")

    def cross_chain_asset_provenance(
        self,
        *,
        chain,
        evidence_sha256,
        current_asset_id,
        current_asset_id_kind,
    ):
        self.provenance_calls.append({
            "chain": chain,
            "evidence_sha256": evidence_sha256,
            "current_asset_id": current_asset_id,
            "current_asset_id_kind": current_asset_id_kind,
        })
        return _envelope()


def test_x1_scout_report_uses_single_cmis_provenance_authority_path():
    client = _GraphClient()
    graph = build_x1_scout_graph(client)
    result = graph.invoke({
        "request": {
            "asset": CURRENT,
            "objective": "Show the canonical cross-chain provenance.",
            "operation": "cross_chain_asset_provenance",
            "provenance_evidence_sha256": EVIDENCE,
            "provenance_current_asset_id": CURRENT,
            "provenance_current_asset_id_kind": "mint",
        },
        "status": "running",
    })
    report = result["report"]
    assert client.asset_lookup_calls == 0
    assert client.provenance_calls == [{
        "chain": "x1",
        "evidence_sha256": EVIDENCE,
        "current_asset_id": CURRENT,
        "current_asset_id_kind": "mint",
    }]
    product = report["x1_cross_chain_asset_provenance"]
    assert product["provenance"]["representation_depth"] == 1
    assert product["provenance"]["lineage"] == _envelope()["data"]["lineage"]
    assert product["risk_interpretation"] is None
    assert product["execution_authorized"] is False
