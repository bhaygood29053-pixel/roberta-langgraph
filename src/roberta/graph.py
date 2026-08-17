"""Roberta LangGraph coordinator/model-tool loop."""

from collections.abc import Callable, Sequence
from typing import Any, Literal

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from roberta.memory import DurableMemoryStore, build_memory_system_message
from roberta.policy import (
    PolicyRuntimeContext,
    build_policy_system_message,
    deterministic_policy_message,
)
from roberta.prompts import ORACLE_SYSTEM_PROMPT
from roberta.state import RobertaState
from roberta.tools import get_roberta_tools

Route = Literal["tools", "__end__"]
PolicyContextProvider = Callable[[RobertaState], PolicyRuntimeContext | None]


def _bind_tools(model: Any, tools: Sequence[BaseTool]) -> Any:
    """Bind Roberta's specialist/tool registry to a chat-model-like object."""
    if not hasattr(model, "bind_tools"):
        raise TypeError("Roberta model must implement bind_tools(tools).")
    return model.bind_tools(list(tools))


def _policy_provider_failure(exc: Exception) -> AIMessage:
    return AIMessage(
        content=(
            "Policy evaluation is unavailable, so Roberta cannot claim this request "
            "is policy-compliant or authorize a consequential action. "
            f"Policy provider error: {type(exc).__name__}."
        )
    )


def _approval_wrapped_response(response: AIMessage, policy: PolicyRuntimeContext) -> AIMessage:
    """Preserve analysis while structurally keeping approval non-authorizing."""

    notice = deterministic_policy_message(policy.decision)
    content = response.content
    if isinstance(content, str) and content.strip():
        wrapped = f"{notice}\n\nNon-authorizing analysis:\n{content}"
    else:
        wrapped = notice
    return AIMessage(content=wrapped)


def make_oracle_node(
    model_with_tools: Any,
    *,
    memory_store: DurableMemoryStore | None = None,
    memory_limit: int = 6,
    policy_context_provider: PolicyContextProvider | None = None,
) -> Callable[[RobertaState], dict[str, Any]]:
    """Create Roberta's Oracle/coordinator model node.

    When a policy provider is configured, deterministic hard blocks short-circuit
    before the model runs. ``needs_evidence`` may still use read-only specialist
    tools, but a final model answer cannot bypass unresolved evidence. Approval
    states preserve non-authorizing analysis while keeping the approval notice
    structurally attached to the final answer.
    """

    def oracle_node(state: RobertaState) -> dict[str, Any]:
        policy: PolicyRuntimeContext | None = None
        if policy_context_provider is not None:
            try:
                policy = policy_context_provider(state)
            except Exception as exc:
                return {"messages": [_policy_provider_failure(exc)], "status": "error"}

            if policy is not None and policy.decision.status == "blocked":
                return {
                    "messages": [AIMessage(content=deterministic_policy_message(policy.decision))],
                    "status": "complete",
                }

        system_messages = [SystemMessage(content=ORACLE_SYSTEM_PROMPT)]
        if memory_store is not None:
            memory_message = build_memory_system_message(
                memory_store,
                state["messages"],
                limit=memory_limit,
            )
            if memory_message is not None:
                system_messages.append(memory_message)
        if policy is not None:
            system_messages.append(
                build_policy_system_message(policy.compilation, policy.summary)
            )

        response = model_with_tools.invoke([*system_messages, *state["messages"]])
        if not isinstance(response, AIMessage):
            raise TypeError("Roberta model must return an AIMessage.")

        if policy is not None and not response.tool_calls:
            if policy.decision.status == "needs_evidence":
                response = AIMessage(content=deterministic_policy_message(policy.decision))
            elif policy.decision.status == "approval_required":
                response = _approval_wrapped_response(response, policy)

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
    memory_store: DurableMemoryStore | None = None,
    memory_limit: int = 6,
    policy_context_provider: PolicyContextProvider | None = None,
):
    """Build Roberta's coordinator loop.

    Flow::

        START -> oracle -> [tools | END]
                         tools -> oracle

    The optional checkpointer owns LangGraph thread/task execution state.
    The optional durable-memory store owns long-term context and is retrieved
    independently for the current user request. Neither checkpoint history nor
    durable memory is authoritative for freshness-sensitive market facts.

    The optional policy context provider owns deterministic policy compilation /
    evaluation inputs. It can structurally block final model output without
    changing X1 Scout or CMIS/provider authority boundaries.

    All dependencies are optional so existing stateless/no-memory/no-policy
    callers keep their previous deterministic behavior.
    """
    if memory_limit < 0:
        raise ValueError("memory_limit must be non-negative")

    active_tools = list(tools) if tools is not None else get_roberta_tools()
    model_with_tools = _bind_tools(model, active_tools)

    builder = StateGraph(RobertaState)
    builder.add_node(
        "oracle",
        make_oracle_node(
            model_with_tools,
            memory_store=memory_store,
            memory_limit=memory_limit,
            policy_context_provider=policy_context_provider,
        ),
    )
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
