from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from roberta.learning.pyramid import Exercise
from roberta.learning.pyramid_critical_retention import (
    CRITICAL_RETENTION_CONTRACT,
    CRITICAL_RETENTION_VERSION,
)
from roberta.learning.pyramid_learned_concept_answer import PyramidLearnedConceptAnswerModel
from roberta.learning.pyramid_learned_concepts import (
    LearnedConcept,
    PYRAMID_LEARNED_CONCEPT_MEMORY_CONTRACT,
    PyramidLearnedConceptError,
    _canonical_hash,
    _concept_material,
    build_promoted_concepts,
    load_learned_concepts,
    write_learned_concepts,
)
from roberta.learning.pyramid_practice import TARGETED_PRACTICE_CONTRACT, TARGETED_PRACTICE_VERSION
from roberta.learning.pyramid_run_cli import _load_learned_memory


CURRICULUM_ID = "learned-concept-fixture"
PRINCIPLE = (
    "Blockchain immutability is practical rather than absolute: accepted history is extremely "
    "difficult to alter, but alteration is not conceptually impossible."
)


def _learned(*, principle: str = PRINCIPLE, concept: str = "benefits", subconcept: str | None = "immutability") -> LearnedConcept:
    source_refs = ("fixture-source",)
    material = _concept_material(
        curriculum_id=CURRICULUM_ID,
        level=1,
        concept=concept,
        subconcept=subconcept,
        principle=principle,
        source_refs=source_refs,
    )
    return LearnedConcept(
        curriculum_id=CURRICULUM_ID,
        level=1,
        concept=concept,
        subconcept=subconcept,
        principle=principle,
        source_refs=source_refs,
        critical_exercise_ids=("q-critical",),
        retention_report_sha256="a" * 64,
        retention_manifest_sha256="b" * 64,
        checkpoint_sha256=(("checkpoint.json", "c" * 64),),
        concept_hash=_canonical_hash(material),
    )


def _retention_files(tmp_path: Path, *, concept: str = "benefits", subconcept: str | None = "immutability") -> tuple[Path, Path]:
    report = {
        "contract": TARGETED_PRACTICE_CONTRACT,
        "version": TARGETED_PRACTICE_VERSION,
        "curriculum_id": CURRICULUM_ID,
        "level": 1,
        "question_count": 10,
        "pass_count": 10,
        "partial_count": 0,
        "fail_count": 0,
        "critical_failures": 0,
        "all_weaknesses_passed": True,
        "critical_weaknesses_passed": True,
        "practice_passed": True,
        "canonical_attempt_authorized": True,
        "weakness_results": [
            {
                "concept": concept,
                "subconcept": subconcept,
                "total": 10,
                "pass_count": 10,
                "partial_count": 0,
                "fail_count": 0,
                "critical_failures": 0,
                "critical_origin": True,
                "passed": True,
            }
        ],
    }
    manifest = {
        "contract": CRITICAL_RETENTION_CONTRACT,
        "version": CRITICAL_RETENTION_VERSION,
        "curriculum_id": CURRICULUM_ID,
        "level": 1,
        "closed_book": True,
        "source_context_injected": False,
        "canonical_exam": False,
        "ledger_mutation_authorized": False,
        "grounded_prerequisite": {"grounded_practice_passed": True},
    }
    report_path = tmp_path / "practice_report.json"
    manifest_path = tmp_path / "critical_retention_manifest.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return report_path, manifest_path


def test_answer_adapter_injects_only_matching_learned_concept_without_source_or_grading_material() -> None:
    class CaptureModel:
        def __init__(self) -> None:
            self.messages = None

        def invoke(self, messages, *args, **kwargs):
            self.messages = messages
            return SimpleNamespace(content='{"answers":[]}')

    base = CaptureModel()
    adapter = PyramidLearnedConceptAnswerModel(base, (_learned(),))
    request = {
        "instruction": "Answer every exercise independently.",
        "schema": {"answers": [{"exercise_id": "string", "answer": "string"}]},
        "exercises": [
            {
                "exercise_id": "q1",
                "question": "What does immutability mean?",
                "concept": "benefits",
                "subconcept": "immutability",
            },
            {
                "exercise_id": "q2",
                "question": "What is a network layer?",
                "concept": "architecture",
                "subconcept": "network_layer",
            },
        ],
    }
    original = [SystemMessage(content="closed-book"), HumanMessage(content=json.dumps(request))]
    adapter.invoke(original)

    assert base.messages is not None
    payload = json.loads(getattr(base.messages[-1], "content"))
    first = payload["exercises"][0]
    second = payload["exercises"][1]
    assert first["learned_concept_memory"] == {
        "contract": PYRAMID_LEARNED_CONCEPT_MEMORY_CONTRACT,
        "principle": PRINCIPLE,
    }
    assert "learned_concept_memory" not in second
    serialized = json.dumps(payload, sort_keys=True)
    assert "expected_answer" not in serialized
    assert "reference_reasoning_points" not in serialized
    assert "forbidden_inferences" not in serialized
    assert "remediation_context" not in serialized
    assert "source_evidence" not in serialized
    assert "fixture-source" not in serialized


