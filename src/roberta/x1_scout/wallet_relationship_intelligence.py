"""Deterministic X1 Scout projection for CMIS Wallet Relationship Intelligence v1."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.cmis.wallet_relationship import (
    CMISWalletRelationshipContractError,
    SERVICE_CONTRACT_VERSION as CMIS_WALLET_RELATIONSHIP_CONTRACT,
    validate_wallet_relationship_response,
)

X1_WALLET_RELATIONSHIP_CONTRACT = "x1_wallet_relationship_intelligence/v1"


class X1WalletRelationshipContractError(ValueError):
    """Raised when CMIS output cannot satisfy the bounded Scout product."""


def build_x1_wallet_relationship_intelligence(
    result: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, object]:
    try:
        safe = validate_wallet_relationship_response(result, expected_request=expected_request)
    except CMISWalletRelationshipContractError as exc:
        raise X1WalletRelationshipContractError(str(exc)) from exc
    data = safe["data"]
    return {
        "contract_version": X1_WALLET_RELATIONSHIP_CONTRACT,
        "product": "x1_wallet_relationship_intelligence",
        "chain": "x1",
        "status": "ok",
        "cmis_contract_version": CMIS_WALLET_RELATIONSHIP_CONTRACT,
        "wallet_relationship_intelligence": deepcopy(data),
        "observed_at": safe.get("observed_at"),
        "confidence": deepcopy(safe.get("confidence") or {}),
        "sources": deepcopy(safe.get("sources") or []),
        "warnings": deepcopy(safe.get("warnings") or []),
        "errors": deepcopy(safe.get("errors") or []),
        "relationship_scope_is_one_selected_finalized_transaction": True,
        "common_ownership_claim_authorized": False,
        "beneficial_ownership_claim_authorized": False,
        "real_world_identity_claim_authorized": False,
        "whale_insider_bot_market_maker_claim_authorized": False,
        "behavior_or_intent_claim_authorized": False,
        "coordination_manipulation_fraud_claim_authorized": False,
        "causality_claim_authorized": False,
        "risk_severity_claim_authorized": False,
        "complete_wallet_history_claim_authorized": False,
        "complete_relationship_graph_claim_authorized": False,
        "execution_authorized": False,
    }


def render_x1_wallet_relationship_text(product: Mapping[str, Any]) -> str:
    if product.get("contract_version") != X1_WALLET_RELATIONSHIP_CONTRACT:
        raise X1WalletRelationshipContractError("wallet relationship Scout contract mismatch")
    data = product.get("wallet_relationship_intelligence")
    if not isinstance(data, Mapping):
        raise X1WalletRelationshipContractError("wallet relationship Scout data missing")
    return (
        "CMIS verified a direct X1 token transfer from "
        f"{data['sender_wallet']} to {data['recipient_wallet']} for mint "
        f"{data['asset_mint']} in transaction {data['transaction_signature']} at "
        f"{data['observed_at']}. This verifies this selected finalized transfer only; "
        "it does not prove common ownership, real-world identity, behavior, intent, "
        "coordination, manipulation, fraud, causality, risk severity, or complete wallet history."
    )


__all__ = [
    "CMIS_WALLET_RELATIONSHIP_CONTRACT",
    "X1_WALLET_RELATIONSHIP_CONTRACT",
    "X1WalletRelationshipContractError",
    "build_x1_wallet_relationship_intelligence",
    "render_x1_wallet_relationship_text",
]
