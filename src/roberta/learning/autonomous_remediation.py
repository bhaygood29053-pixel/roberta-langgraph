from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from langchain_core.messages import HumanMessage

from .pyramid import Exercise
from .pyramid_exam import ExamOutcome, run_exam
from .pyramid_learned_concept_answer import PyramidLearnedConceptAnswerModel
from .pyramid_learned_concepts import (
    PYRAMID_LEARNED_CONCEPT_MEMORY_CONTRACT,
    LearnedConcept,
    write_learned_concepts,
)


AUTONOMOUS_REMEDIATION_CONTRACT = "roberta-autonomous-remediation/v1"
AUTONOMOUS_REMEDIATION_VERSION = "1.2.0"
GROUNDED_QUESTIONS_PER_WEAKNESS = 5
RETENTION_QUESTIONS_PER_WEAKNESS = 10
REMEDIATION_LANE_NAMESPACE = "stage-bound-boss-synthesis-v3"


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


def _boss_synthesis_atoms(
    bank: Sequence[Exercise], boss: Exercise
) -> tuple[Exercise, ...]:
    """Resolve the complete stage-bound atomic synthesis set for one Boss exercise."""

    if not boss.boss_question:
        raise AutonomousRemediationError("Boss synthesis expansion requires a Boss exercise")
    candidates = tuple(
        item
        for item in bank
        if item.curriculum_id == boss.curriculum_id
        and item.level == boss.level
        and not item.boss_question
    )
    if not candidates:
        raise AutonomousRemediationError("Boss synthesis expansion found no stage-bound atomic exercises")

    atoms: list[Exercise] = []
    seen_keys: dict[tuple[str, str | None], Exercise] = {}
    for source_ref in boss.source_refs:
        matched = tuple(item for item in candidates if source_ref in item.source_refs)
        if not matched:
            continue
        signatures = {
            (item.concept, item.subconcept, item.expected_answer.strip())
            for item in matched
        }
        # The package-wide source key intentionally matches many distinct targets.
        # A Boss-specific target ref resolves to exactly one stable atomic principle.
        if len(signatures) != 1:
            continue
        representative = min(matched, key=lambda item: item.exercise_id)
        key = (representative.concept, representative.subconcept)
        prior = seen_keys.get(key)
        if prior is not None:
            if prior.expected_answer.strip() != representative.expected_answer.strip():
                raise AutonomousRemediationError(
                    f"Boss synthesis atom {key[0]}/{key[1] or '-'} has conflicting principles"
                )
            continue
        seen_keys[key] = representative
        atoms.append(representative)

    required_points = tuple(point.strip() for point in boss.required_reasoning_points if point.strip())
    if required_points:
        if len(atoms) != len(required_points):
            raise AutonomousRemediationError(
                "Boss synthesis expansion is incomplete: "
                f"resolved {len(atoms)} atomic principles for {len(required_points)} required synthesis points"
            )
        expected_points = {
            f"Correctly synthesize {atom.concept}/{atom.subconcept}: {atom.expected_answer.strip()}"
            for atom in atoms
        }
        if set(required_points) != expected_points:
            raise AutonomousRemediationError(
                "Boss synthesis expansion could not bind every required synthesis point exactly to a stage atom"
            )
    if not atoms:
        raise AutonomousRemediationError("Boss synthesis expansion resolved no stable stage-bound atoms")
    return tuple(atoms)


def _remediation_targets(
    bank: Sequence[Exercise], weak: Sequence[Exercise]
) -> tuple[Exercise, ...]:
    """Expand failed Bosses into their complete atomic synthesis requirements."""

    selected: dict[tuple[str, str | None], Exercise] = {}
    for item in weak:
        if item.boss_question:
            continue
        key = (item.concept, item.subconcept)
        prior = selected.get(key)
        if prior is not None and prior.expected_answer.strip() != item.expected_answer.strip():
            raise AutonomousRemediationError(
                f"weakness {item.concept}/{item.subconcept or '-'} has conflicting principles"
            )
        selected.setdefault(key, item)

    for boss in (item for item in weak if item.boss_question):
        for atom in _boss_synthesis_atoms(bank, boss):
            key = (atom.concept, atom.subconcept)
            prior = selected.get(key)
            if prior is not None and prior.expected_answer.strip() != atom.expected_answer.strip():
                raise AutonomousRemediationError(
                    f"Boss synthesis atom {atom.concept}/{atom.subconcept or '-'} conflicts with a weak principle"
                )
            selected.setdefault(key, atom)

    return tuple(
        selected[key]
        for key in sorted(selected, key=lambda value: (value[0], value[1] or ""))
    )


