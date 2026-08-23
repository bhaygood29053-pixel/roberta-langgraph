from __future__ import annotations

from dataclasses import replace
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
    PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE,
    PyramidSourceReconstructionError,
    build_source_grounded_reconstructions,
    write_source_grounded_reconstruction_bundle,
)
from roberta.learning.user_source_batch import get_user_source_spec


CURRICULUM_ID = "pyramid_source_reconstruction_fixture"
EXERCISE_ID = "PSR-L01-00001"
EXPECTED_SENTINEL = "SECRET_EXPECTED_ANSWER_MUST_NOT_ENTER_RETRIEVAL"
GRADER_SENTINEL = "SECRET_GRADER_NOTE_MUST_NOT_ENTER_RETRIEVAL"


def _manifest(source_key: str) -> dict[str, object]:
    spec = get_user_source_spec(source_key)
    return {
        "manifest_contract": "roberta-pyramid-manifest/v1",
        "curriculum_contract": PYRAMID_CONTRACT,
        "curriculum_id": CURRICULUM_ID,
        "title": "Pyramid source reconstruction fixture",
        "source_type": "book",
        "approved_source_refs": [source_key],
        "levels": [1],
        "source_title": spec.title,
        "source_author": "Fixture Author",
        "source_edition": None,
        "publication_date": None,
        "source_version": spec.version,
        "source_origin": spec.origin,
        "source_authority_class": spec.authority_class,
        "ingestion_version": "utf8-source/v1",
        "ingestion_timestamp": "2026-08-23T12:00:00-04:00",
        "source_status": "approved_static_fixture",
        "source_limitations": ["Static test evidence only."],
        "source_provenance": {
            "contract": SOURCE_PROVENANCE_CONTRACT,
            "file": "provenance.jsonl",
            "source_key": source_key,
            "source_artifact_sha256": spec.original_sha256,
            "source_transcript_sha256": spec.transcript_sha256,
            "location_scheme": "chapter + named section + printed book page(s)",
        },
    }


def _exercise(source_key: str, *, query_text: str = "What is XONE?") -> dict[str, object]:
    return {
        "exercise_id": EXERCISE_ID,
        "curriculum_id": CURRICULUM_ID,
        "level": 1,
        "concept": "XONE",
        "subconcept": "token",
        "question": query_text,
        "expected_answer": EXPECTED_SENTINEL,
        "source_refs": [source_key],
        "question_type": "definition",
        "difficulty": 1,
        "required_reasoning_points": ["fixture reasoning point"],
        "grading_rubric_id": "pyramid-question-first-v1",
    }


