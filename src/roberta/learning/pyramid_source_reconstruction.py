from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Mapping, Sequence

from .chunking import chunk_parsed_document
from .curriculum_io import load_source_provenance_jsonl, validate_package
from .grounding import EvidenceAnchor, build_evidence_packet
from .indexing import build_evidence_index
from .pyramid import Exercise
from .pyramid_exam import CHECKPOINT_SCHEMA, GRADE_SCORES, GRADING_SEMANTICS
from .pyramid_learning_handoff import (
    PYRAMID_LEARNING_HANDOFF_CONTRACT,
    PYRAMID_LEARNING_HANDOFF_VERSION,
    PyramidLearningHandoff,
    PyramidLearningHandoffError,
    validate_pyramid_learning_handoff,
)
from .retrieval import RetrievalCorpusItem, RetrievalFilters, retrieve_evidence
from .source_ingestion import InMemorySourceStore, SourceIngestionError
from .structure import parse_markdown_structure
from .user_source_batch import get_user_source_spec, ingest_user_source


PYRAMID_SOURCE_RECONSTRUCTION_CONTRACT = "roberta-pyramid-source-grounded-reconstruction/v1"
PYRAMID_SOURCE_RECONSTRUCTION_VERSION = "1.0.0"
PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE = "targeted_pyramid_practice"


class PyramidSourceReconstructionError(RuntimeError):
    """Raised when a Pyramid handoff cannot be grounded in canonical source evidence."""


@dataclass(frozen=True, slots=True)
class SourceProvenanceLocator:
    chapter: str
    section: str
    book_pages: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ReconstructionEvidenceAnchor:
    anchor_id: str
    label: str
    chunk_id: str
    source_id: str
    document_id: str
    section_id: str | None
    structural_path: tuple[str, ...]
    line_start: int
    line_end: int
    text: str
    content_hash: str
    source_authority_class: str
    source_approval_status: str
    fusion_rank: int


@dataclass(frozen=True, slots=True)
class PyramidSourceGroundedReconstruction:
    reconstruction_id: str
    reconstruction_hash: str
    reconstruction_contract: str
    reconstruction_version: str
    handoff_id: str
    handoff_hash: str
    curriculum_id: str
    exercise_id: str
    level: int
    concept: str
    subconcept: str | None
    question: str
    checkpoint_file: str
    checkpoint_sha256: str
    checkpoint_schema: str
    grading_semantics: str
    source_key: str
    source_artifact_sha256: str
    source_transcript_sha256: str
    source_id: str
    source_content_hash: str
    provenance_supports: tuple[str, ...]
    provenance_locations: tuple[SourceProvenanceLocator, ...]
    retrieval_query_text: str
    retrieval_id: str
    retrieval_hash: str
    evidence_packet_id: str
    evidence_packet_hash: str
    evidence_packet_status: str
    evidence_anchors: tuple[ReconstructionEvidenceAnchor, ...]
    source_grounded: bool
    required_next_gate: str
    phase8_candidate_creation_authorized: bool
    source_truth_authorized: bool
    live_state_authorized: bool
    memory_promotion_authorized: bool
    retention_authorized: bool
    governance_mutation_authorized: bool
    execution_authorized: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "reconstruction_id": self.reconstruction_id,
            "reconstruction_hash": self.reconstruction_hash,
            **_reconstruction_material(self),
        }


@dataclass(frozen=True, slots=True)
class PyramidSourceReconstructionReport:
    contract: str
    version: str
    curriculum_id: str
    source_key: str
    reconstruction_count: int
    evidence_anchor_count: int
    packet_status_counts: tuple[tuple[str, int], ...]
    source_grounded_count: int
    phase8_candidate_creation_authorized: bool = False
    source_truth_authorized: bool = False
    live_state_authorized: bool = False
    memory_promotion_authorized: bool = False
    retention_authorized: bool = False
    governance_mutation_authorized: bool = False
    execution_authorized: bool = False

    def to_mapping(self) -> dict[str, Any]:
        return {
            "contract": self.contract,
            "version": self.version,
            "curriculum_id": self.curriculum_id,
            "source_key": self.source_key,
            "reconstruction_count": self.reconstruction_count,
            "evidence_anchor_count": self.evidence_anchor_count,
            "packet_status_counts": dict(self.packet_status_counts),
            "source_grounded_count": self.source_grounded_count,
            "phase8_candidate_creation_authorized": self.phase8_candidate_creation_authorized,
            "source_truth_authorized": self.source_truth_authorized,
            "live_state_authorized": self.live_state_authorized,
            "memory_promotion_authorized": self.memory_promotion_authorized,
            "retention_authorized": self.retention_authorized,
            "governance_mutation_authorized": self.governance_mutation_authorized,
            "execution_authorized": self.execution_authorized,
        }


