"""Opt-in integration test for live DeepSeek -> X1 Scout delegation.

Run with:

    RUN_LIVE_MODEL_TESTS=1 DEEPSEEK_API_KEY=... python -m pytest -v -m live
"""

import os

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from roberta.graph import build_graph
from roberta.models import create_runtime_model


pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.getenv("RUN_LIVE_MODEL_TESTS") != "1",
        reason="Set RUN_LIVE_MODEL_TESTS=1 to enable paid live-model tests.",
    ),
]


def test_live_roberta_autonomously_delegates_x1_market_request() -> None:
    """A real model should delegate the X1 request to X1 Scout."""
    model = create_runtime_model()
    graph = build_graph(model=model)

    result = graph.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "On X1, check AGI market risk.",
                }
            ],
            "status": "running",
        }
    )

    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert tool_messages[0].name == "x1_scout_investigate"
    content = str(tool_messages[0].content)
    assert '"specialist": "x1_scout"' in content
    assert '"service": "cmis"' in content
    assert "TEST_ONLY" in content
    assert "AGI" in content

    final_message = result["messages"][-1]
    assert isinstance(final_message, AIMessage)
    assert final_message.tool_calls == []
    assert result["status"] == "complete"