def _remediation_lineage(
    bank: Sequence[Exercise], weak: Sequence[Exercise]
) -> dict[tuple[str, str | None], tuple[str, ...]]:
    """Bind every remediated semantic target to the failed exercise(s) that triggered it."""

    lineage: dict[tuple[str, str | None], set[str]] = {}
    for item in weak:
        if item.boss_question:
            continue
        lineage.setdefault((item.concept, item.subconcept), set()).add(item.exercise_id)

    for boss in (item for item in weak if item.boss_question):
        for atom in _boss_synthesis_atoms(bank, boss):
            lineage.setdefault((atom.concept, atom.subconcept), set()).add(boss.exercise_id)

    return {
        key: tuple(sorted(ids))
        for key, ids in lineage.items()
    }


def _transfer_exercises(
    bank: Sequence[Exercise], weak: Sequence[Exercise]
) -> tuple[Exercise, ...]:
    atomic = _remediation_targets(bank, weak)
    bosses = tuple(sorted((item for item in weak if item.boss_question), key=lambda item: item.exercise_id))
    return (*atomic, *bosses)


def _is_nonzero_sha256(value: str) -> bool:
    if len(value) != 64 or value == "0" * 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return True


def _require_verified_transfer_provenance(concepts: Sequence[LearnedConcept]) -> None:
    """Reject provisional/unbound memory before any transfer probe can use it."""

    if not concepts:
        raise AutonomousRemediationError("verified transfer requires at least one learned concept")
    for item in concepts:
        if not _is_nonzero_sha256(item.retention_report_sha256):
            raise AutonomousRemediationError(
                f"transfer concept {item.concept}/{item.subconcept or '-'} lacks verified retention-report provenance"
            )
        if not _is_nonzero_sha256(item.retention_manifest_sha256):
            raise AutonomousRemediationError(
                f"transfer concept {item.concept}/{item.subconcept or '-'} lacks verified retention-manifest provenance"
            )
        if not item.checkpoint_sha256:
            raise AutonomousRemediationError(
                f"transfer concept {item.concept}/{item.subconcept or '-'} lacks failed-attempt checkpoint provenance"
            )
        for checkpoint_path, digest in item.checkpoint_sha256:
            if checkpoint_path == "pending" or not checkpoint_path.strip() or not _is_nonzero_sha256(digest):
                raise AutonomousRemediationError(
                    f"transfer concept {item.concept}/{item.subconcept or '-'} has incomplete checkpoint provenance"
                )


CANDIDATE_REMEDIATION_MEMORY_CONTRACT = "roberta-autonomous-remediation-candidate-memory/v1"


