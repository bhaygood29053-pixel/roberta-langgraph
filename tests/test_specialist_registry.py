"""Deterministic tests for the shared chain-specialist registry."""

from roberta.policy.routing import SpecialistRoutingPolicy
from roberta.specialists import DEFAULT_SPECIALIST_REGISTRY, select_chain_specialist


def test_default_registry_contains_x1_and_solana_chain_scouts() -> None:
    assert tuple(entry.specialist for entry in DEFAULT_SPECIALIST_REGISTRY) == (
        "x1_scout",
        "solana_scout",
    )


def test_chain_routing_selects_x1_and_solana_without_model_inference() -> None:
    x1 = select_chain_specialist(chain="X1", capability="risk_check")
    solana = select_chain_specialist(chain="Solana", capability="risk_check")

    assert x1.status == "selected"
    assert x1.specialist == "x1_scout"
    assert x1.chain == "x1"
    assert solana.status == "selected"
    assert solana.specialist == "solana_scout"
    assert solana.chain == "solana"


def test_unsupported_chain_fails_closed() -> None:
    route = select_chain_specialist(chain="ethereum", capability="market_report")

    assert route.status == "unavailable"
    assert route.specialist is None
    assert route.candidates == ()


def test_registry_entry_does_not_claim_live_health() -> None:
    route = select_chain_specialist(chain="solana", capability="market_report")

    assert route.status == "selected"
    assert "availability" not in route.reason.lower()
    assert "health" not in route.reason.lower()


def test_routing_policy_can_block_solana_without_affecting_x1() -> None:
    policy = SpecialistRoutingPolicy(blocked_specialists=("solana_scout",))

    solana = select_chain_specialist(
        chain="solana",
        capability="risk_check",
        policy=policy,
    )
    x1 = select_chain_specialist(
        chain="x1",
        capability="risk_check",
        policy=policy,
    )

    assert solana.status == "unavailable"
    assert x1.specialist == "x1_scout"
