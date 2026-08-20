from copy import deepcopy
import json

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    CMISCapabilityUnavailable,
    validate_capability_manifest,
)
from roberta.cmis.concentration_intelligence import (
    ACCEPTED_CONCLUSION_TYPE,
    PROMOTION_SCOPE,
    SERVICE,
    SERVICE_CONTRACT_VERSION,
    normalize_intelligence_evidence_id,
    require_concentration_intelligence_promotion,
)
from roberta.cmis.http import CMISHTTPClient
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.tool import build_x1_scout_tool
from tests.test_cmis_http_client import _Server, _capabilities


EVIDENCE_ID = "ie_" + ("a" * 64)


def _promoted_capabilities() -> dict[str, object]:
    manifest = deepcopy(_capabilities())
    manifest["contract_version"] = "1.9.0"
    services = manifest["supported_services"]
    services.append(SERVICE)

    x1 = manifest["chains"]["x1"]
    x1["services"][SERVICE] = {
        "state": "bounded",
        "callable": True,
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "service_contract_version": SERVICE_CONTRACT_VERSION,
        "promotion_scope": PROMOTION_SCOPE,
        "accepted_conclusion_types": [ACCEPTED_CONCLUSION_TYPE],
        "requirements": ["exact_x1_asset_id", "cmis_owned_intelligence_evidence_id"],
        "limitations": [
            "no_behavioral_or_ownership_labels",
            "no_execution_authorization",
        ],
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
        "service_contract_version": SERVICE_CONTRACT_VERSION,
        "promotion_scope": None,
        "accepted_conclusion_types": [],
        "requirements": [],
        "limitations": ["concentration_change_intelligence_not_available_for_chain"],
        "execution_authorized": False,
    }
    return manifest


def _intelligence_envelope(*, status: str = "ok") -> dict[str, object]:
    return {
        "service": SERVICE,
        "chain": "x1",
        "status": status,
        "asset": {"canonical_id": "AGI"},
        "data": {
            "contract_version": SERVICE_CONTRACT_VERSION,
            "read_only": True,
            "public_service_promoted": True,
            "scout_reliance_promoted": True,
            "promotion_scope": PROMOTION_SCOPE,
            "accepted_conclusion_type": ACCEPTED_CONCLUSION_TYPE,
            "asset_id": "AGI",
            "facts": {
                "conclusion_type": ACCEPTED_CONCLUSION_TYPE,
                "chain": "x1",
                "asset_id": "AGI",
                "before_ratio": 0.20,
                "after_ratio": 0.24,
                "delta_bps": 400,
                "scope": "observed_top_token_accounts",
            },
            "policy_assessment": None,
            "risk_interpretation": None,
            "evidence": {
                "intelligence_evidence_id": EVIDENCE_ID,
                "receipt_ids": ["er_test"],
                "proof_records": [
                    {
                        "receipt_id": "er_test",
                        "proof_strength": "MODERATE",
                        "proof_percent": 75.0,
                        "method": "test_only",
                    }
                ],
                "freshness_verified": True,
                "unresolved_fields": [],
                "limitations": ["token_accounts_are_not_unique_holders"],
                "intelligence_evidence": {"intelligence_evidence_id": EVIDENCE_ID},
            },
            "proof_strength_separate_from_risk": True,
            "behavioral_interpretation_added": False,
            "provider_assertion_promoted": False,
            "execution_authorized": False,
        },
        "risk": None,
        "confidence": {
            "cmis_owned_evidence_resolved": True,
            "deterministic_evidence_revalidated": True,
            "freshness_verified": True,
            "unresolved_fields": [],
        },
        "sources": [{"source": "x1_rpc", "role": "verifier"}],
        "observed_at": "2026-08-20T02:00:00Z",
        "warnings": [],
        "errors": [],
    }


def test_canonical_intelligence_id_is_exact_and_lowercase_content_addressed() -> None:
    assert normalize_intelligence_evidence_id(EVIDENCE_ID) == EVIDENCE_ID
    for invalid in (
        None,
        "ie_short",
        "ie_" + ("A" * 64),
        " " + EVIDENCE_ID,
        "er_" + ("a" * 64),
    ):
        with pytest.raises(ValueError, match="canonical ie_ content id"):
            normalize_intelligence_evidence_id(invalid)


def test_promoted_x1_contract_is_accepted_without_promoting_phase11_foundation() -> None:
    raw = _promoted_capabilities()
    normalized = validate_capability_manifest(raw)
    promotion = require_concentration_intelligence_promotion(raw, chain="x1")

    assert normalized["contract_version"] == "1.9.0"
    assert normalized["intelligence_foundation"]["public_service_promoted"] is False
    assert normalized["intelligence_foundation"]["scout_reliance_promoted"] is False
    assert promotion["public_service_promoted"] is True
    assert promotion["scout_reliance_promoted"] is True
    assert promotion["execution_authorized"] is False


