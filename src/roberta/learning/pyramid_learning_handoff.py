"""Fail-closed handoff from Pyramid weaknesses into the Learning System.

This module does not create Phase 8 candidate lessons, Phase 9 verification
results, Phase 10 retention decisions, or trusted memory. It preserves a
Pyramid weakness as content-addressed diagnostic evidence and requires canonical
source grounding before the existing Learning System can consider a lesson.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Iterable, Sequence

from .pyramid import Exercise
from .pyramid_remediation import WeakItem


PYRAMID_LEARNING_HANDOFF_CONTRACT = "roberta-pyramid-learning-handoff/v1"
PYRAMID_LEARNING_HANDOFF_VERSION = "1.0.0"
_REQUIRED_CHECKPOINT_SCHEMA = "roberta-pyramid-checkpoint/v3"
_REQUIRED_GRADING_SEMANTICS = "question-first-adjudication/v1"
_REQUIRED_NEXT_GATE = "source_grounded_phase7_reconstruction"
_GRADER_NOTE_ROLE = "diagnostic_only_not_source_evidence"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GRADE_SCORES = {"PASS": 1.0, "PARTIAL": 0.5, "FAIL": 0.0}


class PyramidLearningHandoffError(ValueError):
    """Raised when Pyramid failure evidence cannot be handed off safely."""


@dataclass(frozen=True, slots=True)
class PyramidLearningHandoff:
    handoff_id: str
    handoff_hash: str
    handoff_contract: str
    handoff_version: str
    curriculum_id: str
    exercise_id: str
    level: int
    concept: str
    subconcept: str | None
    question: str
    roberta_answer: str
    grade: str
    score: float
    failure_codes: tuple[str, ...]
    critical_failure: bool
    grader_note: str
    grader_note_role: str
    source_refs: tuple[str, ...]
    checkpoint_file: str
    checkpoint_sha256: str
    checkpoint_schema: str
    grading_semantics: str
    remediation_query: str
    required_next_gate: str
    source_grounding_required: bool
    phase8_candidate_creation_authorized: bool
    source_truth_authorized: bool
    live_state_authorized: bool
    memory_promotion_authorized: bool
    retention_authorized: bool
    governance_mutation_authorized: bool
    execution_authorized: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "handoff_id": self.handoff_id,
            "handoff_hash": self.handoff_hash,
            **_handoff_material(self),
        }


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PyramidLearningHandoffError(
            "Pyramid learning handoff material must be canonical JSON-compatible data"
        ) from exc


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise PyramidLearningHandoffError(f"{name} must be a normalized non-empty string")
    return value


def _normalized_text(name: str, value: object) -> str:
    if not isinstance(value, str) or value != value.strip():
        raise PyramidLearningHandoffError(f"{name} must be a normalized string")
    return value


def _optional_text(name: str, value: object) -> str | None:
    if value is None:
        return None
    return _normalized_text(name, value)


def _source_refs(value: Sequence[str]) -> tuple[str, ...]:
    refs = tuple(_text("source ref", item) for item in value)
    if not refs:
        raise PyramidLearningHandoffError("Pyramid learning handoff requires at least one approved source ref")
    if len(set(refs)) != len(refs):
        raise PyramidLearningHandoffError("Pyramid learning handoff source refs must be unique")
    return refs


def _handoff_material(handoff: PyramidLearningHandoff) -> dict[str, Any]:
    return {
        "handoff_contract": handoff.handoff_contract,
        "handoff_version": handoff.handoff_version,
        "curriculum_id": handoff.curriculum_id,
        "exercise_id": handoff.exercise_id,
        "level": handoff.level,
        "concept": handoff.concept,
        "subconcept": handoff.subconcept,
        "question": handoff.question,
        "roberta_answer": handoff.roberta_answer,
        "grade": handoff.grade,
        "score": handoff.score,
        "failure_codes": list(handoff.failure_codes),
        "critical_failure": handoff.critical_failure,
        "grader_note": handoff.grader_note,
        "grader_note_role": handoff.grader_note_role,
        "source_refs": list(handoff.source_refs),
        "checkpoint_file": handoff.checkpoint_file,
        "checkpoint_sha256": handoff.checkpoint_sha256,
        "checkpoint_schema": handoff.checkpoint_schema,
        "grading_semantics": handoff.grading_semantics,
        "remediation_query": handoff.remediation_query,
        "required_next_gate": handoff.required_next_gate,
        "source_grounding_required": handoff.source_grounding_required,
        "phase8_candidate_creation_authorized": handoff.phase8_candidate_creation_authorized,
        "source_truth_authorized": handoff.source_truth_authorized,
        "live_state_authorized": handoff.live_state_authorized,
        "memory_promotion_authorized": handoff.memory_promotion_authorized,
        "retention_authorized": handoff.retention_authorized,
        "governance_mutation_authorized": handoff.governance_mutation_authorized,
        "execution_authorized": handoff.execution_authorized,
    }


def validate_pyramid_learning_handoff(
    handoff: PyramidLearningHandoff,
) -> PyramidLearningHandoff:
    if not isinstance(handoff, PyramidLearningHandoff):
        raise PyramidLearningHandoffError("handoff must be PyramidLearningHandoff")
    if handoff.handoff_contract != PYRAMID_LEARNING_HANDOFF_CONTRACT:
        raise PyramidLearningHandoffError("unsupported Pyramid learning handoff contract")
    if handoff.handoff_version != PYRAMID_LEARNING_HANDOFF_VERSION:
        raise PyramidLearningHandoffError("unsupported Pyramid learning handoff version")

    for name, value in (
        ("curriculum_id", handoff.curriculum_id),
        ("exercise_id", handoff.exercise_id),
        ("concept", handoff.concept),
        ("question", handoff.question),
        ("roberta_answer", handoff.roberta_answer),
        ("checkpoint_file", handoff.checkpoint_file),
        ("remediation_query", handoff.remediation_query),
    ):
        _text(name, value)
    _optional_text("subconcept", handoff.subconcept)
    _normalized_text("grader_note", handoff.grader_note)

    if isinstance(handoff.level, bool) or not isinstance(handoff.level, int) or not 1 <= handoff.level <= 20:
        raise PyramidLearningHandoffError("level must be an integer from 1 through 20")
    if handoff.grade not in _GRADE_SCORES:
        raise PyramidLearningHandoffError("grade must be PASS, PARTIAL, or FAIL")
    if not math.isfinite(handoff.score) or handoff.score != _GRADE_SCORES[handoff.grade]:
        raise PyramidLearningHandoffError("grade score does not match Pyramid grade semantics")
    if handoff.grade == "PASS" and not handoff.critical_failure:
        raise PyramidLearningHandoffError("non-critical PASS results are not learning handoffs")

    for code in handoff.failure_codes:
        _text("failure code", code)
    if len(set(handoff.failure_codes)) != len(handoff.failure_codes):
        raise PyramidLearningHandoffError("failure codes must be unique")

    _source_refs(handoff.source_refs)
    if _SHA256_RE.fullmatch(handoff.checkpoint_sha256) is None:
        raise PyramidLearningHandoffError("checkpoint_sha256 must be a lowercase SHA-256 digest")
    if handoff.checkpoint_schema != _REQUIRED_CHECKPOINT_SCHEMA:
        raise PyramidLearningHandoffError(
            f"checkpoint schema must equal {_REQUIRED_CHECKPOINT_SCHEMA}"
        )
    if handoff.grading_semantics != _REQUIRED_GRADING_SEMANTICS:
        raise PyramidLearningHandoffError(
            f"grading semantics must equal {_REQUIRED_GRADING_SEMANTICS}"
        )
    if handoff.grader_note_role != _GRADER_NOTE_ROLE:
        raise PyramidLearningHandoffError("grader note must remain diagnostic-only")
    if handoff.required_next_gate != _REQUIRED_NEXT_GATE:
        raise PyramidLearningHandoffError("Pyramid handoff must require canonical source-grounded reconstruction")
    if handoff.source_grounding_required is not True:
        raise PyramidLearningHandoffError("source grounding must be required")

    authority_flags = (
        handoff.phase8_candidate_creation_authorized,
        handoff.source_truth_authorized,
        handoff.live_state_authorized,
        handoff.memory_promotion_authorized,
        handoff.retention_authorized,
        handoff.governance_mutation_authorized,
        handoff.execution_authorized,
    )
    if any(value is not False for value in authority_flags):
        raise PyramidLearningHandoffError("Pyramid learning handoff cannot authorize promotion, truth, retention, governance, or execution")

    expected_hash = _hash(_handoff_material(handoff))
    if handoff.handoff_hash != expected_hash or handoff.handoff_id != f"pyrlearn_{expected_hash}":
        raise PyramidLearningHandoffError("Pyramid learning handoff identity/content is invalid")
    return handoff


def _make_handoff(exercise: Exercise, weak: WeakItem) -> PyramidLearningHandoff:
    source_refs = _source_refs(exercise.source_refs)
    grade = _text("grade", weak.grade).upper()
    if grade not in _GRADE_SCORES:
        raise PyramidLearningHandoffError("grade must be PASS, PARTIAL, or FAIL")
    score = float(weak.score)
    if not math.isfinite(score) or score != _GRADE_SCORES[grade]:
        raise PyramidLearningHandoffError("grade score does not match Pyramid grade semantics")

    concept = _text("concept", exercise.concept)
    subconcept = _optional_text("subconcept", exercise.subconcept)
    concept_path = concept if not subconcept else f"{concept}/{subconcept}"
    remediation_query = (
        f"Ground exercise {exercise.exercise_id} concept {concept_path} "
        "against canonical approved source evidence before any Phase 8 candidate lesson is created; "
        "treat Pyramid grader diagnosis as diagnostic only, not source evidence."
    )
    material = {
        "handoff_contract": PYRAMID_LEARNING_HANDOFF_CONTRACT,
        "handoff_version": PYRAMID_LEARNING_HANDOFF_VERSION,
        "curriculum_id": _text("curriculum_id", exercise.curriculum_id),
        "exercise_id": _text("exercise_id", exercise.exercise_id),
        "level": exercise.level,
        "concept": concept,
        "subconcept": subconcept,
        "question": _text("question", exercise.question),
        "roberta_answer": _text("Roberta answer", weak.answer),
        "grade": grade,
        "score": score,
        "failure_codes": list(tuple(sorted({_text("failure code", code) for code in weak.failure_codes}))),
        "critical_failure": bool(weak.critical_failure),
        "grader_note": _normalized_text("grader_note", weak.grader_note),
        "grader_note_role": _GRADER_NOTE_ROLE,
        "source_refs": list(source_refs),
        "checkpoint_file": _text("checkpoint_file", weak.checkpoint_file),
        "checkpoint_sha256": _text("checkpoint_sha256", weak.checkpoint_sha256),
        "checkpoint_schema": _text("checkpoint_schema", weak.checkpoint_schema),
        "grading_semantics": _text("grading_semantics", weak.grading_semantics),
        "remediation_query": remediation_query,
        "required_next_gate": _REQUIRED_NEXT_GATE,
        "source_grounding_required": True,
        "phase8_candidate_creation_authorized": False,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "memory_promotion_authorized": False,
        "retention_authorized": False,
        "governance_mutation_authorized": False,
        "execution_authorized": False,
    }
    digest = _hash(material)
    handoff = PyramidLearningHandoff(
        handoff_id=f"pyrlearn_{digest}",
        handoff_hash=digest,
        handoff_contract=str(material["handoff_contract"]),
        handoff_version=str(material["handoff_version"]),
        curriculum_id=str(material["curriculum_id"]),
        exercise_id=str(material["exercise_id"]),
        level=int(material["level"]),
        concept=str(material["concept"]),
        subconcept=material["subconcept"],
        question=str(material["question"]),
        roberta_answer=str(material["roberta_answer"]),
        grade=str(material["grade"]),
        score=float(material["score"]),
        failure_codes=tuple(str(code) for code in material["failure_codes"]),
        critical_failure=bool(material["critical_failure"]),
        grader_note=str(material["grader_note"]),
        grader_note_role=str(material["grader_note_role"]),
        source_refs=tuple(str(ref) for ref in material["source_refs"]),
        checkpoint_file=str(material["checkpoint_file"]),
        checkpoint_sha256=str(material["checkpoint_sha256"]),
        checkpoint_schema=str(material["checkpoint_schema"]),
        grading_semantics=str(material["grading_semantics"]),
        remediation_query=str(material["remediation_query"]),
        required_next_gate=str(material["required_next_gate"]),
        source_grounding_required=True,
        phase8_candidate_creation_authorized=False,
        source_truth_authorized=False,
        live_state_authorized=False,
        memory_promotion_authorized=False,
        retention_authorized=False,
        governance_mutation_authorized=False,
        execution_authorized=False,
    )
    return validate_pyramid_learning_handoff(handoff)


def build_pyramid_learning_handoffs(
    exercises: Sequence[Exercise],
    weak_items: Sequence[WeakItem],
    *,
    curriculum_id: str,
    approved_source_refs: Sequence[str],
) -> tuple[PyramidLearningHandoff, ...]:
    expected_curriculum = _text("curriculum_id", curriculum_id)
    approved = set(_source_refs(tuple(approved_source_refs)))
    by_id = {item.exercise_id: item for item in exercises}
    if len(by_id) != len(exercises):
        raise PyramidLearningHandoffError("curriculum contains duplicate exercise ids")
    for exercise in exercises:
        if exercise.curriculum_id != expected_curriculum:
            raise PyramidLearningHandoffError("exercise curriculum id does not match validated curriculum")

    handoffs: list[PyramidLearningHandoff] = []
    for weak in weak_items:
        if weak.grade == "PASS" and not weak.critical_failure:
            continue
        exercise = by_id.get(weak.exercise_id)
        if exercise is None:
            raise PyramidLearningHandoffError(
                f"checkpoint exercise id {weak.exercise_id!r} not found in validated curriculum"
            )
        refs = _source_refs(exercise.source_refs)
        if not set(refs).issubset(approved):
            raise PyramidLearningHandoffError(
                f"exercise {exercise.exercise_id} references an unapproved source"
            )
        handoffs.append(_make_handoff(exercise, weak))
    return tuple(handoffs)


def write_pyramid_learning_handoffs_jsonl(
    path: str | Path,
    handoffs: Iterable[PyramidLearningHandoff],
) -> None:
    canonical_handoffs = tuple(validate_pyramid_learning_handoff(handoff) for handoff in handoffs)
    serialized = tuple(
        json.dumps(handoff.to_mapping(), ensure_ascii=False, sort_keys=True) + "\n"
        for handoff in canonical_handoffs
    )

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            handle.writelines(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except BaseException:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
        raise
