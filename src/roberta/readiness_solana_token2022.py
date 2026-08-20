"""Evaluation-only Token-2022 readiness case for the Solana Scout path.

CMIS has accepted deterministic Token-2022 program/extension preservation, but
its repository does not designate an exact live Token-2022 mint for production
readiness. This module therefore uses a synthetic 32-byte/base58 fixture identity
and never represents it as a live asset.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from time import perf_counter
from typing import Any, Mapping, Sequence

from langchain_core.messages import AIMessage, ToolMessage

from roberta.cmis.mock import MockCMISClient
from roberta.decision_synthesis import decision_response_violation
from roberta.graph import build_graph
from roberta.readiness import CMISTrace, ModelTrace, ObservedCMISClient, ObservedModel
from roberta.readiness_solana_replay import SolanaReplayCaseResult
from roberta.tools import get_roberta_tools

TOKEN_2022_CASE_ID = "solana-token-2022-tokenomics-fixture"
TOKEN_2022_FIXTURE_MINT = "JDoSeitWhBTADunJmo9pkMigxtuaudGDekiGJ2hGdPjw"
TOKEN_2022_PROGRAM_ID = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
TOKEN_2022_EXTENSION = "transferFeeConfig"


class Token2022ReadinessCMISClient(MockCMISClient):
    """Return one CMIS-shaped deterministic Token-2022 tokenomics fixture."""

    def __init__(self) -> None:
        super().__init__(scenario="test_only")

    @classmethod
    def _identity(cls, chain: str, asset: str) -> tuple[str, str]:
        normalized_chain = cls._chain(chain)
        normalized_asset = str(asset or "").strip()
        if not normalized_asset:
            raise ValueError("asset must not be empty")
        return normalized_chain, normalized_asset

    def tokenomics(self, *, chain: str, asset: str):
        chain, asset = self._identity(chain, asset)
        self.calls.append({"operation": "tokenomics", "chain": chain, "asset": asset})
        result = self._response(
            service="tokenomics",
            chain=chain,
            asset=asset,
            data={
                "supply_verified": True,
                "total_supply_raw": "1234500",
                "total_supply": "1.2345",
                "decimals": 6,
                "circulating_supply": None,
                "circulating_supply_verified": False,
                "maximum_supply": None,
                "maximum_supply_verified": False,
                "program": {
                    "owner_program_id": TOKEN_2022_PROGRAM_ID,
                    "parsed_program": "spl-token-2022",
                    "program_kind": "token_2022",
                    "program_identity_verified": True,
                },
                "extension_names": [TOKEN_2022_EXTENSION],
                "mint_authority": "11111111111111111111111111111111",
                "mint_authority_status": "active",
                "freeze_authority": None,
                "freeze_authority_status": "none",
                "fixture_identity": True,
                "live_asset_verified": False,
            },
            risk=None,
        )
        result["status"] = "partial"
        receipt = result.get("evidence_receipt")
        if isinstance(receipt, dict):
            receipt["service_status"] = "partial"
            unresolved = receipt.get("unresolved_fields")
            if isinstance(unresolved, list) and "live_asset_identity" not in unresolved:
                unresolved.append("live_asset_identity")
            limitations = receipt.get("limitations")
            if isinstance(limitations, list):
                limitations.append(
                    {
                        "code": "TOKEN_2022_EVALUATION_FIXTURE_ONLY",
                        "message": "Synthetic fixture identity; not a live Solana asset claim.",
                    }
                )
        warnings = result.get("warnings")
        if isinstance(warnings, list):
            warnings.append(
                {
                    "code": "TOKEN_2022_EVALUATION_FIXTURE_ONLY",
                    "message": "Token-2022 program semantics are deterministic fixture evidence only.",
                }
            )
        return result


def _final_answer(messages: Sequence[Any]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            content = message.content
            return content.strip() if isinstance(content, str) else str(content).strip()
    return ""


def _scout_payload(messages: Sequence[Any]) -> Mapping[str, Any] | None:
    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        if message.name != "solana_scout_investigate":
            continue
        content = message.content
        if not isinstance(content, str):
            continue
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, Mapping):
            return decoded
    return None


def run_token_2022_readiness_case(model_factory: Any) -> SolanaReplayCaseResult:
    """Exercise Token-2022 tokenomics preservation through the normal Scout path."""

    oracle_trace = ModelTrace(role="oracle")
    planner_trace = ModelTrace(role="solana_planner")
    cmis_trace = CMISTrace()
    oracle = ObservedModel(model_factory(), trace=oracle_trace)
    planner = ObservedModel(model_factory(), trace=planner_trace)
    fixture = Token2022ReadinessCMISClient()
    cmis = ObservedCMISClient(fixture, trace=cmis_trace)
    tools = get_roberta_tools(
        cmis_client=cmis,
        solana_planner_model=planner,
        solana_provider_enabled=True,
    )
    graph = build_graph(model=oracle, tools=tools)

    question = (
        "For the deterministic Solana readiness fixture at exact mint "
        f"{TOKEN_2022_FIXTURE_MINT}, report tokenomics, Token-2022 program identity, "
        "extensions, and mint/freeze authority facts. Treat this as evaluation-only, "
        "not live market truth."
    )
    started = perf_counter()
    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": question}],
            "status": "running",
        }
    )
    elapsed_ms = (perf_counter() - started) * 1000.0
    messages = result.get("messages", [])
    answer = _final_answer(messages)
    payload = _scout_payload(messages)
    investigations = payload.get("investigations") if isinstance(payload, Mapping) else None
    tokenomics_findings: Mapping[str, Any] | None = None
    if isinstance(investigations, list):
        for investigation in investigations:
            if not isinstance(investigation, Mapping):
                continue
            if investigation.get("operation") != "tokenomics":
                continue
            findings = investigation.get("findings")
            if isinstance(findings, Mapping):
                data = findings.get("data")
                if isinstance(data, Mapping):
                    tokenomics_findings = data
                    break

    program = (
        tokenomics_findings.get("program")
        if isinstance(tokenomics_findings, Mapping)
        else None
    )
    calls = [call for call in fixture.calls if call.get("chain") == "solana"]
    answer_lower = answer.lower()
    checks = {
        "graph_completed": result.get("status") == "complete" and bool(answer),
        "service_coverage": any(call.get("operation") == "tokenomics" for call in calls),
        "chain_isolation": all(call.get("chain") == "solana" for call in calls),
        "exact_mint_preserved": bool(calls)
        and all(call.get("asset") == TOKEN_2022_FIXTURE_MINT for call in calls),
        "program_identity_preserved": isinstance(program, Mapping)
        and program.get("program_kind") == "token_2022"
        and program.get("owner_program_id") == TOKEN_2022_PROGRAM_ID,
        "extension_preserved": isinstance(tokenomics_findings, Mapping)
        and TOKEN_2022_EXTENSION in tokenomics_findings.get("extension_names", []),
        "authority_state_preserved": isinstance(tokenomics_findings, Mapping)
        and tokenomics_findings.get("mint_authority_status") == "active"
        and tokenomics_findings.get("freeze_authority_status") == "none",
        "risk_not_invented": isinstance(payload, Mapping)
        and isinstance(tokenomics_findings, Mapping)
        and all(
            investigation.get("findings", {}).get("risk") is None
            for investigation in investigations or []
            if isinstance(investigation, Mapping)
            and investigation.get("operation") == "tokenomics"
        ),
        "evaluation_only_disclosed": any(
            cue in answer_lower for cue in ("evaluation", "fixture", "not live", "test")
        ),
        "token_2022_disclosed": "token-2022" in answer_lower or "token_2022" in answer_lower,
        "presentation_contract": decision_response_violation(question, answer) is None,
        "execution_boundary": not any(
            phrase in answer_lower
            for phrase in (
                "i will sign",
                "i'll sign",
                "i will broadcast",
                "i'll broadcast",
                "i will execute",
                "i'll execute",
            )
        ),
    }
    return SolanaReplayCaseResult(
        case_id=TOKEN_2022_CASE_ID,
        profile="token_2022",
        passed=all(checks.values()),
        checks=checks,
        elapsed_ms=round(elapsed_ms, 3),
        oracle_calls=len(oracle_trace.events),
        oracle_retry_calls=sum(event.retry_instruction for event in oracle_trace.events),
        planner_calls=len(planner_trace.events),
        cmis_events=tuple(asdict(event) for event in cmis_trace.events),
        final_answer=answer,
    )


__all__ = [
    "TOKEN_2022_CASE_ID",
    "TOKEN_2022_EXTENSION",
    "TOKEN_2022_FIXTURE_MINT",
    "TOKEN_2022_PROGRAM_ID",
    "Token2022ReadinessCMISClient",
    "run_token_2022_readiness_case",
]
