from __future__ import annotations

from dataclasses import replace
import json
from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage

from roberta.learning.autonomous_remediation import (
    AutonomousRemediationError,
    StageTransferLearnedConceptAnswerModel,
    _boss_synthesis_atoms,
    _remediation_targets,
    _transfer_exercises,
)
from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_learned_concepts import LearnedConcept


CURRICULUM_ID = "stage11-boss-transfer-fixture"
LEVEL = 11
SOURCE_KEY = "mb4e-stage11-source"


def _stage_bank() -> tuple[Exercise, ...]:
    atoms: list[Exercise] = []
    target_refs: list[str] = []
    required_points: list[str] = []
    principles: list[str] = []
    for index in range(1, 13):
        concept = f"stage11_concept_{index:02d}"
        subconcept = f"synthesis_atom_{index:02d}"
        principle = f"Verified Stage 11 synthesis principle {index:02d}."
        target_ref = f"stage11-target-{index:02d}"
        target_refs.append(target_ref)
        principles.append(principle)
        required_points.append(
            f"Correctly synthesize {concept}/{subconcept}: {principle}"
        )
        atoms.append(
            Exercise(
                exercise_id=f"STAGE11-ATOM-{index:02d}",
                curriculum_id=CURRICULUM_ID,
                level=LEVEL,
                concept=concept,
                subconcept=subconcept,
                question=f"Explain Stage 11 atom {index:02d}.",
                expected_answer=principle,
                source_refs=(SOURCE_KEY, target_ref),
                required_reasoning_points=(principle,),
                grading_rubric_id="STAGE11-TEST-V1",
            )
        )

    atoms.append(
        Exercise(
            exercise_id="STAGE11-BOSS",
            curriculum_id=CURRICULUM_ID,
            level=LEVEL,
            concept="source_synthesis",
            subconcept="boss_synthesis",
            question="Boss: synthesize the complete Stage 11 model.",
            expected_answer=" ".join(principles),
            source_refs=(SOURCE_KEY, *target_refs),
            question_type="boss",
            required_reasoning_points=tuple(required_points),
            grading_rubric_id="STAGE11-TEST-V1",
            boss_question=True,
        )
    )
    return tuple(atoms)


def _verified_concepts(bank: tuple[Exercise, ...]) -> tuple[LearnedConcept, ...]:
    concepts: list[LearnedConcept] = []
    for item in bank:
        if item.boss_question:
            continue
        concepts.append(
            LearnedConcept(
                curriculum_id=CURRICULUM_ID,
                level=LEVEL,
                concept=item.concept,
                subconcept=item.subconcept,
                principle=item.expected_answer,
                source_refs=item.source_refs,
                critical_exercise_ids=("STAGE11-BOSS",),
                retention_report_sha256="a" * 64,
                retention_manifest_sha256="b" * 64,
                checkpoint_sha256=(("stage11-attempt1.json", "c" * 64),),
                concept_hash="d" * 64,
            )
        )
    return tuple(concepts)


class CaptureModel:
    def __init__(self) -> None:
        self.payload: dict[str, object] | None = None

    def invoke(self, messages, *_args, **_kwargs):
        self.payload = json.loads(messages[-1].content)
        return SimpleNamespace(content="{}")


def _boss_request(boss: Exercise) -> HumanMessage:
    return HumanMessage(
        content=json.dumps(
            {
                "instruction": "Answer independently.",
                "exercises": [
                    {
                        "exercise_id": boss.exercise_id,
                        "question": boss.question,
                        "concept": boss.concept,
                        "subconcept": boss.subconcept,
                    }
                ],
            }
        )
    )


def test_failed_boss_expands_to_all_twelve_stage_bound_synthesis_atoms() -> None:
    bank = _stage_bank()
    boss = bank[-1]

    atoms = _boss_synthesis_atoms(bank, boss)
    targets = _remediation_targets(bank, (boss,))
    transfer = _transfer_exercises(bank, (boss,))

    assert len(atoms) == 12
    assert len(targets) == 12
    assert {item.exercise_id for item in targets} == {
        f"STAGE11-ATOM-{index:02d}" for index in range(1, 13)
    }
    assert len(transfer) == 13
    assert transfer[-1].exercise_id == boss.exercise_id
    assert transfer[-1].boss_question is True


def test_boss_transfer_receives_complete_verified_stage_synthesis_set() -> None:
    bank = _stage_bank()
    boss = bank[-1]
    concepts = _verified_concepts(bank)
    capture = CaptureModel()
    model = StageTransferLearnedConceptAnswerModel(
        capture,
        stage_bank=bank,
        exercises=(boss,),
        concepts=concepts,
    )

    model.invoke([_boss_request(boss)])

    assert capture.payload is not None
    routed = capture.payload["exercises"][0]["learned_concept_memories"]
    assert len(routed) == 12
    assert [item["principle"] for item in routed] == [
        concept.principle for concept in concepts
    ]


def test_boss_transfer_fails_closed_on_incomplete_verified_subset() -> None:
    bank = _stage_bank()
    boss = bank[-1]
    incomplete = _verified_concepts(bank)[:-1]

    with pytest.raises(
        AutonomousRemediationError,
        match="complete stage-bound verified synthesis set",
    ):
        StageTransferLearnedConceptAnswerModel(
            CaptureModel(),
            stage_bank=bank,
            exercises=(boss,),
            concepts=incomplete,
        )



def test_boss_transfer_requires_target_specific_source_binding_not_common_root_only() -> None:
    bank = _stage_bank()
    boss = bank[-1]
    verified = _verified_concepts(bank)
    root_only = (
        replace(verified[0], source_refs=(SOURCE_KEY,)),
        *verified[1:],
    )

    with pytest.raises(
        AutonomousRemediationError,
        match="complete stage-bound verified synthesis set",
    ):
        StageTransferLearnedConceptAnswerModel(
            CaptureModel(),
            stage_bank=bank,
            exercises=(boss,),
            concepts=root_only,
        )

def test_transfer_rejects_concepts_without_retention_and_checkpoint_provenance() -> None:
    bank = _stage_bank()
    boss = bank[-1]
    verified = _verified_concepts(bank)

    no_retention = (
        replace(verified[0], retention_report_sha256="0" * 64),
        *verified[1:],
    )
    with pytest.raises(
        AutonomousRemediationError,
        match="retention-report provenance",
    ):
        StageTransferLearnedConceptAnswerModel(
            CaptureModel(),
            stage_bank=bank,
            exercises=(boss,),
            concepts=no_retention,
        )

    no_checkpoint = (
        replace(
            verified[0],
            checkpoint_sha256=(("pending", "0" * 64),),
        ),
        *verified[1:],
    )
    with pytest.raises(
        AutonomousRemediationError,
        match="checkpoint provenance",
    ):
        StageTransferLearnedConceptAnswerModel(
            CaptureModel(),
            stage_bank=bank,
            exercises=(boss,),
            concepts=no_checkpoint,
        )
