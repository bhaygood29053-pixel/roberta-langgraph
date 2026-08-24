from __future__ import annotations

from dataclasses import replace

import pytest

from roberta.learning.pyramid import (
    CANONICAL_INTEGRITY_QUESTION_COUNT,
    CANONICAL_LEVEL_QUESTION_COUNT,
    Exercise,
    derive_level_seed,
    evaluate_level,
    next_level_after,
    select_level_exercises,
)


def _exercise(index: int, level: int = 1) -> Exercise:
    return Exercise(
        exercise_id=f"book001-l{level:02d}-{index:05d}",
        curriculum_id="book001",
        level=level,
        concept="fundamentals",
        question=f"Question {index}?",
        expected_answer=f"Answer {index}",
        source_refs=("book001/chapter-1",),
        integrity_question=index % 5 == 0 and index != 0,
        boss_question=index == 0,
    )


def test_level_selection_is_reproducible_seeded_and_uses_300_question_contract() -> None:
    bank = tuple(_exercise(index) for index in range(1200))
    first = select_level_exercises(bank, curriculum_id="book001", level=1, run_seed="run-a")
    replay = select_level_exercises(bank, curriculum_id="book001", level=1, run_seed="run-a")
    different = select_level_exercises(bank, curriculum_id="book001", level=1, run_seed="run-b")

    assert CANONICAL_LEVEL_QUESTION_COUNT == 300
    assert CANONICAL_INTEGRITY_QUESTION_COUNT == 50
    assert len(first) == CANONICAL_LEVEL_QUESTION_COUNT
    assert sum(item.integrity_question for item in first) == CANONICAL_INTEGRITY_QUESTION_COUNT
    assert sum(item.boss_question for item in first) == 1
    assert sum(not item.integrity_question and not item.boss_question for item in first) == 249
    assert first[-1].boss_question is True
    assert [item.exercise_id for item in first] == [item.exercise_id for item in replay]
    assert [item.exercise_id for item in first] != [item.exercise_id for item in different]
    assert derive_level_seed("run-a", "book001", 1) == derive_level_seed("run-a", "book001", 1)


def test_canonical_selection_rejects_boss_integrity_overlap() -> None:
    bank = list(_exercise(index) for index in range(1200))
    bank[0] = replace(bank[0], integrity_question=True)

    with pytest.raises(ValueError, match="Boss Questions cannot also be integrity questions"):
        select_level_exercises(bank, curriculum_id="book001", level=1, run_seed="run-a")


def test_selection_fails_when_bank_is_too_small() -> None:
    bank = tuple(_exercise(index) for index in range(299))
    with pytest.raises(ValueError, match="needs at least 300"):
        select_level_exercises(bank, curriculum_id="book001", level=1, run_seed="run-a")


def test_progressive_thresholds_and_reset_semantics() -> None:
    level_one = evaluate_level(
        level=1,
        total_questions=300,
        correct_questions=255,
        integrity_total=50,
        integrity_correct=50,
        boss_passed=True,
    )
    assert level_one.passed is True
    assert next_level_after(level_one) == 2

    level_sixteen_fail = evaluate_level(
        level=16,
        total_questions=300,
        correct_questions=275,
        integrity_total=50,
        integrity_correct=50,
        boss_passed=True,
    )
    assert level_sixteen_fail.passed is False
    assert next_level_after(level_sixteen_fail) == 1


def test_integrity_boss_and_critical_failures_can_block_pass() -> None:
    low_integrity = evaluate_level(
        level=10,
        total_questions=300,
        correct_questions=297,
        integrity_total=50,
        integrity_correct=44,
        boss_passed=True,
    )
    assert low_integrity.passed is False

    boss_fail = evaluate_level(
        level=10,
        total_questions=300,
        correct_questions=297,
        integrity_total=50,
        integrity_correct=50,
        boss_passed=False,
    )
    assert boss_fail.passed is False

    critical_fail = evaluate_level(
        level=10,
        total_questions=300,
        correct_questions=297,
        integrity_total=50,
        integrity_correct=50,
        boss_passed=True,
        critical_failures=1,
    )
    assert critical_fail.passed is False


def test_grandmaster_requires_95_percent() -> None:
    fail = evaluate_level(
        level=20,
        total_questions=300,
        correct_questions=284,
        integrity_total=50,
        integrity_correct=50,
        boss_passed=True,
    )
    passed = evaluate_level(
        level=20,
        total_questions=300,
        correct_questions=285,
        integrity_total=50,
        integrity_correct=50,
        boss_passed=True,
    )
    assert fail.passed is False
    assert passed.passed is True
    assert next_level_after(passed) is None
