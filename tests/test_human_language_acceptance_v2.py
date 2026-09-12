from pathlib import Path

from roberta.human_language_acceptance import (
    HUMAN_LANGUAGE_ACCEPTANCE_CONTRACT,
    evaluate_acceptance_corpus,
    evaluate_human_language,
    load_acceptance_corpus,
)


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "evals" / "human_language_acceptance_v2.json"


def _case(response, *, depth="normal", case_id="fixture"):
    return {
        "id": case_id,
        "service": "pre_trade",
        "response_depth": depth,
        "prompt": "Should I make this trade?",
        "response": response,
        "authority": "evaluation_input_only",
        "live_market_authority": False,
        "execution_authorized": False,
    }


def test_realistic_acceptance_corpus_is_green_and_broad():
    cases = load_acceptance_corpus(CORPUS)
    results = evaluate_acceptance_corpus(CORPUS)

    assert cases
    assert all(result.passed for result in results)
    assert all(result.contract_version == HUMAN_LANGUAGE_ACCEPTANCE_CONTRACT for result in results)
    assert all(result.live_market_authority is False for result in results)
    assert all(result.execution_authorized is False for result in results)

    services = {str(case["service"]) for case in cases}
    assert {
        "instant_x1_scan",
        "pre_trade",
        "smart_route",
        "wallet_relationship",
        "cross_chain_asset_provenance",
        "burn_intelligence",
        "regulatory_intelligence",
        "daily_intelligence_brief",
        "tokenized_equity_human",
    }.issubset(services)

    depths = {str(case["response_depth"]) for case in cases}
    assert {"quick", "normal", "deep_dive"}.issubset(depths)


def test_normal_mode_rejects_engineering_language_that_old_gate_could_miss():
    result = evaluate_human_language(
        _case(
            "The deterministic risk engine returned WARN because the CMIS freshness state is unverified."
        )
    )

    assert result.passed is False
    codes = {failure.code for failure in result.failures}
    assert "technical_leak:cmis" in codes
    assert "technical_leak:deterministic_engine" in codes
    assert "technical_leak:freshness_state" in codes


def test_normal_mode_rejects_report_style_labels_and_internal_identifiers():
    result = evaluate_human_language(
        _case(
            "Risk: UNKNOWN\nEvidence quality: WEAK\nThe verification_evidence_v1 result is incomplete."
        )
    )

    assert result.passed is False
    codes = {failure.code for failure in result.failures}
    assert "report_style_label" in codes
    assert "technical_leak:identifier" in codes


def test_meaning_must_come_before_mint_authority_term():
    bad = evaluate_human_language(
        _case("The mint authority is active, which means more tokens can still be created.")
    )
    good = evaluate_human_language(
        _case("More tokens can still be created — the mint authority is active.", case_id="good")
    )

    assert bad.passed is False
    assert any(
        failure.code == "meaning_after_term:mint_authority"
        for failure in bad.failures
    )
    assert good.passed is True


def test_deep_dive_allows_supported_technical_detail():
    result = evaluate_human_language(
        _case(
            "The Chain Scout retained the CMIS evidence receipt, source contract, RPC provenance, and execution_authorized=false boundary.",
            depth="deep_dive",
        )
    )

    assert result.passed is True


def test_evaluator_is_observational_and_does_not_rewrite_response():
    text = "I wouldn't make this trade yet because I can't confirm the final fill."
    result = evaluate_human_language(_case(text))

    assert result.response == text
