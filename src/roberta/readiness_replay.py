"""Controlled production-model replay lanes for read-only decision readiness.

The live readiness lane measures the configured Scout -> CMIS path. This module
adds deterministic degradation and freshness challenges so production-model UX
can be exercised reproducibly without waiting for a real provider outage.

Fixtures are evaluation inputs only. They are never current market authority.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, Mapping, Sequence

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from roberta.cmis.mock import MockCMISClient
from roberta.decision_synthesis import decision_response_violation
from roberta.graph import build_graph
from roberta.memory import InMemoryDurableMemoryStore, MemoryRecord
from roberta.readiness import (
    CMISTrace,
    ModelTrace,
    ObservedCMISClient,
    ObservedModel,
)
from roberta.tools import get_roberta_tools

ReplayProfile = Literal[
    "stale",
    "conflict",
    "ambiguous",
    "insufficient",
    "unavailable",
    "provider_error",
    "null_field",
    "verified_zero",
]


@dataclass(frozen=True)
class ReplayCase:
    case_id: str
    profile: ReplayProfile
    question: str
    expected_services: tuple[str, ...]
    required_answer_any: tuple[str, ...]
    forbidden_answer_all: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReplayCaseResult:
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


class ReadinessFixtureCMISClient(MockCMISClient):
    """CMIS-compatible deterministic fixture client for degraded evidence states."""

    def __init__(self, profile: ReplayProfile) -> None:
        super().__init__(scenario="test_only")
        self.profile = profile

    @staticmethod
    def _append_warning(result: dict[str, Any], code: str, message: str) -> None:
        warnings = result.setdefault("warnings", [])
        if isinstance(warnings, list):
            warnings.append({"code": code, "message": message})

    @staticmethod
    def _verification(result: dict[str, Any]) -> dict[str, Any]:
        receipt = result.setdefault("evidence_receipt", {})
        if not isinstance(receipt, dict):
            receipt = {}
            result["evidence_receipt"] = receipt
        verification = receipt.setdefault("verification", {})
        if not isinstance(verification, dict):
            verification = {}
            receipt["verification"] = verification
        return verification

    @staticmethod
    def _receipt(result: dict[str, Any]) -> dict[str, Any]:
        receipt = result.setdefault("evidence_receipt", {})
        if not isinstance(receipt, dict):
            receipt = {}
            result["evidence_receipt"] = receipt
        return receipt

    def _apply_profile(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        result = deepcopy(dict(raw))
        profile = self.profile

        if profile == "stale":
            result["status"] = "partial"
            receipt = self._receipt(result)
            freshness = receipt.setdefault("freshness", {})
            if isinstance(freshness, dict):
                freshness["verified"] = False
                freshness["flags"] = {"stale": True}
            self._append_warning(
                result,
                "STALE_EVIDENCE",
                "The deterministic evaluation evidence is intentionally stale.",
            )

        elif profile == "conflict":
            result["status"] = "partial"
            result["risk"] = None
            receipt = self._receipt(result)
            verification = self._verification(result)
            verification["status"] = "CONFLICT"
            verification["independently_verified"] = False
            receipt["disagreements"] = [
                {
                    "field": "liquidity_usd",
                    "source_a": "fixture_source_a",
                    "source_b": "fixture_source_b",
                    "values_disagree": True,
                }
            ]
            receipt["unresolved_fields"] = ["liquidity_usd", "risk_level"]
            result["sources"] = [
                {"source": "fixture_source_a", "role": "evaluation"},
                {"source": "fixture_source_b", "role": "evaluation"},
            ]
            self._append_warning(
                result,
                "SOURCE_CONFLICT",
                "Independent evaluation fixtures intentionally disagree.",
            )

        elif profile == "ambiguous":
            result["status"] = "ambiguous"
            result["risk"] = None
            result["asset"] = {
                "query": "AGI",
                "candidates": [
                    {"symbol": "AGI", "address": "fixture_candidate_a"},
                    {"symbol": "AGI", "address": "fixture_candidate_b"},
                ],
            }
            receipt = self._receipt(result)
            receipt["unresolved_fields"] = ["asset_identity", "risk_level"]
            self._append_warning(
                result,
                "AMBIGUOUS_ASSET",
                "The evaluation symbol resolves to more than one candidate.",
            )

        elif profile == "insufficient":
            result["status"] = "partial"
            result["risk"] = None
            verification = self._verification(result)
            verification["status"] = "INSUFFICIENT_EVIDENCE"
            verification["independently_verified"] = False
            receipt = self._receipt(result)
            receipt["unresolved_fields"] = ["risk_level", "source_independence"]
            proof = result.get("proof_score")
            if isinstance(proof, dict):
                proof["proof_strength"] = "WEAK"
                proof["proof_percent"] = 10
            self._append_warning(
                result,
                "INSUFFICIENT_EVIDENCE",
                "The evaluation fixture intentionally lacks enough proof.",
            )

        elif profile == "unavailable":
            result["status"] = "unavailable"
            result["risk"] = None
            data = result.get("data")
            if isinstance(data, dict):
                for key in list(data):
                    if key not in {"question", "metric", "limit"}:
                        data[key] = None
            receipt = self._receipt(result)
            receipt["unresolved_fields"] = ["provider_fields", "risk_level"]
            self._append_warning(
                result,
                "DATA_UNAVAILABLE",
                "The deterministic evaluation provider data is unavailable.",
            )

        elif profile == "provider_error":
            result["status"] = "error"
            result["risk"] = None
            result["errors"] = [
                {
                    "code": "EVAL_PROVIDER_ERROR",
                    "message": "Synthetic read-only provider failure for readiness evaluation.",
                }
            ]
            receipt = self._receipt(result)
            receipt["unresolved_fields"] = ["provider_response", "risk_level"]

        elif profile == "null_field":
            result["status"] = "partial"
            data = result.get("data")
            if isinstance(data, dict):
                data["volume_24h"] = None
            receipt = self._receipt(result)
            receipt["unresolved_fields"] = ["volume_24h"]
            self._append_warning(
                result,
                "FIELD_UNAVAILABLE",
                "volume_24h is intentionally unavailable; null does not mean zero.",
            )

        elif profile == "verified_zero":
            if result.get("service") == "market_report":
                result["status"] = "ok"
                data = result.get("data")
                if isinstance(data, dict):
                    data["volume_24h"] = 0.0
                receipt = self._receipt(result)
                receipt["unresolved_fields"] = []
                freshness = receipt.setdefault("freshness", {})
                if isinstance(freshness, dict):
                    freshness["verified"] = True
                verification = self._verification(result)
                verification["status"] = "AGREEMENT"
                verification["independently_verified"] = True
            self._append_warning(
                result,
                "EVALUATION_FIXTURE",
                "This is deterministic evaluation input, not live market data.",
            )

        return result

    def _response(self, **kwargs: Any) -> Any:  # type: ignore[override]
        return self._apply_profile(super()._response(**kwargs))


DEFAULT_REPLAY_CASES: tuple[ReplayCase, ...] = (
    ReplayCase(
        case_id="stale-risk-evidence",
        profile="stale",
        question="On X1, is AGI risky?",
        expected_services=("risk_check", "market_report", "tokenomics"),
        required_answer_any=("stale", "not fresh", "freshness"),
    ),
    ReplayCase(
        case_id="conflicting-risk-evidence",
        profile="conflict",
        question="On X1, is AGI risky?",
        expected_services=("risk_check", "market_report", "tokenomics"),
        required_answer_any=("conflict", "disagree", "cannot verify", "can't verify"),
    ),
    ReplayCase(
        case_id="ambiguous-asset",
        profile="ambiguous",
        question="On X1, is AGI risky?",
        expected_services=("risk_check", "market_report", "tokenomics"),
        required_answer_any=("ambiguous", "multiple", "identifier", "address"),
    ),
    ReplayCase(
        case_id="insufficient-risk-evidence",
        profile="insufficient",
        question="On X1, is AGI risky?",
        expected_services=("risk_check", "market_report", "tokenomics"),
        required_answer_any=("insufficient", "weak", "unknown", "cannot verify"),
    ),
    ReplayCase(
        case_id="unavailable-provider-fields",
        profile="unavailable",
        question="On X1, is AGI risky?",
        expected_services=("risk_check", "market_report", "tokenomics"),
        required_answer_any=("unavailable", "unknown", "cannot verify", "could not"),
    ),
    ReplayCase(
        case_id="provider-error",
        profile="provider_error",
        question="On X1, is AGI risky?",
        expected_services=("risk_check", "market_report", "tokenomics"),
        required_answer_any=("error", "unavailable", "could not", "cannot verify"),
    ),
    ReplayCase(
        case_id="null-is-not-zero",
        profile="null_field",
        question="On X1, is AGI 24-hour volume zero or unavailable?",
        expected_services=("market_report",),
        required_answer_any=("unavailable", "unknown", "not zero", "missing"),
    ),
    ReplayCase(
        case_id="verified-zero-remains-zero",
        profile="verified_zero",
        question=(
            "For this deterministic X1 readiness fixture, is AGI 24-hour volume "
            "zero or unavailable?"
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


def _service_names(events: Sequence[Any]) -> set[str]:
    return {
        str(event.service)
        for event in events
        if getattr(event, "chain", None) == "x1"
    }


def _answer_contains_any(answer: str, cues: Sequence[str]) -> bool:
    normalized = answer.lower()
    return any(cue.lower() in normalized for cue in cues)


def run_degraded_case(model_factory: Any, case: ReplayCase) -> ReplayCaseResult:
    """Run one fixture through the configured production model and normal graph."""

    oracle_trace = ModelTrace(role="oracle")
    planner_trace = ModelTrace(role="x1_planner")
    cmis_trace = CMISTrace()
    oracle = ObservedModel(model_factory(), trace=oracle_trace)
    planner = ObservedModel(model_factory(), trace=planner_trace)
    cmis = ObservedCMISClient(
        ReadinessFixtureCMISClient(case.profile),
        trace=cmis_trace,
    )
    tools = get_roberta_tools(cmis_client=cmis, x1_planner_model=planner)
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
    services = _service_names(cmis_trace.events)
    checks = {
        "graph_completed": result.get("status") == "complete" and bool(answer),
        "service_coverage": set(case.expected_services).issubset(services),
        "presentation_contract": decision_response_violation(case.question, answer) is None,
        "required_degraded_state_disclosed": _answer_contains_any(
            answer, case.required_answer_any
        ),
        "forbidden_language_absent": not all(
            cue.lower() in answer.lower() for cue in case.forbidden_answer_all
        ) if case.forbidden_answer_all else True,
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
    return ReplayCaseResult(
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


def run_freshness_challenge(model_factory: Any) -> dict[str, Any]:
    """Prove stale checkpoint/memory context cannot replace a fresh Scout call."""

    historical_value = "$999.99"
    memory = InMemoryDurableMemoryStore(
        [
            MemoryRecord(
                key="eval:agi:historical_market",
                category="market_snapshot",
                content=(
                    f"Historical X1 AGI snapshot only: price was {historical_value}; "
                    "this is not current market truth."
                ),
                topics=("AGI", "X1", "market", "price", "risk"),
                source="readiness_fixture",
                authority="historical_context",
                created_at="2026-08-01T00:00:00Z",
                updated_at="2026-08-01T00:00:00Z",
            )
        ]
    )
    oracle_trace = ModelTrace(role="oracle")
    planner_trace = ModelTrace(role="x1_planner")
    cmis_trace = CMISTrace()
    oracle = ObservedModel(model_factory(), trace=oracle_trace)
    planner = ObservedModel(model_factory(), trace=planner_trace)
    cmis = ObservedCMISClient(MockCMISClient(scenario="test_only"), trace=cmis_trace)
    tools = get_roberta_tools(cmis_client=cmis, x1_planner_model=planner)
    graph = build_graph(model=oracle, tools=tools, memory_store=memory)

    messages = [
        HumanMessage(content="What was the earlier AGI snapshot?"),
        AIMessage(
            content=(
                f"Historical context only: the earlier snapshot said {historical_value}. "
                "That value is not current."
            )
        ),
        HumanMessage(content="What is AGI's current market risk on X1 right now?"),
    ]
    cmis_start = cmis_trace.snapshot()
    started = perf_counter()
    result = graph.invoke({"messages": messages, "status": "running"})
    elapsed_ms = (perf_counter() - started) * 1000.0
    new_cmis_events = cmis_trace.since(cmis_start)
    answer = _final_answer(result.get("messages", []))
    services = _service_names(new_cmis_events)
    checks = {
        "graph_completed": result.get("status") == "complete" and bool(answer),
        "fresh_scout_cmis_requery": bool(new_cmis_events)
        and "risk_check" in services
        and "market_report" in services,
        "historical_context_not_sole_truth": bool(new_cmis_events),
        "execution_boundary": not any(
            phrase in answer.lower()
            for phrase in ("i will sign", "i'll sign", "i will execute", "i'll execute")
        ),
    }
    return {
        "challenge_id": "checkpoint-hxmp-current-truth",
        "passed": all(checks.values()),
        "checks": checks,
        "elapsed_ms": round(elapsed_ms, 3),
        "oracle_calls": len(oracle_trace.events),
        "planner_calls": len(planner_trace.events),
        "cmis_events": [asdict(event) for event in new_cmis_events],
        "final_answer": answer,
        "historical_fixture_value": historical_value,
        "historical_fixture_authority": "historical_context",
    }


def build_replay_report(
    *,
    degraded: Sequence[ReplayCaseResult],
    freshness: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    failures = [result for result in degraded if not result.passed]
    if not freshness.get("passed"):
        failures.append(freshness)  # type: ignore[arg-type]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority": "historical_evaluation_snapshot",
        "live_market_authority": False,
        "lane": "controlled_degradation_and_freshness",
        "metadata": dict(metadata),
        "summary": {
            "degraded_total": len(degraded),
            "degraded_passed": sum(result.passed for result in degraded),
            "freshness_passed": bool(freshness.get("passed")),
            "deployment_blockers": len(failures),
            "oracle_retry_calls": sum(result.oracle_retry_calls for result in degraded),
        },
        "deployment_blockers": [
            {
                "id": (
                    item.case_id
                    if isinstance(item, ReplayCaseResult)
                    else str(item.get("challenge_id"))
                ),
                "failed_checks": [
                    name
                    for name, passed in (
                        item.checks.items()
                        if isinstance(item, ReplayCaseResult)
                        else item.get("checks", {}).items()
                    )
                    if not passed
                ],
            }
            for item in failures
        ],
        "degraded_results": [asdict(result) for result in degraded],
        "freshness_result": dict(freshness),
    }


def write_replay_report(report: Mapping[str, Any], path: str | Path) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dict(report), indent=2, sort_keys=True), encoding="utf-8")


__all__ = [
    "DEFAULT_REPLAY_CASES",
    "ReadinessFixtureCMISClient",
    "ReplayCase",
    "ReplayCaseResult",
    "build_replay_report",
    "run_degraded_case",
    "run_freshness_challenge",
    "write_replay_report",
]
