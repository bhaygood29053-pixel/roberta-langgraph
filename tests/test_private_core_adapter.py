from __future__ import annotations

import pytest

from roberta import bridge_http
from roberta import private_core


def test_bridge_uses_private_core_adapter() -> None:
    assert bridge_http.build_graph is private_core.build_graph


def test_private_core_is_mandatory_after_phase3_cutover() -> None:
    assert private_core.private_core_required() is True


def test_missing_private_distribution_always_fails_closed(monkeypatch) -> None:
    monkeypatch.setattr(private_core, "_load_private_api", lambda: None)

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


def test_private_status_reports_no_public_fallback(monkeypatch) -> None:
    monkeypatch.setattr(private_core, "_load_private_api", lambda: None)

    assert private_core.private_core_status() == {
        "available": False,
        "required": True,
        "source": "unavailable",
        "expected_contract": "roberta-private-core/v1",
    }
