"""Approval-gated HXMP backend adapter for Roberta durable memory."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Protocol

from roberta.memory.contracts import MemoryCandidate, MemoryRecord
from roberta.memory.policy import classify_memory_candidate
from roberta.memory.retrieval import select_relevant_memory

HXMP_MEMORY_SCHEMA = "roberta.durable-memory"
HXMP_MEMORY_VERSION = 1
DEFAULT_HXMP_MEMORY_LANE = "roberta-memory"
_NO_MEMORY_FRAGMENT = "No owner-matching soul.latest record found"


class HXMPMemoryError(RuntimeError):
    """Base error for HXMP durable-memory integration failures."""


class HXMPVerificationError(HXMPMemoryError):
    """Raised when HXMP read/write verification fails closed."""


class HXMPApprovalRequiredError(HXMPMemoryError):
    """Raised when a caller tries to bypass HXMP's approval-gated write flow."""


class HXMPWriteRefusedError(HXMPMemoryError):
    """Raised when deterministic policy or HXMP preview rules reject a write."""


class HXMPCommandRunner(Protocol):
    """Injected command boundary used by the HXMP adapter."""

    def run(self, command: str, args: Sequence[str]) -> Mapping[str, Any]:
        """Run one HXMP command and return its parsed JSON object."""


@dataclass(frozen=True, slots=True)
class HXMPMemoryConfig:
    """Explicit local configuration for the SyntharaLabs/HXMP tool layer."""

    script_path: str
    wallet: str
    encryption_key_path: str
    lane: str = DEFAULT_HXMP_MEMORY_LANE
    profile: str = "default"
    keypair_path: str | None = None
    node_executable: str = "node"
    timeout_seconds: int = 90
    scan_limit: int = 120

    def __post_init__(self) -> None:
        for name, value in (
            ("script_path", self.script_path),
            ("wallet", self.wallet),
            ("encryption_key_path", self.encryption_key_path),
            ("lane", self.lane),
            ("profile", self.profile),
            ("node_executable", self.node_executable),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if self.keypair_path is not None and (
            not isinstance(self.keypair_path, str) or not self.keypair_path.strip()
        ):
            raise ValueError("keypair_path must be None or a non-empty string")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if self.scan_limit <= 0:
            raise ValueError("scan_limit must be positive")


@dataclass(frozen=True, slots=True)
class HXMPPreparedWrite:
    """A dry-run-verified HXMP memory proposal awaiting explicit approval."""

    record: MemoryRecord
    source_path: str
    plaintext_sha256: str
    preview: Mapping[str, Any]
    ready_to_execute: bool

    @property
    def requires_approval(self) -> bool:
        return True


@dataclass(frozen=True, slots=True)
class HXMPWriteCommit:
    """Verified result of one explicitly approved HXMP memory write."""

    record: MemoryRecord
    plaintext_sha256: str
    latest_tx: str
    readback_verified: bool
    receipt: Mapping[str, Any]


class SubprocessHXMPCommandRunner:
    """Invoke the public SyntharaLabs/HXMP Node tool without reading secret bytes."""

    def __init__(
        self,
        script_path: str,
        *,
        node_executable: str = "node",
        timeout_seconds: int = 90,
    ) -> None:
        self.script_path = str(script_path)
        self.node_executable = str(node_executable)
        self.timeout_seconds = int(timeout_seconds)

    def run(self, command: str, args: Sequence[str]) -> Mapping[str, Any]:
        script = Path(self.script_path).expanduser()
        if not script.is_file():
            raise HXMPMemoryError(f"HXMP tool script not found: {script}")

        completed = subprocess.run(
            [self.node_executable, str(script), command, *[str(arg) for arg in args]],
            capture_output=True,
            text=True,
            timeout=self.timeout_seconds,
            check=False,
        )
        raw = completed.stdout if completed.returncode == 0 else completed.stderr
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HXMPMemoryError(
                f"HXMP command {command!r} returned invalid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise HXMPMemoryError(
                f"HXMP command {command!r} returned a non-object JSON payload"
            )
        if completed.returncode != 0:
            message = str(payload.get("error") or "HXMP command failed")
            raise HXMPMemoryError(message[:500])
        return payload


def _record_to_json(record: MemoryRecord) -> dict[str, Any]:
    return {
        "key": record.key,
        "category": record.category,
        "content": record.content,
        "topics": list(record.topics),
        "source": record.source,
        "rationale": record.rationale,
        "authority": record.authority,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def serialize_memory_records(records: Sequence[MemoryRecord]) -> str:
    """Serialize records deterministically for HXMP plaintext hashing."""

    by_key: dict[str, MemoryRecord] = {}
    for record in records:
        if record.key in by_key:
            raise ValueError(f"duplicate memory key: {record.key!r}")
        by_key[record.key] = record

    payload = {
        "schema": HXMP_MEMORY_SCHEMA,
        "version": HXMP_MEMORY_VERSION,
        "records": [_record_to_json(by_key[key]) for key in sorted(by_key)],
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def deserialize_memory_records(content: str) -> list[MemoryRecord]:
    """Parse one verified Roberta memory snapshot from HXMP plaintext."""

    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise HXMPVerificationError("HXMP plaintext is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise HXMPVerificationError("HXMP plaintext must be a JSON object")
    if payload.get("schema") != HXMP_MEMORY_SCHEMA:
        raise HXMPVerificationError("HXMP plaintext uses an unsupported memory schema")
    if payload.get("version") != HXMP_MEMORY_VERSION:
        raise HXMPVerificationError("HXMP plaintext uses an unsupported memory version")
    raw_records = payload.get("records")
    if not isinstance(raw_records, list):
        raise HXMPVerificationError("HXMP plaintext records must be a list")

    records: list[MemoryRecord] = []
    seen: set[str] = set()
    for item in raw_records:
        if not isinstance(item, dict):
            raise HXMPVerificationError("HXMP memory record must be a JSON object")
        topics = item.get("topics", [])
        if not isinstance(topics, list):
            raise HXMPVerificationError("HXMP memory record topics must be a list")
        try:
            record = MemoryRecord(
                key=item["key"],
                category=item["category"],
                content=item["content"],
                topics=tuple(topics),
                source=item.get("source", "runtime"),
                rationale=item.get("rationale"),
                authority=item.get("authority", "durable"),
                created_at=item.get("created_at"),
                updated_at=item.get("updated_at"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise HXMPVerificationError("HXMP memory record failed validation") from exc
        if record.key in seen:
            raise HXMPVerificationError(f"HXMP memory contains duplicate key {record.key!r}")
        seen.add(record.key)
        records.append(record)
    records.sort(key=lambda record: record.key)
    return records


def _sha256_label_bytes(content: bytes) -> str:
    digest = hashlib.sha256(content).hexdigest()
    return f"sha256:{digest}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class HXMPMemoryStore:
    """Read verified HXMP memory automatically; gate every on-chain write by approval."""

    def __init__(
        self,
        config: HXMPMemoryConfig,
        *,
        runner: HXMPCommandRunner | None = None,
    ) -> None:
        self.config = config
        self.runner = runner or SubprocessHXMPCommandRunner(
            config.script_path,
            node_executable=config.node_executable,
            timeout_seconds=config.timeout_seconds,
        )

    def _read_records(self) -> list[MemoryRecord]:
        result = self.runner.run(
            "read-soul",
            [
                "--wallet",
                self.config.wallet,
                "--encryption-key",
                self.config.encryption_key_path,
                "--lane",
                self.config.lane,
                "--limit",
                str(self.config.scan_limit),
                "--show-content",
            ],
        )
        if result.get("ok") is False and _NO_MEMORY_FRAGMENT in str(result.get("error", "")):
            return []
        if result.get("ok") is not True or result.get("verified") is not True:
            raise HXMPVerificationError("HXMP read-soul did not return verified plaintext")
        if result.get("wallet") != self.config.wallet:
            raise HXMPVerificationError("HXMP read wallet does not match configured wallet")
        if result.get("lane") != self.config.lane:
            raise HXMPVerificationError("HXMP read lane does not match configured lane")
        content = result.get("content")
        if not isinstance(content, str):
            raise HXMPVerificationError("HXMP verified read omitted plaintext content")
        return deserialize_memory_records(content)

    def get(self, key: str) -> MemoryRecord | None:
        if not isinstance(key, str) or not key.strip():
            raise ValueError("memory key must be a non-empty string")
        for record in self._read_records():
            if record.key == key:
                return record
        return None

    def search(self, query: str, *, limit: int = 12) -> list[MemoryRecord]:
        if limit <= 0 or not str(query or "").strip():
            return []
        return select_relevant_memory(self._read_records(), query, limit=limit)

    def upsert(self, record: MemoryRecord) -> None:
        raise HXMPApprovalRequiredError(
            "HXMP upsert never broadcasts automatically; call prepare_upsert(), "
            "show the exact dry-run hash to the user, then call "
            "execute_prepared_write() only after explicit approval"
        )

    def prepare_candidate(
        self,
        candidate: MemoryCandidate,
        *,
        observed_at: str | None = None,
    ) -> HXMPPreparedWrite:
        """Apply Roberta policy, build one replacement record, and dry-run HXMP."""

        decision = classify_memory_candidate(candidate)
        if not decision.allowed or decision.authority is None:
            raise HXMPWriteRefusedError(decision.reason)
        timestamp = observed_at or _utc_now()
        current_records = self._read_records()
        existing = next(
            (record for record in current_records if record.key == candidate.key),
            None,
        )
        record = MemoryRecord(
            key=candidate.key,
            category=candidate.category,
            content=candidate.content,
            topics=tuple(candidate.topics),
            source=candidate.source,
            rationale=candidate.rationale,
            authority=decision.authority,
            created_at=existing.created_at if existing is not None else timestamp,
            updated_at=timestamp,
        )
        return self._prepare_upsert_against_records(record, current_records)

    def prepare_upsert(self, record: MemoryRecord) -> HXMPPreparedWrite:
        """Create a 0600 temporary snapshot and run HXMP dry-run-soul only."""

        return self._prepare_upsert_against_records(record, self._read_records())

    def _prepare_upsert_against_records(
        self,
        record: MemoryRecord,
        current_records: Sequence[MemoryRecord],
    ) -> HXMPPreparedWrite:
        if record.authority != "durable":
            raise HXMPWriteRefusedError(
                "standard HXMP writes accept only authority='durable'"
            )
        records = {item.key: item for item in current_records}
        records[record.key] = record
        content = serialize_memory_records(list(records.values()))
        content_bytes = content.encode("utf-8")
        expected_hash = _sha256_label_bytes(content_bytes)

        fd, source_path = tempfile.mkstemp(prefix="roberta-hxmp-", suffix=".json")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content_bytes)
            try:
                os.chmod(source_path, 0o600)
            except OSError:
                pass

            preview = self.runner.run(
                "dry-run-soul",
                [
                    "--wallet",
                    self.config.wallet,
                    "--source",
                    source_path,
                    "--profile",
                    self.config.profile,
                    "--lane",
                    self.config.lane,
                    "--limit",
                    str(self.config.scan_limit),
                ],
            )
            if preview.get("wallet") != self.config.wallet:
                raise HXMPVerificationError(
                    "HXMP dry-run wallet does not match configured wallet"
                )
            if preview.get("lane") != self.config.lane:
                raise HXMPVerificationError(
                    "HXMP dry-run lane does not match configured lane"
                )
            if preview.get("plaintext_sha256") != expected_hash:
                raise HXMPVerificationError(
                    "HXMP dry-run hash does not match deterministic Roberta snapshot"
                )
            agentid = preview.get("agentid")
            safety = preview.get("safety")
            ready = (
                preview.get("ok") is True
                and isinstance(agentid, dict)
                and agentid.get("verified") is True
                and isinstance(safety, dict)
                and safety.get("classification") == "safe"
            )
            return HXMPPreparedWrite(
                record=record,
                source_path=source_path,
                plaintext_sha256=expected_hash,
                preview=dict(preview),
                ready_to_execute=ready,
            )
        except Exception:
            try:
                Path(source_path).unlink()
            except OSError:
                pass
            raise

    def execute_prepared_write(
        self,
        prepared: HXMPPreparedWrite,
        *,
        approved_sha256: str,
        user_approved: bool,
        keypair_path: str | None = None,
    ) -> HXMPWriteCommit:
        """Execute one exact HXMP preview after explicit human approval."""

        if user_approved is not True:
            raise HXMPApprovalRequiredError("explicit user approval is required")
        if approved_sha256 != prepared.plaintext_sha256:
            raise HXMPApprovalRequiredError(
                "approved SHA-256 does not match the prepared HXMP preview"
            )
        if not prepared.ready_to_execute:
            raise HXMPWriteRefusedError(
                "HXMP dry-run is not executable; inspect Agent ID and safety status"
            )
        source = Path(prepared.source_path)
        if not source.is_file():
            raise HXMPVerificationError("prepared HXMP source file no longer exists")
        actual_hash = _sha256_label_bytes(source.read_bytes())
        if actual_hash != prepared.plaintext_sha256:
            raise HXMPVerificationError(
                "prepared HXMP source changed after dry-run; prepare again"
            )

        keypair = keypair_path or self.config.keypair_path
        if not keypair:
            raise HXMPApprovalRequiredError(
                "HXMP keypair path is required only for explicitly approved execution"
            )

        result = self.runner.run(
            "write-soul",
            [
                "--keypair",
                keypair,
                "--encryption-key",
                self.config.encryption_key_path,
                "--source",
                prepared.source_path,
                "--profile",
                self.config.profile,
                "--lane",
                self.config.lane,
                "--limit",
                str(self.config.scan_limit),
                "--expected-sha256",
                approved_sha256,
                "--execute",
                "--confirm-write",
            ],
        )
        if result.get("ok") is not True or result.get("readback_verified") is not True:
            raise HXMPVerificationError("HXMP write did not pass readback verification")
        if result.get("wallet") != self.config.wallet:
            raise HXMPVerificationError("HXMP write wallet does not match configured wallet")
        if result.get("lane") != self.config.lane:
            raise HXMPVerificationError("HXMP write lane does not match configured lane")
        if result.get("plaintext_sha256") != approved_sha256:
            raise HXMPVerificationError("HXMP write hash does not match approved SHA-256")
        latest_tx = result.get("latest_tx")
        if not isinstance(latest_tx, str) or not latest_tx.strip():
            raise HXMPVerificationError("HXMP verified write omitted latest transaction")

        try:
            source.unlink()
        except OSError:
            pass
        return HXMPWriteCommit(
            record=prepared.record,
            plaintext_sha256=approved_sha256,
            latest_tx=latest_tx,
            readback_verified=True,
            receipt=dict(result),
        )

    def discard_prepared_write(self, prepared: HXMPPreparedWrite) -> None:
        """Delete a plaintext staged snapshot without executing a transaction."""

        try:
            Path(prepared.source_path).unlink()
        except FileNotFoundError:
            return


__all__ = [
    "DEFAULT_HXMP_MEMORY_LANE",
    "HXMPApprovalRequiredError",
    "HXMPCommandRunner",
    "HXMPMemoryConfig",
    "HXMPMemoryError",
    "HXMPMemoryStore",
    "HXMPPreparedWrite",
    "HXMPVerificationError",
    "HXMPWriteCommit",
    "HXMPWriteRefusedError",
    "HXMP_MEMORY_SCHEMA",
    "HXMP_MEMORY_VERSION",
    "SubprocessHXMPCommandRunner",
    "deserialize_memory_records",
    "serialize_memory_records",
]
