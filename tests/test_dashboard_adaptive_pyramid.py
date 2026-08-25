from __future__ import annotations

import json
from pathlib import Path

from roberta.learning.dashboard_adaptive_pyramid import (
    MASTERY_PLAN_CONTRACT,
    adapt_dashboard_html,
    apply_adaptive_pyramid_plan,
    augment_dashboard_data,
)


def _mastery() -> dict[str, object]:
    return {
        "available": True,
        "curriculum_id": "book001",
        "source_title": "Example Source",
        "mastered_level": 2,
        "current_level": 3,
        "level_state": "training",
    }


def _write_plan(db_path: Path, *, required_levels: int = 8, determined_by: str = "roberta") -> Path:
    root = db_path.parent / "pyramid_mastery_plans"
    root.mkdir(parents=True)
    path = root / "book001.json"
    path.write_text(
        json.dumps(
            {
                "contract": MASTERY_PLAN_CONTRACT,
                "curriculum_id": "book001",
                "determined_by": determined_by,
                "required_levels": required_levels,
                "determination_basis": "Source breadth and reasoning depth require eight mastery levels.",
                "decided_at": "2026-08-24T21:00:00-04:00",
            }
        ),
        encoding="utf-8",
    )
    return path


def test_missing_plan_waits_for_roberta_instead_of_assuming_twenty(tmp_path) -> None:
    db_path = tmp_path / ".roberta" / "pyramid_training.sqlite3"
    mastery = apply_adaptive_pyramid_plan(_mastery(), db_path=db_path)

    assert mastery["required_levels"] is None
    assert mastery["required_levels_declared"] is False
    assert mastery["pyramid_display_levels"] == 3
    assert mastery["mastery_plan_status"] == "awaiting_roberta"


def test_valid_roberta_plan_sets_source_specific_level_count(tmp_path) -> None:
    db_path = tmp_path / ".roberta" / "pyramid_training.sqlite3"
    plan_path = _write_plan(db_path, required_levels=8)

    mastery = apply_adaptive_pyramid_plan(_mastery(), db_path=db_path)
    data = augment_dashboard_data({"highest_level": 2}, mastery)

    assert mastery["required_levels"] == 8
    assert mastery["required_levels_declared"] is True
    assert mastery["pyramid_display_levels"] == 8
    assert mastery["mastery_plan_status"] == "declared"
    assert mastery["mastery_plan_path"] == str(plan_path.resolve())
    assert data["pyramid_total_levels"] == 8
    assert data["pyramid_total_levels_declared"] is True


def test_plan_cannot_claim_fewer_levels_than_already_observed(tmp_path) -> None:
    db_path = tmp_path / ".roberta" / "pyramid_training.sqlite3"
    _write_plan(db_path, required_levels=2)

    mastery = apply_adaptive_pyramid_plan(_mastery(), db_path=db_path)

    assert mastery["required_levels"] is None
    assert mastery["required_levels_declared"] is False
    assert mastery["pyramid_display_levels"] == 3
    assert mastery["mastery_plan_status"] == "invalid"
    assert "below the already observed" in mastery["mastery_plan_detail"]


def test_plan_must_explicitly_be_determined_by_roberta(tmp_path) -> None:
    db_path = tmp_path / ".roberta" / "pyramid_training.sqlite3"
    _write_plan(db_path, required_levels=8, determined_by="builder")

    mastery = apply_adaptive_pyramid_plan(_mastery(), db_path=db_path)

    assert mastery["required_levels_declared"] is False
    assert mastery["mastery_plan_status"] == "invalid"
    assert "determined_by=roberta" in mastery["mastery_plan_detail"]


def test_rendered_dashboard_uses_declared_eight_level_pyramid() -> None:
    mastery = dict(_mastery())
    mastery.update(
        {
            "required_levels": 8,
            "required_levels_declared": True,
            "pyramid_display_levels": 8,
            "mastery_plan_status": "declared",
            "mastery_plan_detail": "Roberta selected eight levels.",
        }
    )
    data = {"highest_level": 2, "latest_run": {"status": "active"}}
    html = """
<style></style>
<div id="highest" class="metric-value">2 / 20</div>
<article><h2>20-Level Pyramid</h2><div class="subtitle">Real Blockchain Reasoning Pyramid progression</div><span id="frontier" class="tag">HIGHEST 2</span><div id="pyramid" class="pyramid"><div class="pyramid-row locked" data-level="20"><span>L20</span><small>LOCKED</small></div></div></article>
<section class="card source-card"><div><span>MASTERED THROUGH</span><strong>L02 / 20</strong></div><div class="source-columns"></div></section>
<script>(function(){var rc=1,hs=2,st='active';function cls(s){return s}function paint(h,s){var f=s==='active'?Math.min(20,h+1):h;}function poll(){var ns='active',nh=2,nr=1;document.getElementById('highest').textContent=nh+' / 20';if(nr!==rc||nh!==hs||ns!==st)location.reload()}paint(hs,st)})();</script>
"""

    rendered = adapt_dashboard_html(html, data, mastery)

    assert "8-Level Adaptive Pyramid" in rendered
    assert "2 / 8" in rendered
    assert "L02 / 8" in rendered
    assert rendered.count('class="pyramid-row') == 8
    assert 'data-level="8"' in rendered
    assert 'data-level="9"' not in rendered
    assert "8 LEVELS REQUIRED" in rendered
    assert "Math.min(ts,h+1)" in rendered
    assert "nh+' / '+(nd?nt:'?')" in rendered


def test_rendered_dashboard_shows_unknown_total_until_roberta_declares() -> None:
    mastery = dict(_mastery())
    mastery.update(
        {
            "required_levels": None,
            "required_levels_declared": False,
            "pyramid_display_levels": 3,
            "mastery_plan_status": "awaiting_roberta",
            "mastery_plan_detail": "Awaiting Roberta.",
        }
    )
    data = {"highest_level": 2, "latest_run": {"status": "active"}}
    html = """
<style></style>
<div id="highest" class="metric-value">2 / 20</div>
<article><h2>20-Level Pyramid</h2><div class="subtitle">Real Blockchain Reasoning Pyramid progression</div><div id="pyramid" class="pyramid"><div class="pyramid-row locked" data-level="20"><span>L20</span><small>LOCKED</small></div></div></article>
<section><span>MASTERED THROUGH</span><strong>L02 / 20</strong><div class="source-columns"></div></section>
"""

    rendered = adapt_dashboard_html(html, data, mastery)

    assert "Adaptive Pyramid" in rendered
    assert "2 / ?" in rendered
    assert "L02 / ?" in rendered
    assert rendered.count('class="pyramid-row') == 3
    assert "AWAITING ROBERTA LEVEL DETERMINATION" in rendered
    assert "20-Level Pyramid" not in rendered
