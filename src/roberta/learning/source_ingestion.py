"""Deterministic source-ingestion foundation for the Roberta Learning System.

Phase 1 preserves exact approved UTF-8 source artifacts and immutable provenance
records. It intentionally does not parse, chunk, embed, summarize, or promote
source material into learned/verified knowledge.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol


_AUTHORITY_CLASSES = frozenset({"primary", "secondary", "internal", "unknown"})
_APPROVAL_STATES = frozenset({"approved", "pending_review", "rejected", "quarantined"})
_SOURCE_STATUSES = frozenset(
    {"approved", "pending_review", "rejected", "quarantined", "superseded"}
)
_STATUS_BY_APPROVAL = {
    "approved": frozenset({"approved", "superseded"}),
    "pending_review": frozenset({"pending_review"}),
    "rejected": frozenset({"rejected"}),
    "quarantined": frozenset({"quarantined"}),
}


class SourceIngestionError(ValueError):
    """Raised when deterministic source-ingestion validation fails."""


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """Immutable provenance record for one exact source version/content pair."""

    source_id: str
    origin: str
    title: str
    version: str
    content_hash: str
    authority_class: str
    approval_status: str
    ingested_at: str
    parser_version: str
    artifact_ref: str
    status: str
    metadata: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Observable deterministic outcome for an ingestion request."""

    status: str
    record: SourceRecord


class SourceStore(Protocol):
    """Provider-neutral external/system-of-record boundary for source ingestion."""

    def get_source(self, source_id: str) -> SourceRecord | None: ...

    def put_source(self, record: SourceRecord) -> None: ...

    def get_artifact(self, artifact_ref: str) -> bytes | None: ...

    def put_artifact(self, artifact_ref: str, content: bytes) -> None: ...


class InMemorySourceStore:
    """Deterministic unit-test/local adapter; not production persistence."""

    def __init__(self) -> None:
        self._sources: dict[str, SourceRecord] = {}
        self._artifacts: dict[str, bytes] = {}

    def get_source(self, source_id: str) -> SourceRecord | None:
        return self._sources.get(source_id)

    def put_source(self, record: SourceRecord) -> None:
        existing = self._sources.get(record.source_id)
        if existing is not None:
            if existing != record:
                raise SourceIngestionError(
                    f"conflicting source write for immutable source_id {record.source_id}"
                )
            return
        self._sources[record.source_id] = record

    def get_artifact(self, artifact_ref: str) -> bytes | None:
        value = self._artifacts.get(artifact_ref)
        return None if value is None else bytes(value)

    def put_artifact(self, artifact_ref: str, content: bytes) -> None:
        value = bytes(content)
        existing = self._artifacts.get(artifact_ref)
        if existing is not None:
            if existing != value:
                raise SourceIngestionError(
                    f"conflicting artifact write for immutable artifact_ref {artifact_ref}"
                )
            return
        self._artifacts[artifact_ref] = value


def _normalized_text(name: str, value: Any) -> str:
    if not isinstance(value, str):
        raise SourceIngestionError(f"{name} must be a normalized non-empty string")
    if not value or value != value.strip():
        raise SourceIngestionError(f"{name} must be a normalized non-empty string")
    return value


def _enum_value(name: str, value: Any, allowed: frozenset[str]) -> str:
    text = _normalized_text(name, value)
    if text not in allowed:
        choices = ", ".join(sorted(allowed))
        raise SourceIngestionError(f"{name} must be one of: {choices}")
    return text


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
        raise SourceIngestionError("value must be canonical JSON-compatible data") from exc


def _canonical_metadata(metadata: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if metadata is None:
        return MappingProxyType({})
    if not isinstance(metadata, Mapping):
        raise SourceIngestionError("metadata must be a mapping")
    if any(not isinstance(key, str) for key in metadata):
        raise SourceIngestionError("metadata keys must be strings")

    # JSON round-trip both validates and detaches the stored metadata from the caller.
    canonical = _canonical_json(dict(metadata))
    detached = json.loads(canonical)
    return MappingProxyType(detached)


def _utf8_bytes(content: str | bytes) -> bytes:
    if isinstance(content, str):
        return content.encode("utf-8")
    if isinstance(content, bytes):
        try:
            content.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SourceIngestionError("source content must be valid UTF-8") from exc
        return bytes(content)
    raise SourceIngestionError("source content must be str or UTF-8 bytes")


def _canonical_utc_timestamp(value: datetime) -> str:
    if not isinstance(value, datetime):
        raise SourceIngestionError("clock must return datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise SourceIngestionError("clock must return timezone-aware datetime")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_clock() -> datetime:
    return datetime.now(timezone.utc)


def ingest_utf8_source(
    *,
    store: SourceStore,
    content: str | bytes,
    origin: str,
    title: str,
    version: str,
    authority_class: str,
    approval_status: str,
    parser_version: str,
    status: str | None = None,
    metadata: Mapping[str, Any] | None = None,
    clock: Callable[[], datetime] = _default_clock,
) -> IngestionResult:
    """Validate and persist one exact UTF-8 source artifact and provenance record.

    Re-ingesting an identical canonical source is idempotent: the existing record
    is returned and no stored timestamp or metadata is mutated.
    """

    normalized_origin = _normalized_text("origin", origin)
    normalized_title = _normalized_text("title", title)
    normalized_version = _normalized_text("version", version)
    normalized_parser = _normalized_text("parser_version", parser_version)
    normalized_authority = _enum_value(
        "authority_class", authority_class, _AUTHORITY_CLASSES
    )
    normalized_approval = _enum_value(
        "approval_status", approval_status, _APPROVAL_STATES
    )
    normalized_status = _enum_value(
        "status", status if status is not None else normalized_approval, _SOURCE_STATUSES
    )
    if normalized_status not in _STATUS_BY_APPROVAL[normalized_approval]:
        raise SourceIngestionError(
            "status is inconsistent with approval_status for this source record"
        )

    source_bytes = _utf8_bytes(content)
    content_hash = hashlib.sha256(source_bytes).hexdigest()
    identity = {
        "origin": normalized_origin,
        "title": normalized_title,
        "version": normalized_version,
        "content_hash": content_hash,
    }
    source_id = "src_" + hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()
    artifact_ref = f"artifact_sha256:{content_hash}"

    existing = store.get_source(source_id)
    if existing is not None:
        stored_artifact = store.get_artifact(existing.artifact_ref)
        if stored_artifact != source_bytes:
            raise SourceIngestionError(
                "existing source record does not resolve to the requested immutable artifact"
            )
        return IngestionResult(status="existing", record=existing)

    canonical_metadata = _canonical_metadata(metadata)
    ingested_at = _canonical_utc_timestamp(clock())
    record = SourceRecord(
        source_id=source_id,
        origin=normalized_origin,
        title=normalized_title,
        version=normalized_version,
        content_hash=content_hash,
        authority_class=normalized_authority,
        approval_status=normalized_approval,
        ingested_at=ingested_at,
        parser_version=normalized_parser,
        artifact_ref=artifact_ref,
        status=normalized_status,
        metadata=canonical_metadata,
    )

    # Artifact first: a source record must never point at bytes that were not retained.
    store.put_artifact(artifact_ref, source_bytes)
    store.put_source(record)
    return IngestionResult(status="ingested", record=record)
