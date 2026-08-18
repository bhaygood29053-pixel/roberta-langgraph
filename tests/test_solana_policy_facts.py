"""Tests for Solana Scout and cross-chain policy fact adaptation."""

import json

from langchain_core.messages import HumanMessage, ToolMessage

from roberta.policy import PolicyRule
from roberta.solana_scout.policy_facts import (
    extract_solana_policy_facts,
    solana_policy_facts_from_state,
)
from roberta.specialists.policy_facts import chain_policy_facts_from_state


def _rule():
    return PolicyRule(
        rule_id="liquidity",
        kind="threshold_rule",
        effect="block",
        description="liquidity",
        fact_key="market.liquidity",
        operator="gte",
        expected=100,
    )


def _investigation(*, chain_value: int, status="ok"):
    return {
        "operation": "market_report",
        "cmis_status": status,
        "observed_at_iso": "2026-08-17T13:00:00Z",
        "findings": {"data": {"liquidity": chain_value}, "risk": None},
    }


def _report(specialist, chain, value=None, *, investigations=True):
    return {
        "specialist": specialist,
        "chain": chain,
        "asset": {"symbol": "TEST"} if investigations else {"input": "TEST"},
        "investigations": [] if not investigations else [_investigation(chain_value=value)],
    }


def _tool(name, report, call_id):
    return ToolMessage(
        content=json.dumps(report),
        tool_call_id=call_id,
        name=name,
    )


def test_ok_solana_market_report_maps_standard_fact_keys() -> None:
    facts = extract_solana_policy_facts(
        _report("solana_scout", "solana", 750)
    )

    assert facts["asset.chain"].value == "solana"
    assert facts["asset.symbol"].value == "TEST"
    assert facts["market.liquidity"].value == 750
    assert facts["market.liquidity"].evidence_status == "verified"
    assert facts["market.liquidity"].freshness == "fresh"
    assert facts["market.liquidity"].source == "solana_scout/cmis:market_report"


def test_partial_solana_evidence_cannot_become_verified_fresh() -> None:
    report = {
        "specialist": "solana_scout",
        "chain": "solana",
        "asset": {"symbol": "TEST"},
        "investigations": [_investigation(chain_value=750, status="partial")],
    }
    facts = extract_solana_policy_facts(report)

    assert facts["market.liquidity"].evidence_status == "unverified"
    assert facts["market.liquidity"].freshness == "unknown"


def test_cross_chain_dispatch_uses_latest_scout_within_current_user_turn_only() -> None:
    x1 = _tool(
        "x1_scout_investigate",
        _report("x1_scout", "x1", 111),
        "x1-old",
    )
    solana = _tool(
        "solana_scout_investigate",
        _report("solana_scout", "solana", 999),
        "sol-new",
    )

    facts = chain_policy_facts_from_state(
        {"messages": [HumanMessage(content="Current request"), x1, solana]},
        [_rule()],
    )

    assert facts["market.liquidity"].value == 999
    assert facts["market.liquidity"].source.startswith("solana_scout/")


def test_unconfigured_latest_solana_does_not_fall_back_to_same_turn_x1_fact() -> None:
    x1 = _tool(
        "x1_scout_investigate",
        _report("x1_scout", "x1", 111),
        "x1-old",
    )
    solana_unconfigured = _tool(
        "solana_scout_investigate",
        _report("solana_scout", "solana", investigations=False),
        "sol-new",
    )

    facts = chain_policy_facts_from_state(
        {
            "messages": [
                HumanMessage(content="Current request"),
                x1,
                solana_unconfigured,
            ]
        },
        [_rule()],
    )

    assert facts == {}


def test_latest_x1_within_current_turn_still_uses_existing_x1_adapter() -> None:
    solana = _tool(
        "solana_scout_investigate",
        _report("solana_scout", "solana", 999),
        "sol-old",
    )
    x1 = _tool(
        "x1_scout_investigate",
        _report("x1_scout", "x1", 222),
        "x1-new",
    )

    facts = chain_policy_facts_from_state(
        {"messages": [HumanMessage(content="Current request"), solana, x1]},
        [_rule()],
    )

    assert facts["market.liquidity"].value == 222
    assert facts["market.liquidity"].source.startswith("x1_scout/")


def test_prior_turn_solana_fact_cannot_satisfy_new_x1_or_unspecified_request() -> None:
    old_solana = _tool(
        "solana_scout_investigate",
        _report("solana_scout", "solana", 999999),
        "sol-old",
    )

    facts = chain_policy_facts_from_state(
        {
            "messages": [
                HumanMessage(content="Old Solana request"),
                old_solana,
                HumanMessage(content="New request"),
            ]
        },
        [_rule()],
    )

    assert facts == {}


def test_current_turn_solana_state_provider_ignores_prior_turn_result() -> None:
    old_solana = _tool(
        "solana_scout_investigate",
        _report("solana_scout", "solana", 500),
        "sol-old",
    )

    facts = solana_policy_facts_from_state(
        {
            "messages": [
                HumanMessage(content="Old Solana request"),
                old_solana,
                HumanMessage(content="New Solana request"),
            ]
        },
        [_rule()],
    )

    assert facts == {}


def test_bare_tool_history_without_user_marker_is_not_current_evidence() -> None:
    solana = _tool(
        "solana_scout_investigate",
        _report("solana_scout", "solana", 500),
        "sol-only",
    )

    assert chain_policy_facts_from_state({"messages": [solana]}, [_rule()]) == {}
    assert solana_policy_facts_from_state({"messages": [solana]}, [_rule()]) == {}
