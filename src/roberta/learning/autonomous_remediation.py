from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from .pyramid import Exercise
from .pyramid_exam import ExamOutcome, run_exam
from .pyramid_learned_concept_answer import PyramidLearnedConceptAnswerModel
from .pyramid_learned_concepts import LearnedConcept, write_learned_concepts


AUTONOMOUS_REMEDIATION_CONTRACT = "roberta-autonomous-remediation/v1"
AUTONOMOUS_REMEDIATION_VERSION = "1.0.0"
GROUNDED_QUESTIONS_PER_WEAKNESS = 5
RETENTION_QUESTIONS_PER_WEAKNESS = 10


class AutonomousRemediationError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _all_passed(outcome: ExamOutcome, expected: int) -> bool:
    return (
        len(outcome.graded_answers) == expected
        and all(item.grade == "PASS" for item in outcome.graded_answers)
        and all(not item.critical_failure for item in outcome.graded_answers)
    )


def _weak_exercises(
    bank: Sequence[Exercise], outcome: ExamOutcome
) -> tuple[Exercise, ...]:
    by_id = {item.exercise_id: item for item in bank}
    weak_ids = {
        item.exercise_id
        for item in outcome.graded_answers
        if item.grade != "PASS" or item.critical_failure
    }
    missing = sorted(weak_ids - set(by_id))
    if missing:
        raise AutonomousRemediationError(
            f"failed autonomous exam references exercises absent from the validated bank: {missing}"
        )
    return tuple(by_id[item_id] for item_id in sorted(weak_ids))


def _provisional_concepts(
    *, curriculum_id: str, level: int, weak: Sequence[Exercise]
) -> tuple[LearnedConcept, ...]:
    grouped: dict[tuple[str, str | None], list[Exercise]] = {}
    for item in weak:
        grouped.setdefault((item.concept, item.subconcept), []).append(item)
    concepts: list[LearnedConcept] = []
    for (concept, subconcept), items in sorted(
        grouped.items(), key=lambda value: (value[0][0], value[0][1] or "")
    ):
        principles = {item.expected_answer.strip() for item in items}
        if len(principles) != 1:
            raise AutonomousRemediationError(
                f"weakness {concept}/{subconcept or '-'} has no stable source-grounded principle"
            )
        principle = next(iter(principles))
        source_refs = tuple(sorted({ref for item in items for ref in item.source_refs}))
        if not principle or not source_refs:
            raise AutonomousRemediationError("autonomous remediation requires source-bound principles")
        material = {
            "contract": "roberta-pyramid-learned-concept-memory/v1",
            "curriculum_id": curriculum_id,
            "level": level,
            "concept": concept,
            "subconcept": subconcept,
            "principle": principle,
            "source_refs": list(source_refs),
        }
        concepts.append(
            LearnedConcept(
                curriculum_id=curriculum_id,
                level=level,
                concept=concept,
                subconcept=subconcept,
                principle=principle,
                source_refs=source_refs,
                critical_exercise_ids=tuple(sorted(item.exercise_id for item in items)),
                retention_report_sha256="0" * 64,
                retention_manifest_sha256="0" * 64,
                checkpoint_sha256=(("pending", "0" * 64),),
                concept_hash=_canonical_hash(material),
            )
        )
    return tuple(concepts)


def _practice_bank(
    concepts: Sequence[LearnedConcept], *, count: int, lane: str
) -> tuple[Exercise, ...]:
    exercises: list[Exercise] = []
    for concept in concepts:
        for index in range(1, count + 1):
            digest = hashlib.sha256(
                f"{concept.concept_hash}|{lane}|{index}".encode("utf-8")
            ).hexdigest()[:20]
            exercises.append(
                Exercise(
                    exercise_id=f"AUTO-REMEDIATE-{lane.upper()}-{digest}",
                    curriculum_id=concept.curriculum_id,
                    level=concept.level,
                    concept=concept.concept,
                    subconcept=concept.subconcept,
                    question=(
                        f"Autonomous {lane} check {index}: Explain the validated principle for "
                        f"{concept.concept.replace('_', ' ')}"
                        + (
                            f" / {concept.subconcept.replace('_', ' ')}."
                            if concept.subconcept
                            else "."
                        )
                    ),
                    expected_answer=concept.principle,
                    source_refs=concept.source_refs,
                    question_type="retention" if lane == "retention" else "practice",
                    required_reasoning_points=(concept.principle,),
                    forbidden_inferences=("Do not invent live state or execution authority.",),
                    grading_rubric_id="autonomous-remediation-question-first-v1",
                )
            )
    return tuple(exercises)


