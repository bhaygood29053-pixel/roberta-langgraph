"""Tests for Roberta's coordinator -> X1 Scout delegation loop."""

from langchain_core.messages import AIMessage, ToolMessage

from roberta.cmis.mock import MockCMISClient
from roberta.graph import build_graph
from roberta.tools import get_roberta_tools
from tests.fakes import ScriptedOracleModel


def _test_tools():
    return get_roberta_tools(cmis_client=MockCMISClient())


def test_roberta_can_answer_without_a_specialist() -> None:
    model = ScriptedOracleModel(request_tool=False)
    graph = build_graph(model=model, tools=_test_tools())

    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": "Who are you?"}],
            "status": "running",
        }
    )

    assert result["status"] == "complete"
    assert model.invoke_count == 1
    assert isinstance(result["messages"][-1], AIMessage)
    assert result["messages"][-1].content == "Roberta answered without a specialist."


def test_roberta_delegates_to_x1_scout_observes_report_and_finishes() -> None:
    model = ScriptedOracleModel(request_tool=True)
    graph = build_graph(model=model, tools=_test_tools())

    result = graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "On X1, check AGI market risk",
                }
            ],
            "status": "running",
        }
    )

    assert result["status"] == "complete"
    assert model.invoke_count == 2

    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert tool_messages[0].name == "x1_scout_investigate"
    content = str(tool_messages[0].content)
    assert '"specialist": "x1_scout"' in content
    assert '"chain": "x1"' in content
    assert '"service": "cmis"' in content
    assert '"cmis_status": "partial"' in content
    assert "TEST_ONLY" in content
    assert "AGI" in content

    final_message = result["messages"][-1]
    assert isinstance(final_message, AIMessage)
    assert final_message.tool_calls == []
    assert "delegated the X1 investigation to X1 Scout" in str(final_message.content)
