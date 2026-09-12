from __future__ import annotations

from roberta.web_ui import ROBERTA_WEB_UI_HTML, web_ui_bytes
from roberta.web_ui_beta_feedback import BETA_FEEDBACK_MARKER


def _feedback_submit_function(html: str) -> str:
    start = html.index("async function submitBetaFeedback")
    end = html.index("function showBetaFeedback", start)
    return html[start:end]


def test_beta_feedback_is_conversation_first_and_response_id_gated():
    html = ROBERTA_WEB_UI_HTML
    assert BETA_FEEDBACK_MARKER in html
    assert "d.beta_response_id" in html
    assert "showBetaFeedback(d.beta_response_id)" in html
    assert "Was this useful?" in html
    assert ">Useful<" in html
    assert ">Too technical<" in html
    assert ">Missing evidence<" in html
    assert "data-beta-choice" in html


def test_beta_feedback_posts_only_bounded_categorical_fields():
    html = ROBERTA_WEB_UI_HTML
    feedback = _feedback_submit_function(html)
    assert "fetch(apiUrl('/v1/beta-feedback')" in feedback
    assert "response_id:responseId" in feedback
    assert "helpful:helpful" in feedback
    assert "clarity:clarity" in feedback
    assert "evidence_drill_down:drilled" in feedback

    # Prompt/answer material must never enter the feedback request body.
    for forbidden in (
        "message:",
        "prompt:",
        "reply:",
        "response_text",
        "wallet_address",
        "token_address",
        "raw_evidence",
    ):
        assert forbidden not in feedback


def test_beta_feedback_does_not_create_provider_or_execution_path():
    html = ROBERTA_WEB_UI_HTML
    assert "fetch(apiUrl('/v1/roberta')" in html
    assert "fetch(apiUrl('/v1/beta-feedback')" in html
    assert "fetch(apiUrl('/v1/cmis" not in html
    assert "fetch(apiUrl('/v1/x1-scout" not in html
    assert "executeTrade" not in html
    assert "signTransaction" not in html


def test_live_web_bytes_include_beta_feedback_overlay():
    html = web_ui_bytes().decode("utf-8")
    assert BETA_FEEDBACK_MARKER in html
    assert "Thanks — feedback recorded" in html
    assert "beta_response_id" in html
