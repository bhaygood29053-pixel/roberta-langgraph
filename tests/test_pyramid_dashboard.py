from __future__ import annotations

from roberta.learning.pyramid import evaluate_level
from roberta.learning.pyramid_dashboard import load_dashboard_data, render_dashboard
from roberta.learning.training_ledger import PyramidTrainingLedger


def test_dashboard_reads_training_ledger_without_mutation(tmp_path) -> None:
    path = tmp_path / "pyramid.sqlite3"
    ledger = PyramidTrainingLedger(path)
    run_id = ledger.start_run("book001", "seed", run_id="rp_dashboard")
    result = evaluate_level(
        level=1,
        total_questions=300,
        correct_questions=270,
        integrity_total=50,
        integrity_correct=50,
        boss_passed=True,
    )
    ledger.record_level_result(run_id, result)
    ledger.record_failures(run_id, 1, {"F03": 3})

    before = path.stat().st_mtime_ns
    data = load_dashboard_data(path, "book001")
    after = path.stat().st_mtime_ns

    assert before == after
    assert data["highest_level"] == 1
    assert data["latest_level"] == 1
    assert data["latest_accuracy"] == 0.9
    assert data["failure_event_total"] == 3
    assert data["failure_modes"][0]["failure_code"] == "F03"

    html = render_dashboard(data, path)
    assert "Roberta Learning Command Center" in html
    assert "20-Level Pyramid" in html
    assert "PYRAMID LEDGER" in html
    assert "/api/summary" in html
    assert "/assets/roberta.svg" in html
    assert "F03" in html
