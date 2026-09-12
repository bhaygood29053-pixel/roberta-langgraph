from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request

from roberta.bridge_http import create_server


class FakeBetaBridge:
    def __init__(self):
        self.ask_calls = 0
        self.evaluation_calls = 0

    def ask(self, message: str, *, thread_id=None):
        self.ask_calls += 1
        return "bounded beta answer"

    def ask_with_evaluation(self, message: str, *, thread_id=None, evaluation_mode=None):
        self.evaluation_calls += 1
        return "bounded beta answer", {
            "evaluation_telemetry_version": "roberta_evaluation_telemetry/v1",
            "evaluation_evidence": {
                "human_response_decision": {
                    "workflow": "x1_smart_route_pretrade",
                    "response_depth": "normal",
                    "evidence_quality": "MEDIUM",
                    "important_unknowns": [
                        {"source_value": "smart_route.price_impact"},
                    ],
                    "execution_authorized": False,
                }
            },
            "claims": [{"name": "recommendation"}],
            "evidence_provenance": {"source_contracts": ["accepted-contract"]},
            "execution_authorized": False,
        }


def _request(url: str, *, body=None):
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _serve(bridge):
    server = create_server(host="127.0.0.1", port=0, bridge=bridge)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def test_beta_disabled_preserves_normal_bridge_path(monkeypatch, tmp_path):
    monkeypatch.delenv("ROBERTA_BETA_PRODUCT_PROOF_PATH", raising=False)
    bridge = FakeBetaBridge()
    server, thread = _serve(bridge)
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, payload = _request(
            f"{base}/v1/roberta",
            body={"message": "private prompt content"},
        )
        assert status == 200
        assert payload == {
            "service": "roberta_bridge",
            "status": "ok",
            "reply": "bounded beta answer",
        }
        assert bridge.ask_calls == 1
        assert bridge.evaluation_calls == 0
        assert not list(tmp_path.iterdir())
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_beta_enabled_records_coarse_outcome_without_prompt_or_reply(monkeypatch, tmp_path):
    destination = tmp_path / "beta.jsonl"
    monkeypatch.setenv("ROBERTA_BETA_PRODUCT_PROOF_PATH", str(destination))
    bridge = FakeBetaBridge()
    server, thread = _serve(bridge)
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, payload = _request(
            f"{base}/v1/roberta",
            body={"message": "my wallet and prompt must never be stored"},
        )
        assert status == 200
        assert payload["reply"] == "bounded beta answer"
        response_id = payload["beta_response_id"]
        assert len(response_id) == 32
        assert bridge.ask_calls == 0
        assert bridge.evaluation_calls == 1

        rows = [json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 1
        row = rows[0]
        assert row["record_type"] == "automatic_response_outcome"
        assert row["response_id"] == response_id
        assert row["workflow"] == "x1_smart_route_pretrade"
        assert row["outcome"] == "evidence_required"
        assert row["content_persisted"] is False
        encoded = json.dumps(row).lower()
        assert "my wallet and prompt" not in encoded
        assert "bounded beta answer" not in encoded
        assert "message" not in row
        assert "reply" not in row
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_bounded_feedback_joins_automatic_record(monkeypatch, tmp_path):
    destination = tmp_path / "beta.jsonl"
    monkeypatch.setenv("ROBERTA_BETA_PRODUCT_PROOF_PATH", str(destination))
    bridge = FakeBetaBridge()
    server, thread = _serve(bridge)
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, answer = _request(
            f"{base}/v1/roberta",
            body={"message": "evaluate this privately"},
        )
        assert status == 200
        response_id = answer["beta_response_id"]

        status, feedback = _request(
            f"{base}/v1/beta-feedback",
            body={
                "response_id": response_id,
                "helpful": False,
                "clarity": "too_technical",
                "evidence_drill_down": True,
                "would_use_again": True,
            },
        )
        assert status == 200
        assert feedback == {
            "service": "roberta_bridge",
            "status": "ok",
            "recorded": True,
        }

        rows = [json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines()]
        assert len(rows) == 2
        assert rows[0]["response_id"] == rows[1]["response_id"] == response_id
        assert rows[1]["record_type"] == "explicit_user_feedback"
        assert rows[1]["clarity"] == "too_technical"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_feedback_requires_existing_response_join_id(monkeypatch, tmp_path):
    monkeypatch.setenv("ROBERTA_BETA_PRODUCT_PROOF_PATH", str(tmp_path / "beta.jsonl"))
    server, thread = _serve(FakeBetaBridge())
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, payload = _request(
            f"{base}/v1/beta-feedback",
            body={"helpful": True, "clarity": "clear"},
        )
        assert status == 400
        assert payload["error"]["code"] == "invalid_beta_feedback"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_feedback_rejects_freeform_or_sensitive_extra_fields(monkeypatch, tmp_path):
    monkeypatch.setenv("ROBERTA_BETA_PRODUCT_PROOF_PATH", str(tmp_path / "beta.jsonl"))
    server, thread = _serve(FakeBetaBridge())
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        status, payload = _request(
            f"{base}/v1/beta-feedback",
            body={
                "response_id": "b" * 32,
                "helpful": True,
                "clarity": "clear",
                "prompt": "this must never be accepted",
            },
        )
        assert status == 400
        assert payload["error"]["code"] == "invalid_beta_feedback"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
