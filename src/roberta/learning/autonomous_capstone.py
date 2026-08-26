from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from langchain_core.messages import HumanMessage

from .curriculum_io import validate_package
from .pyramid import Exercise, MIN_INTEGRITY_ACCURACY, get_level_spec
from .pyramid_exam import ExamOutcome, run_exam
from .pyramid_learned_concepts import LearnedConcept, PyramidLearnedConceptError
from .source_mastery import SourceMasteryPlan


CAPSTONE_CONTRACT = "roberta-source-capstone/v1"
CAPSTONE_VERSION = "1.0.0"
CAPSTONE_QUESTION_COUNT = 60
CAPSTONE_INTEGRITY_COUNT = 10
CAPSTONE_REQUIRED_ACCURACY = 0.90


class AutonomousCapstoneError(RuntimeError):
    pass


class SourceCapstoneLearnedConceptAnswerModel:
    """Route verified stage memories into the capstone exercises they support."""

    def __init__(
        self,
        model: Any,
        *,
        plan: SourceMasteryPlan,
        exercises: Sequence[Exercise],
        concepts: Sequence[LearnedConcept],
    ) -> None:
        if any(item.curriculum_id != plan.curriculum_id for item in concepts):
            raise PyramidLearnedConceptError("capstone learned concepts do not match curriculum")
        allowed_levels = set(plan.required_capability_levels)
        if any(item.level not in allowed_levels for item in concepts):
            raise PyramidLearnedConceptError("capstone learned concept level is outside the source plan")
        self._model = model
        all_concepts = tuple(concepts)
        routes: dict[str, tuple[LearnedConcept, ...]] = {}
        for exercise in exercises:
            if exercise.boss_question:
                matched = all_concepts
            else:
                exercise_refs = set(exercise.source_refs)
                matched = tuple(
                    item
                    for item in all_concepts
                    if (set(item.source_refs) - {plan.source_key}) & exercise_refs
                )
            if matched:
                routes[exercise.exercise_id] = matched
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
                raise PyramidLearnedConceptError("capstone answer exercise must be an object")
            if any(
                field in raw
                for field in (
                    "expected_answer",
                    "reference_reasoning_points",
                    "forbidden_inferences",
                    "remediation_context",
                    "source_evidence",
                )
            ):
                raise PyramidLearnedConceptError(
                    "capstone answer request contains prohibited grading/source material"
                )
            item = dict(raw)
            exercise_id = item.get("exercise_id")
            routed = self._routes.get(exercise_id) if isinstance(exercise_id, str) else None
            if routed:
                item["learned_concept_memories"] = [
                    {
                        "contract": "roberta-source-capstone-learned-memory/v1",
                        "principle": memory.principle,
                    }
                    for memory in routed
                ]
                injected += 1
            augmented.append(item)
        if injected == 0:
            return self._model.invoke(messages, *args, **kwargs)
        rewritten = dict(request)
        rewritten["instruction"] = (
            str(request.get("instruction", ""))
            + " Use learned_concept_memories when present. They are previously verified internal curriculum knowledge, not source evidence, live state, or answer keys. Answer the synthesis independently and do not mention the memory objects."
        ).strip()
        rewritten["exercises"] = augmented
        updated = list(messages)
        updated[-1] = HumanMessage(content=json.dumps(rewritten, ensure_ascii=False))
        return self._model.invoke(updated, *args, **kwargs)


@dataclass(frozen=True, slots=True)
class CapstoneResult:
    question_count: int
    accuracy: float
    integrity_accuracy: float
    boss_passed: bool
    critical_failures: int
    passed: bool

    def to_mapping(self) -> dict[str, object]:
        return {"contract": CAPSTONE_CONTRACT, "version": CAPSTONE_VERSION, **asdict(self)}


