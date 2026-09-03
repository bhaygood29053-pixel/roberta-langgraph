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
    assert "CMIS 1.18" in ROBERTA_WEB_UI_HTML
    assert "Warp / bridge-flow intelligence remains evidence-gated" in ROBERTA_WEB_UI_HTML
    assert "Website actions never call CMIS directly" in ROBERTA_WEB_UI_HTML
    assert "execution remains unauthorized" in ROBERTA_WEB_UI_HTML.lower()


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
