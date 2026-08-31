"""Deterministic X1 Compare workflow orchestration.

The workflow remains inside X1 Scout. It obtains two accepted Instant X1 Scan
reports through the existing Scout graph and, when explicitly requested, one
CMIS all_available_pair history result. It never calls a provider directly,
recomputes CMIS history, combines risk scores, averages proof, or authorizes
execution.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    CMISCapabilityUnavailable,
    require_historical_all_available_capability,
)
from roberta.cmis.client import CMISClient
from roberta.cmis.contracts import CMISEnvelope
from roberta.x1_scout.compare_product import (
    X1_COMPARE_CONTRACT,
    build_x1_compare_product_view,
    render_x1_compare_product_text,
)
from roberta.x1_scout.graph import INTERACTIVE_ALL_HISTORY_MAX_SIGNATURES


X1_COMPARE_WORKFLOW_CONTRACT = "x1_compare_workflow/v1"


def _normalize_asset(name: str, value: object) -> str:
    asset = str(value or "").strip()
    if not asset:
        raise ValueError(f"{name} must not be empty")
    return asset


def _scan_report(
    scout_graph: Any,
    *,
    asset: str,
    objective: str,
) -> dict[str, Any]:
    state = scout_graph.invoke(
        {
            "request": {
                "asset": asset,
                "objective": objective,
                "operation": "instant_x1_scan",
            },
            "status": "running",
        }
    )
    report = state.get("report")
    if not isinstance(report, Mapping):
        raise RuntimeError("X1 Scout Instant X1 Scan completed without a report.")
    return dict(report)


def _history_unavailable(
    *,
    code: str,
    message: str,
) -> CMISEnvelope:
    return {
        "service": "historical_compare",
        "chain": "x1",
        "status": "unavailable",
        "asset": {},
        "data": {},
        "risk": None,
        "confidence": {},
        "sources": [],
        "observed_at": None,
        "warnings": [{"code": code, "message": message}],
        "errors": [],
    }


def _pair_history(
    cmis_client: CMISClient,
    *,
    left_asset: str,
    right_asset: str,
    objective: str,
) -> CMISEnvelope:
    try:
        require_historical_all_available_capability(
            cmis_client.capabilities(),
            chain="x1",
            pair=True,
        )
    except CMISCapabilityUnavailable as exc:
        return _history_unavailable(
            code="cmis_pair_history_unavailable",
            message=str(exc),
        )
    except CMISCapabilityContractError as exc:
        return _history_unavailable(
            code="cmis_pair_history_contract_unavailable",
            message=f"CMIS pair-history contract unavailable: {exc}",
        )

    return cmis_client.historical_compare(
        chain="x1",
        asset=left_asset,
        question=objective,
        mode="all_available_pair",
        compare_asset=right_asset,
        provider_history_backfill=False,
        onchain_max_signatures=INTERACTIVE_ALL_HISTORY_MAX_SIGNATURES,
    )


def _base_report(
    *,
    left_asset: str,
    right_asset: str,
    objective: str,
    include_history: bool,
    left_scan_report: Mapping[str, Any],
    right_scan_report: Mapping[str, Any],
    pair_history: Mapping[str, Any] | None,
) -> dict[str, object]:
    return {
        "contract_version": X1_COMPARE_WORKFLOW_CONTRACT,
        "product_contract_version": X1_COMPARE_CONTRACT,
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_assets": {
            "left": left_asset,
            "right": right_asset,
        },
        "objective": objective,
        "include_history": include_history,
        "left_scan_report": dict(left_scan_report),
        "right_scan_report": dict(right_scan_report),
        "pair_history": (
            dict(pair_history)
            if isinstance(pair_history, Mapping)
            else None
        ),
        "execution_authorized": False,
    }


def run_x1_compare_workflow(
    *,
    cmis_client: CMISClient,
    scout_graph: Any,
    left_asset: str,
    right_asset: str,
    objective: str,
    include_history: bool = False,
) -> dict[str, object]:
    """Run the first-class X1 Compare workflow without creating new fact authority."""

    left = _normalize_asset("left_asset", left_asset)
    right = _normalize_asset("right_asset", right_asset)
    if left == right:
        raise ValueError("X1 Compare requires two distinct requested assets")
    if type(include_history) is not bool:
        raise ValueError("include_history must be boolean")

    normalized_objective = str(objective or "").strip() or "compare X1 assets"

    left_report = _scan_report(
        scout_graph,
        asset=left,
        objective=normalized_objective,
    )
    right_report = _scan_report(
        scout_graph,
        asset=right,
        objective=normalized_objective,
    )

    left_view = left_report.get("instant_x1_scan_product_view")
    right_view = right_report.get("instant_x1_scan_product_view")

    if not isinstance(left_view, Mapping) or not isinstance(right_view, Mapping):
        errors: list[dict[str, str]] = []
        if not isinstance(left_view, Mapping):
            errors.append(
                {
                    "code": "x1_compare_left_scan_unavailable",
                    "message": (
                        "The left asset did not produce a validated Instant X1 Scan "
                        "product view."
                    ),
                }
            )
        if not isinstance(right_view, Mapping):
            errors.append(
                {
                    "code": "x1_compare_right_scan_unavailable",
                    "message": (
                        "The right asset did not produce a validated Instant X1 Scan "
                        "product view."
                    ),
                }
            )
        return {
            **_base_report(
                left_asset=left,
                right_asset=right,
                objective=normalized_objective,
                include_history=include_history,
                left_scan_report=left_report,
                right_scan_report=right_report,
                pair_history=None,
            ),
            "status": "error",
            "compare_product_view": None,
            "compare_product_text": None,
            "warnings": [],
            "errors": errors,
        }

    pair_history = (
        _pair_history(
            cmis_client,
            left_asset=left,
            right_asset=right,
            objective=normalized_objective,
        )
        if include_history
        else None
    )

    try:
        product_view = build_x1_compare_product_view(
            left_requested_asset=left,
            right_requested_asset=right,
            left_scan=left_view,
            right_scan=right_view,
            pair_history=pair_history,
        )
        product_text = render_x1_compare_product_text(product_view)
    except ValueError as exc:
        return {
            **_base_report(
                left_asset=left,
                right_asset=right,
                objective=normalized_objective,
                include_history=include_history,
                left_scan_report=left_report,
                right_scan_report=right_report,
                pair_history=pair_history,
            ),
            "status": "error",
            "compare_product_view": None,
            "compare_product_text": None,
            "warnings": [],
            "errors": [
                {
                    "code": "x1_compare_contract_rejected",
                    "message": str(exc),
                }
            ],
        }

    scan_statuses = {
        str(left_view.get("status") or ""),
        str(right_view.get("status") or ""),
    }
    history_status = (
        str(pair_history.get("status") or "")
        if isinstance(pair_history, Mapping)
        else None
    )
    complete = scan_statuses == {"ok"} and (
        history_status in {None, "ok"}
    )

    warnings: list[object] = []
    for report in (left_report, right_report):
        raw = report.get("warnings")
        if isinstance(raw, list):
            warnings.extend(raw)
    if isinstance(pair_history, Mapping):
        raw = pair_history.get("warnings")
        if isinstance(raw, list):
            warnings.extend(raw)

    return {
        **_base_report(
            left_asset=left,
            right_asset=right,
            objective=normalized_objective,
            include_history=include_history,
            left_scan_report=left_report,
            right_scan_report=right_report,
            pair_history=pair_history,
        ),
        "status": "complete" if complete else "partial",
        "compare_product_view": product_view,
        "compare_product_text": product_text,
        "warnings": warnings,
        "errors": [],
    }


__all__ = [
    "X1_COMPARE_WORKFLOW_CONTRACT",
    "run_x1_compare_workflow",
]
