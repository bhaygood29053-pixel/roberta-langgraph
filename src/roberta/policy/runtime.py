"""Provider-neutral runtime composition for Oracle policy."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from roberta.memory import MemoryRecord
from roberta.policy.compiler import compile_policy_memories
from roberta.policy.contracts import (
    PolicyCompilation,
    PolicyEvaluation,
    PolicyEvaluationSummary,
    PolicyFact,
)
from roberta.policy.decision import PolicyDecision, resolve_policy_decision
from roberta.policy.evaluator import evaluate_policy


@dataclass(frozen=True, slots=True)
class PolicyRuntimeContext:
    """Compiled/evaluated policy bundle supplied to the Oracle graph."""

    compilation: PolicyCompilation
    summary: PolicyEvaluationSummary
    decision: PolicyDecision


def evaluate_policy_records(
    records: Iterable[MemoryRecord],
    facts: Mapping[str, PolicyFact],
) -> PolicyRuntimeContext:
    """Compile durable policy records and evaluate them against explicit facts.

    A malformed policy record is not silently ignored at runtime: every compiler
    issue becomes an ``insufficient_evidence`` result so the aggregate decision
    fails closed to ``needs_evidence`` until the durable policy is repaired.
    """

    compilation = compile_policy_memories(records)
    evaluated = evaluate_policy(compilation.rules, facts)
    compile_failures = tuple(
        PolicyEvaluation(
            rule_id=f"compile:{issue.memory_key}",
            kind="evidence_requirement",
            outcome="insufficient_evidence",
            description="Durable policy record could not be compiled safely.",
            fact_key=f"policy.memory:{issue.memory_key}",
            source_memory_key=issue.memory_key,
            reason=issue.reason,
        )
        for issue in compilation.issues
    )
    summary = PolicyEvaluationSummary(results=(*evaluated.results, *compile_failures))
    decision = resolve_policy_decision(summary)
    return PolicyRuntimeContext(
        compilation=compilation,
        summary=summary,
        decision=decision,
    )
