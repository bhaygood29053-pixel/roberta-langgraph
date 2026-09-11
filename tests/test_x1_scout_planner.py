"""Tests for X1 Scout's constrained model-driven planner."""

from langchain_core.messages import AIMessage

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.planner import enforce_plan, parse_plan_proposal


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
    def burn_intelligence(self, *, chain: str, asset: str):
        result = super().burn_intelligence(chain=chain, asset=asset)
        result["status"] = "unavailable"
        result["warnings"].append({"code": "BURN_UNAVAILABLE"})
        return result


def _invoke(scout, objective: str, **request_overrides):
    request = {"asset": "AGI", "objective": objective, **request_overrides}
    return scout.invoke({"request": request, "status": "running"})


def test_model_baseline_fact_calls_collapse_to_one_canonical_scan() -> None:
    planner = ScriptedPlannerModel(["market_report", "tokenomics", "risk_check"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "perform broad due diligence including tokenomics and risk")

    assert planner.invoke_count == 1
    assert [call["operation"] for call in cmis.calls] == ["instant_x1_scan"]
    report = result["report"]
    assert report["plan"] == {
        "operations": ["instant_x1_scan"],
        "source": "model",
        "warnings": [],
    }
    assert [item["operation"] for item in report["investigations"]] == [
        "instant_x1_scan",
    ]
    assert report["source"]["operation"] == "instant_x1_scan"
    assert report["instant_x1_scan_product_view"]["contract_version"] == (
        "instant_x1_scan_product_view/v1"
    )


def test_full_assessment_uses_canonical_rank_burn_scan_composition() -> None:
    planner = ScriptedPlannerModel(["market_report", "tokenomics", "risk_check"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "Full assessment of XNT", asset="XNT")

    assert [call["operation"] for call in cmis.calls] == [
        "rank",
        "burn_intelligence",
        "instant_x1_scan",
    ]

    report = result["report"]
    assert report["plan"]["operations"] == [
        "rank",
        "burn_intelligence",
        "instant_x1_scan",
    ]
    assert report["source"]["operation"] == "instant_x1_scan"
    assert [item["operation"] for item in report["investigations"]] == [
        "rank",
        "burn_intelligence",
        "instant_x1_scan",
    ]
    assert report["instant_x1_scan_product_view"]["contract_version"] == (
        "instant_x1_scan_product_view/v1"
    )


def test_full_assessment_preserves_per_investigation_asset_and_flags_wrapped_xnt() -> None:
    class WrappedXNTCMIS(MockCMISClient):
        def instant_x1_scan(self, *, chain: str, asset: str):
            result = super().instant_x1_scan(chain=chain, asset=asset)
            result["asset"] = {
                "symbol": "XNT",
                "name": "Wrapped XNT",
                "mint": result["asset"]["mint"],
            }
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


def test_risk_requirement_uses_canonical_scan_even_when_planner_proposes_market_only() -> None:
    planner = ScriptedPlannerModel(["market_report"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "assess market risk")

    assert [call["operation"] for call in cmis.calls] == ["instant_x1_scan"]
    assert result["report"]["plan"]["operations"] == ["instant_x1_scan"]
    assert result["report"]["source"]["operation"] == "instant_x1_scan"


def test_tokenomics_requirement_uses_same_canonical_scan() -> None:
    planner = ScriptedPlannerModel(["market_report"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "verify mint authority and supply")

    assert [call["operation"] for call in cmis.calls] == ["instant_x1_scan"]
    assert result["report"]["source"]["operation"] == "instant_x1_scan"


def test_burn_requirement_adds_burn_after_canonical_scan() -> None:
    planner = ScriptedPlannerModel(["market_report"])
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "show burn intelligence and 24h burn activity")

    assert [call["operation"] for call in cmis.calls] == [
        "instant_x1_scan",
        "burn_intelligence",
    ]
    report = result["report"]
    assert report["source"]["operation"] == "burn_intelligence"
    assert report["x1_burn_intelligence"]["contract_version"] == "x1_burn_intelligence/v1"
    assert (
        report["x1_burn_intelligence"]["burn_metrics"]["windows"]["24h"]["burned_tokens"]
        == "10"
    )
    assert report["x1_burn_intelligence"]["execution_authorized"] is False
    assert [item["operation"] for item in report["investigations"]] == [
        "instant_x1_scan",
        "burn_intelligence",
    ]


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

    assert plan["operations"] == ["instant_x1_scan"]
    assert plan["source"] == "deterministic"
    assert "planner_operation_rejected: pre_trade_check" in plan["warnings"]
    assert "planner_operation_rejected: execute_swap" in plan["warnings"]


def test_duplicate_baseline_calls_are_collapsed_and_plan_is_bounded() -> None:
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

    assert plan["operations"] == ["instant_x1_scan"]


def test_invalid_planner_response_falls_back_to_canonical_scan() -> None:
    planner = ScriptedPlannerModel(error=RuntimeError("planner unavailable"))
    cmis = MockCMISClient()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "check token supply")

    assert [call["operation"] for call in cmis.calls] == ["instant_x1_scan"]
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


def test_multistep_report_preserves_scan_and_specialist_status() -> None:
    planner = ScriptedPlannerModel(["market_report", "burn_intelligence"])
    cmis = MixedStatusCMIS()
    scout = build_x1_scout_graph(cmis, planner_model=planner)

    result = _invoke(scout, "show burn intelligence and current market context")

    investigations = result["report"]["investigations"]
    assert [item["operation"] for item in investigations] == [
        "instant_x1_scan",
        "burn_intelligence",
    ]
    assert investigations[-1]["cmis_status"] == "unavailable"
    assert investigations[-1]["warnings"][-1] == {"code": "BURN_UNAVAILABLE"}
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
