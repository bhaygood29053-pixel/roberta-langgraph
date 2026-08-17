"""Deterministic specialist-selection hooks for Oracle routing policy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RoutingStatus = Literal["selected", "unavailable"]


@dataclass(frozen=True, slots=True)
class SpecialistCapability:
    """Stable specialist registry entry used for provider-neutral routing."""

    specialist: str
    chains: tuple[str, ...]
    capabilities: tuple[str, ...]
    priority: int = 100

    def __post_init__(self) -> None:
        if not isinstance(self.specialist, str) or not self.specialist.strip():
            raise ValueError("specialist must be a non-empty string")
        if not self.chains or any(not str(chain).strip() for chain in self.chains):
            raise ValueError("specialist chains must contain non-empty values")
        if not self.capabilities or any(
            not str(capability).strip() for capability in self.capabilities
        ):
            raise ValueError("specialist capabilities must contain non-empty values")
        if not isinstance(self.priority, int):
            raise TypeError("specialist priority must be int")


@dataclass(frozen=True, slots=True)
class SpecialistRoutingPolicy:
    """Optional stable user/system constraints on specialist selection."""

    allowed_specialists: tuple[str, ...] | None = None
    blocked_specialists: tuple[str, ...] = ()
    preferred_specialists: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SpecialistRoute:
    """Explainable deterministic specialist-selection result."""

    status: RoutingStatus
    chain: str
    capability: str
    specialist: str | None
    candidates: tuple[str, ...]
    reason: str


def _rank_specialist(
    capability: SpecialistCapability,
    policy: SpecialistRoutingPolicy,
) -> tuple[int, int, str]:
    try:
        preference_rank = policy.preferred_specialists.index(capability.specialist)
    except ValueError:
        preference_rank = len(policy.preferred_specialists) + 1
    return preference_rank, capability.priority, capability.specialist


def select_specialist(
    *,
    chain: str,
    capability: str,
    registry: tuple[SpecialistCapability, ...],
    policy: SpecialistRoutingPolicy | None = None,
) -> SpecialistRoute:
    """Select one specialist without LLM routing or provider discovery.

    Registry entries are stable capabilities, not live service-health facts. Live
    availability still belongs to specialist/service calls themselves.
    """

    normalized_chain = str(chain or "").strip().lower()
    normalized_capability = str(capability or "").strip().lower()
    if not normalized_chain:
        raise ValueError("chain must be a non-empty string")
    if not normalized_capability:
        raise ValueError("capability must be a non-empty string")

    active_policy = policy or SpecialistRoutingPolicy()
    blocked = set(active_policy.blocked_specialists)
    allowed = (
        None
        if active_policy.allowed_specialists is None
        else set(active_policy.allowed_specialists)
    )

    candidates = []
    for entry in registry:
        entry_chains = {value.strip().lower() for value in entry.chains}
        entry_capabilities = {value.strip().lower() for value in entry.capabilities}
        if normalized_chain not in entry_chains:
            continue
        if normalized_capability not in entry_capabilities:
            continue
        if entry.specialist in blocked:
            continue
        if allowed is not None and entry.specialist not in allowed:
            continue
        candidates.append(entry)

    candidates.sort(key=lambda item: _rank_specialist(item, active_policy))
    names = tuple(entry.specialist for entry in candidates)
    if not candidates:
        return SpecialistRoute(
            status="unavailable",
            chain=normalized_chain,
            capability=normalized_capability,
            specialist=None,
            candidates=(),
            reason="no registered specialist satisfies the chain/capability and routing constraints",
        )

    selected = candidates[0]
    return SpecialistRoute(
        status="selected",
        chain=normalized_chain,
        capability=normalized_capability,
        specialist=selected.specialist,
        candidates=names,
        reason="selected by explicit routing constraints, preference order, priority, then stable specialist name",
    )
