from __future__ import annotations

from types import SimpleNamespace

from roberta.web_ui import ROBERTA_WEB_UI_HTML as BASE_HTML
from roberta.web_ui_intelligence_cards import apply_intelligence_card_surface
from roberta.web_ui_polarity_colors import (
    POLARITY_COLOR_MARKER,
    POLARITY_OUTPUT_MARKER,
    apply_polarity_color_surface,
    apply_polarity_output_contract,
)


def test_signed_directional_values_render_green_and_red() -> None:
    html = apply_intelligence_card_surface(BASE_HTML)
    html = apply_polarity_color_surface(html)

    assert POLARITY_COLOR_MARKER in html
    assert ".robertaIntelCard .neg" in html
    assert "color:#ff6b78!important" in html
    assert ".robertaIntelCard .pos" in html
    assert "color:#63e6a6!important" in html

    # HTML-tag boundaries are intentional: markdown bold first becomes <strong>,
    # so signed values such as **-16.2%** must still be wrapped by polarity spans.
    assert "[\\s(>]" in html
    assert "([-−]\\d" in html
    assert "([+]\\d" in html
    assert '<span class="neg">$2</span>' in html
    assert '<span class="pos">$2</span>' in html


def test_polarity_surface_is_idempotent() -> None:
    once = apply_polarity_color_surface(apply_intelligence_card_surface(BASE_HTML))
    twice = apply_polarity_color_surface(once)
    assert once == twice


def test_human_contract_requires_explicit_signs_only_for_directional_changes() -> None:
    chat = SimpleNamespace(
        HUMAN_ROBERTA_PRESENTATION_POLICY="base policy",
        SINGLE_ASSET_TERMINAL_STYLE="terminal policy",
    )

    apply_polarity_output_contract(chat)
    assert POLARITY_OUTPUT_MARKER in chat.HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "use + for a positive change and - for a negative change" in chat.HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "+16.2% or -16.2%" in chat.HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "Do not add a positive or negative sign to unsigned facts" in chat.HUMAN_ROBERTA_PRESENTATION_POLICY
    assert "must not infer or calculate a delta" in chat.HUMAN_ROBERTA_PRESENTATION_POLICY

    first = chat.HUMAN_ROBERTA_PRESENTATION_POLICY
    apply_polarity_output_contract(chat)
    assert chat.HUMAN_ROBERTA_PRESENTATION_POLICY == first
