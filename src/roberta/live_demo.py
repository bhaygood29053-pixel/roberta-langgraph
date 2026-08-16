"""Command-line smoke test for Roberta -> X1 Scout delegation."""

from __future__ import annotations

import argparse

from langchain_core.messages import AIMessage, ToolMessage

from roberta.graph import build_graph
from roberta.models import create_runtime_model
from roberta.tools import get_roberta_tools


def _message_text(message: object) -> str:
    text = getattr(message, "text", None)
    if isinstance(text, str) and text:
        return text
    return str(getattr(message, "content", ""))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one live Roberta request through the X1 Scout integration."
    )
    parser.add_argument(
        "message",
        nargs="?",
        default="On X1, check AGI market risk",
        help="User message to send to Roberta.",
    )
    args = parser.parse_args()

    oracle_model = create_runtime_model()
    x1_planner_model = create_runtime_model()
    tools = get_roberta_tools(x1_planner_model=x1_planner_model)
    graph = build_graph(model=oracle_model, tools=tools)
    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": args.message}],
            "status": "running",
        }
    )

    print("\n--- Roberta execution ---")
    for message in result["messages"]:
        if isinstance(message, ToolMessage):
            print(f"TOOL [{message.name}]: {message.content}")
        elif isinstance(message, AIMessage):
            if message.tool_calls:
                print(f"ROBERTA TOOL CALL: {message.tool_calls}")
            elif _message_text(message):
                print(f"ROBERTA: {_message_text(message)}")

    print(f"STATUS: {result.get('status')}")


if __name__ == "__main__":
    main()
