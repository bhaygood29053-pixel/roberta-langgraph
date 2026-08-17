"""Cross-chain dispatch for chain-Scout policy fact adapters."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.messages import ToolMessage

from roberta.policy import PolicyFact, PolicyRule
from roberta.solana_scout.policy_facts import extract_solana_policy_facts
from roberta.x1_scout.policy_facts import extract_x1_policy_facts

_TOOL_ADAPTERS = {
    "x1_scout_investigate": extract_x1_policy_facts,
    "solana_scout_investigate": extract_solana_policy_facts,
}


def chain_policy_facts_from_state(
    state: Mapping[str, Any],
    rules: Sequence[PolicyRule],
) -> Mapping[str, PolicyFact]:
    """Use the latest chain-Scout result as the current policy evidence frame.

    The dispatcher intentionally does not merge reports from different chain
    Scouts. A later Solana investigation must not inherit an older X1 market fact
    (or vice versa) merely because both ToolMessages remain in thread history.
    """

    requested = {rule.fact_key for rule in rules}
    messages = state.get("messages", [])
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
