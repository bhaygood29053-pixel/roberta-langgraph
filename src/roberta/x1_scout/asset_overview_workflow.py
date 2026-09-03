"""First-class deterministic X1 Asset Overview workflow.

The workflow composes two already-validated X1 Scout products:
Instant X1 Scan and Burn Intelligence. It does not call providers directly,
recompute CMIS facts, widen holder semantics, invent risk scores, or authorize
execution.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.x1_scout.instant_scan_product_ux import (
    PRODUCT_VIEW_CONTRACT,
    render_instant_x1_scan_product_text,
)
from roberta.x1_scout.burn_intelligence import BURN_INTELLIGENCE_CONTRACT


X1_ASSET_OVERVIEW_CONTRACT = "x1_asset_overview/v1"
X1_ASSET_OVERVIEW_WORKFLOW_CONTRACT = "x1_asset_overview_workflow/v1"

_BASE58_CHARS = frozenset(
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
)


def _normalize_asset(value: object) -> str:
    asset = str(value or "").strip()
    if not asset:
        raise ValueError("asset must not be empty")
    return asset


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _exact_mint(value: object, *, context: str) -> str:
    mint = str(value or "").strip()
    if not (
        32 <= len(mint) <= 44
        and all(character in _BASE58_CHARS for character in mint)
    ):
        raise ValueError(f"{context} requires an exact address-shaped X1 mint")
    return mint


def _run_product(
    scout_graph: Any,
    *,
    asset: str,
    objective: str,
    operation: str,
    product_key: str,
) -> tuple[dict[str, Any], Mapping[str, Any] | None]:
    state = scout_graph.invoke(
        {
            "request": {
                "asset": asset,
                "objective": objective,
                "operation": operation,
            },
            "status": "running",
        }
    )
    report = state.get("report")
    if not isinstance(report, Mapping):
        raise RuntimeError(f"X1 Scout {operation} completed without a report")
    product = report.get(product_key)
    return dict(report), product if isinstance(product, Mapping) else None


def build_x1_asset_overview_product(
    *,
    requested_asset: str,
    scan: Mapping[str, Any],
    burn: Mapping[str, Any],
) -> dict[str, object]:
    """Compose accepted Scout products without recomputing their facts."""

    if scan.get("contract_version") != PRODUCT_VIEW_CONTRACT:
        raise ValueError(
            "Asset Overview requires an accepted Instant X1 Scan product view"
        )
    if burn.get("contract_version") != BURN_INTELLIGENCE_CONTRACT:
        raise ValueError("Asset Overview requires accepted X1 Burn Intelligence")

    for product in (scan, burn):
        if product.get("chain") != "x1":
            raise ValueError("Asset Overview v1 is X1-only")
        if product.get("execution_authorized") is not False:
            raise ValueError(
                "Asset Overview inputs must preserve execution_authorized=false"
            )

    identity = _mapping(scan.get("identity"))
    if identity.get("verified") is not True:
        raise ValueError(
            "Asset Overview requires verified Instant X1 Scan identity before "
            "joining Burn Intelligence"
        )
    scan_mint = _exact_mint(identity.get("mint"), context="Instant X1 Scan identity")

    burn_asset = _mapping(burn.get("asset"))
    burn_mint = _exact_mint(burn_asset.get("mint"), context="Burn Intelligence asset")
    if scan_mint != burn_mint:
        raise ValueError(
            "Asset Overview source products disagree on exact X1 mint identity"
        )

    burn_metrics = burn.get("burn_metrics")
    if not isinstance(burn_metrics, Mapping):
        raise ValueError("Asset Overview requires validated Burn Intelligence metrics")

    statuses = [str(scan.get("status") or ""), str(burn.get("status") or "")]
    status = "ok" if statuses == ["ok", "ok"] else "partial"

    limitations: list[object] = []
    for source in (scan, burn):
        raw = source.get("limitations")
        if isinstance(raw, list):
            limitations.extend(deepcopy(raw))
        raw = source.get("warnings")
        if isinstance(raw, list):
            limitations.extend(deepcopy(raw))

    return {
        "contract_version": X1_ASSET_OVERVIEW_CONTRACT,
        "product": "x1_asset_overview",
        "chain": "x1",
        "requested_asset": requested_asset,
        "status": status,
        "identity": deepcopy(dict(identity)),
        "mint": scan_mint,
        "instant_x1_scan": deepcopy(dict(scan)),
        "burn_intelligence": deepcopy(dict(burn)),
        "source_statuses": {
            "instant_x1_scan": scan.get("status"),
            "burn_intelligence": burn.get("status"),
        },
        "source_contracts": {
            "instant_x1_scan": scan.get("contract_version"),
            "burn_intelligence": burn.get("contract_version"),
        },
        "limitations": limitations,
        "execution_authorized": False,
    }


def _value(value: object) -> str:
    return "UNKNOWN" if value is None else str(value)


def render_x1_asset_overview_product_text(view: Mapping[str, Any]) -> str:
    if view.get("contract_version") != X1_ASSET_OVERVIEW_CONTRACT:
        raise ValueError("unsupported Asset Overview product contract")
    if view.get("execution_authorized") is not False:
        raise ValueError("Asset Overview must preserve execution_authorized=false")

    scan = _mapping(view.get("instant_x1_scan"))
    burn = _mapping(view.get("burn_intelligence"))
    burn_metrics = _mapping(burn.get("burn_metrics"))
    windows = _mapping(burn_metrics.get("windows"))

    lines = [render_instant_x1_scan_product_text(scan), "", "Burn Intelligence"]
    if burn_metrics.get("available") is not True:
        lines.extend(
            [
                "Status: UNAVAILABLE",
                "Verified bounded burn evidence is not available for this asset.",
            ]
        )
    else:
        lines.extend(
            [
                f"Status: {str(burn_metrics.get('status') or burn.get('status') or 'unknown').upper()}",
                (
                    "Verified observed cumulative burn: "
                    f"{_value(burn_metrics.get('verified_burned_observed'))}"
                ),
                (
                    "Observed burn events: "
                    f"{_value(burn_metrics.get('burn_events_observed'))}"
                ),
                (
                    "Lifetime total burn verified: "
                    f"{burn_metrics.get('lifetime_total_burn_verified') is True}"
                ),
            ]
        )
        for label in ("1h", "24h", "7d", "30d"):
            window = _mapping(windows.get(label))
            if not window:
                lines.append(f"{label}: UNAVAILABLE")
                continue
            lines.append(
                f"{label}: status={str(window.get('status') or 'unknown').upper()} "
                f"coverage_verified={window.get('coverage_verified') is True} "
                f"burned_tokens={_value(window.get('burned_tokens'))} "
                f"burn_events={_value(window.get('burn_events'))}"
            )
            if label != "1h":
                comparison = _mapping(window.get("period_over_period"))
                lines.append(
                    f"{label} period-over-period: "
                    f"state={str(comparison.get('change_state') or 'UNKNOWN').upper()} "
                    f"change_pct={_value(comparison.get('percent_change'))}"
                )

    lines.extend(
        [
            "",
            "Asset Overview Boundaries",
            "Burn values are copied from CMIS Burn Intelligence; ROBERTA does not recalculate them.",
            "A bounded observed burn total is not a verified lifetime burn total unless CMIS explicitly proves lifetime coverage.",
            "Proof Score remains separate from risk.",
            "Execution authorized: false",
        ]
    )
    return "\n".join(lines)


def run_x1_asset_overview_workflow(
    *,
    scout_graph: Any,
    asset: str,
    objective: str,
) -> dict[str, object]:
    """Run the bounded first-class X1 Asset Overview workflow."""

    requested_asset = _normalize_asset(asset)
    normalized_objective = (
        str(objective or "").strip()
        or f"asset overview for {requested_asset}"
    )

    scan_report, scan = _run_product(
        scout_graph,
        asset=requested_asset,
        objective=normalized_objective,
        operation="instant_x1_scan",
        product_key="instant_x1_scan_product_view",
    )
    burn_report, burn = _run_product(
        scout_graph,
        asset=requested_asset,
        objective=normalized_objective,
        operation="burn_intelligence",
        product_key="x1_burn_intelligence",
    )

    missing = [
        name
        for name, product in (
            ("instant_x1_scan", scan),
            ("burn_intelligence", burn),
        )
        if not isinstance(product, Mapping)
    ]
    base = {
        "contract_version": X1_ASSET_OVERVIEW_WORKFLOW_CONTRACT,
        "product_contract_version": X1_ASSET_OVERVIEW_CONTRACT,
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": requested_asset,
        "objective": normalized_objective,
        "scan_report": scan_report,
        "burn_report": burn_report,
        "execution_authorized": False,
    }

    if missing:
        return {
            **base,
            "status": "error",
            "asset_overview_product_view": None,
            "asset_overview_product_text": None,
            "warnings": [],
            "errors": [
                {
                    "code": "x1_asset_overview_source_product_unavailable",
                    "message": "Missing validated Scout product(s): " + ", ".join(missing),
                }
            ],
        }

    try:
        product = build_x1_asset_overview_product(
            requested_asset=requested_asset,
            scan=scan,
            burn=burn,
        )
        product_text = render_x1_asset_overview_product_text(product)
    except ValueError as exc:
        return {
            **base,
            "status": "error",
            "asset_overview_product_view": None,
            "asset_overview_product_text": None,
            "warnings": [],
            "errors": [
                {
                    "code": "x1_asset_overview_contract_rejected",
                    "message": str(exc),
                }
            ],
        }

    warnings: list[object] = []
    for report in (scan_report, burn_report):
        raw = report.get("warnings")
        if isinstance(raw, list):
            warnings.extend(deepcopy(raw))

    return {
        **base,
        "status": "complete" if product.get("status") == "ok" else "partial",
        "asset_overview_product_view": product,
        "asset_overview_product_text": product_text,
        "warnings": warnings,
        "errors": [],
    }


__all__ = [
    "X1_ASSET_OVERVIEW_CONTRACT",
    "X1_ASSET_OVERVIEW_WORKFLOW_CONTRACT",
    "build_x1_asset_overview_product",
    "render_x1_asset_overview_product_text",
    "run_x1_asset_overview_workflow",
]
