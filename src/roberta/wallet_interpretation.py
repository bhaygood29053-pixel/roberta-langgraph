"""Roberta contract for future wallet/whale intelligence.

This milestone defines the boundary only. Until CMIS supplies accepted wallet
activity primitives and a later classification contract is approved, Roberta
must not manufacture labels such as insider, whale, bot, accumulator, or
distributor from partial facts.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any


ALLOWED_PRIMITIVES = frozenset(
    {
        "first_observed_activity",
        "last_observed_activity",
        "asset_inflow",
        "asset_outflow",
        "verified_buy",
        "verified_sell",
        "transfer",
        "lp_addition",
        "lp_removal",
        "deployer_originated_transfer",
        "balance_change",
        "activity_window",
        "transaction_count",
        "verified_volume",
        "circulating_supply_share",
    }
)
FORBIDDEN_CLASSIFICATIONS = frozenset(
    {
        "insider",
        "whale",
        "bot",
        "accumulator",
        "distributor",
        "market_maker",
        "manipulator",
        "dumper",
    }
)


class WalletInterpretationContractError(ValueError):
    pass


def validate_wallet_facts(value: Mapping[str, Any]) -> dict[str, Any]:
    """Accept only named deterministic CMIS wallet primitives.

    The values are preserved verbatim. This validator does not derive direction,
    relationships, supply shares, labels, or behavioral classifications.
    """

    if not isinstance(value, Mapping):
        raise TypeError("wallet facts must be a mapping")
    facts: dict[str, Any] = {}
    for raw_name, raw_value in value.items():
        name = str(raw_name or "").strip()
        if name not in ALLOWED_PRIMITIVES:
            raise WalletInterpretationContractError(
                f"unaccepted wallet fact primitive: {name!r}"
            )
        facts[name] = deepcopy(raw_value)
    return facts


def build_wallet_interpretation_contract(
    *,
    chain: str,
    wallet: str,
    facts: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a neutral interpretation envelope with classifications locked."""

    normalized_chain = str(chain or "").strip().lower()
    normalized_wallet = str(wallet or "").strip()
    if not normalized_chain or not normalized_wallet:
        raise ValueError("chain and wallet are required")
    validated = validate_wallet_facts(facts)
    return {
        "chain": normalized_chain,
        "wallet": normalized_wallet,
        "facts": validated,
        "fact_count": len(validated),
        "classification_status": "UNAVAILABLE_PENDING_ACCEPTED_CMIS_PRIMITIVES_AND_CONTRACT",
        "classifications": [],
        "forbidden_classifications": sorted(FORBIDDEN_CLASSIFICATIONS),
        "fact_inference_distinction_preserved": True,
        "execution_authorized": False,
    }


def assert_classification_allowed(label: str) -> None:
    """Fail closed for behavioral labels in the current milestone."""

    normalized = str(label or "").strip().lower().replace(" ", "_")
    if not normalized or normalized in FORBIDDEN_CLASSIFICATIONS:
        raise WalletInterpretationContractError(
            "wallet behavioral classifications are not authorized in this milestone"
        )
    raise WalletInterpretationContractError(
        "no wallet classification contract is accepted in this milestone"
    )


__all__ = [
    "ALLOWED_PRIMITIVES",
    "FORBIDDEN_CLASSIFICATIONS",
    "WalletInterpretationContractError",
    "assert_classification_allowed",
    "build_wallet_interpretation_contract",
    "validate_wallet_facts",
]
