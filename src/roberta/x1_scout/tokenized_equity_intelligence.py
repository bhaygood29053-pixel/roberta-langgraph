"""Typed X1 Scout projection for promoted CMIS Tokenized Equity Intelligence v1."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Literal, NotRequired, TypedDict

from roberta.cmis.tokenized_equity_intelligence import (
    CMISTokenizedEquityContractError,
    SERVICE_CONTRACT_VERSION as CMIS_TOKENIZED_EQUITY_CONTRACT,
    normalize_tokenized_equity_intelligence_request,
    validate_tokenized_equity_intelligence_response,
)

X1_TOKENIZED_EQUITY_CONTRACT = "x1_tokenized_equity_intelligence/v1"


class X1TokenizedEquityContractError(ValueError):
    """Raised when CMIS output cannot satisfy the bounded X1 Scout product."""


TokenizedEquityComponentState = Literal[
    "AVAILABLE", "EVIDENCE_REQUIRED", "UNAVAILABLE", "ERROR"
]


class X1TokenizedEquitySubject(TypedDict):
    chain: str
    asset_mint: str
    asset_id_kind: str
    security_id: str | None
    security_id_kind: str | None


class X1TokenizedEquityProjection(TypedDict):
    contract_version: str
    product: str
    chain: Literal["x1"]
    status: Literal["ok", "partial"]
    cmis_contract_version: str
    subject_resolution_state: Literal["RESOLVED", "EVIDENCE_REQUIRED"]
    selected_subject: X1TokenizedEquitySubject
    resolved_subject: X1TokenizedEquitySubject | None
    requested_components: list[str]
    component_states: dict[str, TokenizedEquityComponentState]
    components: dict[str, object]
    evidence_quality: dict[str, object] | None
    observed_at: object | None
    freshness: dict[str, object]
    confidence: dict[str, object]
    sources: list[object]
    warnings: list[object]
    errors: list[object]
    evidence_receipt: NotRequired[dict[str, object]]
    proof_score: NotRequired[dict[str, object]]
    missing_evidence_zero_filled: bool
    component_state_semantics_preserved: bool
    beneficial_ownership_inference_authorized: bool
    shareholder_status_inference_authorized: bool
    legal_or_economic_equivalence_inference_authorized: bool
    live_deployment_inference_authorized: bool
    bridge_route_inference_authorized: bool
    adoption_inference_authorized: bool
    liquidity_volume_equivalence_authorized: bool
    transfer_trade_equivalence_authorized: bool
    reference_executed_price_equivalence_authorized: bool
    proof_score_as_risk_authorized: bool
    causality_inference_authorized: bool
    automatic_risk_conclusion_authorized: bool
    investment_recommendation_authorized: bool
    legal_advice_authorized: bool
    read_only: bool
    execution_authorized: bool


def _selected_subject(expected_request: Mapping[str, Any]) -> X1TokenizedEquitySubject:
    normalized = normalize_tokenized_equity_intelligence_request(
        chain=expected_request.get("chain", "x1"),
        asset_mint=expected_request.get("asset_mint"),
        security_id=expected_request.get("security_id"),
        security_id_kind=expected_request.get("security_id_kind"),
        requested_components=expected_request.get("requested_components"),
    )
    return {
        "chain": "x1",
        "asset_mint": normalized["asset_mint"],
        "asset_id_kind": "mint",
        "security_id": normalized["security_id"],
        "security_id_kind": normalized["security_id_kind"],
    }


def build_x1_tokenized_equity_intelligence(
    result: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> X1TokenizedEquityProjection:
    """Project accepted CMIS facts into Scout without adding new chain claims."""

    try:
        safe = validate_tokenized_equity_intelligence_response(
            result,
            expected_request=expected_request,
        )
        selected = _selected_subject(expected_request)
    except CMISTokenizedEquityContractError as exc:
        raise X1TokenizedEquityContractError(str(exc)) from exc

    data = safe["data"]
    product: X1TokenizedEquityProjection = {
        "contract_version": X1_TOKENIZED_EQUITY_CONTRACT,
        "product": "x1_tokenized_equity_intelligence",
        "chain": "x1",
        "status": safe["status"],
        "cmis_contract_version": CMIS_TOKENIZED_EQUITY_CONTRACT,
        "subject_resolution_state": data["subject_resolution_state"],
        "selected_subject": selected,
        "resolved_subject": deepcopy(data.get("resolved_subject")),
        "requested_components": deepcopy(data["requested_components"]),
        "component_states": deepcopy(data["component_states"]),
        "components": deepcopy(data["components"]),
        "evidence_quality": deepcopy(data.get("evidence_quality")),
        "observed_at": safe.get("observed_at"),
        "freshness": deepcopy(safe["freshness"]),
        "confidence": deepcopy(safe["confidence"]),
        "sources": deepcopy(safe["sources"]),
        "warnings": deepcopy(safe["warnings"]),
        "errors": deepcopy(safe["errors"]),
        "missing_evidence_zero_filled": False,
        "component_state_semantics_preserved": True,
        "beneficial_ownership_inference_authorized": False,
        "shareholder_status_inference_authorized": False,
        "legal_or_economic_equivalence_inference_authorized": False,
        "live_deployment_inference_authorized": False,
        "bridge_route_inference_authorized": False,
        "adoption_inference_authorized": False,
        "liquidity_volume_equivalence_authorized": False,
        "transfer_trade_equivalence_authorized": False,
        "reference_executed_price_equivalence_authorized": False,
        "proof_score_as_risk_authorized": False,
        "causality_inference_authorized": False,
        "automatic_risk_conclusion_authorized": False,
        "investment_recommendation_authorized": False,
        "legal_advice_authorized": False,
        "read_only": True,
        "execution_authorized": False,
    }
    if isinstance(safe.get("evidence_receipt"), Mapping):
        product["evidence_receipt"] = deepcopy(dict(safe["evidence_receipt"]))
    if isinstance(safe.get("proof_score"), Mapping):
        product["proof_score"] = deepcopy(dict(safe["proof_score"]))
    return product


__all__ = [
    "CMIS_TOKENIZED_EQUITY_CONTRACT",
    "TokenizedEquityComponentState",
    "X1_TOKENIZED_EQUITY_CONTRACT",
    "X1TokenizedEquityContractError",
    "X1TokenizedEquityProjection",
    "X1TokenizedEquitySubject",
    "build_x1_tokenized_equity_intelligence",
]
