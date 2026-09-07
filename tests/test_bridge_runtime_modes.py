from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from roberta.bridge_http import (
    EVALUATION_TELEMETRY_VERSION,
    RobertaBridge,
)
from roberta.graph import build_graph


class HistoryEchoModel:
    """Echo the user-message history visible to the protected Oracle graph."""

    def bind_tools(self, tools: list[Any]) -> "HistoryEchoModel":
        return self

    def invoke(self, messages: list[Any]) -> AIMessage:
        user_text = [
            str(message.content)
            for message in messages
            if isinstance(message, HumanMessage)
        ]
        return AIMessage(content="seen:" + "|".join(user_text))


def _bridge() -> RobertaBridge:
    stateless = build_graph(
        model=HistoryEchoModel(),
        tools=[],
    )
    threaded = build_graph(
        model=HistoryEchoModel(),
        tools=[],
        checkpointer=InMemorySaver(),
    )
    return RobertaBridge(stateless, threaded_graph=threaded)


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
