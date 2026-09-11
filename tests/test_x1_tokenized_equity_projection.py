from __future__ import annotations

from copy import deepcopy
from typing import get_args

import pytest

from roberta.cmis.contracts import CMISOperation, CMISService
from roberta.cmis.tokenized_equity_intelligence import (
    CMISTokenizedEquityContractError,
    normalize_tokenized_equity_intelligence_request,
    validate_tokenized_equity_intelligence_response,
)
from roberta.x1_scout.tokenized_equity_intelligence import (
    X1_TOKENIZED_EQUITY_CONTRACT,
    X1TokenizedEquityContractError,
    build_x1_tokenized_equity_intelligence,
)

MINT = "1" * 32
OTHER_MINT = "2" * 32
SECURITY_ID = "US0378331005"
OBSERVED_AT = "2026-09-11T02:50:00Z"


def _request(*, components: list[str] | None = None) -> dict[str, object]:
    return {
        "chain": "x1",
        "asset_mint": MINT,
        "security_id": SECURITY_ID,
        "security_id_kind": "isin",
        "requested_components": components or ["provenance", "rights", "market_activity"],
    }


def _component(contract: str, **extra: object) -> dict[str, object]:
    return {"contract": contract, "execution_authorized": False, **extra}


def _resolved_response() -> dict[str, object]:
    requested = ["provenance", "rights", "market_activity"]
    components = {
        "provenance": _component(
            "tokenized_equity_provenance/v1",
            token={"chain": "x1", "asset_id": MINT, "asset_id_kind": "mint"},
            underlying_security={"security_id": SECURITY_ID, "security_id_kind": "isin"},
        ),
        "rights": _component(
            "tokenized_equity_rights/v1",
            rights={"voting_rights": {"state": "UNKNOWN"}},
        ),
        "market_activity": _component(
            "tokenized_equity_market_activity/v1",
            metrics={"liquidity": {"state": "UNKNOWN"}},
        ),
    }
    return {
        "service": "tokenized_equity_intelligence",
        "chain": "x1",
        "status": "ok",
        "asset": {"canonical_id": MINT, "asset_id": MINT, "asset_id_kind": "mint"},
        "data": {
            "contract_version": "tokenized_equity_intelligence/v1",
            "request_contract_version": "tokenized_equity_intelligence_request/v1",
            "materialization_contract_version": "tokenized_equity_intelligence_materialization/v1",
            "materialization_id": "tei_" + ("a" * 64),
            "subject_resolution_state": "RESOLVED",
            "resolved_subject": {
                "chain": "x1",
                "asset_mint": MINT,
                "asset_id_kind": "mint",
                "security_id": SECURITY_ID,
                "security_id_kind": "isin",
            },
            "requested_components": requested,
            "component_states": {name: "AVAILABLE" for name in requested},
            "components": components,
            "evidence_quality": {
                "contract": "tokenized_equity_evidence_quality/v1",
                "component_receipts": [],
                "evidence_receipts": [],
                "execution_authorized": False,
            },
            "live_x1_equity_deployment_verified": False,
            "live_robinhood_x1_route_verified": False,
            "rights_are_legal_adjudication": False,
            "liquidity_equals_volume": False,
            "transfer_equals_trade": False,
            "bridge_flow_equals_adoption": False,
            "reference_price_equals_executed_price": False,
            "proof_score_separate_from_risk": True,
            "read_only": True,
            "public_service_promoted": True,
            "scout_reliance_promoted": True,
            "execution_authorized": False,
        },
        "risk": None,
        "confidence": {
            "basis": "accepted_rwa_component_and_evidence_quality_contracts",
            "proof_score": None,
            "proof_score_owned_by_protected_runtime": True,
            "proof_score_separate_from_risk": True,
            "complete_requested_component_coverage": True,
        },
        "sources": [{"source_id": "cmis-private-core"}],
        "observed_at": OBSERVED_AT,
        "freshness": {
            "contract_version": "cmis_response_freshness/v1",
            "scope": "tokenized_equity_intelligence.response",
            "state": "UNKNOWN",
            "freshness_verified": None,
            "observed_at": OBSERVED_AT,
            "details": {},
            "reason": "service_specific_freshness_not_supplied",
        },
        "warnings": [{"code": "bounded_tokenized_equity_scope"}],
        "errors": [],
        "evidence_receipt": {
            "contract_version": "cmis_evidence_receipt/v1",
            "receipt_id": "receipt-1",
        },
        "proof_score": {
            "contract_version": "cmis_proof_score/v1",
            "score": 87,
        },
        "read_only": True,
        "public_service_promoted": True,
        "scout_reliance_promoted": True,
        "runtime_capability_promoted": True,
        "execution_authorized": False,
    }


