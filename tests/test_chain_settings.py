"""Tests for explicit chain-provider runtime gates."""

import pytest

from roberta.config import RobertaChainSettings


def test_solana_provider_gate_defaults_closed(monkeypatch) -> None:
    monkeypatch.delenv("ROBERTA_SOLANA_PROVIDER_ENABLED", raising=False)

    settings = RobertaChainSettings.from_env()

    assert settings.solana_provider_enabled is False


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "on"])
def test_solana_provider_gate_accepts_explicit_true(monkeypatch, value: str) -> None:
    monkeypatch.setenv("ROBERTA_SOLANA_PROVIDER_ENABLED", value)

    settings = RobertaChainSettings.from_env()

    assert settings.solana_provider_enabled is True


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "off", ""])
def test_solana_provider_gate_accepts_explicit_false(monkeypatch, value: str) -> None:
    monkeypatch.setenv("ROBERTA_SOLANA_PROVIDER_ENABLED", value)

    settings = RobertaChainSettings.from_env()

    assert settings.solana_provider_enabled is False


def test_solana_provider_gate_rejects_ambiguous_value(monkeypatch) -> None:
    monkeypatch.setenv("ROBERTA_SOLANA_PROVIDER_ENABLED", "maybe")

    with pytest.raises(ValueError, match="ROBERTA_SOLANA_PROVIDER_ENABLED"):
        RobertaChainSettings.from_env()
