from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from . import pyramid_source_reconstruction as _reconstruction
from .curriculum_io import TrustedSourceBinding
from .user_source_batch import get_user_source_spec


_ORIGINAL_LOAD_SOURCE_PROVENANCE = _reconstruction.load_source_provenance_jsonl


@dataclass(frozen=True, slots=True)
class BasisAwareSourceProvenanceLocator:
    chapter: str
    section: str
    page_basis: str
    pages: tuple[int, ...]
    legacy_source_ref: str | None = None

    @property
    def book_pages(self) -> tuple[int, ...]:
        return self.pages if self.page_basis == "book" else ()

    @property
    def pdf_pages(self) -> tuple[int, ...]:
        return self.pages if self.page_basis == "pdf" else ()


def _positive_pages(name: str, value: object) -> tuple[int, ...]:
    if (
        not isinstance(value, list)
        or not value
        or not all(
            isinstance(page, int) and not isinstance(page, bool) and page > 0
            for page in value
        )
    ):
        raise _reconstruction.PyramidSourceReconstructionError(
            f"source provenance {name} are malformed"
        )
    return tuple(value)


def _basis_aware_locator(
    raw: object,
) -> _reconstruction.SourceProvenanceLocator | BasisAwareSourceProvenanceLocator:
    if not isinstance(raw, Mapping):
        raise _reconstruction.PyramidSourceReconstructionError(
            "source provenance locator must be an object"
        )
    chapter = _reconstruction._text("source provenance chapter", raw.get("chapter"))
    section = _reconstruction._text("source provenance section", raw.get("section"))
    has_book_pages = "book_pages" in raw
    has_pdf_pages = "pdf_pages" in raw
    if has_book_pages == has_pdf_pages:
        raise _reconstruction.PyramidSourceReconstructionError(
            "source provenance locator must declare exactly one of book_pages or pdf_pages"
        )

    if has_book_pages:
        # Preserve the accepted public in-memory representation for every
        # pre-existing printed-book provenance package. The compatibility seam
        # extends only the new PDF-page path; it must not change the locator
        # class, dataclass field shape, isinstance behavior, or pattern-matching
        # surface for legacy book_pages callers.
        return _reconstruction.SourceProvenanceLocator(
            chapter=chapter,
            section=section,
            book_pages=_positive_pages("book_pages", raw.get("book_pages")),
        )

    pages = _positive_pages("pdf_pages", raw.get("pdf_pages"))
    legacy_source_ref = raw.get("legacy_source_ref")
    if legacy_source_ref is not None:
        legacy_source_ref = _reconstruction._text(
            "source provenance legacy_source_ref",
            legacy_source_ref,
        )
    return BasisAwareSourceProvenanceLocator(
        chapter=chapter,
        section=section,
        page_basis="pdf",
        pages=pages,
        legacy_source_ref=legacy_source_ref,
    )


def _basis_aware_locator_mapping(value: object) -> dict[str, Any]:
    if isinstance(value, BasisAwareSourceProvenanceLocator):
        mapping: dict[str, Any] = {
            "chapter": value.chapter,
            "section": value.section,
            f"{value.page_basis}_pages": list(value.pages),
        }
        if value.legacy_source_ref is not None:
            mapping["legacy_source_ref"] = value.legacy_source_ref
        return mapping

    # Preserve the exact accepted representation for pre-existing reconstruction
    # objects created from printed-book provenance.
    if isinstance(value, _reconstruction.SourceProvenanceLocator):
        return {
            "chapter": value.chapter,
            "section": value.section,
            "book_pages": list(value.book_pages),
        }
    raise _reconstruction.PyramidSourceReconstructionError(
        "source provenance locator cannot be serialized"
    )


def _trusted_source_binding(source_key: str) -> TrustedSourceBinding:
    spec = get_user_source_spec(source_key)
    return TrustedSourceBinding(
        source_artifact_sha256=spec.original_sha256,
        source_transcript_sha256=spec.transcript_sha256,
        source_title=spec.title,
        source_version=spec.version,
        source_origin=spec.origin,
        source_authority_class=spec.authority_class,
        original_media_type=spec.original_media_type,
        original_page_count=spec.original_page_count,
    )


def _trusted_provenance_loader(
    path: object,
    *,
    expected_source_key: str,
    expected_exercise_ids: set[str],
    trusted_source: TrustedSourceBinding | None = None,
):
    """Preserve trusted PDF metadata when reconstruction reloads provenance."""

    binding = trusted_source or _trusted_source_binding(expected_source_key)
    return _ORIGINAL_LOAD_SOURCE_PROVENANCE(
        path,
        expected_source_key=expected_source_key,
        expected_exercise_ids=expected_exercise_ids,
        trusted_source=binding,
    )


def install_basis_aware_source_provenance() -> None:
    """Install PDF provenance compatibility and provenance-scoped retrieval.

    Existing ``book_pages`` inputs retain the original public locator class and
    reconstruction behavior. Migrated ``pdf_pages`` inputs retain their basis and
    trusted PDF metadata, then use a cryptographically bound PDF-page-to-transcript
    alignment before retrieval so out-of-provenance chunks cannot compete in
    lexical/vector ranking. Scoped chunks and final anchors must be fully contained
    inside the resolved provenance ranges. Checkpoint validation, canonical exam
    behavior, source integrity, and all authority boundaries remain unchanged.
    """

    if not getattr(
        _reconstruction,
        "_basis_aware_source_provenance_installed",
        False,
    ):
        _reconstruction._locator = _basis_aware_locator
        _reconstruction._locator_mapping = _basis_aware_locator_mapping
        _reconstruction.load_source_provenance_jsonl = _trusted_provenance_loader
        _reconstruction._basis_aware_source_provenance_installed = True

    # Import lazily after the locator/loader seam is active. The scoped builder
    # relies on those basis-aware provenance objects but does not alter their
    # public representation.
    from .pyramid_provenance_scoped_reconstruction import (
        install_provenance_scoped_reconstruction,
    )

    install_provenance_scoped_reconstruction()

    # Tighten the scoped line predicate after the builder/retrieval hooks exist so
    # a boundary-straddling chunk cannot become an evidence anchor merely because
    # part of it overlaps the declared pages.
    from .pyramid_provenance_containment import (
        install_strict_provenance_containment,
    )

    install_strict_provenance_containment()
