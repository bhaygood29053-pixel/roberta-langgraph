"""Stable specialist registry shared by Oracle routing and tool wiring."""

from __future__ import annotations

from roberta.policy.routing import (
    SpecialistCapability,
    SpecialistRoute,
    SpecialistRoutingPolicy,
    select_specialist,
)

_CHAIN_MARKET_CAPABILITIES = (
    "market_report",
    "tokenomics",
    "risk_check",
    "pre_trade_check",
)

DEFAULT_SPECIALIST_REGISTRY: tuple[SpecialistCapability, ...] = (
    SpecialistCapability(
        specialist="x1_scout",
        chains=("x1",),
        capabilities=_CHAIN_MARKET_CAPABILITIES,
        priority=10,
    ),
    SpecialistCapability(
        specialist="solana_scout",
        chains=("solana",),
        capabilities=_CHAIN_MARKET_CAPABILITIES,
        priority=10,
    ),
)


def select_chain_specialist(
    *,
    chain: str,
    capability: str,
    policy: SpecialistRoutingPolicy | None = None,
) -> SpecialistRoute:
    """Select a registered chain Scout without inferring live availability.

    Registry membership describes stable architectural capability only. The
    selected Scout or CMIS service still owns the live/configured availability
    result for the actual request.
    """

    return select_specialist(
        chain=chain,
        capability=capability,
        registry=DEFAULT_SPECIALIST_REGISTRY,
        policy=policy,
    )
