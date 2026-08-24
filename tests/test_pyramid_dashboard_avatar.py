from __future__ import annotations

from pathlib import Path

from roberta.learning.pyramid_dashboard_entry import render_dashboard


def test_dashboard_uses_independent_full_color_roberta_avatar() -> None:
    data = {
        "run_count": 0,
        "mastered_runs": 0,
        "highest_level": 0,
        "latest_run": None,
        "failure_modes": [],
        "failure_event_total": 0,
        "scores": [],
        "latest_accuracy": None,
        "latest_level": None,
        "runs": [],
    }
    html = render_dashboard(data, Path("pyramid.sqlite3"))
    assert "roberta-avatar-full-color" in html
    assert "data:image/jpeg;base64," in html
    assert "filter: none !important" in html
    assert '<div class="avatar" aria-label="Roberta avatar"></div>' not in html
