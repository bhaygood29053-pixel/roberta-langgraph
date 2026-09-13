"""Scenario-aware, privacy-safe ROBERTA public-beta cohort aggregation.

This v2 layer keeps raw response-event telemetry separate from moderator-declared
participant/scenario accounting. A local moderator manifest selects automatic
response events by their 1-based ordinal position among automatic records and
attaches only a bounded scenario id plus PASS/PARTIAL/FAIL score.

The manifest contains no prompt/reply text, wallet/token identifiers, transaction
hashes, persistent participant identity, or cross-session tracking id. Response
ids are used only transiently in memory to join already-accepted feedback and
are never emitted by the summary.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

from roberta.beta_cohort_summary import (
    BetaCohortSummaryError,
    load_beta_jsonl,
    summarize_beta_records,
)
from roberta.beta_product_proof import (
    AUTO_OUTCOME_TYPE,
    USER_FEEDBACK_TYPE,
    validate_beta_record,
)

BETA_COHORT_MANIFEST_VERSION = "roberta_beta_cohort_manifest/v1"
BETA_COHORT_SUMMARY_V2_VERSION = "roberta_beta_cohort_summary/v2"

_SCENARIO_ID_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,32}$")
_MANUAL_SCORES = {"PASS", "PARTIAL", "FAIL"}


class BetaCohortManifestError(BetaCohortSummaryError):
    """Raised when a moderator cohort manifest is invalid or ambiguous."""


def load_beta_cohort_manifest(path: str | Path) -> dict[str, object]:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise BetaCohortManifestError("invalid cohort manifest JSON") from exc

    if not isinstance(value, Mapping):
        raise BetaCohortManifestError("cohort manifest must be a JSON object")
    return validate_beta_cohort_manifest(value)


def validate_beta_cohort_manifest(value: Mapping[str, Any]) -> dict[str, object]:
    expected_top = {"contract_version", "participant_count", "scenarios"}
    if set(value) != expected_top:
        raise BetaCohortManifestError("cohort manifest schema drift")
    if value.get("contract_version") != BETA_COHORT_MANIFEST_VERSION:
        raise BetaCohortManifestError("unsupported cohort manifest contract")

    participant_count = value.get("participant_count")
    if isinstance(participant_count, bool) or not isinstance(participant_count, int):
        raise BetaCohortManifestError("participant_count must be an integer")
    if participant_count < 1:
        raise BetaCohortManifestError("participant_count must be at least 1")

    raw_scenarios = value.get("scenarios")
    if not isinstance(raw_scenarios, list) or not raw_scenarios:
        raise BetaCohortManifestError("scenarios must be a non-empty list")
    if len(raw_scenarios) > 128:
        raise BetaCohortManifestError("scenarios exceeds bounded limit")

    scenarios: list[dict[str, object]] = []
    scenario_ids: set[str] = set()
    event_indices: set[int] = set()

    for raw in raw_scenarios:
        if not isinstance(raw, Mapping):
            raise BetaCohortManifestError("each scenario must be an object")
        expected = {"scenario_id", "automatic_event_index", "manual_score"}
        if set(raw) != expected:
            raise BetaCohortManifestError("scenario manifest schema drift")

        scenario_id = str(raw.get("scenario_id") or "").strip()
        if not _SCENARIO_ID_RE.fullmatch(scenario_id):
            raise BetaCohortManifestError("invalid scenario_id")
        if scenario_id in scenario_ids:
            raise BetaCohortManifestError("duplicate scenario_id")
        scenario_ids.add(scenario_id)

        event_index = raw.get("automatic_event_index")
        if isinstance(event_index, bool) or not isinstance(event_index, int):
            raise BetaCohortManifestError("automatic_event_index must be an integer")
        if event_index < 1:
            raise BetaCohortManifestError("automatic_event_index must be at least 1")
        if event_index in event_indices:
            raise BetaCohortManifestError("duplicate automatic_event_index")
        event_indices.add(event_index)

        manual_score = str(raw.get("manual_score") or "").strip().upper()
        if manual_score not in _MANUAL_SCORES:
            raise BetaCohortManifestError("manual_score must be PASS, PARTIAL, or FAIL")

        scenarios.append(
            {
                "scenario_id": scenario_id,
                "automatic_event_index": event_index,
                "manual_score": manual_score,
            }
        )

    return {
        "contract_version": BETA_COHORT_MANIFEST_VERSION,
        "participant_count": participant_count,
        "scenarios": scenarios,
    }


def summarize_beta_records_v2(
    records: Iterable[Mapping[str, Any]],
    manifest: Mapping[str, Any],
) -> dict[str, object]:
    validated_manifest = validate_beta_cohort_manifest(manifest)
    validated_records = [validate_beta_record(record) for record in records]

    automatic = [
        record
        for record in validated_records
        if record["record_type"] == AUTO_OUTCOME_TYPE
    ]
    raw_feedback = [
        record
        for record in validated_records
        if record["record_type"] == USER_FEEDBACK_TYPE
    ]

    selected_automatic: list[dict[str, object]] = []
    scenario_rows: list[dict[str, object]] = []
    selected_ids: set[str] = set()

    for scenario in validated_manifest["scenarios"]:
        if not isinstance(scenario, Mapping):
            raise BetaCohortManifestError("validated scenario is invalid")
        event_index = int(scenario["automatic_event_index"])
        if event_index > len(automatic):
            raise BetaCohortManifestError(
                f"automatic_event_index {event_index} exceeds response-event count {len(automatic)}"
            )
        record = automatic[event_index - 1]
        selected_automatic.append(record)
        selected_ids.add(str(record["response_id"]))
        scenario_rows.append(
            {
                "scenario_id": str(scenario["scenario_id"]),
                "manual_score": str(scenario["manual_score"]),
                "workflow": str(record.get("workflow") or "unknown"),
                "automatic_outcome": str(record.get("outcome") or "unknown"),
                "evidence_quality": str(record.get("evidence_quality") or "UNKNOWN"),
                "explicit_unknown_count": int(record.get("explicit_unknown_count") or 0),
            }
        )

    selected_feedback = [
        record
        for record in raw_feedback
        if str(record.get("response_id") or "") in selected_ids
    ]
    selected_records = [*selected_automatic, *selected_feedback]

    summary = summarize_beta_records(selected_records)
    summary["contract_version"] = BETA_COHORT_SUMMARY_V2_VERSION
    summary["cohort_size"] = int(validated_manifest["participant_count"])
    summary["participant_count"] = int(validated_manifest["participant_count"])
    summary["response_event_count"] = len(automatic)
    summary["included_response_event_count"] = len(selected_automatic)
    summary["excluded_response_event_count"] = len(automatic) - len(selected_automatic)
    summary["raw_feedback_event_count"] = len(raw_feedback)
    summary["scenario_count"] = len(scenario_rows)
    summary["manual_score_counts"] = dict(
        sorted(Counter(row["manual_score"] for row in scenario_rows).items())
    )
    summary["by_scenario"] = {
        row["scenario_id"]: {
            "manual_score": row["manual_score"],
            "workflow": row["workflow"],
            "automatic_outcome": row["automatic_outcome"],
            "evidence_quality": row["evidence_quality"],
            "explicit_unknown_count": row["explicit_unknown_count"],
        }
        for row in scenario_rows
    }
    summary["selection"] = {
        "manifest_contract_version": BETA_COHORT_MANIFEST_VERSION,
        "selection_basis": "automatic_event_index",
        "setup_or_retry_events_excluded": len(automatic) - len(selected_automatic),
        "cohort_metrics_valid": True,
    }
    summary["measurement_semantics"] = {
        "cohort_size": "declared_participant_count",
        "response_event_count": "all_automatic_response_events_in_jsonl",
        "scenario_count": "moderator_selected_scored_scenarios",
        "automatic_outcomes": "evidence_state_not_manual_pass_partial_fail",
        "manual_scores": "moderator_rubric_signal_separate_from_automatic_outcome",
    }
    summary["privacy"] = {
        "contains_response_ids": False,
        "contains_prompt_or_response_text": False,
        "contains_cross_session_identity": False,
        "contains_participant_identity": False,
        "contains_event_indices": False,
    }
    summary["execution_authorized"] = False
    return summary


def summarize_beta_jsonl_v2(
    path: str | Path,
    manifest_path: str | Path,
) -> dict[str, object]:
    return summarize_beta_records_v2(
        load_beta_jsonl(path),
        load_beta_cohort_manifest(manifest_path),
    )


__all__ = [
    "BETA_COHORT_MANIFEST_VERSION",
    "BETA_COHORT_SUMMARY_V2_VERSION",
    "BetaCohortManifestError",
    "load_beta_cohort_manifest",
    "summarize_beta_jsonl_v2",
    "summarize_beta_records_v2",
    "validate_beta_cohort_manifest",
]
