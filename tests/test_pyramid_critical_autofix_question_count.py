from __future__ import annotations

from pathlib import Path

from roberta.learning.pyramid import Exercise, evaluate_level
from roberta.learning.pyramid_critical_autofix_cli import (
    _failed_run,
    _reconstruct_failed_exam,
    _resolve_checkpoint_dir,
)
from roberta.learning.training_ledger import PyramidTrainingLedger


CURRICULUM = "autofix-q300-fixture"
SEED = "failed-q300-seed"


def _bank() -> tuple[Exercise, ...]:
    ordinary = tuple(
        Exercise(
            exercise_id=f"Q300-ORD-{index:03d}",
            curriculum_id=CURRICULUM,
            level=1,
            concept="fundamentals",
            question=f"Ordinary question {index}?",
            expected_answer=f"Ordinary answer {index}",
            source_refs=("fixture/source",),
        )
        for index in range(249)
    )
    integrity = tuple(
        Exercise(
            exercise_id=f"Q300-INT-{index:03d}",
            curriculum_id=CURRICULUM,
            level=1,
            concept="integrity",
            question=f"Integrity question {index}?",
            expected_answer=f"Integrity answer {index}",
            source_refs=("fixture/source",),
            integrity_question=True,
        )
        for index in range(50)
    )
    boss = Exercise(
        exercise_id="Q300-BOSS-001",
        curriculum_id=CURRICULUM,
        level=1,
        concept="synthesis",
        question="Boss question?",
        expected_answer="Boss answer",
        source_refs=("fixture/source",),
        boss_question=True,
    )
    return ordinary + integrity + (boss,)


def test_failed_run_reads_recorded_300_question_count_from_ledger(tmp_path: Path) -> None:
    ledger_path = tmp_path / "pyramid.sqlite3"
    ledger = PyramidTrainingLedger(ledger_path)
    run_id = ledger.start_run(CURRICULUM, SEED)
    result = evaluate_level(
        level=1,
        total_questions=300,
        correct_questions=299,
        integrity_total=50,
        integrity_correct=50,
        boss_passed=True,
        critical_failures=1,
    )
    assert result.passed is False
    ledger.record_level_result(run_id, result)

    failed = _failed_run(
        ledger_path=ledger_path,
        curriculum_id=CURRICULUM,
        level=1,
        seed=SEED,
    )

    assert failed["question_count"] == 300
    assert failed["run_seed"] == SEED
    assert failed["critical_failures"] == 1


def test_checkpoint_discovery_prefers_q300_namespace_over_legacy_seed_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    seed_root = Path(".roberta/pyramid_checkpoints_v3") / CURRICULUM / SEED
    q300 = seed_root / "q300"
    q300.mkdir(parents=True)
    (q300 / "level_01_batch_0001.json").write_text("{}", encoding="utf-8")
    (seed_root / "level_01_batch_0001.json").write_text("{}", encoding="utf-8")

    discovered = _resolve_checkpoint_dir(
        supplied=None,
        curriculum_id=CURRICULUM,
        seed=SEED,
        question_count=300,
    )
    supplied_root = _resolve_checkpoint_dir(
        supplied=str(Path(".roberta/pyramid_checkpoints_v3")),
        curriculum_id=CURRICULUM,
        seed=SEED,
        question_count=300,
    )

    assert discovered == q300
    assert supplied_root == q300


def test_autofix_reconstructs_new_canonical_exam_from_300_question_minimum_bank() -> None:
    selected = _reconstruct_failed_exam(
        _bank(),
        curriculum_id=CURRICULUM,
        seed=SEED,
        question_count=300,
    )

    assert len(selected) == 300
    assert sum(item.integrity_question for item in selected) == 50
    assert sum(item.boss_question for item in selected) == 1
    assert sum(not item.integrity_question and not item.boss_question for item in selected) == 249
    assert selected[-1].boss_question is True
