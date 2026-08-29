from __future__ import annotations

import json
import os
import threading
from importlib.metadata import distribution
from pathlib import Path

from langchain_core.messages import AIMessage, ToolMessage

import cmis_core
import roberta_core
from cmis_core import api as cmis_private_api
from liquidity_scout.cmis import http as cmis_http
from liquidity_scout.cmis_private_core import load_runtime_contract as load_cmis_runtime_contract
from roberta import private_core as roberta_private_core
from roberta.bridge_http import RobertaBridge
from roberta.cmis.capabilities import CMISCapabilityContractError
from roberta.cmis.http import CMISHTTPClient
from roberta.tools import get_roberta_tools

EXPECTED_CMIS_VERSION = "0.2.0"
EXPECTED_ROBERTA_VERSION = "0.2.0"
EXPECTED_CMIS_CONTRACT = "cmis-private-core/v1"
EXPECTED_ROBERTA_CONTRACT = "roberta-private-core/v1"


def token(symbol: str, mint: str, name: str | None = None) -> dict[str, object]:
    return {"symbol": symbol, "name": name or symbol, "mint": mint, "address": mint}


def pool(address: str, base: dict[str, object], quote: dict[str, object]) -> dict[str, object]:
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

    def __init__(self) -> None:
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


class ScoutRoutingOracle:
    def __init__(self, *, tool_name: str, args: dict[str, object], expected_chain: str):
        self.tool_name = tool_name
        self.args = args
        self.expected_chain = expected_chain
        self.invoke_count = 0
        self.report: dict[str, object] | None = None

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        self.invoke_count += 1
        if self.invoke_count == 1:
            return AIMessage(
                content="",
                tool_calls=[{
                    "name": self.tool_name,
                    "args": self.args,
                    "id": f"phase4-{self.expected_chain}-1",
                    "type": "tool_call",
                }],
            )
        if self.invoke_count == 2:
            tool_messages = [item for item in messages if isinstance(item, ToolMessage)]
            if not tool_messages:
                raise AssertionError("ROBERTA did not receive a Chain Scout result.")
            report = json.loads(str(tool_messages[-1].content))
            assert report["chain"] == self.expected_chain
            self.report = report
            return AIMessage(content=f"Phase 4 {self.expected_chain} routing validation passed.")
        raise AssertionError("Unexpected extra Oracle invocation.")


def dist_paths(name: str) -> set[str]:
    return {str(path).replace("\\", "/") for path in (distribution(name).files or ())}


def _assert_package_ownership() -> None:
    cmis_paths = dist_paths("cmis-private-core")
    roberta_paths = dist_paths("roberta-private-core")

    assert "liquidity_scout/cmis/runtime_gateway.py" in cmis_paths
    assert "liquidity_scout/cmis/gateway.py" in cmis_paths
    assert "liquidity_scout/cmis/http.py" not in cmis_paths
    assert "liquidity_scout/cmis/capabilities.py" not in cmis_paths

    assert "roberta/graph.py" in roberta_paths
    assert "roberta/evidence_aware.py" in roberta_paths
    assert "roberta/private_core.py" not in roberta_paths


