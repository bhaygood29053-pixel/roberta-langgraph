"""Solana Scout adapter from structured CMIS reports to provider-neutral policy facts."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.messages import ToolMessage

from roberta.policy import (
    EvidenceFrame,
    FactPathSpec,
    PolicyFact,
    PolicyRule,
    extract_policy_facts,
    merge_policy_facts,
)
from roberta.specialists.turn_scope import current_user_turn_messages

_OPERATION_FACT_SPECS: dict[str, tuple[FactPathSpec, ...]] = {
    "market_report": (
        FactPathSpec("market.price", ("findings", "data", "price")),
        FactPathSpec("market.liquidity", ("findings", "data", "liquidity")),
        FactPathSpec("market.lp_count", ("findings", "data", "#LPs")),
        FactPathSpec("market.volume_24h", ("findings", "data", "volume_24h")),
    ),
    "risk_check": (
        FactPathSpec("market.risk_outcome", ("findings", "risk", "outcome")),
        FactPathSpec("market.risk_score", ("findings", "risk", "score")),
    ),
    "tokenomics": (
        FactPathSpec("tokenomics.total_supply", ("findings", "data", "total_supply")),
        FactPathSpec("tokenomics.mint_authority", ("findings", "data", "mint_authority")),
        FactPathSpec("tokenomics.freeze_authority", ("findings", "data", "freeze_authority")),
    ),
    "pre_trade_check": (
        FactPathSpec("trade.side", ("findings", "data", "trade", "side")),
        FactPathSpec(
            "trade.notional_usd",
            ("findings", "data", "trade", "notional_usd"),
        ),
    ),
}


def _evidence_status(cmis_status: object) -> str:
    if cmis_status == "ok":
        return "verified"
    if cmis_status == "partial":
        return "unverified"
    return "insufficient_evidence"


def _freshness(investigation: Mapping[str, Any]) -> str:
    if investigation.get("cmis_status") == "ok" and investigation.get("observed_at_iso"):
        return "fresh"
    return "unknown"


def extract_solana_policy_facts(
    report: Mapping[str, Any],
    *,
    requested_fact_keys: set[str] | None = None,
) -> dict[str, PolicyFact]:
    """Map a Solana Scout report to explicit policy facts without provider inference."""

    if report.get("specialist") != "solana_scout" or report.get("chain") != "solana":
        raise ValueError("policy fact adapter requires a Solana Scout report")

    facts: dict[str, PolicyFact] = {
        "asset.chain": PolicyFact(
            value="solana",
            evidence_status="verified",
            freshness="unknown",
            source="solana_scout",
        )
    }
    asset = report.get("asset")
    if isinstance(asset, Mapping) and asset.get("symbol") is not None:
        facts["asset.symbol"] = PolicyFact(
            value=asset.get("symbol"),
            evidence_status="verified",
            freshness="unknown",
            source="solana_scout",
        )

    investigations = report.get("investigations")
    if not isinstance(investigations, list):
        raise ValueError("Solana Scout report investigations must be a list")

    extracted_sets: list[Mapping[str, PolicyFact]] = [facts]
    for investigation in investigations:
        if not isinstance(investigation, Mapping):
            raise ValueError("Solana Scout investigation must be a mapping")
        operation = str(investigation.get("operation") or "")
        specs = _OPERATION_FACT_SPECS.get(operation, ())
        if requested_fact_keys is not None:
            specs = tuple(spec for spec in specs if spec.fact_key in requested_fact_keys)
        if not specs:
            continue
        frame = EvidenceFrame(
            payload=investigation,
            evidence_status=_evidence_status(investigation.get("cmis_status")),
            freshness=_freshness(investigation),
            source=f"solana_scout/cmis:{operation}",
        )
        extracted_sets.append(extract_policy_facts(frame, specs))

    merged = merge_policy_facts(*extracted_sets)
    if requested_fact_keys is None:
        return merged
    return {key: fact for key, fact in merged.items() if key in requested_fact_keys}


def solana_policy_facts_from_state(
    state: Mapping[str, Any],
    rules: Sequence[PolicyRule],
) -> Mapping[str, PolicyFact]:
    """Use only a Solana Scout ToolMessage from the current user turn."""

    requested = {rule.fact_key for rule in rules}
    messages = current_user_turn_messages(state.get("messages", []))
    for message in reversed(messages):
        if not isinstance(message, ToolMessage) or message.name != "solana_scout_investigate":
            continue
        content = message.content
        if not isinstance(content, str):
            raise ValueError("Solana Scout ToolMessage content must be JSON text")
        try:
            report = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("Solana Scout ToolMessage returned invalid JSON") from exc
        if not isinstance(report, Mapping):
            raise ValueError("Solana Scout ToolMessage JSON must be an object")
        return extract_solana_policy_facts(report, requested_fact_keys=requested)
    return {}
