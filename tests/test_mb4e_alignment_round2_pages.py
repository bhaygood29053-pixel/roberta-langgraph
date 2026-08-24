from __future__ import annotations

from roberta.learning.pyramid_provenance_scoped_reconstruction import (
    load_pdf_transcript_alignment,
    resolve_provenance_scope,
)
from roberta.learning.pyramid_source_provenance_compat import (
    BasisAwareSourceProvenanceLocator,
)
from roberta.learning.user_source_batch import get_user_source_spec


SOURCE_KEY = "mastering_blockchain_4e_2023"


def _alignment():
    spec = get_user_source_spec(SOURCE_KEY)
    return spec, load_pdf_transcript_alignment(
        source_key=SOURCE_KEY,
        source_artifact_sha256=spec.original_sha256,
        source_transcript_sha256=spec.transcript_sha256,
        original_page_count=spec.original_page_count,
        transcript_line_count=33988,
    )


def test_round2_distributed_systems_and_cap_pages_have_verified_alignment() -> None:
    _, alignment = _alignment()
    by_page = {entry.pdf_page: entry for entry in alignment.entries}

    expected = {
        37: (1312, 1359),
        38: (1363, 1397),
        39: (1400, 1434),
        40: (1437, 1482),
        41: (1485, 1530),
    }

    for page, (line_start, line_end) in expected.items():
        entry = by_page[page]
        assert (entry.line_start, entry.line_end) == (line_start, line_end)

    # Distributed-system definition and node behavior are on PDF page 37.
    assert by_page[37].line_start <= 1340 <= by_page[37].line_end
    assert by_page[37].line_start <= 1356 <= by_page[37].line_end

    # The CAP theorem definition and its property descriptions are on page 39.
    assert by_page[39].line_start <= 1412 <= by_page[39].line_end
    assert by_page[39].line_start <= 1425 <= by_page[39].line_end


def test_round2_pdf_37_41_scope_resolves_without_global_fallback() -> None:
    spec, alignment = _alignment()
    locator = BasisAwareSourceProvenanceLocator(
        chapter="Chapter 1",
        section="distributed systems and CAP theorem",
        page_basis="pdf",
        pages=(37, 38, 39, 40, 41),
        legacy_source_ref="MB4E-CH1-P37-41-DISTRIBUTED-CAP",
    )

    scope = resolve_provenance_scope(
        source_key=SOURCE_KEY,
        source_artifact_sha256=spec.original_sha256,
        source_transcript_sha256=spec.transcript_sha256,
        original_page_count=spec.original_page_count,
        transcript_line_count=alignment.transcript_line_count,
        locations=(locator,),
    )

    assert scope is not None
    assert scope.pdf_pages == (37, 38, 39, 40, 41)
    assert scope.alignment_hash == alignment.alignment_hash
    assert scope.line_ranges == (
        (1312, 1359),
        (1363, 1397),
        (1400, 1434),
        (1437, 1482),
        (1485, 1530),
    )
