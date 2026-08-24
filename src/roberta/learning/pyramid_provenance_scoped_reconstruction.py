from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib.resources import files
import json
from pathlib import Path
from typing import Any, Mapping

from . import pyramid_source_reconstruction as _reconstruction
from . import retrieval as _retrieval


PDF_TRANSCRIPT_ALIGNMENT_CONTRACT = "roberta-source-pdf-transcript-alignment/v1"
PDF_TRANSCRIPT_ALIGNMENT_VERSION = "1.0.0"

_ALIGNMENT_RESOURCES = {
    "mastering_blockchain_4e_2023": (
        "source_alignments/mastering_blockchain_4e_2023.pdf-lines.v1.json"
    ),
}


@dataclass(frozen=True, slots=True)
class PdfTranscriptLineRange:
    pdf_page: int
    line_start: int
    line_end: int


@dataclass(frozen=True, slots=True)
class PdfTranscriptAlignment:
    contract: str
    version: str
    source_key: str
    source_artifact_sha256: str
    source_transcript_sha256: str
    original_page_count: int
    transcript_line_count: int
    mapping_basis: str
    alignment_method: str
    entries: tuple[PdfTranscriptLineRange, ...]
    alignment_hash: str


@dataclass(frozen=True, slots=True)
class ProvenanceScope:
    line_ranges: tuple[tuple[int, int], ...]
    scope_binding: str
    alignment_hash: str
    pdf_pages: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class ProvenanceScopedRetrievalFilters(_retrieval.RetrievalFilters):
    line_ranges: tuple[tuple[int, int], ...] = ()
    scope_binding: str = ""


_ORIGINAL_NORMALIZE_RETRIEVAL_FILTERS = _retrieval.normalize_retrieval_filters
_ORIGINAL_MATCHES_FILTERS = _retrieval._matches_filters
_ORIGINAL_QUERY_MATERIAL = _retrieval._query_material


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
        raise _reconstruction.PyramidSourceReconstructionError(
            "source-alignment material must be canonical JSON-compatible data"
        ) from exc


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _positive_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise _reconstruction.PyramidSourceReconstructionError(
            f"{name} must be a positive integer"
        )
    return value


def _normalized_line_ranges(
    value: object,
) -> tuple[tuple[int, int], ...]:
    if not isinstance(value, (tuple, list)):
        raise _reconstruction.PyramidSourceReconstructionError(
            "provenance line_ranges must be a tuple/list"
        )
    normalized: list[tuple[int, int]] = []
    for item in value:
        if not isinstance(item, (tuple, list)) or len(item) != 2:
            raise _reconstruction.PyramidSourceReconstructionError(
                "provenance line_ranges entries must be [line_start, line_end]"
            )
        start = _positive_int("provenance line_start", item[0])
        end = _positive_int("provenance line_end", item[1])
        if end < start:
            raise _reconstruction.PyramidSourceReconstructionError(
                "provenance line range end precedes start"
            )
        normalized.append((start, end))
    if not normalized:
        raise _reconstruction.PyramidSourceReconstructionError(
            "provenance line_ranges must not be empty"
        )
    normalized.sort()
    merged: list[tuple[int, int]] = []
    for start, end in normalized:
        if not merged or start > merged[-1][1] + 1:
            merged.append((start, end))
            continue
        previous_start, previous_end = merged[-1]
        merged[-1] = (previous_start, max(previous_end, end))
    return tuple(merged)


def _line_overlap(
    line_start: int,
    line_end: int,
    ranges: tuple[tuple[int, int], ...],
) -> bool:
    return any(
        line_end >= allowed_start and line_start <= allowed_end
        for allowed_start, allowed_end in ranges
    )


def _alignment_material(raw: Mapping[str, object]) -> dict[str, object]:
    required = {
        "contract",
        "version",
        "source_key",
        "source_artifact_sha256",
        "source_transcript_sha256",
        "original_page_count",
        "transcript_line_count",
        "mapping_basis",
        "alignment_method",
        "entries",
    }
    missing = sorted(required - set(raw))
    if missing:
        raise _reconstruction.PyramidSourceReconstructionError(
            f"source alignment is missing required fields: {missing}"
        )
    return {name: raw[name] for name in sorted(required)}


