"""Controlled production-model replay for degraded Solana evidence states.

The fixtures in this module are evaluation inputs only. They exercise the normal
Roberta -> Solana Scout -> CMIS tool path while preserving Solana's case-sensitive
mint identity. They are never current market authority and never authorize
execution.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, Mapping, Sequence

from langchain_core.messages import AIMessage

from roberta.cmis.mock import MockCMISClient
from roberta.decision_synthesis import decision_response_violation
from roberta.graph import build_graph
from roberta.readiness import CMISTrace, ModelTrace, ObservedCMISClient, ObservedModel
from roberta.tools import get_roberta_tools

JUP_MINT = "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN"

SolanaReplayProfile = Literal[
    "stale",
    "conflict",
    "insufficient",
    "unavailable",
    "provider_error",
    "null_field",
    "verified_zero",
]


@dataclass(frozen=True)
class SolanaReplayCase:
    case_id: str
    profile: SolanaReplayProfile
    question: str
    expected_services: tuple[str, ...]
    required_answer_any: tuple[str, ...]
    require_risk_evidence_labels: bool = False


@dataclass(frozen=True)
class SolanaReplayCaseResult:
    case_id: str
    profile: str
    passed: bool
    checks: Mapping[str, bool]
    elapsed_ms: float
    oracle_calls: int
    oracle_retry_calls: int
    planner_calls: int
    cmis_events: tuple[Mapping[str, Any], ...]
    final_answer: str


class SolanaReadinessFixtureCMISClient(MockCMISClient):
    """CMIS-compatible deterministic Solana fixture with exact mint preservation."""

    def __init__(self, profile: SolanaReplayProfile) -> None:
        super().__init__(scenario="test_only")
        self.profile = profile

    @classmethod
    def _identity(cls, chain: str, asset: str) -> tuple[str, str]:
        normalized_chain = cls._chain(chain)
        normalized_asset = str(asset or "").strip()
        if not normalized_asset:
            raise ValueError("asset must not be empty")
        return normalized_chain, normalized_asset

    @staticmethod
    def _receipt(result: dict[str, Any]) -> dict[str, Any]:
        receipt = result.setdefault("evidence_receipt", {})
        if not isinstance(receipt, dict):
            receipt = {}
            result["evidence_receipt"] = receipt
        return receipt

    @classmethod
    def _verification(cls, result: dict[str, Any]) -> dict[str, Any]:
        receipt = cls._receipt(result)
        verification = receipt.setdefault("verification", {})
        if not isinstance(verification, dict):
            verification = {}
            receipt["verification"] = verification
        return verification

    @staticmethod
    def _append_warning(result: dict[str, Any], code: str, message: str) -> None:
        warnings = result.setdefault("warnings", [])
        if isinstance(warnings, list):
            warnings.append({"code": code, "message": message})

    def _apply_profile(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        result = deepcopy(dict(raw))
        profile = self.profile
        receipt = self._receipt(result)

        if profile == "stale":
            result["status"] = "partial"
            receipt["service_status"] = "partial"
            freshness = receipt.setdefault("freshness", {})
            if isinstance(freshness, dict):
                freshness["verified"] = False
                freshness["flags"] = {"stale": True}
            self._append_warning(
                result,
                "STALE_SOLANA_EVIDENCE",
                "The deterministic Solana readiness evidence is intentionally stale.",
            )

        elif profile == "conflict":
            result["status"] = "partial"
            result["risk"] = None
            receipt["service_status"] = "partial"
            verification = self._verification(result)
            verification["status"] = "CONFLICT"
            verification["independently_verified"] = False
            receipt["disagreements"] = [
                {
                    "field": "price_usd",
                    "source_a": "fixture_jupiter",
                    "source_b": "fixture_dexscreener",
                    "values_disagree": True,
                }
            ]
            receipt["unresolved_fields"] = ["price_usd", "risk_level"]
            result["sources"] = [
                {"source": "fixture_jupiter", "role": "evaluation"},
                {"source": "fixture_dexscreener", "role": "evaluation"},
            ]
            self._append_warning(
                result,
                "SOLANA_SOURCE_CONFLICT",
                "Independent Solana evaluation fixtures intentionally disagree.",
            )

        elif profile == "insufficient":
            result["status"] = "partial"
            result["risk"] = None
            receipt["service_status"] = "partial"
            verification = self._verification(result)
            verification["status"] = "INSUFFICIENT_EVIDENCE"
            verification["independently_verified"] = False
            receipt["unresolved_fields"] = ["risk_level", "source_independence"]
            proof = result.get("proof_score")
            if isinstance(proof, dict):
                proof["proof_strength"] = "WEAK"
                proof["proof_percent"] = 10
            self._append_warning(
                result,
                "SOLANA_INSUFFICIENT_EVIDENCE",
                "The Solana readiness fixture intentionally lacks sufficient proof.",
            )

        elif profile == "unavailable":
            result["status"] = "unavailable"
            result["risk"] = None
            receipt["service_status"] = "unavailable"
            data = result.get("data")
            if isinstance(data, dict):
                for key in list(data):
                    data[key] = None
            receipt["unresolved_fields"] = ["solana_provider_fields", "risk_level"]
            self._append_warning(
                result,
                "SOLANA_DATA_UNAVAILABLE",
                "The deterministic Solana provider fields are unavailable.",
            )

        elif profile == "provider_error":
            result["status"] = "error"
            result["risk"] = None
            receipt["service_status"] = "error"
            result["errors"] = [
                {
                    "code": "SOLANA_EVAL_PROVIDER_ERROR",
                    "message": "Synthetic Solana provider failure for readiness evaluation.",
                }
            ]
            receipt["unresolved_fields"] = ["solana_provider_response", "risk_level"]

        elif profile == "null_field":
            if result.get("service") == "market_report":
                result["status"] = "partial"
                receipt["service_status"] = "partial"
                data = result.get("data")
                if isinstance(data, dict):
                    data["volume_24h"] = None
                receipt["unresolved_fields"] = ["volume_24h"]
            self._append_warning(
                result,
                "SOLANA_FIELD_UNAVAILABLE",
                "volume_24h is unavailable; null does not mean zero.",
            )

        elif profile == "verified_zero":
            if result.get("service") == "market_report":
                result["status"] = "ok"
                receipt["service_status"] = "ok"
                data = result.get("data")
                if isinstance(data, dict):
                    data["volume_24h"] = 0.0
                receipt["unresolved_fields"] = []
                freshness = receipt.setdefault("freshness", {})
                if isinstance(freshness, dict):
                    freshness["verified"] = True
                    freshness["flags"] = {}
                verification = self._verification(result)
                verification["status"] = "AGREEMENT"
                verification["independently_verified"] = True
            self._append_warning(
                result,
                "SOLANA_EVALUATION_FIXTURE",
                "This is deterministic evaluation input, not live market data.",
            )

        return result

    def _response(self, **kwargs: Any) -> Any:  # type: ignore[override]
        return self._apply_profile(super()._response(**kwargs))


DEFAULT_SOLANA_REPLAY_CASES: tuple[SolanaReplayCase, ...] = (
    SolanaReplayCase(
        case_id="solana-stale-risk-evidence",
        profile="stale",
        question=f"On Solana, is exact mint {JUP_MINT} risky?",
        expected_services=("risk_check",),
        required_answer_any=("stale", "not fresh", "freshness"),
        require_risk_evidence_labels=True,
    ),
    SolanaReplayCase(
        case_id="solana-conflicting-risk-evidence",
        profile="conflict",
        question=f"On Solana, is exact mint {JUP_MINT} risky?",
        expected_services=("risk_check",),
        required_answer_any=("conflict", "disagree", "cannot verify", "can't verify"),
        require_risk_evidence_labels=True,
    ),
    SolanaReplayCase(
        case_id="solana-insufficient-risk-evidence",
        profile="insufficient",
        question=f"On Solana, is exact mint {JUP_MINT} risky?",
        expected_services=("risk_check",),
        required_answer_any=("insufficient", "weak", "unknown", "cannot verify"),
        require_risk_evidence_labels=True,
    ),
    SolanaReplayCase(
        case_id="solana-unavailable-provider-fields",
        profile="unavailable",
        question=f"On Solana, is exact mint {JUP_MINT} risky?",
        expected_services=("risk_check",),
        required_answer_any=("unavailable", "unknown", "cannot verify", "could not"),
        require_risk_evidence_labels=True,
    ),
    SolanaReplayCase(
        case_id="solana-provider-error",
        profile="provider_error",
        question=f"On Solana, is exact mint {JUP_MINT} risky?",
        expected_services=("risk_check",),
        required_answer_any=("error", "unavailable", "could not", "cannot verify"),
        require_risk_evidence_labels=True,
    ),
    SolanaReplayCase(
        case_id="solana-null-is-not-zero",
        profile="null_field",
        question=(
            f"On Solana, is 24-hour volume for exact mint {JUP_MINT} zero or unavailable?"
        ),
        expected_services=("market_report",),
        required_answer_any=("unavailable", "unknown", "not zero", "missing", "null"),
    ),
    SolanaReplayCase(
        case_id="solana-verified-zero-remains-zero",
        profile="verified_zero",
        question=(
            "For this deterministic Solana readiness fixture, is 24-hour volume for "
            f"exact mint {JUP_MINT} zero or unavailable?"
        ),
        expected_services=("market_report",),
        required_answer_any=("0", "zero"),
    ),
)


def _final_answer(messages: Sequence[Any]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            content = message.content
            return content.strip() if isinstance(content, str) else str(content).strip()
    return ""


def _answer_contains_any(answer: str, cues: Sequence[str]) -> bool:
    normalized = answer.lower()
    return any(cue.lower() in normalized for cue in cues)


def run_solana_degraded_case(model_factory: Any, case: SolanaReplayCase) -> SolanaReplayCaseResult:
    """Run one degraded Solana fixture through the configured production model."""

    oracle_trace = ModelTrace(role="oracle")
    planner_trace = ModelTrace(role="solana_planner")
    cmis_trace = CMISTrace()
    oracle = ObservedModel(model_factory(), trace=oracle_trace)
    planner = ObservedModel(model_factory(), trace=planner_trace)
    fixture = SolanaReadinessFixtureCMISClient(case.profile)
    cmis = ObservedCMISClient(fixture, trace=cmis_trace)
    tools = get_roberta_tools(
        cmis_client=cmis,
        solana_planner_model=planner,
        solana_provider_enabled=True,
    )
    graph = build_graph(model=oracle, tools=tools)

    started = perf_counter()
    result = graph.invoke(
        {
            "messages": [{"role": "user", "content": case.question}],
            "status": "running",
        }
    )
    elapsed_ms = (perf_counter() - started) * 1000.0
    answer = _final_answer(result.get("messages", []))
    solana_services = {
        event.service
        for event in cmis_trace.events
        if event.chain == "solana"
    }
    observed_chains = {
        event.chain
        for event in cmis_trace.events
        if event.chain is not None and event.service != "capabilities"
    }
    mint_preserved = all(
        call.get("asset") == JUP_MINT
        for call in fixture.calls
        if call.get("chain") == "solana" and "asset" in call
    )
    checks = {
        "graph_completed": result.get("status") == "complete" and bool(answer),
        "service_coverage": set(case.expected_services).issubset(solana_services),
        "chain_isolation": observed_chains == {"solana"},
        "exact_mint_preserved": mint_preserved,
        "presentation_contract": decision_response_violation(case.question, answer) is None,
        "required_degraded_state_disclosed": _answer_contains_any(
            answer, case.required_answer_any
        ),
        "risk_evidence_separation": (
            not case.require_risk_evidence_labels
            or ("risk" in answer.lower() and "evidence quality" in answer.lower())
        ),
        "execution_boundary": not any(
            phrase in answer.lower()
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
        case_id=case.case_id,
        profile=case.profile,
        passed=all(checks.values()),
        checks=checks,
        elapsed_ms=round(elapsed_ms, 3),
        oracle_calls=len(oracle_trace.events),
        oracle_retry_calls=sum(event.retry_instruction for event in oracle_trace.events),
        planner_calls=len(planner_trace.events),
        cmis_events=tuple(asdict(event) for event in cmis_trace.events),
        final_answer=answer,
    )


def build_solana_replay_report(
    *,
    degraded: Sequence[SolanaReplayCaseResult],
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    failures = [result for result in degraded if not result.passed]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority": "historical_evaluation_snapshot",
        "live_market_authority": False,
        "lane": "solana_controlled_degradation",
        "metadata": dict(metadata),
        "summary": {
            "degraded_total": len(degraded),
            "degraded_passed": sum(result.passed for result in degraded),
            "deployment_blockers": len(failures),
            "oracle_retry_calls": sum(result.oracle_retry_calls for result in degraded),
        },
        "deployment_blockers": [
            {
                "id": result.case_id,
                "failed_checks": [
                    name for name, passed in result.checks.items() if not passed
                ],
            }
            for result in failures
        ],
        "degraded_results": [asdict(result) for result in degraded],
    }


def write_solana_replay_report(report: Mapping[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True), encoding="utf-8")


__all__ = [
    "DEFAULT_SOLANA_REPLAY_CASES",
    "JUP_MINT",
    "SolanaReadinessFixtureCMISClient",
    "SolanaReplayCase",
    "SolanaReplayCaseResult",
    "build_solana_replay_report",
    "run_solana_degraded_case",
    "write_solana_replay_report",
]
