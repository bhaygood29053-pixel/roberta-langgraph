"""Behavior-first tests for deterministic memory provenance reconciliation."""

from __future__ import annotations

import pytest

from roberta.memory import (
    MemoryReconciliation,
    ReconciliationObservation,
    reconcile_memory_observations,
)


def observation(
    *,
    value: str,
    observed_at: str | None,
    chain: str | None = "x1",
    scope: str | None = "asset:agi:risk",
    accepted_evidence: bool = False,
) -> ReconciliationObservation:
    return ReconciliationObservation(
        semantic_key="agi:risk_status",
        category="risk_snapshot",
        value=value,
        observed_at=observed_at,
        chain=chain,
        scope=scope,
        accepted_evidence=accepted_evidence,
    )


def assert_no_authority_grant(result: MemoryReconciliation) -> None:
    assert result.current_truth_authorized is False
    assert result.execution_authorized is False


def test_newer_accepted_same_value_supersedes_history() -> None:
    result = reconcile_memory_observations(
        observation(value="WARN", observed_at="2026-08-19T12:00:00Z"),
        observation(
            value="WARN",
            observed_at="2026-08-20T12:00:00Z",
            accepted_evidence=True,
        ),
    )

    assert result.label == "superseded"
    assert result.evidence_sufficient is True
    assert result.requires_fresh_verification is False
    assert_no_authority_grant(result)


def test_newer_accepted_different_value_is_evolution() -> None:
    result = reconcile_memory_observations(
        observation(value="WARN", observed_at="2026-08-19T12:00:00Z"),
        observation(
            value="PASS",
            observed_at="2026-08-20T12:00:00Z",
            accepted_evidence=True,
        ),
    )

    assert result.label == "evolution"
    assert "historically valid" in result.reason
    assert result.requires_fresh_verification is False
    assert_no_authority_grant(result)


def test_same_time_disagreement_is_conflict_and_requests_fresh_verification() -> None:
    result = reconcile_memory_observations(
        observation(value="WARN", observed_at="2026-08-20T12:00:00Z"),
        observation(
            value="PASS",
            observed_at="2026-08-20T12:00:00Z",
            accepted_evidence=True,
        ),
    )

    assert result.label == "conflict"
    assert result.evidence_sufficient is True
    assert result.requires_fresh_verification is True
    assert_no_authority_grant(result)


@pytest.mark.parametrize(
    ("prior_time", "candidate_time"),
    [
        (None, "2026-08-20T12:00:00Z"),
        ("2026-08-19T12:00:00Z", None),
        ("not-a-time", "2026-08-20T12:00:00Z"),
        ("2026-08-19T12:00:00", "2026-08-20T12:00:00Z"),
    ],
)
def test_missing_or_ambiguous_timestamps_are_unknown(
    prior_time: str | None,
    candidate_time: str | None,
) -> None:
    result = reconcile_memory_observations(
        observation(value="WARN", observed_at=prior_time),
        observation(
            value="PASS",
            observed_at=candidate_time,
            accepted_evidence=True,
        ),
    )

    assert result.label == "unknown"
    assert result.evidence_sufficient is False
    assert result.requires_fresh_verification is True
    assert_no_authority_grant(result)


@pytest.mark.parametrize(
    ("prior_chain", "candidate_chain"),
    [
        (None, "x1"),
        ("x1", None),
        (None, None),
        ("", "x1"),
    ],
)
def test_missing_chain_scope_is_unknown(
    prior_chain: str | None,
    candidate_chain: str | None,
) -> None:
    result = reconcile_memory_observations(
        observation(
            value="WARN",
            observed_at="2026-08-19T12:00:00Z",
            chain=prior_chain,
        ),
        observation(
            value="PASS",
            observed_at="2026-08-20T12:00:00Z",
            chain=candidate_chain,
            accepted_evidence=True,
        ),
    )

    assert result.label == "unknown"
    assert "chain scope is required" in result.reason
    assert result.evidence_sufficient is False
    assert result.requires_fresh_verification is True
    assert_no_authority_grant(result)


@pytest.mark.parametrize(
    ("prior_scope", "candidate_scope"),
    [
        (None, "asset:agi:risk"),
        ("asset:agi:risk", None),
        (None, None),
        ("", "asset:agi:risk"),
    ],
)
def test_missing_evidence_scope_is_unknown(
    prior_scope: str | None,
    candidate_scope: str | None,
) -> None:
    result = reconcile_memory_observations(
        observation(
            value="WARN",
            observed_at="2026-08-19T12:00:00Z",
            scope=prior_scope,
        ),
        observation(
            value="PASS",
            observed_at="2026-08-20T12:00:00Z",
            scope=candidate_scope,
            accepted_evidence=True,
        ),
    )

    assert result.label == "unknown"
    assert "evidence scope is required" in result.reason
    assert result.evidence_sufficient is False
    assert result.requires_fresh_verification is True
    assert_no_authority_grant(result)


def test_cross_chain_observations_remain_isolated() -> None:
    result = reconcile_memory_observations(
        observation(value="WARN", observed_at="2026-08-19T12:00:00Z", chain="x1"),
        observation(
            value="PASS",
            observed_at="2026-08-20T12:00:00Z",
            chain="solana",
            accepted_evidence=True,
        ),
    )

    assert result.label == "unknown"
    assert "chain scope differs" in result.reason
    assert result.requires_fresh_verification is True
    assert_no_authority_grant(result)


def test_scope_mismatch_fails_closed_as_unknown() -> None:
    result = reconcile_memory_observations(
        observation(
            value="WARN",
            observed_at="2026-08-19T12:00:00Z",
            scope="asset:agi:risk",
        ),
        observation(
            value="PASS",
            observed_at="2026-08-20T12:00:00Z",
            scope="asset:xnt:risk",
            accepted_evidence=True,
        ),
    )

    assert result.label == "unknown"
    assert "scope differs" in result.reason
    assert result.requires_fresh_verification is True
    assert_no_authority_grant(result)


def test_unaccepted_candidate_cannot_resolve_history() -> None:
    result = reconcile_memory_observations(
        observation(value="WARN", observed_at="2026-08-19T12:00:00Z"),
        observation(
            value="PASS",
            observed_at="2026-08-20T12:00:00Z",
            accepted_evidence=False,
        ),
    )

    assert result.label == "unknown"
    assert "not accepted evidence" in result.reason
    assert result.requires_fresh_verification is True
    assert_no_authority_grant(result)


def test_older_candidate_cannot_rewrite_newer_memory_context() -> None:
    result = reconcile_memory_observations(
        observation(value="PASS", observed_at="2026-08-20T12:00:00Z"),
        observation(
            value="WARN",
            observed_at="2026-08-19T12:00:00Z",
            accepted_evidence=True,
        ),
    )

    assert result.label == "unknown"
    assert "predates" in result.reason
    assert result.requires_fresh_verification is True
    assert_no_authority_grant(result)


def test_invalid_observation_fields_fail_closed() -> None:
    with pytest.raises(ValueError, match="semantic_key"):
        ReconciliationObservation(
            semantic_key="",
            category="risk_snapshot",
            value="WARN",
            observed_at="2026-08-20T12:00:00Z",
        )

    with pytest.raises(ValueError, match="value"):
        ReconciliationObservation(
            semantic_key="agi:risk_status",
            category="risk_snapshot",
            value="",
            observed_at="2026-08-20T12:00:00Z",
        )