_HANDOFF_FIELDS = frozenset(
    {
        "handoff_id",
        "handoff_hash",
        "handoff_contract",
        "handoff_version",
        "curriculum_id",
        "exercise_id",
        "level",
        "concept",
        "subconcept",
        "question",
        "roberta_answer",
        "grade",
        "score",
        "failure_codes",
        "critical_failure",
        "grader_note",
        "grader_note_role",
        "source_refs",
        "checkpoint_file",
        "checkpoint_sha256",
        "checkpoint_schema",
        "grading_semantics",
        "remediation_query",
        "required_next_gate",
        "source_grounding_required",
        "phase8_candidate_creation_authorized",
        "source_truth_authorized",
        "live_state_authorized",
        "memory_promotion_authorized",
        "retention_authorized",
        "governance_mutation_authorized",
        "execution_authorized",
    }
)


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise PyramidSourceReconstructionError(
            "source reconstruction material must be canonical JSON-compatible data"
        ) from exc


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise PyramidSourceReconstructionError(f"{name} must be a normalized non-empty string")
    return value


def _optional_text(name: str, value: object) -> str | None:
    if value is None:
        return None
    return _text(name, value)


def _bool(name: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise PyramidSourceReconstructionError(f"{name} must be boolean")
    return value


def _score(value: object, *, grade: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PyramidSourceReconstructionError("handoff score must be numeric")
    score = float(value)
    if not math.isfinite(score) or grade not in GRADE_SCORES or score != GRADE_SCORES[grade]:
        raise PyramidSourceReconstructionError("handoff score does not match grade semantics")
    return score


def _string_tuple(name: str, value: object) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PyramidSourceReconstructionError(f"{name} must be an array of strings")
    return tuple(value)


def _handoff_from_mapping(raw: object) -> PyramidLearningHandoff:
    if not isinstance(raw, Mapping):
        raise PyramidSourceReconstructionError("Pyramid handoff JSONL rows must be objects")
    fields = set(raw)
    if fields != _HANDOFF_FIELDS:
        missing = sorted(_HANDOFF_FIELDS - fields)
        extra = sorted(fields - _HANDOFF_FIELDS)
        raise PyramidSourceReconstructionError(
            f"Pyramid handoff fields do not match contract; missing={missing}, extra={extra}"
        )
    if raw.get("handoff_contract") != PYRAMID_LEARNING_HANDOFF_CONTRACT:
        raise PyramidSourceReconstructionError("unsupported Pyramid learning handoff contract")
    if raw.get("handoff_version") != PYRAMID_LEARNING_HANDOFF_VERSION:
        raise PyramidSourceReconstructionError("unsupported Pyramid learning handoff version")

    grade = _text("grade", raw["grade"]).upper()
    level = raw["level"]
    if isinstance(level, bool) or not isinstance(level, int):
        raise PyramidSourceReconstructionError("handoff level must be an integer")
    handoff = PyramidLearningHandoff(
        handoff_id=_text("handoff_id", raw["handoff_id"]),
        handoff_hash=_text("handoff_hash", raw["handoff_hash"]),
        handoff_contract=str(raw["handoff_contract"]),
        handoff_version=str(raw["handoff_version"]),
        curriculum_id=_text("curriculum_id", raw["curriculum_id"]),
        exercise_id=_text("exercise_id", raw["exercise_id"]),
        level=level,
        concept=_text("concept", raw["concept"]),
        subconcept=_optional_text("subconcept", raw["subconcept"]),
        question=_text("question", raw["question"]),
        roberta_answer=_text("roberta_answer", raw["roberta_answer"]),
        grade=grade,
        score=_score(raw["score"], grade=grade),
        failure_codes=_string_tuple("failure_codes", raw["failure_codes"]),
        critical_failure=_bool("critical_failure", raw["critical_failure"]),
        grader_note=(
            raw["grader_note"]
            if isinstance(raw["grader_note"], str)
            else (_ for _ in ()).throw(
                PyramidSourceReconstructionError("grader_note must be a string")
            )
        ),
        grader_note_role=_text("grader_note_role", raw["grader_note_role"]),
        source_refs=_string_tuple("source_refs", raw["source_refs"]),
        checkpoint_file=_text("checkpoint_file", raw["checkpoint_file"]),
        checkpoint_sha256=_text("checkpoint_sha256", raw["checkpoint_sha256"]),
        checkpoint_schema=_text("checkpoint_schema", raw["checkpoint_schema"]),
        grading_semantics=_text("grading_semantics", raw["grading_semantics"]),
        remediation_query=_text("remediation_query", raw["remediation_query"]),
        required_next_gate=_text("required_next_gate", raw["required_next_gate"]),
        source_grounding_required=_bool(
            "source_grounding_required", raw["source_grounding_required"]
        ),
        phase8_candidate_creation_authorized=_bool(
            "phase8_candidate_creation_authorized",
            raw["phase8_candidate_creation_authorized"],
        ),
        source_truth_authorized=_bool(
            "source_truth_authorized", raw["source_truth_authorized"]
        ),
        live_state_authorized=_bool(
            "live_state_authorized", raw["live_state_authorized"]
        ),
        memory_promotion_authorized=_bool(
            "memory_promotion_authorized", raw["memory_promotion_authorized"]
        ),
        retention_authorized=_bool(
            "retention_authorized", raw["retention_authorized"]
        ),
        governance_mutation_authorized=_bool(
            "governance_mutation_authorized", raw["governance_mutation_authorized"]
        ),
        execution_authorized=_bool(
            "execution_authorized", raw["execution_authorized"]
        ),
    )
    try:
        return validate_pyramid_learning_handoff(handoff)
    except PyramidLearningHandoffError as exc:
        raise PyramidSourceReconstructionError("invalid Pyramid learning handoff") from exc


def load_pyramid_learning_handoffs_jsonl(path: str | Path) -> tuple[PyramidLearningHandoff, ...]:
    source = Path(path)
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise PyramidSourceReconstructionError(f"cannot read Pyramid learning handoffs: {exc}") from exc
    handoffs: list[PyramidLearningHandoff] = []
    for line_number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PyramidSourceReconstructionError(
                f"invalid Pyramid handoff JSONL at line {line_number}: {exc}"
            ) from exc
        handoffs.append(_handoff_from_mapping(raw))
    if not handoffs:
        raise PyramidSourceReconstructionError("Pyramid learning handoff file is empty")
    ids = [item.handoff_id for item in handoffs]
    if len(set(ids)) != len(ids):
        raise PyramidSourceReconstructionError("Pyramid learning handoff ids must be unique")
    return tuple(handoffs)


def _validate_curriculum_binding(handoff: PyramidLearningHandoff, exercise: Exercise) -> None:
    expected = (
        handoff.curriculum_id,
        handoff.exercise_id,
        handoff.level,
        handoff.concept,
        handoff.subconcept,
        handoff.question,
        handoff.source_refs,
    )
    actual = (
        exercise.curriculum_id,
        exercise.exercise_id,
        exercise.level,
        exercise.concept,
        exercise.subconcept,
        exercise.question,
        exercise.source_refs,
    )
    if expected != actual:
        raise PyramidSourceReconstructionError(
            f"Pyramid handoff does not match validated curriculum exercise {handoff.exercise_id}"
        )


def _checkpoint_grade_binding(handoff: PyramidLearningHandoff, checkpoint_root: Path) -> None:
    if Path(handoff.checkpoint_file).name != handoff.checkpoint_file:
        raise PyramidSourceReconstructionError("handoff checkpoint_file must be a basename")
    path = checkpoint_root / handoff.checkpoint_file
    try:
        raw_bytes = path.read_bytes()
        raw = json.loads(raw_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PyramidSourceReconstructionError(
            f"cannot validate checkpoint binding for {handoff.exercise_id}: {exc}"
        ) from exc
    if hashlib.sha256(raw_bytes).hexdigest() != handoff.checkpoint_sha256:
        raise PyramidSourceReconstructionError(
            f"checkpoint SHA-256 does not match handoff for {handoff.exercise_id}"
        )
    if not isinstance(raw, Mapping):
        raise PyramidSourceReconstructionError("checkpoint must be a JSON object")
    if raw.get("checkpoint_schema") != CHECKPOINT_SCHEMA or raw.get("checkpoint_schema") != handoff.checkpoint_schema:
        raise PyramidSourceReconstructionError("checkpoint schema does not match current handoff contract")
    if raw.get("grading_semantics") != GRADING_SEMANTICS or raw.get("grading_semantics") != handoff.grading_semantics:
        raise PyramidSourceReconstructionError("checkpoint grading semantics do not match current handoff contract")
    exercise_ids = raw.get("exercise_ids")
    if not isinstance(exercise_ids, list) or exercise_ids.count(handoff.exercise_id) != 1:
        raise PyramidSourceReconstructionError("checkpoint exercise identity does not uniquely bind handoff")
    grades = raw.get("grades")
    if not isinstance(grades, list):
        raise PyramidSourceReconstructionError("checkpoint grades must be an array")
    matches = [row for row in grades if isinstance(row, Mapping) and row.get("exercise_id") == handoff.exercise_id]
    if len(matches) != 1:
        raise PyramidSourceReconstructionError("checkpoint grade does not uniquely bind handoff")
    row = matches[0]
    raw_codes = row.get("failure_codes", [])
    if not isinstance(raw_codes, list) or not all(isinstance(code, str) for code in raw_codes):
        raise PyramidSourceReconstructionError("checkpoint failure_codes are malformed")
    try:
        score = float(row.get("score"))
    except (TypeError, ValueError) as exc:
        raise PyramidSourceReconstructionError("checkpoint score is malformed") from exc
    binding = (
        row.get("answer"),
        str(row.get("grade", "")).upper(),
        score,
        tuple(raw_codes),
        row.get("critical_failure"),
        row.get("grader_note", ""),
    )
    expected = (
        handoff.roberta_answer,
        handoff.grade,
        handoff.score,
        handoff.failure_codes,
        handoff.critical_failure,
        handoff.grader_note,
    )
    if binding != expected:
        raise PyramidSourceReconstructionError(
            f"checkpoint grade/answer diagnosis does not match handoff for {handoff.exercise_id}"
        )


def _locator(raw: object) -> SourceProvenanceLocator:
    if not isinstance(raw, Mapping):
        raise PyramidSourceReconstructionError("source provenance locator must be an object")
    chapter = _text("source provenance chapter", raw.get("chapter"))
    section = _text("source provenance section", raw.get("section"))
    pages = raw.get("book_pages")
    if (
        not isinstance(pages, list)
        or not pages
        or not all(isinstance(page, int) and not isinstance(page, bool) and page > 0 for page in pages)
    ):
        raise PyramidSourceReconstructionError("source provenance book_pages are malformed")
    return SourceProvenanceLocator(chapter=chapter, section=section, book_pages=tuple(pages))


def _provenance_for_exercise(raw: Mapping[str, object]) -> tuple[tuple[str, ...], tuple[SourceProvenanceLocator, ...]]:
    supports = raw.get("supports")
    locations = raw.get("locations")
    if not isinstance(supports, list) or not all(isinstance(item, str) for item in supports):
        raise PyramidSourceReconstructionError("source provenance supports are malformed")
    if not isinstance(locations, list) or not locations:
        raise PyramidSourceReconstructionError("source provenance locations are missing")
    return tuple(supports), tuple(_locator(item) for item in locations)


def _query_text(handoff: PyramidLearningHandoff) -> str:
    concept_path = handoff.concept if handoff.subconcept is None else f"{handoff.concept}/{handoff.subconcept}"
    return f"{handoff.question}\nConcept: {concept_path}"


def _evidence_anchor(anchor: EvidenceAnchor) -> ReconstructionEvidenceAnchor:
    return ReconstructionEvidenceAnchor(
        anchor_id=anchor.anchor_id,
        label=anchor.label,
        chunk_id=anchor.chunk_id,
        source_id=anchor.source_id,
        document_id=anchor.document_id,
        section_id=anchor.section_id,
        structural_path=anchor.structural_path,
        line_start=anchor.line_start,
        line_end=anchor.line_end,
        text=anchor.text,
        content_hash=anchor.content_hash,
        source_authority_class=anchor.source_authority_class,
        source_approval_status=anchor.source_approval_status,
        fusion_rank=anchor.fusion_rank,
    )


def _locator_mapping(value: SourceProvenanceLocator) -> dict[str, Any]:
    return {
        "chapter": value.chapter,
        "section": value.section,
        "book_pages": list(value.book_pages),
    }


def _anchor_mapping(value: ReconstructionEvidenceAnchor) -> dict[str, Any]:
    return {
        "anchor_id": value.anchor_id,
        "label": value.label,
        "chunk_id": value.chunk_id,
        "source_id": value.source_id,
        "document_id": value.document_id,
        "section_id": value.section_id,
        "structural_path": list(value.structural_path),
        "line_start": value.line_start,
        "line_end": value.line_end,
        "text": value.text,
        "content_hash": value.content_hash,
        "source_authority_class": value.source_authority_class,
        "source_approval_status": value.source_approval_status,
        "fusion_rank": value.fusion_rank,
    }


def _reconstruction_material(value: PyramidSourceGroundedReconstruction) -> dict[str, Any]:
    return {
        "reconstruction_contract": value.reconstruction_contract,
        "reconstruction_version": value.reconstruction_version,
        "handoff_id": value.handoff_id,
        "handoff_hash": value.handoff_hash,
        "curriculum_id": value.curriculum_id,
        "exercise_id": value.exercise_id,
        "level": value.level,
        "concept": value.concept,
        "subconcept": value.subconcept,
        "question": value.question,
        "checkpoint_file": value.checkpoint_file,
        "checkpoint_sha256": value.checkpoint_sha256,
        "checkpoint_schema": value.checkpoint_schema,
        "grading_semantics": value.grading_semantics,
        "source_key": value.source_key,
        "source_artifact_sha256": value.source_artifact_sha256,
        "source_transcript_sha256": value.source_transcript_sha256,
        "source_id": value.source_id,
        "source_content_hash": value.source_content_hash,
        "provenance_supports": list(value.provenance_supports),
        "provenance_locations": [_locator_mapping(item) for item in value.provenance_locations],
        "retrieval_query_text": value.retrieval_query_text,
        "retrieval_id": value.retrieval_id,
        "retrieval_hash": value.retrieval_hash,
        "evidence_packet_id": value.evidence_packet_id,
        "evidence_packet_hash": value.evidence_packet_hash,
        "evidence_packet_status": value.evidence_packet_status,
        "evidence_anchors": [_anchor_mapping(item) for item in value.evidence_anchors],
        "source_grounded": value.source_grounded,
        "required_next_gate": value.required_next_gate,
        "phase8_candidate_creation_authorized": value.phase8_candidate_creation_authorized,
        "source_truth_authorized": value.source_truth_authorized,
        "live_state_authorized": value.live_state_authorized,
        "memory_promotion_authorized": value.memory_promotion_authorized,
        "retention_authorized": value.retention_authorized,
        "governance_mutation_authorized": value.governance_mutation_authorized,
        "execution_authorized": value.execution_authorized,
    }


def validate_pyramid_source_grounded_reconstruction(
    value: PyramidSourceGroundedReconstruction,
) -> PyramidSourceGroundedReconstruction:
    if not isinstance(value, PyramidSourceGroundedReconstruction):
        raise PyramidSourceReconstructionError("reconstruction must be PyramidSourceGroundedReconstruction")
    if value.reconstruction_contract != PYRAMID_SOURCE_RECONSTRUCTION_CONTRACT:
        raise PyramidSourceReconstructionError("unsupported Pyramid source reconstruction contract")
    if value.reconstruction_version != PYRAMID_SOURCE_RECONSTRUCTION_VERSION:
        raise PyramidSourceReconstructionError("unsupported Pyramid source reconstruction version")
    if not value.evidence_anchors or value.source_grounded is not True:
        raise PyramidSourceReconstructionError("source-grounded reconstruction requires evidence anchors")
    if value.required_next_gate != PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE:
        raise PyramidSourceReconstructionError("source reconstruction next gate is invalid")
    if value.source_content_hash != value.source_transcript_sha256:
        raise PyramidSourceReconstructionError("source content hash must match pinned transcript SHA-256")
    for anchor in value.evidence_anchors:
        if anchor.source_id != value.source_id or anchor.source_approval_status != "approved":
            raise PyramidSourceReconstructionError("evidence anchor is outside the approved canonical source")
        if not anchor.text:
            raise PyramidSourceReconstructionError("evidence anchor text must not be empty")
    authority_flags = (
        value.phase8_candidate_creation_authorized,
        value.source_truth_authorized,
        value.live_state_authorized,
        value.memory_promotion_authorized,
        value.retention_authorized,
        value.governance_mutation_authorized,
        value.execution_authorized,
    )
    if any(flag is not False for flag in authority_flags):
        raise PyramidSourceReconstructionError("source reconstruction cannot authorize promotion, truth, retention, governance, or execution")
    digest = _hash(_reconstruction_material(value))
    if value.reconstruction_hash != digest or value.reconstruction_id != f"pyrrecon_{digest}":
        raise PyramidSourceReconstructionError("source reconstruction identity/content is invalid")
    return value


def _make_reconstruction(
    *,
    handoff: PyramidLearningHandoff,
    source_key: str,
    source_artifact_sha256: str,
    source_transcript_sha256: str,
    source_id: str,
    source_content_hash: str,
    provenance_supports: tuple[str, ...],
    provenance_locations: tuple[SourceProvenanceLocator, ...],
    query_text: str,
    retrieval_id: str,
    retrieval_hash: str,
    packet_id: str,
    packet_hash: str,
    packet_status: str,
    anchors: tuple[ReconstructionEvidenceAnchor, ...],
) -> PyramidSourceGroundedReconstruction:
    provisional = PyramidSourceGroundedReconstruction(
        reconstruction_id="",
        reconstruction_hash="",
        reconstruction_contract=PYRAMID_SOURCE_RECONSTRUCTION_CONTRACT,
        reconstruction_version=PYRAMID_SOURCE_RECONSTRUCTION_VERSION,
        handoff_id=handoff.handoff_id,
        handoff_hash=handoff.handoff_hash,
        curriculum_id=handoff.curriculum_id,
        exercise_id=handoff.exercise_id,
        level=handoff.level,
        concept=handoff.concept,
        subconcept=handoff.subconcept,
        question=handoff.question,
        checkpoint_file=handoff.checkpoint_file,
        checkpoint_sha256=handoff.checkpoint_sha256,
        checkpoint_schema=handoff.checkpoint_schema,
        grading_semantics=handoff.grading_semantics,
        source_key=source_key,
        source_artifact_sha256=source_artifact_sha256,
        source_transcript_sha256=source_transcript_sha256,
        source_id=source_id,
        source_content_hash=source_content_hash,
        provenance_supports=provenance_supports,
        provenance_locations=provenance_locations,
        retrieval_query_text=query_text,
        retrieval_id=retrieval_id,
        retrieval_hash=retrieval_hash,
        evidence_packet_id=packet_id,
        evidence_packet_hash=packet_hash,
        evidence_packet_status=packet_status,
        evidence_anchors=anchors,
        source_grounded=True,
        required_next_gate=PYRAMID_SOURCE_RECONSTRUCTION_NEXT_GATE,
        phase8_candidate_creation_authorized=False,
        source_truth_authorized=False,
        live_state_authorized=False,
        memory_promotion_authorized=False,
        retention_authorized=False,
        governance_mutation_authorized=False,
        execution_authorized=False,
    )
    digest = _hash(_reconstruction_material(provisional))
    value = PyramidSourceGroundedReconstruction(
        reconstruction_id=f"pyrrecon_{digest}",
        reconstruction_hash=digest,
        **{name: getattr(provisional, name) for name in provisional.__dataclass_fields__ if name not in {"reconstruction_id", "reconstruction_hash"}},
    )
    return validate_pyramid_source_grounded_reconstruction(value)


def build_source_grounded_reconstructions(
    *,
    curriculum_dir: str | Path,
    handoffs_path: str | Path,
    checkpoints_dir: str | Path,
    source_transcript_path: str | Path | None = None,
    top_k: int = 5,
) -> tuple[PyramidSourceGroundedReconstruction, ...]:
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise PyramidSourceReconstructionError("top_k must be a positive integer")
    manifest, exercises = validate_package(curriculum_dir)
    handoffs = load_pyramid_learning_handoffs_jsonl(handoffs_path)
    by_id = {item.exercise_id: item for item in exercises}
    if len(by_id) != len(exercises):
        raise PyramidSourceReconstructionError("validated curriculum contains duplicate exercise ids")

    declaration = manifest.get("source_provenance")
    if not isinstance(declaration, Mapping):
        raise PyramidSourceReconstructionError("validated curriculum must declare source_provenance")
    source_key = _text("source_provenance.source_key", declaration.get("source_key"))
    provenance_file = _text("source_provenance.file", declaration.get("file"))
    source_artifact_sha256 = _text(
        "source_provenance.source_artifact_sha256", declaration.get("source_artifact_sha256")
    )
    source_transcript_sha256 = _text(
        "source_provenance.source_transcript_sha256", declaration.get("source_transcript_sha256")
    )
    provenance_rows = load_source_provenance_jsonl(
        Path(curriculum_dir) / provenance_file,
        expected_source_key=source_key,
        expected_exercise_ids=set(by_id),
    )
    provenance_by_id = {str(row["exercise_id"]): row for row in provenance_rows}

    checkpoint_root = Path(checkpoints_dir)
    if not checkpoint_root.is_dir():
        raise PyramidSourceReconstructionError("checkpoint directory does not exist")

    # Validate the entire diagnostic chain before source ingestion/retrieval.
    for handoff in handoffs:
        exercise = by_id.get(handoff.exercise_id)
        if exercise is None:
            raise PyramidSourceReconstructionError(
                f"handoff exercise {handoff.exercise_id!r} is absent from validated curriculum"
            )
        _validate_curriculum_binding(handoff, exercise)
        if source_key not in handoff.source_refs:
            raise PyramidSourceReconstructionError(
                f"handoff {handoff.exercise_id} does not reference canonical provenance source {source_key}"
            )
        _checkpoint_grade_binding(handoff, checkpoint_root)

    spec = get_user_source_spec(source_key)
    if spec.original_sha256 != source_artifact_sha256 or spec.transcript_sha256 != source_transcript_sha256:
        raise PyramidSourceReconstructionError("curriculum source digests do not match registered Learning System source")
    external_transcript: bytes | None = None
    if source_transcript_path is not None:
        try:
            external_transcript = Path(source_transcript_path).read_bytes()
        except OSError as exc:
            raise PyramidSourceReconstructionError(f"cannot read source transcript: {exc}") from exc

    store = InMemorySourceStore()
    try:
        ingestion = ingest_user_source(
            source_key,
            store=store,
            external_transcript=external_transcript,
        )
    except SourceIngestionError as exc:
        raise PyramidSourceReconstructionError(
            f"approved source transcript failed integrity validation for {source_key}"
        ) from exc
    source = ingestion.record
    if source.content_hash != source_transcript_sha256 or source.approval_status != "approved":
        raise PyramidSourceReconstructionError("ingested source is not the exact approved transcript")

    parsed = parse_markdown_structure(store=store, source_id=source.source_id)
    chunked = chunk_parsed_document(store=store, parsed=parsed)
    indexed = build_evidence_index(store=store, chunked=chunked, embedding_provider=None)
    corpus = (RetrievalCorpusItem(chunked=chunked, indexed=indexed),)

    reconstructions: list[PyramidSourceGroundedReconstruction] = []
    for handoff in handoffs:
        query_text = _query_text(handoff)
        retrieval = retrieve_evidence(
            store=store,
            corpus=corpus,
            text=query_text,
            filters=RetrievalFilters(
                source_ids=(source.source_id,),
                source_approval_statuses=("approved",),
            ),
            top_k=top_k,
            candidate_limit=max(50, top_k),
        )
        packet = build_evidence_packet(store=store, corpus=corpus, result=retrieval)
        if packet.insufficient_evidence or not packet.evidence_anchors:
            raise PyramidSourceReconstructionError(
                f"canonical source retrieval was insufficient for {handoff.exercise_id}"
            )
        anchors = tuple(_evidence_anchor(item) for item in packet.evidence_anchors)
        if any(item.source_id != source.source_id or item.source_approval_status != "approved" for item in anchors):
            raise PyramidSourceReconstructionError("retrieval escaped canonical approved source filter")
        supports, locations = _provenance_for_exercise(provenance_by_id[handoff.exercise_id])
        reconstructions.append(
            _make_reconstruction(
                handoff=handoff,
                source_key=source_key,
                source_artifact_sha256=source_artifact_sha256,
                source_transcript_sha256=source_transcript_sha256,
                source_id=source.source_id,
                source_content_hash=source.content_hash,
                provenance_supports=supports,
                provenance_locations=locations,
                query_text=query_text,
                retrieval_id=retrieval.retrieval_id,
                retrieval_hash=retrieval.retrieval_hash,
                packet_id=packet.packet_id,
                packet_hash=packet.packet_hash,
                packet_status=packet.packet_status,
                anchors=anchors,
            )
        )
    return tuple(reconstructions)


def _report(reconstructions: Sequence[PyramidSourceGroundedReconstruction]) -> PyramidSourceReconstructionReport:
    if not reconstructions:
        raise PyramidSourceReconstructionError("at least one reconstruction is required")
    curriculum_ids = {item.curriculum_id for item in reconstructions}
    source_keys = {item.source_key for item in reconstructions}
    if len(curriculum_ids) != 1 or len(source_keys) != 1:
        raise PyramidSourceReconstructionError("one reconstruction bundle must use one curriculum and source")
    counts = Counter(item.evidence_packet_status for item in reconstructions)
    return PyramidSourceReconstructionReport(
        contract=PYRAMID_SOURCE_RECONSTRUCTION_CONTRACT,
        version=PYRAMID_SOURCE_RECONSTRUCTION_VERSION,
        curriculum_id=next(iter(curriculum_ids)),
        source_key=next(iter(source_keys)),
        reconstruction_count=len(reconstructions),
        evidence_anchor_count=sum(len(item.evidence_anchors) for item in reconstructions),
        packet_status_counts=tuple(sorted(counts.items())),
        source_grounded_count=sum(item.source_grounded for item in reconstructions),
    )


def write_source_grounded_reconstruction_bundle(
    output_dir: str | Path,
    reconstructions: Sequence[PyramidSourceGroundedReconstruction],
) -> PyramidSourceReconstructionReport:
    canonical = tuple(validate_pyramid_source_grounded_reconstruction(item) for item in reconstructions)
    report = _report(canonical)
    output = Path(output_dir).resolve()
    if output.exists():
        raise PyramidSourceReconstructionError(f"output directory already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    try:
        recon_path = stage / "source_grounded_reconstructions.jsonl"
        with recon_path.open("w", encoding="utf-8") as handle:
            for item in canonical:
                handle.write(json.dumps(item.to_mapping(), ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        (stage / "reconstruction_report.json").write_text(
            json.dumps(report.to_mapping(), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(stage, output)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return report
