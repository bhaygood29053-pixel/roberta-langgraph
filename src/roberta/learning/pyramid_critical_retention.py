from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
from typing import Mapping, Sequence

from .curriculum_io import validate_package
from .pyramid import Exercise
from .pyramid_critical_blocker_supplemental import (
    CRITICAL_BLOCKER_SUPPLEMENTAL_CONTRACT,
    CRITICAL_BLOCKER_SUPPLEMENTAL_VERSION,
    MB4E_SOURCE_REF,
)
from .pyramid_practice import (
    TARGETED_PRACTICE_CONTRACT,
    TARGETED_PRACTICE_VERSION,
    PreparedTargetedPractice,
    TargetedPracticeReport,
    TargetedPyramidPracticeError,
)
from .pyramid_remediation import load_seen_exercise_ids


CRITICAL_RETENTION_CONTRACT = "roberta-pyramid-critical-retention/v1"
CRITICAL_RETENTION_VERSION = "1.0.0"
CRITICAL_RETENTION_ID_PREFIX = "MB4E-SUP3-L01-"
CRITICAL_RETENTION_CHECKPOINT_NAMESPACE = "checkpoints_closed_book_v1"
CRITICAL_GROUNDED_PASS_NEXT_GATE = "closed_book_critical_retention"


def _canonical_hash(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def demote_grounded_canonical_authority(report: TargetedPracticeReport) -> TargetedPracticeReport:
    """Grounded success is a prerequisite for retention, never canonical authority."""

    if not report.practice_passed:
        return report
    return replace(
        report,
        next_gate=CRITICAL_GROUNDED_PASS_NEXT_GATE,
        canonical_attempt_authorized=False,
    )


def mb4e_immutability_critical_retention_bank(
    curriculum_id: str,
    *,
    source_ref: str = MB4E_SOURCE_REF,
) -> tuple[Exercise, ...]:
    """Fresh noncanonical closed-book retention bank for practical immutability."""

    rows: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...]], ...] = (
        (
            "A security review calls a blockchain record 'unchangeable.' Give the precise Level-1 meaning without making an absolute claim.",
            "The record is practically immutable: accepted history is extremely difficult to alter, but alteration is not conceptually impossible under every condition.",
            ("State strong practical resistance to alteration.", "Reject absolute impossibility."),
            ("Accepted history is literally impossible to alter under any condition.",),
        ),
        (
            "Is 'immutable' equivalent to 'mathematically impossible to modify forever'? Answer and explain the distinction.",
            "No. Immutability here means accepted history is extremely difficult or nearly impossible to change in practice, not mathematically impossible to modify forever.",
            ("Distinguish practical immutability from absolute impossibility.",),
            ("Immutable means mathematically impossible to modify forever.",),
        ),
        (
            "A report says, 'The chain is trustworthy because old blocks can never change.' Correct the statement while preserving its useful point.",
            "The useful point is that old accepted history is extremely difficult to change, which gives practical stability; saying it can never change is too absolute.",
            ("Preserve practical stability.", "Remove the absolute claim."),
            ("Old blocks can never change.",),
        ),
        (
            "What does practical immutability contribute to record integrity even though it is not an absolute guarantee?",
            "It makes accepted history extremely difficult to alter, providing strong practical stability and tamper resistance without claiming alteration is impossible in every conceivable case.",
            ("Connect practical difficulty to integrity.", "Keep the non-absolute qualification."),
            ("Record integrity requires absolute impossibility of change.",),
        ),
        (
            "Choose the better statement and justify it: A) accepted data cannot ever be rewritten; B) rewriting accepted data is made extraordinarily difficult in practice.",
            "B is better because it captures practical immutability without turning strong resistance to rewriting into an absolute claim of impossibility.",
            ("Choose the practical formulation.", "Explain why the absolute formulation is too strong."),
            ("A is the exact meaning of immutability.",),
        ),
        (
            "If a blockchain makes historical alteration economically or operationally infeasible in normal conditions, what can you conclude about immutability?",
            "You can conclude that it has strong practical immutability or tamper resistance, not that historical alteration is conceptually impossible under all conditions.",
            ("Infer practical immutability only.",),
            ("Operational infeasibility proves absolute impossibility.",),
        ),
        (
            "Why is 'effectively permanent' safer wording than 'absolutely permanent' when explaining blockchain history?",
            "'Effectively permanent' conveys that accepted history is extremely difficult to alter in practice, while 'absolutely permanent' incorrectly implies alteration is impossible without exception.",
            ("Contrast effective permanence with absolute permanence."),
            ("Absolutely permanent is required by the definition.",),
        ),
        (
            "State the immutability caveat Roberta should remember when answering a new question that never mentions attacks, consensus, or forks.",
            "She should still avoid absolute wording: accepted blockchain history is extremely difficult to change in practice, not conceptually impossible to change.",
            ("Carry the non-absolute qualifier into a new context."),
            ("If no exception is mentioned, it is safe to say change is impossible.",),
        ),
        (
            "Does strong tamper resistance justify the sentence 'deletion of accepted blockchain data is impossible'? Why or why not?",
            "No. Strong tamper resistance supports saying deletion or alteration is extremely difficult in practice; 'impossible' is an unjustified absolute claim.",
            ("Reject the absolute sentence.", "State the practical alternative."),
            ("Deletion is impossible.",),
        ),
        (
            "Explain immutability to a beginner in one sentence without using the words 'never' or 'impossible.'",
            "Blockchain immutability means accepted history is designed to be extremely difficult to alter, giving the ledger strong practical stability.",
            ("Describe strong practical resistance without absolute language."),
            ("Accepted history cannot be changed.",),
        ),
        (
            "A multiple-choice explanation says immutability is valuable because prior records are 'beyond any possible modification.' What conceptual error should be flagged?",
            "It confuses practical immutability with absolute immutability; the supported concept is extreme difficulty of alteration, not impossibility under every possible condition.",
            ("Identify the absolute-overstatement error."),
            ("Beyond any possible modification is accurate.",),
        ),
        (
            "What is the strongest accurate claim you can make about changing accepted blockchain history at this level?",
            "That changing accepted history is extremely difficult or nearly impossible in practice, while stopping short of claiming it is absolutely or conceptually impossible.",
            ("Use the strongest supported non-absolute formulation."),
            ("Changing accepted history is absolutely impossible.",),
        ),
    )

    return tuple(
        Exercise(
            exercise_id=f"{CRITICAL_RETENTION_ID_PREFIX}{index:03d}",
            curriculum_id=curriculum_id,
            level=1,
            concept="benefits",
            subconcept="immutability",
            question=question,
            expected_answer=expected,
            source_refs=(source_ref,),
            question_type="closed_book_retention",
            required_reasoning_points=reasoning,
            forbidden_inferences=forbidden,
            grading_rubric_id="MB4E-L1-RUBRIC-V1",
            integrity_question=False,
            boss_question=False,
            requires_live_data=False,
        )
        for index, (question, expected, reasoning, forbidden) in enumerate(rows, start=1)
    )


