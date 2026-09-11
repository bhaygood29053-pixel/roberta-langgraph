from pathlib import Path

from roberta.cmis.http import CMISHTTPClient


ROOT = Path(__file__).resolve().parents[1]


def test_cmis_http_client_consumes_managed_timeout_environment(monkeypatch) -> None:
    monkeypatch.setenv("CMIS_TIMEOUT_SECONDS", "90")
    client = CMISHTTPClient.from_env()
    assert client.timeout_seconds == 90.0


def test_managed_bridge_has_evidence_completion_timeout_headroom() -> None:
    installer = (
        ROOT / "scripts" / "install_roberta_bridge_systemd.sh"
    ).read_text(encoding="utf-8")

    assert "CMIS_TIMEOUT_SECONDS=90" in installer
    assert "Environment=CMIS_TIMEOUT_SECONDS=$CMIS_TIMEOUT_SECONDS" in installer


def test_stack_sync_refreshes_and_validates_bridge_timeout_contract() -> None:
    sync = (ROOT / "scripts" / "sync_local_stack.sh").read_text(encoding="utf-8")

    assert "bash scripts/install_roberta_bridge_systemd.sh" in sync
    assert "systemctl show roberta-bridge.service -p Environment --value" in sync
    assert "CMIS_TIMEOUT_SECONDS=90" in sync
    assert "roberta_bridge_assembled_runtime=PASS" in sync
