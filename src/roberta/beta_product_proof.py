"""Privacy-safe public-beta product proof records for ROBERTA.

This module observes accepted final/evaluation structures only. It never changes
ROBERTA facts, judgment, evidence state, routing, or execution authority.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

BETA_PRODUCT_PROOF_VERSION = "roberta_beta_product_proof/v1"
AUTO_OUTCOME_TYPE = "automatic_response_outcome"
USER_FEEDBACK_TYPE = "explicit_user_feedback"
BETA_PATH_ENV = "ROBERTA_BETA_PRODUCT_PROOF_PATH"

_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_WORKFLOW_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,96}$")
_ALLOWED_DEPTHS = {"quick", "normal", "deep_dive", "unknown"}
_ALLOWED_EVIDENCE = {"HIGH", "MEDIUM", "LOW", "UNKNOWN", "UNAVAILABLE"}
_ALLOWED_CLARITY = {"clear", "too_technical", "confusing", "missing_evidence"}
_ALLOWED_WTP = {"no", "maybe", "yes"}
_ALLOWED_INTEREST = {"end_user", "developer_api", "both", "unknown"}
_FORBIDDEN_KEYS = {
    "message",
    "prompt",
    "response",
    "reply",
    "response_text",
    "prompt_text",
    "wallet",
    "wallet_address",
    "token_address",
    "address",
    "transaction_hash",
    "tx_hash",
    "raw_provider_json",
    "raw_evidence",
    "tool_arguments",
    "tool_args",
}


class BetaProductProofError(ValueError):
    """Raised when a beta record would widen the privacy or authority boundary."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def new_response_id() -> str:
    return uuid4().hex


def _response_id(value: object | None) -> str:
    result = new_response_id() if value is None else str(value).strip().lower()
    if not _ID_RE.fullmatch(result):
        raise BetaProductProofError("response_id must be a 32-character lowercase hex id")
    return result


def _required_feedback_response_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BetaProductProofError("response_id is required for beta feedback")
    return _response_id(value)


def _duration_bucket(duration_ms: object) -> str:
    if isinstance(duration_ms, bool) or not isinstance(duration_ms, (int, float)):
        raise BetaProductProofError("duration_ms must be a non-negative number")
    value = float(duration_ms)
    if value < 0:
        raise BetaProductProofError("duration_ms must be a non-negative number")
    if value < 2_000:
        return "lt_2s"
    if value < 5_000:
        return "2_5s"
    if value < 15_000:
        return "5_15s"
    if value < 30_000:
        return "15_30s"
    return "gte_30s"


def _decision_from_telemetry(telemetry: Mapping[str, Any]) -> Mapping[str, Any] | None:
    evidence = telemetry.get("evaluation_evidence")
    if not isinstance(evidence, Mapping):
        return None
    decision = evidence.get("human_response_decision")
    return decision if isinstance(decision, Mapping) else None


def _workflow(value: object) -> str:
    result = str(value or "unknown").strip() or "unknown"
    if not _WORKFLOW_RE.fullmatch(result):
        return "unknown"
    return result


def _evidence_quality(value: object) -> str:
    result = str(value or "UNKNOWN").strip().upper() or "UNKNOWN"
    return result if result in _ALLOWED_EVIDENCE else "UNKNOWN"


def _response_depth(value: object) -> str:
    result = str(value or "unknown").strip().lower() or "unknown"
    return result if result in _ALLOWED_DEPTHS else "unknown"


