"""Roberta LangGraph coordinator/model-tool loop."""

import json
from collections.abc import Callable, Mapping, Sequence
from typing import Any, Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from roberta.decision_synthesis import (
    build_decision_retry_system_message,
    build_decision_synthesis_system_message,
    decision_response_violation,
    decision_synthesis_failure_text,
)
from roberta.memory import DurableMemoryStore, build_memory_system_message
from roberta.policy import (
    PolicyRuntimeContext,
    build_policy_system_message,
    deterministic_policy_message,
    deterministic_policy_notes,
)
from roberta.pretrade_ux import technical_pretrade_details_requested
from roberta.prompts import ORACLE_SYSTEM_PROMPT
from roberta.state import RobertaState
from roberta.tools import get_roberta_tools

Route = Literal["tools", "__end__"]
PostToolRoute = Literal["oracle", "pretrade_synthesis"]
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


def _append_policy_notes(response: AIMessage, policy: PolicyRuntimeContext) -> AIMessage:
    notes = deterministic_policy_notes(policy.decision)
    if not notes:
        return response
    content = response.content
    base = content if isinstance(content, str) else str(content)
    suffix = "\n".join(f"- {note}" for note in notes)
    return AIMessage(content=f"{base}\n\nDeterministic policy factors:\n{suffix}".strip())


def _approval_wrapped_response(response: AIMessage, policy: PolicyRuntimeContext) -> AIMessage:
    """Preserve analysis while structurally keeping approval non-authorizing."""

    notice = deterministic_policy_message(policy.decision)
    content = response.content
    if isinstance(content, str) and content.strip():
        wrapped = f"{notice}\n\nNon-authorizing analysis:\n{content}"
    else:
        wrapped = notice
    return _append_policy_notes(AIMessage(content=wrapped), policy)


def _latest_user_content(state: RobertaState) -> object:
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            return message.content
    return ""


def _post_specialist_decision_message(state: RobertaState) -> SystemMessage | None:
    """Return a task-specific decision brief only after specialist evidence exists."""

    if not any(isinstance(message, ToolMessage) for message in state["messages"]):
        return None
    content = build_decision_synthesis_system_message(_latest_user_content(state))
    return SystemMessage(content=content) if content is not None else None


def _post_specialist_decision_violation(
    state: RobertaState,
    response: AIMessage,
) -> str | None:
    """Return an obvious recommendation-presentation violation, if any."""

    if response.tool_calls:
        return None
    if not any(isinstance(message, ToolMessage) for message in state["messages"]):
        return None
    return decision_response_violation(_latest_user_content(state), response.content)


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
    structurally attached to the final answer. Material warnings/preferences are
    also appended deterministically so the model cannot omit them.

    After specialist evidence exists, recognized recommendation questions also
    receive a deterministic, task-specific synthesis brief. An obvious raw-dump
    or diagnostic-first final draft gets one constrained rewrite attempt; repeated
    noncompliance fails closed rather than exposing internal service output.
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
        decision_message = _post_specialist_decision_message(state)
        if decision_message is not None:
            system_messages.append(decision_message)

        response = model_with_tools.invoke([*system_messages, *state["messages"]])
        if not isinstance(response, AIMessage):
            raise TypeError("Roberta model must return an AIMessage.")

        violation = _post_specialist_decision_violation(state, response)
        if violation is not None:
            retry_message = SystemMessage(
                content=build_decision_retry_system_message(violation)
            )
            retry_response = model_with_tools.invoke(
                [*system_messages, retry_message, *state["messages"]]
            )
            if not isinstance(retry_response, AIMessage):
                raise TypeError("Roberta model must return an AIMessage.")
            retry_violation = _post_specialist_decision_violation(state, retry_response)
            response = (
                AIMessage(content=decision_synthesis_failure_text())
                if retry_violation is not None
                else retry_response
            )

        if policy is not None and not response.tool_calls:
            if policy.decision.status == "needs_evidence":
                response = AIMessage(content=deterministic_policy_message(policy.decision))
            elif policy.decision.status == "approval_required":
                response = _approval_wrapped_response(response, policy)
            else:
                response = _append_policy_notes(response, policy)

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


