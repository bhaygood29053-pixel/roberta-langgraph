"""Deterministic tests for the provider-backed CMIS HTTP client."""

from copy import deepcopy
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError
from unittest.mock import patch

from roberta.cmis.capabilities import (
    HISTORICAL_ALL_AVAILABLE_REQUIRED_LIMITATIONS,
    HISTORICAL_PAIR_REQUIRED_LIMITATION,
    INTELLIGENCE_FOUNDATION_CAPABILITIES,
    INTELLIGENCE_FOUNDATION_PHASE,
    INTELLIGENCE_PROMOTION_RULE,
    MIN_CMIS_CONTRACT_VERSION,
    X1_ASSET_IDENTITY_CONTRACT_VERSION,
    X1_ASSET_IDENTITY_MIN_CMIS_CONTRACT_VERSION,
    X1_ASSET_IDENTITY_REQUIRED_LIMITATIONS,
)
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


def _capability(
    state: str,
    *,
    requirements: list[str] | None = None,
    limitations: list[str] | None = None,
) -> dict[str, object]:
    return {
        "state": state,
        "callable": state != "unavailable",
        "requirements": list(requirements or []),
        "limitations": list(limitations or []),
    }


def _intelligence_capability() -> dict[str, object]:
    return {
        "state": "bounded",
        "read_only": True,
        "public_service_promoted": False,
        "scout_reliance_promoted": False,
        "requirements": [],
        "limitations": [],
    }


def _capabilities() -> dict[str, object]:
    services = [
        "asset_lookup",
        "market_report",
        "rank",
        "historical_compare",
        "tokenomics",
        "risk_check",
        "pre_trade_check",
        "trade_verification",
        "verified_asset_activity",
        "verification_evidence",
    ]
    x1 = {service: _capability("supported") for service in services}
    x1["pre_trade_check"] = _capability(
        "bounded",
        limitations=["analysis_only", "execution_authorized_false"],
    )
    x1["trade_verification"] = _capability("bounded")
    x1["verified_asset_activity"] = _capability("bounded")
    x1["verification_evidence"] = _capability("bounded")

    solana = {service: _capability("unavailable") for service in services}
    solana["asset_lookup"] = _capability(
        "bounded",
        requirements=["exact_mint", "solana_rpc_provider_configured"],
    )
    for service in ("market_report", "historical_compare", "tokenomics", "risk_check"):
        solana[service] = _capability("partial", requirements=["exact_mint"])

    return {
        "service": "cmis_gateway",
        "version": 1,
        "schema_version": 1,
        "contract_version": MIN_CMIS_CONTRACT_VERSION,
        "request_path": "/v1/cmis",
        "evidence_quality": {
            "evidence_receipt_schema_version": 1,
            "proof_score_schema_version": 1,
            "proof_strength_values": ["STRONG", "MODERATE", "WEAK"],
            "risk_separate_from_proof": True,
            "missing_evidence_is_unknown": True,
        },
        "intelligence_foundation": {
            "schema_version": 1,
            "phase": INTELLIGENCE_FOUNDATION_PHASE,
            "read_only": True,
            "public_service_promoted": False,
            "scout_reliance_promoted": False,
            "promotion_rule": INTELLIGENCE_PROMOTION_RULE,
            "intelligence_evidence_schema_version": 1,
            "capabilities": {
                name: _intelligence_capability()
                for name in INTELLIGENCE_FOUNDATION_CAPABILITIES
            },
        },
        "supported_services": services,
        "supported_chains": ["x1"],
        "known_chains": ["x1", "solana"],
        "chains": {
            "x1": {
                "services": x1,
                "callable_services": [
                    service for service in services if x1[service]["callable"] is True
                ],
            },
            "solana": {
                "services": solana,
                "callable_services": [
                    service for service in services if solana[service]["callable"] is True
                ],
            },
        },
    }


def _cmis_1_11_identity_capabilities() -> dict[str, object]:
    capabilities = deepcopy(_capabilities())
    capabilities["contract_version"] = X1_ASSET_IDENTITY_MIN_CMIS_CONTRACT_VERSION
    lookup = capabilities["chains"]["x1"]["services"]["asset_lookup"]
    lookup["limitations"] = list(X1_ASSET_IDENTITY_REQUIRED_LIMITATIONS)
    lookup["identity_contract_version"] = X1_ASSET_IDENTITY_CONTRACT_VERSION
    lookup["exact_mint_normalization"] = True
    lookup["normalized_identity_root"] = "mint"
    lookup["metaplex_xdex_reconciliation"] = True
    return capabilities


