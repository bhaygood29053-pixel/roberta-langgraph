"""Tests for current-turn message scoping of specialist policy evidence."""

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from roberta.specialists.turn_scope import current_user_turn_messages


def _tool(call_id: str):
    return ToolMessage(
        content="{}",
        name="x1_scout_investigate",
        tool_call_id=call_id,
    )


def test_no_user_marker_fails_closed_to_no_current_turn_messages() -> None:
    assert current_user_turn_messages([_tool("historical")]) == []


def test_latest_human_message_resets_specialist_evidence_scope() -> None:
    old_tool = _tool("old")
    new_ai = AIMessage(content="researching")
    new_tool = _tool("new")

    scoped = current_user_turn_messages(
        [
            HumanMessage(content="old request"),
            old_tool,
            HumanMessage(content="new request"),
            new_ai,
            new_tool,
        ]
    )

    assert scoped == [new_ai, new_tool]
    assert old_tool not in scoped


def test_raw_user_role_message_also_resets_scope() -> None:
    old_tool = _tool("old")
    current_tool = _tool("current")

    scoped = current_user_turn_messages(
        [
            old_tool,
            {"role": "user", "content": "current request"},
            current_tool,
        ]
    )

    assert scoped == [current_tool]


def test_latest_of_multiple_user_messages_wins() -> None:
    first = _tool("first")
    second = _tool("second")

    scoped = current_user_turn_messages(
        [
            HumanMessage(content="one"),
            first,
            HumanMessage(content="two"),
            second,
        ]
    )

    assert scoped == [second]
