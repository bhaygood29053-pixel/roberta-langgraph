from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync_local_stack.sh"


def test_sync_refreshes_current_cmis_systemd_unit_instead_of_only_restarting() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert 'bash scripts/install_cmis_systemd.sh' in source
    assert 'Environment=PYTHONPATH=$CMIS' in source
    assert 'WorkingDirectory=$CMIS' in source


def test_sync_validates_protected_freshness_runtime_before_pass() -> None:
    source = SCRIPT.read_text(encoding="utf-8")

    assert "runtime_gateway_class" in source
    assert "InstantScanEvidenceCompletionMixin" in source
    assert "_runtime_current_market_freshness_evidence" in source
    assert "freshness_resolver_registered=" in source
    assert "freshness_manager_registered=" in source
    assert "cmis_assembled_runtime=PASS" in source

    validation = source.index("cmis_assembled_runtime=PASS")
    final_pass = source.index("LOCAL_STACK_SYNC=PASS")
    assert validation < final_pass


def test_sync_checks_latest_answer_consistency_surface() -> None:
    source = SCRIPT.read_text(encoding="utf-8")
    assert 'id="roberta-answer-consistency-v1"' in source