class _Server:
    def __init__(
        self,
        response: dict[str, object],
        *,
        capabilities: dict[str, object] | None = None,
        expected_key: str = "",
    ):
        self.requests: list[dict[str, object]] = []
        self.get_paths: list[str] = []
        self.auth_headers: list[tuple[str, str | None]] = []
        requests = self.requests
        get_paths = self.get_paths
        auth_headers = self.auth_headers
        response_body = response
        capability_body = capabilities or _capabilities()
        expected_key_value = expected_key

        class Handler(BaseHTTPRequestHandler):
            def _authorized(self) -> bool:
                if not expected_key_value:
                    return True
                return self.headers.get("Authorization") == f"Bearer {expected_key_value}"

            def _write_json(self, status: int, body_value: dict[str, object]) -> None:
                body = json.dumps(body_value).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):  # noqa: N802
                get_paths.append(self.path)
                auth_headers.append(("GET", self.headers.get("Authorization")))
                if not self._authorized():
                    self._write_json(
                        401,
                        {"status": "error", "error": {"code": "unauthorized", "message": "bad token"}},
                    )
                    return
                if self.path != "/v1/cmis/capabilities":
                    self._write_json(
                        404,
                        {"status": "error", "error": {"code": "not_found", "message": "not found"}},
                    )
                    return
                self._write_json(200, capability_body)

            def do_POST(self):  # noqa: N802
                length = int(self.headers["Content-Length"])
                requests.append(json.loads(self.rfile.read(length).decode("utf-8")))
                auth_headers.append(("POST", self.headers.get("Authorization")))
                if not self._authorized():
                    self._write_json(
                        401,
                        {"status": "error", "error": {"code": "unauthorized", "message": "bad token"}},
                    )
                    return
                self._write_json(200, response_body)

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


def test_http_client_posts_asset_lookup_under_cmis_1_11_identity_contract() -> None:
    mint = "DQ6sApYPMJ8LwpvyUjthL7amykNBJ3fx5jZi2koN7vHb"
    expected = _envelope("asset_lookup")
    expected["asset"] = {"symbol": "XENCAT", "name": "XENCAT", "mint": mint}
    expected["data"] = {
        "identity_contract": X1_ASSET_IDENTITY_CONTRACT_VERSION,
        "normalized_identity": {
            "mint": mint,
            "symbol": "XENCAT",
            "name": "XENCAT",
            "identity_root": "mint",
            "descriptor_source": "metaplex_token_metadata",
            "normalized_onchain_identity_verified": True,
        },
        "identity_reconciliation": {
            "state": "agreement",
            "comparable_fields": ["symbol", "name"],
            "conflicting_fields": [],
        },
    }
    with _Server(
        expected,
        capabilities=_cmis_1_11_identity_capabilities(),
    ) as running:
        client = CMISHTTPClient(base_url=running.base_url, timeout_seconds=2)
        result = client.asset_lookup(chain="x1", asset=mint)

    assert result == expected
    assert running.get_paths == ["/v1/cmis/capabilities"]
    assert running.requests == [
        {"service": "asset_lookup", "chain": "x1", "asset": mint, "params": {}}
    ]


def test_http_client_handshakes_then_posts_market_report_and_preserves_envelope() -> None:
    expected = _envelope("market_report")
    with _Server(expected) as running:
        client = CMISHTTPClient(base_url=running.base_url, timeout_seconds=2)
        result = client.market_report(chain="x1", asset="AGI")

    assert result == expected
    assert running.get_paths == ["/v1/cmis/capabilities"]
    assert running.requests == [
        {"service": "market_report", "chain": "x1", "asset": "AGI", "params": {}}
    ]


def test_http_client_sends_bearer_auth_for_capabilities_and_pre_trade() -> None:
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
    assert running.auth_headers == [("GET", "Bearer secret"), ("POST", "Bearer secret")]
    assert running.requests[0]["params"] == {
        "trade": {"side": "buy", "notional_usd": 25.0}
    }


def test_http_client_caches_validated_capabilities() -> None:
    expected = _envelope("market_report")
    with _Server(expected) as running:
        client = CMISHTTPClient(base_url=running.base_url, timeout_seconds=2)
        first = client.capabilities()
        second = client.capabilities()

    assert first is second
    assert running.get_paths == ["/v1/cmis/capabilities"]
    assert running.requests == []


