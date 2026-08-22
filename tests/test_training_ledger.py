from __future__ import annotations

from roberta.learning.pyramid import evaluate_level
from roberta.learning.training_ledger import PyramidTrainingLedger


def test_ledger_tracks_progress_failure_and_history(tmp_path) -> None:
    ledger = PyramidTrainingLedger(tmp_path / "pyramid.sqlite3")
    run_id = ledger.start_run("book001", "seed-1", run_id="rp_test_1")

    level_one = evaluate_level(
        level=1,
        total_questions=1000,
        correct_questions=900,
        integrity_total=50,
        integrity_correct=49,
        boss_passed=True,
    )
    ledger.record_level_result(run_id, level_one)
    ledger.record_failures(run_id, 1, {"F03": 4, "F09": 2})

    level_two = evaluate_level(
        level=2,
        total_questions=1000,
        correct_questions=700,
        integrity_total=50,
        integrity_correct=48,
        boss_passed=True,
    )
    ledger.record_level_result(run_id, level_two)
    ledger.record_failures(run_id, 2, {"F03": 7})

    summary = ledger.summary("book001")
    assert summary["run_count"] == 1
    assert summary["highest_level"] == 1
    assert summary["mastered_runs"] == 0
    assert summary["latest_run"]["status"] == "failed"
    assert summary["failure_modes"][0] == {"failure_code": "F03", "total": 11}

    new_run = ledger.start_run("book001", "seed-2", run_id="rp_test_2")
    assert new_run == "rp_test_2"
    assert ledger.run_history("book001")[0]["status"] == "active"


def test_ledger_rejects_skipped_level(tmp_path) -> None:
    ledger = PyramidTrainingLedger(tmp_path / "pyramid.sqlite3")
    run_id = ledger.start_run("book001", "seed-1")
    level_two = evaluate_level(
        level=2,
        total_questions=1000,
        correct_questions=900,
        integrity_total=50,
        integrity_correct=50,
        boss_passed=True,
    )

    try:
        ledger.record_level_result(run_id, level_two)
    except ValueError as exc:
        assert "expected level 1" in str(exc)
    else:
        raise AssertionError("skipping Level 1 must fail")
