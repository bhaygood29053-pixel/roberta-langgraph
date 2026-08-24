from __future__ import annotations

import json
from pathlib import Path

import pytest

from roberta.learning.curriculum_io import CurriculumPackageError, validate_package
from roberta.learning.pyramid import PYRAMID_CONTRACT
from roberta.learning.pyramid_provenance_migration import (
    MB4E_SOURCE_KEY,
    PyramidProvenanceMigrationError,
    migrate_legacy_mb4e_curriculum,
)


LEGACY_CURRICULUM_ID = "mastering_blockchain_4e_2023_book01"
REF_A = "MB4E-CH1-P34-37-GROWTH"
REF_B = "MB4E-CH1-P37-41-DISTRIBUTED"


def _manifest() -> dict[str, object]:
    return {
        "manifest_contract": "roberta-pyramid-manifest/v1",
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": LEGACY_CURRICULUM_ID,
        "title": "Legacy Mastering Blockchain Level 1 fixture",
        "source_type": "user_provided_book_derived_curriculum",
        "approved_source_refs": [REF_A, REF_B],
        "levels": [1],
    }


def _exercise(exercise_id: str, source_ref: str, question: str) -> dict[str, object]:
    return {
        "exercise_id": exercise_id,
        "curriculum_id": LEGACY_CURRICULUM_ID,
        "level": 1,
        "concept": "distributed_systems",
        "subconcept": "fixture",
        "question": question,
        "expected_answer": "A concise fixture answer.",
        "source_refs": [source_ref],
        "question_type": "reasoning",
        "difficulty": 2,
        "required_reasoning_points": ["fixture point"],
        "forbidden_inferences": ["do not invent source facts"],
        "grading_rubric_id": "pyramid-question-first-v1",
        "integrity_question": False,
        "boss_question": False,
        "requires_live_data": False,
    }


