"""Deterministic model doubles for Roberta graph tests."""

from typing import Any

from langchain_core.messages import AIMessage, ToolMessage


class ScriptedOracleModel:
    """Minimal chat-model-like object that deterministically delegates."""

    def __init__(self, *, request_tool: bool) -> None:
        self.request_tool = request_tool
        self.bound_tools: list[Any] = []
        self.invoke_count = 0

    def bind_tools(self, tools: list[Any]) -> "ScriptedOracleModel":
        self.bound_tools = list(tools)
        return self

    def invoke(self, messages: list[Any]) -> AIMessage:
        self.invoke_count += 1

        if not self.request_tool:
            return AIMessage(content="Roberta answered without a specialist.")

        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        if not tool_messages:
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "x1_scout_investigate",
                        "args": {
                            "asset": "AGI",
                            "objective": "assess market risk",
                        },
                        "id": "x1-scout-call-1",
                        "type": "tool_call",
                    }
                ],
            )

        return AIMessage(
            content=(
                "Roberta delegated the X1 investigation to X1 Scout. "
                "The specialist report is test-only and not live market data."
            )
        )
