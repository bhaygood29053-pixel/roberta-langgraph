"""Constrained X1 Scout planning helpers.

The model may propose read-only CMIS investigations, but deterministic code
remains authoritative for what actually runs. The planner cannot grant itself
execution authority or autonomous pre-trade access.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from roberta.cmis.contracts import CMISOperation
from roberta.x1_scout.state import X1ScoutPlan, X1ScoutPlanProposal, X1ScoutRequest

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

X1_SCOUT_PLANNER_SYSTEM_PROMPT = """You are the planning component inside X1 Scout.

Your job is only to propose which read-only CMIS investigations are useful for
the user's X1 objective. Return JSON only, with exactly this shape:
{"operations": ["market_report", "tokenomics", "risk_check"]}

Rules:
- You may use only: market_report, tokenomics, risk_check.
- Use the smallest useful plan, with no duplicates and at most three operations.
- Never propose pre_trade_check, transaction preparation, signing, broadcasting,
  wallet permissions, or any value-moving action.
- Do not invent market facts. You are selecting investigations, not answering
  the market question.
- Risk questions should include risk_check.
- Supply, mint-authority, freeze-authority, or tokenomics questions should
  include tokenomics.
"""


def _normalize_objective(objective: object) -> str:
    return " ".join(str(objective or "").strip().lower().split())


def required_operations(objective: object) -> list[CMISOperation]:
    """Return objective-required operations in deterministic priority order."""

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


def parse_plan_proposal(value: Any) -> X1ScoutPlanProposal:
    """Parse the untrusted model response into the narrow proposal shape."""

    if isinstance(value, Mapping):
        payload: Any = value
    else:
        content = getattr(value, "content", value)
        if not isinstance(content, str):
            raise ValueError("X1 Scout planner response must contain JSON text.")
        payload = json.loads(_strip_markdown_fence(content))

    if not isinstance(payload, Mapping):
        raise ValueError("X1 Scout planner response must be a JSON object.")
    operations = payload.get("operations")
    if not isinstance(operations, list):
        raise ValueError("X1 Scout planner response must contain an operations list.")

    parsed: list[str] = []
    for operation in operations:
        if isinstance(operation, str):
            parsed.append(operation.strip())
    return {"operations": parsed}


def propose_plan(planner_model: Any, request: X1ScoutRequest) -> X1ScoutPlanProposal:
    """Ask the injected Scout planner model for a narrow JSON proposal."""

    if not hasattr(planner_model, "invoke"):
        raise TypeError("X1 Scout planner model must implement invoke(messages).")
    response = planner_model.invoke(
        [
            SystemMessage(content=X1_SCOUT_PLANNER_SYSTEM_PROMPT),
            HumanMessage(
                content=(
                    f"X1 asset: {request['asset']}\n"
                    f"Investigation objective: {request['objective']}"
                )
            ),
        ]
    )
    return parse_plan_proposal(response)


def _validate_explicit_request(request: X1ScoutRequest) -> X1ScoutPlan:
    operation = request["operation"]
    if operation == "pre_trade_check":
        if request.get("action") is None or request.get("amount_usd") is None:
            raise ValueError(
                "pre_trade_check requires action and amount_usd in X1 Scout state"
            )
    return {
        "operations": [operation],
        "source": "explicit",
        "warnings": [],
    }


def enforce_plan(
    request: X1ScoutRequest,
    proposal: X1ScoutPlanProposal | None,
    *,
    planner_error: str | None = None,
) -> X1ScoutPlan:
    """Convert an untrusted proposal into the deterministic executable plan."""

    if "operation" in request:
        return _validate_explicit_request(request)

    warnings: list[str] = []
    if planner_error:
        warnings.append(f"planner_fallback: {planner_error}")

    accepted: list[CMISOperation] = []
    proposed_operations = proposal.get("operations", []) if proposal else []
    for raw_operation in proposed_operations:
        operation = str(raw_operation or "").strip()
        if operation not in AUTONOMOUS_OPERATIONS:
            if operation:
                warnings.append(f"planner_operation_rejected: {operation}")
            continue
        typed_operation: CMISOperation = operation  # type: ignore[assignment]
        if typed_operation in accepted:
            continue
        accepted.append(typed_operation)
        if len(accepted) >= MAX_PLAN_OPERATIONS:
            break

    source: str = "model" if proposal is not None else "deterministic"
    if not accepted:
        accepted = [select_cmis_operation(request["objective"])]
        source = "deterministic"
        if proposal is not None and not planner_error:
            warnings.append("planner_fallback: no allowed operations were proposed")

    # Required operations are always executed and moved to the end so the
    # objective-critical deterministic result remains the top-level report.
    for required in required_operations(request["objective"]):
        if required in accepted:
            accepted.remove(required)
        accepted.append(required)

    # There are only three autonomous operation types today, but keep the cap
    # explicit so future additions cannot silently widen model authority.
    accepted = accepted[-MAX_PLAN_OPERATIONS:]

    return {
        "operations": accepted,
        "source": source,  # type: ignore[typeddict-item]
        "warnings": warnings,
    }
