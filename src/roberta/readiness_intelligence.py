"""Controlled production-model replay for promoted X1 concentration intelligence.

The fixture is historical evaluation input only. It exercises the normal Roberta
-> X1 Scout path and never becomes a source of current market truth.
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
from roberta.readiness_replay import ReplayCaseResult
from roberta.tools import get_roberta_tools

SERVICE = "concentration_change_intelligence"
EVIDENCE_ID = "ie_" + ("a" * 64)


class IntelligenceReadinessFixtureCMISClient(MockCMISClient):
    """One partial, scope-limited CMIS intelligence fixture."""

    def concentration_change_intelligence(
        self,
        *,
        chain: str,
        asset: str,
        intelligence_evidence_id: str,
    ) -> dict[str, Any]:
        if chain != "x1" or asset != "AGI" or intelligence_evidence_id != EVIDENCE_ID:
            return {
                "service": SERVICE,
                "chain": chain,
                "status": "unavailable",
                "asset": {"query": asset},
                "data": {},
                "risk": None,
                "confidence": {},
                "sources": [],
                "observed_at": None,
                "warnings": [{
                    "code": "INTELLIGENCE_FIXTURE_SCOPE_MISMATCH",
                    "message": "The readiness fixture accepts one exact X1 AGI intelligence id.",
                }],
                "errors": [],
            }

        return {
            "service": SERVICE,
            "chain": "x1",
            "status": "partial",
            "asset": {"canonical_id": "AGI"},
            "data": {
                "contract_version": "concentration_change_intelligence/v1",
                "read_only": True,
                "public_service_promoted": True,
                "scout_reliance_promoted": True,
                "promotion_scope": "cmis_owned_top_account_concentration_change_evidence_by_id",
                "accepted_conclusion_type": "top_account_concentration_change",
                "asset_id": "AGI",
                "facts": {
                    "conclusion_type": "top_account_concentration_change",
                    "chain": "x1",
                    "asset_id": "AGI",
                    "before_ratio": 0.20,
                    "after_ratio": 0.24,
                    "delta_ratio": 0.04,
                    "delta_bps": 400,
                    "direction": "INCREASED",
                    "scope": "observed_top_token_accounts",
                },
                "policy_assessment": None,
                "risk_interpretation": None,
                "evidence": {
                    "intelligence_evidence_id": EVIDENCE_ID,
                    "receipt_ids": ["er_readiness_concentration"],
                    "proof_records": [{
                        "receipt_id": "er_readiness_concentration",
                        "proof_strength": "MODERATE",
                        "proof_percent": 75.0,
                        "method": "readiness_fixture",
                    }],
                    "freshness_verified": None,
                    "unresolved_fields": ["beneficial_owner_identity"],
                    "limitations": [
                        "observed_top_token_account_scope_is_incomplete",
                        "token_accounts_are_not_unique_holders",
                        "beneficial_owner_identity_unverified",
                        "proof_strength_remains_separate_from_risk",
                    ],
                    "intelligence_evidence": {
                        "intelligence_evidence_id": EVIDENCE_ID,
                        "conclusion_type": "top_account_concentration_change",
                    },
                },
                "proof_strength_separate_from_risk": True,
                "behavioral_interpretation_added": False,
                "provider_assertion_promoted": False,
                "execution_authorized": False,
            },
            "risk": None,
            "confidence": {
                "cmis_owned_evidence_resolved": True,
                "deterministic_evidence_revalidated": True,
                "freshness_verified": None,
                "unresolved_fields": ["beneficial_owner_identity"],
            },
            "sources": [{"source": "readiness_fixture", "role": "evaluation"}],
            "observed_at": "2026-08-20T02:00:00Z",
            "warnings": [{
                "code": "intelligence_evidence_freshness_unknown",
                "message": "Evidence freshness is not explicitly verified by every authoritative receipt.",
            }, {
                "code": "intelligence_evidence_unresolved_fields",
                "message": "Authoritative Evidence Receipts retain unresolved evidence fields.",
            }],
            "errors": [],
        }


class ObservedIntelligenceFixtureCMISClient(ObservedCMISClient):
    """Observed wrapper extension for the promoted service only."""

    def concentration_change_intelligence(
        self,
        *,
        chain: str,
        asset: str,
        intelligence_evidence_id: str,
    ) -> Any:
        return self._call(
            SERVICE,
            chain=chain,
            func=self._delegate.concentration_change_intelligence,
            kwargs={
                "chain": chain,
                "asset": asset,
                "intelligence_evidence_id": intelligence_evidence_id,
            },
        )


def _final_answer(messages: Sequence[Any]) -> str:
    for message in reversed(messages):
        if isinstance(message, AIMessage) and not message.tool_calls:
            content = message.content
            return content.strip() if isinstance(content, str) else str(content).strip()
    return ""


def _tool_reports(messages: Sequence[Any]) -> list[Mapping[str, Any]]:
    reports: list[Mapping[str, Any]] = []
    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        content = message.content
        if not isinstance(content, str):
            continue
        try:
            decoded = json.loads(content)
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, Mapping):
            reports.append(decoded)
    return reports


def run_concentration_intelligence_replay(model_factory: Any) -> ReplayCaseResult:
    """Run the promoted service through normal Roberta/X1 Scout orchestration."""

    oracle_trace = ModelTrace(role="oracle")
    planner_trace = ModelTrace(role="x1_planner")
    cmis_trace = CMISTrace()
    oracle = ObservedModel(model_factory(), trace=oracle_trace)
    planner = ObservedModel(model_factory(), trace=planner_trace)
    cmis = ObservedIntelligenceFixtureCMISClient(
        IntelligenceReadinessFixtureCMISClient(scenario="test_only"),
        trace=cmis_trace,
    )
    tools = get_roberta_tools(cmis_client=cmis, x1_planner_model=planner)
    graph = build_graph(model=oracle, tools=tools)

    question = (
        "On X1, use the exact CMIS intelligence evidence id "
        f"{EVIDENCE_ID} for AGI. Explain what the concentration-change evidence "
        "supports, including evidence quality and important unknowns."
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
    reports = _tool_reports(messages)
    scout_report = next(
        (
            report
            for report in reports
            if report.get("specialist") == "x1_scout"
            and report.get("source", {}).get("operation") == SERVICE
        ),
        None,
    )
    findings = scout_report.get("findings", {}) if isinstance(scout_report, Mapping) else {}
    data = findings.get("data", {}) if isinstance(findings, Mapping) else {}
    evidence = data.get("evidence", {}) if isinstance(data, Mapping) else {}
    facts = data.get("facts", {}) if isinstance(data, Mapping) else {}
    services = {
        event.service
        for event in cmis_trace.events
        if event.chain == "x1"
    }
    normalized_answer = answer.lower()
    uncertainty_disclosed = any(
        cue in normalized_answer
        for cue in ("partial", "freshness", "unknown", "unresolved", "limited", "limitation")
    )
    scope_caveat_disclosed = any(
        cue in normalized_answer
        for cue in (
            "not unique holders",
            "token accounts",
            "does not prove ownership",
            "cannot infer ownership",
            "beneficial owner",
            "scope",
        )
    )
    checks = {
        "graph_completed": result.get("status") == "complete" and bool(answer),
        "service_coverage": SERVICE in services,
        "presentation_contract": decision_response_violation(question, answer) is None,
        "scout_report_preserved": scout_report is not None,
        "exact_fact_preserved": facts.get("delta_bps") == 400
        and facts.get("scope") == "observed_top_token_accounts",
        "risk_not_invented": findings.get("risk") is None
        and data.get("risk_interpretation") is None,
        "proof_risk_separation_preserved": data.get("proof_strength_separate_from_risk") is True,
        "partial_evidence_preserved": scout_report is not None
        and scout_report.get("cmis_status") == "partial"
        and evidence.get("freshness_verified") is None
        and "beneficial_owner_identity" in (evidence.get("unresolved_fields") or []),
        "behavioral_interpretation_not_added": data.get("behavioral_interpretation_added") is False,
        "execution_boundary": data.get("execution_authorized") is False,
        "answer_discloses_uncertainty": uncertainty_disclosed,
        "answer_discloses_scope_caveat": scope_caveat_disclosed,
    }
    return ReplayCaseResult(
        case_id="x1-concentration-change-intelligence-partial",
        profile="concentration_partial",
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
    "EVIDENCE_ID",
    "IntelligenceReadinessFixtureCMISClient",
    "ObservedIntelligenceFixtureCMISClient",
    "run_concentration_intelligence_replay",
]
