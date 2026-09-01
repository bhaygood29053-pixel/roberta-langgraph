"""X1 Scout chain-specialist boundary.

The public shell exposes X1 Scout product/contract modules even when the
protected ROBERTA host is not installed. Keep graph/tool/policy convenience
exports lazy so importing a public submodule does not eagerly load protected
orchestration dependencies such as ``roberta.evidence_aware``.
"""

from __future__ import annotations

from typing import Any


__all__ = [
    "build_x1_scout_graph",
    "build_x1_scout_tool",
    "extract_x1_policy_facts",
    "x1_policy_facts_from_state",
]


def __getattr__(name: str) -> Any:
    if name == "build_x1_scout_graph":
        from roberta.x1_scout.graph import build_x1_scout_graph

        return build_x1_scout_graph
    if name == "build_x1_scout_tool":
        from roberta.x1_scout.tool import build_x1_scout_tool

        return build_x1_scout_tool
    if name in {"extract_x1_policy_facts", "x1_policy_facts_from_state"}:
        from roberta.x1_scout.policy_facts import (
            extract_x1_policy_facts,
            x1_policy_facts_from_state,
        )

        return {
            "extract_x1_policy_facts": extract_x1_policy_facts,
            "x1_policy_facts_from_state": x1_policy_facts_from_state,
        }[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
