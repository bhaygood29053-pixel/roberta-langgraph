from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import patch

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout import build_x1_scout_tool
from roberta.x1_scout.daily_brief_tool import (
    is_x1_daily_intelligence_brief_objective,
)
from roberta.x1_scout.daily_intelligence_brief_workflow import (
    X1_DAILY_BRIEF_SCOPE_SELECTION_CONTRACT,
    run_x1_daily_intelligence_brief_workflow,
)


C05 = "Give me today's X1 intelligence brief and tell me what deserves attention."
MINT_A = "7SXmUpcBGSAwW5LmtzQVF9jHswZ7xzmdKqWa4nDgL3ER"
MINT_B = "AnvCcvnY4DLRW42EZBEAb1QeU6Pt9aab3r3D75GtgJUUJ"


def test_canonical_c05_intent_is_recognized_without_asset_guessing() -> None:
    assert is_x1_daily_intelligence_brief_objective(C05) is True
    assert is_x1_daily_intelligence_brief_objective("What changed on X1 today?") is True
    assert is_x1_daily_intelligence_brief_objective("Top 10 XDEX tokens by volume") is False


def test_c05_overrides_model_proposed_xdex_asset_lookup() -> None:
    client = MockCMISClient()
    expected = {
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_scope": "x1_daily_intelligence_brief",
        "source": {"service": "cmis", "operation": "x1_intelligence_brief_inputs"},
        "execution_authorized": False,
    }

    with patch(
        "roberta.x1_scout.daily_brief_tool.run_x1_daily_intelligence_brief_workflow",
        return_value=expected,
    ) as run:
        tool = build_x1_scout_tool(client)
        rendered = tool.invoke(
            {
                "asset": "XDEX",
                "objective": C05,
                "operation": "asset_intelligence",
            }
        )

    assert json.loads(rendered) == expected
    run.assert_called_once()
    assert run.call_args.kwargs["objective"] == C05
    # The model-proposed XDEX asset lookup never reached CMIS.
    assert client.calls == []


class _RankClient:
    def __init__(self, rankings):
        self.rankings = rankings
        self.calls = []

    def rank(self, *, chain, metric, limit):
        self.calls.append({"chain": chain, "metric": metric, "limit": limit})
        return {
            "service": "rank",
            "chain": "x1",
            "status": "partial",
            "asset": {},
            "data": {
                "metric": "volume",
                "limit": limit,
                "rankings": list(self.rankings),
            },
            "risk": None,
            "confidence": {"complete": False},
            "sources": [{"source": "X1.Ninja/XDEX", "role": "rank"}],
            "observed_at": "2026-09-13T11:59:00Z",
            "warnings": [],
            "errors": [],
        }


class _CapturingGraph:
    def __init__(self):
        self.state = None

    def invoke(self, state):
        self.state = state
        return {
            "report": {
                "specialist": "x1_scout",
                "chain": "x1",
                "requested_asset": state["request"]["asset"],
                "objective": state["request"]["objective"],
                "source": {
                    "service": "cmis",
                    "operation": "x1_intelligence_brief_inputs",
                },
                "x1_daily_intelligence_brief_runtime": {
                    "contract_version": "x1_daily_intelligence_brief_runtime/v1",
                    "product": "x1_daily_intelligence_brief_runtime",
                    "runtime_reliance_authorized": True,
                    "complete_x1_ecosystem_coverage_verified": False,
                    "execution_authorized": False,
                },
            }
        }


def test_daily_brief_selects_exact_ranked_mints_then_uses_explicit_accepted_route() -> None:
    client = _RankClient(
        [
            {"rank": 1, "mint": MINT_A, "symbol": "AAA", "value": 1000.0},
            {"rank": 2, "mint": MINT_B, "symbol": "BBB", "value": 900.0},
        ]
    )
    graph = _CapturingGraph()

    report = run_x1_daily_intelligence_brief_workflow(
        cmis_client=client,
        scout_graph=graph,
        objective=C05,
        now=datetime(2026, 9, 13, 12, 34, 56, tzinfo=timezone.utc),
    )

    assert client.calls == [{"chain": "x1", "metric": "volume", "limit": 5}]
    request = graph.state["request"]
    assert request["asset"] == MINT_A
    assert request["operation"] == "x1_intelligence_brief_inputs"
    assert request["daily_brief_subjects"] == [MINT_A, MINT_B]
    assert request["daily_brief_window_start"] == "2026-09-13T00:00:00Z"
    assert request["daily_brief_window_end"] == "2026-09-13T12:34:56Z"
    assert sorted(request["daily_brief_requested_services"]) == [
        "concentration_warning_intelligence",
        "discovery_intelligence",
        "large_trade_discovery",
    ]

    selection = report["daily_brief_scope_selection"]
    assert selection["contract_version"] == X1_DAILY_BRIEF_SCOPE_SELECTION_CONTRACT
    assert selection["state"] == "selected"
    assert selection["selector_basis"] == "top_verified_24h_volume"
    assert selection["selected_subject_count"] == 2
    assert selection["complete_x1_ecosystem_coverage_verified"] is False
    assert selection["rank_is_brief_fact"] is False
    assert selection["execution_authorized"] is False
    assert report["execution_authorized"] is False


def test_daily_brief_fails_closed_when_rank_has_no_exact_mint_subject() -> None:
    client = _RankClient(
        [{"rank": 1, "mint": "XDEX", "symbol": "XDEX", "value": 1000.0}]
    )
    graph = _CapturingGraph()

    report = run_x1_daily_intelligence_brief_workflow(
        cmis_client=client,
        scout_graph=graph,
        objective=C05,
        now=datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc),
    )

    assert graph.state is None
    assert report["status"] == "unavailable"
    assert report["requested_asset"] == "X1"
    assert report["source"] == {"service": "cmis", "operation": "rank"}
    selection = report["daily_brief_scope_selection"]
    assert selection["selected_subject_count"] == 0
    assert selection["reason"] == "no_exact_ranked_x1_mint_subjects"
    assert selection["complete_x1_ecosystem_coverage_verified"] is False
    assert report["execution_authorized"] is False
