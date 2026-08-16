"""Roberta LangGraph coordinator/model-tool loop."""

from collections.abc import Callable, Sequence
from typing import Any, Literal

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from roberta.prompts import ORACLE_SYSTEM_PROMPT
from roberta.state import RobertaState
from roberta.tools import get_roberta_tools

Route = Literal["tools", "__end__"]


def _bind_tools(model: Any, tools: Sequence[BaseTool]) -> Any:
    """Bind Roberta's specialist/tool registry to a chat-model-like object."""
    if not hasattr(model, "bind_tools"):
        raise TypeError("Roberta model must implement bind_tools(tools).")
    return model.bind_tools(list(tools))


def make_oracle_node(model_with_tools: Any) -> Callable[[RobertaState], dict[str, Any]]:
    """Create Roberta's Oracle/coordinator model node."""

    def oracle_node(state: RobertaState) -> dict[str, Any]:
        response = model_with_tools.invoke(
            [SystemMessage(content=ORACLE_SYSTEM_PROMPT), *state["messages"]]
        )
        if not isinstance(response, AIMessage):
            raise TypeError("Roberta model must return an AIMessage.")

        return {
            "messages": [response],
            "status": "running" if response.tool_calls else "complete",
        }

    return oracle_node


def route_after_oracle(state: RobertaState) -> Route:
    """Route to a specialist/tool when Roberta requested one; otherwise stop."""
    last_message = state["messages"][-1]
    tool_calls = getattr(last_message, "tool_calls", None)
    if tool_calls:
        return "tools"
    return END


def build_graph(
    model: Any,
    tools: Sequence[BaseTool] | None = None,
    *,
    checkpointer: Any | None = None,
):
    """Build Roberta's coordinator loop.

    Flow::

        START -> oracle -> [tools | END]
                         tools -> oracle

    The optional checkpointer owns LangGraph thread/task execution state. It is
    deliberately separate from future HXMP/HMPX durable-memory integration.
    The default remains stateless so existing deterministic callers do not need
    a thread identifier unless persistence is explicitly enabled.
    """
    active_tools = list(tools) if tools is not None else get_roberta_tools()
    model_with_tools = _bind_tools(model, active_tools)

    builder = StateGraph(RobertaState)
    builder.add_node("oracle", make_oracle_node(model_with_tools))
    builder.add_node("tools", ToolNode(active_tools))

    builder.add_edge(START, "oracle")
    builder.add_conditional_edges(
        "oracle",
        route_after_oracle,
        {
            "tools": "tools",
            END: END,
        },
    )
    builder.add_edge("tools", "oracle")

    return builder.compile(checkpointer=checkpointer)
