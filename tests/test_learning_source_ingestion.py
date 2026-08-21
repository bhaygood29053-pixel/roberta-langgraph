from __future__ import annotations

from datetime import datetime, timezone
import hashlib

import pytest

from roberta.learning import (
    InMemorySourceStore,
    SourceIngestionError,
    SourceRecord,
    ingest_utf8_source,
)


FIXED_TIME = datetime(2026, 8, 21, 9, 30, tzinfo=timezone.utc)


def _clock() -> datetime:
    return FIXED_TIME


def _ingest(store: InMemorySourceStore, content: str = "alpha\n", **overrides):
    params = {
        "store": store,
        "content": content,
        "origin": "project://learning-system-spec",
        "title": "Roberta Learning System Specification",
        "version": "1.1",
        "authority_class": "internal",
        "approval_status": "approved",
        "parser_version": "utf8-source/v1",
        "metadata": {"document_type": "normative_spec", "tags": ["learning", "roberta"]},
        "clock": _clock,
    }
    params.update(overrides)
    return ingest_utf8_source(**params)


def test_ingestion_preserves_exact_bytes_and_independent_sha256_identity() -> None:
    store = InMemorySourceStore()
    content = "Roberta learns from evidence.\n"

    result = _ingest(store, content)

    expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    assert result.status == "ingested"
    assert result.record.content_hash == expected_hash
    assert result.record.source_id.startswith("src_")
    assert len(result.record.source_id) == len("src_") + 64
    assert result.record.artifact_ref == f"artifact_sha256:{expected_hash}"
    assert store.get_artifact(result.record.artifact_ref) == content.encode("utf-8")
    assert result.record.ingested_at == "2026-08-21T09:30:00Z"


def test_identical_reingestion_is_idempotent_and_keeps_original_record() -> None:
    store = InMemorySourceStore()
    first = _ingest(store)

    later = datetime(2027, 1, 1, tzinfo=timezone.utc)
    second = _ingest(store, clock=lambda: later)

    assert first.status == "ingested"
    assert second.status == "existing"
    assert second.record is first.record
    assert second.record.ingested_at == "2026-08-21T09:30:00Z"


def test_changed_content_creates_distinct_record_without_erasing_prior_artifact() -> None:
    store = InMemorySourceStore()
    first = _ingest(store, "version one\n")
    second = _ingest(store, "version two\n")

    assert first.record.source_id != second.record.source_id
    assert first.record.content_hash != second.record.content_hash
    assert store.get_source(first.record.source_id) == first.record
    assert store.get_source(second.record.source_id) == second.record
    assert store.get_artifact(first.record.artifact_ref) == b"version one\n"
    assert store.get_artifact(second.record.artifact_ref) == b"version two\n"


def test_same_bytes_with_different_source_version_reuses_artifact_but_not_source_identity() -> None:
    store = InMemorySourceStore()
    first = _ingest(store, "same bytes\n", version="1.1")
    second = _ingest(store, "same bytes\n", version="1.2")

    assert first.record.source_id != second.record.source_id
    assert first.record.content_hash == second.record.content_hash
    assert first.record.artifact_ref == second.record.artifact_ref
    assert store.get_artifact(first.record.artifact_ref) == b"same bytes\n"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authority_class", "trusted-because-model-said-so"),
        ("approval_status", "verified"),
        ("status", "live"),
        ("origin", " project://bad-whitespace"),
        ("parser_version", ""),
    ],
)
def test_malformed_identity_and_state_inputs_fail_closed(field: str, value: str) -> None:
    store = InMemorySourceStore()

    with pytest.raises(SourceIngestionError):
        _ingest(store, **{field: value})


def test_status_must_be_consistent_with_approval_state() -> None:
    store = InMemorySourceStore()

    with pytest.raises(SourceIngestionError, match="inconsistent"):
        _ingest(store, approval_status="approved", status="quarantined")


def test_invalid_utf8_bytes_fail_closed_without_storage_mutation() -> None:
    store = InMemorySourceStore()

    with pytest.raises(SourceIngestionError, match="UTF-8"):
        _ingest(store, content=b"\xff\xfe")

    assert store._sources == {}
    assert store._artifacts == {}


def test_metadata_must_be_json_compatible_and_is_detached_from_caller() -> None:
    store = InMemorySourceStore()
    metadata = {"tags": ["a", "b"]}
    result = _ingest(store, metadata=metadata)

    metadata["tags"].append("caller-mutation")

    assert result.record.metadata["tags"] == ["a", "b"]
    with pytest.raises(TypeError):
        result.record.metadata["new"] = "blocked"  # type: ignore[index]

    with pytest.raises(SourceIngestionError, match="canonical JSON"):
        _ingest(store, content="other\n", metadata={"not_json": object()})


def test_non_string_metadata_keys_and_nan_fail_closed() -> None:
    store = InMemorySourceStore()

    with pytest.raises(SourceIngestionError, match="keys"):
        _ingest(store, metadata={1: "bad"})  # type: ignore[dict-item]

    with pytest.raises(SourceIngestionError, match="canonical JSON"):
        _ingest(store, metadata={"value": float("nan")})


def test_in_memory_store_rejects_conflicting_immutable_writes() -> None:
    store = InMemorySourceStore()
    result = _ingest(store)

    with pytest.raises(SourceIngestionError, match="artifact write"):
        store.put_artifact(result.record.artifact_ref, b"tampered")

    conflicting = SourceRecord(
        source_id=result.record.source_id,
        origin=result.record.origin,
        title="Tampered title",
        version=result.record.version,
        content_hash=result.record.content_hash,
        authority_class=result.record.authority_class,
        approval_status=result.record.approval_status,
        ingested_at=result.record.ingested_at,
        parser_version=result.record.parser_version,
        artifact_ref=result.record.artifact_ref,
        status=result.record.status,
        metadata=result.record.metadata,
    )
    with pytest.raises(SourceIngestionError, match="source write"):
        store.put_source(conflicting)


def test_missing_record_or_artifact_returns_none() -> None:
    store = InMemorySourceStore()

    assert store.get_source("src_missing") is None
    assert store.get_artifact("artifact_sha256:missing") is None