def _validated_pretrade_presentation(
    state: RobertaState,
) -> Mapping[str, Any] | None:
    """Return one trusted deterministic X1 Scout pre-trade presentation.

    Multiple simultaneous tool calls stay on the normal Oracle synthesis path;
    this finalizer is intentionally limited to one X1 Scout pre-trade result so
    it cannot accidentally discard another specialist result.
    """

    trailing_tools: list[ToolMessage] = []
    for message in reversed(state["messages"]):
        if isinstance(message, ToolMessage):
            trailing_tools.append(message)
            continue
        break
    if len(trailing_tools) != 1:
        return None

    tool_message = trailing_tools[0]
    if tool_message.name != "x1_scout_investigate":
        return None
    content = tool_message.content
    if not isinstance(content, str) or not content.strip():
        return None
    try:
        report = json.loads(content)
    except json.JSONDecodeError:
        return None
    if not isinstance(report, Mapping):
        return None
    if report.get("specialist") != "x1_scout" or report.get("chain") != "x1":
        return None

    source = report.get("source")
    if not isinstance(source, Mapping):
        return None
    if source.get("service") != "cmis" or source.get("operation") != "pre_trade_check":
        return None

    presentation = report.get("pretrade_presentation")
    if not isinstance(presentation, Mapping):
        return None
    if presentation.get("voice") != "roberta":
        return None
    if presentation.get("cmis_status") != report.get("cmis_status"):
        return None
    conversational = presentation.get("conversational_text")
    technical = presentation.get("technical_text")
    if not isinstance(conversational, str) or not conversational.strip():
        return None
    if not isinstance(technical, str) or not technical.strip():
        return None
    return presentation


def _pretrade_user_text(state: RobertaState) -> str | None:
    presentation = _validated_pretrade_presentation(state)
    if presentation is None:
        return None
    technical = technical_pretrade_details_requested(_latest_user_content(state))
    key = "technical_text" if technical else "conversational_text"
    text = presentation.get(key)
    return text.strip() if isinstance(text, str) and text.strip() else None


def route_after_tools(state: RobertaState) -> PostToolRoute:
    """Use deterministic synthesis only for a validated pre-trade presentation."""

    return "pretrade_synthesis" if _pretrade_user_text(state) is not None else "oracle"


def make_pretrade_synthesis_node(
    *,
    policy_context_provider: PolicyContextProvider | None = None,
) -> Callable[[RobertaState], dict[str, Any]]:
    """Create Roberta's deterministic post-Scout pre-trade finalizer.

    The presentation text comes from X1 Scout's deterministic CMIS-preserving
    formatter, but the conversational/technical mode is chosen from the user's
    actual message and policy is evaluated again after the tool result. This
    keeps Phase 8/9 hard blocks, unresolved-evidence handling, and human-approval
    wrappers structurally authoritative without a second free-form model rewrite.
    """

    def pretrade_synthesis_node(state: RobertaState) -> dict[str, Any]:
        text = _pretrade_user_text(state)
        if text is None:  # defensive; routing should prevent this path
            raise RuntimeError("Validated pre-trade presentation is unavailable.")
        response = AIMessage(content=text)

        if policy_context_provider is not None:
            try:
                policy = policy_context_provider(state)
            except Exception as exc:
                return {"messages": [_policy_provider_failure(exc)], "status": "error"}

            if policy is not None:
                if policy.decision.status == "blocked":
                    response = AIMessage(content=deterministic_policy_message(policy.decision))
                elif policy.decision.status == "needs_evidence":
                    response = AIMessage(content=deterministic_policy_message(policy.decision))
                elif policy.decision.status == "approval_required":
                    response = _approval_wrapped_response(response, policy)
                else:
                    response = _append_policy_notes(response, policy)

        return {"messages": [response], "status": "complete"}

    return pretrade_synthesis_node


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
                         tools -> [pretrade_synthesis | oracle]
                         pretrade_synthesis -> END

    Ordinary specialist results return to the Oracle as before. Recognized
    recommendation families receive a deterministic post-specialist synthesis
    brief in that Oracle call, with one constrained rewrite for obvious raw-dump
    or diagnostic-first failures. A validated single X1 Scout ``pre_trade_check``
    result still takes the stricter deterministic Roberta presentation path.

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
    builder.add_node(
        "pretrade_synthesis",
        make_pretrade_synthesis_node(
            policy_context_provider=policy_context_provider,
        ),
    )

    builder.add_edge(START, "oracle")
    builder.add_conditional_edges(
        "oracle",
        route_after_oracle,
        {
            "tools": "tools",
            END: END,
        },
    )
    builder.add_conditional_edges(
        "tools",
        route_after_tools,
        {
            "pretrade_synthesis": "pretrade_synthesis",
            "oracle": "oracle",
        },
    )
    builder.add_edge("pretrade_synthesis", END)

    return builder.compile(checkpointer=checkpointer)