def test_answer_adapter_passes_grader_request_through_unchanged() -> None:
    class IdentityModel:
        def __init__(self) -> None:
            self.messages = None

        def invoke(self, messages, *args, **kwargs):
            self.messages = messages
            return SimpleNamespace(content="{}")

    base = IdentityModel()
    adapter = PyramidLearnedConceptAnswerModel(base, (_learned(),))
    messages = [
        SystemMessage(content="grader"),
        HumanMessage(
            content=json.dumps(
                {
                    "items": [
                        {
                            "exercise_id": "q1",
                            "expected_answer": "grader-only",
                            "roberta_answer": "answer",
                        }
                    ]
                }
            )
        ),
    ]
    adapter.invoke(messages)
    assert base.messages is messages


def test_answer_adapter_requires_one_curriculum_level_scope() -> None:
    other = _learned(concept="architecture", subconcept="network_layer")
    other = LearnedConcept(
        curriculum_id="other-curriculum",
        level=1,
        concept=other.concept,
        subconcept=other.subconcept,
        principle=other.principle,
        source_refs=other.source_refs,
        critical_exercise_ids=other.critical_exercise_ids,
        retention_report_sha256=other.retention_report_sha256,
        retention_manifest_sha256=other.retention_manifest_sha256,
        checkpoint_sha256=other.checkpoint_sha256,
        concept_hash=other.concept_hash,
    )
    with pytest.raises(PyramidLearnedConceptError, match="one curriculum/level scope"):
        PyramidLearnedConceptAnswerModel(SimpleNamespace(invoke=lambda _: None), (_learned(), other))


def test_store_roundtrip_is_content_addressed_and_conflicts_fail_closed(tmp_path: Path) -> None:
    path = tmp_path / "learned.json"
    first = _learned()
    written = write_learned_concepts(path, (first,))
    assert written == (first,)
    loaded = load_learned_concepts(path, curriculum_id=CURRICULUM_ID, level=1)
    assert loaded == (first,)

    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["concepts"][0]["principle"] = "tampered"
    path.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(PyramidLearnedConceptError, match="hash does not match"):
        load_learned_concepts(path)

    path.unlink()
    write_learned_concepts(path, (first,))
    conflicting = _learned(principle="A different principle.")
    with pytest.raises(PyramidLearnedConceptError, match="conflicting learned concept"):
        write_learned_concepts(path, (conflicting,))


def test_promotion_requires_matching_perfect_source_free_closed_book_retention(monkeypatch, tmp_path: Path) -> None:
    exercise = Exercise(
        exercise_id="q-critical",
        curriculum_id=CURRICULUM_ID,
        level=1,
        concept="benefits",
        subconcept="immutability",
        question="What is immutability?",
        expected_answer=PRINCIPLE,
        source_refs=("fixture-source",),
        required_reasoning_points=(PRINCIPLE,),
        forbidden_inferences=("Do not claim absolute immutability.",),
        grading_rubric_id="MB4E-L1-RUBRIC-V1",
    )
    monkeypatch.setattr(
        "roberta.learning.pyramid_learned_concepts.validate_package",
        lambda _: (
            {"curriculum_id": CURRICULUM_ID, "approved_source_refs": ["fixture-source"]},
            (exercise,),
        ),
    )
    monkeypatch.setattr(
        "roberta.learning.pyramid_learned_concepts.load_weak_items",
        lambda *args, **kwargs: (SimpleNamespace(exercise_id="q-critical"),),
    )
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    (checkpoint_dir / "level_01_batch_0001.json").write_text("{}", encoding="utf-8")

    report_path, manifest_path = _retention_files(tmp_path)
    promoted = build_promoted_concepts(
        curriculum_dir="fixture",
        critical_checkpoint_dir=checkpoint_dir,
        retention_report_path=report_path,
        retention_manifest_path=manifest_path,
    )
    assert len(promoted) == 1
    assert promoted[0].principle == PRINCIPLE
    assert promoted[0].source_refs == ("fixture-source",)
    assert promoted[0].critical_exercise_ids == ("q-critical",)

    mismatch_report, mismatch_manifest = _retention_files(
        tmp_path,
        concept="architecture",
        subconcept="network_layer",
    )
    with pytest.raises(PyramidLearnedConceptError, match="lack matching perfect closed-book retention"):
        build_promoted_concepts(
            curriculum_dir="fixture",
            critical_checkpoint_dir=checkpoint_dir,
            retention_report_path=mismatch_report,
            retention_manifest_path=mismatch_manifest,
        )


def test_pyramid_run_auto_loads_only_matching_curriculum_level(tmp_path: Path) -> None:
    path = tmp_path / "learned.json"
    write_learned_concepts(path, (_learned(),))
    resolved, learned = _load_learned_memory(
        supplied_path=str(path),
        disabled=False,
        curriculum_id=CURRICULUM_ID,
        level=1,
    )
    assert resolved == path
    assert len(learned) == 1

    _, none_for_level_two = _load_learned_memory(
        supplied_path=str(path),
        disabled=False,
        curriculum_id=CURRICULUM_ID,
        level=2,
    )
    assert none_for_level_two == ()


def test_autofix_entry_installs_scoped_adapter() -> None:
    from roberta.learning import pyramid_critical_autofix_entry  # noqa: F401
    from roberta.learning import pyramid_learned_concepts

    assert pyramid_learned_concepts.PyramidLearnedConceptAnswerModel is PyramidLearnedConceptAnswerModel
