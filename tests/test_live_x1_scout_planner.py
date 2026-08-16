"""Opt-in live contract probe for the DeepSeek-backed X1 Scout planner."""

import os

import pytest

from roberta.models import create_runtime_model
from roberta.x1_scout.planner import AUTONOMOUS_OPERATIONS, enforce_plan, propose_plan


RUN_LIVE = os.getenv("RUN_X1_SCOUT_PLANNER_LIVE") == "1"


@pytest.mark.live
@pytest.mark.skipif(
    not RUN_LIVE,
    reason="Set RUN_X1_SCOUT_PLANNER_LIVE=1 to call the live planner model.",
)
def test_live_x1_scout_planner_proposes_enforceable_risk_plan() -> None:
    planner_model = create_runtime_model()
    request = {
        "asset": "AGI",
        "objective": "review current market context, tokenomics, and market risk",
    }

    proposal = propose_plan(planner_model, request)
    plan = enforce_plan(request, proposal)

    assert plan["operations"]
    assert len(plan["operations"]) <= 3
    assert "tokenomics" in plan["operations"]
    assert plan["operations"][-1] == "risk_check"
    assert all(operation in AUTONOMOUS_OPERATIONS for operation in plan["operations"])
    assert "pre_trade_check" not in plan["operations"]
