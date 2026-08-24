from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from roberta.learning.curriculum_io import SOURCE_PROVENANCE_CONTRACT, validate_package
from roberta.learning.pyramid import PYRAMID_CONTRACT
from roberta.learning.pyramid_exam import CHECKPOINT_SCHEMA, GRADING_SEMANTICS
from roberta.learning.pyramid_learning_handoff import (
    build_pyramid_learning_handoffs,
    write_pyramid_learning_handoffs_jsonl,
)
from roberta.learning.pyramid_remediation import WeakItem
from roberta.learning.pyramid_source_reconstruction import (
    PyramidSourceReconstructionError,
    build_source_grounded_reconstructions,
)
from roberta.learning.user_source_batch import get_user_source_spec


SOURCE_KEY = "xone_erc20_v4"
CURRICULUM_ID = "pyramid_pdf_reconstruction_reload_fixture"
EXERCISE_ID = "PPR-L01-00001"


def _write_pdf_fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    spec = get_user_source_spec(SOURCE_KEY)
    assert spec.original_media_type == "application/pdf"
    assert spec.original_page_count is not None

    curriculum = tmp_path / "curriculum"
    curriculum.mkdir()
    manifest = {
        "manifest_contract": "roberta-pyramid-manifest/v1",
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": CURRICULUM_ID,
        "title": "Pyramid PDF reconstruction reload fixture",
        "source_type": "book",
        "approved_source_refs": [SOURCE_KEY],
        "levels": [1],
        "source_title": spec.title,
        "source_author": "Fixture Author",
        "source_edition": None,
        "publication_date": None,
        "source_version": spec.version,
        "source_origin": spec.origin,
        "source_authority_class": spec.authority_class,
        "ingestion_version": "utf8-source/v1",
        "ingestion_timestamp": "2026-08-23T22:57:00-04:00",
        "source_status": "approved_static_fixture",
        "source_limitations": ["Static test evidence only."],
        "source_provenance": {
            "contract": SOURCE_PROVENANCE_CONTRACT,
            "file": "provenance.jsonl",
            "source_key": SOURCE_KEY,
            "source_artifact_sha256": spec.original_sha256,
            "source_transcript_sha256": spec.transcript_sha256,
            "location_scheme": "chapter + named section + PDF page(s)",
        },
    }
    exercise = {
        "exercise_id": EXERCISE_ID,
        "curriculum_id": CURRICULUM_ID,
        "level": 1,
        "concept": "XONE",
        "subconcept": "token",
        "question": "What is XONE?",
        "expected_answer": "XONE is the token described by the source.",
        "source_refs": [SOURCE_KEY],
        "question_type": "definition",
        "difficulty": 1,
        "required_reasoning_points": ["identify the token from the source"],
        "grading_rubric_id": "pyramid-question-first-v1",
    }
    provenance = {
        "exercise_id": EXERCISE_ID,
        "source_key": SOURCE_KEY,
        "locations": [
            {
                "chapter": "Chapter 1: Fixture",
                "section": "Token",
                "pdf_pages": [1, 2],
                "legacy_source_ref": "XONE-PDF-P1-2-FIXTURE",
            }
        ],
        "supports": [
            "question",
            "expected_answer",
            "required_reasoning_points",
        ],
    }
    (curriculum / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    (curriculum / "exercises.jsonl").write_text(
        json.dumps(exercise) + "\n", encoding="utf-8"
    )
    (curriculum / "provenance.jsonl").write_text(
        json.dumps(provenance) + "\n", encoding="utf-8"
    )

    _, exercises = validate_package(curriculum)

    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    checkpoint_file = "level_01_batch_0001.json"
    checkpoint_path = checkpoints / checkpoint_file
    grade = {
        "exercise_id": EXERCISE_ID,
        "answer": "XONE is a blockchain token used by its project.",
        "grade": "PARTIAL",
        "score": 0.5,
        "correct": False,
        "failure_codes": ["conceptual_mismatch"],
        "critical_failure": False,
        "grader_note": "fixture diagnostic",
    }
    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_schema": CHECKPOINT_SCHEMA,
                "grading_semantics": GRADING_SEMANTICS,
                "exercise_ids": [EXERCISE_ID],
                "grades": [grade],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    checkpoint_sha = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest()
    weak = WeakItem(
        exercise_id=EXERCISE_ID,
        grade="PARTIAL",
        score=0.5,
        critical_failure=False,
        failure_codes=("conceptual_mismatch",),
        answer=grade["answer"],
        grader_note=grade["grader_note"],
        checkpoint_file=checkpoint_file,
        checkpoint_sha256=checkpoint_sha,
        checkpoint_schema=CHECKPOINT_SCHEMA,
        grading_semantics=GRADING_SEMANTICS,
    )
    handoff_rows = build_pyramid_learning_handoffs(
        exercises,
        (weak,),
        curriculum_id=CURRICULUM_ID,
        approved_source_refs=(SOURCE_KEY,),
    )
    handoffs = tmp_path / "learning_handoffs.jsonl"
    write_pyramid_learning_handoffs_jsonl(handoffs, handoff_rows)
    return curriculum, checkpoints, handoffs


def test_pdf_provenance_without_verified_alignment_fails_closed_after_trusted_reload(
    tmp_path: Path,
) -> None:
    curriculum, checkpoints, handoffs = _write_pdf_fixture(tmp_path)

    with pytest.raises(
        PyramidSourceReconstructionError,
        match="no verified PDF/transcript alignment",
    ):
        build_source_grounded_reconstructions(
            curriculum_dir=curriculum,
            handoffs_path=handoffs,
            checkpoints_dir=checkpoints,
            top_k=2,
        )
