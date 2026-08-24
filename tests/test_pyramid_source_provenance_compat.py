from __future__ import annotations

from dataclasses import asdict

import pytest

from roberta.learning import pyramid_source_reconstruction as reconstruction
from roberta.learning.pyramid_source_provenance_compat import (
    BasisAwareSourceProvenanceLocator,
    install_basis_aware_source_provenance,
)


def test_learning_package_installs_pdf_locator_support_for_programmatic_reconstruction_api() -> None:
    # Importing the Learning package is the normal boundary even for callers
    # that request the reconstruction submodule directly. The compatibility
    # seam must already be active before a caller invokes the builder.
    assert getattr(reconstruction, "_basis_aware_source_provenance_installed", False) is True

    locator = reconstruction._locator(
        {
            "chapter": "Chapter 1",
            "section": "legacy PDF provenance",
            "pdf_pages": [34, 35],
            "legacy_source_ref": "MB4E-CH1-P34-35-FIXTURE",
        }
    )
    assert isinstance(locator, BasisAwareSourceProvenanceLocator)
    assert reconstruction._locator_mapping(locator)["pdf_pages"] == [34, 35]


def test_basis_aware_adapter_preserves_pdf_pages_and_legacy_source_ref() -> None:
    install_basis_aware_source_provenance()

    locator = reconstruction._locator(
        {
            "chapter": "Chapter 1",
            "section": "benefits and limitations",
            "pdf_pages": [53, 54, 55, 56],
            "legacy_source_ref": "MB4E-CH1-P53-56-BENEFITS-LIMITS",
        }
    )

    assert isinstance(locator, BasisAwareSourceProvenanceLocator)
    assert locator.page_basis == "pdf"
    assert locator.pages == (53, 54, 55, 56)
    assert locator.book_pages == ()
    assert locator.pdf_pages == (53, 54, 55, 56)
    assert reconstruction._locator_mapping(locator) == {
        "chapter": "Chapter 1",
        "section": "benefits and limitations",
        "pdf_pages": [53, 54, 55, 56],
        "legacy_source_ref": "MB4E-CH1-P53-56-BENEFITS-LIMITS",
    }


def test_basis_aware_adapter_preserves_existing_book_locator_public_type_and_shape() -> None:
    install_basis_aware_source_provenance()

    locator = reconstruction._locator(
        {
            "chapter": "Chapter 1",
            "section": "Blocks",
            "book_pages": [12, 13],
        }
    )

    assert type(locator) is reconstruction.SourceProvenanceLocator
    assert isinstance(locator, reconstruction.SourceProvenanceLocator)
    assert not isinstance(locator, BasisAwareSourceProvenanceLocator)
    assert asdict(locator) == {
        "chapter": "Chapter 1",
        "section": "Blocks",
        "book_pages": (12, 13),
    }
    assert reconstruction._locator_mapping(locator) == {
        "chapter": "Chapter 1",
        "section": "Blocks",
        "book_pages": [12, 13],
    }


@pytest.mark.parametrize(
    "raw",
    [
        {"chapter": "Chapter 1", "section": "x"},
        {
            "chapter": "Chapter 1",
            "section": "x",
            "book_pages": [1],
            "pdf_pages": [1],
        },
    ],
)
def test_basis_aware_adapter_rejects_ambiguous_page_basis(raw: dict[str, object]) -> None:
    install_basis_aware_source_provenance()

    with pytest.raises(
        reconstruction.PyramidSourceReconstructionError,
        match="exactly one of book_pages or pdf_pages",
    ):
        reconstruction._locator(raw)
