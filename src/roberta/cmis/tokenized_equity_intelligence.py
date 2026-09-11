"""ROBERTA-side contract for promoted CMIS Tokenized Equity Intelligence v1.

This layer accepts only exact selectors and validates the promoted CMIS service
without widening its authority. Missing components remain explicit evidence
gaps; protected evidence receipts and Proof Score are preserved when supplied
but are never converted into risk, ownership, legal, adoption, or execution
claims here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import re
from typing import Any

SERVICE = "tokenized_equity_intelligence"
SERVICE_CONTRACT_VERSION = "tokenized_equity_intelligence/v1"
REQUEST_CONTRACT_VERSION = "tokenized_equity_intelligence_request/v1"
MATERIALIZATION_CONTRACT_VERSION = "tokenized_equity_intelligence_materialization/v1"
EVIDENCE_QUALITY_CONTRACT_VERSION = "tokenized_equity_evidence_quality/v1"
RESPONSE_FRESHNESS_CONTRACT_VERSION = "cmis_response_freshness/v1"

SUPPORTED_COMPONENTS = ("provenance", "cross_chain", "rights", "market_activity")
COMPONENT_CONTRACTS = {
    "provenance": "tokenized_equity_provenance/v1",
    "cross_chain": "cross_chain_equity_provenance/v1",
    "rights": "tokenized_equity_rights/v1",
    "market_activity": "tokenized_equity_market_activity/v1",
}
SUBJECT_STATES = frozenset({"RESOLVED", "EVIDENCE_REQUIRED"})
COMPONENT_STATES = frozenset({"AVAILABLE", "EVIDENCE_REQUIRED", "UNAVAILABLE", "ERROR"})
ALLOWED_SECURITY_ID_KINDS = frozenset(
    {"isin", "cusip", "sedol", "figi", "issuer_security_id", "registry_security_id"}
)
_ALLOWED_FRESHNESS_STATES = frozenset(
    {"VERIFIED", "PARTIAL", "NOT_VERIFIED", "UNKNOWN", "STALE", "NOT_APPLICABLE"}
)
_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
_BASE58_INDEX = {char: index for index, char in enumerate(_BASE58_ALPHABET)}
_MATERIALIZATION_ID_RE = re.compile(r"^tei_[0-9a-f]{64}$")


class CMISTokenizedEquityContractError(ValueError):
    """Raised when CMIS Tokenized Equity material widens accepted authority."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise CMISTokenizedEquityContractError(f"{field} must be normalized non-empty text")
    return value


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CMISTokenizedEquityContractError(f"{field} must be a mapping")
    return value


def _sequence(value: Any, field: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray, Mapping)):
        raise CMISTokenizedEquityContractError(f"{field} must be a list")
    return list(value)


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


def _x1_pubkey(value: Any, field: str) -> str:
    text = _text(value, field)
    decoded = _decode_base58(text)
    if decoded is None or len(decoded) != 32:
        raise CMISTokenizedEquityContractError(
            f"{field} must be an exact 32-byte base58 X1 public key"
        )
    return text


def normalize_tokenized_equity_intelligence_request(
    *,
    chain: str,
    asset_mint: Any,
    requested_components: Any,
    security_id: Any = None,
    security_id_kind: Any = None,
) -> dict[str, Any]:
    normalized_chain = _text(chain, "chain").casefold()
    if normalized_chain != "x1":
        raise CMISTokenizedEquityContractError("Tokenized Equity Intelligence requires chain=x1")

    mint = _x1_pubkey(asset_mint, "asset_mint")
    if (security_id is None) != (security_id_kind is None):
        raise CMISTokenizedEquityContractError(
            "security_id and security_id_kind must be supplied together"
        )
    normalized_security_id: str | None = None
    normalized_security_kind: str | None = None
    if security_id is not None:
        normalized_security_id = _text(security_id, "security_id")
        normalized_security_kind = _text(security_id_kind, "security_id_kind").casefold()
        if normalized_security_kind not in ALLOWED_SECURITY_ID_KINDS:
            raise CMISTokenizedEquityContractError(
                "security_id_kind must use an accepted exact security identifier"
            )

    raw_components = _sequence(requested_components, "requested_components")
    selected: set[str] = set()
    for index, raw in enumerate(raw_components):
        component = _text(raw, f"requested_components[{index}]").casefold()
        if component not in SUPPORTED_COMPONENTS:
            raise CMISTokenizedEquityContractError(
                f"unsupported requested component: {component}"
            )
        if component in selected:
            raise CMISTokenizedEquityContractError("requested_components must be unique")
        selected.add(component)
    if not selected:
        raise CMISTokenizedEquityContractError("requested_components must not be empty")
    if "provenance" not in selected:
        raise CMISTokenizedEquityContractError(
            "requested_components must include provenance as the identity foundation"
        )

    return {
        "contract_version": REQUEST_CONTRACT_VERSION,
        "chain": "x1",
        "asset_mint": mint,
        "security_id": normalized_security_id,
        "security_id_kind": normalized_security_kind,
        "requested_components": [name for name in SUPPORTED_COMPONENTS if name in selected],
    }


