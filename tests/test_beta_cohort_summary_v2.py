from __future__ import annotations

import json

import pytest

from roberta.beta_cohort_summary_v2 import (
    BETA_COHORT_MANIFEST_VERSION,
    BETA_COHORT_SUMMARY_V2_VERSION,
    BetaCohortManifestError,
    summarize_beta_records_v2,
    validate_beta_cohort_manifest,
)
from roberta.beta_product_proof import build_automatic_outcome, build_user_feedback


def _telemetry(*, workflow: str, unknowns: int = 0):
    return {
        "evaluation_evidence": {
            "human_response_decision": {
                "workflow": workflow,
                "response_depth": "normal",
                "evidence_quality": "LOW" if unknowns else "MEDIUM",
                "important_unknowns": [f"gap_{index}" for index in range(unknowns)],
                "execution_authorized": False,
            }
        },
        "claims": [],
        "evidence_provenance": {"source_contracts": ["bounded_contract/v1"]},
        "execution_authorized": False,
    }


def _manifest(indices: list[int]):
    scores = ["PASS", "FAIL", "PARTIAL", "PARTIAL", "FAIL", "PASS", "PARTIAL"]
    return {
        "contract_version": BETA_COHORT_MANIFEST_VERSION,
        "participant_count": 1,
        "scenarios": [
            {
                "scenario_id": f"C{number:02d}",
                "automatic_event_index": event_index,
                "manual_score": score,
            }
            for number, (event_index, score) in enumerate(zip(indices, scores), start=1)
        ],
    }


def test_v2_separates_participant_scenarios_from_raw_response_events():
    records = []
    response_ids = []
    for index in range(1, 14):
        response_id = f"{index:032x}"
        response_ids.append(response_id)
        records.append(
            build_automatic_outcome(
                _telemetry(
                    workflow="setup_retry" if index % 2 == 0 else "scored_workflow",
                    unknowns=1 if index in {1, 4, 5, 8, 11, 12} else 0,
                ),
                duration_ms=2_500,
                response_id=response_id,
            )
        )

    # Feedback for one selected response and one excluded setup/retry response.
    records.append(
        build_user_feedback(
            response_id=response_ids[0],
            helpful=True,
            clarity="clear",
            would_use_again=True,
        )
    )
    records.append(
        build_user_feedback(
            response_id=response_ids[1],
            helpful=False,
            clarity="confusing",
            would_use_again=False,
        )
    )

    selected = [1, 3, 5, 7, 9, 11, 13]
    summary = summarize_beta_records_v2(records, _manifest(selected))

    assert summary["contract_version"] == BETA_COHORT_SUMMARY_V2_VERSION
    assert summary["cohort_size"] == 1
    assert summary["participant_count"] == 1
    assert summary["response_event_count"] == 13
    assert summary["included_response_event_count"] == 7
    assert summary["excluded_response_event_count"] == 6
    assert summary["scenario_count"] == 7
    assert summary["feedback_count"] == 1
    assert summary["raw_feedback_event_count"] == 2
    assert summary["manual_score_counts"] == {"FAIL": 2, "PARTIAL": 3, "PASS": 2}
    assert summary["selection"] == {
        "manifest_contract_version": BETA_COHORT_MANIFEST_VERSION,
        "selection_basis": "automatic_event_index",
        "setup_or_retry_events_excluded": 6,
        "cohort_metrics_valid": True,
    }

    # Automatic evidence state remains separate from moderator rubric score.
    assert summary["by_scenario"]["C01"]["manual_score"] == "PASS"
    assert summary["by_scenario"]["C01"]["automatic_outcome"] == "evidence_required"
    assert summary["by_scenario"]["C06"]["manual_score"] == "PASS"

    # Excluded setup/retry feedback and events do not influence included metrics.
    assert "setup_retry" not in summary["by_workflow"]
    assert summary["rates"]["helpful"]["rate"] == 1.0
    assert all(row["workflow"] != "setup_retry" for row in summary["ranked_product_signals"])

    encoded = json.dumps(summary, sort_keys=True)
    for response_id in response_ids:
        assert response_id not in encoded
    assert summary["privacy"] == {
        "contains_response_ids": False,
        "contains_prompt_or_response_text": False,
        "contains_cross_session_identity": False,
        "contains_participant_identity": False,
        "contains_event_indices": False,
    }
    assert summary["execution_authorized"] is False


def test_manifest_rejects_persistent_identity_or_schema_expansion():
    manifest = _manifest([1, 2, 3, 4, 5, 6, 7])
    manifest["participant_id"] = "do-not-store"

    with pytest.raises(BetaCohortManifestError, match="schema drift"):
        validate_beta_cohort_manifest(manifest)


def test_manifest_rejects_duplicate_or_out_of_range_event_selection():
    duplicate = _manifest([1, 2, 3, 4, 5, 6, 6])
    with pytest.raises(BetaCohortManifestError, match="duplicate automatic_event_index"):
        validate_beta_cohort_manifest(duplicate)

    records = [
        build_automatic_outcome(
            _telemetry(workflow="only_event"),
            duration_ms=1_000,
            response_id="a" * 32,
        )
    ]
    with pytest.raises(BetaCohortManifestError, match="exceeds response-event count"):
        summarize_beta_records_v2(records, _manifest([1, 2, 3, 4, 5, 6, 7]))
