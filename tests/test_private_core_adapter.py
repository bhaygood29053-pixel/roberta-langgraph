from __future__ import annotations

import os

import pytest

from roberta import bridge_http
from roberta import private_core


def test_bridge_uses_private_core_adapter() -> None:
    assert bridge_http.build_graph is private_core.build_graph


def test_required_mode_fails_closed_without_private_distribution(monkeypatch) -> None:
    monkeypatch.setattr(private_core, "_load_private_api", lambda: None)
    monkeypatch.setenv("ROBERTA_PRIVATE_CORE_REQUIRED", "1")

    with pytest.raises(private_core.PrivateCoreUnavailable):
        private_core.build_graph(model=object(), tools=[])


def test_private_contract_must_match_expected_version(monkeypatch) -> None:
    class FakePrivateAPI:
        CUTOVER_CONTRACT = "wrong/v1"

        @staticmethod
        def build_graph(*args, **kwargs):
            raise AssertionError("incompatible facade must not execute")

    monkeypatch.setattr(private_core, "_load_private_api", lambda: FakePrivateAPI)

    with pytest.raises(private_core.PrivateCoreUnavailable):
        private_core.build_graph(model=object(), tools=[])


def test_private_status_reports_expected_contract(monkeypatch) -> None:
    monkeypatch.setattr(private_core, "_load_private_api", lambda: None)
    monkeypatch.delenv("ROBERTA_PRIVATE_CORE_REQUIRED", raising=False)

    status = private_core.private_core_status()
    assert status == {
        "available": False,
        "required": False,
        "expected_contract": "roberta-private-core/v1",
    }
