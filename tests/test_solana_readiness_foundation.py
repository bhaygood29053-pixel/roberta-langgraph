from pathlib import Path

from roberta.readiness import (
    ReadinessScenario,
    build_readiness_report,
    load_readiness_scenarios,
    skipped_readiness_result,
)
from roberta.readiness_cli import _apply_required_execution_gate


CORPUS = Path("evals/solana_readiness_v1.json")
JUP_MINT = "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN"


def test_solana_readiness_corpus_is_chain_scoped_and_versioned() -> None:
    scenarios = load_readiness_scenarios(CORPUS)

    assert [scenario.scenario_id for scenario in scenarios] == [
        "solana-market-report-exact-mint",
        "solana-tokenomics-exact-mint",
        "solana-risk-exact-mint",
        "solana-symbol-only-identity-fails-closed",
        "solana-cross-chain-isolation",
    ]
    assert all(scenario.requires_solana for scenario in scenarios)

    promoted = {"market_report", "tokenomics", "risk_check"}
    for scenario in scenarios[:4]:
        assert scenario.expected_chains == ("solana",)
        assert set(scenario.expected_services) == {"solana"}
        assert set(scenario.expected_services["solana"]).issubset(promoted)

    cross_chain = scenarios[-1]
    assert set(cross_chain.expected_chains) == {"x1", "solana"}
    assert set(cross_chain.expected_services["solana"]) == {
        "market_report",
        "risk_check",
    }


def test_solana_normal_cases_use_exact_mint_and_symbol_case_does_not_fake_one() -> None:
    scenarios = load_readiness_scenarios(CORPUS)
    by_id = {scenario.scenario_id: scenario for scenario in scenarios}

    for scenario_id in (
        "solana-market-report-exact-mint",
        "solana-tokenomics-exact-mint",
        "solana-risk-exact-mint",
        "solana-cross-chain-isolation",
    ):
        assert JUP_MINT in by_id[scenario_id].turns[0]

    symbol_only = by_id["solana-symbol-only-identity-fails-closed"].turns[0]
    assert "JUP" in symbol_only
    assert JUP_MINT not in symbol_only
    assert "Do not guess a mint" in symbol_only


def test_required_execution_gate_turns_skips_into_deployment_blockers() -> None:
    scenario = ReadinessScenario(
        scenario_id="solana-disabled",
        turns=("On Solana, assess this exact mint.",),
        expected_chains=("solana",),
        expected_services={"solana": ("market_report",)},
        requires_solana=True,
    )
    skipped = skipped_readiness_result(
        scenario,
        reason="ROBERTA_SOLANA_PROVIDER_ENABLED is false",
    )
    report = build_readiness_report(results=[skipped], metadata={})

    blockers = _apply_required_execution_gate(
        report,
        results=[skipped],
        require_no_skips=True,
    )

    assert blockers == 1
    assert report["summary"]["failed"] == 0
    assert report["summary"]["skipped"] == 1
    assert report["summary"]["required_execution_blockers"] == 1
    assert report["deployment_blockers"] == [
        {
            "scenario_id": "solana-disabled",
            "failed_checks": ["scenario_skipped"],
            "reason": "ROBERTA_SOLANA_PROVIDER_ENABLED is false",
        }
    ]


def test_required_execution_gate_is_opt_in() -> None:
    scenario = ReadinessScenario(
        scenario_id="solana-disabled",
        turns=("On Solana, assess this exact mint.",),
        expected_chains=("solana",),
        requires_solana=True,
    )
    skipped = skipped_readiness_result(scenario, reason="disabled")
    report = build_readiness_report(results=[skipped], metadata={})

    blockers = _apply_required_execution_gate(
        report,
        results=[skipped],
        require_no_skips=False,
    )

    assert blockers == 0
    assert report["deployment_blockers"] == []
    assert "required_execution_blockers" not in report["summary"]