def _unresolved_response() -> dict[str, object]:
    value = _resolved_response()
    value["status"] = "partial"
    data = value["data"]
    assert isinstance(data, dict)
    data["subject_resolution_state"] = "EVIDENCE_REQUIRED"
    data["resolved_subject"] = None
    data["requested_components"] = ["provenance", "rights"]
    data["component_states"] = {"provenance": "EVIDENCE_REQUIRED", "rights": "EVIDENCE_REQUIRED"}
    data["components"] = {}
    data["evidence_quality"] = None
    confidence = value["confidence"]
    assert isinstance(confidence, dict)
    confidence["complete_requested_component_coverage"] = False
    value.pop("evidence_receipt")
    value.pop("proof_score")
    return value


def test_contract_types_include_promoted_tokenized_equity_service():
    assert "tokenized_equity_intelligence" in get_args(CMISService)
    assert "tokenized_equity_intelligence" in get_args(CMISOperation)


def test_selector_request_is_exact_normalized_and_provenance_first():
    request = normalize_tokenized_equity_intelligence_request(
        chain="X1",
        asset_mint=MINT,
        security_id=SECURITY_ID,
        security_id_kind="ISIN",
        requested_components=["market_activity", "provenance", "rights"],
    )
    assert request == {
        "contract_version": "tokenized_equity_intelligence_request/v1",
        "chain": "x1",
        "asset_mint": MINT,
        "security_id": SECURITY_ID,
        "security_id_kind": "isin",
        "requested_components": ["provenance", "rights", "market_activity"],
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"asset_mint": "A", "requested_components": ["provenance"]},
        {"asset_mint": MINT, "requested_components": ["rights"]},
        {"asset_mint": MINT, "requested_components": ["provenance", "provenance"]},
        {"asset_mint": MINT, "requested_components": ["provenance"], "security_id": SECURITY_ID},
    ],
)
def test_selector_request_rejects_ambiguous_or_incomplete_identity(kwargs: dict[str, object]):
    with pytest.raises(CMISTokenizedEquityContractError):
        normalize_tokenized_equity_intelligence_request(chain="x1", **kwargs)


def test_resolved_projection_preserves_components_evidence_and_truth_boundaries():
    source = _resolved_response()
    product = build_x1_tokenized_equity_intelligence(source, expected_request=_request())

    assert product["contract_version"] == X1_TOKENIZED_EQUITY_CONTRACT
    assert product["status"] == "ok"
    assert product["subject_resolution_state"] == "RESOLVED"
    assert product["selected_subject"]["asset_mint"] == MINT
    assert product["resolved_subject"]["security_id"] == SECURITY_ID
    assert product["component_states"] == {
        "provenance": "AVAILABLE",
        "rights": "AVAILABLE",
        "market_activity": "AVAILABLE",
    }
    assert product["components"] == source["data"]["components"]
    assert product["evidence_quality"] == source["data"]["evidence_quality"]
    assert product["evidence_receipt"] == source["evidence_receipt"]
    assert product["proof_score"] == source["proof_score"]
    assert product["missing_evidence_zero_filled"] is False
    assert product["component_state_semantics_preserved"] is True
    assert product["beneficial_ownership_inference_authorized"] is False
    assert product["shareholder_status_inference_authorized"] is False
    assert product["legal_or_economic_equivalence_inference_authorized"] is False
    assert product["live_deployment_inference_authorized"] is False
    assert product["bridge_route_inference_authorized"] is False
    assert product["adoption_inference_authorized"] is False
    assert product["liquidity_volume_equivalence_authorized"] is False
    assert product["transfer_trade_equivalence_authorized"] is False
    assert product["reference_executed_price_equivalence_authorized"] is False
    assert product["proof_score_as_risk_authorized"] is False
    assert product["causality_inference_authorized"] is False
    assert product["automatic_risk_conclusion_authorized"] is False
    assert product["investment_recommendation_authorized"] is False
    assert product["legal_advice_authorized"] is False
    assert product["execution_authorized"] is False


