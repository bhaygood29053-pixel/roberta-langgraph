"""Approved static user-supplied blockchain sources for the Learning System.

This module binds exact user-uploaded provenance to deterministic UTF-8 source
artifacts without granting source text any runtime, memory, live-state, policy,
wallet, transaction, CMIS/provider, or Controlled Execution authority.

PDF inputs are represented by deterministic derivative transcripts because the
accepted Learning System source contract is UTF-8 text. The original PDF
SHA-256/page count remains immutable provenance. The copyrighted Mastering
Blockchain reference is intentionally not republished in this repository:
callers must supply the exact precomputed transcript bytes and they are accepted
only when their pinned SHA-256 matches.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import base64
import gzip
import hashlib
from importlib.resources import files
from typing import Callable

from .source_ingestion import (
    IngestionResult,
    SourceIngestionError,
    SourceStore,
    ingest_utf8_source,
)


TRANSCRIPTION_PROFILE = "poppler-pdftotext-layout-clean-c0/v1"
EXACT_UTF8_PROFILE = "exact-user-supplied-utf8/v1"
STATIC_AUTHORITY_SCOPE = "static_learning_evidence_only"
CONTRADICTION_POLICY = "preserve_do_not_silently_reconcile"


@dataclass(frozen=True, slots=True)
class UserSourceSpec:
    """Immutable source-package/integrity contract for one uploaded source."""

    key: str
    title: str
    version: str
    origin: str
    authority_class: str
    source_kind: str
    original_media_type: str
    original_sha256: str
    original_bytes: int
    original_page_count: int | None
    transcript_sha256: str
    transcript_bytes: int
    transcription_profile: str
    storage_mode: str
    resource_paths: tuple[str, ...] = ()
    packaged_gzip_sha256: str | None = None
    copyright_note: str | None = None

    @property
    def live_state_authorized(self) -> bool:
        return False


USER_SOURCE_SPECS: tuple[UserSourceSpec, ...] = (
    UserSourceSpec(
        key="xdex_docs_2026_08_21",
        title="XDEX Documentation Snapshot",
        version="2026-08-21-user-supplied",
        origin="user-upload://xdex-docs/2026-08-21",
        authority_class="unknown",
        source_kind="documentation_snapshot",
        original_media_type="text/plain; charset=utf-8",
        original_sha256="5298a12395ad152ba3f440bf3a9fe3ccf62e5ebd507ff72d2a57e691bd007909",
        original_bytes=115631,
        original_page_count=None,
        transcript_sha256="5298a12395ad152ba3f440bf3a9fe3ccf62e5ebd507ff72d2a57e691bd007909",
        transcript_bytes=115631,
        transcription_profile=EXACT_UTF8_PROFILE,
        storage_mode="packaged_gzip_base64_parts",
        resource_paths=(
            "sources/xdex_docs_snapshot_2026_08_21.part0.gz.b64",
            "sources/xdex_docs_snapshot_2026_08_21.part1.gz.b64",
            "sources/xdex_docs_snapshot_2026_08_21.part2.gz.b64",
        ),
        packaged_gzip_sha256="6cad7ebb6ede14ced174d47012c73189031e32a6e2bd1c62c2d84587ada60cb8",
    ),
    UserSourceSpec(
        key="xen_litepaper_v1_7",
        title="XEN Litepaper",
        version="v1.7",
        origin="user-upload://xen-litepaper/v1.7",
        authority_class="primary",
        source_kind="litepaper_transcript",
        original_media_type="application/pdf",
        original_sha256="1234e95b33b8219e5388a14fecf07309e27b7e43f10ba87208f3a0bfbc0f4c10",
        original_bytes=331729,
        original_page_count=15,
        transcript_sha256="8dbd1d70d29288af86bec23713a18ad79b7212ca1aff5d1d859a081a07f7cc62",
        transcript_bytes=41935,
        transcription_profile=TRANSCRIPTION_PROFILE,
        storage_mode="packaged_gzip_base64_parts",
        resource_paths=("sources/xen_litepaper_v1_7.gz.b64",),
        packaged_gzip_sha256="d4f076e210eab54d638164c0929d654b71a34dee9d4ab3a530e265f4e1f600ff",
    ),
    UserSourceSpec(
        key="xenft_litepaper_v0_3",
        title="XEN Torrent Litepaper",
        version="v0.3",
        origin="user-upload://xenft-litepaper/v0.3",
        authority_class="primary",
        source_kind="litepaper_transcript",
        original_media_type="application/pdf",
        original_sha256="501ba4f3b8a199b91bba2c17aaaa897215896c898d80b6f3da833be3199db266",
        original_bytes=613296,
        original_page_count=17,
        transcript_sha256="28bfc0b2c59f1c96496be7ac64e901a8886ab86522ac611d5f749cef84451cb1",
        transcript_bytes=26694,
        transcription_profile=TRANSCRIPTION_PROFILE,
        storage_mode="packaged_gzip_base64_parts",
        resource_paths=("sources/xenft_litepaper_v0_3.gz.b64",),
        packaged_gzip_sha256="154104af40acc4947514a0b48b06bcdaae5110724c2b4134c8702c58ed1014b9",
    ),
    UserSourceSpec(
        key="xone_erc20_v4",
        title="XONE ERC20 Token",
        version="v4",
        origin="user-upload://xone-erc20/v4",
        authority_class="unknown",
        source_kind="token_design_transcript",
        original_media_type="application/pdf",
        original_sha256="0e21aead464b1b94b1741ac55d815c086da297fffaf54e31337454b8a75d2f7f",
        original_bytes=60811,
        original_page_count=3,
        transcript_sha256="bd8492adbcd058c5270815964af7ae5a21a37b6d1ae2a9ed7fc7991eb884c4c5",
        transcript_bytes=4139,
        transcription_profile=TRANSCRIPTION_PROFILE,
        storage_mode="packaged_gzip_base64_parts",
        resource_paths=("sources/xone_erc20_v4.gz.b64",),
        packaged_gzip_sha256="13a739d83f4cec3cdf01413e0905d06c87e89c2963f58ffa65fd2e3ecc4db2e3",
    ),
    UserSourceSpec(
        key="mastering_blockchain_4e_2023",
        title="Mastering Blockchain: Fourth Edition",
        version="Fourth Edition (2023)",
        origin="user-upload://mastering-blockchain/fourth-edition-2023",
        authority_class="secondary",
        source_kind="educational_reference_transcript",
        original_media_type="application/pdf",
        original_sha256="75e83498e8522886e422ab642f91d26f527dce5424b262fe818af59a0b1af550",
        original_bytes=22526945,
        original_page_count=819,
        transcript_sha256="69f6429ed1515d5543bcaf67dd65701f892ea3127ac092f21eca6f93c57f8dac",
        transcript_bytes=2027459,
        transcription_profile=TRANSCRIPTION_PROFILE,
        storage_mode="external_exact_transcript",
        copyright_note=(
            "User-supplied copyrighted reference; repository stores provenance "
            "and integrity contract only, not the book transcript."
        ),
    ),
    UserSourceSpec(
        key="solana_whitepaper_v0_8_13",
        title="Solana: A new architecture for a high performance blockchain",
        version="v0.8.13",
        origin="user-upload://solana-whitepaper/v0.8.13",
        authority_class="primary",
        source_kind="whitepaper_transcript",
        original_media_type="application/pdf",
        original_sha256="17c29f7785ff3a7e457f0de10fb86556090c5b398bfaa20a602116e700519b28",
        original_bytes=689365,
        original_page_count=32,
        transcript_sha256="dfa397e48c0ade3e51ab5aa5dcbce237ae282d3a4e72a99b307d1c1351e5091d",
        transcript_bytes=54019,
        transcription_profile=TRANSCRIPTION_PROFILE,
        storage_mode="packaged_gzip_base64_parts",
        resource_paths=(
            "sources/solana_whitepaper_v0_8_13.part0.gz.b64",
            "sources/solana_whitepaper_v0_8_13.part1.gz.b64",
            "sources/solana_whitepaper_v0_8_13.part2.gz.b64",
            "sources/solana_whitepaper_v0_8_13.part3.gz.b64",
        ),
        packaged_gzip_sha256="88481b114a63bfbd2d0aa58319814872ae690b6cb604527be8a25a9ad4d7c462",
    ),
)

_SPECS_BY_KEY = {spec.key: spec for spec in USER_SOURCE_SPECS}


def get_user_source_spec(source_key: str) -> UserSourceSpec:
    """Return the immutable source spec or fail closed for an unknown key."""

    try:
        return _SPECS_BY_KEY[source_key]
    except (KeyError, TypeError) as exc:
        raise SourceIngestionError(f"unknown user source key: {source_key!r}") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _validate_transcript_bytes(spec: UserSourceSpec, content: bytes) -> bytes:
    value = bytes(content)
    if len(value) != spec.transcript_bytes:
        raise SourceIngestionError(
            f"{spec.key} transcript byte count does not match pinned provenance"
        )
    if _sha256(value) != spec.transcript_sha256:
        raise SourceIngestionError(
            f"{spec.key} transcript does not match pinned SHA-256"
        )
    try:
        value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SourceIngestionError(
            f"{spec.key} transcript must be valid UTF-8"
        ) from exc
    return value


def _packaged_transcript_bytes(spec: UserSourceSpec) -> bytes:
    if spec.storage_mode != "packaged_gzip_base64_parts":
        raise SourceIngestionError(f"{spec.key} is not a packaged source")
    if not spec.resource_paths or spec.packaged_gzip_sha256 is None:
        raise SourceIngestionError(f"{spec.key} has incomplete packaged-source metadata")

    root = files("roberta.learning")
    compressed_parts: list[bytes] = []
    for resource_path in spec.resource_paths:
        encoded = root.joinpath(resource_path).read_bytes()
        try:
            ascii_payload = encoded.decode("ascii").strip()
        except UnicodeDecodeError as exc:
            raise SourceIngestionError(
                f"{spec.key} packaged source must contain ASCII base64"
            ) from exc
        try:
            compressed_parts.append(
                base64.b64decode(ascii_payload, validate=True)
            )
        except (ValueError, base64.binascii.Error) as exc:
            raise SourceIngestionError(
                f"{spec.key} packaged source has invalid base64"
            ) from exc

    compressed = b"".join(compressed_parts)
    if _sha256(compressed) != spec.packaged_gzip_sha256:
        raise SourceIngestionError(
            f"{spec.key} packaged gzip does not match pinned SHA-256"
        )
    try:
        transcript = gzip.decompress(compressed)
    except (OSError, EOFError) as exc:
        raise SourceIngestionError(
            f"{spec.key} packaged gzip could not be decompressed"
        ) from exc
    return _validate_transcript_bytes(spec, transcript)


def user_source_bytes(
    source_key: str,
    *,
    external_transcript: bytes | None = None,
) -> bytes:
    """Return exact ingestible UTF-8 bytes after all integrity checks.

    Packaged sources reject caller-supplied replacements. The copyrighted
    Mastering Blockchain source is the inverse: it requires externally supplied
    transcript bytes and accepts them only after exact length/SHA validation.
    """

    spec = get_user_source_spec(source_key)
    if spec.storage_mode == "packaged_gzip_base64_parts":
        if external_transcript is not None:
            raise SourceIngestionError(
                f"{spec.key} uses pinned packaged bytes; external replacement is not allowed"
            )
        return _packaged_transcript_bytes(spec)

    if spec.storage_mode == "external_exact_transcript":
        if external_transcript is None:
            raise SourceIngestionError(
                f"{spec.key} requires the exact external transcript bytes"
            )
        if not isinstance(external_transcript, bytes):
            raise SourceIngestionError(
                f"{spec.key} external transcript must be bytes"
            )
        return _validate_transcript_bytes(spec, external_transcript)

    raise SourceIngestionError(f"unsupported storage mode for {spec.key}")


def user_source_text(
    source_key: str,
    *,
    external_transcript: bytes | None = None,
) -> str:
    """Return integrity-validated UTF-8 text."""

    return user_source_bytes(
        source_key,
        external_transcript=external_transcript,
    ).decode("utf-8")


def _metadata_for(spec: UserSourceSpec) -> dict[str, object]:
    metadata: dict[str, object] = {
        "source_kind": spec.source_kind,
        "original_media_type": spec.original_media_type,
        "original_artifact_sha256": spec.original_sha256,
        "original_artifact_bytes": spec.original_bytes,
        "original_artifact_provenance": "user_supplied_upload",
        "origin_live_verified": False,
        "transcript_media_type": "text/plain; charset=utf-8",
        "transcript_sha256": spec.transcript_sha256,
        "transcript_bytes": spec.transcript_bytes,
        "transcription_profile": spec.transcription_profile,
        "storage_mode": spec.storage_mode,
        "authority_scope": STATIC_AUTHORITY_SCOPE,
        "untrusted_evidence_data": True,
        "instruction_authority": False,
        "current_state_authority": False,
        "memory_write_authority": False,
        "cmis_provider_trust_authority": False,
        "policy_governance_authority": False,
        "wallet_transaction_authority": False,
        "controlled_execution_authority": False,
        "contradiction_policy": CONTRADICTION_POLICY,
    }
    if spec.original_page_count is not None:
        metadata["original_pdf_page_count"] = spec.original_page_count
    if spec.packaged_gzip_sha256 is not None:
        metadata["packaged_gzip_sha256"] = spec.packaged_gzip_sha256
    if spec.copyright_note is not None:
        metadata["copyright_note"] = spec.copyright_note
        metadata["repository_republication"] = False
    if spec.key == "xdex_docs_2026_08_21":
        metadata["exact_original_utf8_bytes_preserved"] = True
        metadata["line_ending_policy"] = "preserve_exact_user_supplied_bytes"
    return metadata


def ingest_user_source(
    source_key: str,
    *,
    store: SourceStore,
    external_transcript: bytes | None = None,
    clock: Callable[[], datetime] | None = None,
) -> IngestionResult:
    """Ingest one approved static source through the Phase 1 UTF-8 contract."""

    spec = get_user_source_spec(source_key)
    content = user_source_bytes(
        source_key,
        external_transcript=external_transcript,
    )
    common = dict(
        store=store,
        content=content,
        origin=spec.origin,
        title=spec.title,
        version=spec.version,
        authority_class=spec.authority_class,
        approval_status="approved",
        parser_version="utf8-source/v1",
        metadata=_metadata_for(spec),
    )
    if clock is None:
        return ingest_utf8_source(**common)
    return ingest_utf8_source(**common, clock=clock)


def ingest_packaged_user_sources(
    *,
    store: SourceStore,
    clock: Callable[[], datetime] | None = None,
) -> tuple[IngestionResult, ...]:
    """Ingest every repository-packaged source, excluding external-only content."""

    results: list[IngestionResult] = []
    for spec in USER_SOURCE_SPECS:
        if spec.storage_mode != "packaged_gzip_base64_parts":
            continue
        if clock is None:
            results.append(ingest_user_source(spec.key, store=store))
        else:
            results.append(ingest_user_source(spec.key, store=store, clock=clock))
    return tuple(results)
