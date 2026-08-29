from __future__ import annotations

import json
import os
import threading
from importlib.metadata import distribution

from langchain_core.messages import AIMessage, ToolMessage

import cmis_core
import roberta_core
from cmis_core import api as cmis_private_api
from liquidity_scout.cmis import http as cmis_http
from liquidity_scout.cmis_private_core import load_runtime_contract as load_cmis_runtime_contract
from roberta import private_core as roberta_private_core
from roberta.bridge_http import RobertaBridge
from roberta.cmis.http import CMISHTTPClient
from roberta.tools import get_roberta_tools

EXPECTED_CMIS_VERSION = "0.2.0"
EXPECTED_ROBERTA_VERSION = "0.2.0"
EXPECTED_CMIS_CONTRACT = "cmis-private-core/v1"
EXPECTED_ROBERTA_CONTRACT = "roberta-private-core/v1"


def token(symbol: str, mint: str, name: str | None = None):
    return {"symbol": symbol, "name": name or symbol, "mint": mint, "address": mint}


def pool(address: str, base: dict, quote: dict):
    return {
        "address": address,
        "baseToken": base,
        "quoteToken": quote,
        "createdAt": "2026-01-01T00:00:00Z",
        "liquidity": 5000,
        "volume24h": 100,
        "txns24h": 10,
        "holders": 1000,
        "priceUsd": 0.25,
    }


class FakeX1MarketProvider:
    chain = "x1"

    def __init__(self):
        agi = token("AGI", "MINT_AGI", "Artificial General Intelligence")
        usdc = token("USDC", "MINT_USDC", "USD Coin")
        self.pools = [pool("P1", agi, usdc)]
        self.xnt_price_usd = None
        self.last_refresh = 123.0
        self.refresh_calls = 0

    def refresh_if_needed(self):
        self.refresh_calls += 1
        return self

    def market_catalog(self):
        return {
            "chain": "x1",
            "source": "X1.Ninja/XDEX",
            "pools": list(self.pools),
            "xnt_price_usd": self.xnt_price_usd,
            "observed_at": self.last_refresh,
        }


class ScriptedOracle:
    def __init__(self):
        self.invoke_count = 0
        self.report = None

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self.invoke_count += 1
        if self.invoke_count == 1:
            return AIMessage(
                content="",
                tool_calls=[{
                    "name": "x1_scout_investigate",
                    "args": {"asset": "AGI", "objective": "current market report"},
                    "id": "phase3-required-private-core-1",
                    "type": "tool_call",
                }],
            )
        if self.invoke_count == 2:
            tool_messages = [item for item in messages if isinstance(item, ToolMessage)]
            if not tool_messages:
                raise AssertionError("ROBERTA did not receive the X1 Scout result.")
            report = json.loads(str(tool_messages[-1].content))
            assert report["specialist"] == "x1_scout"
            assert report["chain"] == "x1"
            assert report["source"] == {"service": "cmis", "operation": "market_report"}
            assert report["findings"]["data"]["liquidity_usd"] == 5000
            assert report["findings"]["data"]["#LPs"] == 1
            self.report = report
            return AIMessage(content="Phase 3 required-private-core split validation passed.")
        raise AssertionError("Unexpected extra Oracle invocation.")


def dist_paths(name: str) -> set[str]:
    return {str(path).replace("\\", "/") for path in (distribution(name).files or ())}


def main() -> int:
    assert os.environ.get("CMIS_PRIVATE_CORE_REQUIRED") == "1"
    assert os.environ.get("ROBERTA_PRIVATE_CORE_REQUIRED") == "1"
    assert cmis_core.PHASE == 3 and cmis_core.__version__ == EXPECTED_CMIS_VERSION
    assert roberta_core.PHASE == 3 and roberta_core.__version__ == EXPECTED_ROBERTA_VERSION
    assert cmis_private_api.CUTOVER_CONTRACT == EXPECTED_CMIS_CONTRACT
    assert roberta_private_core.EXPECTED_PRIVATE_CONTRACT == EXPECTED_ROBERTA_CONTRACT

    cmis_paths = dist_paths("cmis-private-core")
    roberta_paths = dist_paths("roberta-private-core")
    assert "liquidity_scout/cmis/runtime_gateway.py" in cmis_paths
    assert "liquidity_scout/cmis/http.py" not in cmis_paths
    assert "liquidity_scout/cmis/capabilities.py" not in cmis_paths
    assert "roberta/graph.py" in roberta_paths
    assert "roberta/private_core.py" not in roberta_paths

    cmis_contract = load_cmis_runtime_contract()
    assert cmis_contract["source"] == "private"
    assert cmis_contract["contract"] == EXPECTED_CMIS_CONTRACT

    roberta_status = roberta_private_core.private_core_status()
    assert roberta_status["available"] is True
    assert roberta_status["required"] is True
    assert roberta_private_core._validated_private_api() is not None

    provider = FakeX1MarketProvider()
    gateway = cmis_contract["gateway_class"](
        x1_market_provider=provider,
        verification_evidence_db_path=":memory:",
        intelligence_evidence_db_path=":memory:",
        auto_record_history=False,
    )

    server = cmis_http.create_server(host="127.0.0.1", port=0, gateway=gateway, api_key="")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        client = CMISHTTPClient(
            base_url=f"http://127.0.0.1:{server.server_port}",
            timeout_seconds=5,
        )
        model = ScriptedOracle()
        graph = roberta_private_core.build_graph(
            model=model,
            tools=get_roberta_tools(cmis_client=client),
        )
        reply = RobertaBridge(graph).ask("Give me the current AGI market report on X1.")

        assert reply == "Phase 3 required-private-core split validation passed."
        assert model.invoke_count == 2
        assert model.report is not None
        assert provider.refresh_calls >= 1
        assert client.capabilities()["contract_version"] == "1.13.0"

        print("PHASE3_SPLIT_VALIDATION=PASS")
        print("ROBERTA_PRIVATE_CORE_REQUIRED=PASS")
        print("CMIS_PRIVATE_CORE_REQUIRED=PASS")
        print("ROBERTA_TO_X1_SCOUT=PASS")
        print("X1_SCOUT_TO_CMIS_HTTP=PASS")
        print("CMIS_PRIVATE_RUNTIME=PASS")
        print("PUBLIC_FALLBACK_USED=FALSE")
        return 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    raise SystemExit(main())