def validate_pdf_transcript_alignment(
    raw: object,
    *,
    expected_source_key: str,
    expected_source_artifact_sha256: str,
    expected_source_transcript_sha256: str,
    expected_original_page_count: int,
    expected_transcript_line_count: int,
) -> PdfTranscriptAlignment:
    if not isinstance(raw, Mapping):
        raise _reconstruction.PyramidSourceReconstructionError(
            "source alignment artifact must be a JSON object"
        )

    contract = _reconstruction._text("alignment.contract", raw.get("contract"))
    version = _reconstruction._text("alignment.version", raw.get("version"))
    if contract != PDF_TRANSCRIPT_ALIGNMENT_CONTRACT:
        raise _reconstruction.PyramidSourceReconstructionError(
            "unsupported PDF/transcript alignment contract"
        )
    if version != PDF_TRANSCRIPT_ALIGNMENT_VERSION:
        raise _reconstruction.PyramidSourceReconstructionError(
            "unsupported PDF/transcript alignment version"
        )

    source_key = _reconstruction._text(
        "alignment.source_key", raw.get("source_key")
    )
    source_artifact_sha256 = _reconstruction._text(
        "alignment.source_artifact_sha256",
        raw.get("source_artifact_sha256"),
    )
    source_transcript_sha256 = _reconstruction._text(
        "alignment.source_transcript_sha256",
        raw.get("source_transcript_sha256"),
    )
    original_page_count = _positive_int(
        "alignment.original_page_count", raw.get("original_page_count")
    )
    transcript_line_count = _positive_int(
        "alignment.transcript_line_count", raw.get("transcript_line_count")
    )
    mapping_basis = _reconstruction._text(
        "alignment.mapping_basis", raw.get("mapping_basis")
    )
    alignment_method = _reconstruction._text(
        "alignment.alignment_method", raw.get("alignment_method")
    )

    expected = (
        expected_source_key,
        expected_source_artifact_sha256,
        expected_source_transcript_sha256,
        expected_original_page_count,
        expected_transcript_line_count,
    )
    observed = (
        source_key,
        source_artifact_sha256,
        source_transcript_sha256,
        original_page_count,
        transcript_line_count,
    )
    if observed != expected:
        raise _reconstruction.PyramidSourceReconstructionError(
            "source alignment binding does not match the registered artifact/transcript"
        )

    raw_entries = raw.get("entries")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise _reconstruction.PyramidSourceReconstructionError(
            "source alignment entries must be a non-empty array"
        )
    entries: list[PdfTranscriptLineRange] = []
    seen_pages: set[int] = set()
    for item in raw_entries:
        if not isinstance(item, Mapping):
            raise _reconstruction.PyramidSourceReconstructionError(
                "source alignment entry must be an object"
            )
        page = _positive_int("alignment.pdf_page", item.get("pdf_page"))
        line_start = _positive_int(
            "alignment.line_start", item.get("line_start")
        )
        line_end = _positive_int("alignment.line_end", item.get("line_end"))
        if page > original_page_count:
            raise _reconstruction.PyramidSourceReconstructionError(
                "source alignment page exceeds registered PDF page count"
            )
        if line_end < line_start or line_end > transcript_line_count:
            raise _reconstruction.PyramidSourceReconstructionError(
                "source alignment transcript line range is invalid"
            )
        if page in seen_pages:
            raise _reconstruction.PyramidSourceReconstructionError(
                "source alignment contains duplicate PDF page mappings"
            )
        seen_pages.add(page)
        entries.append(
            PdfTranscriptLineRange(
                pdf_page=page,
                line_start=line_start,
                line_end=line_end,
            )
        )
    entries.sort(key=lambda item: item.pdf_page)

    alignment_hash = _reconstruction._text(
        "alignment.alignment_hash", raw.get("alignment_hash")
    )
    expected_hash = _hash(_alignment_material(raw))
    if alignment_hash != expected_hash:
        raise _reconstruction.PyramidSourceReconstructionError(
            "source alignment hash does not match alignment material"
        )

    return PdfTranscriptAlignment(
        contract=contract,
        version=version,
        source_key=source_key,
        source_artifact_sha256=source_artifact_sha256,
        source_transcript_sha256=source_transcript_sha256,
        original_page_count=original_page_count,
        transcript_line_count=transcript_line_count,
        mapping_basis=mapping_basis,
        alignment_method=alignment_method,
        entries=tuple(entries),
        alignment_hash=alignment_hash,
    )


