"""Typed, fail-closed human-approval contracts for Roberta."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Literal, Mapping

ApprovalDecisionType = Literal[
    "approve",
    "reject",
    "edit",
    "request_more_evidence",
]
ApprovalStatus = Literal[
    "approved",
    "rejected",
    "edited",
    "more_evidence",
]

_DECISIONS = frozenset({"approve", "reject", "edit", "request_more_evidence"})
_STATUSES = frozenset({"approved", "rejected", "edited", "more_evidence"})
_SECRET_KEY_MARKERS = frozenset(
    {
        "api_key",
        "credential",
        "credentials",
        "encryption_key",
        "keypair",
        "mnemonic",
        "password",
        "private_key",
        "secret",
        "seed",
        "seed_phrase",
        "signing_key",
    }
)
_ALLOWED_RESUME_KEYS = frozenset(
    {
        "request_id",
        "proposal_sha256",
        "binding_sha256",
        "decision",
        "feedback",
        "edited_proposal",
    }
)


def _normalized_key(value: object) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", str(value)).strip("_").lower()


def _looks_secret_bearing(normalized: str) -> bool:
    padded = f"_{normalized}_"
    return any(f"_{marker}_" in padded for marker in _SECRET_KEY_MARKERS)


def _assert_no_secret_fields(value: Any, *, path: str = "payload") -> None:
    """Reject common secret-bearing key names from checkpoint/interrupt payloads."""

    if isinstance(value, Mapping):
        for key, nested in value.items():
            normalized = _normalized_key(key)
            if _looks_secret_bearing(normalized):
                raise ValueError(f"secret-bearing field is not allowed at {path}.{key}")
            _assert_no_secret_fields(nested, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _assert_no_secret_fields(nested, path=f"{path}[{index}]")


def _freeze_json(value: Any, *, path: str = "payload") -> Any:
    """Recursively freeze JSON data so an approved proposal cannot mutate in place."""

    if isinstance(value, Mapping):
        frozen: dict[str, Any] = {}
        for key, nested in value.items():
            if not isinstance(key, str) or not key:
                raise ValueError(f"JSON object keys must be non-empty strings at {path}")
            frozen[key] = _freeze_json(nested, path=f"{path}.{key}")
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(
            _freeze_json(nested, path=f"{path}[{index}]")
            for index, nested in enumerate(value)
        )
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValueError(f"approval payload contains non-JSON value at {path}")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(nested) for key, nested in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(nested) for nested in value]
    return value


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            _thaw_json(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("approval payload must be JSON-serializable") from exc


def _validate_sha256(value: object, *, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in "0123456789abcdef" for ch in value.lower())
    ):
        raise ValueError(f"{field} must be a 64-character hex digest")
    return value.lower()


def canonical_proposal_sha256(proposal: Mapping[str, Any]) -> str:
    """Hash the exact canonical proposal that an approval decision is bound to."""

    if not isinstance(proposal, Mapping):
        raise TypeError("proposal must be a mapping")
    if not proposal:
        raise ValueError("proposal must not be empty")
    _assert_no_secret_fields(proposal, path="proposal")
    frozen = _freeze_json(proposal, path="proposal")
    return hashlib.sha256(_canonical_json(frozen).encode("utf-8")).hexdigest()


def canonical_approval_binding_sha256(
    *,
    request_id: str,
    action_type: str,
    scope: tuple[str, ...],
    proposal_sha256: str,
) -> str:
    """Bind approval to exact request identity, action class, scope, and proposal."""

    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be non-empty for approval binding")
    if not isinstance(action_type, str) or not action_type.strip():
        raise ValueError("action_type must be non-empty for approval binding")
    if not isinstance(scope, tuple) or not scope:
        raise ValueError("scope must be non-empty for approval binding")
    digest = _validate_sha256(proposal_sha256, field="proposal_sha256")
    payload = {
        "request_id": request_id,
        "action_type": action_type,
        "scope": list(scope),
        "proposal_sha256": digest,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class ApprovalRequest:
    """One exact consequential proposal requiring explicit human review."""

    request_id: str
    action_type: str
    summary: str
    scope: tuple[str, ...]
    proposal: Mapping[str, Any]
    policy_reasons: tuple[str, ...] = ()
    evidence_summary: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("request_id", self.request_id),
            ("action_type", self.action_type),
            ("summary", self.summary),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.scope, tuple) or not self.scope:
            raise ValueError("approval scope must be a non-empty tuple")
        if any(not isinstance(item, str) or not item.strip() for item in self.scope):
            raise ValueError("approval scope values must be non-empty strings")
        if len(set(self.scope)) != len(self.scope):
            raise ValueError("approval scope values must be unique")
        if not isinstance(self.proposal, Mapping):
            raise TypeError("approval proposal must be a mapping")
        if not self.proposal:
            raise ValueError("approval proposal must not be empty")
        for name, values in (
            ("policy_reasons", self.policy_reasons),
            ("evidence_summary", self.evidence_summary),
        ):
            if not isinstance(values, tuple):
                raise TypeError(f"{name} must be a tuple")
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise ValueError(f"{name} values must be non-empty strings")
        _assert_no_secret_fields(self.proposal, path="proposal")
        object.__setattr__(self, "proposal", _freeze_json(self.proposal, path="proposal"))
        _canonical_json(self.to_state_payload())

    @property
    def proposal_sha256(self) -> str:
        return canonical_proposal_sha256(self.proposal)

    @property
    def binding_sha256(self) -> str:
        return canonical_approval_binding_sha256(
            request_id=self.request_id,
            action_type=self.action_type,
            scope=self.scope,
            proposal_sha256=self.proposal_sha256,
        )

    def to_state_payload(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "action_type": self.action_type,
            "summary": self.summary,
            "scope": list(self.scope),
            "proposal": _thaw_json(self.proposal),
            "policy_reasons": list(self.policy_reasons),
            "evidence_summary": list(self.evidence_summary),
        }

    def to_interrupt_payload(self) -> dict[str, Any]:
        return {
            "schema": "roberta.approval-request",
            "version": 1,
            "request_id": self.request_id,
            "action_type": self.action_type,
            "summary": self.summary,
            "scope": list(self.scope),
            "proposal": _thaw_json(self.proposal),
            "proposal_sha256": self.proposal_sha256,
            "binding_sha256": self.binding_sha256,
            "policy_reasons": list(self.policy_reasons),
            "evidence_summary": list(self.evidence_summary),
            "allowed_decisions": [
                "approve",
                "reject",
                "edit",
                "request_more_evidence",
            ],
        }

    @classmethod
    def from_state_payload(cls, payload: Mapping[str, Any]) -> "ApprovalRequest":
        if not isinstance(payload, Mapping):
            raise TypeError("approval request state must be a mapping")
        return cls(
            request_id=payload.get("request_id"),
            action_type=payload.get("action_type"),
            summary=payload.get("summary"),
            scope=tuple(payload.get("scope") or ()),
            proposal=payload.get("proposal") or {},
            policy_reasons=tuple(payload.get("policy_reasons") or ()),
            evidence_summary=tuple(payload.get("evidence_summary") or ()),
        )


@dataclass(frozen=True, slots=True)
class ApprovalDecision:
    """Validated human response bound to one exact approval request."""

    request_id: str
    proposal_sha256: str
    binding_sha256: str
    decision: ApprovalDecisionType
    feedback: str | None = None
    edited_proposal: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise ValueError("approval decision request_id must be non-empty")
        object.__setattr__(
            self,
            "proposal_sha256",
            _validate_sha256(self.proposal_sha256, field="proposal_sha256"),
        )
        object.__setattr__(
            self,
            "binding_sha256",
            _validate_sha256(self.binding_sha256, field="binding_sha256"),
        )
        if self.decision not in _DECISIONS:
            raise ValueError(f"unsupported approval decision: {self.decision!r}")
        if self.feedback is not None and (
            not isinstance(self.feedback, str) or not self.feedback.strip()
        ):
            raise ValueError("feedback must be None or a non-empty string")
        if self.decision == "edit":
            if not isinstance(self.edited_proposal, Mapping):
                raise ValueError("edit decision requires edited_proposal mapping")
            canonical_proposal_sha256(self.edited_proposal)
            object.__setattr__(
                self,
                "edited_proposal",
                _freeze_json(self.edited_proposal, path="edited_proposal"),
            )
        elif self.edited_proposal is not None:
            raise ValueError("edited_proposal is only valid for an edit decision")

    @classmethod
    def from_resume(cls, value: Any, *, request: ApprovalRequest) -> "ApprovalDecision":
        if not isinstance(value, Mapping):
            raise ValueError("approval resume value must be an explicit mapping")
        unknown = set(value) - _ALLOWED_RESUME_KEYS
        if unknown:
            raise ValueError(f"approval resume value contains unknown fields: {sorted(unknown)}")
        decision = cls(
            request_id=value.get("request_id"),
            proposal_sha256=value.get("proposal_sha256"),
            binding_sha256=value.get("binding_sha256"),
            decision=value.get("decision"),
            feedback=value.get("feedback"),
            edited_proposal=value.get("edited_proposal"),
        )
        if decision.request_id != request.request_id:
            raise ValueError("approval request_id does not match the paused request")
        if decision.proposal_sha256 != request.proposal_sha256:
            raise ValueError("approval proposal hash does not match the paused proposal")
        if decision.binding_sha256 != request.binding_sha256:
            raise ValueError("approval binding hash does not match the paused request scope")
        return decision


@dataclass(frozen=True, slots=True)
class ApprovalOutcome:
    """Deterministic result after validating one human review response."""

    status: ApprovalStatus
    request_id: str
    original_proposal_sha256: str
    approval_binding_sha256: str
    reviewed_proposal: Mapping[str, Any]
    reviewed_proposal_sha256: str
    scope: tuple[str, ...]
    feedback: str | None = None

    def __post_init__(self) -> None:
        if self.status not in _STATUSES:
            raise ValueError(f"unsupported approval outcome status: {self.status!r}")
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise ValueError("approval outcome request_id must be non-empty")
        original = _validate_sha256(
            self.original_proposal_sha256,
            field="original_proposal_sha256",
        )
        binding = _validate_sha256(
            self.approval_binding_sha256,
            field="approval_binding_sha256",
        )
        reviewed_hash = _validate_sha256(
            self.reviewed_proposal_sha256,
            field="reviewed_proposal_sha256",
        )
        if not isinstance(self.reviewed_proposal, Mapping) or not self.reviewed_proposal:
            raise ValueError("reviewed_proposal must be a non-empty mapping")
        frozen = _freeze_json(self.reviewed_proposal, path="reviewed_proposal")
        if canonical_proposal_sha256(frozen) != reviewed_hash:
            raise ValueError("reviewed proposal hash does not match reviewed proposal")
        object.__setattr__(self, "original_proposal_sha256", original)
        object.__setattr__(self, "approval_binding_sha256", binding)
        object.__setattr__(self, "reviewed_proposal_sha256", reviewed_hash)
        object.__setattr__(self, "reviewed_proposal", frozen)

    def to_state_payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "request_id": self.request_id,
            "original_proposal_sha256": self.original_proposal_sha256,
            "approval_binding_sha256": self.approval_binding_sha256,
            "reviewed_proposal": _thaw_json(self.reviewed_proposal),
            "reviewed_proposal_sha256": self.reviewed_proposal_sha256,
            "scope": list(self.scope),
            "feedback": self.feedback,
        }


def resolve_approval_decision(
    request: ApprovalRequest,
    decision: ApprovalDecision,
) -> ApprovalOutcome:
    """Resolve a validated decision without performing any consequential action."""

    if decision.request_id != request.request_id:
        raise ValueError("approval decision is not bound to this request")
    if decision.proposal_sha256 != request.proposal_sha256:
        raise ValueError("approval decision is not bound to this proposal")
    if decision.binding_sha256 != request.binding_sha256:
        raise ValueError("approval decision is not bound to this request scope")

    if decision.decision == "approve":
        status: ApprovalStatus = "approved"
        reviewed = request.proposal
    elif decision.decision == "reject":
        status = "rejected"
        reviewed = request.proposal
    elif decision.decision == "request_more_evidence":
        status = "more_evidence"
        reviewed = request.proposal
    else:
        status = "edited"
        assert decision.edited_proposal is not None
        reviewed = decision.edited_proposal

    return ApprovalOutcome(
        status=status,
        request_id=request.request_id,
        original_proposal_sha256=request.proposal_sha256,
        approval_binding_sha256=request.binding_sha256,
        reviewed_proposal=reviewed,
        reviewed_proposal_sha256=canonical_proposal_sha256(reviewed),
        scope=request.scope,
        feedback=decision.feedback,
    )