def test_promoted_service_fails_closed_on_old_or_weakened_promotion_contract() -> None:
    old = _promoted_capabilities()
    old["contract_version"] = "1.8.9"
    with pytest.raises(CMISCapabilityContractError, match="requires contract 1.9.0"):
        require_concentration_intelligence_promotion(old, chain="x1")

    weakened = _promoted_capabilities()
    weakened["chains"]["x1"]["services"][SERVICE]["scout_reliance_promoted"] = False
    with pytest.raises(CMISCapabilityContractError, match="scout_reliance_promoted"):
        require_concentration_intelligence_promotion(weakened, chain="x1")

    widened = _promoted_capabilities()
    widened["chains"]["x1"]["services"][SERVICE]["accepted_conclusion_types"] = [
        ACCEPTED_CONCLUSION_TYPE,
        "wallet_behavior",
    ]
    with pytest.raises(CMISCapabilityContractError, match="conclusion scope drifted"):
        require_concentration_intelligence_promotion(widened, chain="x1")


def test_solana_concentration_intelligence_remains_unavailable() -> None:
    with pytest.raises(CMISCapabilityUnavailable, match="solana"):
        require_concentration_intelligence_promotion(
            _promoted_capabilities(),
            chain="solana",
        )


def test_http_client_posts_only_exact_asset_and_cmis_owned_evidence_id() -> None:
    expected = _intelligence_envelope()
    with _Server(expected, capabilities=_promoted_capabilities()) as running:
        client = CMISHTTPClient(base_url=running.base_url, timeout_seconds=2)
        result = client.concentration_change_intelligence(
            chain="x1",
            asset="AGI",
            intelligence_evidence_id=EVIDENCE_ID,
        )

    assert result == expected
    assert running.requests == [
        {
            "service": SERVICE,
            "chain": "x1",
            "asset": "AGI",
            "params": {"intelligence_evidence_id": EVIDENCE_ID},
        }
    ]


def test_http_client_blocks_weakened_promotion_before_post() -> None:
    capabilities = _promoted_capabilities()
    capabilities["chains"]["x1"]["services"][SERVICE]["public_service_promoted"] = False
    with _Server(_intelligence_envelope(), capabilities=capabilities) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).concentration_change_intelligence(
            chain="x1",
            asset="AGI",
            intelligence_evidence_id=EVIDENCE_ID,
        )

    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == "cmis_capability_contract_unavailable"
    assert running.requests == []


class _IntelligenceOnlyCMIS:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def concentration_change_intelligence(
        self,
        *,
        chain: str,
        asset: str,
        intelligence_evidence_id: str,
    ) -> dict[str, object]:
        self.calls.append(
            {
                "chain": chain,
                "asset": asset,
                "intelligence_evidence_id": intelligence_evidence_id,
            }
        )
        return _intelligence_envelope()


def test_x1_scout_explicit_operation_preserves_facts_proof_and_risk_separation() -> None:
    cmis = _IntelligenceOnlyCMIS()
    graph = build_x1_scout_graph(cmis)  # type: ignore[arg-type]
    result = graph.invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "explain this exact concentration-change evidence",
                "operation": SERVICE,
                "intelligence_evidence_id": EVIDENCE_ID,
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert cmis.calls == [
        {"chain": "x1", "asset": "AGI", "intelligence_evidence_id": EVIDENCE_ID}
    ]
    assert report["plan"]["source"] == "explicit"
    assert report["source"] == {"service": "cmis", "operation": SERVICE}
    assert report["findings"]["risk"] is None
    data = report["findings"]["data"]
    assert data["facts"]["delta_bps"] == 400
    assert data["risk_interpretation"] is None
    assert data["behavioral_interpretation_added"] is False
    assert data["evidence"]["proof_records"][0]["proof_strength"] == "MODERATE"
    assert data["evidence"]["limitations"] == ["token_accounts_are_not_unique_holders"]
    assert data["execution_authorized"] is False


def test_x1_scout_tool_never_invents_or_accepts_malformed_intelligence_id() -> None:
    cmis = _IntelligenceOnlyCMIS()
    tool = build_x1_scout_tool(cmis)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="canonical ie_ content id"):
        tool.invoke(
            {
                "asset": "AGI",
                "objective": "inspect concentration change",
                "operation": SERVICE,
                "intelligence_evidence_id": "ie_not_a_content_id",
            }
        )
    assert cmis.calls == []

    encoded = tool.invoke(
        {
            "asset": "AGI",
            "objective": "inspect concentration change",
            "operation": SERVICE,
            "intelligence_evidence_id": EVIDENCE_ID,
        }
    )
    report = json.loads(encoded)
    assert report["source"]["operation"] == SERVICE
    assert cmis.calls[-1]["intelligence_evidence_id"] == EVIDENCE_ID