def test_http_client_turns_capability_transport_failure_into_unavailable_envelope() -> None:
    client = CMISHTTPClient()
    with patch("roberta.cmis.http.urlopen", side_effect=URLError("offline")):
        result = client.market_report(chain="x1", asset="AGI")

    assert result["service"] == "market_report"
    assert result["chain"] == "x1"
    assert result["status"] == "unavailable"
    assert result["data"] == {}
    assert result["risk"] is None
    assert result["errors"] == []
    assert result["warnings"][0]["code"] == "cmis_capability_contract_unavailable"


def test_http_client_fails_closed_on_stale_capability_contract_before_post() -> None:
    capabilities = deepcopy(_capabilities())
    capabilities["contract_version"] = "1.7.9"
    with _Server(_envelope("market_report"), capabilities=capabilities) as running:
        result = CMISHTTPClient(base_url=running.base_url, timeout_seconds=2).market_report(
            chain="x1", asset="AGI"
        )

    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == "cmis_capability_contract_unavailable"
    assert running.get_paths == ["/v1/cmis/capabilities"]
    assert running.requests == []


def test_http_client_blocks_unadvertised_solana_pretrade_before_post() -> None:
    with _Server(_envelope("pre_trade_check", chain="solana")) as running:
        result = CMISHTTPClient(base_url=running.base_url, timeout_seconds=2).pre_trade_check(
            chain="solana",
            asset="So11111111111111111111111111111111111111112",
            action="BUY",
            amount_usd=100,
        )

    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == "cmis_capability_unavailable"
    assert running.get_paths == ["/v1/cmis/capabilities"]
    assert running.requests == []


def _cmis_1_10_history_capabilities() -> dict[str, object]:
    capabilities = deepcopy(_capabilities())
    capabilities["contract_version"] = "1.10.0"
    history = capabilities["chains"]["x1"]["services"]["historical_compare"]
    history["requirements"] = ["verified_current_market_snapshot"]
    history["limitations"] = [
        *HISTORICAL_ALL_AVAILABLE_REQUIRED_LIMITATIONS,
        HISTORICAL_PAIR_REQUIRED_LIMITATION,
    ]
    return capabilities


def test_http_client_posts_one_all_available_pair_request_under_cmis_1_10() -> None:
    expected = _envelope("historical_compare")
    capabilities = _cmis_1_10_history_capabilities()
    objective = "Compare XNT and ANL over their entire history"

    with _Server(expected, capabilities=capabilities) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).historical_compare(
            chain="x1",
            asset="XNT",
            question=objective,
            mode="all_available_pair",
            compare_asset="ANL",
        )

    assert result == expected
    assert running.get_paths == ["/v1/cmis/capabilities"]
    assert running.requests == [
        {
            "service": "historical_compare",
            "chain": "x1",
            "asset": "XNT",
            "params": {
                "mode": "all_available_pair",
                "compare_asset": "ANL",
                "question": objective,
            },
        }
    ]


def test_http_client_blocks_all_available_pair_on_cmis_1_9_before_post() -> None:
    capabilities = _cmis_1_10_history_capabilities()
    capabilities["contract_version"] = "1.9.0"

    with _Server(_envelope("historical_compare"), capabilities=capabilities) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).historical_compare(
            chain="x1",
            asset="XNT",
            question="Compare XNT and ANL over their full history",
            mode="all_available_pair",
            compare_asset="ANL",
        )

    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == "cmis_historical_mode_contract_unavailable"
    assert running.get_paths == ["/v1/cmis/capabilities"]
    assert running.requests == []


def test_http_client_blocks_pair_mode_when_pair_limitation_is_missing() -> None:
    capabilities = _cmis_1_10_history_capabilities()
    limitations = capabilities["chains"]["x1"]["services"]["historical_compare"]["limitations"]
    limitations.remove(HISTORICAL_PAIR_REQUIRED_LIMITATION)

    with _Server(_envelope("historical_compare"), capabilities=capabilities) as running:
        result = CMISHTTPClient(
            base_url=running.base_url,
            timeout_seconds=2,
        ).historical_compare(
            chain="x1",
            asset="XNT",
            question="Compare XNT and ANL over their full history",
            mode="all_available_pair",
            compare_asset="ANL",
        )

    assert result["status"] == "unavailable"
    assert result["warnings"][0]["code"] == "cmis_historical_mode_contract_unavailable"
    assert running.requests == []


def test_http_client_fails_closed_on_response_identity_mismatch() -> None:
    bad = _envelope("market_report", chain="solana")
    with _Server(bad) as running:
        result = CMISHTTPClient(base_url=running.base_url, timeout_seconds=2).market_report(
            chain="x1", asset="AGI"
        )

    assert result["status"] == "error"
    assert result["errors"][0]["code"] == "cmis_identity_mismatch"
