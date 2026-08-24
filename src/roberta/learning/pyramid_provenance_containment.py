from __future__ import annotations

from . import pyramid_provenance_scoped_reconstruction as _scoped


def _line_contained(
    line_start: int,
    line_end: int,
    ranges: tuple[tuple[int, int], ...],
) -> bool:
    """Return true only when the complete chunk/anchor is inside one allowed range."""
    return any(
        line_start >= allowed_start and line_end <= allowed_end
        for allowed_start, allowed_end in ranges
    )


def install_strict_provenance_containment() -> None:
    """Tighten scoped retrieval so boundary-straddling chunks fail closed.

    PR #189 introduced provenance candidate scoping by line overlap. That correctly
    prevents unrelated later-chapter chunks from competing, but a chunk that only
    partially overlaps a provenance range can still contain text outside the declared
    pages. Requirement 9 is stricter: final evidence anchors must not escape the
    allowed ranges. Replacing the scoped module's line predicate with containment
    applies the same fail-closed rule to candidate eligibility, retrieval filtering,
    and the final evidence-anchor validation without changing legacy book_pages or
    canonical Pyramid behavior.
    """
    if getattr(_scoped, "_strict_provenance_containment_installed", False):
        return
    _scoped._line_overlap = _line_contained
    _scoped._strict_provenance_containment_installed = True