def build_source_capstone(
    *,
    curriculum_dir: str | Path,
    plan: SourceMasteryPlan,
) -> tuple[Exercise, ...]:
    manifest, bank = validate_package(curriculum_dir)
    if str(manifest["curriculum_id"]) != plan.curriculum_id:
        raise AutonomousCapstoneError("capstone plan does not match curriculum")
    by_level: dict[int, list[Exercise]] = {}
    required_levels = set(plan.required_capability_levels)
    for item in bank:
        if item.level in required_levels:
            by_level.setdefault(item.level, []).append(item)
    missing = [stage.capability_level for stage in plan.stages if stage.capability_level not in by_level]
    if missing:
        raise AutonomousCapstoneError(f"capstone cannot cover missing source-stage banks: {missing}")

    # Capstone construction reuses only already validated expected answers and
    # source references. It introduces no new source claim or live-state premise.
    representatives: list[Exercise] = []
    for stage in plan.stages:
        pool = by_level[stage.capability_level]
        ordinary = [item for item in pool if not item.integrity_question and not item.boss_question]
        bosses = [item for item in pool if item.boss_question]
        representatives.extend(ordinary[: max(2, 40 // max(1, len(plan.stages)))])
        if bosses:
            representatives.append(bosses[0])
    if len(representatives) < 10:
        raise AutonomousCapstoneError("not enough validated source-stage material for a capstone")

    highest = max(stage.capability_level for stage in plan.stages)
    source_refs = tuple(dict.fromkeys(ref for item in representatives for ref in item.source_refs))
    exercises: list[Exercise] = []
    ordinary_count = CAPSTONE_QUESTION_COUNT - CAPSTONE_INTEGRITY_COUNT - 1
    for index in range(ordinary_count):
        left = representatives[index % len(representatives)]
        right = representatives[(index * 7 + 3) % len(representatives)]
        if right.exercise_id == left.exercise_id:
            right = representatives[(index + 1) % len(representatives)]
        exercises.append(
            Exercise(
                exercise_id=f"CAP-{plan.plan_hash[:10]}-{index + 1:04d}",
                curriculum_id=plan.curriculum_id,
                level=highest,
                concept="source_capstone",
                subconcept=f"synthesis_{index + 1}",
                question=(
                    f"Source capstone: Explain how the source-grounded ideas represented by '{left.concept}/{left.subconcept or '-'}' and "
                    f"'{right.concept}/{right.subconcept or '-'}' relate or differ. Preserve both concepts' important boundaries and do not add live-state claims."
                ),
                expected_answer=f"{left.expected_answer} {right.expected_answer}",
                source_refs=tuple(dict.fromkeys((*left.source_refs, *right.source_refs))),
                question_type="capstone_synthesis",
                difficulty=min(20, highest + 2),
                required_reasoning_points=(
                    f"Correctly preserve {left.concept}: {left.expected_answer}",
                    f"Correctly preserve {right.concept}: {right.expected_answer}",
                    "Relate or distinguish the two without inventing unsupported source claims.",
                ),
                forbidden_inferences=(
                    "Do not invent current prices, chain state, tool results, transactions, or evidence absent from the static source.",
                ),
                grading_rubric_id="SOURCE-CAPSTONE-V1",
            )
        )
    for index in range(CAPSTONE_INTEGRITY_COUNT):
        item = representatives[(index * 5) % len(representatives)]
        exercises.append(
            Exercise(
                exercise_id=f"CAP-{plan.plan_hash[:10]}-I{index + 1:03d}",
                curriculum_id=plan.curriculum_id,
                level=highest,
                concept="source_capstone_integrity",
                subconcept=item.concept,
                question=(
                    f"Capstone integrity check: State the supported rule for {item.concept}/{item.subconcept or '-'} and explicitly reject one unsupported inference that would go beyond the selected source."
                ),
                expected_answer=item.expected_answer,
                source_refs=item.source_refs,
                question_type="integrity",
                difficulty=min(20, highest + 2),
                required_reasoning_points=(item.expected_answer, "Reject unsupported expansion beyond the static source."),
                forbidden_inferences=(
                    "Do not fabricate source evidence or promote static source material into current live truth.",
                ),
                grading_rubric_id="SOURCE-CAPSTONE-V1",
                integrity_question=True,
            )
        )
    exercises.append(
        Exercise(
            exercise_id=f"CAP-{plan.plan_hash[:10]}-BOSS",
            curriculum_id=plan.curriculum_id,
            level=highest,
            concept="source_capstone",
            subconcept="final_boss",
            question=(
                f"Final source Boss: Build a coherent mastery model of '{plan.source_title}' across all {plan.required_stage_count} required source stages. "
                "Explain the major capability boundaries, connect related mechanisms, preserve important limitations, and distinguish static source knowledge from facts that would require fresh external evidence."
            ),
            expected_answer=" ".join(item.expected_answer for item in representatives[: min(20, len(representatives))]),
            source_refs=source_refs,
            question_type="boss",
            difficulty=min(20, highest + 3),
            required_reasoning_points=tuple(
                f"Include a correct source-grounded contribution from {stage.capability_name}." for stage in plan.stages
            ),
            forbidden_inferences=(
                "Do not invent live state, current market values, unobserved transactions, tool results, or source passages.",
                "Do not claim the source supports a global capability excluded by its frozen source-mastery plan.",
            ),
            grading_rubric_id="SOURCE-CAPSTONE-V1",
            boss_question=True,
        )
    )
    return tuple(exercises)


def run_source_capstone(
    *,
    curriculum_dir: str | Path,
    plan: SourceMasteryPlan,
    answer_model: Any,
    grader_model: Any,
    checkpoint_dir: str | Path,
    learned_concepts: Sequence[LearnedConcept] = (),
    batch_size: int = 10,
    progress=None,
) -> tuple[CapstoneResult, ExamOutcome]:
    exercises = build_source_capstone(curriculum_dir=curriculum_dir, plan=plan)
    if learned_concepts:
        answer_model = SourceCapstoneLearnedConceptAnswerModel(
            answer_model,
            plan=plan,
            exercises=exercises,
            concepts=learned_concepts,
        )
    outcome = run_exam(
        exercises=exercises,
        answer_model=answer_model,
        grader_model=grader_model,
        batch_size=batch_size,
        checkpoint_dir=checkpoint_dir,
        progress=progress,
        canonical_exam=False,
    )
    level = outcome.level_result
    passed = (
        level.accuracy >= max(CAPSTONE_REQUIRED_ACCURACY, get_level_spec(level.level).pass_accuracy)
        and level.integrity_accuracy >= MIN_INTEGRITY_ACCURACY
        and level.boss_passed
        and level.critical_failures == 0
    )
    return (
        CapstoneResult(
            question_count=level.total_questions,
            accuracy=level.accuracy,
            integrity_accuracy=level.integrity_accuracy,
            boss_passed=level.boss_passed,
            critical_failures=level.critical_failures,
            passed=passed,
        ),
        outcome,
    )