def validate_grounded_critical_prerequisite(
    *,
    grounded_report_path: str | Path,
    grounded_manifest_path: str | Path,
    curriculum_id: str,
    gate_evidence: Mapping[str, object],
) -> dict[str, object]:
    """Validate a perfect grounded critical-blocker run without trusting its authority flag."""

    report_path = Path(grounded_report_path)
    manifest_path = Path(grounded_manifest_path)
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TargetedPyramidPracticeError(f"cannot read grounded critical prerequisite: {exc}") from exc
    if not isinstance(report, Mapping) or not isinstance(manifest, Mapping):
        raise TargetedPyramidPracticeError("grounded critical prerequisite artifacts must be JSON objects")

    if report.get("contract") != TARGETED_PRACTICE_CONTRACT or report.get("version") != TARGETED_PRACTICE_VERSION:
        raise TargetedPyramidPracticeError("grounded practice report contract/version is invalid")
    if report.get("curriculum_id") != curriculum_id or report.get("level") != 1:
        raise TargetedPyramidPracticeError("grounded practice report does not match curriculum/level")
    question_count = report.get("question_count")
    if isinstance(question_count, bool) or not isinstance(question_count, int) or question_count < 10:
        raise TargetedPyramidPracticeError("grounded critical prerequisite requires at least 10 questions")
    if (
        report.get("pass_count") != question_count
        or report.get("partial_count") != 0
        or report.get("fail_count") != 0
        or report.get("critical_failures") != 0
        or report.get("all_weaknesses_passed") is not True
        or report.get("critical_weaknesses_passed") is not True
        or report.get("practice_passed") is not True
    ):
        raise TargetedPyramidPracticeError("grounded critical prerequisite must be a perfect critical-origin pass")

    weakness_results = report.get("weakness_results")
    if not isinstance(weakness_results, list) or len(weakness_results) != 1:
        raise TargetedPyramidPracticeError("grounded critical prerequisite must contain exactly one weakness result")
    weakness = weakness_results[0]
    if (
        not isinstance(weakness, Mapping)
        or weakness.get("concept") != "benefits"
        or weakness.get("subconcept") != "immutability"
        or weakness.get("critical_origin") is not True
        or weakness.get("passed") is not True
        or weakness.get("pass_count") != weakness.get("total")
    ):
        raise TargetedPyramidPracticeError("grounded critical prerequisite weakness is not a perfect immutability critical-origin pass")

    if manifest.get("critical_blocker_contract") != CRITICAL_BLOCKER_SUPPLEMENTAL_CONTRACT:
        raise TargetedPyramidPracticeError("grounded critical manifest contract is invalid")
    if manifest.get("critical_blocker_version") != CRITICAL_BLOCKER_SUPPLEMENTAL_VERSION:
        raise TargetedPyramidPracticeError("grounded critical manifest version is invalid")
    if manifest.get("critical_blocker_mode") is not True:
        raise TargetedPyramidPracticeError("grounded critical manifest is not in critical-blocker mode")
    if manifest.get("curriculum_id") != curriculum_id or manifest.get("level") != 1:
        raise TargetedPyramidPracticeError("grounded critical manifest does not match curriculum/level")
    if manifest.get("canonical_bank_overlap") is not False or manifest.get("canonical_exam") is not False:
        raise TargetedPyramidPracticeError("grounded critical prerequisite must be noncanonical and nonoverlapping")
    if manifest.get("ledger_mutation_authorized") is not False:
        raise TargetedPyramidPracticeError("grounded critical prerequisite cannot authorize ledger mutation")

    manifest_gate = manifest.get("critical_blocker_gate")
    if not isinstance(manifest_gate, Mapping):
        raise TargetedPyramidPracticeError("grounded critical manifest is missing gate evidence")
    for field in ("curriculum_id", "level", "run_id", "run_seed", "critical_ids"):
        if manifest_gate.get(field) != gate_evidence.get(field):
            raise TargetedPyramidPracticeError(f"grounded critical manifest gate mismatch: {field}")

    return {
        "contract": "roberta-pyramid-grounded-critical-prerequisite/v1",
        "curriculum_id": curriculum_id,
        "level": 1,
        "question_count": question_count,
        "grounded_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "grounded_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "legacy_premature_authorization_ignored": report.get("canonical_attempt_authorized") is True,
        "grounded_practice_passed": True,
        "canonical_attempt_authorized": False,
        "next_gate": CRITICAL_GROUNDED_PASS_NEXT_GATE,
    }


