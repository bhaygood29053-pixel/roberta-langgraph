"""Tests for deterministic chain objective -> Scout tool dispatch."""

from roberta.specialists import route_chain_objective


def test_x1_objective_resolves_to_x1_scout_tool() -> None:
    dispatch = route_chain_objective(chain="x1", objective="assess market risk")

    assert dispatch.status == "selected"
    assert dispatch.capability == "risk_check"
    assert dispatch.specialist == "x1_scout"
    assert dispatch.tool_name == "x1_scout_investigate"


def test_solana_objective_resolves_to_solana_scout_tool() -> None:
    dispatch = route_chain_objective(chain="solana", objective="verify mint authority")

    assert dispatch.status == "selected"
    assert dispatch.capability == "tokenomics"
    assert dispatch.specialist == "solana_scout"
    assert dispatch.tool_name == "solana_scout_investigate"


def test_dispatch_never_selects_pre_trade_from_natural_language_objective() -> None:
    dispatch = route_chain_objective(
        chain="solana",
        objective="please buy after a pre trade check",
    )

    assert dispatch.status == "selected"
    assert dispatch.capability == "market_report"
    assert dispatch.tool_name == "solana_scout_investigate"


def test_unknown_chain_has_no_tool_binding() -> None:
    dispatch = route_chain_objective(chain="base", objective="show market activity")

    assert dispatch.status == "unavailable"
    assert dispatch.specialist is None
    assert dispatch.tool_name is None