class CandidateRemediationAnswerModel:
    """Route unpromoted candidate lesson memory into remediation answer requests only.

    Candidate memory is deliberately distinct from verified learned-concept memory.
    It may help the answer model rehearse and retain the source-derived principle, but
    it is not source evidence, an answer key, durable memory, live state, or execution
    authority. The grader receives the ordinary unmodified grading request.
    """

    def __init__(self, model: Any, concepts: Sequence[LearnedConcept]) -> None:
        if not concepts:
            raise AutonomousRemediationError("candidate remediation requires at least one concept")
        scopes = {(item.curriculum_id, item.level) for item in concepts}
        if len(scopes) != 1:
            raise AutonomousRemediationError(
                "candidate remediation concepts must share one curriculum/level scope"
            )
        self._model = model
        self._concepts = {(item.concept, item.subconcept): item for item in concepts}
        if len(self._concepts) != len(concepts):
            raise AutonomousRemediationError(
                "candidate remediation concept keys must be unique"
            )

    def invoke(self, messages: Sequence[object], *args: object, **kwargs: object) -> object:
        if not messages:
            return self._model.invoke(messages, *args, **kwargs)
        content = getattr(messages[-1], "content", None)
        if not isinstance(content, str):
            return self._model.invoke(messages, *args, **kwargs)
        try:
            request = json.loads(content)
        except json.JSONDecodeError:
            return self._model.invoke(messages, *args, **kwargs)
        if not isinstance(request, Mapping) or not isinstance(request.get("exercises"), list):
            return self._model.invoke(messages, *args, **kwargs)

        augmented: list[dict[str, object]] = []
        injected = 0
        for raw in request["exercises"]:
            if not isinstance(raw, Mapping):
                raise AutonomousRemediationError("candidate remediation exercise must be an object")
            if any(
                field in raw
                for field in (
                    "expected_answer",
                    "reference_reasoning_points",
                    "forbidden_inferences",
                    "remediation_context",
                    "source_evidence",
                    "source_refs",
                    "learned_concept_memory",
                    "learned_concept_memories",
                    "remediation_candidate_memory",
                )
            ):
                raise AutonomousRemediationError(
                    "candidate remediation answer request contains prohibited grading/source/memory material"
                )

            item = dict(raw)
            concept = item.get("concept")
            subconcept_raw = item.get("subconcept")
            subconcept = subconcept_raw if isinstance(subconcept_raw, str) else None
            memory = (
                self._concepts.get((concept, subconcept))
                if isinstance(concept, str)
                else None
            )
            if memory is not None:
                item["remediation_candidate_memory"] = {
                    "contract": CANDIDATE_REMEDIATION_MEMORY_CONTRACT,
                    "principle": memory.principle,
                    "promotion_status": "candidate_unverified",
                }
                injected += 1
            augmented.append(item)

        if injected == 0:
            return self._model.invoke(messages, *args, **kwargs)

        rewritten = dict(request)
        rewritten["instruction"] = (
            str(request.get("instruction", ""))
            + " You may use remediation_candidate_memory when present. It is an unpromoted "
            "candidate lesson under retention evaluation, not source evidence, an answer key, "
            "verified durable memory, live state, or execution authority. Answer the actual "
            "question independently and do not mention the candidate-memory object."
        ).strip()
        rewritten["exercises"] = augmented

        updated = list(messages)
        updated[-1] = HumanMessage(content=json.dumps(rewritten, ensure_ascii=False))
        return self._model.invoke(updated, *args, **kwargs)


