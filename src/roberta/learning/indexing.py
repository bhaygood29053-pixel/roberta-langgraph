"""Deterministic lexical + embedding indexing foundation for the Learning System.

Phase 4 creates replaceable relevance representations over canonical Phase 3
EvidenceChunk records. Index output is derived metadata: it is not source truth,
current market state, a risk score, a concept model, or execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import re
import unicodedata
from typing import Any, Protocol

from .chunking import ChunkedDocument, ChunkingError, chunk_parsed_document
from .source_ingestion import SourceStore
from .structure import StructureParseError, parse_markdown_structure


INDEX_CONTRACT = "evidence-index/v1"
LEXICAL_ANALYZER_CONTRACT = "unicode-word-casefold/v1"
_DEFAULT_INDEX_VERSION = "1.0.0"
_DEFAULT_LEXICAL_ANALYZER_VERSION = "1.0.0"
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_ALLOWED_EMBEDDING_STATUSES = frozenset({"ok", "error", "unavailable"})


class IndexingError(ValueError):
    """Raised when canonical index representations cannot be produced safely."""


@dataclass(frozen=True, slots=True)
class EmbeddingProviderInfo:
    provider_id: str
    model_id: str
    model_version: str
    dimension: int

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class EmbeddingRequest:
    chunk_id: str
    content_hash: str
    text: str

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    chunk_id: str
    content_hash: str
    status: str
    vector: tuple[float, ...] | None
    warnings: tuple[str, ...] = ()
    error: str | None = None

    @property
    def live_state_authorized(self) -> bool:
        return False


class EmbeddingProvider(Protocol):
    """Provider-neutral embedding seam used by the Phase 4 index builder."""

    def describe(self) -> EmbeddingProviderInfo:
        """Return stable provider/model metadata before any embedding call."""

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        """Return one result bound to the exact request identity."""


@dataclass(frozen=True, slots=True)
class LexicalIndexEntry:
    lexical_entry_id: str
    chunk_id: str
    source_id: str
    document_id: str
    section_id: str | None
    structural_path: tuple[str, ...]
    chunk_kind: str
    line_start: int
    line_end: int
    source_authority_class: str
    source_approval_status: str
    chunk_content_hash: str
    index_contract: str
    index_version: str
    lexical_analyzer_contract: str
    lexical_analyzer_version: str
    tokens: tuple[str, ...]
    token_count: int
    unique_term_count: int

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class EmbeddingIndexEntry:
    embedding_entry_id: str
    chunk_id: str
    source_id: str
    document_id: str
    section_id: str | None
    structural_path: tuple[str, ...]
    chunk_kind: str
    line_start: int
    line_end: int
    source_authority_class: str
    source_approval_status: str
    chunk_content_hash: str
    index_contract: str
    index_version: str
    provider_id: str
    model_id: str
    model_version: str
    dimension: int
    status: str
    vector: tuple[float, ...] | None
    vector_fingerprint: str | None
    warnings: tuple[str, ...]
    error: str | None

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class IndexManifest:
    index_id: str
    index_hash: str
    source_id: str
    document_id: str
    chunk_set_id: str
    index_contract: str
    index_version: str
    lexical_analyzer_contract: str
    lexical_analyzer_version: str
    lexical_entry_ids: tuple[str, ...]
    embedding_provider_id: str | None
    embedding_model_id: str | None
    embedding_model_version: str | None
    embedding_dimension: int | None
    embedding_entry_ids: tuple[str, ...]
    embedding_ok_count: int
    embedding_error_count: int
    embedding_unavailable_count: int
    status: str
    warnings: tuple[str, ...]
    errors: tuple[str, ...]

    @property
    def live_state_authorized(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class IndexedDocument:
    manifest: IndexManifest
    lexical_entries: tuple[LexicalIndexEntry, ...]
    embedding_entries: tuple[EmbeddingIndexEntry, ...]

    @property
    def live_state_authorized(self) -> bool:
        return False


class DeterministicHashEmbeddingProvider:
    """Deterministic test adapter for the embedding-provider contract.

    This is intentionally NOT a semantic embedding model. It exists only to
    exercise provider identity, exact request binding, vector validation, and
    reproducible derived-index identities without external model dependencies.
    """

    def __init__(
        self,
        *,
        provider_id: str = "deterministic-hash-test",
        model_id: str = "sha256-contract-vector",
        model_version: str = "1.0.0",
        dimension: int = 8,
    ) -> None:
        self._info = EmbeddingProviderInfo(
            provider_id=_normalized_text("provider_id", provider_id),
            model_id=_normalized_text("model_id", model_id),
            model_version=_normalized_text("model_version", model_version),
            dimension=_positive_int("dimension", dimension),
        )

    def describe(self) -> EmbeddingProviderInfo:
        return self._info

    def embed(self, request: EmbeddingRequest) -> EmbeddingResult:
        if not isinstance(request, EmbeddingRequest):
            raise IndexingError("request must be an EmbeddingRequest")
        payload = _canonical_json(
            {
                "provider_id": self._info.provider_id,
                "model_id": self._info.model_id,
                "model_version": self._info.model_version,
                "dimension": self._info.dimension,
                "chunk_id": request.chunk_id,
                "content_hash": request.content_hash,
                "text": request.text,
            }
        ).encode("utf-8")
        needed = self._info.dimension * 2
        material = bytearray()
        counter = 0
        while len(material) < needed:
            material.extend(
                hashlib.sha256(payload + counter.to_bytes(4, "big")).digest()
            )
            counter += 1
        vector = tuple(
            (int.from_bytes(material[index : index + 2], "big") / 32767.5) - 1.0
            for index in range(0, needed, 2)
        )
        return EmbeddingResult(
            chunk_id=request.chunk_id,
            content_hash=request.content_hash,
            status="ok",
            vector=vector,
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
        raise IndexingError("index material must be canonical JSON-compatible data") from exc


def _content_id(prefix: str, value: Any) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"{prefix}{digest}"


def _normalized_text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise IndexingError(f"{name} must be a normalized non-empty string")
    return value


def _positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise IndexingError(f"{name} must be a positive integer")
    return value


def _normalized_warnings(value: Any) -> tuple[str, ...]:
    if not isinstance(value, (tuple, list)):
        raise IndexingError("embedding warnings must be a tuple/list of strings")
    warnings: list[str] = []
    for warning in value:
        warnings.append(_normalized_text("embedding warning", warning))
    return tuple(warnings)


def _lexical_tokens(text: str) -> tuple[str, ...]:
    if not isinstance(text, str):
        raise IndexingError("chunk text must be a string")
    normalized = unicodedata.normalize("NFKC", text).casefold()
    return tuple(match.group(0) for match in _TOKEN_RE.finditer(normalized))


def _canonical_chunked_document(
    *, store: SourceStore, chunked: ChunkedDocument
) -> ChunkedDocument:
    if not isinstance(chunked, ChunkedDocument):
        raise IndexingError("chunked must be a canonical ChunkedDocument")
    manifest = chunked.manifest
    try:
        parsed = parse_markdown_structure(
            store=store,
            source_id=manifest.source_id,
            parser_contract=manifest.parser_contract,
            parser_version=manifest.parser_version,
        )
        canonical = chunk_parsed_document(
            store=store,
            parsed=parsed,
            chunker_contract=manifest.chunker_contract,
            chunker_version=manifest.chunker_version,
            max_chars=manifest.max_chars,
            overlap_lines=manifest.overlap_lines,
        )
    except (StructureParseError, ChunkingError) as exc:
        raise IndexingError("canonical Phase 3 reconstruction failed") from exc
    if canonical != chunked:
        raise IndexingError(
            "supplied ChunkedDocument does not match canonical Phase 3 chunks"
        )
    return canonical


def _validate_provider_info(value: Any) -> EmbeddingProviderInfo:
    if not isinstance(value, EmbeddingProviderInfo):
        raise IndexingError("embedding provider describe() must return EmbeddingProviderInfo")
    return EmbeddingProviderInfo(
        provider_id=_normalized_text("provider_id", value.provider_id),
        model_id=_normalized_text("model_id", value.model_id),
        model_version=_normalized_text("model_version", value.model_version),
        dimension=_positive_int("dimension", value.dimension),
    )


def _exception_error(exc: Exception) -> str:
    message = str(exc).strip()
    if message:
        return f"provider_exception:{type(exc).__name__}:{message}"
    return f"provider_exception:{type(exc).__name__}"


def _validate_embedding_result(
    *,
    value: Any,
    request: EmbeddingRequest,
    provider: EmbeddingProviderInfo,
) -> tuple[str, tuple[float, ...] | None, tuple[str, ...], str | None]:
    if not isinstance(value, EmbeddingResult):
        raise IndexingError("embedding provider must return EmbeddingResult")
    if value.chunk_id != request.chunk_id or value.content_hash != request.content_hash:
        raise IndexingError("embedding result identity does not match request")
    status = _normalized_text("embedding status", value.status)
    if status not in _ALLOWED_EMBEDDING_STATUSES:
        raise IndexingError(f"unsupported embedding status {status!r}")
    warnings = _normalized_warnings(value.warnings)

    if status == "ok":
        if value.error is not None:
            raise IndexingError("ok embedding result must not contain an error")
        if value.vector is None or not isinstance(value.vector, (tuple, list)):
            raise IndexingError("ok embedding result must contain a vector")
        if len(value.vector) != provider.dimension:
            raise IndexingError(
                "embedding vector dimension does not match provider declaration"
            )
        validated: list[float] = []
        for item in value.vector:
            if isinstance(item, bool) or not isinstance(item, (int, float)):
                raise IndexingError("embedding vector elements must be numeric")
            numeric = float(item)
            if not math.isfinite(numeric):
                raise IndexingError("embedding vector elements must be finite")
            validated.append(numeric)
        return status, tuple(validated), warnings, None

    if value.vector is not None:
        raise IndexingError("failed/unavailable embedding result must not contain a vector")
    error = _normalized_text("embedding error", value.error)
    return status, None, warnings, error


def _lexical_entry_material(
    entry: LexicalIndexEntry, *, include_id: bool = True
) -> dict[str, Any]:
    material: dict[str, Any] = {
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
    if include_id:
        material["lexical_entry_id"] = entry.lexical_entry_id
    return material


def _embedding_entry_material(
    entry: EmbeddingIndexEntry, *, include_id: bool = True
) -> dict[str, Any]:
    material: dict[str, Any] = {
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
    if include_id:
        material["embedding_entry_id"] = entry.embedding_entry_id
    return material


def build_evidence_index(
    *,
    store: SourceStore,
    chunked: ChunkedDocument,
    index_contract: str = INDEX_CONTRACT,
    index_version: str = _DEFAULT_INDEX_VERSION,
    lexical_analyzer_contract: str = LEXICAL_ANALYZER_CONTRACT,
    lexical_analyzer_version: str = _DEFAULT_LEXICAL_ANALYZER_VERSION,
    embedding_provider: EmbeddingProvider | None = None,
) -> IndexedDocument:
    """Build deterministic derived index representations from canonical chunks."""

    normalized_index_contract = _normalized_text("index_contract", index_contract)
    if normalized_index_contract != INDEX_CONTRACT:
        raise IndexingError(
            f"unsupported index_contract {normalized_index_contract!r}; expected {INDEX_CONTRACT!r}"
        )
    normalized_index_version = _normalized_text("index_version", index_version)
    normalized_lexical_contract = _normalized_text(
        "lexical_analyzer_contract", lexical_analyzer_contract
    )
    if normalized_lexical_contract != LEXICAL_ANALYZER_CONTRACT:
        raise IndexingError(
            "unsupported lexical_analyzer_contract "
            f"{normalized_lexical_contract!r}; expected {LEXICAL_ANALYZER_CONTRACT!r}"
        )
    normalized_lexical_version = _normalized_text(
        "lexical_analyzer_version", lexical_analyzer_version
    )

    canonical = _canonical_chunked_document(store=store, chunked=chunked)

    lexical_entries_list: list[LexicalIndexEntry] = []
    for chunk in canonical.chunks:
        tokens = _lexical_tokens(chunk.text)
        material = {
            "chunk_id": chunk.chunk_id,
            "source_id": chunk.source_id,
            "document_id": chunk.document_id,
            "section_id": chunk.section_id,
            "structural_path": list(chunk.structural_path),
            "chunk_kind": chunk.kind,
            "line_start": chunk.line_start,
            "line_end": chunk.line_end,
            "source_authority_class": chunk.source_authority_class,
            "source_approval_status": chunk.source_approval_status,
            "chunk_content_hash": chunk.content_hash,
            "index_contract": normalized_index_contract,
            "index_version": normalized_index_version,
            "lexical_analyzer_contract": normalized_lexical_contract,
            "lexical_analyzer_version": normalized_lexical_version,
            "tokens": list(tokens),
            "token_count": len(tokens),
            "unique_term_count": len(set(tokens)),
        }
        lexical_entries_list.append(
            LexicalIndexEntry(
                lexical_entry_id=_content_id("lex_", material),
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                document_id=chunk.document_id,
                section_id=chunk.section_id,
                structural_path=chunk.structural_path,
                chunk_kind=chunk.kind,
                line_start=chunk.line_start,
                line_end=chunk.line_end,
                source_authority_class=chunk.source_authority_class,
                source_approval_status=chunk.source_approval_status,
                chunk_content_hash=chunk.content_hash,
                index_contract=normalized_index_contract,
                index_version=normalized_index_version,
                lexical_analyzer_contract=normalized_lexical_contract,
                lexical_analyzer_version=normalized_lexical_version,
                tokens=tokens,
                token_count=len(tokens),
                unique_term_count=len(set(tokens)),
            )
        )
    lexical_entries = tuple(lexical_entries_list)

    provider_info: EmbeddingProviderInfo | None = None
    embedding_entries_list: list[EmbeddingIndexEntry] = []
    manifest_warnings: list[str] = []
    manifest_errors: list[str] = []

    if embedding_provider is not None:
        try:
            provider_info = _validate_provider_info(embedding_provider.describe())
        except IndexingError:
            raise
        except Exception as exc:
            raise IndexingError("embedding provider describe() failed") from exc

        for chunk in canonical.chunks:
            request = EmbeddingRequest(
                chunk_id=chunk.chunk_id,
                content_hash=chunk.content_hash,
                text=chunk.text,
            )
            try:
                raw_result = embedding_provider.embed(request)
            except Exception as exc:
                raw_result = EmbeddingResult(
                    chunk_id=request.chunk_id,
                    content_hash=request.content_hash,
                    status="error",
                    vector=None,
                    error=_exception_error(exc),
                )

            status, vector, warnings, error = _validate_embedding_result(
                value=raw_result,
                request=request,
                provider=provider_info,
            )
            vector_fingerprint = (
                hashlib.sha256(_canonical_json(list(vector)).encode("utf-8")).hexdigest()
                if vector is not None
                else None
            )
            material = {
                "chunk_id": chunk.chunk_id,
                "source_id": chunk.source_id,
                "document_id": chunk.document_id,
                "section_id": chunk.section_id,
                "structural_path": list(chunk.structural_path),
                "chunk_kind": chunk.kind,
                "line_start": chunk.line_start,
                "line_end": chunk.line_end,
                "source_authority_class": chunk.source_authority_class,
                "source_approval_status": chunk.source_approval_status,
                "chunk_content_hash": chunk.content_hash,
                "index_contract": normalized_index_contract,
                "index_version": normalized_index_version,
                "provider_id": provider_info.provider_id,
                "model_id": provider_info.model_id,
                "model_version": provider_info.model_version,
                "dimension": provider_info.dimension,
                "status": status,
                "vector_fingerprint": vector_fingerprint,
                "warnings": list(warnings),
                "error": error,
            }
            entry = EmbeddingIndexEntry(
                embedding_entry_id=_content_id("emb_", material),
                chunk_id=chunk.chunk_id,
                source_id=chunk.source_id,
                document_id=chunk.document_id,
                section_id=chunk.section_id,
                structural_path=chunk.structural_path,
                chunk_kind=chunk.kind,
                line_start=chunk.line_start,
                line_end=chunk.line_end,
                source_authority_class=chunk.source_authority_class,
                source_approval_status=chunk.source_approval_status,
                chunk_content_hash=chunk.content_hash,
                index_contract=normalized_index_contract,
                index_version=normalized_index_version,
                provider_id=provider_info.provider_id,
                model_id=provider_info.model_id,
                model_version=provider_info.model_version,
                dimension=provider_info.dimension,
                status=status,
                vector=vector,
                vector_fingerprint=vector_fingerprint,
                warnings=warnings,
                error=error,
            )
            embedding_entries_list.append(entry)
            for warning in warnings:
                message = f"embedding_warning:chunk={chunk.chunk_id}:{warning}"
                if message not in manifest_warnings:
                    manifest_warnings.append(message)
            if status == "error":
                message = f"embedding_error:chunk={chunk.chunk_id}:{error}"
                if message not in manifest_errors:
                    manifest_errors.append(message)
            elif status == "unavailable":
                message = f"embedding_unavailable:chunk={chunk.chunk_id}:{error}"
                if message not in manifest_warnings:
                    manifest_warnings.append(message)

    embedding_entries = tuple(embedding_entries_list)
    ok_count = sum(entry.status == "ok" for entry in embedding_entries)
    error_count = sum(entry.status == "error" for entry in embedding_entries)
    unavailable_count = sum(entry.status == "unavailable" for entry in embedding_entries)

    if provider_info is None:
        status = "lexical_only"
    elif error_count or unavailable_count:
        status = "partial"
    else:
        status = "complete"

    manifest_material = {
        "source_id": canonical.manifest.source_id,
        "document_id": canonical.manifest.document_id,
        "chunk_set_id": canonical.manifest.chunk_set_id,
        "index_contract": normalized_index_contract,
        "index_version": normalized_index_version,
        "lexical_analyzer_contract": normalized_lexical_contract,
        "lexical_analyzer_version": normalized_lexical_version,
        "lexical_entries": [
            _lexical_entry_material(entry) for entry in lexical_entries
        ],
        "embedding_provider": (
            {
                "provider_id": provider_info.provider_id,
                "model_id": provider_info.model_id,
                "model_version": provider_info.model_version,
                "dimension": provider_info.dimension,
            }
            if provider_info is not None
            else None
        ),
        "embedding_entries": [
            _embedding_entry_material(entry) for entry in embedding_entries
        ],
        "embedding_ok_count": ok_count,
        "embedding_error_count": error_count,
        "embedding_unavailable_count": unavailable_count,
        "status": status,
        "warnings": manifest_warnings,
        "errors": manifest_errors,
    }
    index_hash = hashlib.sha256(
        _canonical_json(manifest_material).encode("utf-8")
    ).hexdigest()
    manifest = IndexManifest(
        index_id=f"idx_{index_hash}",
        index_hash=index_hash,
        source_id=canonical.manifest.source_id,
        document_id=canonical.manifest.document_id,
        chunk_set_id=canonical.manifest.chunk_set_id,
        index_contract=normalized_index_contract,
        index_version=normalized_index_version,
        lexical_analyzer_contract=normalized_lexical_contract,
        lexical_analyzer_version=normalized_lexical_version,
        lexical_entry_ids=tuple(entry.lexical_entry_id for entry in lexical_entries),
        embedding_provider_id=(provider_info.provider_id if provider_info else None),
        embedding_model_id=(provider_info.model_id if provider_info else None),
        embedding_model_version=(provider_info.model_version if provider_info else None),
        embedding_dimension=(provider_info.dimension if provider_info else None),
        embedding_entry_ids=tuple(
            entry.embedding_entry_id for entry in embedding_entries
        ),
        embedding_ok_count=ok_count,
        embedding_error_count=error_count,
        embedding_unavailable_count=unavailable_count,
        status=status,
        warnings=tuple(manifest_warnings),
        errors=tuple(manifest_errors),
    )
    return IndexedDocument(
        manifest=manifest,
        lexical_entries=lexical_entries,
        embedding_entries=embedding_entries,
    )