def _forbidden_key_scan(value: object, *, path: str = "record") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized = str(key).strip().lower()
            if normalized in _FORBIDDEN_KEYS:
                raise BetaProductProofError(f"forbidden beta field at {path}.{key}")
            _forbidden_key_scan(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _forbidden_key_scan(item, path=f"{path}[{index}]")


def build_automatic_outcome(
    telemetry: Mapping[str, Any],
    *,
    duration_ms: int | float,
    response_id: str | None = None,
    timestamp: str | None = None,
) -> dict[str, object]:
    """Derive a coarse product record from accepted evaluation telemetry."""

    if not isinstance(telemetry, Mapping):
        raise BetaProductProofError("telemetry must be a mapping")
    if telemetry.get("execution_authorized") is True:
        raise BetaProductProofError("beta observation cannot accept execution_authorized=true")

    decision = _decision_from_telemetry(telemetry)
    if decision is None:
        workflow = "unknown"
        depth = "unknown"
        evidence_quality = "UNAVAILABLE"
        unknown_count = 0
        outcome = "unavailable"
    else:
        if decision.get("execution_authorized") is True:
            raise BetaProductProofError("decision execution_authorized must remain false")
        workflow = _workflow(decision.get("workflow"))
        depth = _response_depth(decision.get("response_depth"))
        evidence_quality = _evidence_quality(decision.get("evidence_quality"))
        unknowns = decision.get("important_unknowns")
        unknown_count = min(len(unknowns), 99) if isinstance(unknowns, list) else 0
        outcome = "evidence_required" if unknown_count else "success"

    claims = telemetry.get("claims")
    claim_count = min(len(claims), 99) if isinstance(claims, list) else 0
    provenance = telemetry.get("evidence_provenance")
    source_contracts = provenance.get("source_contracts") if isinstance(provenance, Mapping) else None
    source_contract_count = min(len(source_contracts), 99) if isinstance(source_contracts, list) else 0

    record: dict[str, object] = {
        "contract_version": BETA_PRODUCT_PROOF_VERSION,
        "record_type": AUTO_OUTCOME_TYPE,
        "response_id": _response_id(response_id),
        "timestamp": str(timestamp or _now_iso()),
        "workflow": workflow,
        "outcome": outcome,
        "response_depth": depth,
        "evidence_quality": evidence_quality,
        "explicit_unknown_count": unknown_count,
        "claim_count": claim_count,
        "source_contract_count": source_contract_count,
        "duration_bucket": _duration_bucket(duration_ms),
        "execution_authorized": False,
        "content_persisted": False,
    }
    return validate_beta_record(record)


def build_user_feedback(
    *,
    response_id: str,
    helpful: bool,
    clarity: str,
    evidence_drill_down: bool = False,
    would_use_again: bool | None = None,
    willingness_to_pay: str | None = None,
    interest_surface: str | None = None,
    timestamp: str | None = None,
) -> dict[str, object]:
    joined_response_id = _required_feedback_response_id(response_id)
    clarity_value = str(clarity).strip().lower()
    if clarity_value not in _ALLOWED_CLARITY:
        raise BetaProductProofError("unsupported clarity feedback")
    wtp = None if willingness_to_pay is None else str(willingness_to_pay).strip().lower()
    if wtp is not None and wtp not in _ALLOWED_WTP:
        raise BetaProductProofError("unsupported willingness_to_pay value")
    interest = None if interest_surface is None else str(interest_surface).strip().lower()
    if interest is not None and interest not in _ALLOWED_INTEREST:
        raise BetaProductProofError("unsupported interest_surface value")
    if not isinstance(helpful, bool) or not isinstance(evidence_drill_down, bool):
        raise BetaProductProofError("feedback booleans must be bool values")
    if would_use_again is not None and not isinstance(would_use_again, bool):
        raise BetaProductProofError("would_use_again must be bool or null")

    record: dict[str, object] = {
        "contract_version": BETA_PRODUCT_PROOF_VERSION,
        "record_type": USER_FEEDBACK_TYPE,
        "response_id": joined_response_id,
        "timestamp": str(timestamp or _now_iso()),
        "helpful": helpful,
        "clarity": clarity_value,
        "evidence_drill_down": evidence_drill_down,
        "would_use_again": would_use_again,
        "willingness_to_pay": wtp,
        "interest_surface": interest,
        "execution_authorized": False,
        "content_persisted": False,
    }
    return validate_beta_record(record)


def validate_beta_record(record: Mapping[str, Any]) -> dict[str, object]:
    if not isinstance(record, Mapping):
        raise BetaProductProofError("beta record must be a mapping")
    _forbidden_key_scan(record)
    if record.get("contract_version") != BETA_PRODUCT_PROOF_VERSION:
        raise BetaProductProofError("unsupported beta product proof contract")
    if record.get("execution_authorized") is not False:
        raise BetaProductProofError("execution_authorized must be false")
    if record.get("content_persisted") is not False:
        raise BetaProductProofError("content_persisted must be false")
    _response_id(record.get("response_id"))

    record_type = record.get("record_type")
    auto_keys = {
        "contract_version", "record_type", "response_id", "timestamp", "workflow",
        "outcome", "response_depth", "evidence_quality", "explicit_unknown_count",
        "claim_count", "source_contract_count", "duration_bucket",
        "execution_authorized", "content_persisted",
    }
    feedback_keys = {
        "contract_version", "record_type", "response_id", "timestamp", "helpful",
        "clarity", "evidence_drill_down", "would_use_again", "willingness_to_pay",
        "interest_surface", "execution_authorized", "content_persisted",
    }
    expected = auto_keys if record_type == AUTO_OUTCOME_TYPE else feedback_keys if record_type == USER_FEEDBACK_TYPE else None
    if expected is None:
        raise BetaProductProofError("unsupported beta record_type")
    if set(record) != expected:
        raise BetaProductProofError("beta record schema drift")
    return dict(record)


def configured_beta_path() -> Path | None:
    value = os.getenv(BETA_PATH_ENV, "").strip()
    return Path(value).expanduser() if value else None


def append_beta_record(record: Mapping[str, Any], *, path: str | Path | None = None) -> bool:
    """Append one validated JSONL record. Disabled when no path is configured."""

    validated = validate_beta_record(record)
    destination = Path(path).expanduser() if path is not None else configured_beta_path()
    if destination is None:
        return False
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(validated, separators=(",", ":"), ensure_ascii=False, allow_nan=False))
        handle.write("\n")
    return True


__all__ = [
    "AUTO_OUTCOME_TYPE",
    "BETA_PATH_ENV",
    "BETA_PRODUCT_PROOF_VERSION",
    "BetaProductProofError",
    "USER_FEEDBACK_TYPE",
    "append_beta_record",
    "build_automatic_outcome",
    "build_user_feedback",
    "configured_beta_path",
    "new_response_id",
    "validate_beta_record",
]