def _write_evidence(payload: dict[str, object]) -> None:
    path = Path(os.getenv("PHASE4_EVIDENCE_PATH", "phase4-evidence.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    gates: dict[str, bool] = {}

    assert os.environ.get("ROBERTA_PRIVATE_CORE_REQUIRED") == "1"
    assert os.environ.get("CMIS_PRIVATE_CORE_REQUIRED") == "1"
    assert os.environ.get("PHASE4_PUBLIC_STRIP_VERIFIED") == "1"
    gates["public_protected_source_stripped_before_private_install"] = True

    assert cmis_core.__version__ == EXPECTED_CMIS_VERSION
    assert roberta_core.__version__ == EXPECTED_ROBERTA_VERSION
    assert cmis_private_api.CUTOVER_CONTRACT == EXPECTED_CMIS_CONTRACT
    assert roberta_private_core.EXPECTED_PRIVATE_CONTRACT == EXPECTED_ROBERTA_CONTRACT
    gates["private_facade_contracts"] = True

    _assert_package_ownership()
    gates["package_ownership"] = True

    cmis_contract = load_cmis_runtime_contract()
    assert cmis_contract["source"] == "private"
    assert cmis_contract["contract"] == EXPECTED_CMIS_CONTRACT
    assert tuple(cmis_contract["supported_services"]) == tuple(cmis_http.SUPPORTED_SERVICES)
    assert tuple(cmis_contract["supported_chains"]) == tuple(cmis_http.SUPPORTED_CHAINS)
    assert tuple(cmis_contract["known_chains"]) == tuple(cmis_http.KNOWN_CHAINS)
    gates["public_private_cmis_surface_parity"] = True

    roberta_status = roberta_private_core.private_core_status()
    assert roberta_status["available"] is True
    assert roberta_status["required"] is True
    assert roberta_status["source"] == "private"
    gates["roberta_private_core_required"] = True
    gates["cmis_private_core_required"] = True

    provider = FakeX1MarketProvider()
    gateway = cmis_contract["gateway_class"](
        x1_market_provider=provider,
        verification_evidence_db_path=":memory:",
        intelligence_evidence_db_path=":memory:",
        auto_record_history=False,
    )

    api_key = "phase4-local-validation"
    server = cmis_http.create_server(
        host="127.0.0.1",
        port=0,
        gateway=gateway,
        api_key=api_key,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_port}"

        unauthorized = CMISHTTPClient(base_url=base_url, timeout_seconds=5)
        try:
            unauthorized.capabilities()
        except CMISCapabilityContractError:
            gates["cmis_http_auth_fail_closed"] = True
        else:
            raise AssertionError("CMIS split runtime accepted an unauthenticated capability request.")

        client = CMISHTTPClient(
            base_url=base_url,
            api_key=api_key,
            timeout_seconds=5,
        )
        capabilities = client.capabilities()
        assert capabilities["contract_version"] == "1.13.0"
        gates["cmis_capability_handshake"] = True

        tools = get_roberta_tools(cmis_client=client)

        x1_model = ScoutRoutingOracle(
            tool_name="x1_scout_investigate",
            args={"asset": "AGI", "objective": "current market report"},
            expected_chain="x1",
        )
        x1_graph = roberta_private_core.build_graph(model=x1_model, tools=tools)
        x1_reply = RobertaBridge(x1_graph).ask("Give me the current AGI market report on X1.")
        assert x1_reply == "Phase 4 x1 routing validation passed."
        assert x1_model.report is not None
        assert x1_model.report["specialist"] == "x1_scout"
        assert x1_model.report["source"] == {"service": "cmis", "operation": "market_report"}
        assert x1_model.report["findings"]["data"]["liquidity_usd"] == 5000
        assert x1_model.report["findings"]["data"]["#LPs"] == 1
        assert provider.refresh_calls >= 1
        gates["roberta_to_x1_scout"] = True
        gates["x1_scout_to_private_cmis_http"] = True

        refresh_calls_before_solana = provider.refresh_calls
        solana_model = ScoutRoutingOracle(
            tool_name="solana_scout_investigate",
            args={"asset": "JUP", "objective": "verify token supply"},
            expected_chain="solana",
        )
        solana_graph = roberta_private_core.build_graph(model=solana_model, tools=tools)
        solana_reply = RobertaBridge(solana_graph).ask("Verify JUP token supply on Solana.")
        assert solana_reply == "Phase 4 solana routing validation passed."
        assert solana_model.report is not None
        assert solana_model.report["specialist"] == "solana_scout"
        assert solana_model.report["status"] == "unavailable"
        assert solana_model.report["warnings"][0]["code"] == "SOLANA_PROVIDER_NOT_CONFIGURED"
        assert provider.refresh_calls == refresh_calls_before_solana
        gates["roberta_to_solana_scout"] = True
        gates["solana_provider_gate_fail_closed"] = True
        gates["solana_did_not_fall_through_to_x1"] = True

        assert all(gates.values())
        evidence = {
            "schema_version": 1,
            "phase": 4,
            "status": "pass",
            "authority_chain": "User -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider",
            "public_heads": {
                "roberta_langgraph": os.getenv("PHASE4_ROBERTA_PUBLIC_SHA", ""),
                "cmis": os.getenv("PHASE4_CMIS_PUBLIC_SHA", ""),
            },
            "private_distributions": {
                "roberta_private_core": EXPECTED_ROBERTA_VERSION,
                "cmis_private_core": EXPECTED_CMIS_VERSION,
            },
            "contracts": {
                "roberta": EXPECTED_ROBERTA_CONTRACT,
                "cmis": EXPECTED_CMIS_CONTRACT,
                "cmis_public_contract": capabilities["contract_version"],
            },
            "gates": gates,
            "execution_authorized": False,
            "public_fallback_used": False,
        }
        _write_evidence(evidence)

        for name in sorted(gates):
            print(f"PHASE4_{name.upper()}=PASS")
        print("PHASE4_SPLIT_INTEGRATION=PASS")
        print("PUBLIC_FALLBACK_USED=FALSE")
        print("EXECUTION_AUTHORIZED=FALSE")
        return 0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


if __name__ == "__main__":
    raise SystemExit(main())