def run_autonomous_remediation(
    *,
    curriculum_id: str,
    level: int,
    bank: Sequence[Exercise],
    failed_outcome: ExamOutcome,
    model: Any,
    output_dir: str | Path,
    failed_checkpoint_dir: str | Path,
    learned_concepts_path: str | Path,
    batch_size: int,
) -> tuple[LearnedConcept, ...]:
    """Teach failed concepts, verify closed-book retention, then promote them.

    Source-grounded memory is used only in the grounded practice and transfer
    lanes. The intervening retention lane receives the unaugmented model. Nothing
    is written to the learned-concepts store unless all three lanes pass perfectly.
    """

    weak = _weak_exercises(bank, failed_outcome)
    if not weak:
        raise AutonomousRemediationError("failed attempt exposes no remediable weak exercises")
    provisional = _provisional_concepts(
        curriculum_id=curriculum_id, level=level, weak=weak
    )
    root = Path(output_dir)
    grounded_bank = _practice_bank(
        provisional, count=GROUNDED_QUESTIONS_PER_WEAKNESS, lane="grounded"
    )
    grounded = run_exam(
        exercises=grounded_bank,
        answer_model=PyramidLearnedConceptAnswerModel(model, provisional),
        grader_model=model,
        batch_size=batch_size,
        checkpoint_dir=root / "grounded_checkpoints",
        canonical_exam=False,
    )
    if not _all_passed(grounded, len(grounded_bank)):
        raise AutonomousRemediationError("source-grounded remediation practice did not pass perfectly")

    retention_bank = _practice_bank(
        provisional, count=RETENTION_QUESTIONS_PER_WEAKNESS, lane="retention"
    )
    retention = run_exam(
        exercises=retention_bank,
        answer_model=model,
        grader_model=model,
        batch_size=batch_size,
        checkpoint_dir=root / "retention_checkpoints",
        canonical_exam=False,
    )
    if not _all_passed(retention, len(retention_bank)):
        raise AutonomousRemediationError("closed-book remediation retention did not pass perfectly")

    report_path = root / "retention_report.json"
    manifest_path = root / "retention_manifest.json"
    _atomic_json(
        report_path,
        {
            "contract": AUTONOMOUS_REMEDIATION_CONTRACT,
            "version": AUTONOMOUS_REMEDIATION_VERSION,
            "curriculum_id": curriculum_id,
            "level": level,
            "weakness_count": len(provisional),
            "question_count": len(retention_bank),
            "pass_count": len(retention.graded_answers),
            "partial_count": 0,
            "fail_count": 0,
            "critical_failures": 0,
            "closed_book": True,
            "source_context_injected": False,
            "canonical_exam": False,
            "ledger_mutation_authorized": False,
            "source_truth_authorized": False,
            "live_state_authorized": False,
            "execution_authorized": False,
        },
    )
    _atomic_json(
        manifest_path,
        {
            "contract": AUTONOMOUS_REMEDIATION_CONTRACT,
            "version": AUTONOMOUS_REMEDIATION_VERSION,
            "curriculum_id": curriculum_id,
            "level": level,
            "grounded_question_count": len(grounded_bank),
            "retention_question_count": len(retention_bank),
            "grounded_passed": True,
            "closed_book_retention_passed": True,
            "source_context_injected_into_retention": False,
            "canonical_exam": False,
            "ledger_mutation_authorized": False,
            "general_durable_memory_promotion_authorized": False,
            "source_truth_authorized": False,
            "live_state_authorized": False,
            "execution_authorized": False,
        },
    )
    checkpoint_root = Path(failed_checkpoint_dir)
    checkpoint_paths = tuple(sorted(checkpoint_root.glob("level_*_batch_*.json")))
    if not checkpoint_paths:
        raise AutonomousRemediationError("failed attempt checkpoints are missing")
    checkpoint_hashes = tuple((str(path), _sha256(path)) for path in checkpoint_paths)
    verified = tuple(
        replace(
            item,
            retention_report_sha256=_sha256(report_path),
            retention_manifest_sha256=_sha256(manifest_path),
            checkpoint_sha256=checkpoint_hashes,
        )
        for item in provisional
    )

    transfer = run_exam(
        exercises=weak,
        answer_model=PyramidLearnedConceptAnswerModel(model, verified),
        grader_model=model,
        batch_size=batch_size,
        checkpoint_dir=root / "transfer_checkpoints",
        canonical_exam=False,
    )
    if not _all_passed(transfer, len(weak)):
        raise AutonomousRemediationError("verified concept transfer probe did not pass perfectly")
    write_learned_concepts(learned_concepts_path, verified)
    _atomic_json(
        root / "promotion.json",
        {
            "contract": AUTONOMOUS_REMEDIATION_CONTRACT,
            "version": AUTONOMOUS_REMEDIATION_VERSION,
            "curriculum_id": curriculum_id,
            "level": level,
            "promoted_concepts": len(verified),
            "transfer_questions": len(weak),
            "transfer_passed": True,
            "pyramid_learned_concept_authorized": True,
            "general_durable_memory_promotion_authorized": False,
            "source_truth_authorized": False,
            "live_state_authorized": False,
            "execution_authorized": False,
        },
    )
    return verified