def load_pdf_transcript_alignment(
    *,
    source_key: str,
    source_artifact_sha256: str,
    source_transcript_sha256: str,
    original_page_count: int,
    transcript_line_count: int,
) -> PdfTranscriptAlignment:
    resource_path = _ALIGNMENT_RESOURCES.get(source_key)
    if resource_path is None:
        raise _reconstruction.PyramidSourceReconstructionError(
            f"no verified PDF/transcript alignment is registered for {source_key}"
        )
    try:
        resource = files("roberta.learning")
        for part in resource_path.split("/"):
            resource = resource.joinpath(part)
        payload = resource.read_text(encoding="utf-8")
        raw = json.loads(payload)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _reconstruction.PyramidSourceReconstructionError(
            f"cannot load verified PDF/transcript alignment for {source_key}"
        ) from exc
    return validate_pdf_transcript_alignment(
        raw,
        expected_source_key=source_key,
        expected_source_artifact_sha256=source_artifact_sha256,
        expected_source_transcript_sha256=source_transcript_sha256,
        expected_original_page_count=original_page_count,
        expected_transcript_line_count=transcript_line_count,
    )


def resolve_provenance_scope(
    *,
    source_key: str,
    source_artifact_sha256: str,
    source_transcript_sha256: str,
    original_page_count: int | None,
    transcript_line_count: int,
    locations: tuple[object, ...],
) -> ProvenanceScope | None:
    pdf_pages: list[int] = []
    has_book_pages = False

    for locator in locations:
        locator_pdf_pages = tuple(getattr(locator, "pdf_pages", ()) or ())
        locator_book_pages = tuple(getattr(locator, "book_pages", ()) or ())
        if locator_pdf_pages:
            pdf_pages.extend(locator_pdf_pages)
        if locator_book_pages:
            has_book_pages = True

    if pdf_pages and has_book_pages:
        raise _reconstruction.PyramidSourceReconstructionError(
            "mixed PDF-page and printed-book provenance cannot be scoped safely"
        )
    if not pdf_pages:
        return None
    if original_page_count is None:
        raise _reconstruction.PyramidSourceReconstructionError(
            "PDF provenance requires a registered original PDF page count"
        )

    alignment = load_pdf_transcript_alignment(
        source_key=source_key,
        source_artifact_sha256=source_artifact_sha256,
        source_transcript_sha256=source_transcript_sha256,
        original_page_count=original_page_count,
        transcript_line_count=transcript_line_count,
    )
    by_page = {entry.pdf_page: entry for entry in alignment.entries}
    requested_pages = tuple(sorted(set(pdf_pages)))
    missing_pages = [page for page in requested_pages if page not in by_page]
    if missing_pages:
        raise _reconstruction.PyramidSourceReconstructionError(
            f"source provenance PDF pages have no verified transcript mapping: {missing_pages}"
        )

    line_ranges = _normalized_line_ranges(
        tuple(
            (by_page[page].line_start, by_page[page].line_end)
            for page in requested_pages
        )
    )
    location_material = [
        _reconstruction._locator_mapping(locator) for locator in locations
    ]
    scope_binding = _hash(
        {
            "alignment_hash": alignment.alignment_hash,
            "alignment_contract": alignment.contract,
            "alignment_version": alignment.version,
            "source_key": source_key,
            "provenance_locations": location_material,
            "pdf_pages": list(requested_pages),
            "line_ranges": [list(item) for item in line_ranges],
        }
    )
    return ProvenanceScope(
        line_ranges=line_ranges,
        scope_binding=scope_binding,
        alignment_hash=alignment.alignment_hash,
        pdf_pages=requested_pages,
    )


def _normalize_retrieval_filters(
    filters: _retrieval.RetrievalFilters | None = None,
) -> _retrieval.RetrievalFilters:
    if not isinstance(filters, ProvenanceScopedRetrievalFilters):
        return _ORIGINAL_NORMALIZE_RETRIEVAL_FILTERS(filters)

    base = _ORIGINAL_NORMALIZE_RETRIEVAL_FILTERS(
        _retrieval.RetrievalFilters(
            source_ids=filters.source_ids,
            document_ids=filters.document_ids,
            section_ids=filters.section_ids,
            source_authority_classes=filters.source_authority_classes,
            source_approval_statuses=filters.source_approval_statuses,
            chunk_kinds=filters.chunk_kinds,
        )
    )
    scope_binding = _reconstruction._text(
        "provenance scope binding", filters.scope_binding
    )
    return ProvenanceScopedRetrievalFilters(
        source_ids=base.source_ids,
        document_ids=base.document_ids,
        section_ids=base.section_ids,
        source_authority_classes=base.source_authority_classes,
        source_approval_statuses=base.source_approval_statuses,
        chunk_kinds=base.chunk_kinds,
        line_ranges=_normalized_line_ranges(filters.line_ranges),
        scope_binding=scope_binding,
    )


