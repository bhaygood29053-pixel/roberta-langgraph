"""Constrained X1 Scout planning helpers.

The model may propose read-only CMIS investigations, but deterministic code
remains authoritative for what actually runs. The planner cannot grant itself
execution authority or autonomous pre-trade or verification-evidence access.
Recommendation-style questions are expanded through the deterministic Roberta
evidence-needs policy so required market/risk/history facts are not omitted by
model prose.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from roberta.cmis.contracts import CMISOperation, HistoricalMode, RankMetric
from roberta.cmis.verification import normalize_verification_evidence_selector
from roberta.recommendation_policy import (
    autonomous_x1_operations_for_recommendation,
    recommendation_intent,
)
from roberta.x1_scout.state import X1ScoutPlan, X1ScoutPlanProposal, X1ScoutRequest

AUTONOMOUS_OPERATIONS: tuple[CMISOperation, ...] = (
    "instant_x1_scan",
    "market_report",
    "rank",
    "historical_compare",
    "tokenomics",
    "risk_check",
)
MAX_PLAN_OPERATIONS = 3
FULL_ASSESSMENT_MAX_PLAN_OPERATIONS = 5
MAX_RANK_LIMIT = 50

_INSTANT_SCAN_TERMS = (
    "instant x1 scan",
    "instant scan",
    "quick x1 scan",
    "quick scan",
    "scan this asset",
    "scan this token",
    "scan this coin",
    "scan the asset",
    "scan the token",
)
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
_ALL_AVAILABLE_HISTORY_TERMS = (
    "entire history",
    "full history",
    "all history",
    "all available history",
    "since inception",
    "since launch",
    "lifetime history",
    "whole history",
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
{"operations": ["instant_x1_scan", "market_report", "rank", "historical_compare", "tokenomics", "risk_check"]}

Rules:
- You may use only: instant_x1_scan, market_report, rank, historical_compare, tokenomics, risk_check.
- Use instant_x1_scan only when the objective explicitly asks for an Instant X1 Scan or quick/instant asset scan.
- Use the smallest useful plan, with no duplicates and at most three operations.
- For a full/complete/comprehensive assessment or due-diligence objective, propose
  up to five operations because deterministic policy requires market_report,
  rank, tokenomics, historical_compare, and risk_check.
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


def is_instant_x1_scan_objective(objective: object) -> bool:
    """Return whether the user explicitly requested the flagship Instant X1 Scan."""

    normalized = _normalize_objective(objective)
    if not normalized:
        return False
    if any(term in normalized for term in _INSTANT_SCAN_TERMS):
        return True

    # X1 Scout already owns the chain scope, so a direct user command such as
    # "scan AGI", "scan XNT", "scan token AGI", or "please scan AGI" is an
    # explicit request for the flagship scan. This is request routing only; the
    # asset itself remains the separately supplied Scout request identity.
    return re.match(
        r"^(?:please\s+)?(?:x1\s+)?scan"
        r"(?:\s+(?:the\s+)?(?:asset|token|coin))?"
        r"\s+\S+",
        normalized,
    ) is not None


def is_rank_objective(objective: object) -> bool:
    normalized = _normalize_objective(objective)
    if not normalized:
        return False
    padded = f" {normalized} "
    return any(term in padded for term in _RANK_TERMS)


def is_historical_objective(objective: object) -> bool:
    normalized = _normalize_objective(objective)
    return bool(normalized) and any(term in normalized for term in _HISTORICAL_TERMS)



def is_all_available_history_objective(objective: object) -> bool:
    normalized = _normalize_objective(objective)
    return bool(normalized) and any(
        term in normalized for term in _ALL_AVAILABLE_HISTORY_TERMS
    )


def compare_asset_from_objective(
    objective: object,
    *,
    primary_asset: object,
) -> str | None:
    """Extract a simple second asset symbol from the exact user objective.

    This is request parsing only. It does not resolve symbols to chain identity
    or create a market fact; CMIS remains authoritative for asset resolution.
    """

    text = " ".join(str(objective or "").strip().split())
    primary = str(primary_asset or "").strip()
    if not text or not primary:
        return None

    match = re.search(
        r"\bcompare\s+([A-Za-z0-9._:-]+)\s+(?:and|versus|vs\.?)\s+([A-Za-z0-9._:-]+)\b",
        text,
        flags=re.IGNORECASE,
    )
    if match is None:
        match = re.search(
            r"\b([A-Za-z0-9._:-]+)\s+(?:versus|vs\.?)\s+([A-Za-z0-9._:-]+)\b",
            text,
            flags=re.IGNORECASE,
        )
    if match is None:
        return None

    left, right = match.group(1), match.group(2)
    if left.lower() == primary.lower() and right.lower() != primary.lower():
        return right
    if right.lower() == primary.lower() and left.lower() != primary.lower():
        return left
    return None


def historical_mode_from_objective(
    objective: object,
    *,
    compare_asset: object = None,
) -> HistoricalMode:
    full_assessment = recommendation_intent(objective) == "full_assessment"
    if not is_all_available_history_objective(objective) and not full_assessment:
        return "window"
    if str(compare_asset or "").strip():
        return "all_available_pair"
    return "all_available"


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


def max_plan_operations_for_objective(objective: object) -> int:
    """Return the deterministic plan ceiling for the requested evidence scope."""

    if is_instant_x1_scan_objective(objective):
        return 1
    return (
        FULL_ASSESSMENT_MAX_PLAN_OPERATIONS
        if recommendation_intent(objective) == "full_assessment"
        else MAX_PLAN_OPERATIONS
    )


def required_operations(objective: object) -> list[CMISOperation]:
    """Return objective-required operations in deterministic priority order.

    Recommendation-style evidence requirements are deterministic and therefore
    cannot be omitted by the Scout planning model. Explicit pre-trade itself is
    still excluded here and remains guarded by `_validate_explicit_request`.
    """

    normalized = _normalize_objective(objective)
    if is_instant_x1_scan_objective(normalized):
        return ["instant_x1_scan"]
    intent = recommendation_intent(normalized)
    if is_rank_objective(normalized) and intent != "full_assessment":
        return ["rank"]

    required: list[CMISOperation] = []
    for operation in autonomous_x1_operations_for_recommendation(normalized):
        if operation not in required:
            required.append(operation)
    if any(term in normalized for term in _TOKENOMICS_TERMS) and "tokenomics" not in required:
        required.append("tokenomics")
    if any(term in normalized for term in _RISK_TERMS) and "risk_check" not in required:
        required.append("risk_check")
    if is_historical_objective(normalized) and "historical_compare" not in required:
        required.append("historical_compare")
    return required[-max_plan_operations_for_objective(normalized):]


def select_cmis_operation(objective: object) -> CMISOperation:
    """Return the deterministic single-operation fallback for an objective."""

    if is_instant_x1_scan_objective(objective):
        return "instant_x1_scan"
    if is_rank_objective(objective):
        return "rank"
    if is_historical_objective(objective):
        return "historical_compare"
    required = required_operations(objective)
    if "risk_check" in required:
        return "risk_check"
    if "tokenomics" in required:
        return "tokenomics"
    if "market_report" in required:
        return "market_report"
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

    objective = request["objective"]
    rank_only_objective = (
        is_rank_objective(objective)
        and recommendation_intent(objective) != "full_assessment"
    )
    max_plan_operations = max_plan_operations_for_objective(objective)
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
        if operation == "instant_x1_scan" and not is_instant_x1_scan_objective(objective):
            warnings.append(
                "planner_operation_rejected_without_instant_scan_objective: instant_x1_scan"
            )
            continue
        if rank_only_objective and operation != "rank":
            warnings.append(
                f"planner_operation_rejected_for_rank_objective: {operation}"
            )
            continue
        typed_operation: CMISOperation = operation  # type: ignore[assignment]
        if typed_operation in accepted:
            continue
        accepted.append(typed_operation)
        if len(accepted) >= max_plan_operations:
            break

    source: str = "model" if proposal is not None else "deterministic"
    if not accepted:
        accepted = [select_cmis_operation(objective)]
        source = "deterministic"
        if proposal is not None and not planner_error:
            warnings.append("planner_fallback: no allowed operations were proposed")

    # Objective-required operations are always executed and moved to the end so
    # the objective-critical deterministic result remains the top-level report.
    for required in required_operations(objective):
        if required in accepted:
            accepted.remove(required)
        accepted.append(required)

    accepted = accepted[-max_plan_operations:]

    return {
        "operations": accepted,
        "source": source,  # type: ignore[typeddict-item]
        "warnings": warnings,
    }
