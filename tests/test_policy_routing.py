"""Tests for provider-neutral deterministic specialist routing hooks."""

from roberta.policy.routing import (
    SpecialistCapability,
    SpecialistRoutingPolicy,
    select_specialist,
)


REGISTRY = (
    SpecialistCapability(
        specialist="x1_scout",
        chains=("x1",),
        capabilities=("market_investigation", "market_risk"),
        priority=10,
    ),
    SpecialistCapability(
        specialist="solana_scout",
        chains=("solana",),
        capabilities=("market_investigation", "market_risk"),
        priority=10,
    ),
)


def test_x1_routes_to_x1_scout_without_model_inference():
    route = select_specialist(
        chain="X1",
        capability="market_risk",
        registry=REGISTRY,
    )

    assert route.status == "selected"
    assert route.specialist == "x1_scout"


def test_future_solana_registry_entry_uses_same_contract():
    route = select_specialist(
        chain="solana",
        capability="market_investigation",
        registry=REGISTRY,
    )

    assert route.status == "selected"
    assert route.specialist == "solana_scout"


def test_blocked_specialist_fails_closed_to_unavailable():
    route = select_specialist(
        chain="x1",
        capability="market_risk",
        registry=REGISTRY,
        policy=SpecialistRoutingPolicy(blocked_specialists=("x1_scout",)),
    )

    assert route.status == "unavailable"
    assert route.specialist is None


def test_allowed_specialists_is_an_enforced_allowlist():
    route = select_specialist(
        chain="x1",
        capability="market_risk",
        registry=REGISTRY,
        policy=SpecialistRoutingPolicy(allowed_specialists=("solana_scout",)),
    )

    assert route.status == "unavailable"


def test_explicit_preference_beats_numeric_priority():
    registry = (
        SpecialistCapability(
            specialist="primary",
            chains=("x1",),
            capabilities=("security",),
            priority=1,
        ),
        SpecialistCapability(
            specialist="preferred",
            chains=("x1",),
            capabilities=("security",),
            priority=50,
        ),
    )

    route = select_specialist(
        chain="x1",
        capability="security",
        registry=registry,
        policy=SpecialistRoutingPolicy(preferred_specialists=("preferred",)),
    )

    assert route.specialist == "preferred"
    assert route.candidates == ("preferred", "primary")


def test_live_health_is_not_fabricated_by_registry_selection():
    route = select_specialist(
        chain="x1",
        capability="market_risk",
        registry=REGISTRY,
    )

    assert "health" not in route.reason.lower()
    assert "availability" not in route.reason.lower()
