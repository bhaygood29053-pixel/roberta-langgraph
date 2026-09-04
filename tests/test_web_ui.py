from __future__ import annotations

import threading
import urllib.request

from langchain_core.messages import AIMessage

from roberta.bridge_http import RobertaBridge, create_server
from roberta.web_ui import ROBERTA_WEB_UI_HTML


class FakeGraph:
    def invoke(self, payload):
        return {"messages": [AIMessage(content="ok")], "status": "complete"}


def test_web_ui_contains_current_service_surface():
    assert "Instant X1 Scan" in ROBERTA_WEB_UI_HTML
    assert "Burn Intelligence" in ROBERTA_WEB_UI_HTML
    assert "Discovery Intelligence" in ROBERTA_WEB_UI_HTML
    assert "What Changed?" in ROBERTA_WEB_UI_HTML
    assert "Concentration Warning" in ROBERTA_WEB_UI_HTML
    assert "Solana Market Report" in ROBERTA_WEB_UI_HTML
    assert "Solana Tokenomics" in ROBERTA_WEB_UI_HTML
    assert "Solana Risk Assessment" in ROBERTA_WEB_UI_HTML
    assert "ROBERTA_SOLANA_PROVIDER_ENABLED" not in ROBERTA_WEB_UI_HTML
    assert "CMIS 1.18" in ROBERTA_WEB_UI_HTML
    assert "Exact route/config semantics" in ROBERTA_WEB_UI_HTML
    assert "CMIS #441 → #409 → #410 → ROBERTA #314" in ROBERTA_WEB_UI_HTML
    assert "Route-wide 24h/7d/30d bridge-flow totals and verified bridged supply remain unavailable" in ROBERTA_WEB_UI_HTML
    assert "Website actions never call CMIS directly" in ROBERTA_WEB_UI_HTML
    assert "execution remains unauthorized" in ROBERTA_WEB_UI_HTML.lower()
    assert "Human-first output" in ROBERTA_WEB_UI_HTML
    assert "WHAT ROBERTA STILL NEEDS" in ROBERTA_WEB_UI_HTML
    assert "raw snake_case limitation codes" in ROBERTA_WEB_UI_HTML
    assert "humanServicePrompt" in ROBERTA_WEB_UI_HTML
    assert "three highest-priority missing items" in ROBERTA_WEB_UI_HTML
    assert "Do not repeat freshness warnings inside RISK" in ROBERTA_WEB_UI_HTML
    assert "Use EVIDENCE QUALITY instead of a raw evidence-status dump" in ROBERTA_WEB_UI_HTML
    assert "plain-English BOTTOM LINE" in ROBERTA_WEB_UI_HTML
    assert 'id="historyBtn"' in ROBERTA_WEB_UI_HTML
    assert 'id="clearChat"' in ROBERTA_WEB_UI_HTML
    assert 'id="clearHistory"' in ROBERTA_WEB_UI_HTML
    assert 'id="historyPanel"' in ROBERTA_WEB_UI_HTML
    assert "robertaChatHistoryV1" in ROBERTA_WEB_UI_HTML
    assert "localStorage.getItem" in ROBERTA_WEB_UI_HTML
    assert "localStorage.setItem" in ROBERTA_WEB_UI_HTML
    assert "recordUserMessage" in ROBERTA_WEB_UI_HTML
    assert "restoreLatestChat" in ROBERTA_WEB_UI_HTML
    assert ".chatTitle{" in ROBERTA_WEB_UI_HTML
    assert "text-decoration:underline" in ROBERTA_WEB_UI_HTML
    assert ".messages{height:650px;min-height:650px" in ROBERTA_WEB_UI_HTML
    assert "min-height:100px;max-height:260px" in ROBERTA_WEB_UI_HTML
    assert ".statusToken.pass" in ROBERTA_WEB_UI_HTML
    assert ".statusToken.warn" in ROBERTA_WEB_UI_HTML
    assert ".statusToken.block" in ROBERTA_WEB_UI_HTML
    assert ".signedPositive" in ROBERTA_WEB_UI_HTML
    assert ".signedNegative" in ROBERTA_WEB_UI_HTML
    assert ".statusToken.strong" in ROBERTA_WEB_UI_HTML
    assert ".statusToken.moderate" in ROBERTA_WEB_UI_HTML
    assert ".statusToken.weak" in ROBERTA_WEB_UI_HTML
    assert "|STRONG|MODERATE|WEAK" in ROBERTA_WEB_UI_HTML
    assert "formatAssistant" in ROBERTA_WEB_UI_HTML
    assert 'id="robertaHeroCanvas"' in ROBERTA_WEB_UI_HTML
    assert "function profilePoint" in ROBERTA_WEB_UI_HTML
    assert "prefers-reduced-motion" in ROBERTA_WEB_UI_HTML
    assert "ResizeObserver" in ROBERTA_WEB_UI_HTML
    assert "document.hidden" in ROBERTA_WEB_UI_HTML
    assert "execution_authorized=false" in ROBERTA_WEB_UI_HTML
    assert "ROBERTA Opinion v1" in ROBERTA_WEB_UI_HTML
    assert "roberta_opinion/v1" in ROBERTA_WEB_UI_HTML
    assert "My recommendation: <TOKEN>" in ROBERTA_WEB_UI_HTML
    assert "Best evidence against my view" in ROBERTA_WEB_UI_HTML
    assert "What would change my mind" in ROBERTA_WEB_UI_HTML
    assert "ROBERTA may disagree with the user" in ROBERTA_WEB_UI_HTML
    assert "id:'opinion'" in ROBERTA_WEB_UI_HTML
    assert ".opinionLine{" in ROBERTA_WEB_UI_HTML


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

        with urllib.request.urlopen(base + "/healthz", timeout=2) as response:
            assert response.status == 200
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
