"""Read-only production-readiness evaluation helpers for Roberta.

This module observes the accepted runtime without changing its authority path.
It records model and CMIS timing/call metadata, runs representative scenarios,
and evaluates deterministic presentation/route invariants. It never computes
market facts, risk, proof, or execution decisions.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any, Mapping, Sequence

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from roberta.decision_synthesis import (
    decision_response_violation,
    decision_synthesis_failure_text,
    technical_decision_detail_requested,
)
from roberta.recommendation_policy import recommendation_intent

_ALLOWED_EVALUATION_SERVICES = frozenset(
    {
        "asset_lookup",
        "market_report",
        "instant_x1_scan",
        "rank",
        "historical_compare",
        "tokenomics",
        "burn_intelligence",
        "risk_check",
        "pre_trade_check",
        "verification_evidence",
    }
)
_UNCERTAINTY_STATUS_TOKENS = frozenset(
    {
        "partial",
        "unavailable",
        "ambiguous",
        "error",
        "conflict",
        "insufficient_evidence",
        "unverified",
        "stale",
        "unknown",
    }
)
_UNCERTAINTY_LANGUAGE = (
    "unknown",
    "unavailable",
    "not available",
    "missing",
    "partial",
    "ambiguous",
    "conflict",
    "insufficient",
    "stale",
    "could not",
    "couldn't",
    "cannot verify",
    "can't verify",
    "error",
)
_EXECUTION_PROMISES = (
    "i will sign",
    "i'll sign",
    "i will broadcast",
    "i'll broadcast",
    "i will execute",
    "i'll execute",
    "execution_authorized=true",
    '"execution_authorized": true',
)


@dataclass(frozen=True)
class ReadinessScenario:
    """One reproducible read-only evaluation scenario."""

    scenario_id: str
    turns: tuple[str, ...]
    expected_chains: tuple[str, ...] = ()
    expected_services: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    requires_solana: bool = False
    require_risk_evidence_labels: bool = False
    technical_detail_expected: bool = False
    control: bool = False


@dataclass(frozen=True)
class ModelObservation:
    role: str
    elapsed_ms: float
    retry_instruction: bool
    error_type: str | None


@dataclass(frozen=True)
class CMISObservation:
    service: str
    chain: str | None
    status: str | None
    elapsed_ms: float
    error_type: str | None


@dataclass
class ModelTrace:
    """Mutable event sink shared by bound wrappers for one model role."""

    role: str
    events: list[ModelObservation] = field(default_factory=list)

    def snapshot(self) -> int:
        return len(self.events)

    def since(self, start: int) -> list[ModelObservation]:
        return list(self.events[start:])


@dataclass
class CMISTrace:
    """Mutable event sink for provider-neutral CMIS calls."""

    events: list[CMISObservation] = field(default_factory=list)

    def snapshot(self) -> int:
        return len(self.events)

    def since(self, start: int) -> list[CMISObservation]:
        return list(self.events[start:])


class ObservedModel:
    """Transparent invoke/bind_tools wrapper that records timing and retry calls."""

    def __init__(self, delegate: Any, *, trace: ModelTrace) -> None:
        self._delegate = delegate
        self.trace = trace

    def bind_tools(self, tools: Sequence[Any]) -> "ObservedModel":
        if not hasattr(self._delegate, "bind_tools"):
            raise TypeError("Observed model delegate must implement bind_tools(tools).")
        return ObservedModel(self._delegate.bind_tools(list(tools)), trace=self.trace)

    def invoke(self, messages: Sequence[Any], *args: Any, **kwargs: Any) -> Any:
        retry_instruction = any(
            isinstance(message, SystemMessage)
            and "previous recommendation draft violated"
            in str(getattr(message, "content", "")).lower()
            for message in messages
        )
        started = perf_counter()
        error_type: str | None = None
        try:
            return self._delegate.invoke(messages, *args, **kwargs)
        except Exception as exc:
            error_type = type(exc).__name__
            raise
        finally:
            self.trace.events.append(
                ModelObservation(
                    role=self.trace.role,
                    elapsed_ms=round((perf_counter() - started) * 1000.0, 3),
                    retry_instruction=retry_instruction,
                    error_type=error_type,
                )
            )


class ObservedCMISClient:
    """Transparent CMIS client wrapper that records latency/status without payloads."""

    def __init__(self, delegate: Any, *, trace: CMISTrace | None = None) -> None:
        self._delegate = delegate
        self.trace = trace or CMISTrace()

    def _call(
        self,
        service: str,
        *,
        chain: str | None,
        func: Any,
        kwargs: Mapping[str, Any],
    ) -> Any:
        started = perf_counter()
        status: str | None = None
        error_type: str | None = None
        try:
            result = func(**dict(kwargs))
            if isinstance(result, Mapping):
                raw_status = result.get("status")
                status = str(raw_status) if raw_status is not None else None
            return result
        except Exception as exc:
            error_type = type(exc).__name__
            raise
        finally:
            self.trace.events.append(
                CMISObservation(
                    service=service,
                    chain=chain,
                    status=status,
                    elapsed_ms=round((perf_counter() - started) * 1000.0, 3),
                    error_type=error_type,
                )
            )

    def capabilities(self) -> Any:
        return self._call(
            "capabilities",
            chain=None,
            func=self._delegate.capabilities,
            kwargs={},
        )

    def market_report(self, *, chain: str, asset: str) -> Any:
        return self._call(
            "market_report",
            chain=chain,
            func=self._delegate.market_report,
            kwargs={"chain": chain, "asset": asset},
        )

    def instant_x1_scan(self, *, chain: str, asset: str) -> Any:
        return self._call(
            "instant_x1_scan",
            chain=chain,
            func=self._delegate.instant_x1_scan,
            kwargs={"chain": chain, "asset": asset},
        )

    def rank(self, *, chain: str, metric: str = "volume", limit: int = 10) -> Any:
        return self._call(
            "rank",
            chain=chain,
            func=self._delegate.rank,
            kwargs={"chain": chain, "metric": metric, "limit": limit},
        )

    def historical_compare(self, *, chain: str, asset: str, question: str) -> Any:
        return self._call(
            "historical_compare",
            chain=chain,
            func=self._delegate.historical_compare,
            kwargs={"chain": chain, "asset": asset, "question": question},
        )

    def tokenomics(self, *, chain: str, asset: str) -> Any:
        return self._call(
            "tokenomics",
            chain=chain,
            func=self._delegate.tokenomics,
            kwargs={"chain": chain, "asset": asset},
        )

    def burn_intelligence(self, *, chain: str, asset: str) -> Any:
        return self._call(
            "burn_intelligence",
            chain=chain,
            func=self._delegate.burn_intelligence,
            kwargs={"chain": chain, "asset": asset},
        )

    def risk_check(self, *, chain: str, asset: str) -> Any:
        return self._call(
            "risk_check",
            chain=chain,
            func=self._delegate.risk_check,
            kwargs={"chain": chain, "asset": asset},
        )

    def pre_trade_check(
        self,
        *,
        chain: str,
        asset: str,
        action: str,
        amount_usd: float,
    ) -> Any:
        return self._call(
            "pre_trade_check",
            chain=chain,
            func=self._delegate.pre_trade_check,
            kwargs={
                "chain": chain,
                "asset": asset,
                "action": action,
                "amount_usd": amount_usd,
            },
        )

    def verification_evidence(
        self,
        *,
        chain: str,
        evidence_id: str | None = None,
        fact_type: str | None = None,
        subject_id: str | None = None,
    ) -> Any:
        return self._call(
            "verification_evidence",
            chain=chain,
            func=self._delegate.verification_evidence,
            kwargs={
                "chain": chain,
                "evidence_id": evidence_id,
                "fact_type": fact_type,
                "subject_id": subject_id,
            },
        )


@dataclass(frozen=True)
class ReadinessResult:
    scenario_id: str
    passed: bool
    checks: Mapping[str, bool]
    total_elapsed_ms: float
    oracle_calls: int
    oracle_retry_calls: int
    oracle_model_elapsed_ms: float
    planner_calls: int
    planner_model_elapsed_ms: float
    cmis_elapsed_ms: float
    cmis_events: tuple[Mapping[str, Any], ...]
    final_answer: str
    fail_closed: bool
    uncertainty_detected: bool
    skipped: bool = False
    skip_reason: str | None = None


def _scenario_from_mapping(value: Mapping[str, Any]) -> ReadinessScenario:
    scenario_id = str(value.get("id") or "").strip()
    turns_raw = value.get("turns")
    if not scenario_id:
        raise ValueError("readiness scenario id is required")
    if not isinstance(turns_raw, list) or not turns_raw:
        raise ValueError(f"scenario {scenario_id!r} must contain non-empty turns")
    turns = tuple(str(item).strip() for item in turns_raw if str(item).strip())
    if not turns:
        raise ValueError(f"scenario {scenario_id!r} must contain non-empty turns")

    expected_services_raw = value.get("expected_services") or {}
    if not isinstance(expected_services_raw, Mapping):
        raise ValueError(f"scenario {scenario_id!r} expected_services must be an object")
    expected_services: dict[str, tuple[str, ...]] = {}
    for raw_chain, raw_services in expected_services_raw.items():
        chain = str(raw_chain).strip().lower()
        if not chain or not isinstance(raw_services, list):
            raise ValueError(f"scenario {scenario_id!r} has invalid service coverage")
        services = tuple(str(item).strip() for item in raw_services if str(item).strip())
        unknown = sorted(set(services).difference(_ALLOWED_EVALUATION_SERVICES))
        if unknown:
            raise ValueError(
                f"scenario {scenario_id!r} contains non-read-only/unknown services: "
                + ", ".join(unknown)
            )
        expected_services[chain] = services

    expected_chains_raw = value.get("expected_chains") or list(expected_services)
    if not isinstance(expected_chains_raw, list):
        raise ValueError(f"scenario {scenario_id!r} expected_chains must be a list")
    expected_chains = tuple(
        str(item).strip().lower()
        for item in expected_chains_raw
        if str(item).strip()
    )
    return ReadinessScenario(
        scenario_id=scenario_id,
        turns=turns,
        expected_chains=expected_chains,
        expected_services=expected_services,
        requires_solana=bool(value.get("requires_solana", False)),
        require_risk_evidence_labels=bool(
            value.get("require_risk_evidence_labels", False)
        ),
        technical_detail_expected=bool(value.get("technical_detail_expected", False)),
        control=bool(value.get("control", False)),
    )


def load_readiness_scenarios(path: str | Path) -> list[ReadinessScenario]:
    """Load and validate a versioned JSON readiness corpus."""

    decoded = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(decoded, Mapping):
        raise ValueError("readiness corpus must be a JSON object")
    if decoded.get("schema_version") != 1:
        raise ValueError("unsupported readiness corpus schema_version")
    scenarios_raw = decoded.get("scenarios")
    if not isinstance(scenarios_raw, list) or not scenarios_raw:
        raise ValueError("readiness corpus must include scenarios")
    scenarios = [
        _scenario_from_mapping(item)
        for item in scenarios_raw
        if isinstance(item, Mapping)
    ]
    if len(scenarios) != len(scenarios_raw):
        raise ValueError("every readiness scenario must be a JSON object")
    return scenarios


def _contains_uncertainty(value: Any) -> bool:
    if isinstance(value, Mapping):
        for raw_key, item in value.items():
            key = str(raw_key).strip().lower()
            if key in {"status", "verification_status", "state"}:
                normalized = str(item or "").strip().lower()
                if normalized in _UNCERTAINTY_STATUS_TOKENS:
                    return True
            if key in {
                "warnings",
                "errors",
                "unresolved_fields",
                "disagreements",
                "limitations",
                "unknown_categories",
            } and bool(item):
                return True
            if key in {"freshness_verified", "freshness"} and item is False:
                return True
            if _contains_uncertainty(item):
                return True
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(_contains_uncertainty(item) for item in value)
    return False


def _tool_uncertainty_detected(messages: Sequence[Any]) -> bool:
    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        content = message.content
        if not isinstance(content, str) or not content.strip():
            continue
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError:
            continue
        if _contains_uncertainty(decoded):
            return True
    return False


def _final_answer(messages: Sequence[Any]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            content = message.content
            return content.strip() if isinstance(content, str) else str(content).strip()
    return ""


def _tool_names(messages: Sequence[Any]) -> set[str]:
    return {
        str(message.name)
        for message in messages
        if isinstance(message, ToolMessage) and message.name
    }


def _service_coverage(
    scenario: ReadinessScenario,
    cmis_events: Sequence[CMISObservation],
) -> bool:
    by_chain: dict[str, set[str]] = {}
    for event in cmis_events:
        if event.chain is None:
            continue
        by_chain.setdefault(event.chain.lower(), set()).add(event.service)
    return all(
        set(services).issubset(by_chain.get(chain, set()))
        for chain, services in scenario.expected_services.items()
    )


def _chain_isolation(
    scenario: ReadinessScenario,
    cmis_events: Sequence[CMISObservation],
) -> bool:
    observed = {
        event.chain.lower()
        for event in cmis_events
        if event.chain is not None and event.service != "capabilities"
    }
    expected = set(scenario.expected_chains)
    if scenario.control:
        return not observed
    return observed.issubset(expected) and expected.issubset(observed)


def _execution_boundary_ok(answer: str, tool_names: set[str]) -> bool:
    normalized = answer.lower()
    if any(phrase in normalized for phrase in _EXECUTION_PROMISES):
        return False
    return tool_names.issubset({"x1_scout_investigate", "solana_scout_investigate"})


def _uncertainty_language_present(answer: str) -> bool:
    normalized = answer.lower()
    return any(cue in normalized for cue in _UNCERTAINTY_LANGUAGE)


def evaluate_readiness_result(
    scenario: ReadinessScenario,
    *,
    graph_result: Mapping[str, Any],
    total_elapsed_ms: float,
    oracle_events: Sequence[ModelObservation],
    planner_events: Sequence[ModelObservation],
    cmis_events: Sequence[CMISObservation],
) -> ReadinessResult:
    """Evaluate deterministic readiness invariants for one completed scenario."""

    messages = graph_result.get("messages")
    if not isinstance(messages, Sequence):
        messages = []
    answer = _final_answer(messages)
    question = scenario.turns[-1]
    intent = recommendation_intent(question)
    uncertainty_detected = _tool_uncertainty_detected(messages) or any(
        (event.status or "").lower() in _UNCERTAINTY_STATUS_TOKENS
        or event.error_type is not None
        for event in cmis_events
    )
    technical_requested = technical_decision_detail_requested(question)
    risk_evidence_labels_ok = (
        not scenario.require_risk_evidence_labels
        or technical_requested
        or ("risk" in answer.lower() and "evidence quality" in answer.lower())
    )
    unknowns_ok = (
        not uncertainty_detected
        or scenario.control
        or technical_requested
        or _uncertainty_language_present(answer)
    )
    checks = {
        "graph_completed": graph_result.get("status") == "complete" and bool(answer),
        "service_coverage": _service_coverage(scenario, cmis_events),
        "chain_isolation": _chain_isolation(scenario, cmis_events),
        "presentation_contract": (
            True
            if scenario.control or intent == "general"
            else decision_response_violation(question, answer) is None
        ),
        "risk_evidence_separation": risk_evidence_labels_ok,
        "important_unknowns": unknowns_ok,
        "technical_progressive_disclosure": (
            not scenario.technical_detail_expected or technical_requested
        ),
        "execution_boundary": _execution_boundary_ok(answer, _tool_names(messages)),
    }
    return ReadinessResult(
        scenario_id=scenario.scenario_id,
        passed=all(checks.values()),
        checks=checks,
        total_elapsed_ms=round(total_elapsed_ms, 3),
        oracle_calls=len(oracle_events),
        oracle_retry_calls=sum(event.retry_instruction for event in oracle_events),
        oracle_model_elapsed_ms=round(
            sum(event.elapsed_ms for event in oracle_events), 3
        ),
        planner_calls=len(planner_events),
        planner_model_elapsed_ms=round(
            sum(event.elapsed_ms for event in planner_events), 3
        ),
        cmis_elapsed_ms=round(sum(event.elapsed_ms for event in cmis_events), 3),
        cmis_events=tuple(asdict(event) for event in cmis_events),
        final_answer=answer,
        fail_closed=answer == decision_synthesis_failure_text(),
        uncertainty_detected=uncertainty_detected,
    )


def skipped_readiness_result(
    scenario: ReadinessScenario,
    *,
    reason: str,
) -> ReadinessResult:
    return ReadinessResult(
        scenario_id=scenario.scenario_id,
        passed=False,
        checks={},
        total_elapsed_ms=0.0,
        oracle_calls=0,
        oracle_retry_calls=0,
        oracle_model_elapsed_ms=0.0,
        planner_calls=0,
        planner_model_elapsed_ms=0.0,
        cmis_elapsed_ms=0.0,
        cmis_events=(),
        final_answer="",
        fail_closed=False,
        uncertainty_detected=False,
        skipped=True,
        skip_reason=reason,
    )


def run_readiness_scenario(
    graph: Any,
    scenario: ReadinessScenario,
    *,
    oracle_trace: ModelTrace,
    planner_traces: Sequence[ModelTrace],
    cmis_trace: CMISTrace,
) -> ReadinessResult:
    """Run one scenario through the existing graph and measure observable behavior."""

    oracle_start = oracle_trace.snapshot()
    planner_starts = [(trace, trace.snapshot()) for trace in planner_traces]
    cmis_start = cmis_trace.snapshot()
    started = perf_counter()
    state: Mapping[str, Any] | None = None

    for index, turn in enumerate(scenario.turns):
        if index == 0:
            invocation = {
                "messages": [{"role": "user", "content": turn}],
                "status": "running",
            }
        else:
            prior_messages = list((state or {}).get("messages", []))
            invocation = {
                "messages": [*prior_messages, HumanMessage(content=turn)],
                "status": "running",
            }
        state = graph.invoke(invocation)

    total_elapsed_ms = (perf_counter() - started) * 1000.0
    planner_events: list[ModelObservation] = []
    for trace, start in planner_starts:
        planner_events.extend(trace.since(start))
    return evaluate_readiness_result(
        scenario,
        graph_result=state or {},
        total_elapsed_ms=total_elapsed_ms,
        oracle_events=oracle_trace.since(oracle_start),
        planner_events=planner_events,
        cmis_events=cmis_trace.since(cmis_start),
    )


def build_readiness_report(
    *,
    results: Sequence[ReadinessResult],
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a historical, non-authoritative evaluation report."""

    completed = [result for result in results if not result.skipped]
    skipped = [result for result in results if result.skipped]
    failed = [result for result in completed if not result.passed]
    provider_failures = [
        event
        for result in completed
        for event in result.cmis_events
        if event.get("error_type") or event.get("status") == "error"
    ]
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authority": "historical_evaluation_snapshot",
        "live_market_authority": False,
        "metadata": dict(metadata),
        "summary": {
            "total": len(results),
            "completed": len(completed),
            "passed": sum(result.passed for result in completed),
            "failed": len(failed),
            "skipped": len(skipped),
            "oracle_retry_calls": sum(
                result.oracle_retry_calls for result in completed
            ),
            "fail_closed_count": sum(result.fail_closed for result in completed),
            "provider_error_events": len(provider_failures),
        },
        "deployment_blockers": [
            {
                "scenario_id": result.scenario_id,
                "failed_checks": [
                    name for name, passed in result.checks.items() if not passed
                ],
            }
            for result in failed
        ],
        "results": [asdict(result) for result in results],
    }


__all__ = [
    "CMISObservation",
    "CMISTrace",
    "ModelObservation",
    "ModelTrace",
    "ObservedCMISClient",
    "ObservedModel",
    "ReadinessResult",
    "ReadinessScenario",
    "build_readiness_report",
    "evaluate_readiness_result",
    "load_readiness_scenarios",
    "run_readiness_scenario",
    "skipped_readiness_result",
]
