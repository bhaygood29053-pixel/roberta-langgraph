from __future__ import annotations

from pathlib import Path

from roberta.learning.pyramid import (
    CANONICAL_INTEGRITY_QUESTION_COUNT,
    CANONICAL_LEVEL_QUESTION_COUNT,
    LEGACY_CANONICAL_LEVEL_QUESTION_COUNT,
    Exercise,
    select_level_exercises,
)
from roberta.learning.pyramid_run_cli import _checkpoint_run_dir


CURRICULUM = "migration-curriculum"


def _bank() -> tuple[Exercise, ...]:
    exercises: list[Exercise] = []
    for index in range(1155):
        exercises.append(
            Exercise(
                exercise_id=f"ordinary-{index:04d}",
                curriculum_id=CURRICULUM,
                level=2,
                concept="mechanics",
                question=f"Ordinary {index}?",
                expected_answer="answer",
                source_refs=("source",),
            )
        )
    for index in range(50):
        exercises.append(
            Exercise(
                exercise_id=f"integrity-{index:02d}",
                curriculum_id=CURRICULUM,
                level=2,
                concept="mechanics",
                question=f"Integrity {index}?",
                expected_answer="answer",
                source_refs=("source",),
                integrity_question=True,
            )
        )
    exercises.append(
        Exercise(
            exercise_id="boss",
            curriculum_id=CURRICULUM,
            level=2,
            concept="mechanics",
            question="Boss?",
            expected_answer="answer",
            source_refs=("source",),
            boss_question=True,
        )
    )
    return tuple(exercises)


def test_new_default_canonical_selection_is_300_with_disjoint_categories() -> None:
    selected = select_level_exercises(
        _bank(), curriculum_id=CURRICULUM, level=2, run_seed="same-seed"
    )

    assert CANONICAL_LEVEL_QUESTION_COUNT == 300
    assert len(selected) == 300
    assert sum(item.integrity_question for item in selected) == 50
    assert sum(item.boss_question for item in selected) == 1
    assert sum(not item.integrity_question and not item.boss_question for item in selected) == 249
    assert selected[-1].boss_question


def test_legacy_1000_selection_remains_canonical_for_historical_reconstruction() -> None:
    selected = select_level_exercises(
        _bank(),
        curriculum_id=CURRICULUM,
        level=2,
        run_seed="same-seed",
        count=LEGACY_CANONICAL_LEVEL_QUESTION_COUNT,
    )

    assert LEGACY_CANONICAL_LEVEL_QUESTION_COUNT == 1000
    assert len(selected) == 1000
    assert sum(item.integrity_question for item in selected) == CANONICAL_INTEGRITY_QUESTION_COUNT == 50
    assert sum(item.boss_question for item in selected) == 1
    assert sum(not item.integrity_question and not item.boss_question for item in selected) == 949
    assert selected[-1].boss_question


def test_new_checkpoint_namespace_cannot_collide_with_legacy_seed_root() -> None:
    root = Path(".roberta/pyramid_checkpoints")
    legacy = root / CURRICULUM / "seed-1"
    current = _checkpoint_run_dir(
        root,
        curriculum_id=CURRICULUM,
        seed="seed-1",
        question_count=300,
    )

    assert current == legacy / "q300"
    assert current != legacy
