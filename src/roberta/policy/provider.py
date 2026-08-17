"""Durable-memory backed Oracle policy context providers."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Protocol

from roberta.memory import DurableMemoryStore, MemoryRecord
from roberta.policy.compiler import compile_policy_memories
from roberta.policy.contracts import PolicyFact, PolicyRule
from roberta.policy.runtime import PolicyRuntimeContext, evaluate_policy_records
from roberta.state import RobertaState

_POLICY_CATEGORY_QUERIES: tuple[tuple[str, str], ...] = (
    ("user_risk_policy", "user risk policy"),
    ("stable_preference", "stable preference"),
    ("approval_rule", "approval rule"),
)


class PolicyFactProvider(Protocol):
    """Application boundary that supplies explicit facts for compiled rules."""

    def __call__(
        self,
        state: RobertaState,
        rules: Sequence[PolicyRule],
    ) -> Mapping[str, PolicyFact]: ...


class PolicyLoadError(RuntimeError):
    """Raised when durable policy cannot be loaded completely/safely."""


def load_policy_records(
    store: DurableMemoryStore,
    *,
    max_records_per_category: int = 64,
) -> tuple[MemoryRecord, ...]:
    """Load bounded deterministic policy categories through the store contract.

    Each query includes the exact durable-memory category tokens, so every record
    in that category is eligible regardless of the current conversational query.
    One extra record is requested to detect truncation. If the configured bound
    is exceeded, policy loading fails closed instead of dropping an unknown rule.
    """

    if max_records_per_category <= 0:
        raise ValueError("max_records_per_category must be greater than zero")

    records_by_key: dict[str, MemoryRecord] = {}
    for category, query in _POLICY_CATEGORY_QUERIES:
        candidates = store.search(query, limit=max_records_per_category + 1)
        matching = [record for record in candidates if record.category == category]
        if len(matching) > max_records_per_category:
            raise PolicyLoadError(
                f"durable policy category {category!r} exceeds configured bound "
                f"of {max_records_per_category} records"
            )
        for record in matching:
            previous = records_by_key.get(record.key)
            if previous is not None and previous != record:
                raise PolicyLoadError(
                    f"durable policy returned conflicting records for key {record.key!r}"
                )
            records_by_key[record.key] = record

    return tuple(records_by_key[key] for key in sorted(records_by_key))


def build_policy_context_provider(
    store: DurableMemoryStore,
    fact_provider: PolicyFactProvider,
    *,
    max_records_per_category: int = 64,
) -> Callable[[RobertaState], PolicyRuntimeContext | None]:
    """Bind HXMP/other durable memory and explicit fact supply to the Oracle graph.

    Free-form Phase 7B risk/preference memories remain ordinary context: when the
    loaded category records contain no explicit policy rules/issues, this returns
    ``None`` and preserves existing no-policy behavior. Store/fact-provider
    failures intentionally propagate so the graph can fail closed.
    """

    def provide(state: RobertaState) -> PolicyRuntimeContext | None:
        records = load_policy_records(
            store,
            max_records_per_category=max_records_per_category,
        )
        if not records:
            return None

        compilation = compile_policy_memories(records)
        if not compilation.rules and not compilation.issues:
            return None
        facts = fact_provider(state, compilation.rules)
        if not isinstance(facts, Mapping):
            raise TypeError("policy fact provider must return a mapping")
        return evaluate_policy_records(records, facts)

    return provide
