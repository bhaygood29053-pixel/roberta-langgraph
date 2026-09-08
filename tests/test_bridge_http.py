from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from roberta.bridge_http import (
    EVALUATION_TELEMETRY_VERSION,
    EVALUATION_TELEMETRY_V2,
    RobertaBridge,
    create_server,
)


class FakeGraph:
    def __init__(self, messages):
        self.messages = messages
        self.calls = []

    def invoke(self, payload, config=None):
        self.calls.append({"payload": payload, "config": config})
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
    assert graph.calls[0]["payload"]["messages"] == [
        {"role": "user", "content": "Is it ok to purchase $500 of AGI?"}
    ]
    assert graph.calls[0]["config"] is None


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


def test_bridge_thread_id_uses_checkpoint_config_without_rewriting_user_message():
    graph = FakeGraph([AIMessage(content="threaded reply")])
    bridge = RobertaBridge(graph)

    reply = bridge.ask("What about $50 instead?", thread_id="chat-123")

    assert reply == "threaded reply"
    assert graph.calls[0]["payload"]["messages"] == [
        {"role": "user", "content": "What about $50 instead?"}
    ]
    assert graph.calls[0]["config"] == {
        "configurable": {"thread_id": "chat-123"}
    }


def test_http_bridge_accepts_and_echoes_thread_id():
    graph = FakeGraph([AIMessage(content="continued")])
    bridge = RobertaBridge(graph)
    server, thread = _serve_once(bridge)
    try:
        url = f"http://127.0.0.1:{server.server_port}/v1/roberta"
        status, payload = _request(
            url,
            body={"message": "Why?", "thread_id": "chat-why"},
        )
        assert status == 200
        assert payload == {
            "service": "roberta_bridge",
            "status": "ok",
            "reply": "continued",
            "thread_id": "chat-why",
        }
        assert graph.calls[0]["config"] == {
            "configurable": {"thread_id": "chat-why"}
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize("thread_id", ["", "   ", "x" * 129])
def test_http_bridge_rejects_invalid_thread_id(thread_id):
    bridge = RobertaBridge(FakeGraph([AIMessage(content="unused")]))
    server, thread = _serve_once(bridge)
    try:
        status, payload = _request(
            f"http://127.0.0.1:{server.server_port}/v1/roberta",
            body={"message": "hello", "thread_id": thread_id},
        )
        assert status == 400
        assert payload["error"]["code"] == "invalid_thread_id"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_bridge_evaluation_mode_exposes_only_accepted_final_structures():
    final = AIMessage(
        content="I would avoid XNT for now.",
        additional_kwargs={
            "roberta_human_response_decision": {
                "contract_version": "roberta_human_response_decision/v1",
                "subject": {"chain": "x1", "symbol": "XNT"},
                "recommendation": "AVOID",
                "conviction": "MODERATE",
                "evidence_quality": "LOW",
                "primary_decision_driver": {
                    "fact_ref": "facts.market.liquidity_usd",
                    "source_value": 1250.0,
                },
                "evidence_profile": [
                    {
                        "dimension": "freshness",
                        "state": "VERIFIED",
                        "source_ref": "facts.market.freshness.freshness_state",
                        "source_value": "VERIFIED",
                    }
                ],
                "facts_authority": "chain_scout_cmis",
                "judgment_authority": "roberta",
                "execution_authorized": False,
            },
            "roberta_opinion": {
                "contract_version": "roberta_opinion/v1",
                "recommendation": "AVOID",
                "facts_authority": "chain_scout_cmis",
                "judgment_authority": "roberta",
                "execution_authorized": False,
            },
            "roberta_claim_integrity": {
                "contract_version": "roberta_claim_integrity/v1",
                "status": "PASS",
                "source_contracts": ["instant_x1_scan_product_view/v1"],
                "facts_authority": "chain_scout_cmis",
                "judgment_authority": "roberta",
                "provider_truth_certified": False,
                "all_natural_language_claims_certified": False,
                "execution_authorized": False,
            },
            "roberta_human_renderer": {
                "contract_version": "roberta_human_renderer/v1",
                "facts_authority": "chain_scout_cmis",
                "judgment_authority": "roberta",
                "execution_authorized": False,
            },
            "unrelated_internal_metadata": {
                "must_not_be_exposed": True,
            },
        },
    )
    graph = FakeGraph([final])
    bridge = RobertaBridge(graph)
    server, thread = _serve_once(bridge)
    try:
        url = f"http://127.0.0.1:{server.server_port}/v1/roberta"
        status, payload = _request(
            url,
            body={
                "message": "Should I buy XNT?",
                "evaluation_mode": EVALUATION_TELEMETRY_VERSION,
            },
        )
        assert status == 200
        assert payload["reply"] == "I would avoid XNT for now."
        assert payload["evaluation_telemetry_version"] == EVALUATION_TELEMETRY_VERSION
        evidence = payload["evaluation_evidence"]
        assert set(evidence) == {
            "human_response_decision",
            "opinion",
            "claim_integrity",
            "human_renderer",
        }
        assert evidence["claim_integrity"]["status"] == "PASS"
        assert payload["execution_authorized"] is False
        assert payload["evidence_freshness"]["state"] == "VERIFIED"
        assert payload["evidence_provenance"]["source_contracts"] == [
            "instant_x1_scan_product_view/v1"
        ]
        claims = payload["claims"]
        assert {
            "name": "recommendation",
            "evidence_path": "human_response_decision.recommendation",
            "value": "AVOID",
        } in claims
        assert {
            "name": "primary_decision_driver",
            "evidence_path": (
                "human_response_decision.primary_decision_driver.source_value"
            ),
            "value": 1250.0,
        } in claims
        assert len(graph.calls) == 1
        assert "unrelated_internal_metadata" not in json.dumps(payload)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_bridge_evaluation_mode_stays_unqualified_without_structured_final_evidence():
    bridge = RobertaBridge(FakeGraph([AIMessage(content="Pure factual prose.")]))
    server, thread = _serve_once(bridge)
    try:
        url = f"http://127.0.0.1:{server.server_port}/v1/roberta"
        status, payload = _request(
            url,
            body={
                "message": "What is XNT?",
                "evaluation_mode": EVALUATION_TELEMETRY_VERSION,
            },
        )
        assert status == 200
        assert payload["evaluation_evidence"] == {}
        assert payload["claims"] == []
        assert payload["evidence_freshness"]["state"] == "UNAVAILABLE"
        assert payload["execution_authorized"] is False
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_bridge_rejects_unknown_evaluation_mode():
    graph = FakeGraph([AIMessage(content="unused")])
    bridge = RobertaBridge(graph)
    server, thread = _serve_once(bridge)
    try:
        status, payload = _request(
            f"http://127.0.0.1:{server.server_port}/v1/roberta",
            body={
                "message": "hello",
                "evaluation_mode": "unversioned-debug-mode",
            },
        )
        assert status == 400
        assert payload["error"]["code"] == "invalid_evaluation_mode"
        assert graph.calls == []
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_bridge_evaluation_v2_projects_current_turn_factual_scout_evidence():
    report = {
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": "XNT",
        "asset": {"symbol": "XNT", "mint": "verified-mint"},
        "source": {"service": "cmis", "operation": "market_report"},
        "cmis_status": "ok",
        "observed_at_iso": "2026-09-08T16:00:00Z",
        "findings": {
            "data": {
                "price": 0.0123,
                "liquidity": 5000.0,
                "volume_24h": 900.0,
            },
            "risk": None,
        },
        "confidence": {"verification_status": "VERIFIED"},
        "evidence_context": {"freshness_verified": True},
        "freshness": {
            "contract_version": "cmis_response_freshness/v1",
            "state": "VERIFIED",
        },
        "sources": [{"provider": "must_not_be_exposed"}],
        "warnings": [{"message": "must_not_be_exposed"}],
        "errors": [],
    }
    graph = FakeGraph(
        [
            HumanMessage(content="Give me the current verified X1 market report for XNT."),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "x1_scout_investigate",
                        "args": {},
                        "id": "1",
                        "type": "tool_call",
                    }
                ],
            ),
            ToolMessage(
                content=json.dumps(report),
                tool_call_id="1",
                name="x1_scout_investigate",
            ),
            AIMessage(content="XNT has a verified current market observation."),
        ]
    )
    bridge = RobertaBridge(graph)
    server, thread = _serve_once(bridge)
    try:
        url = f"http://127.0.0.1:{server.server_port}/v1/roberta"
        status, payload = _request(
            url,
            body={
                "message": "Give me the current verified X1 market report for XNT.",
                "evaluation_mode": EVALUATION_TELEMETRY_V2,
            },
        )
        assert status == 200
        assert payload["evaluation_telemetry_version"] == EVALUATION_TELEMETRY_V2
        factual = payload["evaluation_evidence"]["factual_response"]
        assert factual["contract_version"] == "roberta_evaluation_factual_evidence/v1"
        assert factual["source"] == {"service": "cmis", "operation": "market_report"}
        assert factual["findings"]["data"]["price"] == 0.0123
        assert "sources" not in factual
        assert "warnings" not in factual

        integrity = payload["evaluation_evidence"]["evaluation_projection_integrity"]
        assert integrity["contract_version"] == "roberta_evaluation_projection_integrity/v1"
        assert integrity["status"] == "PASS"
        assert integrity["provider_truth_certified"] is False
        assert integrity["all_natural_language_claims_certified"] is False
        assert integrity["execution_authorized"] is False

        assert {
            "name": "factual_data_price",
            "evidence_path": "factual_response.findings.data.price",
            "value": 0.0123,
        } in payload["claims"]
        assert payload["evidence_freshness"]["state"] == "VERIFIED"
        assert payload["evidence_provenance"]["factual_projection"][
            "second_cmis_query_performed"
        ] is False
        assert payload["evidence_provenance"]["factual_projection"][
            "prose_claim_inference_performed"
        ] is False
        assert payload["execution_authorized"] is False
        assert len(graph.calls) == 1
        assert "must_not_be_exposed" not in json.dumps(payload)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_bridge_evaluation_v2_does_not_reuse_prior_turn_scout_evidence():
    prior_report = {
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": "XNT",
        "asset": {"symbol": "XNT"},
        "source": {"service": "cmis", "operation": "market_report"},
        "cmis_status": "ok",
        "findings": {"data": {"price": 999.0}, "risk": None},
        "confidence": {},
        "evidence_context": {"freshness_verified": True},
    }
    graph = FakeGraph(
        [
            HumanMessage(content="Old question"),
            ToolMessage(
                content=json.dumps(prior_report),
                tool_call_id="old",
                name="x1_scout_investigate",
            ),
            AIMessage(content="Old answer"),
            HumanMessage(content="New unrelated question"),
            AIMessage(content="New answer with no current-turn Scout evidence."),
        ]
    )
    bridge = RobertaBridge(graph)
    server, thread = _serve_once(bridge)
    try:
        url = f"http://127.0.0.1:{server.server_port}/v1/roberta"
        status, payload = _request(
            url,
            body={
                "message": "New unrelated question",
                "evaluation_mode": EVALUATION_TELEMETRY_V2,
            },
        )
        assert status == 200
        assert payload["claims"] == []
        assert "factual_response" not in payload["evaluation_evidence"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
