"""First-class deterministic X1 WHAT CHANGED? workflow.

The workflow composes only already-validated X1 Scout products:
Instant X1 Scan, Burn Intelligence, and Discovery Intelligence. It does not
call providers directly, calculate market deltas, infer causality, or authorize
execution. Change values are surfaced only when the accepted upstream products
already contain them.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.cmis.client import CMISClient


X1_WHAT_CHANGED_CONTRACT = "x1_what_changed/v1"
X1_WHAT_CHANGED_WORKFLOW_CONTRACT = "x1_what_changed_workflow/v1"


def _normalize_asset(value: object) -> str:
    asset = str(value or "").strip()
    if not asset:
        raise ValueError("asset must not be empty")
    return asset


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


def _exact_mint(product: Mapping[str, Any], section: str) -> str | None:
    container = product.get(section)
    if not isinstance(container, Mapping):
        return None
    mint = container.get("mint")
    text = str(mint or "").strip()
    return text or None


def _validated_mint(
    scan: Mapping[str, Any],
    burn: Mapping[str, Any],
    discovery: Mapping[str, Any],
) -> str:
    scan_mint = _exact_mint(scan, "identity")
    burn_mint = _exact_mint(burn, "asset")
    discovery_mint = _exact_mint(discovery, "asset")
    mints = [value for value in (scan_mint, burn_mint, discovery_mint) if value]
    if len(mints) != 3:
        raise ValueError("WHAT CHANGED? requires exact mint identity from all three Scout products")
    if len(set(mints)) != 1:
        raise ValueError("WHAT CHANGED? Scout products disagree on exact X1 mint identity")
    return mints[0]


def build_x1_what_changed_product(
    *,
    requested_asset: str,
    scan: Mapping[str, Any],
    burn: Mapping[str, Any],
    discovery: Mapping[str, Any],
) -> dict[str, object]:
    """Compose accepted product facts without recalculation."""

    if scan.get("contract_version") != "instant_x1_scan_product_view/v1":
        raise ValueError("WHAT CHANGED? requires an accepted Instant X1 Scan product view")
    if burn.get("contract_version") != "x1_burn_intelligence/v1":
        raise ValueError("WHAT CHANGED? requires accepted X1 Burn Intelligence")
    if discovery.get("contract_version") != "x1_discovery_intelligence/v1":
        raise ValueError("WHAT CHANGED? requires accepted X1 Discovery Intelligence")
    for product in (scan, burn, discovery):
        if product.get("chain") != "x1":
            raise ValueError("WHAT CHANGED? v1 is X1-only")
        if product.get("execution_authorized") is not False:
            raise ValueError("WHAT CHANGED? inputs must preserve execution_authorized=false")

    mint = _validated_mint(scan, burn, discovery)
    identity = scan.get("identity")
    history = scan.get("history")
    market = scan.get("market")
    burn_metrics = burn.get("burn_metrics")
    discovery_data = discovery.get("discovery")
    if not all(
        isinstance(value, Mapping)
        for value in (identity, history, market, burn_metrics, discovery_data)
    ):
        raise ValueError("WHAT CHANGED? requires validated market/history/burn/discovery sections")

    coverage = discovery_data.get("coverage")
    if not isinstance(coverage, Mapping):
        raise ValueError("WHAT CHANGED? requires Discovery coverage")
    if discovery_data.get("token_launch_time") is not None:
        raise ValueError("WHAT CHANGED? must not promote first observation to token launch time")
    if discovery_data.get("token_launch_time_verified") is not False:
        raise ValueError("WHAT CHANGED? must preserve token launch time as unverified")
    if coverage.get("continuous_coverage_verified") is not False:
        raise ValueError("WHAT CHANGED? must not promote Discovery continuity")
    if coverage.get("archive_completeness_verified") is not False:
        raise ValueError("WHAT CHANGED? must not promote Discovery archive completeness")

    statuses = [
        str(scan.get("status") or ""),
        str(burn.get("status") or ""),
        str(discovery.get("status") or ""),
    ]
    status = "ok" if statuses == ["ok", "ok", "ok"] else "partial"

    limitations: list[object] = []
    for source in (scan, burn, discovery):
        raw = source.get("limitations")
        if isinstance(raw, list):
            limitations.extend(deepcopy(raw))
        raw = source.get("warnings")
        if isinstance(raw, list):
            limitations.extend(deepcopy(raw))

    return {
        "contract_version": X1_WHAT_CHANGED_CONTRACT,
        "product": "x1_what_changed",
        "chain": "x1",
        "requested_asset": requested_asset,
        "status": status,
        "identity": deepcopy(dict(identity)),
        "mint": mint,
        "current_market": deepcopy(dict(market)),
        "market_history": deepcopy(dict(history)),
        "burn_changes": deepcopy(dict(burn_metrics)),
        "discovery_history": deepcopy(dict(discovery_data)),
        "source_statuses": {
            "instant_x1_scan": scan.get("status"),
            "burn_intelligence": burn.get("status"),
            "discovery_intelligence": discovery.get("status"),
        },
        "source_contracts": {
            "instant_x1_scan": scan.get("contract_version"),
            "burn_intelligence": burn.get("contract_version"),
            "discovery_intelligence": discovery.get("contract_version"),
        },
        "limitations": limitations,
        "execution_authorized": False,
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _change_text(value: object) -> str:
    return "UNKNOWN" if value is None else str(value)


def render_x1_what_changed_product_text(view: Mapping[str, Any]) -> str:
    if view.get("contract_version") != X1_WHAT_CHANGED_CONTRACT:
        raise ValueError("unsupported WHAT CHANGED? product contract")
    if view.get("execution_authorized") is not False:
        raise ValueError("WHAT CHANGED? must preserve execution_authorized=false")

    identity = _mapping(view.get("identity"))
    history = _mapping(view.get("market_history"))
    metrics = _mapping(history.get("metrics"))
    burn = _mapping(view.get("burn_changes"))
    windows = _mapping(burn.get("windows"))
    discovery = _mapping(view.get("discovery_history"))
    coverage = _mapping(discovery.get("coverage"))

    label = (
        identity.get("symbol")
        or identity.get("name")
        or view.get("requested_asset")
        or view.get("mint")
        or "requested X1 asset"
    )

    lines = [
        f"X1 WHAT CHANGED? — {label}",
        f"Status: {str(view.get('status') or 'unknown').upper()}",
        "",
        "MARKET / HISTORY",
    ]
    for metric_name in ("price", "liquidity", "volume_24h", "transactions_24h"):
        metric = _mapping(metrics.get(metric_name))
        title = metric_name.replace("_", " ").title()
        if not metric:
            lines.append(f"{title}: CHANGE UNKNOWN")
            continue
        lines.append(f"{title} status: {str(metric.get('status') or 'unknown').upper()}")
        lines.append(f"{title} total change pct: {_change_text(metric.get('total_change_pct'))}")
        if metric.get("observation_count") is not None:
            lines.append(f"{title} observations: {metric.get('observation_count')}")

    lines.extend(["", "BURN CHANGES"])
    for label_name in ("24h", "7d", "30d"):
        window = _mapping(windows.get(label_name))
        comparison = _mapping(window.get("period_over_period"))
        lines.append(
            f"{label_name}: state={str(comparison.get('change_state') or 'UNKNOWN').upper()} "
            f"change_pct={_change_text(comparison.get('percent_change'))}"
        )

    first = _mapping(discovery.get("first_verified_observation"))
    recent = _mapping(discovery.get("most_recent_verified_observation"))
    lines.extend(
        [
            "",
            "DISCOVERY",
            f"Verified observation count: {_change_text(discovery.get('verified_observation_count'))}",
            f"First verified fact time: {_change_text(first.get('fact_time_unix'))}",
            f"Most recent verified fact time: {_change_text(recent.get('fact_time_unix'))}",
            f"Elapsed observed seconds: {_change_text(coverage.get('elapsed_observed_seconds'))}",
            "Token launch time: NOT VERIFIED",
            "Continuous Discovery coverage: NOT VERIFIED",
            "Discovery archive completeness: NOT VERIFIED",
            "",
            "BOUNDARIES",
            "No ROBERTA market delta is calculated locally.",
            "No causal, manipulation, ownership, or launch inference is added.",
            "Execution authorized: false",
        ]
    )
    return "\n".join(lines)


def run_x1_what_changed_workflow(
    *,
    cmis_client: CMISClient,
    scout_graph: Any,
    asset: str,
    objective: str,
) -> dict[str, object]:
    """Run the bounded first-class WHAT CHANGED? workflow."""

    requested_asset = _normalize_asset(asset)
    normalized_objective = str(objective or "").strip() or f"what changed with {requested_asset}"

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
    discovery_report, discovery = _run_product(
        scout_graph,
        asset=requested_asset,
        objective=normalized_objective,
        operation="discovery_intelligence",
        product_key="x1_discovery_intelligence",
    )

    missing = [
        name
        for name, product in (
            ("instant_x1_scan", scan),
            ("burn_intelligence", burn),
            ("discovery_intelligence", discovery),
        )
        if not isinstance(product, Mapping)
    ]
    base = {
        "contract_version": X1_WHAT_CHANGED_WORKFLOW_CONTRACT,
        "product_contract_version": X1_WHAT_CHANGED_CONTRACT,
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": requested_asset,
        "objective": normalized_objective,
        "scan_report": scan_report,
        "burn_report": burn_report,
        "discovery_report": discovery_report,
        "execution_authorized": False,
    }
    if missing:
        return {
            **base,
            "status": "error",
            "what_changed_product_view": None,
            "what_changed_product_text": None,
            "warnings": [],
            "errors": [
                {
                    "code": "x1_what_changed_source_product_unavailable",
                    "message": "Missing validated Scout product(s): " + ", ".join(missing),
                }
            ],
        }

    try:
        product = build_x1_what_changed_product(
            requested_asset=requested_asset,
            scan=scan,
            burn=burn,
            discovery=discovery,
        )
        text = render_x1_what_changed_product_text(product)
    except ValueError as exc:
        return {
            **base,
            "status": "error",
            "what_changed_product_view": None,
            "what_changed_product_text": None,
            "warnings": [],
            "errors": [
                {
                    "code": "x1_what_changed_contract_rejected",
                    "message": str(exc),
                }
            ],
        }

    warnings: list[object] = []
    for report in (scan_report, burn_report, discovery_report):
        raw = report.get("warnings")
        if isinstance(raw, list):
            warnings.extend(raw)

    return {
        **base,
        "status": "complete" if product.get("status") == "ok" else "partial",
        "what_changed_product_view": product,
        "what_changed_product_text": text,
        "warnings": warnings,
        "errors": [],
    }


__all__ = [
    "X1_WHAT_CHANGED_CONTRACT",
    "X1_WHAT_CHANGED_WORKFLOW_CONTRACT",
    "build_x1_what_changed_product",
    "render_x1_what_changed_product_text",
    "run_x1_what_changed_workflow",
]
