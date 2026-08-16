"""Deterministic tests for Roberta's provider-neutral durable-memory boundary."""

from __future__ import annotations

from typing import Any

import pytest
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage

from roberta.cmis.mock import MockCMISClient
from roberta.graph import build_graph
from roberta.memory import (
    InMemoryDurableMemoryStore,
    MemoryCandidate,
    MemoryRecord,
    format_memory_context,
    retrieve_relevant_memory,
)
from roberta.prompts import ORACLE_SYSTEM_PROMPT
from roberta.runtime import write_durable_memory
from roberta.tools import get_roberta_tools
from tests.fakes import ScriptedOracleModel


class CapturingOracleModel:
    """Model double that records the exact prompt supplied by Roberta."""

    def __init__(self) -> None:
        self.bound_tools: list[Any] = []
        self.invocations: list[list[Any]] = []

    def bind_tools(self, tools: list[Any]) -> "CapturingOracleModel":
        self.bound_tools = list(tools)
        return self

    def invoke(self, messages: list[Any]) -> AIMessage:
        self.invocations.append(list(messages))
        return AIMessage(content="Roberta answered with relevant durable context.")


class CapturingScriptedOracleModel(ScriptedOracleModel):
    """Existing delegation fake plus exact prompt capture."""

    def __init__(self, *, request_tool: bool) -> None:
        super().__init__(request_tool=request_tool)
        self.invocations: list[list[Any]] = []

    def invoke(self, messages: list[Any]) -> AIMessage:
        self.invocations.append(list(messages))
        return super().invoke(messages)


class FailingMemoryStore:
    """Provider double that proves memory failures do not break Roberta."""

    def get(self, key: str) -> MemoryRecord | None:
        raise RuntimeError("memory provider unavailable")

    def upsert(self, record: MemoryRecord) -> None:
        raise RuntimeError("memory provider unavailable")

    def search(self, query: str, *, limit: int = 12) -> list[MemoryRecord]:
        raise RuntimeError("memory provider unavailable")


def _test_tools():
    return get_roberta_tools(cmis_client=MockCMISClient())


@pytest.mark.parametrize(
    "category",
    [
        "identity_role",
        "user_risk_policy",
        "stable_preference",
        "service_definition",
        "specialist_capability",
        "approval_rule",
        "long_term_goal",
        "decision",
    ],
)
def test_stable_memory_categories_write_and_roundtrip(category: str) -> None:
    store = InMemoryDurableMemoryStore()
    result = write_durable_memory(
        store,
        MemoryCandidate(
            key=f"{category}:primary",
            category=category,  # type: ignore[arg-type]
            content=f"Stable {category} content",
            topics=("roberta", "x1"),
            source="test",
            rationale="accepted by permanent-memory policy",
        ),
        observed_at="2026-08-15T22:00:00Z",
    )

    assert result.accepted is True
    assert result.record is not None
    assert result.record.authority == "durable"
    assert result.record.created_at == "2026-08-15T22:00:00Z"
    assert result.record.updated_at == "2026-08-15T22:00:00Z"
    assert store.get(f"{category}:primary") == result.record


@pytest.mark.parametrize(
    "category",
    [
        "market_snapshot",
        "wallet_snapshot",
        "risk_snapshot",
        "tokenomics_snapshot",
    ],
)
def test_freshness_sensitive_snapshots_are_rejected_from_durable_truth(
    category: str,
) -> None:
    store = InMemoryDurableMemoryStore()
    result = write_durable_memory(
        store,
        MemoryCandidate(
            key=f"{category}:agi",
            category=category,  # type: ignore[arg-type]
            content="AGI live value that must not become permanent truth",
            topics=("agi", "x1"),
        ),
        observed_at="2026-08-15T22:00:00Z",
    )

    assert result.accepted is False
    assert result.record is None
    assert "freshness-sensitive" in result.reason
    assert store.all_records() == []


def test_retrieval_injects_only_task_relevant_memory() -> None:
    store = InMemoryDurableMemoryStore()
    write_durable_memory(
        store,
        MemoryCandidate(
            key="policy:x1-risk-limit",
            category="user_risk_policy",
            content="Keep X1 position exposure below the configured portfolio limit.",
            topics=("x1", "risk", "exposure"),
        ),
        observed_at="2026-08-15T22:00:00Z",
    )
    write_durable_memory(
        store,
        MemoryCandidate(
            key="preference:dinner",
            category="stable_preference",
            content="Prefer pasta for dinner.",
            topics=("food", "cooking", "dinner"),
        ),
        observed_at="2026-08-15T22:00:00Z",
    )

    records = retrieve_relevant_memory(
        store,
        "What is my X1 risk exposure policy?",
        limit=6,
    )

    assert [record.key for record in records] == ["policy:x1-risk-limit"]


