from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest
from langchain_core.messages import AIMessage, ToolMessage

from roberta.bridge_http import (
    GATEWAY_ASK_PATH,
    GATEWAY_CAPABILITIES_PATH,
    GATEWAY_CONTRACT,
    RobertaBridge,
    create_server,
)


class FakeGraph:
    def __init__(self, messages):
        self.messages = messages
        self.calls = []

    def invoke(self, payload):
        self.calls.append(payload)
        return {"messages": list(self.messages), "status": "complete"}


def _request(url: str, *, body=None, api_key: str = ""):
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _serve_once(bridge: RobertaBridge, *, api_key: str = ""):
    server = create_server(host="127.0.0.1", port=0, bridge=bridge, api_key=api_key)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_bridge_returns_final_non_tool_ai_message():
    graph = FakeGraph(
        [
            AIMessage(content="", tool_calls=[{"name": "x1_scout_investigate", "args": {}, "id": "1", "type": "tool_call"}]),
            ToolMessage(content="{}", tool_call_id="1", name="x1_scout_investigate"),
            AIMessage(content="I would be cautious about buying $500 of AGI."),
        ]
    )
    bridge = RobertaBridge(graph)

    reply = bridge.ask("Is it ok to purchase $500 of AGI?")

    assert reply == "I would be cautious about buying $500 of AGI."
    assert graph.calls[0]["messages"] == [
        {"role": "user", "content": "Is it ok to purchase $500 of AGI?"}
    ]


def test_bridge_rejects_empty_message():
    with pytest.raises(ValueError, match="non-empty"):
        RobertaBridge(FakeGraph([])).ask("   ")


def test_loopback_http_health_and_message_round_trip():
    bridge = RobertaBridge(FakeGraph([AIMessage(content="Roberta conversational reply")]))
    server, thread = _serve_once(bridge)
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, health = _request(f"{base}/healthz")
        assert status == 200
        assert health == {"service": "roberta_bridge", "status": "ok", "version": 1}

        status, payload = _request(
            f"{base}/v1/roberta",
            body={"message": "Is it ok to purchase $500 of AGI?"},
        )
        assert status == 200
        assert payload == {
            "service": "roberta_bridge",
            "status": "ok",
            "reply": "Roberta conversational reply",
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_bridge_rejects_missing_message():
    bridge = RobertaBridge(FakeGraph([AIMessage(content="unused")]))
    server, thread = _serve_once(bridge)
    try:
        status, payload = _request(
            f"http://127.0.0.1:{server.server_port}/v1/roberta",
            body={"objective": "do not accept tool-routing controls"},
        )
        assert status == 400
        assert payload["error"]["code"] == "message_required"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_bridge_honors_bearer_auth_when_configured():
    bridge = RobertaBridge(FakeGraph([AIMessage(content="authenticated reply")]))
    server, thread = _serve_once(bridge, api_key="secret-token")
    try:
        url = f"http://127.0.0.1:{server.server_port}/v1/roberta"
        status, payload = _request(url, body={"message": "hello"})
        assert status == 401
        assert payload["error"]["code"] == "unauthorized"

        status, payload = _request(
            url,
            body={"message": "hello"},
            api_key="secret-token",
        )
        assert status == 200
        assert payload["reply"] == "authenticated reply"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_non_loopback_bind_requires_api_key():
    with pytest.raises(RuntimeError, match="ROBERTA_API_KEY"):
        create_server(host="0.0.0.0", port=0, bridge=RobertaBridge(FakeGraph([])), api_key="")


def test_gateway_capabilities_are_authenticated_and_read_only():
    bridge = RobertaBridge(FakeGraph([AIMessage(content="unused")]))
    server, thread = _serve_once(bridge, api_key="gateway-secret")
    try:
        base = f"http://127.0.0.1:{server.server_port}"

        status, payload = _request(f"{base}{GATEWAY_CAPABILITIES_PATH}")
        assert status == 401
        assert payload["error"]["code"] == "unauthorized"

        status, payload = _request(
            f"{base}{GATEWAY_CAPABILITIES_PATH}",
            api_key="gateway-secret",
        )
        assert status == 200
        assert payload == {
            "service": "roberta_bridge",
            "status": "ok",
            "gateway_contract": GATEWAY_CONTRACT,
            "mode": "read_only",
            "ask_path": GATEWAY_ASK_PATH,
            "tool_selection_allowed": False,
            "direct_cmis_access": False,
            "execution_authorized": False,
            "private_core_required": True,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_gateway_ask_returns_roberta_reply_with_no_execution_authority():
    bridge = RobertaBridge(FakeGraph([AIMessage(content="Roberta gateway reply")]))
    server, thread = _serve_once(bridge, api_key="gateway-secret")
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, payload = _request(
            f"{base}{GATEWAY_ASK_PATH}",
            body={"message": "Investigate AGI"},
            api_key="gateway-secret",
        )
        assert status == 200
        assert payload == {
            "service": "roberta_bridge",
            "status": "ok",
            "gateway_contract": GATEWAY_CONTRACT,
            "mode": "read_only",
            "reply": "Roberta gateway reply",
            "execution_authorized": False,
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_gateway_rejects_caller_tool_and_routing_controls():
    bridge = RobertaBridge(FakeGraph([AIMessage(content="unused")]))
    server, thread = _serve_once(bridge, api_key="gateway-secret")
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, payload = _request(
            f"{base}{GATEWAY_ASK_PATH}",
            body={
                "message": "Investigate AGI",
                "tool": "cmis",
                "route": "provider-direct",
            },
            api_key="gateway-secret",
        )
        assert status == 400
        assert payload["error"]["code"] == "unsupported_fields"
        assert payload["error"]["fields"] == ["route", "tool"]
        assert bridge._graph.calls == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
