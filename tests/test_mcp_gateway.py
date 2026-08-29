from __future__ import annotations

import asyncio
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from roberta.mcp_gateway import (
    GATEWAY_CONTRACT,
    RobertaMCPGatewayError,
    _validated_upstream_url,
    ask_roberta_via_gateway,
    build_mcp_server,
)


class _GatewayHandler(BaseHTTPRequestHandler):
    response_payload = {
        "service": "roberta_bridge",
        "status": "ok",
        "gateway_contract": GATEWAY_CONTRACT,
        "mode": "read_only",
        "reply": "ROBERTA live reply",
        "execution_authorized": False,
    }
    expected_key = "gateway-secret"
    observed_body = None

    def do_POST(self):  # noqa: N802
        if self.path != "/v1/gateway/ask":
            self.send_response(404)
            self.end_headers()
            return
        if self.headers.get("Authorization") != f"Bearer {self.expected_key}":
            self.send_response(401)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length") or "0")
        type(self).observed_body = json.loads(
            self.rfile.read(length).decode("utf-8")
        )
        body = json.dumps(type(self).response_payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A003
        return


def _serve_gateway(payload=None):
    handler = type("GatewayHandler", (_GatewayHandler,), {})
    if payload is not None:
        handler.response_payload = payload
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/v1/gateway/ask"
    return server, thread, handler, url


def test_mcp_proxy_round_trip_preserves_read_only_contract():
    server, thread, handler, url = _serve_gateway()
    try:
        result = ask_roberta_via_gateway(
            "Investigate AGI",
            upstream_url=url,
            api_key="gateway-secret",
            timeout_seconds=2,
        )
        assert handler.observed_body == {"message": "Investigate AGI"}
        assert result == {
            "gateway_contract": GATEWAY_CONTRACT,
            "mode": "read_only",
            "reply": "ROBERTA live reply",
            "execution_authorized": False,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_mcp_proxy_requires_api_key_before_network_request():
    with pytest.raises(RobertaMCPGatewayError, match="ROBERTA_API_KEY"):
        ask_roberta_via_gateway(
            "hello",
            upstream_url="http://127.0.0.1:9/v1/gateway/ask",
            api_key="",
            timeout_seconds=1,
        )


@pytest.mark.parametrize(
    "url",
    [
        "https://127.0.0.1:8766/v1/gateway/ask",
        "http://example.com/v1/gateway/ask",
        "http://127.0.0.1:8766/v1/roberta",
        "http://user:pass@127.0.0.1:8766/v1/gateway/ask",
        "http://127.0.0.1:8766/v1/gateway/ask?route=cmis",
        "http://127.0.0.1:8766/v1/gateway/ask#provider",
    ],
)
def test_mcp_upstream_is_fail_closed_to_exact_loopback_gateway(url):
    with pytest.raises(RobertaMCPGatewayError):
        _validated_upstream_url(url)


def test_mcp_proxy_rejects_weakened_gateway_contract():
    server, thread, _handler, url = _serve_gateway(
        {
            "service": "roberta_bridge",
            "status": "ok",
            "gateway_contract": GATEWAY_CONTRACT,
            "mode": "read_only",
            "reply": "unsafe",
            "execution_authorized": True,
        }
    )
    try:
        with pytest.raises(RobertaMCPGatewayError, match="execution authority"):
            ask_roberta_via_gateway(
                "hello",
                upstream_url=url,
                api_key="gateway-secret",
                timeout_seconds=2,
            )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_mcp_server_registers_exactly_one_read_only_tool():
    server = build_mcp_server()
    tools = asyncio.run(server.list_tools())

    assert len(tools) == 1
    tool = tools[0]
    assert tool.name == "ask_roberta"
    assert tool.annotations is not None
    assert tool.annotations.read_only_hint is True
    assert tool.annotations.open_world_hint is True
    assert "message" in tool.input_schema.get("properties", {})
    assert set(tool.input_schema.get("required", [])) == {"message"}
