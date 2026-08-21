"""Deterministic evidence retrieval foundation for the Roberta Learning System.

Phase 5 retrieves exact canonical evidence chunks from validated Phase 4 indexes.
Retrieval scores are relevance metadata only. They are never source authority,
truth, risk, live-state verification, or execution authorization.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import math
import re
import unicodedata
from typing import Any

from .chunking import ChunkedDocument, EvidenceChunk
from .indexing import (
    INDEX_CONTRACT,
    LEXICAL_ANALYZER_CONTRACT,
    EmbeddingIndexEntry,
    IndexedDocument,
    LexicalIndexEntry,
    build_evidence_index,
)
from .source_ingestion import SourceStore


RETRIEVAL_CONTRACT = "evidence-retrieval/v1"
FUSION_CONTRACT = "reciprocal-rank-fusion/v1"
_DEFAULT_RETRIEVAL_VERSION = "1.0.0"
_DEFAULT_RRF_K = 60
_DEFAULT_TOP_K = 5
_DEFAULT_CANDIDATE_LIMIT = 50
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_ALLOWED_EMBEDDING_STATUSES = frozenset({"ok", "error", "unavailable"})


class RetrievalError(ValueError):
    """Raised when evidence retrieval cannot be performed safely."""


@dataclass(frozen=True, slots=True)
class RetrievalFilters:
    source_ids: tuple[str, ...] = ()
    document_ids: tuple[str, ...] = ()
    section_ids: tuple[str | None, ...] = ()
    source_authority_classes: tuple[str, ...] = ()
    source_approval_statuses: tuple[str, ...] = ()
    chunk_kinds: tuple[str, ...] = ()

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class QueryVector:
    provider_id: str
    model_id: str
    model_version: str
    dimension: int
    vector: tuple[float, ...]
    vector_fingerprint: str

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class RetrievalQuery:
    query_id: str
    text: str
    normalized_tokens: tuple[str, ...]
    filters: RetrievalFilters
    top_k: int
    candidate_limit: int
    retrieval_contract: str
    retrieval_version: str
    fusion_contract: str
    rrf_k: int
    lexical_analyzer_contract: str
    lexical_analyzer_version: str
    query_vector: QueryVector | None

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class RetrievalCorpusItem:
    chunked: ChunkedDocument
    indexed: IndexedDocument

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class RetrievalCandidate:
    chunk_id: str
    source_id: str
    document_id: str
    section_id: str | None
    block_ids: tuple[str, ...]
    structural_path: tuple[str, ...]
    chunk_kind: str
    chunk_order: int
    line_start: int
    line_end: int
    text: str
    content_hash: str
    source_authority_class: str
    source_approval_status: str
    lexical_rank: int | None
    lexical_matched_terms: tuple[str, ...]
    lexical_matched_term_count: int
    lexical_matched_occurrences: int
    lexical_phrase_match: bool
    vector_rank: int | None
    vector_similarity: float | None
    fusion_rank: int
    fusion_score_numerator: int
    fusion_score_denominator: int
    channel_count: int

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    retrieval_id: str
    retrieval_hash: str
    query: RetrievalQuery
    corpus_index_ids: tuple[str, ...]
    candidates: tuple[RetrievalCandidate, ...]
    diversity_deferred_chunk_ids: tuple[str, ...]
    vector_eligible_index_ids: tuple[str, ...]
    vector_ineligible_index_ids: tuple[str, ...]
    status: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class RetrievalMetrics:
    recall_at_k: float | None
    precision_at_k: float | None
    reciprocal_rank: float | None
    ndcg_at_k: float | None
    evidence_coverage: float | None
    redundancy_rate: float
    source_diversity: float
    filter_correct: bool
    retrieved_count: int
    relevant_count: int
    hit_count: int

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(slots=True)
class _CandidateState:
    chunk: EvidenceChunk
    lexical_rank: int | None = None
    lexical_matched_terms: tuple[str, ...] = ()
    lexical_matched_term_count: int = 0
    lexical_matched_occurrences: int = 0
    lexical_phrase_match: bool = False
    vector_rank: int | None = None
    vector_similarity: float | None = None
    fusion_rank: int = 0
    fusion_score: Fraction = Fraction(0, 1)


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
        raise RetrievalError(
            "retrieval material must be canonical JSON-compatible data"
        ) from exc


def _content_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}{digest}"


def _normalized_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise RetrievalError(f"{name} must be a normalized non-empty string")
    return value


def _positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RetrievalError(f"{name} must be a positive integer")
    return value


def _normalize_text_filter(name: str, values: Any) -> tuple[str, ...]:
    if not isinstance(values, (tuple, list)):
        raise RetrievalError(f"{name} must be a tuple/list")
    normalized = {_normalized_text(name, value) for value in values}
    return tuple(sorted(normalized))


def _normalize_section_filter(values: Any) -> tuple[str | None, ...]:
    if not isinstance(values, (tuple, list)):
        raise RetrievalError("section_ids must be a tuple/list")
    normalized: set[str | None] = set()
    for value in values:
        if value is None:
            normalized.add(None)
        else:
            normalized.add(_normalized_text("section_id", value))
    return tuple(sorted(normalized, key=lambda value: (value is not None, value or "")))


def normalize_retrieval_filters(
    filters: RetrievalFilters | None = None,
) -> RetrievalFilters:
    """Return canonical order-independent exact-match retrieval filters."""

    value = filters if filters is not None else RetrievalFilters()
    if not isinstance(value, RetrievalFilters):
        raise RetrievalError("filters must be RetrievalFilters")
    return RetrievalFilters(
        source_ids=_normalize_text_filter("source_id", value.source_ids),
        document_ids=_normalize_text_filter("document_id", value.document_ids),
        section_ids=_normalize_section_filter(value.section_ids),
        source_authority_classes=_normalize_text_filter(
            "source_authority_class", value.source_authority_classes
        ),
        source_approval_statuses=_normalize_text_filter(
            "source_approval_status", value.source_approval_statuses
        ),
        chunk_kinds=_normalize_text_filter("chunk_kind", value.chunk_kinds),
    )


def _lexical_tokens(text: str) -> tuple[str, ...]:
    if not isinstance(text, str):
        raise RetrievalError("query text must be a string")
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return tuple(match.group(0) for match in _TOKEN_RE.finditer(normalized))


def _validate_numeric_vector(
    *, vector: Any, dimension: int, name: str
) -> tuple[float, ...]:
    if not isinstance(vector, (tuple, list)):
        raise RetrievalError(f"{name} must be a tuple/list of finite numbers")
    if len(vector) != dimension:
        raise RetrievalError(f"{name} dimension does not match declared dimension")
    values: list[float] = []
    for item in vector:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            raise RetrievalError(f"{name} elements must be numeric")
        numeric = float(item)
        if not math.isfinite(numeric):
            raise RetrievalError(f"{name} elements must be finite")
        values.append(numeric)
    return tuple(values)


def make_query_vector(
    *,
    provider_id: str,
    model_id: str,
    model_version: str,
    dimension: int,
    vector: tuple[float, ...] | list[float],
) -> QueryVector:
    """Create a validated query vector bound to one exact embedding space."""

    normalized_dimension = _positive_int("dimension", dimension)
    validated = _validate_numeric_vector(
        vector=vector, dimension=normalized_dimension, name="query vector"
    )
    norm = math.sqrt(sum(value * value for value in validated))
    if norm == 0.0:
        raise RetrievalError("query vector must have non-zero magnitude")
    fingerprint = hashlib.sha256(
        _canonical_json(list(validated)).encode("utf-8")
    ).hexdigest()
    return QueryVector(
        provider_id=_normalized_text("provider_id", provider_id),
        model_id=_normalized_text("model_id", model_id),
        model_version=_normalized_text("model_version", model_version),
        dimension=normalized_dimension,
        vector=validated,
        vector_fingerprint=fingerprint,
    )


def _validate_query_vector(value: Any) -> QueryVector:
    if not isinstance(value, QueryVector):
        raise RetrievalError("query_vector must be QueryVector")
    canonical = make_query_vector(
        provider_id=value.provider_id,
        model_id=value.model_id,
        model_version=value.model_version,
        dimension=value.dimension,
        vector=value.vector,
    )
    if canonical.vector_fingerprint != value.vector_fingerprint:
        raise RetrievalError("query vector fingerprint does not match vector")
    return canonical


def _lexical_entry_material(entry: LexicalIndexEntry) -> dict[str, Any]:
    return {
        "lexical_entry_id": entry.lexical_entry_id,
        "chunk_id": entry.chunk_id,
        "source_id": entry.source_id,
        "document_id": entry.document_id,
        "section_id": entry.section_id,
        "structural_path": list(entry.structural_path),
        "chunk_kind": entry.chunk_kind,
        "line_start": entry.line_start,
        "line_end": entry.line_end,
        "source_authority_class": entry.source_authority_class,
        "source_approval_status": entry.source_approval_status,
        "chunk_content_hash": entry.chunk_content_hash,
        "index_contract": entry.index_contract,
        "index_version": entry.index_version,
        "lexical_analyzer_contract": entry.lexical_analyzer_contract,
        "lexical_analyzer_version": entry.lexical_analyzer_version,
        "tokens": list(entry.tokens),
        "token_count": entry.token_count,
        "unique_term_count": entry.unique_term_count,
    }


def _embedding_entry_material(entry: EmbeddingIndexEntry) -> dict[str, Any]:
    return {
        "embedding_entry_id": entry.embedding_entry_id,
        "chunk_id": entry.chunk_id,
        "source_id": entry.source_id,
        "document_id": entry.document_id,
        "section_id": entry.section_id,
        "structural_path": list(entry.structural_path),
        "chunk_kind": entry.chunk_kind,
        "line_start": entry.line_start,
        "line_end": entry.line_end,
        "source_authority_class": entry.source_authority_class,
        "source_approval_status": entry.source_approval_status,
        "chunk_content_hash": entry.chunk_content_hash,
        "index_contract": entry.index_contract,
        "index_version": entry.index_version,
        "provider_id": entry.provider_id,
        "model_id": entry.model_id,
        "model_version": entry.model_version,
        "dimension": entry.dimension,
        "status": entry.status,
        "vector_fingerprint": entry.vector_fingerprint,
        "warnings": list(entry.warnings),
        "error": entry.error,
    }


def _entry_content_id(prefix: str, material_with_id: dict[str, Any], id_field: str) -> str:
    material = dict(material_with_id)
    material.pop(id_field, None)
    return _content_id(prefix, material)


def _validate_indexed_item(
    *, store: SourceStore, item: RetrievalCorpusItem
) -> RetrievalCorpusItem:
    if not isinstance(item, RetrievalCorpusItem):
        raise RetrievalError("corpus items must be RetrievalCorpusItem")
    if not isinstance(item.chunked, ChunkedDocument):
        raise RetrievalError("corpus chunked value must be ChunkedDocument")
    if not isinstance(item.indexed, IndexedDocument):
        raise RetrievalError("corpus indexed value must be IndexedDocument")

    manifest = item.indexed.manifest
    if manifest.index_contract != INDEX_CONTRACT:
        raise RetrievalError(
            f"unsupported Phase 4 index_contract {manifest.index_contract!r}"
        )
    if manifest.lexical_analyzer_contract != LEXICAL_ANALYZER_CONTRACT:
        raise RetrievalError(
            "unsupported Phase 4 lexical_analyzer_contract "
            f"{manifest.lexical_analyzer_contract!r}"
        )

    try:
        lexical_rebuild = build_evidence_index(
            store=store,
            chunked=item.chunked,
            index_contract=manifest.index_contract,
            index_version=manifest.index_version,
            lexical_analyzer_contract=manifest.lexical_analyzer_contract,
            lexical_analyzer_version=manifest.lexical_analyzer_version,
            embedding_provider=None,
        )
    except Exception as exc:
        raise RetrievalError("canonical Phase 4 lexical reconstruction failed") from exc

    canonical_chunked = item.chunked
    rebuilt_manifest = lexical_rebuild.manifest
    if (
        manifest.source_id != rebuilt_manifest.source_id
        or manifest.document_id != rebuilt_manifest.document_id
        or manifest.chunk_set_id != rebuilt_manifest.chunk_set_id
        or manifest.index_version != rebuilt_manifest.index_version
        or manifest.lexical_analyzer_version
        != rebuilt_manifest.lexical_analyzer_version
    ):
        raise RetrievalError("Phase 4 index manifest does not match canonical chunks")
    if item.indexed.lexical_entries != lexical_rebuild.lexical_entries:
        raise RetrievalError("Phase 4 lexical index does not match canonical chunks")
    if manifest.lexical_entry_ids != tuple(
        entry.lexical_entry_id for entry in item.indexed.lexical_entries
    ):
        raise RetrievalError("Phase 4 lexical entry ids do not match manifest")

    chunks_by_id = {chunk.chunk_id: chunk for chunk in canonical_chunked.chunks}
    if len(chunks_by_id) != len(canonical_chunked.chunks):
        raise RetrievalError("canonical chunk ids must be unique")

    embedding_entries = item.indexed.embedding_entries
    provider_fields = (
        manifest.embedding_provider_id,
        manifest.embedding_model_id,
        manifest.embedding_model_version,
        manifest.embedding_dimension,
    )
    provider_configured = any(field is not None for field in provider_fields)

    if not embedding_entries:
        if provider_configured:
            raise RetrievalError("embedding provider metadata exists without entries")
        if manifest.embedding_entry_ids:
            raise RetrievalError("embedding entry ids exist without entries")
        if (
            manifest.embedding_ok_count
            or manifest.embedding_error_count
            or manifest.embedding_unavailable_count
        ):
            raise RetrievalError("embedding counts exist without entries")
        if manifest.status != "lexical_only":
            raise RetrievalError("index without embeddings must be lexical_only")
        if manifest.warnings or manifest.errors:
            raise RetrievalError("lexical-only index must not contain embedding diagnostics")
        provider_info: dict[str, Any] | None = None
    else:
        if any(field is None for field in provider_fields):
            raise RetrievalError("embedding entries require complete provider metadata")
        provider_id = _normalized_text(
            "embedding_provider_id", manifest.embedding_provider_id
        )
        model_id = _normalized_text("embedding_model_id", manifest.embedding_model_id)
        model_version = _normalized_text(
            "embedding_model_version", manifest.embedding_model_version
        )
        dimension = _positive_int(
            "embedding_dimension", manifest.embedding_dimension
        )
        provider_info = {
            "provider_id": provider_id,
            "model_id": model_id,
            "model_version": model_version,
            "dimension": dimension,
        }
        if len(embedding_entries) != len(canonical_chunked.chunks):
            raise RetrievalError("embedding index must contain one entry per canonical chunk")
        if tuple(entry.chunk_id for entry in embedding_entries) != tuple(
            chunk.chunk_id for chunk in canonical_chunked.chunks
        ):
            raise RetrievalError("embedding entry order does not match canonical chunks")
        if tuple(entry.embedding_entry_id for entry in embedding_entries) != (
            manifest.embedding_entry_ids
        ):
            raise RetrievalError("embedding entry ids do not match manifest")

    manifest_warnings: list[str] = []
    manifest_errors: list[str] = []
    ok_count = 0
    error_count = 0
    unavailable_count = 0

    for entry in embedding_entries:
        if provider_info is None:
            raise RetrievalError("embedding entry exists without provider metadata")
        chunk = chunks_by_id.get(entry.chunk_id)
        if chunk is None:
            raise RetrievalError("embedding entry references unknown canonical chunk")
        if (
            entry.source_id != chunk.source_id
            or entry.document_id != chunk.document_id
            or entry.section_id != chunk.section_id
            or entry.structural_path != chunk.structural_path
            or entry.chunk_kind != chunk.kind
            or entry.line_start != chunk.line_start
            or entry.line_end != chunk.line_end
            or entry.source_authority_class != chunk.source_authority_class
            or entry.source_approval_status != chunk.source_approval_status
            or entry.chunk_content_hash != chunk.content_hash
        ):
            raise RetrievalError("embedding entry provenance does not match canonical chunk")
        if (
            entry.index_contract != manifest.index_contract
            or entry.index_version != manifest.index_version
            or entry.provider_id != provider_info["provider_id"]
            or entry.model_id != provider_info["model_id"]
            or entry.model_version != provider_info["model_version"]
            or entry.dimension != provider_info["dimension"]
        ):
            raise RetrievalError("embedding entry metadata does not match manifest")

        if entry.status not in _ALLOWED_EMBEDDING_STATUSES:
            raise RetrievalError(f"unsupported embedding status {entry.status!r}")
        for warning in entry.warnings:
            _normalized_text("embedding warning", warning)

        if entry.status == "ok":
            ok_count += 1
            if entry.error is not None:
                raise RetrievalError("ok embedding entry must not contain error")
            vector = _validate_numeric_vector(
                vector=entry.vector,
                dimension=entry.dimension,
                name="embedding vector",
            )
            fingerprint = hashlib.sha256(
                _canonical_json(list(vector)).encode("utf-8")
            ).hexdigest()
            if entry.vector_fingerprint != fingerprint:
                raise RetrievalError("embedding vector fingerprint mismatch")
        else:
            if entry.vector is not None or entry.vector_fingerprint is not None:
                raise RetrievalError(
                    "failed/unavailable embedding entry must not contain vector"
                )
            _normalized_text("embedding error", entry.error)
            if entry.status == "error":
                error_count += 1
            else:
                unavailable_count += 1

        expected_id = _entry_content_id(
            "emb_",
            _embedding_entry_material(entry),
            "embedding_entry_id",
        )
        if entry.embedding_entry_id != expected_id:
            raise RetrievalError("embedding entry id is not content-addressed correctly")

        for warning in entry.warnings:
            message = f"embedding_warning:chunk={entry.chunk_id}:{warning}"
            if message not in manifest_warnings:
                manifest_warnings.append(message)
        if entry.status == "error":
            message = f"embedding_error:chunk={entry.chunk_id}:{entry.error}"
            if message not in manifest_errors:
                manifest_errors.append(message)
        elif entry.status == "unavailable":
            message = f"embedding_unavailable:chunk={entry.chunk_id}:{entry.error}"
            if message not in manifest_warnings:
                manifest_warnings.append(message)

    if (
        manifest.embedding_ok_count != ok_count
        or manifest.embedding_error_count != error_count
        or manifest.embedding_unavailable_count != unavailable_count
    ):
        raise RetrievalError("embedding status counts do not match manifest")

    if provider_info is None:
        expected_status = "lexical_only"
    elif error_count or unavailable_count:
        expected_status = "partial"
    else:
        expected_status = "complete"
    if manifest.status != expected_status:
        raise RetrievalError("index status does not match embedding state")
    if manifest.warnings != tuple(manifest_warnings):
        raise RetrievalError("index warnings do not match embedding state")
    if manifest.errors != tuple(manifest_errors):
        raise RetrievalError("index errors do not match embedding state")

    manifest_material = {
        "source_id": manifest.source_id,
        "document_id": manifest.document_id,
        "chunk_set_id": manifest.chunk_set_id,
        "index_contract": manifest.index_contract,
        "index_version": manifest.index_version,
        "lexical_analyzer_contract": manifest.lexical_analyzer_contract,
        "lexical_analyzer_version": manifest.lexical_analyzer_version,
        "lexical_entries": [
            _lexical_entry_material(entry) for entry in item.indexed.lexical_entries
        ],
        "embedding_provider": provider_info,
        "embedding_entries": [
            _embedding_entry_material(entry) for entry in embedding_entries
        ],
        "embedding_ok_count": ok_count,
        "embedding_error_count": error_count,
        "embedding_unavailable_count": unavailable_count,
        "status": expected_status,
        "warnings": manifest_warnings,
        "errors": manifest_errors,
    }
    expected_hash = hashlib.sha256(
        _canonical_json(manifest_material).encode("utf-8")
    ).hexdigest()
    if manifest.index_hash != expected_hash or manifest.index_id != f"idx_{expected_hash}":
        raise RetrievalError("Phase 4 index manifest hash/id is invalid")

    return item


def _matches_filters(chunk: EvidenceChunk, filters: RetrievalFilters) -> bool:
    return (
        (not filters.source_ids or chunk.source_id in filters.source_ids)
        and (not filters.document_ids or chunk.document_id in filters.document_ids)
        and (not filters.section_ids or chunk.section_id in filters.section_ids)
        and (
            not filters.source_authority_classes
            or chunk.source_authority_class in filters.source_authority_classes
        )
        and (
            not filters.source_approval_statuses
            or chunk.source_approval_status in filters.source_approval_statuses
        )
        and (not filters.chunk_kinds or chunk.kind in filters.chunk_kinds)
    )


def _phrase_match(query_tokens: tuple[str, ...], tokens: tuple[str, ...]) -> bool:
    if not query_tokens or len(query_tokens) > len(tokens):
        return False
    width = len(query_tokens)
    return any(
        tokens[index : index + width] == query_tokens
        for index in range(len(tokens) - width + 1)
    )


def _cosine_similarity(left: tuple[float, ...], right: tuple[float, ...]) -> float | None:
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return None
    value = sum(a * b for a, b in zip(left, right, strict=True)) / (
        left_norm * right_norm
    )
    return max(-1.0, min(1.0, value))


def _query_material(query: RetrievalQuery) -> dict[str, Any]:
    vector = query.query_vector
    return {
        "text": query.text,
        "normalized_tokens": list(query.normalized_tokens),
        "filters": {
            "source_ids": list(query.filters.source_ids),
            "document_ids": list(query.filters.document_ids),
            "section_ids": list(query.filters.section_ids),
            "source_authority_classes": list(
                query.filters.source_authority_classes
            ),
            "source_approval_statuses": list(
                query.filters.source_approval_statuses
            ),
            "chunk_kinds": list(query.filters.chunk_kinds),
        },
        "top_k": query.top_k,
        "candidate_limit": query.candidate_limit,
        "retrieval_contract": query.retrieval_contract,
        "retrieval_version": query.retrieval_version,
        "fusion_contract": query.fusion_contract,
        "rrf_k": query.rrf_k,
        "lexical_analyzer_contract": query.lexical_analyzer_contract,
        "lexical_analyzer_version": query.lexical_analyzer_version,
        "query_vector": (
            {
                "provider_id": vector.provider_id,
                "model_id": vector.model_id,
                "model_version": vector.model_version,
                "dimension": vector.dimension,
                "vector_fingerprint": vector.vector_fingerprint,
            }
            if vector is not None
            else None
        ),
    }


def _is_local_neighbor(left: EvidenceChunk, right: EvidenceChunk) -> bool:
    return (
        left.source_id == right.source_id
        and left.document_id == right.document_id
        and left.section_id == right.section_id
        and abs(left.order - right.order) <= 1
    )


def _is_candidate_neighbor(
    left: RetrievalCandidate, right: RetrievalCandidate
) -> bool:
    return (
        left.source_id == right.source_id
        and left.document_id == right.document_id
        and left.section_id == right.section_id
        and abs(left.chunk_order - right.chunk_order) <= 1
    )


def retrieve_evidence(
    *,
    store: SourceStore,
    corpus: tuple[RetrievalCorpusItem, ...] | list[RetrievalCorpusItem],
    text: str,
    filters: RetrievalFilters | None = None,
    top_k: int = _DEFAULT_TOP_K,
    candidate_limit: int = _DEFAULT_CANDIDATE_LIMIT,
    query_vector: QueryVector | None = None,
    retrieval_contract: str = RETRIEVAL_CONTRACT,
    retrieval_version: str = _DEFAULT_RETRIEVAL_VERSION,
    fusion_contract: str = FUSION_CONTRACT,
    rrf_k: int = _DEFAULT_RRF_K,
) -> RetrievalResult:
    """Retrieve canonical evidence from validated Phase 4 indexes."""

    if not isinstance(corpus, (tuple, list)) or not corpus:
        raise RetrievalError("corpus must contain at least one RetrievalCorpusItem")

    normalized_retrieval_contract = _normalized_text(
        "retrieval_contract", retrieval_contract
    )
    if normalized_retrieval_contract != RETRIEVAL_CONTRACT:
        raise RetrievalError(
            f"unsupported retrieval_contract {normalized_retrieval_contract!r}"
        )
    normalized_retrieval_version = _normalized_text(
        "retrieval_version", retrieval_version
    )
    normalized_fusion_contract = _normalized_text("fusion_contract", fusion_contract)
    if normalized_fusion_contract != FUSION_CONTRACT:
        raise RetrievalError(
            f"unsupported fusion_contract {normalized_fusion_contract!r}"
        )
    normalized_rrf_k = _positive_int("rrf_k", rrf_k)
    normalized_top_k = _positive_int("top_k", top_k)
    normalized_candidate_limit = _positive_int("candidate_limit", candidate_limit)
    if normalized_candidate_limit < normalized_top_k:
        raise RetrievalError("candidate_limit must be greater than or equal to top_k")
    if not isinstance(text, str) or not text.strip():
        raise RetrievalError("query text must contain non-whitespace text")
    normalized_text = text
    normalized_filters = normalize_retrieval_filters(filters)
    normalized_vector = (
        _validate_query_vector(query_vector) if query_vector is not None else None
    )

    validated_items = [
        _validate_indexed_item(store=store, item=item) for item in corpus
    ]
    validated_items.sort(key=lambda item: item.indexed.manifest.index_id)

    index_ids = tuple(item.indexed.manifest.index_id for item in validated_items)
    if len(set(index_ids)) != len(index_ids):
        raise RetrievalError("corpus index ids must be unique")

    analyzer_contracts = {
        item.indexed.manifest.lexical_analyzer_contract for item in validated_items
    }
    analyzer_versions = {
        item.indexed.manifest.lexical_analyzer_version for item in validated_items
    }
    if len(analyzer_contracts) != 1 or len(analyzer_versions) != 1:
        raise RetrievalError(
            "all corpus indexes must use one lexical analyzer contract/version in v1"
        )
    analyzer_contract = next(iter(analyzer_contracts))
    analyzer_version = next(iter(analyzer_versions))
    if analyzer_contract != LEXICAL_ANALYZER_CONTRACT:
        raise RetrievalError("unsupported corpus lexical analyzer contract")

    normalized_tokens = _lexical_tokens(normalized_text)
    if not normalized_tokens and normalized_vector is None:
        raise RetrievalError(
            "query normalization produced no lexical tokens and no query vector was supplied"
        )

    chunk_by_id: dict[str, EvidenceChunk] = {}
    lexical_by_chunk: dict[str, LexicalIndexEntry] = {}
    embedding_by_chunk: dict[str, EmbeddingIndexEntry] = {}
    index_for_chunk: dict[str, str] = {}

    for item in validated_items:
        chunks = {chunk.chunk_id: chunk for chunk in item.chunked.chunks}
        for chunk in item.chunked.chunks:
            if chunk.chunk_id in chunk_by_id:
                raise RetrievalError(
                    "duplicate canonical chunk_id across corpus would inflate retrieval"
                )
            chunk_by_id[chunk.chunk_id] = chunk
            index_for_chunk[chunk.chunk_id] = item.indexed.manifest.index_id
        for entry in item.indexed.lexical_entries:
            if entry.chunk_id not in chunks:
                raise RetrievalError("lexical entry references unknown chunk")
            lexical_by_chunk[entry.chunk_id] = entry
        for entry in item.indexed.embedding_entries:
            if entry.chunk_id not in chunks:
                raise RetrievalError("embedding entry references unknown chunk")
            embedding_by_chunk[entry.chunk_id] = entry

    vector_eligible: list[str] = []
    vector_ineligible: list[str] = []
    warnings: list[str] = []

    active_index_ids: set[str] = set()
    for chunk_id, chunk in chunk_by_id.items():
        if _matches_filters(chunk, normalized_filters):
            active_index_ids.add(index_for_chunk[chunk_id])

    if normalized_vector is not None:
        for item in validated_items:
            manifest = item.indexed.manifest
            if manifest.index_id not in active_index_ids:
                continue
            matches_space = (
                manifest.embedding_provider_id == normalized_vector.provider_id
                and manifest.embedding_model_id == normalized_vector.model_id
                and manifest.embedding_model_version == normalized_vector.model_version
                and manifest.embedding_dimension == normalized_vector.dimension
            )
            if matches_space:
                vector_eligible.append(manifest.index_id)
                if manifest.status == "partial":
                    warnings.append(f"vector_index_partial:index={manifest.index_id}")
            else:
                vector_ineligible.append(manifest.index_id)
                warnings.append(
                    f"vector_space_ineligible:index={manifest.index_id}"
                )

    query = RetrievalQuery(
        query_id="",
        text=normalized_text,
        normalized_tokens=normalized_tokens,
        filters=normalized_filters,
        top_k=normalized_top_k,
        candidate_limit=normalized_candidate_limit,
        retrieval_contract=normalized_retrieval_contract,
        retrieval_version=normalized_retrieval_version,
        fusion_contract=normalized_fusion_contract,
        rrf_k=normalized_rrf_k,
        lexical_analyzer_contract=analyzer_contract,
        lexical_analyzer_version=analyzer_version,
        query_vector=normalized_vector,
    )
    query_id = _content_id("qry_", _query_material(query))
    query = RetrievalQuery(
        query_id=query_id,
        text=query.text,
        normalized_tokens=query.normalized_tokens,
        filters=query.filters,
        top_k=query.top_k,
        candidate_limit=query.candidate_limit,
        retrieval_contract=query.retrieval_contract,
        retrieval_version=query.retrieval_version,
        fusion_contract=query.fusion_contract,
        rrf_k=query.rrf_k,
        lexical_analyzer_contract=query.lexical_analyzer_contract,
        lexical_analyzer_version=query.lexical_analyzer_version,
        query_vector=query.query_vector,
    )

    states: dict[str, _CandidateState] = {}

    distinct_query_terms = tuple(dict.fromkeys(normalized_tokens))
    lexical_rows: list[
        tuple[int, int, int, int, str, tuple[str, ...]]
    ] = []
    if normalized_tokens:
        for chunk_id, entry in lexical_by_chunk.items():
            chunk = chunk_by_id[chunk_id]
            if not _matches_filters(chunk, normalized_filters):
                continue
            counts = Counter(entry.tokens)
            matched_terms = tuple(
                term for term in distinct_query_terms if counts.get(term, 0) > 0
            )
            if not matched_terms:
                continue
            occurrences = sum(counts[term] for term in matched_terms)
            phrase = _phrase_match(normalized_tokens, entry.tokens)
            lexical_rows.append(
                (
                    int(phrase),
                    len(matched_terms),
                    occurrences,
                    entry.token_count,
                    chunk_id,
                    matched_terms,
                )
            )
        lexical_rows.sort(
            key=lambda row: (-row[0], -row[1], -row[2], row[3], row[4])
        )
        for rank, row in enumerate(
            lexical_rows[:normalized_candidate_limit], start=1
        ):
            phrase, term_count, occurrences, _, chunk_id, matched_terms = row
            state = states.setdefault(
                chunk_id, _CandidateState(chunk=chunk_by_id[chunk_id])
            )
            state.lexical_rank = rank
            state.lexical_matched_terms = matched_terms
            state.lexical_matched_term_count = term_count
            state.lexical_matched_occurrences = occurrences
            state.lexical_phrase_match = bool(phrase)

    if normalized_vector is not None and vector_eligible:
        eligible_ids = set(vector_eligible)
        vector_rows: list[tuple[float, str]] = []
        for chunk_id, entry in embedding_by_chunk.items():
            index_id = index_for_chunk[chunk_id]
            if index_id not in eligible_ids or entry.status != "ok":
                continue
            chunk = chunk_by_id[chunk_id]
            if not _matches_filters(chunk, normalized_filters):
                continue
            vector = _validate_numeric_vector(
                vector=entry.vector,
                dimension=normalized_vector.dimension,
                name="embedding vector",
            )
            similarity = _cosine_similarity(normalized_vector.vector, vector)
            if similarity is None:
                warnings.append(f"zero_norm_embedding:chunk={chunk_id}")
                continue
            vector_rows.append((similarity, chunk_id))
        vector_rows.sort(key=lambda row: (-row[0], row[1]))
        for rank, (similarity, chunk_id) in enumerate(
            vector_rows[:normalized_candidate_limit], start=1
        ):
            state = states.setdefault(
                chunk_id, _CandidateState(chunk=chunk_by_id[chunk_id])
            )
            state.vector_rank = rank
            state.vector_similarity = similarity

    fused_states = list(states.values())
    for state in fused_states:
        score = Fraction(0, 1)
        if state.lexical_rank is not None:
            score += Fraction(1, normalized_rrf_k + state.lexical_rank)
        if state.vector_rank is not None:
            score += Fraction(1, normalized_rrf_k + state.vector_rank)
        state.fusion_score = score

    fused_states.sort(
        key=lambda state: (
            -state.fusion_score,
            min(
                rank
                for rank in (state.lexical_rank, state.vector_rank)
                if rank is not None
            ),
            state.chunk.chunk_id,
        )
    )
    for rank, state in enumerate(fused_states, start=1):
        state.fusion_rank = rank

    selected: list[_CandidateState] = []
    deferred: list[_CandidateState] = []
    for state in fused_states:
        if len(selected) >= normalized_top_k:
            break
        if any(_is_local_neighbor(state.chunk, other.chunk) for other in selected):
            deferred.append(state)
            continue
        selected.append(state)

    if len(selected) < normalized_top_k:
        selected_ids = {state.chunk.chunk_id for state in selected}
        for state in deferred:
            if len(selected) >= normalized_top_k:
                break
            if state.chunk.chunk_id not in selected_ids:
                selected.append(state)
                selected_ids.add(state.chunk.chunk_id)

    candidates = tuple(
        RetrievalCandidate(
            chunk_id=state.chunk.chunk_id,
            source_id=state.chunk.source_id,
            document_id=state.chunk.document_id,
            section_id=state.chunk.section_id,
            block_ids=state.chunk.block_ids,
            structural_path=state.chunk.structural_path,
            chunk_kind=state.chunk.kind,
            chunk_order=state.chunk.order,
            line_start=state.chunk.line_start,
            line_end=state.chunk.line_end,
            text=state.chunk.text,
            content_hash=state.chunk.content_hash,
            source_authority_class=state.chunk.source_authority_class,
            source_approval_status=state.chunk.source_approval_status,
            lexical_rank=state.lexical_rank,
            lexical_matched_terms=state.lexical_matched_terms,
            lexical_matched_term_count=state.lexical_matched_term_count,
            lexical_matched_occurrences=state.lexical_matched_occurrences,
            lexical_phrase_match=state.lexical_phrase_match,
            vector_rank=state.vector_rank,
            vector_similarity=state.vector_similarity,
            fusion_rank=state.fusion_rank,
            fusion_score_numerator=state.fusion_score.numerator,
            fusion_score_denominator=state.fusion_score.denominator,
            channel_count=int(state.lexical_rank is not None)
            + int(state.vector_rank is not None),
        )
        for state in selected
    )

    if not candidates:
        status = "no_match"
    elif normalized_vector is not None and (
        vector_ineligible
        or any(
            item.indexed.manifest.index_id in vector_eligible
            and item.indexed.manifest.status == "partial"
            for item in validated_items
        )
        or any(warning.startswith("zero_norm_embedding:") for warning in warnings)
    ):
        status = "partial"
    else:
        status = "ok"

    deferred_ids = tuple(state.chunk.chunk_id for state in deferred)
    warning_tuple = tuple(dict.fromkeys(warnings))
    retrieval_material = {
        "query_id": query.query_id,
        "corpus_index_ids": list(index_ids),
        "selected": [
            {
                "chunk_id": candidate.chunk_id,
                "lexical_rank": candidate.lexical_rank,
                "vector_rank": candidate.vector_rank,
                "fusion_rank": candidate.fusion_rank,
                "fusion_score": [
                    candidate.fusion_score_numerator,
                    candidate.fusion_score_denominator,
                ],
            }
            for candidate in candidates
        ],
        "diversity_deferred_chunk_ids": list(deferred_ids),
        "vector_eligible_index_ids": vector_eligible,
        "vector_ineligible_index_ids": vector_ineligible,
        "status": status,
        "warnings": list(warning_tuple),
        "errors": [],
    }
    retrieval_hash = hashlib.sha256(
        _canonical_json(retrieval_material).encode("utf-8")
    ).hexdigest()

    return RetrievalResult(
        retrieval_id=f"ret_{retrieval_hash}",
        retrieval_hash=retrieval_hash,
        query=query,
        corpus_index_ids=index_ids,
        candidates=candidates,
        diversity_deferred_chunk_ids=deferred_ids,
        vector_eligible_index_ids=tuple(vector_eligible),
        vector_ineligible_index_ids=tuple(vector_ineligible),
        status=status,
        warnings=warning_tuple,
        errors=(),
    )


def evaluate_retrieval(
    *,
    result: RetrievalResult,
    relevant_chunk_ids: tuple[str, ...] | list[str],
) -> RetrievalMetrics:
    """Compute deterministic first-slice retrieval metrics for one golden case."""

    if not isinstance(result, RetrievalResult):
        raise RetrievalError("result must be RetrievalResult")
    if not isinstance(relevant_chunk_ids, (tuple, list)):
        raise RetrievalError("relevant_chunk_ids must be a tuple/list")
    relevant: list[str] = []
    for value in relevant_chunk_ids:
        item = _normalized_text("relevant_chunk_id", value)
        if item not in relevant:
            relevant.append(item)
    relevant_set = set(relevant)

    retrieved = list(result.candidates)
    retrieved_ids = [candidate.chunk_id for candidate in retrieved]
    hits = [chunk_id for chunk_id in retrieved_ids if chunk_id in relevant_set]
    hit_count = len(hits)

    recall = hit_count / len(relevant_set) if relevant_set else None
    precision = hit_count / len(retrieved) if retrieved else None

    if relevant_set:
        first_rank = next(
            (
                index
                for index, chunk_id in enumerate(retrieved_ids, start=1)
                if chunk_id in relevant_set
            ),
            None,
        )
        reciprocal_rank = 0.0 if first_rank is None else 1.0 / first_rank
    else:
        reciprocal_rank = None

    if relevant_set:
        dcg = 0.0
        for rank, chunk_id in enumerate(retrieved_ids, start=1):
            if chunk_id in relevant_set:
                dcg += 1.0 / math.log2(rank + 1)
        ideal_hits = min(len(relevant_set), len(retrieved))
        idcg = sum(
            1.0 / math.log2(rank + 1)
            for rank in range(1, ideal_hits + 1)
        )
        ndcg = dcg / idcg if idcg > 0.0 else 0.0
    else:
        ndcg = None

    redundant = 0
    for index, candidate in enumerate(retrieved):
        if any(
            _is_candidate_neighbor(candidate, earlier)
            for earlier in retrieved[:index]
        ):
            redundant += 1

    redundancy_rate = redundant / len(retrieved) if retrieved else 0.0
    source_diversity = (
        len({candidate.source_id for candidate in retrieved}) / len(retrieved)
        if retrieved
        else 0.0
    )
    filter_correct = all(
        (
            (
                not result.query.filters.source_ids
                or candidate.source_id in result.query.filters.source_ids
            )
            and (
                not result.query.filters.document_ids
                or candidate.document_id in result.query.filters.document_ids
            )
            and (
                not result.query.filters.section_ids
                or candidate.section_id in result.query.filters.section_ids
            )
            and (
                not result.query.filters.source_authority_classes
                or candidate.source_authority_class
                in result.query.filters.source_authority_classes
            )
            and (
                not result.query.filters.source_approval_statuses
                or candidate.source_approval_status
                in result.query.filters.source_approval_statuses
            )
            and (
                not result.query.filters.chunk_kinds
                or candidate.chunk_kind in result.query.filters.chunk_kinds
            )
        )
        for candidate in retrieved
    )

    return RetrievalMetrics(
        recall_at_k=recall,
        precision_at_k=precision,
        reciprocal_rank=reciprocal_rank,
        ndcg_at_k=ndcg,
        evidence_coverage=recall,
        redundancy_rate=redundancy_rate,
        source_diversity=source_diversity,
        filter_correct=filter_correct,
        retrieved_count=len(retrieved),
        relevant_count=len(relevant_set),
        hit_count=hit_count,
    )
