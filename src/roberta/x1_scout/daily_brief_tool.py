"""ROBERTA-facing X1 Scout wrapper for network-level Daily Brief intent.

The historical X1 Scout tool remains the implementation for every existing
operation. This wrapper changes only one product intent: a network-level X1
Daily Intelligence Brief. That intent is routed to a bounded Scout workflow
instead of letting a model-proposed ``asset='XDEX'`` become a token lookup.
"""

from __future__ import annotations

from typing import Any

from roberta.x1_scout.daily_intelligence_brief_workflow import (
    run_x1_daily_intelligence_brief_workflow,
)
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.tool import build_x1_scout_tool as _build_base_x1_scout_tool


def is_x1_daily_intelligence_brief_objective(value: object) -> bool:
    """Recognize only clear network-level X1 Daily Brief requests."""

    text = " ".join(str(value or "").strip().lower().split())
    if not text:
        return False
    if "x1 intelligence brief" in text or "x1 daily brief" in text:
        return True
    if "daily intelligence brief" in text and "x1" in text:
        return True
    if "today's x1" in text and "brief" in text:
        return True
    if "today’s x1" in text and "brief" in text:
        return True
    if "what changed on x1 today" in text:
        return True
    return False


def build_x1_scout_tool(cmis_client: Any, planner_model: Any | None = None):
    """Return the accepted X1 Scout tool with deterministic Daily Brief routing."""

    base = _build_base_x1_scout_tool(cmis_client, planner_model=planner_model)
    original_func = base.func
    if original_func is None:  # pragma: no cover - current Scout tool is synchronous
        raise RuntimeError("X1 Scout tool has no synchronous implementation")

    scout_graph = build_x1_scout_graph(cmis_client, planner_model=planner_model)

    def routed_func(**kwargs: Any) -> str:
        objective = kwargs.get("objective")
        if is_x1_daily_intelligence_brief_objective(objective):
            report = run_x1_daily_intelligence_brief_workflow(
                cmis_client=cmis_client,
                scout_graph=scout_graph,
                objective=str(objective or ""),
            )
            # Match the original StructuredTool contract: JSON text containing one
            # X1 Scout report. The bridge/tool layer owns serialization, not facts.
            import json

            return json.dumps(report, sort_keys=True)
        return original_func(**kwargs)

    description = (
        f"{base.description}\n\n"
        "X1 Daily Intelligence Brief routing: for a clear network-level request such as "
        "'Give me today's X1 intelligence brief', preserve the user's exact objective. "
        "The Scout deterministically selects a bounded exact-mint scope and uses the "
        "accepted Daily Brief service. Never treat XDEX as a token mint for that intent."
    )

    # StructuredTool is a Pydantic model. Copying it preserves the exact accepted
    # argument schema while replacing only the synchronous function and description.
    if hasattr(base, "model_copy"):
        return base.model_copy(update={"func": routed_func, "description": description})
    return base.copy(update={"func": routed_func, "description": description})


__all__ = [
    "build_x1_scout_tool",
    "is_x1_daily_intelligence_brief_objective",
]
