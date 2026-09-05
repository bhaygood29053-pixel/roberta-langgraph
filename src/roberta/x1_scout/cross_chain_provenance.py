"""Deterministic X1 Scout projection of CMIS cross-chain provenance v1.

The product preserves the validated CMIS public projection verbatim. It does
not reconstruct hops, recalculate representation depth, infer identity from
labels, or convert dependency metadata into risk.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.cmis.cross_chain_provenance import (
    SERVICE_CONTRACT_VERSION as CMIS_CROSS_CHAIN_PROVENANCE_CONTRACT,
    validate_cross_chain_provenance_response,
)

CROSS_CHAIN_PROVENANCE_CONTRACT = "x1_cross_chain_asset_provenance/v1"


class X1CrossChainProvenanceContractError(ValueError):
    """CMIS output cannot satisfy the X1 Scout provenance product."""


def build_x1_cross_chain_provenance(
    result: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, object]:
    try:
        safe = validate_cross_chain_provenance_response(
            result,
            expected_request=expected_request,
        )
    except Exception as exc:
        raise X1CrossChainProvenanceContractError(str(exc)) from exc

    data = safe["data"]
    return {
        "contract_version": CROSS_CHAIN_PROVENANCE_CONTRACT,
        "product": "x1_cross_chain_asset_provenance",
        "chain": "x1",
        "status": "ok",
        "requested_current_asset_id": expected_request["current_asset_id"],
        "requested_current_asset_id_kind": expected_request[
            "current_asset_id_kind"
        ],
        "cmis_contract_version": CMIS_CROSS_CHAIN_PROVENANCE_CONTRACT,
        "provenance": deepcopy(data),
        "observed_at": safe.get("observed_at"),
        "confidence": deepcopy(safe.get("confidence") or {}),
        "sources": deepcopy(safe.get("sources") or []),
        "warnings": deepcopy(safe.get("warnings") or []),
        "errors": deepcopy(safe.get("errors") or []),
        "evidence_receipt": deepcopy(safe.get("evidence_receipt")),
        "proof_score": deepcopy(safe.get("proof_score")),
        "symbol_or_name_identity_inference_authorized": False,
        "bridge_dependency_is_risk": False,
        "custody_dependency_is_risk": False,
        "backing_claim_authorized": False,
        "solvency_claim_authorized": False,
        "safety_claim_authorized": False,
        "adoption_claim_authorized": False,
        "causal_inference_authorized": False,
        "current_bridge_state_claim_authorized": False,
        "automatic_risk_conclusion_authorized": False,
        "risk_interpretation": None,
        "execution_authorized": False,
    }


__all__ = [
    "CMIS_CROSS_CHAIN_PROVENANCE_CONTRACT",
    "CROSS_CHAIN_PROVENANCE_CONTRACT",
    "X1CrossChainProvenanceContractError",
    "build_x1_cross_chain_provenance",
]
