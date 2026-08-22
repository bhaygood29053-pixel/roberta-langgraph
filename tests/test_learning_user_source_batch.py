from datetime import datetime, timezone
import hashlib

import pytest

from roberta.learning.chunking import chunk_parsed_document
from roberta.learning.source_ingestion import InMemorySourceStore, SourceIngestionError
from roberta.learning.structure import parse_markdown_structure
from roberta.learning.user_source_batch import (
    CONTRADICTION_POLICY,
    USER_SOURCE_SPECS,
    get_user_source_spec,
    ingest_packaged_user_sources,
    ingest_user_source,
    user_source_bytes,
    user_source_text,
)


EXPECTED_KEYS = {
    "xdex_docs_2026_08_21",
    "xen_litepaper_v1_7",
    "xenft_litepaper_v0_3",
    "xone_erc20_v4",
    "mastering_blockchain_4e_2023",
    "solana_whitepaper_v0_8_13",
}
PACKAGED_KEYS = EXPECTED_KEYS - {"mastering_blockchain_4e_2023"}


def fixed_clock() -> datetime:
    return datetime(2026, 8, 21, 20, 1, tzinfo=timezone.utc)


def test_source_batch_pins_all_six_uploaded_artifacts() -> None:
    assert {spec.key for spec in USER_SOURCE_SPECS} == EXPECTED_KEYS
    assert {spec.authority_class for spec in USER_SOURCE_SPECS} <= {
        "primary",
        "secondary",
        "unknown",
    }
    assert all(spec.live_state_authorized is False for spec in USER_SOURCE_SPECS)

    mastering = get_user_source_spec("mastering_blockchain_4e_2023")
    assert mastering.original_sha256 == (
        "75e83498e8522886e422ab642f91d26f527dce5424b262fe818af59a0b1af550"
    )
    assert mastering.original_page_count == 819
    assert mastering.storage_mode == "external_exact_transcript"
    assert mastering.resource_paths == ()
    assert mastering.authority_class == "secondary"
    assert mastering.copyright_note is not None


@pytest.mark.parametrize("source_key", sorted(PACKAGED_KEYS))
def test_packaged_sources_reconstruct_exact_pinned_utf8_bytes(source_key: str) -> None:
    spec = get_user_source_spec(source_key)
    content = user_source_bytes(source_key)

    assert len(content) == spec.transcript_bytes
    assert hashlib.sha256(content).hexdigest() == spec.transcript_sha256
    assert content.decode("utf-8")


def test_xdex_preserves_exact_uploaded_bytes_and_visible_contradictions() -> None:
    spec = get_user_source_spec("xdex_docs_2026_08_21")
    content = user_source_bytes(spec.key)
    text = content.decode("utf-8")

    assert spec.original_sha256 == spec.transcript_sha256
    assert hashlib.sha256(content).hexdigest() == spec.original_sha256
    assert b"\r\n" in content
    assert "Total fee: 0.28%" in text
    assert "Each trade in the pool applies a **0.25% fee**" in text


def test_representative_pdf_transcripts_keep_source_language() -> None:
    assert "Proof of Participation" in user_source_text("xen_litepaper_v1_7")
    assert "Virtual Minting Units" in user_source_text("xenft_litepaper_v0_3")
    assert "XONE ERC20 Token" in user_source_text("xone_erc20_v4")
    assert "Proof of History" in user_source_text("solana_whitepaper_v0_8_13")


def test_external_copyrighted_reference_fails_closed_without_exact_transcript() -> None:
    with pytest.raises(SourceIngestionError, match="requires the exact external transcript bytes"):
        user_source_bytes("mastering_blockchain_4e_2023")

    with pytest.raises(SourceIngestionError, match="byte count"):
        user_source_bytes(
            "mastering_blockchain_4e_2023",
            external_transcript=b"not-the-pinned-transcript",
        )


def test_packaged_sources_reject_caller_replacement() -> None:
    with pytest.raises(SourceIngestionError, match="external replacement is not allowed"):
        user_source_bytes("xen_litepaper_v1_7", external_transcript=b"replacement")


def test_unknown_source_key_fails_closed() -> None:
    with pytest.raises(SourceIngestionError, match="unknown user source key"):
        get_user_source_spec("not-a-real-source")


def test_packaged_sources_ingest_idempotently_with_non_authorizing_metadata() -> None:
    store = InMemorySourceStore()

    first = ingest_packaged_user_sources(store=store, clock=fixed_clock)
    second = ingest_packaged_user_sources(store=store, clock=fixed_clock)

    assert len(first) == 5
    assert [item.status for item in first] == ["ingested"] * 5
    assert [item.status for item in second] == ["existing"] * 5

    for result in first:
        record = result.record
        assert record.live_state_authorized is False
        assert record.approval_status == "approved"
        assert record.status == "approved"
        assert record.metadata["untrusted_evidence_data"] is True
        assert record.metadata["instruction_authority"] is False
        assert record.metadata["current_state_authority"] is False
        assert record.metadata["memory_write_authority"] is False
        assert record.metadata["cmis_provider_trust_authority"] is False
        assert record.metadata["policy_governance_authority"] is False
        assert record.metadata["wallet_transaction_authority"] is False
        assert record.metadata["controlled_execution_authority"] is False
        assert record.metadata["contradiction_policy"] == CONTRADICTION_POLICY
        assert record.metadata["origin_live_verified"] is False


@pytest.mark.parametrize(
    "source_key",
    ("xdex_docs_2026_08_21", "solana_whitepaper_v0_8_13"),
)
def test_packaged_sources_flow_through_structure_and_chunking(
    source_key: str,
) -> None:
    store = InMemorySourceStore()
    result = ingest_user_source(source_key, store=store, clock=fixed_clock)

    parsed = parse_markdown_structure(store=store, source_id=result.record.source_id)
    chunked = chunk_parsed_document(store=store, parsed=parsed)

    assert parsed.document.source_id == result.record.source_id
    assert parsed.document.live_state_authorized is False
    assert parsed.blocks
    assert chunked.chunks
    assert chunked.live_state_authorized is False
    assert all(chunk.live_state_authorized is False for chunk in chunked.chunks)


def test_xdex_ingestion_metadata_declares_exact_original_byte_preservation() -> None:
    store = InMemorySourceStore()
    result = ingest_user_source(
        "xdex_docs_2026_08_21",
        store=store,
        clock=fixed_clock,
    )

    metadata = result.record.metadata
    assert metadata["exact_original_utf8_bytes_preserved"] is True
    assert metadata["line_ending_policy"] == "preserve_exact_user_supplied_bytes"
    assert result.record.content_hash == get_user_source_spec(
        "xdex_docs_2026_08_21"
    ).original_sha256
