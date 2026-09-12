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
    assert "latest accepted/stored observation; currentness is unverified" in html
    assert "accepted/stored market snapshot; currentness is unverified" in html
    assert "Evidence quality: WEAK" in html


def test_answer_consistency_recognizes_broader_unverified_freshness_phrasing() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert "/freshness (?:is|are) (?:not verified|unverified)/i.test(text)" in html
    assert "current[- ]market freshness check came back NOT_VERIFIED" in html
    assert "snapshot with unverified currentness" in html


def test_answer_consistency_surface_is_idempotent() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert apply_answer_consistency_surface(html) == html


def test_consistency_overlay_runs_after_intelligence_card_surface() -> None:
    source = (ROOT / "src" / "roberta" / "__init__.py").read_text(encoding="utf-8")
    intelligence_index = source.index("apply_intelligence_card_surface(")
    consistency_index = source.index("apply_answer_consistency_surface(")
    assert intelligence_index < consistency_index


def test_consistency_overlay_stays_inside_existing_script_block() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    normalizer_index = html.index("function normalizeRobertaHumanAnswer(value){")
    actions_index = html.index("function answerActions(chatId){")
    script_start = html.rfind("<script", 0, normalizer_index)
    script_end = html.find("</script>", normalizer_index)

    assert script_start >= 0
    assert script_start < normalizer_index < actions_index < script_end
    assert '<script id="roberta-answer-consistency-v1">' not in html