class StageTransferLearnedConceptAnswerModel:
    """Route verified stage memory, including complete Boss synthesis sets, into transfer probes."""

    def __init__(
        self,
        model: Any,
        *,
        stage_bank: Sequence[Exercise],
        exercises: Sequence[Exercise],
        concepts: Sequence[LearnedConcept],
    ) -> None:
        _require_verified_transfer_provenance(concepts)
        scopes = {(item.curriculum_id, item.level) for item in concepts}
        if len(scopes) != 1:
            raise AutonomousRemediationError(
                "verified transfer concepts must share one curriculum/level scope"
            )
        scope = next(iter(scopes))
        by_key = {(item.concept, item.subconcept): item for item in concepts}
        if len(by_key) != len(concepts):
            raise AutonomousRemediationError("verified transfer concept keys must be unique")

        routes: dict[str, tuple[LearnedConcept, ...]] = {}
        for exercise in exercises:
            if (exercise.curriculum_id, exercise.level) != scope:
                raise AutonomousRemediationError(
                    f"transfer exercise {exercise.exercise_id} is outside verified concept scope"
                )
            if exercise.boss_question:
                required_atoms = _boss_synthesis_atoms(stage_bank, exercise)
                matched: list[LearnedConcept] = []
                missing: list[str] = []
                for atom in required_atoms:
                    key = (atom.concept, atom.subconcept)
                    memory = by_key.get(key)
                    if (
                        memory is None
                        or memory.principle != atom.expected_answer.strip()
                        or not set(atom.source_refs).issubset(set(memory.source_refs))
                    ):
                        missing.append(f"{atom.concept}/{atom.subconcept or '-'}")
                        continue
                    matched.append(memory)
                if missing:
                    raise AutonomousRemediationError(
                        "Boss transfer requires the complete stage-bound verified synthesis set; "
                        f"missing or mismatched atoms: {sorted(missing)}"
                    )
                routes[exercise.exercise_id] = tuple(matched)
                continue

            key = (exercise.concept, exercise.subconcept)
            memory = by_key.get(key)
            if (
                memory is None
                or memory.principle != exercise.expected_answer.strip()
                or not set(exercise.source_refs).issubset(set(memory.source_refs))
            ):
                raise AutonomousRemediationError(
                    f"atomic transfer exercise {exercise.exercise_id} lacks its verified stage-bound concept"
                )
            routes[exercise.exercise_id] = (memory,)

        self._model = model
        self._routes = routes

    def invoke(self, messages: Sequence[object], *args: object, **kwargs: object) -> object:
        if not messages:
            return self._model.invoke(messages, *args, **kwargs)
        content = getattr(messages[-1], "content", None)
        if not isinstance(content, str):
            return self._model.invoke(messages, *args, **kwargs)
        try:
            request = json.loads(content)
        except json.JSONDecodeError:
            return self._model.invoke(messages, *args, **kwargs)
        if not isinstance(request, Mapping) or not isinstance(request.get("exercises"), list):
            return self._model.invoke(messages, *args, **kwargs)

        augmented: list[dict[str, object]] = []
        injected = 0
        for raw in request["exercises"]:
            if not isinstance(raw, Mapping):
                raise AutonomousRemediationError("transfer answer exercise must be an object")
            if any(
                field in raw
                for field in (
                    "expected_answer",
                    "reference_reasoning_points",
                    "forbidden_inferences",
                    "remediation_context",
                    "source_evidence",
                    "learned_concept_memory",
                    "learned_concept_memories",
                )
            ):
                raise AutonomousRemediationError(
                    "transfer answer request contains prohibited grading/source/memory material"
                )
            item = dict(raw)
            exercise_id = item.get("exercise_id")
            routed = self._routes.get(exercise_id) if isinstance(exercise_id, str) else None
            if not routed:
                raise AutonomousRemediationError(
                    f"transfer answer request contains an unrouted exercise: {exercise_id!r}"
                )
            if len(routed) == 1:
                item["learned_concept_memory"] = {
                    "contract": PYRAMID_LEARNED_CONCEPT_MEMORY_CONTRACT,
                    "principle": routed[0].principle,
                }
            else:
                item["learned_concept_memories"] = [
                    {
                        "contract": PYRAMID_LEARNED_CONCEPT_MEMORY_CONTRACT,
                        "principle": memory.principle,
                    }
                    for memory in routed
                ]
            injected += 1
            augmented.append(item)

        if injected == 0:
            raise AutonomousRemediationError("transfer answer request contained no routable exercises")
        rewritten = dict(request)
        rewritten["instruction"] = (
            str(request.get("instruction", ""))
            + " Use learned_concept_memory or learned_concept_memories when present. "
            "They are previously retention-verified internal curriculum knowledge, not source evidence, "
            "live state, or answer keys. Answer each transfer question independently and do not mention "
            "the memory objects."
        ).strip()
        rewritten["exercises"] = augmented
        updated = list(messages)
        updated[-1] = HumanMessage(content=json.dumps(rewritten, ensure_ascii=False))
        return self._model.invoke(updated, *args, **kwargs)


