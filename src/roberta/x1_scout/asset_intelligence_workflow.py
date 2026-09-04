"""Full verified X1 Asset Intelligence Packet workflow.

X1 Scout assembles a broad, read-only asset dossier from already-accepted CMIS
products, then attaches request-specific enrichments only when the user supplied
the required inputs. The packet is evidence for ROBERTA; it does not write a
recommendation, recalculate market facts, widen source semantics, or authorize
execution.

The baseline packet attempts:
- Instant X1 Scan v3 product view;
- Burn Intelligence v1;
- Discovery Intelligence v1.

A bounded pre-trade enrichment is attempted only when an explicit BUY/SELL side
and positive USD notional are supplied. Source products whose exact subject
identity cannot be bound to the Scan subject remain visible as unbound source
evidence and are not listed as usable asset sections.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.x1_scout.burn_intelligence import BURN_INTELLIGENCE_CONTRACT
from roberta.x1_scout.discovery_intelligence import DISCOVERY_INTELLIGENCE_CONTRACT
from roberta.x1_scout.instant_scan_product_ux import PRODUCT_VIEW_CONTRACT


X1_ASSET_INTELLIGENCE_CONTRACT = "x1_asset_intelligence/v1"
X1_ASSET_INTELLIGENCE_WORKFLOW_CONTRACT = "x1_asset_intelligence_workflow/v1"

_BASELINE = (
    "instant_x1_scan",
    "burn_intelligence",
    "discovery_intelligence",
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _normalize_asset(value: object) -> str:
    asset = str(value or "").strip()
    if not asset:
        raise ValueError("asset must not be empty")
    return asset


def _report_status(report: Mapping[str, Any]) -> object:
    return report.get("cmis_status") or report.get("status")


def _source_subject(product: Mapping[str, Any] | None, section: str) -> Mapping[str, Any]:
    if not isinstance(product, Mapping):
        return {}
    value = product.get(section)
    return value if isinstance(value, Mapping) else {}


def _canonical_subject_key(subject: Mapping[str, Any]) -> tuple[str, str] | None:
    canonical_id = str(subject.get("canonical_id") or "").strip()
    if canonical_id:
        return ("canonical_id", canonical_id.lower())

    identity_key = str(subject.get("identity_key") or "").strip()
    if identity_key:
        normalized = identity_key.lower()
        if normalized == "native:xnt":
            return ("canonical_id", "x1:native:xnt")
        return ("identity_key", normalized)

    mint = str(subject.get("mint") or subject.get("address") or "").strip()
    if mint:
        return ("mint", mint)

    return None


def _identity_binding(
    scan: Mapping[str, Any] | None,
    source_subject: Mapping[str, Any],
) -> dict[str, object]:
    """Return deterministic exact-subject binding without symbol shortcuts."""

    if not isinstance(scan, Mapping):
        return {
            "state": "unverified",
            "usable_for_canonical_asset": False,
            "reason": "instant_scan_subject_unavailable",
        }

    scan_identity = _source_subject(scan, "identity")
    scan_key = _canonical_subject_key(scan_identity)
    source_key = _canonical_subject_key(source_subject)

    if scan_key is None:
        return {
            "state": "unverified",
            "usable_for_canonical_asset": False,
            "reason": "instant_scan_exact_subject_identity_unverified",
        }
    if source_key is None:
        return {
            "state": "unverified",
            "usable_for_canonical_asset": False,
            "reason": "source_exact_subject_identity_unverified",
            "scan_subject_key": list(scan_key),
        }
    if scan_key != source_key:
        return {
            "state": "mismatch",
            "usable_for_canonical_asset": False,
            "reason": "exact_subject_identity_mismatch",
            "scan_subject_key": list(scan_key),
            "source_subject_key": list(source_key),
        }
    return {
        "state": "verified_match",
        "usable_for_canonical_asset": True,
        "reason": "exact_subject_identity_match",
        "scan_subject_key": list(scan_key),
        "source_subject_key": list(source_key),
    }


def _copy_limitations(product: Mapping[str, Any] | None) -> list[object]:
    if not isinstance(product, Mapping):
        return []
    result: list[object] = []
    for key in ("limitations", "warnings"):
        raw = product.get(key)
        if isinstance(raw, list):
            result.extend(deepcopy(raw))
    return result


def _pretrade_projection(report: Mapping[str, Any] | None) -> dict[str, object] | None:
    if not isinstance(report, Mapping):
        return None
    source = _mapping(report.get("source"))
    if source.get("service") != "cmis" or source.get("operation") != "pre_trade_check":
        return None
    presentation = report.get("pretrade_presentation")
    if not isinstance(presentation, Mapping):
        return None
    return {
        "service": "pre_trade_check",
        "cmis_status": report.get("cmis_status"),
        "asset": deepcopy(dict(_mapping(report.get("asset")))),
        "observed_at": report.get("observed_at"),
        "observed_at_iso": report.get("observed_at_iso"),
        "findings": deepcopy(dict(_mapping(report.get("findings")))),
        "confidence": deepcopy(dict(_mapping(report.get("confidence")))),
        "evidence_context": deepcopy(dict(_mapping(report.get("evidence_context")))),
        "pretrade_presentation": deepcopy(dict(presentation)),
        "sources": deepcopy(list(report.get("sources") or [])),
        "warnings": deepcopy(list(report.get("warnings") or [])),
        "errors": deepcopy(list(report.get("errors") or [])),
        "analysis_only": True,
        "execution_authorized": False,
    }


def build_x1_asset_intelligence_packet(
    *,
    requested_asset: str,
    objective: str,
    scan: Mapping[str, Any] | None,
    burn: Mapping[str, Any] | None,
    discovery: Mapping[str, Any] | None,
    scan_report: Mapping[str, Any],
    burn_report: Mapping[str, Any],
    discovery_report: Mapping[str, Any],
    pretrade_report: Mapping[str, Any] | None = None,
    trade_enrichment_requested: bool = False,
) -> dict[str, object]:
    """Compose accepted Scout products without recomputing their facts."""

    if scan is not None:
        if scan.get("contract_version") != PRODUCT_VIEW_CONTRACT:
            raise ValueError("Asset Intelligence requires accepted Instant X1 Scan product view")
        if scan.get("chain") != "x1":
            raise ValueError("Asset Intelligence v1 is X1-only")
        if scan.get("execution_authorized") is not False:
            raise ValueError("Instant X1 Scan must preserve execution_authorized=false")
    if burn is not None:
        if burn.get("contract_version") != BURN_INTELLIGENCE_CONTRACT:
            raise ValueError("Asset Intelligence requires accepted X1 Burn Intelligence")
        if burn.get("chain") != "x1" or burn.get("execution_authorized") is not False:
            raise ValueError("Burn Intelligence must preserve X1/read-only boundaries")
    if discovery is not None:
        if discovery.get("contract_version") != DISCOVERY_INTELLIGENCE_CONTRACT:
            raise ValueError("Asset Intelligence requires accepted X1 Discovery Intelligence")
        if discovery.get("chain") != "x1" or discovery.get("execution_authorized") is not False:
            raise ValueError("Discovery Intelligence must preserve X1/read-only boundaries")

    bindings: dict[str, dict[str, object]] = {
        "instant_x1_scan": {
            "state": "authoritative_subject" if scan is not None else "unavailable",
            "usable_for_canonical_asset": scan is not None,
            "reason": (
                "scan_defines_packet_subject"
                if scan is not None
                else "validated_scan_product_unavailable"
            ),
        },
        "burn_intelligence": _identity_binding(
            scan,
            _source_subject(burn, "asset"),
        ),
        "discovery_intelligence": _identity_binding(
            scan,
            _source_subject(discovery, "asset"),
        ),
    }

    pretrade = _pretrade_projection(pretrade_report)
    if trade_enrichment_requested:
        bindings["pre_trade_check"] = _identity_binding(
            scan,
            _mapping(pretrade.get("asset")) if pretrade is not None else {},
        )

    source_products: dict[str, object] = {
        "instant_x1_scan": deepcopy(dict(scan)) if scan is not None else None,
        "burn_intelligence": deepcopy(dict(burn)) if burn is not None else None,
        "discovery_intelligence": (
            deepcopy(dict(discovery)) if discovery is not None else None
        ),
    }
    if trade_enrichment_requested:
        source_products["pre_trade_check"] = deepcopy(pretrade)

    available_sections = [
        name
        for name, binding in bindings.items()
        if binding.get("usable_for_canonical_asset") is True
        and source_products.get(name) is not None
    ]
    unbound_sections = [
        name
        for name, binding in bindings.items()
        if source_products.get(name) is not None
        and binding.get("usable_for_canonical_asset") is not True
    ]
    unavailable_sections = [
        name
        for name, product in source_products.items()
        if product is None
    ]

    source_statuses = {
        "instant_x1_scan": _report_status(scan_report),
        "burn_intelligence": _report_status(burn_report),
        "discovery_intelligence": _report_status(discovery_report),
    }
    source_contracts = {
        "instant_x1_scan": scan.get("contract_version") if scan is not None else None,
        "burn_intelligence": burn.get("contract_version") if burn is not None else None,
        "discovery_intelligence": (
            discovery.get("contract_version") if discovery is not None else None
        ),
    }
    if trade_enrichment_requested:
        source_statuses["pre_trade_check"] = (
            _report_status(pretrade_report) if isinstance(pretrade_report, Mapping) else None
        )
        source_contracts["pre_trade_check"] = "pre_trade_check"

    attempted = list(_BASELINE)
    requested_enrichments = ["pre_trade_check"] if trade_enrichment_requested else []
    returned_enrichments = [
        name for name in requested_enrichments if source_products.get(name) is not None
    ]

    limitations: list[object] = []
    for product in (scan, burn, discovery):
        limitations.extend(_copy_limitations(product))
    if pretrade is not None:
        limitations.extend(deepcopy(list(pretrade.get("warnings") or [])))
    for name in unbound_sections:
        limitations.append(
            {
                "code": "x1_asset_intelligence_identity_binding_incomplete",
                "section": name,
                "message": (
                    "This source product is preserved in the packet but is not bound "
                    "to the canonical Scan subject by exact identity evidence."
                ),
            }
        )

    baseline_products_returned = [
        name for name in _BASELINE if source_products.get(name) is not None
    ]
    baseline_attempts_terminal = all(
        source_statuses.get(name) is not None for name in _BASELINE
    )
    all_requested_enrichments_returned = len(returned_enrichments) == len(
        requested_enrichments
    )

    evidence_state = "complete"
    if (
        len(baseline_products_returned) != len(_BASELINE)
        or unbound_sections
        or unavailable_sections
        or not all_requested_enrichments_returned
        or any(
            str(source_statuses.get(name) or "").lower() != "ok"
            for name in source_statuses
            if source_statuses.get(name) is not None
        )
    ):
        evidence_state = "partial"

    return {
        "contract_version": X1_ASSET_INTELLIGENCE_CONTRACT,
        "product": "x1_asset_intelligence",
        "chain": "x1",
        "requested_asset": requested_asset,
        "objective": objective,
        "status": evidence_state,
        "subject": (
            deepcopy(dict(_source_subject(scan, "identity")))
            if scan is not None
            else {"requested_asset": requested_asset}
        ),
        "source_products": source_products,
        "identity_bindings": bindings,
        "available_sections": available_sections,
        "unbound_sections": unbound_sections,
        "unavailable_sections": unavailable_sections,
        "source_statuses": source_statuses,
        "source_contracts": source_contracts,
        "evidence_completion": {
            "baseline_required": list(_BASELINE),
            "baseline_attempted": attempted,
            "baseline_products_returned": baseline_products_returned,
            "all_baseline_attempts_terminal": baseline_attempts_terminal,
            "requested_enrichments": requested_enrichments,
            "returned_enrichments": returned_enrichments,
            "all_requested_enrichments_returned": all_requested_enrichments_returned,
            "decision_input_ready": scan is not None and baseline_attempts_terminal,
        },
        "limitations": limitations,
        "facts_authority": "chain_scout_cmis",
        "judgment_authority": "roberta",
        "read_only": True,
        "execution_authorized": False,
    }


def render_x1_asset_intelligence_packet_text(packet: Mapping[str, Any]) -> str:
    if packet.get("contract_version") != X1_ASSET_INTELLIGENCE_CONTRACT:
        raise ValueError("unsupported X1 Asset Intelligence contract")
    if packet.get("execution_authorized") is not False:
        raise ValueError("Asset Intelligence must preserve execution_authorized=false")

    completion = _mapping(packet.get("evidence_completion"))
    bindings = _mapping(packet.get("identity_bindings"))
    lines = [
        "X1 ASSET INTELLIGENCE PACKET",
        f"Requested asset: {packet.get('requested_asset')}",
        f"Evidence state: {str(packet.get('status') or 'unknown').upper()}",
        "",
        "BASELINE COLLECTION",
    ]
    for name in _BASELINE:
        binding = _mapping(bindings.get(name))
        lines.append(
            f"{name}: status={packet.get('source_statuses', {}).get(name)} "
            f"identity_binding={binding.get('state')}"
        )
    lines.extend(
        [
            "",
            "ENRICHMENTS",
            "requested: " + ", ".join(completion.get("requested_enrichments") or []) or "none",
            "returned: " + ", ".join(completion.get("returned_enrichments") or []) or "none",
            "",
            "BOUNDARY",
            "Scout supplies the dossier; ROBERTA decides which evidence matters to the question.",
            "No source fact is recomputed or widened by this packet.",
            "Execution authorized: false",
        ]
    )
    return "\n".join(lines)


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


def _run_pretrade(
    scout_graph: Any,
    *,
    asset: str,
    objective: str,
    action: str,
    amount_usd: float,
) -> dict[str, Any]:
    state = scout_graph.invoke(
        {
            "request": {
                "asset": asset,
                "objective": objective,
                "operation": "pre_trade_check",
                "action": action,
                "amount_usd": amount_usd,
            },
            "status": "running",
        }
    )
    report = state.get("report")
    if not isinstance(report, Mapping):
        raise RuntimeError("X1 Scout pre_trade_check completed without a report")
    return dict(report)


def _merge_investigations(*reports: Mapping[str, Any] | None) -> list[object]:
    merged: list[object] = []
    for report in reports:
        if not isinstance(report, Mapping):
            continue
        raw = report.get("investigations")
        if isinstance(raw, list):
            merged.extend(deepcopy(raw))
    return merged


def run_x1_asset_intelligence_workflow(
    *,
    scout_graph: Any,
    asset: str,
    objective: str,
    action: str | None = None,
    amount_usd: float | None = None,
) -> dict[str, object]:
    """Run the full baseline dossier plus explicit conditional enrichments."""

    requested_asset = _normalize_asset(asset)
    normalized_objective = (
        str(objective or "").strip()
        or f"full verified asset intelligence for {requested_asset}"
    )

    if (action is None) != (amount_usd is None):
        raise ValueError("asset intelligence pre-trade enrichment requires both action and amount_usd")
    trade_requested = action is not None and amount_usd is not None
    normalized_action: str | None = None
    normalized_amount: float | None = None
    if trade_requested:
        normalized_action = str(action or "").strip().upper()
        if normalized_action not in {"BUY", "SELL"}:
            raise ValueError("asset intelligence action must be BUY or SELL")
        if isinstance(amount_usd, bool) or float(amount_usd) <= 0:
            raise ValueError("asset intelligence amount_usd must be greater than zero")
        normalized_amount = float(amount_usd)

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
    pretrade_report = (
        _run_pretrade(
            scout_graph,
            asset=requested_asset,
            objective=normalized_objective,
            action=normalized_action or "",
            amount_usd=normalized_amount or 0.0,
        )
        if trade_requested
        else None
    )

    base = {
        "contract_version": X1_ASSET_INTELLIGENCE_WORKFLOW_CONTRACT,
        "product_contract_version": X1_ASSET_INTELLIGENCE_CONTRACT,
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": requested_asset,
        "objective": normalized_objective,
        "source": {"service": "x1_scout", "operation": "asset_intelligence"},
        "scan_report": scan_report,
        "burn_report": burn_report,
        "discovery_report": discovery_report,
        "pretrade_report": pretrade_report,
        "investigations": _merge_investigations(
            scan_report,
            burn_report,
            discovery_report,
            pretrade_report,
        ),
        "evidence_context": deepcopy(dict(_mapping(scan_report.get("evidence_context")))),
        "execution_authorized": False,
    }

    try:
        packet = build_x1_asset_intelligence_packet(
            requested_asset=requested_asset,
            objective=normalized_objective,
            scan=scan,
            burn=burn,
            discovery=discovery,
            scan_report=scan_report,
            burn_report=burn_report,
            discovery_report=discovery_report,
            pretrade_report=pretrade_report,
            trade_enrichment_requested=trade_requested,
        )
        packet_text = render_x1_asset_intelligence_packet_text(packet)
    except ValueError as exc:
        return {
            **base,
            "status": "error",
            "asset_intelligence_packet": None,
            "asset_intelligence_packet_text": None,
            "warnings": [],
            "errors": [
                {
                    "code": "x1_asset_intelligence_contract_rejected",
                    "message": str(exc),
                }
            ],
        }

    warnings: list[object] = []
    errors: list[object] = []
    for report in (scan_report, burn_report, discovery_report, pretrade_report):
        if not isinstance(report, Mapping):
            continue
        raw_warnings = report.get("warnings")
        if isinstance(raw_warnings, list):
            warnings.extend(deepcopy(raw_warnings))
        raw_errors = report.get("errors")
        if isinstance(raw_errors, list):
            errors.extend(deepcopy(raw_errors))

    return {
        **base,
        "status": "complete",
        "asset_intelligence_packet": packet,
        "asset_intelligence_packet_text": packet_text,
        "findings": packet,
        "warnings": warnings,
        "errors": errors,
    }


__all__ = [
    "X1_ASSET_INTELLIGENCE_CONTRACT",
    "X1_ASSET_INTELLIGENCE_WORKFLOW_CONTRACT",
    "build_x1_asset_intelligence_packet",
    "render_x1_asset_intelligence_packet_text",
    "run_x1_asset_intelligence_workflow",
]