def prepare_closed_book_critical_retention(
    *,
    curriculum_dir: str | Path,
    gate_evidence: Mapping[str, object],
    exclude_checkpoint_dirs: Sequence[str | Path] = (),
    questions_per_weakness: int = 10,
    seed: str = "critical-retention-r1",
    retention_bank: Sequence[Exercise] | None = None,
) -> tuple[PreparedTargetedPractice, str]:
    if questions_per_weakness < 10:
        raise TargetedPyramidPracticeError("closed-book critical retention requires at least 10 questions")

    manifest, canonical_bank = validate_package(curriculum_dir)
    curriculum_id = str(manifest["curriculum_id"])
    if gate_evidence.get("curriculum_id") != curriculum_id or gate_evidence.get("level") != 1:
        raise TargetedPyramidPracticeError("critical retention gate does not match validated curriculum")
    critical_ids = gate_evidence.get("critical_ids")
    if not isinstance(critical_ids, list) or not critical_ids or not all(isinstance(item, str) and item for item in critical_ids):
        raise TargetedPyramidPracticeError("critical retention gate critical ids are invalid")

    bank = tuple(retention_bank) if retention_bank is not None else mb4e_immutability_critical_retention_bank(curriculum_id)
    if not bank:
        raise TargetedPyramidPracticeError("closed-book critical retention bank is empty")
    ids = [item.exercise_id for item in bank]
    if len(ids) != len(set(ids)):
        raise TargetedPyramidPracticeError("closed-book critical retention bank contains duplicate ids")
    canonical_ids = {item.exercise_id for item in canonical_bank}
    overlap = canonical_ids & set(ids)
    if overlap:
        raise TargetedPyramidPracticeError(f"closed-book retention ids overlap canonical curriculum: {sorted(overlap)}")

    approved = manifest.get("approved_source_refs")
    if not isinstance(approved, list):
        raise TargetedPyramidPracticeError("validated curriculum manifest is missing approved_source_refs")
    approved_refs = {str(item) for item in approved}
    for item in bank:
        if item.curriculum_id != curriculum_id or item.level != 1:
            raise TargetedPyramidPracticeError("retention exercises must bind to the current Level-1 curriculum")
        if (item.concept, item.subconcept) != ("benefits", "immutability"):
            raise TargetedPyramidPracticeError("critical retention bank currently supports only benefits/immutability")
        if item.integrity_question or item.boss_question or item.requires_live_data:
            raise TargetedPyramidPracticeError("retention cannot contain integrity, Boss, or live-data questions")
        if not set(item.source_refs).issubset(approved_refs):
            raise TargetedPyramidPracticeError(f"retention exercise {item.exercise_id} references an unapproved source")

    seen: set[str] = set()
    if exclude_checkpoint_dirs:
        try:
            seen.update(load_seen_exercise_ids(exclude_checkpoint_dirs))
        except ValueError as exc:
            raise TargetedPyramidPracticeError(str(exc)) from exc
    pool = [item for item in bank if item.exercise_id not in seen]
    rng = random.Random(seed)
    rng.shuffle(pool)
    if len(pool) < questions_per_weakness:
        raise TargetedPyramidPracticeError(
            "closed-book retention bank does not contain enough fresh questions for benefits/immutability: "
            f"need {questions_per_weakness}, found {len(pool)}"
        )
    selected = tuple(pool[:questions_per_weakness])
    bank_hash = _canonical_hash([
        {
            "exercise_id": item.exercise_id,
            "question": item.question,
            "expected_answer": item.expected_answer,
            "source_refs": list(item.source_refs),
            "required_reasoning_points": list(item.required_reasoning_points),
            "forbidden_inferences": list(item.forbidden_inferences),
        }
        for item in selected
    ])
    prepared = PreparedTargetedPractice(
        curriculum_id=curriculum_id,
        level=1,
        exercises=selected,
        weakness_critical_counts=(("benefits", "immutability", len(critical_ids)),),
        original_weak_ids=tuple(sorted(critical_ids)),
        source_grounded_weak_items=0,
    )
    return prepared, bank_hash


def critical_retention_binding(
    prepared: PreparedTargetedPractice,
    prerequisite: Mapping[str, object],
) -> str:
    material = {
        "contract": CRITICAL_RETENTION_CONTRACT,
        "version": CRITICAL_RETENTION_VERSION,
        "curriculum_id": prepared.curriculum_id,
        "level": prepared.level,
        "original_critical_ids": list(prepared.original_weak_ids),
        "exercise_ids": [item.exercise_id for item in prepared.exercises],
        "questions": [item.question for item in prepared.exercises],
        "grounded_report_sha256": prerequisite.get("grounded_report_sha256"),
        "grounded_manifest_sha256": prerequisite.get("grounded_manifest_sha256"),
        "closed_book": True,
        "source_context_injected": False,
    }
    return _canonical_hash(material)
