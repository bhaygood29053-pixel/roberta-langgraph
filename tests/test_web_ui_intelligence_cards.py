from __future__ import annotations

from roberta import chat_ui
from roberta.web_ui import ROBERTA_WEB_UI_HTML
from roberta.web_ui_intelligence_cards import (
    CLEAN_HUMAN_OUTPUT_MARKER,
    INTELLIGENCE_CARD_MARKER,
    apply_intelligence_card_surface,
)


def test_live_web_ui_uses_clean_intelligence_card_renderer() -> None:
    html = ROBERTA_WEB_UI_HTML

    assert INTELLIGENCE_CARD_MARKER in html
    assert "function formatIntelligenceCard" in html
    assert "function intelMetricGrid" in html
    assert "function intelMatters" in html
    assert "function intelNeeds" in html
    assert "function intelEvidence" in html
    assert "function intelBottom" in html

    # Assistant messages now enter the intelligence-card renderer instead of
    # exposing the base Markdown-like formatter directly in the chat bubble.
    assert "if(role==='assistant')d.innerHTML=formatIntelligenceCard(text);" in html
    assert (
        "if(role==='assistant')d.innerHTML=decisionSummary(text)+formatAssistant(text);"
        not in html
    )

    # The first screen is intentionally selective and the rest stays available.
    assert ".metricGrid" in html
    assert "What ROBERTA still needs" in html
    assert "More verified context" in html
    assert "More verified facts" in html
    assert "Analysis only" in html
    assert "Details stay available below" in html


def test_intelligence_card_overlay_is_idempotent() -> None:
    html = ROBERTA_WEB_UI_HTML
    assert apply_intelligence_card_surface(html) == html
    assert html.count(INTELLIGENCE_CARD_MARKER) == 1


def test_clean_human_output_contract_is_systemwide() -> None:
    assert CLEAN_HUMAN_OUTPUT_MARKER in chat_ui.HUMAN_ROBERTA_PRESENTATION_POLICY
    assert CLEAN_HUMAN_OUTPUT_MARKER in chat_ui.SINGLE_ASSET_TERMINAL_STYLE
    assert "up to five key market metrics" in chat_ui.HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "no more than three decision-relevant reasons" in chat_ui.HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "Do not repeat the same WARN" in chat_ui.HUMAN_ROBERTA_PRESENTATION_POLICY


def test_card_renderer_only_reorganizes_roberta_returned_evidence() -> None:
    html = ROBERTA_WEB_UI_HTML

    # The card parser only formats returned text. It does not add a new data path,
    # risk engine, execution path, or provider call in the browser.
    assert "intelMetricFromSegment" in html
    assert "intelInline" in html
    assert "fetch(apiUrl('/v1/roberta')" in html
    assert "fetch(apiUrl('/v1/cmis" not in html
    assert "calculateRisk" not in html
    assert "executeTrade" not in html
    assert "ROBERTA does not execute transactions from this website." in html
