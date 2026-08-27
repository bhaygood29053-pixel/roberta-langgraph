"""Boundary tests for X1 Scout -> CMIS."""

import pytest

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph, select_cmis_operation


def test_x1_scout_routes_market_risk_objective_to_risk_check() -> None:
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": "agi",
                "objective": "assess market risk",
            },
            "status": "running",
        }
    )

    assert cmis.calls == [
        {
            "operation": "risk_check",
            "chain": "x1",
            "asset": "AGI",
        }
    ]

    report = result["report"]
    assert result["status"] == "complete"
    assert report["specialist"] == "x1_scout"
    assert report["chain"] == "x1"
    assert report["requested_asset"] == "agi"
    assert report["asset"] == {"symbol": "AGI"}
    assert report["source"] == {
        "service": "cmis",
        "operation": "risk_check",
    }
    assert report["cmis_status"] == "partial"
    assert report["observed_at"] == "2026-08-15T21:45:00Z"
    assert report["observed_at_iso"] == "2026-08-15T21:45:00Z"
    assert report["confidence"] == {"level": "TEST_ONLY"}
    assert report["findings"]["risk"] == {
        "outcome": "TEST_ONLY",
        "score": None,
        "flags": ["NOT_LIVE_DATA"],
    }
    assert report["errors"] == []


XENCAT_MINT = "DQ6sApYPMJ8LwpvyUjthL7amykNBJ3fx5jZi2koN7vHb"


def test_x1_scout_preflights_exact_mint_and_preserves_cmis_normalized_identity() -> None:
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": XENCAT_MINT,
                "objective": "assess market risk",
            },
            "status": "running",
        }
    )

    assert cmis.calls == [
        {
            "operation": "asset_lookup",
            "chain": "x1",
            "asset": XENCAT_MINT,
        },
        {
            "operation": "risk_check",
            "chain": "x1",
            "asset": XENCAT_MINT,
        },
    ]
    report = result["report"]
    assert report["requested_asset"] == XENCAT_MINT
    assert report["asset"] == {
        "symbol": "TEST",
        "name": "Test Asset",
        "mint": XENCAT_MINT,
    }
    assert report["normalized_asset_identity"]["mint"] == XENCAT_MINT
    assert report["normalized_asset_identity"]["identity_root"] == "mint"
    assert report["asset_identity_reconciliation"]["state"] == "agreement"
    assert report["asset_identity_status"] == "partial"
    assert report["source"]["operation"] == "risk_check"


def test_x1_scout_does_not_preflight_symbol_queries() -> None:
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis)

    scout.invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "assess market risk",
            },
            "status": "running",
        }
    )

    assert [call["operation"] for call in cmis.calls] == ["risk_check"]


def test_x1_scout_skips_normalized_identity_reliance_on_cmis_1_10() -> None:
    class OldCMIS(MockCMISClient):
        def capabilities(self):
            manifest = super().capabilities()
            manifest["contract_version"] = "1.10.0"
            return manifest

    cmis = OldCMIS()
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": XENCAT_MINT,
                "objective": "assess market risk",
            },
            "status": "running",
        }
    )

    assert [call["operation"] for call in cmis.calls] == ["risk_check"]
    assert "normalized_asset_identity" not in result["report"]


def test_x1_scout_preserves_cmis_descriptor_conflict_without_recomputing_it() -> None:
    class ConflictCMIS(MockCMISClient):
        def asset_lookup(self, *, chain: str, asset: str):
            result = super().asset_lookup(chain=chain, asset=asset)
            result["data"]["normalized_identity"]["symbol"] = "META"
            result["data"]["normalized_identity"]["name"] = "Metadata Name"
            result["data"]["identity_reconciliation"] = {
                "state": "descriptor_conflict",
                "comparable_fields": ["symbol", "name"],
                "conflicting_fields": ["symbol", "name"],
                "metaplex": {"mint": asset, "symbol": "META"},
                "xdex": {
                    "available": True,
                    "present": True,
                    "variants": [{"mint": asset, "symbol": "XDEX"}],
                },
            }
            result["warnings"].append(
                {
                    "code": "x1_asset_descriptor_conflict",
                    "message": "test conflict",
                }
            )
            return result

    cmis = ConflictCMIS()
    scout = build_x1_scout_graph(cmis)
    result = scout.invoke(
        {
            "request": {
                "asset": XENCAT_MINT,
                "objective": "assess market risk",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["asset"]["mint"] == XENCAT_MINT
    assert report["asset"]["symbol"] == "META"
    assert report["asset_identity_reconciliation"]["state"] == "descriptor_conflict"
    assert report["asset_identity_reconciliation"]["conflicting_fields"] == [
        "symbol",
        "name",
    ]
    assert any(
        warning.get("code") == "x1_asset_descriptor_conflict"
        for warning in report["warnings"]
    )


def test_x1_scout_preserves_raw_numeric_observed_at_and_adds_iso() -> None:
    cmis = MockCMISClient()
    cmis.observed_at = 1786835050.0581603
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "assess market risk",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["observed_at"] == 1786835050.0581603
    assert report["observed_at_iso"] == "2026-08-15T23:04:10.058160Z"


@pytest.mark.parametrize(
    ("objective", "expected"),
    [
        ("check market risk", "risk_check"),
        ("is this asset safe?", "risk_check"),
        ("check token supply", "tokenomics"),
        ("verify mint authority", "tokenomics"),
        ("show price and liquidity", "market_report"),
        ("current market activity", "market_report"),
    ],
)
def test_objective_planner_selects_minimum_required_operation(
    objective: str,
    expected: str,
) -> None:
    assert select_cmis_operation(objective) == expected


@pytest.mark.parametrize(
    "operation",
    ["market_report", "tokenomics", "risk_check", "pre_trade_check"],
)
def test_x1_scout_dispatches_explicit_cmis_operations(operation: str) -> None:
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis)
    request: dict[str, object] = {
        "asset": "AGI",
        "objective": f"exercise {operation}",
        "operation": operation,
    }
    if operation == "pre_trade_check":
        request.update({"action": "BUY", "amount_usd": 500.0})

    result = scout.invoke({"request": request, "status": "running"})

    assert cmis.calls[0]["operation"] == operation
    assert cmis.calls[0]["chain"] == "x1"
    assert result["report"]["source"]["operation"] == operation
    assert result["report"]["cmis_status"] == "partial"
    assert result["report"]["status"] == "complete"


@pytest.mark.parametrize("scenario,status", [("unavailable", "unavailable"), ("error", "error")])
def test_x1_scout_propagates_failed_cmis_state_without_fabrication(
    scenario: str,
    status: str,
) -> None:
    cmis = MockCMISClient(scenario=scenario)
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "assess market risk",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert cmis.calls[0]["operation"] == "risk_check"
    assert result["status"] == "error"
    assert report["status"] == "error"
    assert report["cmis_status"] == status
    assert report["findings"]["risk"] is None
