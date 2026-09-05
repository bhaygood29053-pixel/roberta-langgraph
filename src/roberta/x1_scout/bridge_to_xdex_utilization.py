"""Deterministic X1 Scout projection of CMIS Bridge-to-XDEX Utilization v1.

The Scout product preserves the validated CMIS public projection verbatim.
It does not recalculate bridge flow, supply, XDEX market values, utilization,
adoption, causality, or risk.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.cmis.bridge_to_xdex import (
    SERVICE_CONTRACT_VERSION as CMIS_BRIDGE_TO_XDEX_CONTRACT,
    validate_bridge_to_xdex_response,
)

BRIDGE_TO_XDEX_CONTRACT = "x1_bridge_to_xdex_utilization/v1"


class X1BridgeToXdexContractError(ValueError):
    """Raised when CMIS output cannot satisfy the X1 Scout product."""


def build_x1_bridge_to_xdex_utilization(
    result: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, object]:
    try:
        safe = validate_bridge_to_xdex_response(
            result,
            expected_request=expected_request,
        )
    except Exception as exc:
        raise X1BridgeToXdexContractError(str(exc)) from exc

    data = safe["data"]
    return {
        "contract_version": BRIDGE_TO_XDEX_CONTRACT,
        "product": "x1_bridge_to_xdex_utilization",
        "chain": "x1",
        "status": "ok",
        "requested_destination_mint": expected_request["destination_mint"],
        "cmis_contract_version": CMIS_BRIDGE_TO_XDEX_CONTRACT,
        "bridge_to_xdex": deepcopy(data),
        "observed_at": safe.get("observed_at"),
        "confidence": deepcopy(safe.get("confidence") or {}),
        "sources": deepcopy(safe.get("sources") or []),
        "warnings": deepcopy(safe.get("warnings") or []),
        "errors": deepcopy(safe.get("errors") or []),
        "evidence_receipt": deepcopy(safe.get("evidence_receipt")),
        "proof_score": deepcopy(safe.get("proof_score")),
        "verified_xdex_program_family_is_global_x1_dex_scope": False,
        "bridge_activity_is_adoption": False,
        "liquidity_is_volume": False,
        "causal_inference_authorized": False,
        "automatic_risk_conclusion_authorized": False,
        "risk_interpretation": None,
        "execution_authorized": False,
    }


__all__ = [
    "BRIDGE_TO_XDEX_CONTRACT",
    "CMIS_BRIDGE_TO_XDEX_CONTRACT",
    "X1BridgeToXdexContractError",
    "build_x1_bridge_to_xdex_utilization",
]
