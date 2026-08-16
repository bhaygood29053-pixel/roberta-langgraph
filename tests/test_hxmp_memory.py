"""Deterministic tests for the approval-gated HXMP durable-memory adapter."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

import pytest

from roberta.memory import MemoryCandidate, MemoryRecord
from roberta.memory.hxmp import (
    HXMPApprovalRequiredError,
    HXMPMemoryConfig,
    HXMPMemoryStore,
    HXMPVerificationError,
    HXMPWriteRefusedError,
    deserialize_memory_records,
    serialize_memory_records,
)


class FakeHXMPRunner:
    """In-process fake for the public HXMP JSON command contract."""

    def __init__(
        self,
        *,
        wallet: str = "Wallet111111111111111111111111111111111",
        lane: str = "roberta-memory",
        records: list[MemoryRecord] | None = None,
    ) -> None:
        self.wallet = wallet
        self.lane = lane
        self.records = records
        self.calls: list[tuple[str, list[str]]] = []
        self.read_verified = True
        self.dry_run_ready = True
        self.force_dry_run_hash: str | None = None
        self.write_readback_verified = True
        self.last_source_path: str | None = None

    @staticmethod
    def _value(args: list[str], name: str) -> str:
        index = args.index(name)
        return args[index + 1]

    def run(self, command: str, args: list[str]) -> dict[str, Any]:
        args = list(args)
        self.calls.append((command, args))
        if command == "read-soul":
            if self.records is None:
                return {
                    "ok": False,
                    "wallet": self.wallet,
                    "error": (
                        "No owner-matching soul.latest record found in recent signatures."
                    ),
                }
            content = serialize_memory_records(self.records)
            return {
                "ok": self.read_verified,
                "verified": self.read_verified,
                "wallet": self.wallet,
                "lane": self.lane,
                "content": content,
                "plaintext_sha256": (
                    "sha256:" + hashlib.sha256(content.encode("utf-8")).hexdigest()
                ),
            }
        if command == "dry-run-soul":
            source = self._value(args, "--source")
            self.last_source_path = source
            content = Path(source).read_bytes()
            digest = "sha256:" + hashlib.sha256(content).hexdigest()
            return {
                "ok": self.dry_run_ready,
                "command": "dry-run-soul",
                "wallet": self.wallet,
                "lane": self.lane,
                "sequence": 1,
                "previous_sha256": None,
                "plaintext_sha256": self.force_dry_run_hash or digest,
                "agentid": {"verified": self.dry_run_ready},
                "safety": {
                    "classification": "safe"
                    if self.dry_run_ready
                    else "requires_force_confirmation_or_redaction",
                    "hits": [],
                },
                "requires_confirmation": True,
            }
        if command == "write-soul":
            approved = self._value(args, "--expected-sha256")
            return {
                "ok": self.write_readback_verified,
                "wallet": self.wallet,
                "lane": self.lane,
                "plaintext_sha256": approved,
                "latest_tx": "5YverifiedLatestTx",
                "readback_verified": self.write_readback_verified,
                "receipt_links": [],
            }
        raise AssertionError(f"unexpected fake command: {command}")


class FakeKeypairWalletResolver:
    def __init__(self, wallet: str = "Wallet111111111111111111111111111111111") -> None:
        self.wallet = wallet
        self.calls: list[str] = []

    def resolve(self, keypair_path: str) -> str:
        self.calls.append(keypair_path)
        return self.wallet


def _config(*, keypair_path: str | None = None) -> HXMPMemoryConfig:
    return HXMPMemoryConfig(
        script_path="/opt/hxmp/scripts/hxmp_tools.mjs",
        wallet="Wallet111111111111111111111111111111111",
        encryption_key_path="/home/test/.hermes/x1/default/hxmp-encryption.key",
        keypair_path=keypair_path,
    )


def _record(
    key: str = "goal:roberta",
    *,
    content: str = "Build Roberta as the top-level Oracle.",
) -> MemoryRecord:
    return MemoryRecord(
        key=key,
        category="long_term_goal",
        content=content,
        topics=("roberta", "oracle"),
        source="test",
        rationale="stable project goal",
        authority="durable",
        created_at="2026-08-15T22:00:00Z",
        updated_at="2026-08-15T22:00:00Z",
    )


def test_snapshot_serialization_is_deterministic_and_roundtrips_all_fields() -> None:
    first = _record("goal:zeta", content="Zeta")
    second = MemoryRecord(
        key="policy:alpha",
        category="user_risk_policy",
        content="Alpha",
        topics=("risk", "alpha"),
        source="migration-test",
        rationale=None,
        authority="historical_context",
        created_at="2026-08-01T00:00:00Z",
        updated_at="2026-08-02T00:00:00Z",
    )

    encoded_a = serialize_memory_records([first, second])
    encoded_b = serialize_memory_records([second, first])
    decoded = deserialize_memory_records(encoded_a)

    assert encoded_a == encoded_b
    assert [record.key for record in decoded] == ["goal:zeta", "policy:alpha"]
    assert decoded[1] == second


def test_verified_hxmp_read_supports_exact_get_and_local_search() -> None:
    records = [
        _record(),
        MemoryRecord(
            key="preference:dinner",
            category="stable_preference",
            content="Prefer pasta for dinner.",
            topics=("food", "dinner"),
        ),
    ]
    runner = FakeHXMPRunner(records=records)
    store = HXMPMemoryStore(_config(), runner=runner)

    exact = store.get("goal:roberta")
    relevant = store.search("What is the Roberta oracle goal?", limit=3)

    assert exact == records[0]
    assert [record.key for record in relevant] == ["goal:roberta"]
    assert runner.calls[0][0] == "read-soul"
    assert "--show-content" in runner.calls[0][1]


def test_missing_hxmp_lane_is_treated_as_empty_memory() -> None:
    runner = FakeHXMPRunner(records=None)
    store = HXMPMemoryStore(_config(), runner=runner)

    assert store.get("missing:key") is None
    assert store.search("missing key") == []


def test_unverified_hxmp_plaintext_fails_closed() -> None:
    runner = FakeHXMPRunner(records=[_record()])
    runner.read_verified = False
    store = HXMPMemoryStore(_config(), runner=runner)

    with pytest.raises(HXMPVerificationError, match="verified plaintext"):
        store.get("goal:roberta")


def test_plain_upsert_can_never_broadcast() -> None:
    runner = FakeHXMPRunner(records=[])
    store = HXMPMemoryStore(_config(), runner=runner)

    with pytest.raises(HXMPApprovalRequiredError, match="never broadcasts"):
        store.upsert(_record())

    assert runner.calls == []


def test_prepare_candidate_runs_only_read_and_dry_run_and_stages_0600_file() -> None:
    runner = FakeHXMPRunner(records=None)
    store = HXMPMemoryStore(_config(), runner=runner)

    prepared = store.prepare_candidate(
        MemoryCandidate(
            key="goal:roberta",
            category="long_term_goal",
            content="Build Roberta as the top-level Oracle.",
            topics=("roberta", "oracle"),
        ),
        observed_at="2026-08-15T23:00:00Z",
    )

    try:
        assert prepared.ready_to_execute is True
        assert prepared.requires_approval is True
        assert prepared.record.created_at == "2026-08-15T23:00:00Z"
        assert prepared.record.updated_at == "2026-08-15T23:00:00Z"
        assert [command for command, _ in runner.calls] == [
            "read-soul",
            "dry-run-soul",
        ]
        dry_args = runner.calls[-1][1]
        assert "--wallet" in dry_args
        assert "--lane" in dry_args
        assert "--keypair" not in dry_args
        assert "--execute" not in dry_args
        assert "--confirm-write" not in dry_args
        assert prepared.preview["plaintext_sha256"] == prepared.plaintext_sha256
        assert Path(prepared.source_path).is_file()
        if os.name != "nt":
            assert (Path(prepared.source_path).stat().st_mode & 0o777) == 0o600
    finally:
        store.discard_prepared_write(prepared)

    assert not Path(prepared.source_path).exists()


def test_freshness_sensitive_candidate_is_refused_before_hxmp_access() -> None:
    runner = FakeHXMPRunner(records=None)
    store = HXMPMemoryStore(_config(), runner=runner)

    with pytest.raises(HXMPWriteRefusedError, match="freshness-sensitive"):
        store.prepare_candidate(
            MemoryCandidate(
                key="market:agi",
                category="market_snapshot",
                content="AGI price snapshot",
                topics=("agi", "price"),
            )
        )

    assert runner.calls == []


def test_dry_run_hash_mismatch_fails_closed_and_removes_staged_plaintext() -> None:
    runner = FakeHXMPRunner(records=None)
    runner.force_dry_run_hash = "sha256:" + ("0" * 64)
    store = HXMPMemoryStore(_config(), runner=runner)

    with pytest.raises(HXMPVerificationError, match="dry-run hash"):
        store.prepare_upsert(_record())

    assert runner.last_source_path is not None
    assert not Path(runner.last_source_path).exists()


def test_execute_requires_explicit_approval_and_exact_hash_before_write_command() -> None:
    runner = FakeHXMPRunner(records=None)
    resolver = FakeKeypairWalletResolver()
    store = HXMPMemoryStore(
        _config(keypair_path="/secrets/id.json"),
        runner=runner,
        keypair_wallet_resolver=resolver,
    )
    prepared = store.prepare_upsert(_record())

    try:
        before = len(runner.calls)
        with pytest.raises(HXMPApprovalRequiredError, match="explicit user approval"):
            store.execute_prepared_write(
                prepared,
                approved_sha256=prepared.plaintext_sha256,
                approved_wallet=store.config.wallet,
                approved_lane=store.config.lane,
                user_approved=False,
            )
        assert len(runner.calls) == before

        with pytest.raises(HXMPApprovalRequiredError, match="does not match"):
            store.execute_prepared_write(
                prepared,
                approved_sha256="sha256:" + ("f" * 64),
                approved_wallet=store.config.wallet,
                approved_lane=store.config.lane,
                user_approved=True,
            )
        assert len(runner.calls) == before
    finally:
        store.discard_prepared_write(prepared)


def test_execute_approved_write_uses_hxmp_flags_and_requires_verified_readback() -> None:
    runner = FakeHXMPRunner(records=None)
    resolver = FakeKeypairWalletResolver()
    store = HXMPMemoryStore(
        _config(keypair_path="/secrets/id.json"),
        runner=runner,
        keypair_wallet_resolver=resolver,
    )
    prepared = store.prepare_upsert(_record())

    commit = store.execute_prepared_write(
        prepared,
        approved_sha256=prepared.plaintext_sha256,
        approved_wallet=store.config.wallet,
        approved_lane=store.config.lane,
        user_approved=True,
    )

    command, args = runner.calls[-1]
    assert command == "write-soul"
    assert "--keypair" in args
    assert "/secrets/id.json" in args
    assert "--expected-sha256" in args
    assert prepared.plaintext_sha256 in args
    assert "--execute" in args
    assert "--confirm-write" in args
    assert resolver.calls == ["/secrets/id.json"]
    assert commit.readback_verified is True
    assert commit.latest_tx == "5YverifiedLatestTx"
    assert not Path(prepared.source_path).exists()


def test_failed_write_readback_is_not_reported_as_committed() -> None:
    runner = FakeHXMPRunner(records=None)
    runner.write_readback_verified = False
    resolver = FakeKeypairWalletResolver()
    store = HXMPMemoryStore(
        _config(keypair_path="/secrets/id.json"),
        runner=runner,
        keypair_wallet_resolver=resolver,
    )
    prepared = store.prepare_upsert(_record())

    try:
        with pytest.raises(HXMPVerificationError, match="readback verification"):
            store.execute_prepared_write(
                prepared,
                approved_sha256=prepared.plaintext_sha256,
                approved_wallet=store.config.wallet,
                approved_lane=store.config.lane,
                user_approved=True,
            )
        assert Path(prepared.source_path).exists()
    finally:
        store.discard_prepared_write(prepared)


def test_direct_prepare_upsert_cannot_bypass_freshness_sensitive_policy() -> None:
    runner = FakeHXMPRunner(records=None)
    store = HXMPMemoryStore(_config(), runner=runner)
    record = MemoryRecord(
        key="market:agi",
        category="market_snapshot",
        content="Old market snapshot",
        topics=("agi", "price"),
        authority="durable",
    )

    with pytest.raises(HXMPWriteRefusedError, match="freshness-sensitive"):
        store.prepare_upsert(record)

    assert runner.calls == []


def test_keypair_wallet_mismatch_is_refused_before_write_soul() -> None:
    runner = FakeHXMPRunner(records=None)
    resolver = FakeKeypairWalletResolver(wallet="DifferentWallet22222222222222222222222222222")
    store = HXMPMemoryStore(
        _config(keypair_path="/secrets/id.json"),
        runner=runner,
        keypair_wallet_resolver=resolver,
    )
    prepared = store.prepare_upsert(_record())

    try:
        before = len(runner.calls)
        with pytest.raises(HXMPApprovalRequiredError, match="keypair public wallet"):
            store.execute_prepared_write(
                prepared,
                approved_sha256=prepared.plaintext_sha256,
                approved_wallet=store.config.wallet,
                approved_lane=store.config.lane,
                user_approved=True,
            )
        assert len(runner.calls) == before
        assert resolver.calls == ["/secrets/id.json"]
    finally:
        store.discard_prepared_write(prepared)
