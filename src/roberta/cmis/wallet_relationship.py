"""ROBERTA-side contract for CMIS Wallet Relationship Intelligence v1.

Only exact caller selectors cross the Scout -> CMIS boundary. The validator
preserves one CMIS-proven finalized X1 direct token transfer and fails closed on
ownership, behavior, intent, risk, causality, completeness, or execution drift.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import re
from typing import Any

SERVICE = "wallet_relationship_intelligence"
SERVICE_CONTRACT_VERSION = "wallet_relationship_intelligence/v1"
REQUEST_CONTRACT_VERSION = "wallet_relationship_intelligence_request/v1"
RELATIONSHIP_KIND = "observed_direct_interaction"
INTERACTION_TYPE = "verified_token_transfer"
EVIDENCE_SCOPE = "exact_finalized_x1_transaction"

_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_INDEX = {char: index for index, char in enumerate(_BASE58_ALPHABET)}
_WR_ID = re.compile(r"^wr_[0-9a-f]{64}$")
_WA_ID = re.compile(r"^wa_[0-9a-f]{64}$")
_REQUIRED_LIMITATIONS = frozenset({
    "observed_direct_interaction_only",
    "ownership_not_inferred",
    "beneficial_ownership_not_inferred",
    "behavior_intent_and_risk_not_inferred",
    "complete_wallet_history_not_proven",
    "complete_relationship_graph_not_proven",
    "missing_amounts_are_not_zero_filled",
})


class CMISWalletRelationshipContractError(ValueError):
    """Raised when CMIS wallet-relationship material widens accepted authority."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise CMISWalletRelationshipContractError(f"{field} must be normalized non-empty text")
    return value


