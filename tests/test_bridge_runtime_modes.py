from __future__ import annotations

from collections import defaultdict
from typing import Any

from langchain_core.messages import AIMessage

from roberta.bridge_http import (
    EVALUATION_TELEMETRY_VERSION,
    RobertaBridge,
)


class StrictStatelessGraph:
    """Public-shell stand-in that rejects accidental checkpoint config."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def invoke(self, payload, config=None):
        if config is not None:
            raise AssertionError("stateless graph received checkpoint config")
        self.calls.append({"payload": payload, "config": config})
        text = str(payload["messages"][-1]["content"])
        return {
            "messages": [AIMessage(content=f"seen:{text}")],
            "status": "complete",
        }


class StrictCheckpointGraph:
    """Emulate LangGraph's explicit-thread checkpoint requirement."""

    def __init__(self) -> None:
        self.history: dict[str, list[str]] = defaultdict(list)
        self.calls: list[dict[str, Any]] = []

    def invoke(self, payload, config=None):
        configurable = config.get("configurable") if isinstance(config, dict) else None
        thread_id = configurable.get("thread_id") if isinstance(configurable, dict) else None
        if not isinstance(thread_id, str) or not thread_id:
            raise ValueError("checkpointed graph requires thread_id")

        text = str(payload["messages"][-1]["content"])
        self.history[thread_id].append(text)
        self.calls.append({"payload": payload, "config": config})
        return {
            "messages": [
                AIMessage(content="seen:" + "|".join(self.history[thread_id]))
            ],
            "status": "complete",
        }


def _bridge() -> RobertaBridge:
    return RobertaBridge(
        StrictStatelessGraph(),
        threaded_graph=StrictCheckpointGraph(),
    )


def test_stateless_bridge_requests_do_not_require_checkpoint_config() -> None:
    bridge = _bridge()

    first = bridge.ask("first")
    second = bridge.ask("second")

    assert first == "seen:first"
    assert second == "seen:second"


def test_evaluation_mode_can_use_stateless_graph() -> None:
    bridge = _bridge()

    reply, telemetry = bridge.ask_with_evaluation("evaluate me")

    assert reply == "seen:evaluate me"
    assert telemetry["evaluation_telemetry_version"] == EVALUATION_TELEMETRY_VERSION
    assert telemetry["evaluation_evidence"] == {}
    assert telemetry["claims"] == []
    assert telemetry["execution_authorized"] is False


def test_explicit_thread_id_uses_checkpointed_graph_and_preserves_continuity() -> None:
    bridge = _bridge()

    first = bridge.ask("first", thread_id="thread-a")
    second = bridge.ask("second", thread_id="thread-a")
    other = bridge.ask("other", thread_id="thread-b")

    assert first == "seen:first"
    assert second == "seen:first|second"
    assert other == "seen:other"
