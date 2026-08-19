from roberta.readiness_replay import (
    ReadinessFixtureCMISClient,
    ReplayCaseResult,
    build_replay_report,
)


def test_stale_fixture_preserves_explicit_freshness_failure():
    result = ReadinessFixtureCMISClient("stale").risk_check(chain="x1", asset="AGI")

    assert result["status"] == "partial"
    assert result["evidence_receipt"]["freshness"]["verified"] is False
    assert any(item["code"] == "STALE_EVIDENCE" for item in result["warnings"])


def test_conflict_fixture_does_not_promote_a_risk_conclusion():
    result = ReadinessFixtureCMISClient("conflict").risk_check(
        chain="x1", asset="AGI"
    )

    assert result["risk"] is None
    assert result["evidence_receipt"]["verification"]["status"] == "CONFLICT"
    assert result["evidence_receipt"]["disagreements"]
    assert "risk_level" in result["evidence_receipt"]["unresolved_fields"]


def test_ambiguous_fixture_preserves_multiple_candidates():
    result = ReadinessFixtureCMISClient("ambiguous").market_report(
        chain="x1", asset="AGI"
    )

    assert result["status"] == "ambiguous"
    assert len(result["asset"]["candidates"]) == 2
    assert "asset_identity" in result["evidence_receipt"]["unresolved_fields"]


def test_insufficient_fixture_keeps_proof_weak_and_risk_unknown():
    result = ReadinessFixtureCMISClient("insufficient").risk_check(
        chain="x1", asset="AGI"
    )

    assert result["risk"] is None
    assert (
        result["evidence_receipt"]["verification"]["status"]
        == "INSUFFICIENT_EVIDENCE"
    )
    assert result["proof_score"]["proof_strength"] == "WEAK"


def test_unavailable_and_provider_error_are_distinct_states():
    unavailable = ReadinessFixtureCMISClient("unavailable").market_report(
        chain="x1", asset="AGI"
    )
    provider_error = ReadinessFixtureCMISClient("provider_error").market_report(
        chain="x1", asset="AGI"
    )

    assert unavailable["status"] == "unavailable"
    assert provider_error["status"] == "error"
    assert provider_error["errors"][0]["code"] == "EVAL_PROVIDER_ERROR"


def test_null_field_and_verified_zero_remain_distinguishable():
    missing = ReadinessFixtureCMISClient("null_field").market_report(
        chain="x1", asset="AGI"
    )
    zero = ReadinessFixtureCMISClient("verified_zero").market_report(
        chain="x1", asset="AGI"
    )

    assert missing["data"]["volume_24h"] is None
    assert missing["status"] == "partial"
    assert zero["data"]["volume_24h"] == 0.0
    assert zero["status"] == "ok"
    assert zero["evidence_receipt"]["freshness"]["verified"] is True


def test_replay_report_turns_failed_checks_into_deployment_blockers():
    degraded = [
        ReplayCaseResult(
            case_id="stale",
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
    ]
    freshness = {
        "challenge_id": "checkpoint-hxmp-current-truth",
        "passed": False,
        "checks": {"fresh_scout_cmis_requery": False},
    }

    report = build_replay_report(
        degraded=degraded,
        freshness=freshness,
        metadata={"model": "test"},
    )

    assert report["summary"]["deployment_blockers"] == 2
    assert report["live_market_authority"] is False
    assert report["authority"] == "historical_evaluation_snapshot"
