from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_critical_blocker_supplemental import (
    CRITICAL_BLOCKER_SUPPLEMENTAL_CONTRACT,
    CRITICAL_BLOCKER_SUPPLEMENTAL_VERSION,
)
from roberta.learning.pyramid_critical_retention import (
    CRITICAL_GROUNDED_PASS_NEXT_GATE,
    CRITICAL_RETENTION_ID_PREFIX,
    demote_grounded_canonical_authority,
    mb4e_immutability_critical_retention_bank,
    prepare_closed_book_critical_retention,
    validate_grounded_critical_prerequisite,
)
from roberta.learning.pyramid_exam import ANSWER_SYSTEM_PROMPT, GradedAnswer, answer_batch
from roberta.learning.pyramid_practice import PreparedTargetedPractice, evaluate_targeted_practice


CURRICULUM_ID = "critical-retention-fixture"


def _grade(exercise_id: str, grade: str) -> GradedAnswer:
    score = {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0}[grade]
    return GradedAnswer(
        exercise_id=exercise_id,
        answer=f"answer-{exercise_id}",
        grade=grade,
        score=score,
        correct=grade == "PASS",
        failure_codes=() if grade == "PASS" else ("factual_error",),
        critical_failure=False,
        grader_note="fixture",
    )


def _prepared(*, source_grounded_weak_items: int = 0) -> PreparedTargetedPractice:
    bank = mb4e_immutability_critical_retention_bank(CURRICULUM_ID, source_ref="fixture-source")[:10]
    return PreparedTargetedPractice(
        curriculum_id=CURRICULUM_ID,
        level=1,
        exercises=bank,
        weakness_critical_counts=(("benefits", "immutability", 5),),
        original_weak_ids=("q1", "q2", "q3", "q4", "q5"),
        source_grounded_weak_items=source_grounded_weak_items,
    )


def _perfect_report_mapping() -> dict[str, object]:
    prepared = _prepared(source_grounded_weak_items=5)
    report = evaluate_targeted_practice(
        prepared,
        [_grade(item.exercise_id, "PASS") for item in prepared.exercises],
    )
    return report.to_mapping()


def test_grounded_perfect_pass_is_demoted_before_canonical_authority() -> None:
    prepared = _prepared(source_grounded_weak_items=5)
    original = evaluate_targeted_practice(
        prepared,
        [_grade(item.exercise_id, "PASS") for item in prepared.exercises],
    )
    assert original.practice_passed is True
    assert original.canonical_attempt_authorized is True

    demoted = demote_grounded_canonical_authority(original)
    assert demoted.practice_passed is True
    assert demoted.next_gate == CRITICAL_GROUNDED_PASS_NEXT_GATE
    assert demoted.canonical_attempt_authorized is False


def test_retention_bank_is_fresh_third_namespace_and_has_twelve_questions() -> None:
    bank = mb4e_immutability_critical_retention_bank(CURRICULUM_ID, source_ref="fixture-source")
    assert len(bank) == 12
    assert len({item.exercise_id for item in bank}) == 12
    assert all(item.exercise_id.startswith(CRITICAL_RETENTION_ID_PREFIX) for item in bank)
    assert all((item.concept, item.subconcept) == ("benefits", "immutability") for item in bank)
    assert all(item.question_type == "closed_book_retention" for item in bank)


def test_closed_book_retention_requires_ten_of_ten() -> None:
    prepared = _prepared()
    nine_pass = [_grade(item.exercise_id, "PASS") for item in prepared.exercises]
    nine_pass[-1] = _grade(prepared.exercises[-1].exercise_id, "PARTIAL")
    failed = evaluate_targeted_practice(prepared, nine_pass)
    assert failed.accuracy == 0.95
    assert failed.critical_weaknesses_passed is False
    assert failed.practice_passed is False
    assert failed.canonical_attempt_authorized is False

    perfect = evaluate_targeted_practice(
        prepared,
        [_grade(item.exercise_id, "PASS") for item in prepared.exercises],
    )
    assert perfect.accuracy == 1.0
    assert perfect.critical_failures == 0
    assert perfect.critical_weaknesses_passed is True
    assert perfect.practice_passed is True
    assert perfect.canonical_attempt_authorized is True
    assert perfect.next_gate == "new_canonical_level_1_attempt"
    assert perfect.phase8_candidate_creation_authorized is False
    assert perfect.source_truth_authorized is False
    assert perfect.live_state_authorized is False
    assert perfect.memory_promotion_authorized is False
    assert perfect.retention_authorized is False
    assert perfect.governance_mutation_authorized is False
    assert perfect.execution_authorized is False


