"""X1 Scout adapter from structured CMIS reports to provider-neutral policy facts."""

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
    # This adapter only calls an observation fresh when the current Scout call is
    # fully OK and carries a normalized observation timestamp. Partial/unavailable
    # output never becomes fresh merely because a timestamp exists.
    if investigation.get("cmis_status") == "ok" and investigation.get("observed_at_iso"):
        return "fresh"
    return "unknown"


def extract_x1_policy_facts(
    report: Mapping[str, Any],
    *,
    requested_fact_keys: set[str] | None = None,
) -> dict[str, PolicyFact]:
    """Map an X1 Scout report to explicit policy facts without provider inference."""

    if report.get("specialist") != "x1_scout" or report.get("chain") != "x1":
        raise ValueError("policy fact adapter requires an X1 Scout report")

    facts: dict[str, PolicyFact] = {
        "asset.chain": PolicyFact(
            value="x1",
            evidence_status="verified",
            freshness="unknown",
            source="x1_scout",
        )
    }
    asset = report.get("asset")
    if isinstance(asset, Mapping) and asset.get("symbol") is not None:
        facts["asset.symbol"] = PolicyFact(
            value=asset.get("symbol"),
            evidence_status="verified",
            freshness="unknown",
            source="x1_scout",
        )

    investigations = report.get("investigations")
    if not isinstance(investigations, list):
        raise ValueError("X1 Scout report investigations must be a list")

    extracted_sets: list[Mapping[str, PolicyFact]] = [facts]
    for investigation in investigations:
        if not isinstance(investigation, Mapping):
            raise ValueError("X1 Scout investigation must be a mapping")
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
            source=f"x1_scout/cmis:{operation}",
        )
        extracted_sets.append(extract_policy_facts(frame, specs))

    merged = merge_policy_facts(*extracted_sets)
    if requested_fact_keys is None:
        return merged
    return {key: fact for key, fact in merged.items() if key in requested_fact_keys}


def x1_policy_facts_from_state(
    state: Mapping[str, Any],
    rules: Sequence[PolicyRule],
) -> Mapping[str, PolicyFact]:
    """Use only an X1 Scout result from the current user turn.

    Before the current turn's Scout tool has run, this returns no market facts so
    fresh/evidence rules become ``needs_evidence`` and the Oracle can delegate.
    ToolMessages retained from earlier turns are historical thread context and
    cannot satisfy the current freshness-sensitive policy decision.
    """

    requested = {rule.fact_key for rule in rules}
    messages = current_user_turn_messages(state.get("messages", []))
    for message in reversed(messages):
        if not isinstance(message, ToolMessage) or message.name != "x1_scout_investigate":
            continue
        content = message.content
        if not isinstance(content, str):
            raise ValueError("X1 Scout ToolMessage content must be JSON text")
        try:
            report = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ValueError("X1 Scout ToolMessage returned invalid JSON") from exc
        if not isinstance(report, Mapping):
            raise ValueError("X1 Scout ToolMessage JSON must be an object")
        return extract_x1_policy_facts(report, requested_fact_keys=requested)
    return {}
