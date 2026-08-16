"""Deterministic tests for Roberta thread/checkpoint persistence."""

from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver

from roberta.graph import build_graph
from roberta.runtime import build_thread_config, invoke_thread


class HistoryEchoModel:
    """Echo the user-message history visible to the Oracle node."""

    def bind_tools(self, tools: list[Any]) -> "HistoryEchoModel":
        return self

    def invoke(self, messages: list[Any]) -> AIMessage:
        user_text = [
            str(message.content)
            for message in messages
            if isinstance(message, HumanMessage)
        ]
        return AIMessage(content="seen:" + "|".join(user_text))


def _input(text: str) -> dict[str, object]:
    return {
        "messages": [{"role": "user", "content": text}],
        "status": "running",
    }


def test_same_thread_continues_prior_messages() -> None:
    checkpointer = InMemorySaver()
    graph = build_graph(
        model=HistoryEchoModel(),
        tools=[],
        checkpointer=checkpointer,
    )

    first = invoke_thread(graph, _input("first"), thread_id="thread-a")
    second = invoke_thread(graph, _input("second"), thread_id="thread-a")

    assert first["messages"][-1].content == "seen:first"
    assert second["messages"][-1].content == "seen:first|second"
    assert len(second["messages"]) == 4


def test_different_thread_ids_are_isolated() -> None:
    checkpointer = InMemorySaver()
    graph = build_graph(
        model=HistoryEchoModel(),
        tools=[],
        checkpointer=checkpointer,
    )

    invoke_thread(graph, _input("alpha"), thread_id="thread-a")
    other = invoke_thread(graph, _input("beta"), thread_id="thread-b")

    assert other["messages"][-1].content == "seen:beta"
    assert len(other["messages"]) == 2


def test_new_graph_instance_resumes_from_same_checkpoint_backend() -> None:
    checkpointer = InMemorySaver()
    graph_one = build_graph(
        model=HistoryEchoModel(),
        tools=[],
        checkpointer=checkpointer,
    )
    invoke_thread(graph_one, _input("before-restart"), thread_id="thread-a")

    graph_two = build_graph(
        model=HistoryEchoModel(),
        tools=[],
        checkpointer=checkpointer,
    )
    resumed = invoke_thread(
        graph_two,
        _input("after-restart"),
        thread_id="thread-a",
    )

    assert resumed["messages"][-1].content == (
        "seen:before-restart|after-restart"
    )
    assert len(resumed["messages"]) == 4


def test_thread_config_is_explicit_and_validated() -> None:
    assert build_thread_config("thread-a") == {
        "configurable": {"thread_id": "thread-a"}
    }

    with pytest.raises(ValueError, match="thread_id must not be empty"):
        build_thread_config("   ")

    with pytest.raises(TypeError, match="thread_id must be a string"):
        build_thread_config(None)  # type: ignore[arg-type]
