"""Roberta Oracle policy contracts, compiler, and deterministic evaluator."""

from roberta.policy.compiler import POLICY_DOCUMENT_VERSION, compile_policy_memories
from roberta.policy.contracts import (
    EvidenceStatus,
    FreshnessStatus,
    PolicyCompilation,
    PolicyCompileIssue,
    PolicyEffect,
    PolicyEvaluation,
    PolicyEvaluationSummary,
    PolicyFact,
    PolicyKind,
    PolicyOperator,
    PolicyOutcome,
    PolicyRule,
)
from roberta.policy.evaluator import evaluate_policy, evaluate_policy_rule

__all__ = [
    "EvidenceStatus",
    "FreshnessStatus",
    "POLICY_DOCUMENT_VERSION",
    "PolicyCompilation",
    "PolicyCompileIssue",
    "PolicyEffect",
    "PolicyEvaluation",
    "PolicyEvaluationSummary",
    "PolicyFact",
    "PolicyKind",
    "PolicyOperator",
    "PolicyOutcome",
    "PolicyRule",
    "compile_policy_memories",
    "evaluate_policy",
    "evaluate_policy_rule",
]