def test_grounded_prerequisite_accepts_legacy_premature_flag_but_does_not_trust_it(tmp_path: Path) -> None:
    report = _perfect_report_mapping()
    assert report["canonical_attempt_authorized"] is True
    gate = {
        "curriculum_id": CURRICULUM_ID,
        "level": 1,
        "run_id": "rp_fixture",
        "run_seed": "seed",
        "critical_ids": ["q1", "q2", "q3", "q4", "q5"],
    }
    manifest = {
        "contract": "roberta-pyramid-supplemental-practice/v1",
        "version": "1.0.0",
        "curriculum_id": CURRICULUM_ID,
        "level": 1,
        "canonical_bank_overlap": False,
        "canonical_exam": False,
        "ledger_mutation_authorized": False,
        "critical_blocker_contract": CRITICAL_BLOCKER_SUPPLEMENTAL_CONTRACT,
        "critical_blocker_version": CRITICAL_BLOCKER_SUPPLEMENTAL_VERSION,
        "critical_blocker_mode": True,
        "critical_blocker_gate": gate,
    }
    report_path = tmp_path / "practice_report.json"
    manifest_path = tmp_path / "critical_blocker_supplemental_manifest.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    prerequisite = validate_grounded_critical_prerequisite(
        grounded_report_path=report_path,
        grounded_manifest_path=manifest_path,
        curriculum_id=CURRICULUM_ID,
        gate_evidence=gate,
    )
    assert prerequisite["grounded_practice_passed"] is True
    assert prerequisite["legacy_premature_authorization_ignored"] is True
    assert prerequisite["canonical_attempt_authorized"] is False
    assert prerequisite["next_gate"] == CRITICAL_GROUNDED_PASS_NEXT_GATE


def test_prepare_retention_excludes_seen_sup3_ids(monkeypatch) -> None:
    bank = mb4e_immutability_critical_retention_bank(CURRICULUM_ID, source_ref="fixture-source")
    canonical = Exercise(
        exercise_id="canonical-q",
        curriculum_id=CURRICULUM_ID,
        level=1,
        concept="benefits",
        subconcept="immutability",
        question="canonical question",
        expected_answer="canonical answer",
        source_refs=("fixture-source",),
        required_reasoning_points=(),
        forbidden_inferences=(),
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
    )
    monkeypatch.setattr(
        "roberta.learning.pyramid_critical_retention.validate_package",
        lambda _: ({"curriculum_id": CURRICULUM_ID, "approved_source_refs": ["fixture-source"]}, (canonical,)),
    )
    monkeypatch.setattr(
        "roberta.learning.pyramid_critical_retention.load_seen_exercise_ids",
        lambda _: {bank[0].exercise_id, bank[1].exercise_id},
    )
    prepared, _ = prepare_closed_book_critical_retention(
        curriculum_dir="fixture",
        gate_evidence={
            "curriculum_id": CURRICULUM_ID,
            "level": 1,
            "critical_ids": ["q1", "q2", "q3", "q4", "q5"],
        },
        exclude_checkpoint_dirs=("seen",),
        questions_per_weakness=10,
        seed="fresh-ten",
        retention_bank=bank,
    )
    selected = {item.exercise_id for item in prepared.exercises}
    assert len(selected) == 10
    assert bank[0].exercise_id not in selected
    assert bank[1].exercise_id not in selected
    assert prepared.source_grounded_weak_items == 0


def test_closed_book_answer_payload_contains_no_remediation_context() -> None:
    exercise = mb4e_immutability_critical_retention_bank(CURRICULUM_ID, source_ref="fixture-source")[0]

    class CaptureModel:
        def __init__(self) -> None:
            self.messages = None

        def invoke(self, messages):
            self.messages = messages
            return SimpleNamespace(
                content=json.dumps(
                    {"answers": [{"exercise_id": exercise.exercise_id, "answer": "It is extremely difficult to alter, not absolutely impossible."}]}
                )
            )

    model = CaptureModel()
    answers = answer_batch(model, (exercise,))
    assert answers[exercise.exercise_id]
    assert model.messages is not None
    assert getattr(model.messages[0], "content") == ANSWER_SYSTEM_PROMPT
    assert "closed-book" in ANSWER_SYSTEM_PROMPT.lower()
    payload = json.loads(getattr(model.messages[-1], "content"))
    serialized = json.dumps(payload, sort_keys=True)
    assert "remediation_context" not in serialized
    assert "source_evidence" not in serialized
    assert "expected_answer" not in serialized
    assert "reference_reasoning_points" not in serialized
