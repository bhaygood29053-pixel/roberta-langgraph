"""Versioned factual projection for ROBERTA Evaluation Telemetry v2.

The v2 projection is deliberately read-only and bounded. It projects only
structured facts already present in the current-turn X1 Scout result returned by
the same ROBERTA graph invocation. It does not query CMIS/providers again,
derive claims from natural-language prose, or widen provider/Scout scope.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.messages import HumanMessage, ToolMessage


EVALUATION_TELEMETRY_V2 = "roberta_evaluation_telemetry/v2"
FACTUAL_EVIDENCE_CONTRACT = "roberta_evaluation_factual_evidence/v1"
PROJECTION_INTEGRITY_CONTRACT = "roberta_evaluation_projection_integrity/v1"
_X1_SCOUT_TOOL = "x1_scout_investigate"
_MAX_FACTUAL_CLAIMS = 32


def _clone_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _clone_json(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_clone_json(item) for item in value]
    return str(value)


def _current_turn_messages(messages: Sequence[object]) -> list[object]:
    last_human = -1
    for index, message in enumerate(messages):
        if isinstance(message, HumanMessage):
            last_human = index
    if last_human >= 0:
        return list(messages[last_human + 1 :])
    return list(messages)


def _current_turn_x1_scout_report(
    messages: Sequence[object],
) -> dict[str, Any] | None:
    for message in reversed(_current_turn_messages(messages)):
        if not isinstance(message, ToolMessage) or message.name != _X1_SCOUT_TOOL:
            continue
        content = message.content
        if not isinstance(content, str) or not content.strip():
            continue
        try:
            report = json.loads(content)
        except json.JSONDecodeError:
            continue
        if not isinstance(report, Mapping):
            continue
        if report.get("specialist") != "x1_scout" or report.get("chain") != "x1":
            continue
        source = report.get("source")
        if not isinstance(source, Mapping):
            continue
        if source.get("service") != "cmis":
            continue
        operation = source.get("operation")
        if not isinstance(operation, str) or not operation.strip():
            continue
        return dict(report)
    return None


def _factual_evidence(report: Mapping[str, Any]) -> dict[str, Any]:
    source = report.get("source")
    findings = report.get("findings")
    evidence: dict[str, Any] = {
        "contract_version": FACTUAL_EVIDENCE_CONTRACT,
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": report.get("requested_asset"),
        "asset": _clone_json(report.get("asset") if isinstance(report.get("asset"), Mapping) else {}),
        "source": {
            "service": "cmis",
            "operation": source.get("operation") if isinstance(source, Mapping) else None,
        },
        "cmis_status": report.get("cmis_status"),
        "observed_at_iso": report.get("observed_at_iso"),
        "findings": _clone_json(findings if isinstance(findings, Mapping) else {}),
        "confidence": _clone_json(
            report.get("confidence") if isinstance(report.get("confidence"), Mapping) else {}
        ),
        "evidence_context": _clone_json(
            report.get("evidence_context")
            if isinstance(report.get("evidence_context"), Mapping)
            else {}
        ),
    }
    freshness = report.get("freshness")
    if isinstance(freshness, Mapping):
        evidence["freshness"] = _clone_json(freshness)
    return evidence


def _scalar_claims(
    value: Any,
    *,
    path: str,
    name_prefix: str,
    output: list[dict[str, Any]],
) -> None:
    if len(output) >= _MAX_FACTUAL_CLAIMS:
        return
    if isinstance(value, Mapping):
        for raw_key in sorted(value, key=lambda item: str(item)):
            key = str(raw_key)
            if not key or "." in key:
                continue
            _scalar_claims(
                value[raw_key],
                path=f"{path}.{key}",
                name_prefix=f"{name_prefix}_{key}",
                output=output,
            )
            if len(output) >= _MAX_FACTUAL_CLAIMS:
                return
        return
    if value is None or isinstance(value, (list, tuple, dict)):
        return
    if isinstance(value, (str, int, float, bool)):
        output.append(
            {
                "name": name_prefix,
                "evidence_path": path,
                "value": value,
            }
        )


def _factual_claims(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    claims: list[dict[str, Any]] = []
    findings = evidence.get("findings")
    if not isinstance(findings, Mapping):
        return claims
    for branch in ("data", "risk"):
        value = findings.get(branch)
        if not isinstance(value, Mapping):
            continue
        _scalar_claims(
            value,
            path=f"factual_response.findings.{branch}",
            name_prefix=f"factual_{branch}",
            output=claims,
        )
    return claims


def _factual_freshness(evidence: Mapping[str, Any]) -> dict[str, Any]:
    freshness = evidence.get("freshness")
    if isinstance(freshness, Mapping):
        explicit_state = None
        for key in ("state", "freshness_state", "status"):
            value = freshness.get(key)
            if isinstance(value, str) and value.strip():
                explicit_state = value
                break
        return {
            "state": explicit_state or "UNAVAILABLE",
            "source_ref": "factual_response.freshness",
            "source_value": _clone_json(freshness),
        }

    context = evidence.get("evidence_context")
    if isinstance(context, Mapping) and isinstance(
        context.get("freshness_verified"), bool
    ):
        verified = context["freshness_verified"]
        return {
            "state": "VERIFIED" if verified else "NOT_VERIFIED",
            "source_ref": "factual_response.evidence_context.freshness_verified",
            "source_value": verified,
        }

    return {
        "state": "UNAVAILABLE",
        "source_ref": None,
        "source_value": None,
    }


def extend_evaluation_telemetry_v2(
    base_telemetry: Mapping[str, Any],
    messages: Sequence[object],
) -> dict[str, Any]:
    """Extend accepted v1 final-message telemetry with bounded factual evidence."""

    payload = _clone_json(dict(base_telemetry))
    payload["evaluation_telemetry_version"] = EVALUATION_TELEMETRY_V2

    report = _current_turn_x1_scout_report(messages)
    if report is None:
        return payload

    factual = _factual_evidence(report)
    claims = _factual_claims(factual)
    evidence = payload.get("evaluation_evidence")
    if not isinstance(evidence, dict):
        evidence = {}
        payload["evaluation_evidence"] = evidence
    evidence["factual_response"] = factual

    existing_claims = payload.get("claims")
    merged_claims = list(existing_claims) if isinstance(existing_claims, list) else []
    existing_paths = {
        item.get("evidence_path")
        for item in merged_claims
        if isinstance(item, Mapping)
    }
    for claim in claims:
        if claim["evidence_path"] not in existing_paths:
            merged_claims.append(claim)
            existing_paths.add(claim["evidence_path"])
    payload["claims"] = merged_claims

    if claims:
        evidence["evaluation_projection_integrity"] = {
            "contract_version": PROJECTION_INTEGRITY_CONTRACT,
            "status": "PASS",
            "claim_count": len(claims),
            "source_scope": "current_turn_x1_scout_cmis_projection",
            "facts_authority": "chain_scout_cmis",
            "judgment_authority": "roberta",
            "provider_truth_certified": False,
            "all_natural_language_claims_certified": False,
            "execution_authorized": False,
        }

    provenance = payload.get("evidence_provenance")
    if not isinstance(provenance, dict):
        provenance = {}
        payload["evidence_provenance"] = provenance
    provenance["factual_projection"] = {
        "facts_authority": "chain_scout_cmis",
        "source_service": "cmis",
        "source_operation": factual["source"]["operation"],
        "telemetry_scope": "current_turn_x1_scout_structured_evidence_only",
        "second_cmis_query_performed": False,
        "prose_claim_inference_performed": False,
    }

    current_freshness = payload.get("evidence_freshness")
    if (
        not isinstance(current_freshness, Mapping)
        or current_freshness.get("state") in {None, "UNAVAILABLE"}
    ):
        payload["evidence_freshness"] = _factual_freshness(factual)

    # The projection never grants execution authority. If an accepted final
    # structure already exposed a violation, preserve it rather than masking it.
    if payload.get("execution_authorized") is not True:
        payload["execution_authorized"] = False

    return payload


__all__ = [
    "EVALUATION_TELEMETRY_V2",
    "FACTUAL_EVIDENCE_CONTRACT",
    "PROJECTION_INTEGRITY_CONTRACT",
    "extend_evaluation_telemetry_v2",
]
