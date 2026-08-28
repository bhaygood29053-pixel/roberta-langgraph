"""Tests for X1 Scout's constrained model-driven planner."""

from langchain_core.messages import AIMessage

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.planner import (
    enforce_plan,
    parse_plan_proposal,
    select_cmis_operation,
)


class ScriptedPlannerModel:
    def __init__(self, operations: list[str] | None = None, *, error: Exception | None = None):
        self.operations = list(operations or [])
        self.error = error
        self.invoke_count = 0

    def invoke(self, messages):
        self.invoke_count += 1
        if self.error is not None:
            raise self.error
        payload = ", ".join(f'"{operation}"' for operation in self.operations)
        return AIMessage(content=f'{{"operations": [{payload}]}}')


class MixedStatusCMIS(MockCMISClient):
    def market_report(self, *, chain: str, asset: str):
        result = super().market_report(chain=chain, asset=asset)
        result["status"] = "unavailable"
        result["warnings"].append({"code": "MARKET_UNAVAILABLE"})
        return result


def _invoke(scout, objective: str, **request_overrides):
    request = {"asset": "AGI", "objective": objective, **request_overrides}
    return scout.invoke({"request": request, "status": "running"})


def test_model_can_propose_multistep_read_only_investigation() -> None:
    planner = ScriptedPlannerModel(["market_report", "tokenomics", "risk_check"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "perform broad due diligence including tokenomics and risk")

    assert planner.invoke_count == 1
    assert [call["operation"] for call in cmis.calls] == [
        "market_report",
        "tokenomics",
        "risk_check",
    ]
    report = result["report"]
    assert report["plan"] == {
        "operations": ["market_report", "tokenomics", "risk_check"],
        "source": "model",
        "warnings": [],
    }
    assert [item["operation"] for item in report["investigations"]] == [
        "market_report",
        "tokenomics",
        "risk_check",
    ]
    assert report["source"]["operation"] == "risk_check"
    assert report["findings"]["risk"]["outcome"] == "TEST_ONLY"


def test_instant_scan_forces_current_three_service_plan_despite_negative_exclusions() -> None:
    planner = ScriptedPlannerModel(["rank", "historical_compare"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    objective = (
        "Instant X1 Scan of XNT. Gather market_report, tokenomics, and risk_check. "
        "Do not autonomously add rank or historical_compare."
    )
    result = _invoke(scout, objective, asset="XNT")

    assert select_cmis_operation(objective) == "market_report"
    assert [call["operation"] for call in cmis.calls] == [
        "market_report",
        "tokenomics",
        "risk_check",
    ]
    assert result["report"]["plan"]["operations"] == [
        "market_report",
        "tokenomics",
        "risk_check",
    ]
    assert not any(
        warning.startswith("planner_operation_rejected_for_rank_objective")
        for warning in result["report"]["plan"]["warnings"]
    )


def test_full_assessment_forces_all_five_services_and_all_available_history() -> None:
    planner = ScriptedPlannerModel(["rank"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "Full assessment of XNT", asset="XNT")

    assert [call["operation"] for call in cmis.calls] == [
        "market_report",
        "rank",
        "tokenomics",
        "historical_compare",
        "risk_check",
    ]
    historical_call = next(
        call for call in cmis.calls if call["operation"] == "historical_compare"
    )
    assert historical_call["mode"] == "all_available"

    report = result["report"]
    assert report["plan"]["operations"] == [
        "market_report",
        "rank",
        "tokenomics",
        "historical_compare",
        "risk_check",
    ]
    assert report["source"]["operation"] == "risk_check"
    assert [item["operation"] for item in report["investigations"]] == [
        "market_report",
        "rank",
        "tokenomics",
        "historical_compare",
        "risk_check",
    ]


def test_full_assessment_preserves_per_investigation_asset_and_flags_wrapped_xnt() -> None:
    class WrappedXNTCMIS(MockCMISClient):
        def market_report(self, *, chain: str, asset: str):
            result = super().market_report(chain=chain, asset=asset)
            result["asset"] = {"symbol": "XNT", "name": "Wrapped XNT"}
            return result

    cmis = WrappedXNTCMIS()
    scout = build_x1_scout_graph(cmis)

    result = _invoke(scout, "Full assessment of XNT", asset="XNT")
    report = result["report"]

    assert report["investigations"][0]["asset"] == {
        "symbol": "XNT",
        "name": "Wrapped XNT",
    }
    assert any(
        warning.get("code") == "x1_xnt_native_wrapped_scope_unresolved"
        for warning in report["warnings"]
        if isinstance(warning, dict)
    )


def test_risk_requirement_is_forced_even_when_planner_omits_it() -> None:
    planner = ScriptedPlannerModel(["market_report"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "assess market risk")

    assert [call["operation"] for call in cmis.calls] == [
        "market_report",
        "risk_check",
    ]
    assert result["report"]["plan"]["operations"][-1] == "risk_check"
    assert result["report"]["source"]["operation"] == "risk_check"


def test_tokenomics_requirement_is_forced_and_made_primary() -> None:
    planner = ScriptedPlannerModel(["market_report"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "verify mint authority and supply")

    assert [call["operation"] for call in cmis.calls] == [
        "market_report",
        "tokenomics",
    ]
    assert result["report"]["source"]["operation"] == "tokenomics"


def test_planner_cannot_grant_itself_pre_trade_or_unknown_operations() -> None:
    request = {"asset": "AGI", "objective": "assess market risk"}
    plan = enforce_plan(
        request,
        {
            "operations": [
                "pre_trade_check",
                "execute_swap",
                "pre_trade_check",
            ]
        },
    )

    assert plan["operations"] == ["risk_check"]
    assert plan["source"] == "deterministic"
    assert "planner_operation_rejected: pre_trade_check" in plan["warnings"]
    assert "planner_operation_rejected: execute_swap" in plan["warnings"]


def test_duplicates_are_removed_and_plan_is_bounded() -> None:
    plan = enforce_plan(
        {"asset": "AGI", "objective": "broad market research"},
        {
            "operations": [
                "market_report",
                "market_report",
                "tokenomics",
                "risk_check",
                "market_report",
            ]
        },
    )

    assert plan["operations"] == ["market_report", "tokenomics", "risk_check"]
    assert len(plan["operations"]) == 3


def test_invalid_planner_response_falls_back_deterministically() -> None:
    planner = ScriptedPlannerModel(error=RuntimeError("planner unavailable"))
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "check token supply")

    assert [call["operation"] for call in cmis.calls] == ["tokenomics"]
    assert result["report"]["plan"]["source"] == "deterministic"
    assert result["report"]["plan"]["warnings"][0].startswith("planner_fallback:")


def test_explicit_pre_trade_bypasses_planner_and_requires_trade_inputs() -> None:
    planner = ScriptedPlannerModel(["risk_check"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(
        scout,
        "explicit pre-trade verification",
        operation="pre_trade_check",
        action="BUY",
        amount_usd=250.0,
    )

    assert planner.invoke_count == 0
    assert cmis.calls == [
        {
            "operation": "pre_trade_check",
            "chain": "x1",
            "asset": "AGI",
            "action": "BUY",
            "amount_usd": 250.0,
        }
    ]
    assert result["report"]["plan"]["source"] == "explicit"


def test_multistep_report_preserves_per_step_status_and_provenance() -> None:
    planner = ScriptedPlannerModel(["market_report", "risk_check"])
    cmis = MixedStatusCMIS()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "assess market risk")

    investigations = result["report"]["investigations"]
    assert [item["cmis_status"] for item in investigations] == [
        "unavailable",
        "partial",
    ]
    assert investigations[0]["warnings"][-1] == {"code": "MARKET_UNAVAILABLE"}
    assert investigations[0]["observed_at"] == "2026-08-15T21:45:00Z"
    assert investigations[0]["observed_at_iso"] == "2026-08-15T21:45:00Z"
    assert investigations[1]["sources"] == [
        {"source": "mock_cmis", "role": "test"}
    ]
    assert result["status"] == "error"


def test_plan_parser_accepts_json_fence_but_not_non_object_payload() -> None:
    assert parse_plan_proposal(
        AIMessage(content='```json\n{"operations": ["risk_check"]}\n```')
    ) == {"operations": ["risk_check"]}

    try:
        parse_plan_proposal(AIMessage(content='["risk_check"]'))
    except ValueError as exc:
        assert "JSON object" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("non-object planner payload should fail")