def _write_fixture(
    tmp_path: Path,
    *,
    source_key: str = "xone_erc20_v4",
    query_text: str = "What is XONE?",
) -> tuple[Path, Path, Path]:
    curriculum = tmp_path / "curriculum"
    curriculum.mkdir()
    (curriculum / "manifest.json").write_text(
        json.dumps(_manifest(source_key)), encoding="utf-8"
    )
    (curriculum / "exercises.jsonl").write_text(
        json.dumps(_exercise(source_key, query_text=query_text)) + "\n",
        encoding="utf-8",
    )
    (curriculum / "provenance.jsonl").write_text(
        json.dumps(
            {
                "exercise_id": EXERCISE_ID,
                "source_key": source_key,
                "locations": [
                    {
                        "chapter": "Chapter 1: Fixture",
                        "section": "Token",
                        "book_pages": [1, 2],
                    }
                ],
                "supports": [
                    "question",
                    "expected_answer",
                    "required_reasoning_points",
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    _, exercises = validate_package(curriculum)
    checkpoints = tmp_path / "checkpoints"
    checkpoints.mkdir()
    checkpoint_file = "level_01_batch_0001.json"
    checkpoint_path = checkpoints / checkpoint_file
    row = {
        "exercise_id": EXERCISE_ID,
        "answer": "XONE is a blockchain token used by its project.",
        "grade": "PARTIAL",
        "score": 0.5,
        "correct": False,
        "failure_codes": ["conceptual_mismatch"],
        "critical_failure": False,
        "grader_note": GRADER_SENTINEL,
    }
    checkpoint_path.write_text(
        json.dumps(
            {
                "checkpoint_schema": CHECKPOINT_SCHEMA,
                "grading_semantics": GRADING_SEMANTICS,
                "exercise_ids": [EXERCISE_ID],
                "grades": [row],
            },
            ensure_ascii=False,
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
        answer=row["answer"],
        grader_note=GRADER_SENTINEL,
        checkpoint_file=checkpoint_file,
        checkpoint_sha256=checkpoint_sha,
        checkpoint_schema=CHECKPOINT_SCHEMA,
        grading_semantics=GRADING_SEMANTICS,
    )
    handoffs = build_pyramid_learning_handoffs(
        exercises,
        (weak,),
        curriculum_id=CURRICULUM_ID,
        approved_source_refs=(source_key,),
    )
    handoffs_path = tmp_path / "learning_handoffs.jsonl"
    write_pyramid_learning_handoffs_jsonl(handoffs_path, handoffs)
    return curriculum, checkpoints, handoffs_path


def test_valid_handoff_checkpoint_and_approved_source_produce_deterministic_reconstruction(tmp_path) -> None:
    curriculum, checkpoints, handoffs = _write_fixture(tmp_path)

    first = build_source_grounded_reconstructions(
        curriculum_dir=curriculum,
        handoffs_path=handoffs,
        checkpoints_dir=checkpoints,
        top_k=2,
    )
    second = build_source_grounded_reconstructions(
        curriculum_dir=curriculum,
        handoffs_path=handoffs,
        checkpoints_dir=checkpoints,
        top_k=2,
    )

    assert len(first) == 1
    assert first == second
    reconstruction = first[0]
    assert reconstruction.reconstruction_id.startswith("pyrrecon_")
    assert reconstruction.reconstruction_hash == reconstruction.reconstruction_id.removeprefix("pyrrecon_")
    assert reconstruction.source_grounded is True
    assert reconstruction.required_next_gate == PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE
    assert reconstruction.evidence_anchors
    assert all(anchor.source_id == reconstruction.source_id for anchor in reconstruction.evidence_anchors)
    assert all(anchor.source_approval_status == "approved" for anchor in reconstruction.evidence_anchors)
    assert EXPECTED_SENTINEL not in reconstruction.retrieval_query_text
    assert GRADER_SENTINEL not in reconstruction.retrieval_query_text
    assert reconstruction.question in reconstruction.retrieval_query_text
    assert reconstruction.provenance_locations[0].book_pages == (1, 2)
    assert reconstruction.phase8_candidate_creation_authorized is False
    assert reconstruction.source_truth_authorized is False
    assert reconstruction.live_state_authorized is False
    assert reconstruction.memory_promotion_authorized is False
    assert reconstruction.retention_authorized is False
    assert reconstruction.governance_mutation_authorized is False
    assert reconstruction.execution_authorized is False


def test_reconstruction_identity_changes_when_canonical_retrieval_changes(tmp_path) -> None:
    curriculum, checkpoints, handoffs = _write_fixture(tmp_path)
    one = build_source_grounded_reconstructions(
        curriculum_dir=curriculum,
        handoffs_path=handoffs,
        checkpoints_dir=checkpoints,
        top_k=1,
    )[0]
    two = build_source_grounded_reconstructions(
        curriculum_dir=curriculum,
        handoffs_path=handoffs,
        checkpoints_dir=checkpoints,
        top_k=2,
    )[0]
    assert one.retrieval_id != two.retrieval_id
    assert one.evidence_packet_id != two.evidence_packet_id
    assert one.reconstruction_id != two.reconstruction_id


def test_tampered_handoff_fails_closed(tmp_path) -> None:
    curriculum, checkpoints, handoffs = _write_fixture(tmp_path)
    raw = json.loads(handoffs.read_text(encoding="utf-8").strip())
    raw["question"] = "Tampered question?"
    handoffs.write_text(json.dumps(raw) + "\n", encoding="utf-8")

    with pytest.raises(PyramidSourceReconstructionError, match="invalid Pyramid learning handoff"):
        build_source_grounded_reconstructions(
            curriculum_dir=curriculum,
            handoffs_path=handoffs,
            checkpoints_dir=checkpoints,
        )


def test_curriculum_drift_after_handoff_fails_closed(tmp_path) -> None:
    curriculum, checkpoints, handoffs = _write_fixture(tmp_path)
    exercise = _exercise("xone_erc20_v4", query_text="What changed in XONE?")
    (curriculum / "exercises.jsonl").write_text(json.dumps(exercise) + "\n", encoding="utf-8")

    with pytest.raises(PyramidSourceReconstructionError, match="does not match validated curriculum"):
        build_source_grounded_reconstructions(
            curriculum_dir=curriculum,
            handoffs_path=handoffs,
            checkpoints_dir=checkpoints,
        )


def test_checkpoint_tampering_fails_before_source_reconstruction(tmp_path) -> None:
    curriculum, checkpoints, handoffs = _write_fixture(tmp_path)
    checkpoint = checkpoints / "level_01_batch_0001.json"
    checkpoint.write_text(checkpoint.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(PyramidSourceReconstructionError, match="checkpoint SHA-256"):
        build_source_grounded_reconstructions(
            curriculum_dir=curriculum,
            handoffs_path=handoffs,
            checkpoints_dir=checkpoints,
        )


@pytest.mark.parametrize("wrong_bytes", [None, b"not-the-pinned-mastering-blockchain-transcript"])
def test_external_source_requires_exact_pinned_transcript(tmp_path, wrong_bytes: bytes | None) -> None:
    curriculum, checkpoints, handoffs = _write_fixture(
        tmp_path,
        source_key="mastering_blockchain_4e_2023",
        query_text="What is a blockchain?",
    )
    transcript_path = None
    if wrong_bytes is not None:
        path = tmp_path / "wrong-transcript.txt"
        path.write_bytes(wrong_bytes)
        transcript_path = path

    with pytest.raises(PyramidSourceReconstructionError, match="failed integrity validation"):
        build_source_grounded_reconstructions(
            curriculum_dir=curriculum,
            handoffs_path=handoffs,
            checkpoints_dir=checkpoints,
            source_transcript_path=transcript_path,
        )


def test_no_match_source_retrieval_fails_closed(tmp_path) -> None:
    curriculum, checkpoints, handoffs = _write_fixture(
        tmp_path,
        query_text="zzzzqwertynotfound qqqqplughneverpresent?",
    )
    raw_exercise = json.loads((curriculum / "exercises.jsonl").read_text(encoding="utf-8"))
    raw_exercise["concept"] = "zzzzconceptneverpresent"
    raw_exercise["subconcept"] = "zzzzsubconceptneverpresent"
    (curriculum / "exercises.jsonl").write_text(json.dumps(raw_exercise) + "\n", encoding="utf-8")

    # Regenerate the handoff so curriculum/handoff identity is valid; only source retrieval is absent.
    _, exercises = validate_package(curriculum)
    checkpoint = checkpoints / "level_01_batch_0001.json"
    checkpoint_sha = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    checkpoint_raw = json.loads(checkpoint.read_text(encoding="utf-8"))
    row = checkpoint_raw["grades"][0]
    weak = WeakItem(
        exercise_id=EXERCISE_ID,
        grade="PARTIAL",
        score=0.5,
        critical_failure=False,
        failure_codes=("conceptual_mismatch",),
        answer=row["answer"],
        grader_note=GRADER_SENTINEL,
        checkpoint_file=checkpoint.name,
        checkpoint_sha256=checkpoint_sha,
        checkpoint_schema=CHECKPOINT_SCHEMA,
        grading_semantics=GRADING_SEMANTICS,
    )
    regenerated = build_pyramid_learning_handoffs(
        exercises,
        (weak,),
        curriculum_id=CURRICULUM_ID,
        approved_source_refs=("xone_erc20_v4",),
    )
    write_pyramid_learning_handoffs_jsonl(handoffs, regenerated)

    with pytest.raises(PyramidSourceReconstructionError, match="retrieval was insufficient"):
        build_source_grounded_reconstructions(
            curriculum_dir=curriculum,
            handoffs_path=handoffs,
            checkpoints_dir=checkpoints,
        )


def test_bundle_writer_is_atomic_and_rejects_authority_widening(tmp_path) -> None:
    curriculum, checkpoints, handoffs = _write_fixture(tmp_path)
    valid = build_source_grounded_reconstructions(
        curriculum_dir=curriculum,
        handoffs_path=handoffs,
        checkpoints_dir=checkpoints,
        top_k=1,
    )[0]
    invalid = replace(valid, retention_authorized=True)
    output = tmp_path / "reconstruction-output"

    with pytest.raises(PyramidSourceReconstructionError, match="cannot authorize"):
        write_source_grounded_reconstruction_bundle(output, (valid, invalid))
    assert not output.exists()


def test_bundle_writer_emits_report_and_machine_readable_jsonl(tmp_path) -> None:
    curriculum, checkpoints, handoffs = _write_fixture(tmp_path)
    reconstructions = build_source_grounded_reconstructions(
        curriculum_dir=curriculum,
        handoffs_path=handoffs,
        checkpoints_dir=checkpoints,
        top_k=1,
    )
    output = tmp_path / "reconstruction-output"
    report = write_source_grounded_reconstruction_bundle(output, reconstructions)

    assert report.reconstruction_count == 1
    assert report.source_grounded_count == 1
    assert report.retention_authorized is False
    rows = (output / "source_grounded_reconstructions.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(rows) == 1
    raw = json.loads(rows[0])
    assert raw["reconstruction_id"] == reconstructions[0].reconstruction_id
    assert raw["source_grounded"] is True
    report_raw = json.loads((output / "reconstruction_report.json").read_text(encoding="utf-8"))
    assert report_raw["reconstruction_count"] == 1
    assert report_raw["phase8_candidate_creation_authorized"] is False
    assert report_raw["retention_authorized"] is False
