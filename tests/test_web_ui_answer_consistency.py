from __future__ import annotations

from pathlib import Path

from roberta import web_ui
from roberta.web_ui_answer_consistency import (
    ANSWER_CONSISTENCY_MARKER,
    apply_answer_consistency_surface,
)


ROOT = Path(__file__).resolve().parents[1]


def test_answer_consistency_surface_is_applied_systemwide() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert ANSWER_CONSISTENCY_MARKER in html
    assert "normalizeRobertaHumanAnswer(text)" in html
    assert "latest accepted/stored observations; currentness is unverified" in html
    assert "Evidence quality: proof strength" in html


def test_answer_consistency_surface_is_idempotent() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert apply_answer_consistency_surface(html) == html


def test_consistency_overlay_runs_after_intelligence_card_surface() -> None:
    source = (ROOT / "src" / "roberta" / "__init__.py").read_text(encoding="utf-8")
    intelligence_index = source.index("apply_intelligence_card_surface(")
    consistency_index = source.index("apply_answer_consistency_surface(")
    assert intelligence_index < consistency_index
