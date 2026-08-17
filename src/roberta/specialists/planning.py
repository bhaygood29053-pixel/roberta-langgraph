"""Shared constrained planning helpers for chain-specialist Scouts.

Chain Scouts may ask an injected model which read-only CMIS investigations are
useful, but deterministic code remains authoritative for what can run. This
module is chain-neutral; chain-specific Scouts still own interpretation.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from roberta.cmis.contracts import CMISOperation

AUTONOMOUS_OPERATIONS: tuple[CMISOperation, ...] = (
    "market_report",
    "tokenomics",
    "risk_check",
)
MAX_PLAN_OPERATIONS = 3

_RISK_TERMS = (
    "risk",
    "risky",
    "safety",
    "safe",
    "danger",
    "rug",
)
_TOKENOMICS_TERMS = (
    "tokenomics",
    "supply",
    "mint authority",
    "freeze authority",
    "minting",
)


def _normalize_objective(objective: object) -> str:
    return " ".join(str(objective or "").strip().lower().split())


def required_operations(objective: object) -> list[CMISOperation]:
    """Return objective-required CMIS operations in stable priority order."""

    normalized = _normalize_objective(objective)
    required: list[CMISOperation] = []
    if any(term in normalized for term in _TOKENOMICS_TERMS):
        required.append("tokenomics")
    if any(term in normalized for term in _RISK_TERMS):
        required.append("risk_check")
    return required


def select_cmis_operation(objective: object) -> CMISOperation:
    """Return the deterministic single-operation fallback for an objective."""

    required = required_operations(objective)
    if "risk_check" in required:
        return "risk_check"
    if "tokenomics" in required:
        return "tokenomics"
    return "market_report"


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def parse_plan_proposal(value: Any) -> dict[str, list[str]]:
    """Parse an untrusted planner response into the narrow operation proposal."""

    if isinstance(value, Mapping):
        payload: Any = value
    else:
        content = getattr(value, "content", value)
        if not isinstance(content, str):
            raise ValueError("chain Scout planner response must contain JSON text")
        payload = json.loads(_strip_markdown_fence(content))

    if not isinstance(payload, Mapping):
        raise ValueError("chain Scout planner response must be a JSON object")
    operations = payload.get("operations")
    if not isinstance(operations, list):
        raise ValueError("chain Scout planner response must contain an operations list")

    return {
        "operations": [
            operation.strip()
            for operation in operations
            if isinstance(operation, str) and operation.strip()
        ]
    }


def propose_plan(
    planner_model: Any,
    *,
    chain: str,
    asset: str,
    objective: str,
) -> dict[str, list[str]]:
    """Ask an injected planner for a bounded read-only CMIS proposal."""

    if not hasattr(planner_model, "invoke"):
        raise TypeError("chain Scout planner model must implement invoke(messages)")
    normalized_chain = str(chain or "").strip().lower()
    if not normalized_chain:
        raise ValueError("chain must be a non-empty string")

    prompt = f"""You are the planning component inside the {normalized_chain} chain Scout.

Return JSON only with exactly this shape:
{{"operations": ["market_report", "tokenomics", "risk_check"]}}

Rules:
- You may use only market_report, tokenomics, risk_check.
- Use the smallest useful plan, with no duplicates and at most three operations.
- Never propose pre_trade_check, transaction preparation, signing, broadcasting,
  wallet permissions, or any value-moving action.
- Do not invent market facts. Select investigations only.
- Risk/safety questions should include risk_check.
- Supply, mint-authority, freeze-authority, or tokenomics questions should include tokenomics.
"""
    response = planner_model.invoke(
        [
            SystemMessage(content=prompt),
            HumanMessage(
                content=(
                    f"Chain: {normalized_chain}\n"
                    f"Asset: {asset}\n"
                    f"Investigation objective: {objective}"
                )
            ),
        ]
    )
    return parse_plan_proposal(response)


def _validate_explicit_request(request: Mapping[str, Any]) -> dict[str, Any]:
    operation = request.get("operation")
    if operation not in {
        "market_report",
        "tokenomics",
        "risk_check",
        "pre_trade_check",
    }:
        raise ValueError(f"unsupported explicit CMIS operation: {operation!r}")
    if operation == "pre_trade_check":
        if request.get("action") is None or request.get("amount_usd") is None:
            raise ValueError("pre_trade_check requires action and amount_usd")
    return {
        "operations": [operation],
        "source": "explicit",
        "warnings": [],
    }


def enforce_plan(
    request: Mapping[str, Any],
    proposal: Mapping[str, Any] | None,
    *,
    planner_error: str | None = None,
) -> dict[str, Any]:
    """Convert an untrusted proposal into a deterministic executable plan."""

    if request.get("operation") is not None:
        return _validate_explicit_request(request)

    warnings: list[str] = []
    if planner_error:
        warnings.append(f"planner_fallback: {planner_error}")

    accepted: list[CMISOperation] = []
    proposed_operations = proposal.get("operations", []) if proposal else []
    if not isinstance(proposed_operations, list):
        proposed_operations = []
    for raw_operation in proposed_operations:
        operation = str(raw_operation or "").strip()
        if operation not in AUTONOMOUS_OPERATIONS:
            if operation:
                warnings.append(f"planner_operation_rejected: {operation}")
            continue
        typed: CMISOperation = operation  # type: ignore[assignment]
        if typed in accepted:
            continue
        accepted.append(typed)
        if len(accepted) >= MAX_PLAN_OPERATIONS:
            break

    source = "model" if proposal is not None else "deterministic"
    if not accepted:
        accepted = [select_cmis_operation(request.get("objective"))]
        source = "deterministic"
        if proposal is not None and not planner_error:
            warnings.append("planner_fallback: no allowed operations were proposed")

    for required in required_operations(request.get("objective")):
        if required in accepted:
            accepted.remove(required)
        accepted.append(required)

    accepted = accepted[-MAX_PLAN_OPERATIONS:]
    return {
        "operations": accepted,
        "source": source,
        "warnings": warnings,
    }
