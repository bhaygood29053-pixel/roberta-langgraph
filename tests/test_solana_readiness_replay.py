from langchain_core.messages import AIMessage, ToolMessage

from roberta.readiness_solana_replay import (
    DEFAULT_SOLANA_REPLAY_CASES,
    JUP_MINT,
    SolanaReadinessFixtureCMISClient,
    SolanaReplayCaseResult,
    build_solana_replay_report,
    run_solana_degraded_case,
)


class _ScriptedSolanaOracle:
    def bind_tools(self, tools):
        self.tools = list(tools)
        return self

    def invoke(self, messages):
        if not any(isinstance(message, ToolMessage) for message in messages):
            return AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "solana_scout_investigate",
                        "args": {
                            "asset": JUP_MINT,
                            "objective": f"On Solana, is exact mint {JUP_MINT} risky?",
                        },
                        "id": "solana-readiness-call-1",
                        "type": "tool_call",
                    }
                ],
            )
        return AIMessage(
            content=(
                "Recommendation: I cannot verify the current Solana risk because the "
                "available evidence is stale.\n"
                "Risk: UNKNOWN.\n"
                "Evidence quality: WEAK because freshness verification failed."
            )
        )


class _ScriptedSolanaPlanner:
    def invoke(self, messages):
        return AIMessage(content='{"operations":["risk_check"]}')


def test_solana_fixture_preserves_case_sensitive_mint_identity() -> None:
    fixture = SolanaReadinessFixtureCMISClient("stale")

    result = fixture.risk_check(chain="solana", asset=JUP_MINT)

    assert fixture.calls == [
        {"operation": "risk_check", "chain": "solana", "asset": JUP_MINT}
    ]
    assert result["asset"]["symbol"] == JUP_MINT
    assert result["evidence_receipt"]["freshness"]["verified"] is False


def test_solana_replay_profiles_preserve_distinct_uncertainty_states() -> None:
    stale = SolanaReadinessFixtureCMISClient("stale").risk_check(
        chain="solana", asset=JUP_MINT
    )
    conflict = SolanaReadinessFixtureCMISClient("conflict").risk_check(
        chain="solana", asset=JUP_MINT
    )
    insufficient = SolanaReadinessFixtureCMISClient("insufficient").risk_check(
        chain="solana", asset=JUP_MINT
    )
    unavailable = SolanaReadinessFixtureCMISClient("unavailable").risk_check(
        chain="solana", asset=JUP_MINT
    )
    provider_error = SolanaReadinessFixtureCMISClient("provider_error").risk_check(
        chain="solana", asset=JUP_MINT
    )

    assert stale["status"] == "partial"
    assert stale["evidence_receipt"]["freshness"]["verified"] is False
    assert conflict["risk"] is None
    assert conflict["evidence_receipt"]["verification"]["status"] == "CONFLICT"
    assert insufficient["risk"] is None
    assert (
        insufficient["evidence_receipt"]["verification"]["status"]
        == "INSUFFICIENT_EVIDENCE"
    )
    assert insufficient["proof_score"]["proof_strength"] == "WEAK"
    assert unavailable["status"] == "unavailable"
    assert provider_error["status"] == "error"
    assert provider_error["errors"][0]["code"] == "SOLANA_EVAL_PROVIDER_ERROR"


def test_solana_null_and_verified_zero_remain_distinct() -> None:
    missing = SolanaReadinessFixtureCMISClient("null_field").market_report(
        chain="solana", asset=JUP_MINT
    )
    zero = SolanaReadinessFixtureCMISClient("verified_zero").market_report(
        chain="solana", asset=JUP_MINT
    )

    assert missing["data"]["volume_24h"] is None
    assert missing["status"] == "partial"
    assert zero["data"]["volume_24h"] == 0.0
    assert zero["status"] == "ok"
    assert zero["evidence_receipt"]["freshness"]["verified"] is True
    assert zero["evidence_receipt"]["verification"]["status"] == "AGREEMENT"


def test_solana_stale_case_runs_normal_scout_path_and_preserves_mint() -> None:
    models = [_ScriptedSolanaOracle(), _ScriptedSolanaPlanner()]

    def model_factory():
        return models.pop(0)

    result = run_solana_degraded_case(
        model_factory,
        DEFAULT_SOLANA_REPLAY_CASES[0],
    )

    assert result.passed is True
    assert result.checks["service_coverage"] is True
    assert result.checks["chain_isolation"] is True
    assert result.checks["exact_mint_preserved"] is True
    assert result.checks["required_degraded_state_disclosed"] is True
    assert result.checks["risk_evidence_separation"] is True
    assert any(
        event["service"] == "risk_check" and event["chain"] == "solana"
        for event in result.cmis_events
    )


def test_solana_replay_report_promotes_failed_checks_to_blockers() -> None:
    failed = SolanaReplayCaseResult(
        case_id="solana-stale-risk-evidence",
        profile="stale",
        passed=False,
        checks={"required_degraded_state_disclosed": False},
        elapsed_ms=1.0,
        oracle_calls=1,
        oracle_retry_calls=0,
        planner_calls=1,
        cmis_events=(),
        final_answer="Looks fine.",
    )

    report = build_solana_replay_report(degraded=[failed], metadata={"model": "test"})

    assert report["authority"] == "historical_evaluation_snapshot"
    assert report["live_market_authority"] is False
    assert report["summary"]["deployment_blockers"] == 1
    assert report["deployment_blockers"] == [
        {
            "id": "solana-stale-risk-evidence",
            "failed_checks": ["required_degraded_state_disclosed"],
        }
    ]
