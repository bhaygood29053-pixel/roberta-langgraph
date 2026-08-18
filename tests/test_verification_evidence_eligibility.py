"""Deterministic eligibility tests for persisted CMIS verification evidence."""

import json

import pytest

from roberta.cmis.http import CMISHTTPClient
from roberta.cmis.mock import MockCMISClient
from roberta.cmis.verification import normalize_verification_evidence_selector
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.planner import enforce_plan


class _Response:
    def __init__(self, payload: dict[str, object]):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def _envelope(service: str = "verification_evidence") -> dict[str, object]:
    return {
        "service": service,
        "chain": "x1",
        "status": "partial",
        "asset": {},
        "data": {
            "fact": {
                "fact_type": "pool_reserve",
                "subject_id": "x1:pool:vault",
                "normalized_value": None,
                "unit": None,
            },
            "verification": {"status": "INSUFFICIENT_EVIDENCE"},
            "evidence_ref": {"evidence_id": "ve_abc", "recorded_at": 1.0},
            "cmis_promotable": False,
        },
        "risk": None,
        "confidence": {"level": "LOW"},
        "sources": [],
        "observed_at": 1.0,
        "warnings": [],
        "errors": [],
    }


def _capabilities_response() -> _Response:
    return _Response(MockCMISClient().capabilities())


def test_selector_accepts_only_one_exact_mode() -> None:
    assert normalize_verification_evidence_selector(evidence_id=" ve_abc ") == {
        "evidence_id": "ve_abc"
    }
    assert normalize_verification_evidence_selector(
        fact_type=" pool_reserve ", subject_id=" x1:pool:vault "
    ) == {
        "fact_type": "pool_reserve",
        "subject_id": "x1:pool:vault",
    }

    invalid = [
        {},
        {"fact_type": "pool_reserve"},
        {"subject_id": "x1:pool:vault"},
        {
            "evidence_id": "ve_abc",
            "fact_type": "pool_reserve",
            "subject_id": "x1:pool:vault",
        },
    ]
    for selector in invalid:
        with pytest.raises(ValueError):
            normalize_verification_evidence_selector(**selector)


def test_http_client_posts_evidence_id_without_asset(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, *, timeout):
        captured["timeout"] = timeout
        if request.data is None:
            return _capabilities_response()
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _Response(_envelope())

    monkeypatch.setattr("roberta.cmis.http.urlopen", fake_urlopen)
    result = CMISHTTPClient(timeout_seconds=2).verification_evidence(
        chain="X1",
        evidence_id="ve_abc",
    )

    assert result["service"] == "verification_evidence"
    assert captured["payload"] == {
        "service": "verification_evidence",
        "chain": "x1",
        "params": {"evidence_id": "ve_abc"},
    }
    assert "asset" not in captured["payload"]


def test_http_client_posts_exact_fact_selector_without_asset(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_urlopen(request, *, timeout):
        if request.data is None:
            return _capabilities_response()
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _Response(_envelope())

    monkeypatch.setattr("roberta.cmis.http.urlopen", fake_urlopen)
    CMISHTTPClient(timeout_seconds=2).verification_evidence(
        chain="x1",
        fact_type="pool_reserve",
        subject_id="x1:pool:vault",
    )

    assert captured["payload"] == {
        "service": "verification_evidence",
        "chain": "x1",
        "params": {
            "fact_type": "pool_reserve",
            "subject_id": "x1:pool:vault",
        },
    }


def test_x1_scout_dispatches_explicit_evidence_selector_without_asset_identity() -> None:
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "inspect already-stored verification evidence",
                "operation": "verification_evidence",
                "evidence_id": "ve_abc",
            },
            "status": "running",
        }
    )

    assert cmis.calls == [
        {
            "operation": "verification_evidence",
            "chain": "x1",
            "evidence_id": "ve_abc",
        }
    ]
    assert result["report"]["plan"] == {
        "operations": ["verification_evidence"],
        "source": "explicit",
        "warnings": [],
    }
    assert result["report"]["source"]["operation"] == "verification_evidence"
    assert result["report"]["requested_asset"] == "AGI"
    assert result["report"]["asset"] == {}
    assert result["report"]["findings"]["data"]["cmis_promotable"] is False


def test_x1_scout_rejects_malformed_explicit_evidence_selector() -> None:
    scout = build_x1_scout_graph(MockCMISClient())

    with pytest.raises(ValueError, match="requires evidence_id OR fact_type"):
        scout.invoke(
            {
                "request": {
                    "asset": "AGI",
                    "objective": "inspect evidence",
                    "operation": "verification_evidence",
                },
                "status": "running",
            }
        )


def test_autonomous_planner_cannot_add_verification_evidence() -> None:
    plan = enforce_plan(
        {"asset": "AGI", "objective": "show current market activity"},
        {"operations": ["verification_evidence"]},
    )

    assert plan["operations"] == ["market_report"]
    assert plan["source"] == "deterministic"
    assert "planner_operation_rejected: verification_evidence" in plan["warnings"]
