from __future__ import annotations

import pytest

from roberta.learning.mb4e_level2_factory import (
    SOURCE_KEY,
    build_level2_bank,
    level2_provenance_records,
)


def test_level2_provenance_rejects_noncanonical_source_key_explicitly() -> None:
    exercise = build_level2_bank()[0]

    with pytest.raises(ValueError, match="must be canonical"):
        level2_provenance_records((exercise,), source_key="custom-source")

    records = level2_provenance_records((exercise,), source_key=SOURCE_KEY)
    assert records[0]["source_key"] == SOURCE_KEY
