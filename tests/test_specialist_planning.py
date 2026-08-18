"""Tests for shared bounded chain-Scout planning helpers."""

from langchain_core.messages import AIMessage

from roberta.specialists.planning import enforce_plan, propose_plan, select_cmis_operation


class _Planner:
    def __init__(self, content: str) -> None:
        self.content = content
        self.messages = None

    def invoke(self, messages):
        self.messages = messages
        return AIMessage(content=self.content)


def test_deterministic_selector_keeps_risk_and_tokenomics_requirements() -> None:
    assert select_cmis_operation("assess market risk") == "risk_check"
    assert select_cmis_operation("verify mint authority") == "tokenomics"
    assert select_cmis_operation("show price and liquidity") == "market_report"


def test_generic_planner_prompt_names_target_chain_without_granting_execution() -> None:
    planner = _Planner('{"operations":["market_report","risk_check"]}')

    proposal = propose_plan(
        planner,
        chain="solana",
        asset="JUP",
        objective="assess market risk",
    )

    assert proposal == {"operations": ["market_report", "risk_check"]}
    prompt = str(planner.messages[0].content)
    assert "solana" in prompt.lower()
    assert "Never propose pre_trade_check" in prompt


def test_autonomous_plan_rejects_pre_trade_and_unknown_operations() -> None:
    plan = enforce_plan(
        {"asset": "JUP", "objective": "show price"},
        {"operations": ["pre_trade_check", "swap", "market_report"]},
    )

    assert plan["operations"] == ["market_report"]
    assert "planner_operation_rejected: pre_trade_check" in plan["warnings"]
    assert "planner_operation_rejected: swap" in plan["warnings"]


def test_explicit_pre_trade_requires_exact_trade_inputs() -> None:
    try:
        enforce_plan(
            {
                "asset": "JUP",
                "objective": "pre trade",
                "operation": "pre_trade_check",
            },
            None,
        )
    except ValueError as exc:
        assert "action and amount_usd" in str(exc)
    else:
        raise AssertionError("pre_trade_check unexpectedly ran without trade inputs")

    plan = enforce_plan(
        {
            "asset": "JUP",
            "objective": "pre trade",
            "operation": "pre_trade_check",
            "action": "BUY",
            "amount_usd": 25.0,
        },
        None,
    )
    assert plan["source"] == "explicit"
    assert plan["operations"] == ["pre_trade_check"]