def _write_legacy_package(tmp_path: Path) -> Path:
    root = tmp_path / "legacy"
    root.mkdir()
    (root / "manifest.json").write_text(json.dumps(_manifest()), encoding="utf-8")
    rows = [
        _exercise("MB4E-L01-00001", REF_A, "What changed as blockchain matured?"),
        _exercise("MB4E-L01-00002", REF_B, "Why do distributed systems need fault tolerance?"),
    ]
    (root / "exercises.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )
    (root / "source_map.json").write_text(
        json.dumps(
            {
                REF_A: "PDF pages 34-37: growth/maturity and high-level challenges",
                REF_B: "PDF pages 37-41: distributed systems, Byzantine behavior, CAP, PACELC",
            }
        ),
        encoding="utf-8",
    )
    (root / "README.md").write_text("legacy support file\n", encoding="utf-8")
    return root


def _raw_rows(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_migration_preserves_historical_semantics_and_explicit_pdf_page_basis(tmp_path: Path) -> None:
    legacy = _write_legacy_package(tmp_path)
    original = _raw_rows(legacy / "exercises.jsonl")
    output = tmp_path / "migrated"

    report = migrate_legacy_mb4e_curriculum(curriculum_dir=legacy, output_dir=output)

    assert report.exercise_count_before == 2
    assert report.exercise_count_after == 2
    assert report.provenance_count == 2
    assert report.exercise_ids_identical is True
    assert report.question_text_identical is True
    assert report.semantic_fields_identical is True
    assert (output / "README.md").read_text(encoding="utf-8") == "legacy support file\n"
    assert json.loads((output / "migration_report.json").read_text(encoding="utf-8")) == report.to_mapping()

    manifest, exercises = validate_package(output)
    assert manifest["curriculum_id"] == LEGACY_CURRICULUM_ID
    assert manifest["source_provenance"]["source_key"] == MB4E_SOURCE_KEY
    assert "PDF page" in manifest["source_provenance"]["location_scheme"]
    assert len(exercises) == 2

    migrated = _raw_rows(output / "exercises.jsonl")
    assert [row["exercise_id"] for row in migrated] == [row["exercise_id"] for row in original]
    assert [row["question"] for row in migrated] == [row["question"] for row in original]
    for before, after in zip(original, migrated, strict=True):
        before_semantics = {key: value for key, value in before.items() if key != "source_refs"}
        after_semantics = {key: value for key, value in after.items() if key != "source_refs"}
        assert before_semantics == after_semantics
        assert after["source_refs"][:-1] == before["source_refs"]
        assert after["source_refs"][-1] == MB4E_SOURCE_KEY

    provenance = _raw_rows(output / "provenance.jsonl")
    assert len(provenance) == 2
    assert {row["exercise_id"] for row in provenance} == {row["exercise_id"] for row in original}
    first = provenance[0]
    assert first["supports"] == ["question", "expected_answer", "required_reasoning_points"]
    location = first["locations"][0]
    assert location["legacy_source_ref"] == REF_A
    assert location["pdf_pages"] == [34, 35, 36, 37]
    assert "book_pages" not in location


def test_migration_verifies_existing_checkpoint_exercise_ids_without_mutating_checkpoints(tmp_path: Path) -> None:
    legacy = _write_legacy_package(tmp_path)
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    checkpoint = checkpoints / "level_01_batch_0001.json"
    checkpoint.write_text(
        json.dumps({"exercise_ids": ["MB4E-L01-00001", "MB4E-L01-00002"], "grades": []}),
        encoding="utf-8",
    )
    before = checkpoint.read_bytes()

    report = migrate_legacy_mb4e_curriculum(
        curriculum_dir=legacy,
        output_dir=tmp_path / "migrated",
        checkpoints_dir=checkpoints,
    )

    assert report.checkpoint_compatible is True
    assert report.checkpoint_exercise_count == 2
    assert checkpoint.read_bytes() == before


def test_migration_rejects_pdf_range_disagreement_instead_of_guessing(tmp_path: Path) -> None:
    legacy = _write_legacy_package(tmp_path)
    (legacy / "source_map.json").write_text(
        json.dumps(
            {
                REF_A: "PDF pages 35-38: growth/maturity and high-level challenges",
                REF_B: "PDF pages 37-41: distributed systems, Byzantine behavior, CAP, PACELC",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(PyramidProvenanceMigrationError, match="page-map mismatch"):
        migrate_legacy_mb4e_curriculum(
            curriculum_dir=legacy,
            output_dir=tmp_path / "migrated",
        )


def test_migration_rejects_existing_output_instead_of_overwriting(tmp_path: Path) -> None:
    legacy = _write_legacy_package(tmp_path)
    output = tmp_path / "migrated"
    output.mkdir()

    with pytest.raises(PyramidProvenanceMigrationError, match="already exists"):
        migrate_legacy_mb4e_curriculum(curriculum_dir=legacy, output_dir=output)


def test_migration_rejects_output_nested_inside_historical_package(tmp_path: Path) -> None:
    legacy = _write_legacy_package(tmp_path)
    nested_output = legacy / "migrated"

    with pytest.raises(PyramidProvenanceMigrationError, match="outside the legacy curriculum tree"):
        migrate_legacy_mb4e_curriculum(
            curriculum_dir=legacy,
            output_dir=nested_output,
        )

    assert not nested_output.exists()


def test_migration_report_write_failure_does_not_publish_partial_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    legacy = _write_legacy_package(tmp_path)
    output = tmp_path / "migrated"
    original_write_text = Path.write_text

    def fail_report_write(self: Path, data: str, *args: object, **kwargs: object) -> int:
        if self.name == "migration_report.json":
            raise OSError("simulated report write failure")
        return original_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fail_report_write)

    with pytest.raises(OSError, match="simulated report write failure"):
        migrate_legacy_mb4e_curriculum(curriculum_dir=legacy, output_dir=output)

    assert not output.exists()


def test_provenance_rejects_ambiguous_mixed_page_basis(tmp_path: Path) -> None:
    legacy = _write_legacy_package(tmp_path)
    output = tmp_path / "migrated"
    migrate_legacy_mb4e_curriculum(curriculum_dir=legacy, output_dir=output)
    rows = _raw_rows(output / "provenance.jsonl")
    rows[0]["locations"][0]["book_pages"] = [34]
    (output / "provenance.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in rows),
        encoding="utf-8",
    )

    with pytest.raises(CurriculumPackageError, match="exactly one of book_pages or pdf_pages"):
        validate_package(output)