def _decode_base58(value: str) -> bytes | None:
    number = 0
    for char in value:
        digit = _BASE58_INDEX.get(char)
        if digit is None:
            return None
        number = number * 58 + digit
    leading_zeroes = len(value) - len(value.lstrip("1"))
    payload = b"" if number == 0 else number.to_bytes((number.bit_length() + 7) // 8, "big")
    return (b"\x00" * leading_zeroes) + payload


def _pubkey(value: Any, field: str) -> str:
    text = _text(value, field)
    decoded = _decode_base58(text)
    if decoded is None or len(decoded) != 32:
        raise CMISWalletRelationshipContractError(f"{field} must be an exact 32-byte base58 X1 public key")
    return text


def _signature(value: Any) -> str:
    text = _text(value, "transaction_signature")
    decoded = _decode_base58(text)
    if decoded is None or len(decoded) != 64:
        raise CMISWalletRelationshipContractError(
            "transaction_signature must be an exact 64-byte base58 transaction signature"
        )
    return text


def normalize_wallet_relationship_request(
    *,
    chain: str,
    transaction_signature: Any,
    asset_mint: Any,
    sender_wallet: Any,
    recipient_wallet: Any,
) -> dict[str, str]:
    normalized_chain = _text(chain, "chain").lower()
    if normalized_chain != "x1":
        raise CMISWalletRelationshipContractError("wallet relationship request must use chain=x1")
    sender = _pubkey(sender_wallet, "sender_wallet")
    recipient = _pubkey(recipient_wallet, "recipient_wallet")
    if sender == recipient:
        raise CMISWalletRelationshipContractError("sender_wallet and recipient_wallet must be distinct")
    return {
        "contract_version": REQUEST_CONTRACT_VERSION,
        "chain": "x1",
        "transaction_signature": _signature(transaction_signature),
        "asset_mint": _pubkey(asset_mint, "asset_mint"),
        "sender_wallet": sender,
        "recipient_wallet": recipient,
    }


def validate_wallet_relationship_response(
    response: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CMISWalletRelationshipContractError("CMIS wallet relationship response must be an object")
    safe = deepcopy(dict(response))
    if safe.get("service") != SERVICE or safe.get("chain") != "x1":
        raise CMISWalletRelationshipContractError("wallet relationship service/chain mismatch")
    if safe.get("status") != "ok":
        raise CMISWalletRelationshipContractError("promoted wallet relationship response requires status=ok")
    if safe.get("risk") is not None:
        raise CMISWalletRelationshipContractError("wallet relationship response must not add risk")
    if safe.get("execution_authorized") is not False:
        raise CMISWalletRelationshipContractError("wallet relationship response must preserve execution_authorized=false")

    expected = normalize_wallet_relationship_request(
        chain=expected_request.get("chain", "x1"),
        transaction_signature=expected_request.get("transaction_signature"),
        asset_mint=expected_request.get("asset_mint"),
        sender_wallet=expected_request.get("sender_wallet"),
        recipient_wallet=expected_request.get("recipient_wallet"),
    )
    asset = safe.get("asset")
    if not isinstance(asset, Mapping) or asset.get("id") != expected["asset_mint"] or asset.get("id_kind") != "mint":
        raise CMISWalletRelationshipContractError("wallet relationship exact asset identity mismatch")
    data = safe.get("data")
    if not isinstance(data, Mapping):
        raise CMISWalletRelationshipContractError("wallet relationship data must be an object")
    if data.get("contract_version") != SERVICE_CONTRACT_VERSION:
        raise CMISWalletRelationshipContractError("wallet relationship service contract mismatch")
    exact_fields = {
        "relationship_kind": RELATIONSHIP_KIND,
        "interaction_type": INTERACTION_TYPE,
        "asset_mint": expected["asset_mint"],
        "sender_wallet": expected["sender_wallet"],
        "recipient_wallet": expected["recipient_wallet"],
        "transaction_signature": expected["transaction_signature"],
        "evidence_scope": EVIDENCE_SCOPE,
    }
    for field, value in exact_fields.items():
        if data.get(field) != value:
            raise CMISWalletRelationshipContractError(f"wallet relationship {field} mismatch")
    if data.get("observed_at") != safe.get("observed_at"):
        raise CMISWalletRelationshipContractError("wallet relationship fact time mismatch")
    block_slot = data.get("block_slot")
    if block_slot is not None and (isinstance(block_slot, bool) or not isinstance(block_slot, int) or block_slot < 0):
        raise CMISWalletRelationshipContractError("block_slot must be a non-negative integer or null")
    amount_raw = data.get("amount_raw")
    if not isinstance(amount_raw, str) or not amount_raw.isdigit() or int(amount_raw) <= 0 or str(int(amount_raw)) != amount_raw:
        raise CMISWalletRelationshipContractError("amount_raw must be a positive canonical raw integer string")
    decimals = data.get("decimals")
    if isinstance(decimals, bool) or not isinstance(decimals, int) or decimals < 0:
        raise CMISWalletRelationshipContractError("decimals must be a non-negative integer")
    for field in ("source_token_account", "destination_token_account"):
        _text(data.get(field), field)
    relationship_id = data.get("relationship_evidence_id")
    observation_id = data.get("wallet_activity_observation_id")
    if not isinstance(relationship_id, str) or _WR_ID.fullmatch(relationship_id) is None:
        raise CMISWalletRelationshipContractError("relationship_evidence_id must be canonical wr_ content id")
    if not isinstance(observation_id, str) or _WA_ID.fullmatch(observation_id) is None:
        raise CMISWalletRelationshipContractError("wallet_activity_observation_id must be canonical wa_ content id")
    for field in (
        "evidence_receipt_binding_available",
        "proof_score_binding_available",
        "ownership_inference_added",
        "beneficial_ownership_inference_added",
        "behavioral_interpretation_added",
        "intent_interpretation_added",
        "complete_history_claimed",
        "complete_graph_coverage_claimed",
        "execution_authorized",
    ):
        if data.get(field) is not False:
            raise CMISWalletRelationshipContractError(f"wallet relationship {field} must remain false")
    if data.get("proof_strength_separate_from_risk") is not True:
        raise CMISWalletRelationshipContractError("Proof Score must remain separate from risk")
    if data.get("risk_interpretation") is not None:
        raise CMISWalletRelationshipContractError("wallet relationship risk_interpretation must remain null")
    limitations = data.get("limitations")
    if not isinstance(limitations, list) or not _REQUIRED_LIMITATIONS.issubset(set(limitations)):
        raise CMISWalletRelationshipContractError("wallet relationship truth-boundary limitations are incomplete")
    confidence = safe.get("confidence")
    if not isinstance(confidence, Mapping) or confidence.get("proof_score_available") is not False:
        raise CMISWalletRelationshipContractError("wallet relationship v1 must not invent Proof Score")
    return safe


__all__ = [
    "CMISWalletRelationshipContractError",
    "EVIDENCE_SCOPE",
    "INTERACTION_TYPE",
    "RELATIONSHIP_KIND",
    "REQUEST_CONTRACT_VERSION",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "normalize_wallet_relationship_request",
    "validate_wallet_relationship_response",
]
