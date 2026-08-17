"""Deterministic chain objective -> specialist tool dispatch metadata."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from roberta.policy.routing import SpecialistRoutingPolicy
from roberta.specialists.planning import select_cmis_operation
from roberta.specialists.registry import select_chain_specialist

DispatchStatus = Literal["selected", "unavailable"]

_TOOL_BY_SPECIALIST = {
    "x1_scout": "x1_scout_investigate",
    "solana_scout": "solana_scout_investigate",
}


@dataclass(frozen=True, slots=True)
class ChainSpecialistDispatch:
    """Explainable routing metadata; selection is not a live-health claim."""

    status: DispatchStatus
    chain: str
    capability: str
    specialist: str | None
    tool_name: str | None
    reason: str


def route_chain_objective(
    *,
    chain: str,
    objective: str,
    policy: SpecialistRoutingPolicy | None = None,
) -> ChainSpecialistDispatch:
    """Resolve an explicit chain objective to the registered Scout tool.

    Natural-language objective interpretation here is intentionally narrow: it
    chooses only the same read-only CMIS fallback operation used by Scout planning.
    It never selects pre_trade_check or any execution capability autonomously.
    """

    capability = select_cmis_operation(objective)
    route = select_chain_specialist(
        chain=chain,
        capability=capability,
        policy=policy,
    )
    if route.status != "selected" or route.specialist is None:
        return ChainSpecialistDispatch(
            status="unavailable",
            chain=route.chain,
            capability=capability,
            specialist=None,
            tool_name=None,
            reason=route.reason,
        )

    tool_name = _TOOL_BY_SPECIALIST.get(route.specialist)
    if tool_name is None:
        return ChainSpecialistDispatch(
            status="unavailable",
            chain=route.chain,
            capability=capability,
            specialist=route.specialist,
            tool_name=None,
            reason="selected specialist has no registered Roberta-facing tool binding",
        )

    return ChainSpecialistDispatch(
        status="selected",
        chain=route.chain,
        capability=capability,
        specialist=route.specialist,
        tool_name=tool_name,
        reason=route.reason,
    )
