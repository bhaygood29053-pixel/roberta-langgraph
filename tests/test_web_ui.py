from __future__ import annotations

import threading
import urllib.request

from langchain_core.messages import AIMessage

from roberta.bridge_http import RobertaBridge, create_server
from roberta.web_ui import ROBERTA_WEB_UI_HTML


class FakeGraph:
    def invoke(self, payload):
        return {"messages": [AIMessage(content="ok")], "status": "complete"}


def test_web_ui_is_human_first_v2_experience():
    # Public identity and plain-English positioning.
    assert "ROBERTA — Verified On-Chain Intelligence" in ROBERTA_WEB_UI_HTML
    assert "Ask about a token, trade, wallet, or market move." in ROBERTA_WEB_UI_HTML
    assert "You do not need to know which blockchain tool to use." in ROBERTA_WEB_UI_HTML
    assert "Enter Human Chat" in ROBERTA_WEB_UI_HTML
    assert "Agent / API Access" in ROBERTA_WEB_UI_HTML

    # Six condensed human-facing services.
    assert "Check a Token" in ROBERTA_WEB_UI_HTML
    assert "Compare Tokens" in ROBERTA_WEB_UI_HTML
    assert "Should I Buy or Sell?" in ROBERTA_WEB_UI_HTML
    assert "Check Risk" in ROBERTA_WEB_UI_HTML
    assert "Track Wallets &amp; Big Trades" in ROBERTA_WEB_UI_HTML
    assert "Ask ROBERTA" in ROBERTA_WEB_UI_HTML

    # Human-friendly examples are actionable.
    assert 'data-example="Check AGI."' in ROBERTA_WEB_UI_HTML
    assert "Which looks better right now, XNT or AGI?" in ROBERTA_WEB_UI_HTML
    assert "Should I buy $500 of AGI right now?" in ROBERTA_WEB_UI_HTML
    assert "Could I get stuck trying to sell AGI?" in ROBERTA_WEB_UI_HTML
    assert "Did this transaction move the pool price?" in ROBERTA_WEB_UI_HTML
    assert "How much XNT was burned this week?" in ROBERTA_WEB_UI_HTML

    # The landing page transforms into a dedicated chat workspace.
    assert 'id="workspace"' in ROBERTA_WEB_UI_HTML
    assert "workspaceMode" in ROBERTA_WEB_UI_HTML
    assert "function enterWorkspace" in ROBERTA_WEB_UI_HTML
    assert "function leaveWorkspace" in ROBERTA_WEB_UI_HTML
    assert "robertaWorkspaceMode" in ROBERTA_WEB_UI_HTML
    assert 'id="newChat"' in ROBERTA_WEB_UI_HTML
    assert 'id="clearChat"' in ROBERTA_WEB_UI_HTML
    assert 'id="clearHistory"' in ROBERTA_WEB_UI_HTML
    assert 'id="historyList"' in ROBERTA_WEB_UI_HTML
    assert 'id="backAbout"' in ROBERTA_WEB_UI_HTML

    # Chat history is local to the browser and grouped for humans.
    assert "robertaChatHistoryV2" in ROBERTA_WEB_UI_HTML
    assert "localStorage.getItem" in ROBERTA_WEB_UI_HTML
    assert "localStorage.setItem" in ROBERTA_WEB_UI_HTML
    assert "Today" in ROBERTA_WEB_UI_HTML
    assert "Previous" in ROBERTA_WEB_UI_HTML

    # Answer labels and opinion formatting remain readable.
    assert "Answer labels" in ROBERTA_WEB_UI_HTML
    assert "Evidence" in ROBERTA_WEB_UI_HTML
    assert "Risk" in ROBERTA_WEB_UI_HTML
    assert "Freshness" in ROBERTA_WEB_UI_HTML
    assert "Opinion" in ROBERTA_WEB_UI_HTML
    assert "My recommendation" in ROBERTA_WEB_UI_HTML
    assert "Best evidence against my view" in ROBERTA_WEB_UI_HTML
    assert "What would change my mind" in ROBERTA_WEB_UI_HTML
    assert "formatAssistant" in ROBERTA_WEB_UI_HTML
    assert "statusToken" in ROBERTA_WEB_UI_HTML

    # Architecture and execution boundaries remain intact.
    assert "Scout → CMIS" in ROBERTA_WEB_UI_HTML
    assert "User / Agent → ROBERTA → Chain Scout → CMIS" in ROBERTA_WEB_UI_HTML
    assert "ROBERTA does not execute transactions from this website." in ROBERTA_WEB_UI_HTML
    assert "POST /v1/roberta" in ROBERTA_WEB_UI_HTML
    assert 'fetch(apiUrl("/v1/roberta")' not in ROBERTA_WEB_UI_HTML
    assert "fetch(apiUrl('/v1/roberta')" in ROBERTA_WEB_UI_HTML
    assert "fetch(apiUrl('/healthz')" in ROBERTA_WEB_UI_HTML

    # Legacy technical-dashboard UI is removed rather than hidden.
    assert "Instant X1 Scan" not in ROBERTA_WEB_UI_HTML
    assert "Concentration Warning" not in ROBERTA_WEB_UI_HTML
    assert "Rank X1 Assets" not in ROBERTA_WEB_UI_HTML
    assert "serviceTools" not in ROBERTA_WEB_UI_HTML
    assert "productBand" not in ROBERTA_WEB_UI_HTML
    assert "Current product state" not in ROBERTA_WEB_UI_HTML


def test_bridge_serves_web_ui_and_keeps_roberta_api_path():
    server = create_server(
        host="127.0.0.1",
        port=0,
        bridge=RobertaBridge(FakeGraph()),
        api_key="",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with urllib.request.urlopen(base + "/", timeout=2) as response:
            html = response.read().decode("utf-8")
            assert response.status == 200
            assert response.headers["Content-Type"] == "text/html; charset=utf-8"
            assert "ROBERTA — Verified On-Chain Intelligence" in html
            assert "/v1/roberta" in html
            assert "Check a Token" in html
            assert 'id="workspace"' in html

        with urllib.request.urlopen(base + "/healthz", timeout=2) as response:
            assert response.status == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
