"""Cross-chain dispatch for chain-Scout policy fact adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.messages import ToolMessage

from roberta.policy import PolicyFact, PolicyRule
from roberta.solana_scout.policy_facts import extract_solana_policy_facts
from roberta.specialists.turn_scope import current_user_turn_messages
from roberta.x1_scout.policy_facts import extract_x1_policy_facts

_TOOL_ADAPTERS = {
    "x1_scout_investigate": extract_x1_policy_facts,
    "solana_scout_investigate": extract_solana_policy_facts,
}


def chain_policy_facts_from_state(
    state: Mapping[str, Any],
    rules: Sequence[PolicyRule],
) -> Mapping[str, PolicyFact]:
    """Use the latest chain-Scout result from the current user turn only.

    The dispatcher intentionally does not merge reports from different chain
    Scouts. It also ignores ToolMessages retained from prior user turns. A new
    request starts with no current market evidence until a Scout runs again.
    """

    requested = {rule.fact_key for rule in rules}
    messages = current_user_turn_messages(state.get("messages", []))
    for message in reversed(messages):
        if not isinstance(message, ToolMessage):
            continue
        adapter = _TOOL_ADAPTERS.get(message.name)
        if adapter is None:
            continue
        content = message.content
        if not isinstance(content, str):
            raise ValueError("chain Scout ToolMessage content must be JSON text")
        try:
            report = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("chain Scout ToolMessage returned invalid JSON") from exc
        if not isinstance(report, Mapping):
            raise ValueError("chain Scout ToolMessage JSON must be an object")
        return adapter(report, requested_fact_keys=requested)
    return {}
