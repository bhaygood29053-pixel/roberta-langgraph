"""Deterministic tests for the provider-backed CMIS HTTP client."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from unittest.mock import patch

from roberta.cmis.http import CMISHTTPClient


def _envelope(service: str, *, chain: str = "x1") -> dict[str, object]:
    return {
        "service": service,
        "chain": chain,
        "status": "ok",
        "asset": {"symbol": "AGI", "mint": "mint-1"},
        "data": {"price": 1.25, "liquidity": 5000.0, "#LPs": 2},
        "risk": None,
        "confidence": {"level": "high"},
        "sources": [{"source": "x1_ninja"}],
        "observed_at": "2026-08-15T22:00:00Z",
        "warnings": [],
        "errors": [],
    }


class _Server:
    def __init__(self, response: dict[str, object], *, expected_key: str = ""):
        self.requests: list[dict[str, object]] = []
        self.auth_headers: list[str | None] = []
        requests = self.requests
        auth_headers = self.auth_headers
        response_body = response
        expected_key_value = expected_key

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                length = int(self.headers["Content-Length"])
                requests.append(json.loads(self.rfile.read(length).decode("utf-8")))
                auth_headers.append(self.headers.get("Authorization"))
                if expected_key_value and self.headers.get("Authorization") != (
                    f"Bearer {expected_key_value}"
                ):
                    self.send_response(401)
                    body = json.dumps(
                        {
                            "status": "error",
                            "error": {
                                "code": "unauthorized",
                                "message": "bad token",
                            },
                        }
                    ).encode("utf-8")
                else:
                    self.send_response(200)
                    body = json.dumps(response_body).encode("utf-8")
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):  # noqa: A003
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server.server_port}"

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def test_http_client_posts_market_report_and_preserves_cmis_envelope() -> None:
    expected = _envelope("market_report")
    with _Server(expected) as running:
        client = CMISHTTPClient(base_url=running.base_url, timeout_seconds=2)
        result = client.market_report(chain="x1", asset="AGI")

    assert result == expected
    assert running.requests == [
        {
            "service": "market_report",
            "chain": "x1",
            "asset": "AGI",
            "params": {},
        }
    ]


def test_http_client_sends_bearer_auth_and_pre_trade_shape() -> None:
    expected = _envelope("pre_trade_check")
    with _Server(expected, expected_key="secret") as running:
        client = CMISHTTPClient(
            base_url=running.base_url,
            api_key="secret",
            timeout_seconds=2,
        )
        result = client.pre_trade_check(
            chain="x1",
            asset="AGI",
            action="BUY",
            amount_usd=25,
        )

    assert result["status"] == "ok"
    assert running.auth_headers == ["Bearer secret"]
    assert running.requests[0]["params"] == {
        "trade": {"side": "buy", "notional_usd": 25.0}
    }


def test_http_client_turns_transport_failure_into_unavailable_envelope() -> None:
    client = CMISHTTPClient()
    with patch("roberta.cmis.http.urlopen", side_effect=URLError("offline")):
        result = client.market_report(chain="x1", asset="AGI")

    assert result["service"] == "market_report"
    assert result["chain"] == "x1"
    assert result["status"] == "unavailable"
    assert result["data"] == {}
    assert result["risk"] is None
    assert result["errors"] == []
    assert result["warnings"][0]["code"] == "cmis_transport_unavailable"


def test_http_client_fails_closed_on_response_identity_mismatch() -> None:
    bad = _envelope("market_report", chain="solana")
    with _Server(bad) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).market_report(chain="x1", asset="AGI")

    assert result["status"] == "error"
    assert result["errors"][0]["code"] == "cmis_identity_mismatch"
