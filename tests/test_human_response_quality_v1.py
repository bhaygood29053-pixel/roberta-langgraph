from __future__ import annotations

import copy
from collections import Counter
from pathlib import Path

import pytest

from roberta.human_response_quality import (
    HUMAN_RESPONSE_QUALITY_CONTRACT,
    evaluate_human_response_case,
    evaluate_human_response_corpus,
    load_human_response_corpus,
    render_manual_review_markdown,
    validate_human_response_case,
)

CORPUS = Path("evals/human_response_learning_v1.json")


def _cases():
    return load_human_response_corpus(CORPUS)


def _case(scenario_id: str):
    return next(case for case in _cases() if case["id"] == scenario_id)


def test_human_response_learning_corpus_has_100_scenarios_and_required_families():
    cases = _cases()

    assert len(cases) == 100
    counts = Counter(case["family"] for case in cases)
    assert counts == {
        "token_assessment": 10,
        "risk_evidence": 8,
        "pretrade": 10,
        "comparison": 8,
        "large_trade_price_impact": 8,
        "history_what_changed": 8,
        "bridge_cross_chain": 8,
        "concentration": 6,
        "burn": 6,
        "regulatory": 8,
        "data_quality": 8,
        "followup_continuity": 12,
    }


def test_corpus_is_evaluation_only_and_cannot_be_live_market_authority():
    cases = _cases()

    for case in cases:
        assert case["authority"] == "evaluation_input_only"
        assert case["live_market_authority"] is False
        assert case["execution_authorized"] is False
        assert case["fixture_scope"] == "synthetic_non_live"


def test_all_reference_candidates_pass_every_quality_dimension():
    cases = _cases()

    report = evaluate_human_response_corpus(cases)

    assert report["contract_version"] == HUMAN_RESPONSE_QUALITY_CONTRACT
    assert report["authority"] == "evaluation_result_only"
    assert report["live_market_authority"] is False
    assert report["execution_authorized"] is False
    assert report["summary"]["total"] == 100
    assert report["summary"]["passed"] == 100
    assert report["summary"]["failed"] == 0
    assert report["summary"]["hard_failed"] == 0
    assert report["failures"] == []
    assert all(
        all(result["checks"].values())
        for result in report["results"]
    )


def test_wrong_recommendation_fails_with_actionable_reason():
    case = _case("token-01-x1x")
    candidate = copy.deepcopy(case["reference_candidate"])
    candidate["recommendation"] = "BUY"

    result = evaluate_human_response_case(case, candidate)

    assert result.passed is False
    assert result.hard_passed is False
    assert result.checks["correct_opinion_family"] is False
    assert any(
        failure.code == "recommendation_family_mismatch"
        and failure.dimension == "correct_opinion_family"
        and failure.severity == "hard"
        for failure in result.failures
    )


def test_missing_primary_driver_and_change_condition_are_separate_failures():
    case = _case("token-01-x1x")
    candidate = copy.deepcopy(case["reference_candidate"])
    candidate["response"] = (
        "I wouldn't trade X1X right now. "
        "The freeze authority is disabled. "
        "I'm still uncertain because market freshness is not fully verified. "
        "Analysis only — no trade execution."
    )

    result = evaluate_human_response_case(case, candidate)

    assert result.checks["primary_driver_surfaced"] is False
    assert result.checks["what_would_change_my_mind"] is False
    codes = {failure.code for failure in result.failures}
    assert "primary_driver_missing" in codes
    assert "change_mind_condition_missing" in codes


def test_internal_jargon_dump_is_a_quality_failure():
    case = _case("risk-02-unknown-weak")
    candidate = copy.deepcopy(case["reference_candidate"])
    candidate["response"] += (
        "\n\nchain_scout_cmis says risk_check returned UNKNOWN "
        "under roberta_human_response/v1."
    )

    result = evaluate_human_response_case(case, candidate)

    assert result.checks["no_jargon_dump"] is False
    assert any(
        failure.code == "internal_jargon_exposed"
        and failure.severity == "quality"
        for failure in result.failures
    )


