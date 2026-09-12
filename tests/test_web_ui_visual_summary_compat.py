from __future__ import annotations

from roberta import web_ui
from roberta.web_ui_visual_summary_compat import (
    VISUAL_SUMMARY_COMPAT_MARKER,
    VISUAL_SUMMARY_COMPAT_SURFACE,
    apply_visual_summary_narrative_compat,
)


def test_visual_summary_narrative_compat_is_applied_to_live_html() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert VISUAL_SUMMARY_COMPAT_MARKER in html
    assert VISUAL_SUMMARY_COMPAT_SURFACE == "roberta-visual-summary-narrative-compat/v1"
    assert "function vscNarrativeDashboard" in html
    assert "What ROBERTA still needs" in html
    assert "ROBERTA'S TAKE" in html
    assert "returned evidence" in html
    assert "Full ROBERTA response" in html


def test_visual_summary_parser_supports_current_human_answer_shape() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    # These are the narrative sections emitted by the accepted Human ROBERTA
    # presentation contract and seen in the live XNT response.
    assert "What (?:the )?evidence supports" in html
    assert "missing or unverified" in html
    assert "Deterministic risk recommendation" in html
    assert "Evidence quality" in html
    assert "Bottom line" in html
    assert "24h volume" in html
    assert "transactions" in html
    assert "Tokenomics" in html
    assert "Live market freshness" in html
    assert "Holders / concentration" in html


def test_visual_summary_compat_is_idempotent() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert apply_visual_summary_narrative_compat(html) == html
    assert html.count(VISUAL_SUMMARY_COMPAT_MARKER) == 1


def test_visual_summary_compat_preserves_authority_boundary() -> None:
    html = web_ui.ROBERTA_WEB_UI_HTML
    assert "fetch(apiUrl('/v1/cmis" not in html
    assert "calculateRisk" not in html
    assert "executeTrade" not in html
    assert "var _robertaVisualSummaryBaseFormatter=formatIntelligenceCard" in html
