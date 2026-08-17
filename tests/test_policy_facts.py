"""Tests for explicit specialist/CMIS evidence -> policy fact adaptation."""

import pytest

from roberta.policy import (
    EvidenceFrame,
    FactPathSpec,
    PolicyFact,
    extract_policy_facts,
    merge_policy_facts,
)


def test_exact_declared_path_becomes_policy_fact_without_field_inference():
    frame = EvidenceFrame(
        payload={"findings": {"data": {"liquidity": 125000}}},
        evidence_status="verified",
        freshness="fresh",
        source="cmis:market_report",
    )

    facts = extract_policy_facts(
        frame,
        [FactPathSpec("market.liquidity_usd", ("findings", "data", "liquidity"))],
    )

    assert facts == {
        "market.liquidity_usd": PolicyFact(
            value=125000,
            evidence_status="verified",
            freshness="fresh",
            source="cmis:market_report",
        )
    }


def test_missing_path_is_omitted_for_evaluator_to_mark_insufficient():
    frame = EvidenceFrame(
        payload={"data": {}},
        evidence_status="verified",
        freshness="fresh",
        source="cmis",
    )

    facts = extract_policy_facts(
        frame,
        [FactPathSpec("market.volume_usd", ("data", "volume_24h"))],
    )

    assert facts == {}


def test_explicit_null_is_not_treated_as_verified_zero_or_false():
    frame = EvidenceFrame(
        payload={"data": {"liquidity": None}},
        evidence_status="verified",
        freshness="fresh",
        source="cmis",
    )

    facts = extract_policy_facts(
        frame,
        [FactPathSpec("market.liquidity_usd", ("data", "liquidity"))],
    )

    fact = facts["market.liquidity_usd"]
    assert fact.value is None
    assert fact.evidence_status == "insufficient_evidence"


def test_adapter_preserves_unverified_and_historical_labels_exactly():
    frame = EvidenceFrame(
        payload={"risk": {"score": 7}},
        evidence_status="unverified",
        freshness="historical",
        source="legacy_snapshot",
    )

    fact = extract_policy_facts(
        frame,
        [FactPathSpec("market.risk_score", ("risk", "score"))],
    )["market.risk_score"]

    assert fact.evidence_status == "unverified"
    assert fact.freshness == "historical"
    assert fact.source == "legacy_snapshot"


def test_duplicate_fact_specs_fail_closed():
    frame = EvidenceFrame(
        payload={"a": 1, "b": 2},
        evidence_status="verified",
        freshness="fresh",
        source="test",
    )

    with pytest.raises(ValueError, match="duplicate policy fact mapping"):
        extract_policy_facts(
            frame,
            [
                FactPathSpec("same", ("a",)),
                FactPathSpec("same", ("b",)),
            ],
        )


def test_merge_rejects_silent_cross_source_fact_replacement():
    a = {"market.value": PolicyFact(value=1, source="source-a")}
    b = {"market.value": PolicyFact(value=1, source="source-b")}

    with pytest.raises(ValueError, match="multiple sources"):
        merge_policy_facts(a, b)


def test_merge_accepts_distinct_fact_keys():
    merged = merge_policy_facts(
        {"market.liquidity": PolicyFact(value=10, source="market")},
        {"portfolio.exposure": PolicyFact(value=20, source="portfolio")},
    )

    assert set(merged) == {"market.liquidity", "portfolio.exposure"}
