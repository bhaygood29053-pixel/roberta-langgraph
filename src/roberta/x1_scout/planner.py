"""Constrained X1 Scout planning helpers.

The model may propose read-only CMIS investigations, but deterministic code
remains authoritative for what actually runs. The planner cannot grant itself
execution authority or autonomous pre-trade or verification-evidence access.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from roberta.cmis.contracts import CMISOperation, RankMetric
from roberta.cmis.verification import normalize_verification_evidence_selector
from roberta.x1_scout.state import X1ScoutPlan, X1ScoutPlanProposal, X1ScoutRequest

AUTONOMOUS_OPERATIONS: tuple[CMISOperation, ...] = (
    "market_report",
    "rank",
    "historical_compare",
    "tokenomics",
    "risk_check",
)
MAX_PLAN_OPERATIONS = 3
MAX_RANK_LIMIT = 50

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
_RANK_TERMS = (
    " rank",
    "rank ",
    "ranking",
    "top ",
    "gainer",
    "loser",
    "trending",
    "most active",
    "safest tokens",
)
_HISTORICAL_TERMS = (
    "historical",
    "history",
    "yesterday",
    "last week",
    "last month",
    "ago",
    "since ",
    "over the last",
    "compared to last",
    "compared with last",
    "changed over",
    "fallen",
    "fell ",
    "dropped",
    "declined",
    "risen",
    "rose ",
)

X1_SCOUT_PLANNER_SYSTEM_PROMPT = """You are the planning component inside X1 Scout.

Your job is only to propose which read-only CMIS investigations are useful for
the user's X1 objective. Return JSON only, with exactly this shape:
{"operations": ["market_report", "rank", "historical_compare", "tokenomics", "risk_check"]}

Rules:
- You may use only: market_report, rank, historical_compare, tokenomics, risk_check.
- Use the smallest useful plan, with no duplicates and at most three operations.
- Never propose pre_trade_check, verification_evidence, transaction preparation,
  signing, broadcasting, wallet permissions, or any value-moving action.
- Do not invent market facts. You are selecting investigations, not answering
  the market question.
- Ranking/top/gainer/loser/trending requests should include rank.
- Historical change/comparison requests should include historical_compare.
- Risk questions should include risk_check.
- Supply, mint-authority, freeze-authority, or tokenomics questions should
  include tokenomics.
"""


def _normalize_objective(objective: object) -> str:
    return " ".join(str(objective or "").strip().lower().split())


def is_rank_objective(objective: object) -> bool:
    normalized = _normalize_objective(objective)
    if not normalized:
        return False
    padded = f" {normalized} "
    return any(term in padded for term in _RANK_TERMS)


def is_historical_objective(objective: object) -> bool:
    normalized = _normalize_objective(objective)
    return bool(normalized) and any(term in normalized for term in _HISTORICAL_TERMS)


def rank_metric_from_objective(objective: object) -> RankMetric:
    """Derive the CMIS ranking metric without relying on model-supplied params."""

    normalized = _normalize_objective(objective)
    if "trending" in normalized or "most active" in normalized:
        return "trending"
    if "gainer" in normalized or "biggest gain" in normalized:
        return "gainers"
    if "loser" in normalized or "biggest loss" in normalized:
        return "losers"
    if "liquidity" in normalized or re.search(r"\bliq\b", normalized):
        return "liquidity"
    if "holder" in normalized:
        return "holders"
    if "safety" in normalized or "safest" in normalized or "safe tokens" in normalized:
        return "safety"
    return "volume"


def rank_limit_from_objective(objective: object, *, default: int = 10) -> int:
    """Derive a bounded user-facing ranking limit from an objective."""

    normalized = _normalize_objective(objective)
    match = re.search(r"\btop\s+(\d+)\b", normalized)
    if not match:
        return default
    value = int(match.group(1))
    return max(1, min(value, MAX_RANK_LIMIT))


def required_operations(objective: object) -> list[CMISOperation]:
    """Return objective-required operations in deterministic priority order."""

    normalized = _normalize_objective(objective)
    if is_rank_objective(normalized):
        return ["rank"]

    required: list[CMISOperation] = []
    if any(term in normalized for term in _TOKENOMICS_TERMS):
        required.append("tokenomics")
    if any(term in normalized for term in _RISK_TERMS):
        required.append("risk_check")
    if is_historical_objective(normalized):
        required.append("historical_compare")
    return required


def select_cmis_operation(objective: object) -> CMISOperation:
    """Return the deterministic single-operation fallback for an objective."""

    if is_rank_objective(objective):
        return "rank"
    if is_historical_objective(objective):
        return "historical_compare"
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
    if operation == "verification_evidence":
        normalize_verification_evidence_selector(
            evidence_id=request.get("evidence_id"),
            fact_type=request.get("fact_type"),
            subject_id=request.get("subject_id"),
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

    accepted = accepted[-MAX_PLAN_OPERATIONS:]

    return {
        "operations": accepted,
        "source": source,  # type: ignore[typeddict-item]
        "warnings": warnings,
    }
