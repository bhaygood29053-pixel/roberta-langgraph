"""Tests for X1 Scout -> provider-neutral Oracle policy fact adaptation."""

import json

import pytest
from langchain_core.messages import HumanMessage, ToolMessage

from roberta.policy import PolicyRule
from roberta.x1_scout.policy_facts import (
    extract_x1_policy_facts,
    x1_policy_facts_from_state,
)


def _investigation(operation, *, status="ok", data=None, risk=None, observed=True):
    return {
        "operation": operation,
        "cmis_status": status,
        "observed_at_iso": "2026-08-17T13:00:00Z" if observed else None,
        "findings": {"data": data or {}, "risk": risk},
    }


def _report(investigations):
    return {
        "specialist": "x1_scout",
        "chain": "x1",
        "asset": {"symbol": "TEST"},
        "investigations": investigations,
    }


def test_ok_market_report_maps_standard_fact_keys_as_verified_fresh():
    facts = extract_x1_policy_facts(
        _report(
            [
                _investigation(
                    "market_report",
                    data={
                        "price": 1.25,
                        "liquidity": 50000,
                        "#LPs": 12,
                        "volume_24h": 9000,
                    },
                )
            ]
        )
    )

    assert facts["asset.chain"].value == "x1"
    assert facts["asset.symbol"].value == "TEST"
    assert facts["market.liquidity"].value == 50000
    assert facts["market.liquidity"].evidence_status == "verified"
    assert facts["market.liquidity"].freshness == "fresh"


def test_partial_cmis_report_never_becomes_verified_policy_fact():
    facts = extract_x1_policy_facts(
        _report(
            [
                _investigation(
                    "market_report",
                    status="partial",
                    data={"liquidity": 50000},
                )
            ]
        )
    )

    assert facts["market.liquidity"].evidence_status == "unverified"
    assert facts["market.liquidity"].freshness == "unknown"


def test_ok_report_without_normalized_timestamp_is_not_marked_fresh():
    facts = extract_x1_policy_facts(
        _report(
            [
                _investigation(
                    "market_report",
                    status="ok",
                    observed=False,
                    data={"liquidity": 50000},
                )
            ]
        )
    )

    assert facts["market.liquidity"].evidence_status == "verified"
    assert facts["market.liquidity"].freshness == "unknown"


def test_null_market_field_becomes_insufficient_not_zero():
    facts = extract_x1_policy_facts(
        _report([_investigation("market_report", data={"liquidity": None})])
    )

    assert facts["market.liquidity"].value is None
    assert facts["market.liquidity"].evidence_status == "insufficient_evidence"


def test_multi_operation_report_maps_risk_tokenomics_and_trade_without_primary_only_bias():
    facts = extract_x1_policy_facts(
        _report(
            [
                _investigation(
                    "risk_check",
                    risk={"outcome": "PASS", "score": 3},
                ),
                _investigation(
                    "tokenomics",
                    data={
                        "total_supply": 1000000,
                        "mint_authority": None,
                        "freeze_authority": None,
                    },
                ),
                _investigation(
                    "pre_trade_check",
                    data={"trade": {"side": "buy", "notional_usd": 250}},
                ),
            ]
        )
    )

    assert facts["market.risk_outcome"].value == "PASS"
    assert facts["market.risk_score"].value == 3
    assert facts["tokenomics.total_supply"].value == 1000000
    assert facts["tokenomics.mint_authority"].evidence_status == "insufficient_evidence"
    assert facts["trade.side"].value == "buy"
    assert facts["trade.notional_usd"].value == 250


def test_requested_fact_keys_prevent_unneeded_fact_injection():
    facts = extract_x1_policy_facts(
        _report(
            [
                _investigation(
                    "market_report",
                    data={"price": 1, "liquidity": 2, "volume_24h": 3, "#LPs": 4},
                )
            ]
        ),
        requested_fact_keys={"market.liquidity"},
    )

    assert set(facts) == {"market.liquidity"}


def test_state_provider_returns_empty_before_x1_scout_runs():
    rule = PolicyRule(
        rule_id="liquidity",
        kind="threshold_rule",
        effect="block",
        description="liquidity",
        fact_key="market.liquidity",
        operator="gte",
        expected=100,
    )

    facts = x1_policy_facts_from_state(
        {"messages": [HumanMessage(content="Assess TEST")]},
        [rule],
    )

    assert facts == {}


def test_state_provider_uses_latest_structured_x1_scout_tool_message():
    rule = PolicyRule(
        rule_id="liquidity",
        kind="threshold_rule",
        effect="block",
        description="liquidity",
        fact_key="market.liquidity",
        operator="gte",
        expected=100,
    )
    report = _report([_investigation("market_report", data={"liquidity": 500})])
    tool = ToolMessage(
        content=json.dumps(report),
        tool_call_id="call-1",
        name="x1_scout_investigate",
    )

    facts = x1_policy_facts_from_state({"messages": [tool]}, [rule])

    assert facts["market.liquidity"].value == 500


def test_malformed_x1_scout_tool_json_fails_closed():
    rule = PolicyRule(
        rule_id="liquidity",
        kind="threshold_rule",
        effect="block",
        description="liquidity",
        fact_key="market.liquidity",
        operator="gte",
        expected=100,
    )
    tool = ToolMessage(
        content="not-json",
        tool_call_id="call-1",
        name="x1_scout_investigate",
    )

    with pytest.raises(ValueError, match="invalid JSON"):
        x1_policy_facts_from_state({"messages": [tool]}, [rule])
