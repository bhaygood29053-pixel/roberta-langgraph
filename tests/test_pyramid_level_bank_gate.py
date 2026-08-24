from __future__ import annotations

import pytest

from roberta.learning.pyramid_run_cli import _select_or_exit


def test_missing_mb4e_level2_bank_exits_with_actionable_gate() -> None:
    with pytest.raises(SystemExit) as excinfo:
        _select_or_exit(
            (),
            curriculum_id="mastering_blockchain_4e_2023_book01",
            level=2,
            seed="active-seed",
            curriculum_path="/tmp/curriculum",
        )
    message = str(excinfo.value)
    assert "CURRICULUM_LEVEL_BANK_MISSING" in message
    assert "LEVEL 2" in message
    assert "ELIGIBLE 0" in message
    assert "REQUIRED 1000" in message
    assert 'BUILD_COMMAND roberta-pyramid-build-mb4e-level2 --curriculum "/tmp/curriculum"' in message
    assert "NEXT_GATE build_level_2_curriculum" in message
