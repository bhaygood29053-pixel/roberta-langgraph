"""Aggregate ROBERTA public-beta product proof records without reading content.

The summary layer accepts only validated ``roberta_beta_product_proof/v1``
records. It intentionally emits no response ids, prompts, replies, wallet/token
identifiers, raw evidence, or cross-session identity.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from roberta.beta_product_proof import (
    AUTO_OUTCOME_TYPE,
    USER_FEEDBACK_TYPE,
    validate_beta_record,
)

BETA_COHORT_SUMMARY_VERSION = "roberta_beta_cohort_summary/v1"

_IMPACT_WEIGHTS = {
    "unavailable": 5,
    "not_helpful": 4,
    "missing_evidence": 3,
    "confusing": 2,
    "too_technical": 2,
    "evidence_required": 1,
}


class BetaCohortSummaryError(ValueError):
    """Raised when cohort records cannot be summarized without ambiguity."""


def load_beta_jsonl(path: str | Path) -> list[dict[str, object]]:
    source = Path(path)
    records: list[dict[str, object]] = []
    with source.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            text = raw.strip()
            if not text:
                continue
            try:
                value = json.loads(text)
            except json.JSONDecodeError as exc:
                raise BetaCohortSummaryError(
                    f"invalid JSON on beta line {line_number}"
                ) from exc
            if not isinstance(value, Mapping):
                raise BetaCohortSummaryError(
                    f"beta line {line_number} must be a JSON object"
                )
            try:
                records.append(validate_beta_record(value))
            except ValueError as exc:
                raise BetaCohortSummaryError(
                    f"invalid beta record on line {line_number}: {exc}"
                ) from exc
    return records


def _rate(numerator: int, denominator: int) -> dict[str, int | float | None]:
    return {
        "numerator": int(numerator),
        "denominator": int(denominator),
        "rate": None if denominator == 0 else round(numerator / denominator, 4),
    }


def _target(rate: float | None, *, minimum: float | None = None, maximum: float | None = None) -> bool | None:
    if rate is None:
        return None
    if minimum is not None:
        return rate >= minimum
    if maximum is not None:
        return rate <= maximum
    raise AssertionError("minimum or maximum target is required")


def _signal_rankings(
    automatic: Iterable[Mapping[str, Any]],
    feedback_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, object]]:
    counts: Counter[tuple[str, str]] = Counter()

    for record in automatic:
        workflow = str(record.get("workflow") or "unknown")
        outcome = str(record.get("outcome") or "")
        if outcome in {"unavailable", "evidence_required"}:
            counts[(workflow, outcome)] += 1

        response_id = str(record.get("response_id") or "")
        feedback = feedback_by_id.get(response_id)
        if feedback is None:
            continue
        if feedback.get("helpful") is False:
            counts[(workflow, "not_helpful")] += 1
        clarity = str(feedback.get("clarity") or "")
        if clarity in {"missing_evidence", "confusing", "too_technical"}:
            counts[(workflow, clarity)] += 1

    rows = [
        {
            "workflow": workflow,
            "signal": signal,
            "count": count,
            "impact_weight": _IMPACT_WEIGHTS[signal],
            "priority_score": count * _IMPACT_WEIGHTS[signal],
        }
        for (workflow, signal), count in counts.items()
    ]
    rows.sort(
        key=lambda item: (
            -int(item["priority_score"]),
            -int(item["count"]),
            str(item["workflow"]),
            str(item["signal"]),
        )
    )
    return rows


def summarize_beta_records(records: Iterable[Mapping[str, Any]]) -> dict[str, object]:
    automatic: list[dict[str, object]] = []
    feedback_by_id: dict[str, dict[str, object]] = {}
    automatic_ids: set[str] = set()
    duplicate_feedback_count = 0

    for raw in records:
        record = validate_beta_record(raw)
        response_id = str(record["response_id"])
        if record["record_type"] == AUTO_OUTCOME_TYPE:
            if response_id in automatic_ids:
                raise BetaCohortSummaryError(
                    "duplicate automatic response_id would inflate cohort size"
                )
            automatic_ids.add(response_id)
            automatic.append(record)
            continue

        if record["record_type"] == USER_FEEDBACK_TYPE:
            if response_id in feedback_by_id:
                duplicate_feedback_count += 1
                continue
            feedback_by_id[response_id] = record

    matched_feedback = {
        response_id: feedback
        for response_id, feedback in feedback_by_id.items()
        if response_id in automatic_ids
    }
    orphan_feedback_count = len(feedback_by_id) - len(matched_feedback)

    outcomes: Counter[str] = Counter()
    evidence_quality: Counter[str] = Counter()
    duration_buckets: Counter[str] = Counter()
    workflow_rows: dict[str, Counter[str]] = defaultdict(Counter)
    evidence_required_without_unknown = 0

    for record in automatic:
        workflow = str(record.get("workflow") or "unknown")
        outcome = str(record.get("outcome") or "unknown")
        quality = str(record.get("evidence_quality") or "UNKNOWN")
        duration = str(record.get("duration_bucket") or "unknown")
        outcomes[outcome] += 1
        evidence_quality[quality] += 1
        duration_buckets[duration] += 1
        workflow_rows[workflow]["responses"] += 1
        workflow_rows[workflow][f"outcome:{outcome}"] += 1
        if outcome == "evidence_required" and int(record.get("explicit_unknown_count") or 0) <= 0:
            evidence_required_without_unknown += 1

    helpful = 0
    clarity: Counter[str] = Counter()
    drill_down = 0
    would_use_again_yes = 0
    would_use_again_answered = 0
    willingness_to_pay: Counter[str] = Counter()
    interest_surface: Counter[str] = Counter()

    for response_id, feedback in matched_feedback.items():
        if feedback.get("helpful") is True:
            helpful += 1
        clarity[str(feedback.get("clarity") or "unknown")] += 1
        if feedback.get("evidence_drill_down") is True:
            drill_down += 1
        use_again = feedback.get("would_use_again")
        if isinstance(use_again, bool):
            would_use_again_answered += 1
            if use_again:
                would_use_again_yes += 1
        wtp = feedback.get("willingness_to_pay")
        if wtp is not None:
            willingness_to_pay[str(wtp)] += 1
        interest = feedback.get("interest_surface")
        if interest is not None:
            interest_surface[str(interest)] += 1

        workflow = next(
            (
                str(record.get("workflow") or "unknown")
                for record in automatic
                if str(record.get("response_id")) == response_id
            ),
            "unknown",
        )
        workflow_rows[workflow]["feedback"] += 1
        if feedback.get("helpful") is True:
            workflow_rows[workflow]["helpful"] += 1
        clarity_value = str(feedback.get("clarity") or "unknown")
        workflow_rows[workflow][f"clarity:{clarity_value}"] += 1

    feedback_count = len(matched_feedback)
    technical_or_confusing = clarity["too_technical"] + clarity["confusing"]

    helpful_rate = _rate(helpful, feedback_count)
    technical_rate = _rate(technical_or_confusing, feedback_count)
    unavailable_rate = _rate(outcomes["unavailable"], len(automatic))
    use_again_rate = _rate(would_use_again_yes, would_use_again_answered)
    drill_down_rate = _rate(drill_down, feedback_count)

    by_workflow: dict[str, object] = {}
    for workflow in sorted(workflow_rows):
        row = workflow_rows[workflow]
        response_count = row["responses"]
        workflow_feedback = row["feedback"]
        by_workflow[workflow] = {
            "responses": response_count,
            "outcomes": {
                "success": row["outcome:success"],
                "evidence_required": row["outcome:evidence_required"],
                "unavailable": row["outcome:unavailable"],
            },
            "feedback_count": workflow_feedback,
            "helpful_rate": _rate(row["helpful"], workflow_feedback),
            "clarity": {
                "clear": row["clarity:clear"],
                "too_technical": row["clarity:too_technical"],
                "confusing": row["clarity:confusing"],
                "missing_evidence": row["clarity:missing_evidence"],
            },
        }

    return {
        "contract_version": BETA_COHORT_SUMMARY_VERSION,
        "cohort_size": len(automatic),
        "feedback_count": feedback_count,
        "feedback_coverage": _rate(feedback_count, len(automatic)),
        "orphan_feedback_count": orphan_feedback_count,
        "duplicate_feedback_ignored": duplicate_feedback_count,
        "outcomes": dict(sorted(outcomes.items())),
        "evidence_quality": dict(sorted(evidence_quality.items())),
        "duration_buckets": dict(sorted(duration_buckets.items())),
        "clarity": dict(sorted(clarity.items())),
        "rates": {
            "helpful": helpful_rate,
            "too_technical_or_confusing": technical_rate,
            "unavailable": unavailable_rate,
            "would_use_again": use_again_rate,
            "evidence_drill_down": drill_down_rate,
        },
        "willingness_to_pay": dict(sorted(willingness_to_pay.items())),
        "interest_surface": dict(sorted(interest_surface.items())),
        "evidence_required_without_explicit_unknown_count": evidence_required_without_unknown,
        "targets": {
            "helpful_gte_70pct": _target(helpful_rate["rate"], minimum=0.70),
            "too_technical_or_confusing_lte_20pct": _target(
                technical_rate["rate"], maximum=0.20
            ),
            "supported_workflow_unavailable_lte_10pct": _target(
                unavailable_rate["rate"], maximum=0.10
            ),
            "would_use_again_gte_60pct": _target(
                use_again_rate["rate"], minimum=0.60
            ),
            "evidence_required_names_unknowns": evidence_required_without_unknown == 0,
        },
        "by_workflow": by_workflow,
        "ranked_product_signals": _signal_rankings(automatic, matched_feedback),
        "privacy": {
            "contains_response_ids": False,
            "contains_prompt_or_response_text": False,
            "contains_cross_session_identity": False,
        },
        "execution_authorized": False,
    }


def summarize_beta_jsonl(path: str | Path) -> dict[str, object]:
    return summarize_beta_records(load_beta_jsonl(path))


__all__ = [
    "BETA_COHORT_SUMMARY_VERSION",
    "BetaCohortSummaryError",
    "load_beta_jsonl",
    "summarize_beta_jsonl",
    "summarize_beta_records",
]