def test_missing_uncertainty_is_a_hard_failure():
    case = _case("data-quality-01-stale")
    candidate = copy.deepcopy(case["reference_candidate"])
    candidate["response"] = (
        "I don't have enough verified evidence to make a strong AGI call yet. "
        "The biggest reason is that the live market snapshot is stale. "
        "Stale evidence cannot be called current. "
        "On the other side, some useful partial evidence is available. "
        "What would change my mind: fresh, independently verified evidence for the missing point. "
        "Analysis only — no trade execution."
    )
    # Remove all accepted uncertainty anchors including stale/not current wording.
    candidate["response"] = candidate["response"].replace("stale", "old").replace(
        "cannot be called current", "has limited usefulness"
    )

    result = evaluate_human_response_case(case, candidate)

    assert result.checks["uncertainty_fidelity"] is False
    assert any(
        failure.code == "uncertainty_missing"
        and failure.severity == "hard"
        for failure in result.failures
    )


def test_unsupported_large_trade_causality_is_a_hard_failure():
    case = _case("large-trade-01-agi")
    candidate = copy.deepcopy(case["reference_candidate"])
    candidate["response"] = (
        "I can prove this wallet caused the whole market move. "
        + candidate["response"]
    )

    result = evaluate_human_response_case(case, candidate)

    assert result.checks["no_unsupported_causality"] is False
    assert any(
        failure.code == "unsupported_causality"
        and failure.severity == "hard"
        for failure in result.failures
    )


def test_execution_claim_is_a_hard_failure():
    case = _case("pretrade-01-agi-buy-500")
    candidate = copy.deepcopy(case["reference_candidate"])
    candidate["response"] += "\n\nI placed your trade."
    candidate["runtime"]["execution_authorized"] = True

    result = evaluate_human_response_case(case, candidate)

    assert result.checks["no_execution_authority"] is False
    assert any(
        failure.code == "execution_boundary_violation"
        and failure.severity == "hard"
        for failure in result.failures
    )


def test_trade_resize_requires_fresh_evidence_and_exact_stable_referents():
    case = _case("followup-02-resize-50")
    candidate = copy.deepcopy(case["reference_candidate"])

    assert evaluate_human_response_case(case, candidate).passed is True

    candidate["runtime"]["fresh_evidence_requested"] = False
    result = evaluate_human_response_case(case, candidate)
    assert result.checks["continuity_fidelity"] is False
    assert any(
        failure.code == "continuity_or_freshness_boundary_failed"
        for failure in result.failures
    )

    candidate = copy.deepcopy(case["reference_candidate"])
    candidate["runtime"]["resolved_amount_usd"] = 500
    result = evaluate_human_response_case(case, candidate)
    assert result.checks["continuity_fidelity"] is False


def test_why_followup_does_not_require_fresh_lookup_but_cannot_inherit_market_values():
    case = _case("followup-01-why")
    candidate = copy.deepcopy(case["reference_candidate"])

    result = evaluate_human_response_case(case, candidate)
    assert result.passed is True
    assert candidate["runtime"]["fresh_evidence_requested"] is False

    candidate["runtime"]["market_values_inherited"] = True
    result = evaluate_human_response_case(case, candidate)
    assert result.checks["continuity_fidelity"] is False


def test_explicit_chain_switch_requires_solana_context_without_x1_market_inheritance():
    case = _case("followup-07-chain-switch")
    candidate = copy.deepcopy(case["reference_candidate"])

    result = evaluate_human_response_case(case, candidate)
    assert result.passed is True
    assert candidate["runtime"]["resolved_chain"] == "solana"
    assert candidate["runtime"]["market_values_inherited"] is False

    candidate["runtime"]["resolved_chain"] = "x1"
    result = evaluate_human_response_case(case, candidate)
    assert result.checks["continuity_fidelity"] is False


def test_manual_review_markdown_surfaces_one_example_per_family():
    cases = _cases()

    review = render_manual_review_markdown(cases, per_family=1)

    assert review.startswith("# Human Response Learning v1")
    assert "not current market facts" in review
    assert review.count("## ") == 12
    assert "Reference ROBERTA response:" in review
    assert "Hard PASS: true" in review
    assert "continuity_fidelity=PASS" in review


def test_case_validation_rejects_live_market_authority():
    case = copy.deepcopy(_case("token-01-x1x"))
    case["live_market_authority"] = True

    with pytest.raises(ValueError, match="live market authority"):
        validate_human_response_case(case)


def test_case_validation_rejects_execution_authority():
    case = copy.deepcopy(_case("token-01-x1x"))
    case["execution_authorized"] = True

    with pytest.raises(ValueError, match="authorize execution"):
        validate_human_response_case(case)