def _matches_filters(
    chunk: object,
    filters: _retrieval.RetrievalFilters,
) -> bool:
    if not _ORIGINAL_MATCHES_FILTERS(chunk, filters):
        return False
    if not isinstance(filters, ProvenanceScopedRetrievalFilters):
        return True
    return _line_overlap(
        chunk.line_start,
        chunk.line_end,
        filters.line_ranges,
    )


def _query_material(query: _retrieval.RetrievalQuery) -> dict[str, Any]:
    material = _ORIGINAL_QUERY_MATERIAL(query)
    filters = query.filters
    if isinstance(filters, ProvenanceScopedRetrievalFilters):
        material["filters"]["line_ranges"] = [
            list(item) for item in filters.line_ranges
        ]
        material["filters"]["scope_binding"] = filters.scope_binding
    return material


def _build_source_grounded_reconstructions(
    *,
    curriculum_dir: str | Path,
    handoffs_path: str | Path,
    checkpoints_dir: str | Path,
    source_transcript_path: str | Path | None = None,
    top_k: int = 5,
) -> tuple[_reconstruction.PyramidSourceGroundedReconstruction, ...]:
    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k <= 0:
        raise _reconstruction.PyramidSourceReconstructionError(
            "top_k must be a positive integer"
        )
    manifest, exercises = _reconstruction.validate_package(curriculum_dir)
    handoffs = _reconstruction.load_pyramid_learning_handoffs_jsonl(
        handoffs_path
    )
    by_id = {item.exercise_id: item for item in exercises}
    if len(by_id) != len(exercises):
        raise _reconstruction.PyramidSourceReconstructionError(
            "validated curriculum contains duplicate exercise ids"
        )

    declaration = manifest.get("source_provenance")
    if not isinstance(declaration, Mapping):
        raise _reconstruction.PyramidSourceReconstructionError(
            "validated curriculum must declare source_provenance"
        )
    source_key = _reconstruction._text(
        "source_provenance.source_key", declaration.get("source_key")
    )
    provenance_file = _reconstruction._text(
        "source_provenance.file", declaration.get("file")
    )
    source_artifact_sha256 = _reconstruction._text(
        "source_provenance.source_artifact_sha256",
        declaration.get("source_artifact_sha256"),
    )
    source_transcript_sha256 = _reconstruction._text(
        "source_provenance.source_transcript_sha256",
        declaration.get("source_transcript_sha256"),
    )
    provenance_rows = _reconstruction.load_source_provenance_jsonl(
        Path(curriculum_dir) / provenance_file,
        expected_source_key=source_key,
        expected_exercise_ids=set(by_id),
    )
    provenance_by_id = {
        str(row["exercise_id"]): row for row in provenance_rows
    }

    checkpoint_root = Path(checkpoints_dir)
    if not checkpoint_root.is_dir():
        raise _reconstruction.PyramidSourceReconstructionError(
            "checkpoint directory does not exist"
        )

    for handoff in handoffs:
        exercise = by_id.get(handoff.exercise_id)
        if exercise is None:
            raise _reconstruction.PyramidSourceReconstructionError(
                f"handoff exercise {handoff.exercise_id!r} is absent from validated curriculum"
            )
        _reconstruction._validate_curriculum_binding(handoff, exercise)
        if source_key not in handoff.source_refs:
            raise _reconstruction.PyramidSourceReconstructionError(
                f"handoff {handoff.exercise_id} does not reference canonical provenance source {source_key}"
            )
        _reconstruction._checkpoint_grade_binding(handoff, checkpoint_root)

    spec = _reconstruction.get_user_source_spec(source_key)
    if (
        spec.original_sha256 != source_artifact_sha256
        or spec.transcript_sha256 != source_transcript_sha256
    ):
        raise _reconstruction.PyramidSourceReconstructionError(
            "curriculum source digests do not match registered Learning System source"
        )
    external_transcript: bytes | None = None
    if source_transcript_path is not None:
        try:
            external_transcript = Path(source_transcript_path).read_bytes()
        except OSError as exc:
            raise _reconstruction.PyramidSourceReconstructionError(
                f"cannot read source transcript: {exc}"
            ) from exc

    store = _reconstruction.InMemorySourceStore()
    try:
        ingestion = _reconstruction.ingest_user_source(
            source_key,
            store=store,
            external_transcript=external_transcript,
        )
    except _reconstruction.SourceIngestionError as exc:
        raise _reconstruction.PyramidSourceReconstructionError(
            f"approved source transcript failed integrity validation for {source_key}"
        ) from exc
    source = ingestion.record
    if (
        source.content_hash != source_transcript_sha256
        or source.approval_status != "approved"
    ):
        raise _reconstruction.PyramidSourceReconstructionError(
            "ingested source is not the exact approved transcript"
        )

    artifact = store.get_artifact(source.artifact_ref)
    if artifact is None:
        raise _reconstruction.PyramidSourceReconstructionError(
            "ingested source transcript artifact is unavailable"
        )
    try:
        transcript_line_count = len(artifact.decode("utf-8").splitlines())
    except UnicodeDecodeError as exc:
        raise _reconstruction.PyramidSourceReconstructionError(
            "ingested source transcript is not valid UTF-8"
        ) from exc

    parsed = _reconstruction.parse_markdown_structure(
        store=store, source_id=source.source_id
    )
    chunked = _reconstruction.chunk_parsed_document(
        store=store, parsed=parsed
    )
    indexed = _reconstruction.build_evidence_index(
        store=store,
        chunked=chunked,
        embedding_provider=None,
    )
    corpus = (
        _reconstruction.RetrievalCorpusItem(
            chunked=chunked,
            indexed=indexed,
        ),
    )

    reconstructions: list[
        _reconstruction.PyramidSourceGroundedReconstruction
    ] = []
    for handoff in handoffs:
        supports, locations = _reconstruction._provenance_for_exercise(
            provenance_by_id[handoff.exercise_id]
        )
        scope = resolve_provenance_scope(
            source_key=source_key,
            source_artifact_sha256=source_artifact_sha256,
            source_transcript_sha256=source_transcript_sha256,
            original_page_count=spec.original_page_count,
            transcript_line_count=transcript_line_count,
            locations=locations,
        )

        if scope is None:
            filters: _retrieval.RetrievalFilters = _retrieval.RetrievalFilters(
                source_ids=(source.source_id,),
                source_approval_statuses=("approved",),
            )
        else:
            eligible_chunks = tuple(
                chunk
                for chunk in chunked.chunks
                if chunk.source_id == source.source_id
                and chunk.source_approval_status == "approved"
                and _line_overlap(
                    chunk.line_start,
                    chunk.line_end,
                    scope.line_ranges,
                )
            )
            if not eligible_chunks:
                raise _reconstruction.PyramidSourceReconstructionError(
                    f"no canonical source chunks overlap declared provenance for {handoff.exercise_id}"
                )
            filters = ProvenanceScopedRetrievalFilters(
                source_ids=(source.source_id,),
                source_approval_statuses=("approved",),
                line_ranges=scope.line_ranges,
                scope_binding=scope.scope_binding,
            )

        query_text = _reconstruction._query_text(handoff)
        retrieval = _retrieval.retrieve_evidence(
            store=store,
            corpus=corpus,
            text=query_text,
            filters=filters,
            top_k=top_k,
            candidate_limit=max(50, top_k),
        )
        packet = _reconstruction.build_evidence_packet(
            store=store,
            corpus=corpus,
            result=retrieval,
        )
        if packet.insufficient_evidence or not packet.evidence_anchors:
            raise _reconstruction.PyramidSourceReconstructionError(
                f"canonical source retrieval was insufficient for {handoff.exercise_id}"
            )
        anchors = tuple(
            _reconstruction._evidence_anchor(item)
            for item in packet.evidence_anchors
        )
        if any(
            item.source_id != source.source_id
            or item.source_approval_status != "approved"
            for item in anchors
        ):
            raise _reconstruction.PyramidSourceReconstructionError(
                "retrieval escaped canonical approved source filter"
            )
        if scope is not None and any(
            not _line_overlap(
                item.line_start,
                item.line_end,
                scope.line_ranges,
            )
            for item in anchors
        ):
            raise _reconstruction.PyramidSourceReconstructionError(
                f"retrieval escaped declared source provenance for {handoff.exercise_id}"
            )

        reconstructions.append(
            _reconstruction._make_reconstruction(
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


def install_provenance_scoped_reconstruction() -> None:
    if getattr(
        _reconstruction,
        "_provenance_scoped_reconstruction_installed",
        False,
    ):
        return

    _retrieval.normalize_retrieval_filters = _normalize_retrieval_filters
    _retrieval._matches_filters = _matches_filters
    _retrieval._query_material = _query_material
    _reconstruction.build_source_grounded_reconstructions = (
        _build_source_grounded_reconstructions
    )
    _reconstruction._provenance_scoped_reconstruction_installed = True