def _validate_response_freshness(value: Any, *, observed_at: Any) -> dict[str, Any]:
    freshness = deepcopy(dict(_mapping(value, "freshness")))
    if freshness.get("contract_version") != RESPONSE_FRESHNESS_CONTRACT_VERSION:
        raise CMISTokenizedEquityContractError("Tokenized Equity response freshness contract mismatch")
    if freshness.get("scope") != f"{SERVICE}.response":
        raise CMISTokenizedEquityContractError("Tokenized Equity response freshness scope mismatch")
    if freshness.get("state") not in _ALLOWED_FRESHNESS_STATES:
        raise CMISTokenizedEquityContractError("Tokenized Equity response freshness state invalid")
    verified = freshness.get("freshness_verified")
    if verified is not None and not isinstance(verified, bool):
        raise CMISTokenizedEquityContractError("freshness_verified must be boolean or null")
    if freshness.get("state") == "VERIFIED" and verified is not True:
        raise CMISTokenizedEquityContractError("VERIFIED freshness requires freshness_verified=true")
    if verified is True and freshness.get("state") != "VERIFIED":
        raise CMISTokenizedEquityContractError("freshness_verified=true requires state=VERIFIED")
    if freshness.get("observed_at") != observed_at:
        raise CMISTokenizedEquityContractError("freshness observed_at must equal response observed_at")
    if not isinstance(freshness.get("details"), Mapping):
        raise CMISTokenizedEquityContractError("freshness details must be a mapping")
    return freshness


