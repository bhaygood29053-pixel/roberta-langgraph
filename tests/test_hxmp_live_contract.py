"""Opt-in, read-only contract probe against the real SyntharaLabs/HXMP tool."""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

import pytest

from roberta.memory import MemoryRecord
from roberta.memory.hxmp import (
    DEFAULT_HXMP_MEMORY_LANE,
    SubprocessHXMPCommandRunner,
    serialize_memory_records,
)

pytestmark = pytest.mark.live


def _live_config() -> tuple[str, str]:
    if os.getenv("RUN_HXMP_LIVE_TESTS") != "1":
        pytest.skip("set RUN_HXMP_LIVE_TESTS=1 to run HXMP live contract probes")
    script = os.getenv("HXMP_TOOL_SCRIPT", "").strip()
    wallet = os.getenv("HXMP_WALLET", "").strip()
    if not script or not wallet:
        pytest.skip("HXMP_TOOL_SCRIPT and HXMP_WALLET are required")
    if not Path(script).expanduser().is_file():
        pytest.skip("HXMP_TOOL_SCRIPT does not point to a local hxmp_tools.mjs file")
    return script, wallet


def test_real_hxmp_rpc_and_dry_run_contract_without_keypair_or_write() -> None:
    script, wallet = _live_config()
    runner = SubprocessHXMPCommandRunner(script, timeout_seconds=45)

    health = runner.run("rpc-health", [])
    assert health.get("ok") is True
    assert isinstance(health.get("slot"), int)

    record = MemoryRecord(
        key="probe:phase7b",
        category="decision",
        content="Phase 7B uses an approval-gated HXMP durable-memory adapter.",
        topics=("roberta", "hxmp", "phase7b"),
        source="live-contract-probe",
        rationale="verify the upstream dry-run contract without broadcasting",
        authority="durable",
        created_at="2026-08-15T00:00:00Z",
        updated_at="2026-08-15T00:00:00Z",
    )
    content = serialize_memory_records([record]).encode("utf-8")
    expected_hash = "sha256:" + hashlib.sha256(content).hexdigest()

    fd, source = tempfile.mkstemp(prefix="roberta-hxmp-live-", suffix=".json")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(content)
        preview = runner.run(
            "dry-run-soul",
            [
                "--wallet",
                wallet,
                "--source",
                source,
                "--profile",
                "default",
                "--lane",
                DEFAULT_HXMP_MEMORY_LANE,
            ],
        )
    finally:
        Path(source).unlink(missing_ok=True)

    assert preview.get("command") == "dry-run-soul"
    assert preview.get("wallet") == wallet
    assert preview.get("lane") == DEFAULT_HXMP_MEMORY_LANE
    assert preview.get("plaintext_sha256") == expected_hash
    assert preview.get("requires_confirmation") is True
    assert isinstance(preview.get("agentid"), dict)
    assert isinstance(preview.get("safety"), dict)


def test_real_hxmp_read_contract_when_memory_key_is_configured() -> None:
    script, wallet = _live_config()
    encryption_key = os.getenv("HXMP_ENCRYPTION_KEY_PATH", "").strip()
    if not encryption_key:
        pytest.skip("HXMP_ENCRYPTION_KEY_PATH is required for the read-soul probe")
    if not Path(encryption_key).expanduser().is_file():
        pytest.skip("HXMP_ENCRYPTION_KEY_PATH does not point to a local key file")

    runner = SubprocessHXMPCommandRunner(script, timeout_seconds=45)
    result = runner.run(
        "read-soul",
        [
            "--wallet",
            wallet,
            "--encryption-key",
            encryption_key,
            "--lane",
            DEFAULT_HXMP_MEMORY_LANE,
            "--show-content",
        ],
    )

    assert result.get("wallet") == wallet
    if result.get("ok") is False:
        assert "No owner-matching soul.latest record found" in str(result.get("error", ""))
        return

    assert result.get("ok") is True
    assert result.get("verified") is True
    assert result.get("lane") == DEFAULT_HXMP_MEMORY_LANE
    assert isinstance(result.get("plaintext_sha256"), str)
    assert isinstance(result.get("content"), str)
