from __future__ import annotations

from roberta.web_ui import ROBERTA_WEB_UI_HTML, web_ui_bytes
from roberta.web_ui_current_capabilities import WEBSITE_CAPABILITY_MARKER


def test_current_accepted_capabilities_are_visible_without_internal_service_catalog():
    html = ROBERTA_WEB_UI_HTML

    assert WEBSITE_CAPABILITY_MARKER in html
    assert "Current accepted capabilities" in html
    assert "Pre-trade intelligence" in html
    assert "Wallet relationships" in html
    assert "Tokenized equities &amp; RWAs" in html
    assert "X1 Daily Intelligence Brief" in html
    assert "Large trades &amp; price impact" in html
    assert "Evidence-complete answers" in html

    # Newly accepted capabilities remain conversational entry points rather than
    # exposing implementation service names to website users.
    assert "Give me today's X1 intelligence brief." in html
    assert "What exactly am I buying with this tokenized equity?" in html
    assert "Did these two wallets directly interact?" in html
    assert "cmis_evidence_complete_response/v1" not in html
    assert "CMIS" not in html
    assert "X1 Scout" not in html


def test_live_web_bytes_include_current_capability_surface():
    html = web_ui_bytes().decode("utf-8")
    assert WEBSITE_CAPABILITY_MARKER in html
    assert "Evidence-complete answers" in html
    assert "ROBERTA does not execute transactions from this website." in html