def validate_tokenized_equity_intelligence_response(
    response: Mapping[str, Any],
    *,
    expected_request: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CMISTokenizedEquityContractError("CMIS Tokenized Equity response must be an object")
    safe = deepcopy(dict(response))
    if safe.get("service") != SERVICE or safe.get("chain") != "x1":
        raise CMISTokenizedEquityContractError("Tokenized Equity service/chain mismatch")
    if safe.get("status") not in {"ok", "partial"}:
        raise CMISTokenizedEquityContractError("promoted Tokenized Equity response requires status=ok|partial")
    if safe.get("risk") is not None:
        raise CMISTokenizedEquityContractError("Tokenized Equity projection must not add risk")
    for field in ("read_only", "public_service_promoted", "scout_reliance_promoted", "runtime_capability_promoted"):
        if safe.get(field) is not True:
            raise CMISTokenizedEquityContractError(f"Tokenized Equity {field} must be true")
    if safe.get("execution_authorized") is not False:
        raise CMISTokenizedEquityContractError("Tokenized Equity must preserve execution_authorized=false")

    expected = normalize_tokenized_equity_intelligence_request(
        chain=expected_request.get("chain", "x1"),
        asset_mint=expected_request.get("asset_mint"),
        security_id=expected_request.get("security_id"),
        security_id_kind=expected_request.get("security_id_kind"),
        requested_components=expected_request.get("requested_components"),
    )

    asset = _mapping(safe.get("asset"), "asset")
    if (
        asset.get("canonical_id") != expected["asset_mint"]
        or asset.get("asset_id") != expected["asset_mint"]
        or asset.get("asset_id_kind") != "mint"
    ):
        raise CMISTokenizedEquityContractError("Tokenized Equity exact asset identity mismatch")

    data = _mapping(safe.get("data"), "data")
    if data.get("contract_version") != SERVICE_CONTRACT_VERSION:
        raise CMISTokenizedEquityContractError("Tokenized Equity service contract mismatch")
    if data.get("request_contract_version") != REQUEST_CONTRACT_VERSION:
        raise CMISTokenizedEquityContractError("Tokenized Equity request contract mismatch")
    if data.get("materialization_contract_version") != MATERIALIZATION_CONTRACT_VERSION:
        raise CMISTokenizedEquityContractError("Tokenized Equity materialization contract mismatch")
    materialization_id = data.get("materialization_id")
    if not isinstance(materialization_id, str) or _MATERIALIZATION_ID_RE.fullmatch(materialization_id) is None:
        raise CMISTokenizedEquityContractError("materialization_id must be canonical tei_ SHA-256 identity")

    requested = _sequence(data.get("requested_components"), "data.requested_components")
    if requested != expected["requested_components"]:
        raise CMISTokenizedEquityContractError("requested_components must exactly match caller selectors")
    states = dict(_mapping(data.get("component_states"), "data.component_states"))
    if set(states) != set(requested):
        raise CMISTokenizedEquityContractError("component_states must exactly cover requested components")
    if any(state not in COMPONENT_STATES for state in states.values()):
        raise CMISTokenizedEquityContractError("component_states contains unsupported state")

    components = dict(_mapping(data.get("components"), "data.components"))
    available = {name for name, state in states.items() if state == "AVAILABLE"}
    if set(components) != available:
        raise CMISTokenizedEquityContractError("components must contain exactly AVAILABLE components")
    for name in available:
        component = _mapping(components[name], f"data.components.{name}")
        if component.get("contract") != COMPONENT_CONTRACTS[name]:
            raise CMISTokenizedEquityContractError(f"{name} component contract mismatch")
        if component.get("execution_authorized") is not False:
            raise CMISTokenizedEquityContractError(f"{name} component must preserve execution_authorized=false")

    subject_state = data.get("subject_resolution_state")
    if subject_state not in SUBJECT_STATES:
        raise CMISTokenizedEquityContractError("subject_resolution_state is invalid")
    resolved_subject = data.get("resolved_subject")
    evidence_quality = data.get("evidence_quality")
    if subject_state == "EVIDENCE_REQUIRED":
        if resolved_subject is not None or components:
            raise CMISTokenizedEquityContractError("unresolved subject cannot carry resolved subject/components")
        if any(state != "EVIDENCE_REQUIRED" for state in states.values()):
            raise CMISTokenizedEquityContractError("unresolved subject must keep every component EVIDENCE_REQUIRED")
        if evidence_quality is not None:
            raise CMISTokenizedEquityContractError("unresolved subject cannot carry evidence quality")
    else:
        if states.get("provenance") != "AVAILABLE":
            raise CMISTokenizedEquityContractError("resolved subject requires AVAILABLE provenance")
        subject = _mapping(resolved_subject, "data.resolved_subject")
        if subject.get("chain") != "x1" or subject.get("asset_mint") != expected["asset_mint"]:
            raise CMISTokenizedEquityContractError("resolved subject does not match exact X1 selector")
        if subject.get("asset_id_kind") != "mint":
            raise CMISTokenizedEquityContractError("resolved subject asset_id_kind must be mint")
        if expected["security_id"] is not None:
            if subject.get("security_id") != expected["security_id"] or subject.get("security_id_kind") != expected["security_id_kind"]:
                raise CMISTokenizedEquityContractError("resolved security identity does not match caller selector")
        quality = _mapping(evidence_quality, "data.evidence_quality")
        if quality.get("contract") != EVIDENCE_QUALITY_CONTRACT_VERSION:
            raise CMISTokenizedEquityContractError("Tokenized Equity evidence quality contract mismatch")
        if quality.get("execution_authorized") is not False:
            raise CMISTokenizedEquityContractError("evidence quality must preserve execution_authorized=false")

    complete = subject_state == "RESOLVED" and all(states[name] == "AVAILABLE" for name in requested)
    if safe.get("status") != ("ok" if complete else "partial"):
        raise CMISTokenizedEquityContractError("Tokenized Equity status does not match component coverage")

    required_false = (
        "live_x1_equity_deployment_verified",
        "live_robinhood_x1_route_verified",
        "rights_are_legal_adjudication",
        "liquidity_equals_volume",
        "transfer_equals_trade",
        "bridge_flow_equals_adoption",
        "reference_price_equals_executed_price",
        "execution_authorized",
    )
    for field in required_false:
        if data.get(field) is not False:
            raise CMISTokenizedEquityContractError(f"Tokenized Equity data.{field} must remain false")
    if data.get("proof_score_separate_from_risk") is not True:
        raise CMISTokenizedEquityContractError("Proof Score must remain separate from risk")
    for field in ("read_only", "public_service_promoted", "scout_reliance_promoted"):
        if data.get(field) is not True:
            raise CMISTokenizedEquityContractError(f"Tokenized Equity data.{field} must be true")

    confidence = _mapping(safe.get("confidence"), "confidence")
    if confidence.get("proof_score_owned_by_protected_runtime") is not True:
        raise CMISTokenizedEquityContractError("Proof Score ownership must remain protected-runtime-owned")
    if confidence.get("proof_score_separate_from_risk") is not True:
        raise CMISTokenizedEquityContractError("confidence must keep Proof Score separate from risk")
    if confidence.get("proof_score") is not None:
        raise CMISTokenizedEquityContractError("public confidence must not invent a Proof Score")
    if confidence.get("complete_requested_component_coverage") is not complete:
        raise CMISTokenizedEquityContractError("confidence coverage flag does not match component states")

    _validate_response_freshness(safe.get("freshness"), observed_at=safe.get("observed_at"))
    for field in ("sources", "warnings", "errors"):
        _sequence(safe.get(field), field)
    for field in ("evidence_receipt", "proof_score"):
        if field in safe and safe[field] is not None and not isinstance(safe[field], Mapping):
            raise CMISTokenizedEquityContractError(f"protected {field} must be a mapping when supplied")
    return safe


__all__ = [
    "ALLOWED_SECURITY_ID_KINDS",
    "CMISTokenizedEquityContractError",
    "COMPONENT_CONTRACTS",
    "COMPONENT_STATES",
    "EVIDENCE_QUALITY_CONTRACT_VERSION",
    "MATERIALIZATION_CONTRACT_VERSION",
    "REQUEST_CONTRACT_VERSION",
    "SERVICE",
    "SERVICE_CONTRACT_VERSION",
    "SUBJECT_STATES",
    "SUPPORTED_COMPONENTS",
    "normalize_tokenized_equity_intelligence_request",
    "validate_tokenized_equity_intelligence_response",
]