def test_partial_projection_preserves_evidence_required_without_zero_fill():
    source = _unresolved_response()
    product = build_x1_tokenized_equity_intelligence(
        source,
        expected_request=_request(components=["provenance", "rights"]),
    )
    assert product["status"] == "partial"
    assert product["subject_resolution_state"] == "EVIDENCE_REQUIRED"
    assert product["resolved_subject"] is None
    assert product["component_states"] == {
        "provenance": "EVIDENCE_REQUIRED",
        "rights": "EVIDENCE_REQUIRED",
    }
    assert product["components"] == {}
    assert product["evidence_quality"] is None
    assert "proof_score" not in product
    assert "evidence_receipt" not in product
    assert product["missing_evidence_zero_filled"] is False


def test_projection_deep_copies_cmis_material():
    source = _resolved_response()
    product = build_x1_tokenized_equity_intelligence(source, expected_request=_request())
    source["data"]["components"]["rights"]["rights"]["voting_rights"]["state"] = "VERIFIED"
    source["proof_score"]["score"] = 1
    assert product["components"]["rights"]["rights"]["voting_rights"]["state"] == "UNKNOWN"
    assert product["proof_score"]["score"] == 87


def test_response_rejects_selector_or_available_component_contract_mismatch():
    wrong_asset = _resolved_response()
    wrong_asset["asset"]["asset_id"] = OTHER_MINT
    with pytest.raises(CMISTokenizedEquityContractError):
        validate_tokenized_equity_intelligence_response(wrong_asset, expected_request=_request())

    wrong_contract = _resolved_response()
    wrong_contract["data"]["components"]["rights"]["contract"] = "rights/v999"
    with pytest.raises(CMISTokenizedEquityContractError):
        validate_tokenized_equity_intelligence_response(wrong_contract, expected_request=_request())


def test_response_rejects_component_state_strengthening_and_status_drift():
    widened = _unresolved_response()
    widened["data"]["component_states"]["rights"] = "AVAILABLE"
    with pytest.raises(CMISTokenizedEquityContractError):
        validate_tokenized_equity_intelligence_response(
            widened,
            expected_request=_request(components=["provenance", "rights"]),
        )

    wrong_status = _resolved_response()
    wrong_status["status"] = "partial"
    with pytest.raises(CMISTokenizedEquityContractError):
        validate_tokenized_equity_intelligence_response(wrong_status, expected_request=_request())


@pytest.mark.parametrize(
    ("location", "field", "value"),
    [
        ("top", "execution_authorized", True),
        ("top", "scout_reliance_promoted", False),
        ("data", "live_x1_equity_deployment_verified", True),
        ("data", "live_robinhood_x1_route_verified", True),
        ("data", "rights_are_legal_adjudication", True),
        ("data", "liquidity_equals_volume", True),
        ("data", "transfer_equals_trade", True),
        ("data", "bridge_flow_equals_adoption", True),
        ("data", "reference_price_equals_executed_price", True),
        ("data", "proof_score_separate_from_risk", False),
    ],
)
def test_response_rejects_truth_boundary_drift(location: str, field: str, value: object):
    source = _resolved_response()
    target = source if location == "top" else source["data"]
    target[field] = value
    with pytest.raises(CMISTokenizedEquityContractError):
        validate_tokenized_equity_intelligence_response(source, expected_request=_request())


def test_response_rejects_risk_or_public_proof_score_invention():
    risk = _resolved_response()
    risk["risk"] = {"severity": "HIGH"}
    with pytest.raises(CMISTokenizedEquityContractError):
        validate_tokenized_equity_intelligence_response(risk, expected_request=_request())

    proof = _resolved_response()
    proof["confidence"]["proof_score"] = 87
    with pytest.raises(CMISTokenizedEquityContractError):
        validate_tokenized_equity_intelligence_response(proof, expected_request=_request())


def test_scout_wraps_cmis_contract_errors_without_widening():
    source = _resolved_response()
    source["data"]["resolved_subject"]["security_id"] = "WRONG"
    with pytest.raises(X1TokenizedEquityContractError):
        build_x1_tokenized_equity_intelligence(source, expected_request=_request())
