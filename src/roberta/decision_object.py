"""Canonical ROBERTA decision/intelligence projection.

The Decision Object is a ROBERTA-owned composition boundary above validated
Chain Scout product output. It never calls CMIS or providers and never
recalculates market facts, tokenomics, history, risk, or Proof Score.

The first v1 tracer bullet accepts only the already-validated X1 Instant Scan
product view. Human and Machine renderers consume the same canonical object so
presentation cannot silently become a second fact authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.x1_scout.instant_scan_product_ux import PRODUCT_VIEW_CONTRACT


DECISION_OBJECT_CONTRACT = "roberta_decision/v1"
MACHINE_INTELLIGENCE_CONTRACT = "roberta_intelligence/v1"


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _require_mapping(container: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = container.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(f"Instant X1 Scan Decision Object requires object section: {key}")
    return value


def _require_list(container: Mapping[str, Any], key: str) -> list[object]:
    value = container.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Instant X1 Scan Decision Object requires list field: {key}")
    return list(value)


def _validate_scan_view(view: Mapping[str, Any]) -> None:
    if view.get("contract_version") != PRODUCT_VIEW_CONTRACT:
        raise ValueError("Decision Object input is not an accepted Instant X1 Scan product view")
    if view.get("product") != "instant_x1_scan" or view.get("chain") != "x1":
        raise ValueError("Decision Object v1 tracer requires an X1 Instant X1 Scan view")
    if view.get("status") not in {"ok", "partial"}:
        raise ValueError("Decision Object input must preserve an ok/partial Scout status")
    if view.get("execution_authorized") is not False:
        raise ValueError("Decision Object input must preserve execution_authorized=false")

    for key in (
        "identity",
        "market",
        "tokenomics",
        "holder_concentration",
        "history",
        "risk",
        "evidence",
    ):
        _require_mapping(view, key)
    for key in ("limitations", "warnings", "errors"):
        _require_list(view, key)

    risk = _mapping(view.get("risk"))
    if risk.get("execution_authorized") is not False:
        raise ValueError("Decision Object risk must preserve execution_authorized=false")

    evidence = _mapping(view.get("evidence"))
    if evidence.get("proof_score_separate_from_risk") is not True:
        raise ValueError("Decision Object must keep Proof Score separate from deterministic risk")


def _unverified_fact_paths(view: Mapping[str, Any]) -> list[str]:
    """Return deterministic availability paths without inventing fact values."""

    paths: list[str] = []
    checked_sections = {
        "market": _mapping(view.get("market")),
        "tokenomics": _mapping(view.get("tokenomics")),
        "holder_concentration": _mapping(view.get("holder_concentration")),
    }
    for section_name, section in checked_sections.items():
        for key, raw in section.items():
            if isinstance(raw, Mapping) and "verified" in raw:
                if raw.get("verified") is not True:
                    paths.append(f"{section_name}.{key}")

    holder = _mapping(view.get("holder_concentration"))
    concentration = _mapping(holder.get("top_account_concentration"))
    if concentration and concentration.get("verified") is not True:
        path = "holder_concentration.top_account_concentration"
        if path not in paths:
            paths.append(path)

    risk = _mapping(view.get("risk"))
    if risk.get("score_verified") is not True:
        paths.append("risk.score")

    return sorted(set(paths))


def build_roberta_decision_object(
    view: Mapping[str, Any],
    *,
    request_id: str | None = None,
) -> dict[str, object]:
    """Project one validated Instant X1 Scan view into canonical ROBERTA state."""

    if not isinstance(view, Mapping):
        raise ValueError("Decision Object input must be an object")
    _validate_scan_view(view)

    identity = _mapping(view.get("identity"))
    risk = _mapping(view.get("risk"))
    limitations = _require_list(view, "limitations")
    warnings = _require_list(view, "warnings")
    errors = _require_list(view, "errors")

    subject = {
        "requested_asset": view.get("requested_asset"),
        "identity_status": identity.get("status"),
        "identity_verified": identity.get("verified") is True,
        "symbol": identity.get("symbol"),
        "name": identity.get("name"),
        "mint": identity.get("mint"),
        "resolved_by": identity.get("resolved_by"),
        "match_quality": identity.get("match_quality"),
    }

    return {
        "contract_version": DECISION_OBJECT_CONTRACT,
        "request_id": request_id,
        "chain": "x1",
        "workflow": "instant_x1_scan",
        "status": view.get("status"),
        "request": {
            "requested_asset": view.get("requested_asset"),
        },
        "subject": subject,
        "decision": {
            # This first slice does not create a new ROBERTA BUY/WAIT/BLOCK
            # policy. It preserves the accepted risk presentation verbatim.
            "recommendation": risk.get("recommendation"),
            "risk_status": risk.get("status"),
            "reason_codes": [],
            "policy_applied": False,
        },
        "facts": {
            "market": deepcopy(dict(_mapping(view.get("market")))),
            "tokenomics": deepcopy(dict(_mapping(view.get("tokenomics")))),
            "holder_concentration": deepcopy(
                dict(_mapping(view.get("holder_concentration")))
            ),
        },
        "risk": deepcopy(dict(risk)),
        "history": deepcopy(dict(_mapping(view.get("history")))),
        "evidence": deepcopy(dict(_mapping(view.get("evidence")))),
        "unknowns": {
            "unverified_fact_paths": _unverified_fact_paths(view),
            "limitations": deepcopy(limitations),
        },
        "limitations": deepcopy(limitations),
        "warnings": deepcopy(warnings),
        "errors": deepcopy(errors),
        "observed_at": view.get("observed_at"),
        "observed_at_iso": view.get("observed_at_iso"),
        "observed_at_display": view.get("observed_at_display"),
        "source_contract": PRODUCT_VIEW_CONTRACT,
        "execution_authorized": False,
    }


def _validate_decision_object(decision: Mapping[str, Any]) -> None:
    if decision.get("contract_version") != DECISION_OBJECT_CONTRACT:
        raise ValueError("unsupported ROBERTA Decision Object contract")
    if decision.get("chain") != "x1" or decision.get("workflow") != "instant_x1_scan":
        raise ValueError("Decision Object v1 tracer supports X1 Instant X1 Scan only")
    if decision.get("status") not in {"ok", "partial"}:
        raise ValueError("Decision Object must preserve an ok/partial source status")
    if decision.get("execution_authorized") is not False:
        raise ValueError("Decision Object must preserve execution_authorized=false")

    risk = _require_mapping(decision, "risk")
    evidence = _require_mapping(decision, "evidence")
    for key in ("request", "subject", "decision", "facts", "history", "unknowns"):
        _require_mapping(decision, key)
    for key in ("limitations", "warnings", "errors"):
        _require_list(decision, key)

    if risk.get("execution_authorized") is not False:
        raise ValueError("Decision Object risk must preserve execution_authorized=false")
    if evidence.get("proof_score_separate_from_risk") is not True:
        raise ValueError("Decision Object must keep Proof Score separate from risk")


def render_machine_intelligence(
    decision: Mapping[str, Any],
    *,
    evidence_depth: str = "standard",
) -> dict[str, object]:
    """Render a stable machine envelope from one canonical Decision Object."""

    if not isinstance(decision, Mapping):
        raise ValueError("Machine ROBERTA requires a Decision Object")
    _validate_decision_object(decision)
    if evidence_depth not in {"standard", "full"}:
        raise ValueError("unsupported Machine ROBERTA evidence depth")

    facts = _mapping(decision.get("facts"))
    envelope: dict[str, object] = {
        "schema": MACHINE_INTELLIGENCE_CONTRACT,
        "request_id": decision.get("request_id"),
        "chain": decision.get("chain"),
        "workflow": decision.get("workflow"),
        "status": decision.get("status"),
        "subject": deepcopy(dict(_mapping(decision.get("subject")))),
        "decision": deepcopy(dict(_mapping(decision.get("decision")))),
        "facts": deepcopy(dict(facts)),
        "risk": deepcopy(dict(_mapping(decision.get("risk")))),
        "history": deepcopy(dict(_mapping(decision.get("history")))),
        "evidence": deepcopy(dict(_mapping(decision.get("evidence")))),
        "unknowns": deepcopy(dict(_mapping(decision.get("unknowns")))),
        "limitations": deepcopy(list(decision.get("limitations") or [])),
        "warnings": deepcopy(list(decision.get("warnings") or [])),
        "errors": deepcopy(list(decision.get("errors") or [])),
        "observed_at": decision.get("observed_at"),
        "observed_at_iso": decision.get("observed_at_iso"),
        "observed_at_display": decision.get("observed_at_display"),
        "evidence_depth": evidence_depth,
        "execution": {"authorized": False},
    }
    if evidence_depth == "full":
        envelope["source_contract"] = decision.get("source_contract")
    return envelope


def _verified_text(label: str, item: object) -> str:
    value = _mapping(item)
    raw = value.get("value")
    if value.get("verified") is True:
        return f"{label}: {raw}"
    if raw is None:
        return f"{label}: unknown"
    return f"{label}: {raw} (unverified)"


def render_human_decision(decision: Mapping[str, Any]) -> str:
    """Render an answer-first human summary from the canonical Decision Object."""

    if not isinstance(decision, Mapping):
        raise ValueError("Human ROBERTA requires a Decision Object")
    _validate_decision_object(decision)

    subject = _mapping(decision.get("subject"))
    decision_state = _mapping(decision.get("decision"))
    facts = _mapping(decision.get("facts"))
    market = _mapping(facts.get("market"))
    risk = _mapping(decision.get("risk"))
    unknowns = _mapping(decision.get("unknowns"))

    identity_label = (
        subject.get("symbol")
        or subject.get("name")
        or subject.get("mint")
        or subject.get("requested_asset")
        or "requested X1 asset"
    )
    recommendation = decision_state.get("recommendation") or "insufficient evidence"

    lines = [
        f"ROBERTA — {identity_label}",
        f"Conclusion: {recommendation}",
        f"Status: {decision.get('status')}",
        f"Observed: {decision.get('observed_at_display') or decision.get('observed_at_iso') or 'unknown'}",
        "",
        "Key verified market facts",
        _verified_text("Price USD", market.get("price_usd")),
        _verified_text("Liquidity USD", market.get("liquidity_usd")),
        _verified_text("24h Volume USD", market.get("volume_24h_usd")),
        "",
        "Risk",
        f"Recommendation: {risk.get('recommendation') or 'unknown'}",
        (
            f"Risk score: {risk.get('score')}"
            if risk.get("score_verified") is True
            else "Risk score: unavailable/unverified"
        ),
    ]

    reasons = risk.get("reasons")
    if isinstance(reasons, list) and reasons:
        lines.append("Evidence-backed risk reasons:")
        lines.extend(f"- {reason}" for reason in reasons[:4])

    paths = unknowns.get("unverified_fact_paths")
    limitations = decision.get("limitations")
    if (isinstance(paths, list) and paths) or (isinstance(limitations, list) and limitations):
        lines.extend(["", "Important unknowns / limitations"])
        if isinstance(paths, list):
            lines.extend(f"- Unverified: {path}" for path in paths)
        if isinstance(limitations, list):
            lines.extend(f"- {item}" for item in limitations)

    lines.extend(["", "Execution authorized: false"])
    return "\n".join(lines)


__all__ = [
    "DECISION_OBJECT_CONTRACT",
    "MACHINE_INTELLIGENCE_CONTRACT",
    "build_roberta_decision_object",
    "render_human_decision",
    "render_machine_intelligence",
]