def test_upsert_preserves_original_creation_time() -> None:
    store = InMemoryDurableMemoryStore()
    candidate = MemoryCandidate(
        key="goal:roberta",
        category="long_term_goal",
        content="Build Roberta as the top-level Oracle.",
        topics=("roberta", "oracle"),
    )
    first = write_durable_memory(
        store,
        candidate,
        observed_at="2026-08-15T21:00:00Z",
    )
    second = write_durable_memory(
        store,
        MemoryCandidate(
            key="goal:roberta",
            category="long_term_goal",
            content="Build Roberta as the top-level Oracle and coordinator.",
            topics=("roberta", "oracle", "coordinator"),
        ),
        observed_at="2026-08-15T22:00:00Z",
    )

    assert first.accepted and second.accepted
    assert second.record is not None
    assert second.record.created_at == "2026-08-15T21:00:00Z"
    assert second.record.updated_at == "2026-08-15T22:00:00Z"


def test_migrated_historical_snapshot_is_explicitly_non_authoritative() -> None:
    record = MemoryRecord(
        key="history:agi-price",
        category="market_snapshot",
        content="AGI price was 1.23 at an earlier observation.",
        topics=("agi", "price", "x1"),
        source="migration",
        authority="historical_context",
        created_at="2026-08-01T12:00:00Z",
        updated_at="2026-08-01T12:00:00Z",
    )

    context = format_memory_context([record])

    assert context is not None
    assert "authority=historical_context" in context
    assert "never establish current" in context
    assert "AGI price was 1.23" in context


def test_graph_injects_relevant_memory_but_not_unrelated_memory() -> None:
    store = InMemoryDurableMemoryStore()
    write_durable_memory(
        store,
        MemoryCandidate(
            key="policy:x1-risk-limit",
            category="user_risk_policy",
            content="Keep X1 exposure below the configured portfolio limit.",
            topics=("x1", "risk", "exposure"),
        ),
        observed_at="2026-08-15T22:00:00Z",
    )
    write_durable_memory(
        store,
        MemoryCandidate(
            key="preference:dinner",
            category="stable_preference",
            content="Prefer pasta for dinner.",
            topics=("food", "dinner"),
        ),
        observed_at="2026-08-15T22:00:00Z",
    )
    model = CapturingOracleModel()
    graph = build_graph(
        model=model,
        tools=_test_tools(),
        memory_store=store,
    )

    result = graph.invoke(
        {
            "messages": [
                {"role": "user", "content": "What is my X1 risk exposure policy?"}
            ],
            "status": "running",
        }
    )

    assert result["status"] == "complete"
    system_text = "\n".join(
        str(message.content)
        for message in model.invocations[0]
        if isinstance(message, SystemMessage)
    )
    assert "policy:x1-risk-limit" in system_text
    assert "configured portfolio limit" in system_text
    assert "preference:dinner" not in system_text
    assert "Prefer pasta" not in system_text


def test_memory_provider_failure_degrades_to_no_memory_context() -> None:
    model = CapturingOracleModel()
    graph = build_graph(
        model=model,
        tools=_test_tools(),
        memory_store=FailingMemoryStore(),
    )

    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": "Who are you?"}],
            "status": "running",
        }
    )

    assert result["status"] == "complete"
    system_messages = [
        message
        for message in model.invocations[0]
        if isinstance(message, SystemMessage)
    ]
    assert len(system_messages) == 1
    assert system_messages[0].content == ORACLE_SYSTEM_PROMPT


def test_current_market_request_still_delegates_with_historical_memory() -> None:
    store = InMemoryDurableMemoryStore(
        [
            MemoryRecord(
                key="history:agi-risk",
                category="risk_snapshot",
                content="Earlier AGI risk status was WARN.",
                topics=("agi", "risk", "x1"),
                source="migration",
                authority="historical_context",
                created_at="2026-08-01T12:00:00Z",
                updated_at="2026-08-01T12:00:00Z",
            )
        ]
    )
    model = CapturingScriptedOracleModel(request_tool=True)
    graph = build_graph(
        model=model,
        tools=_test_tools(),
        memory_store=store,
    )

    result = graph.invoke(
        {
            "messages": [
                {"role": "user", "content": "On X1, check current AGI market risk"}
            ],
            "status": "running",
        }
    )

    tool_messages = [
        message for message in result["messages"] if isinstance(message, ToolMessage)
    ]
    assert len(tool_messages) == 1
    first_system_text = "\n".join(
        str(message.content)
        for message in model.invocations[0]
        if isinstance(message, SystemMessage)
    )
    assert "history:agi-risk" in first_system_text
    assert "authority=historical_context" in first_system_text
    assert '"operation": "risk_check"' in str(tool_messages[0].content)


def test_oracle_prompt_makes_fresh_data_override_durable_memory() -> None:
    prompt = ORACLE_SYSTEM_PROMPT.lower()
    assert "durable memory" in prompt
    assert "authority=historical_context" in prompt
    assert "fresh deterministic specialist/cmis/provider evidence always overrides" in prompt
    assert "current information is required" in prompt


def test_negative_memory_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="memory_limit"):
        build_graph(
            model=CapturingOracleModel(),
            tools=_test_tools(),
            memory_limit=-1,
        )