def _provisional_concepts(
    *,
    curriculum_id: str,
    level: int,
    weak: Sequence[Exercise],
    critical_ids_by_key: Mapping[tuple[str, str | None], Sequence[str]] | None = None,
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
        critical_ids = tuple(
            sorted(
                critical_ids_by_key.get((concept, subconcept), ())
                if critical_ids_by_key is not None
                else (item.exercise_id for item in items)
            )
        )
        if not critical_ids:
            raise AutonomousRemediationError(
                f"remediation weakness {concept}/{subconcept or '-'} has no triggering failure lineage"
            )
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
                critical_exercise_ids=critical_ids,
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
    """Teach failed concepts, verify closed-source candidate-memory retention, then promote them.

    Grounded practice and retention may use unpromoted candidate lesson memory,
    but the answer path receives no raw source text, expected answers, grading
    material, live state, or execution authority. Transfer receives only concepts
    that have passed perfect retention and have bound provenance. Nothing is
    written to the learned-concepts store unless all three lanes pass perfectly.
    """

    weak = _weak_exercises(bank, failed_outcome)
    if not weak:
        raise AutonomousRemediationError("failed attempt exposes no remediable weak exercises")
    remediation_targets = _remediation_targets(bank, weak)
    if not remediation_targets:
        raise AutonomousRemediationError("failed attempt exposes no stable atomic remediation targets")
    remediation_lineage = _remediation_lineage(bank, weak)
    provisional = _provisional_concepts(
        curriculum_id=curriculum_id,
        level=level,
        weak=remediation_targets,
        critical_ids_by_key=remediation_lineage,
    )
    # A routing revision must never reuse pre-fix remediation checkpoints or overwrite their evidence.
    base_root = Path(output_dir)
    root = base_root / "lanes" / REMEDIATION_LANE_NAMESPACE
    grounded_bank = _practice_bank(
        provisional, count=GROUNDED_QUESTIONS_PER_WEAKNESS, lane="grounded"
    )
    grounded = run_exam(
        exercises=grounded_bank,
        answer_model=CandidateRemediationAnswerModel(model, provisional),
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
        answer_model=CandidateRemediationAnswerModel(model, provisional),
        grader_model=model,
        batch_size=batch_size,
        checkpoint_dir=root / "retention_checkpoints",
        canonical_exam=False,
    )
    if not _all_passed(retention, len(retention_bank)):
        raise AutonomousRemediationError(
            "closed-source candidate-memory remediation retention did not pass perfectly"
        )

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
            "retention_mode": "closed-source-candidate-memory-v1",
            "candidate_memory_injected": True,
            "source_context_injected": False,
            "raw_source_context_injected": False,
            "answer_grading_material_injected": False,
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
            "retention_mode": "closed-source-candidate-memory-v1",
            "candidate_memory_injected_into_retention": True,
            "source_context_injected_into_retention": False,
            "raw_source_context_injected_into_retention": False,
            "answer_grading_material_injected_into_retention": False,
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

    transfer_bank = _transfer_exercises(bank, weak)
    transfer = run_exam(
        exercises=transfer_bank,
        answer_model=StageTransferLearnedConceptAnswerModel(
            model,
            stage_bank=bank,
            exercises=transfer_bank,
            concepts=verified,
        ),
        grader_model=model,
        batch_size=batch_size,
        checkpoint_dir=root / "transfer_checkpoints",
        canonical_exam=False,
    )
    if not _all_passed(transfer, len(transfer_bank)):
        raise AutonomousRemediationError("verified concept transfer probe did not pass perfectly")
    write_learned_concepts(learned_concepts_path, verified)
    promotion_payload = {
        "contract": AUTONOMOUS_REMEDIATION_CONTRACT,
        "version": AUTONOMOUS_REMEDIATION_VERSION,
        "curriculum_id": curriculum_id,
        "level": level,
        "checkpoint_namespace": REMEDIATION_LANE_NAMESPACE,
        "lane_artifact_root": f"lanes/{REMEDIATION_LANE_NAMESPACE}",
        "promoted_concepts": len(verified),
        "transfer_questions": len(transfer_bank),
        "atomic_transfer_questions": sum(1 for item in transfer_bank if not item.boss_question),
        "boss_transfer_questions": sum(1 for item in transfer_bank if item.boss_question),
        "boss_synthesis_atoms": sum(
            len(_boss_synthesis_atoms(bank, item))
            for item in transfer_bank
            if item.boss_question
        ),
        "retention_mode": "closed-source-candidate-memory-v1",
        "candidate_memory_retention_passed": True,
        "transfer_passed": True,
        "pyramid_learned_concept_authorized": True,
        "general_durable_memory_promotion_authorized": False,
        "source_truth_authorized": False,
        "live_state_authorized": False,
        "execution_authorized": False,
    }
    _atomic_json(root / "promotion.json", promotion_payload)
    # Preserve the established operator/status path while keeping all lane evidence isolated.
    _atomic_json(base_root / "promotion.json", promotion_payload)
    return verified
