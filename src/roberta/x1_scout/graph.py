"""X1 Scout LangGraph specialist subgraph.

X1 Scout owns X1-specific investigation planning and interpretation. CMIS owns
deterministic current market/tokenomics/risk/verification services and the X1
Provider beneath them. Evidence receipt/proof metadata is projected separately
from market findings so Roberta can explain proof without rewriting facts.
"""

from collections.abc import Callable, Mapping
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    CMISCapabilityUnavailable,
    X1_ASSET_IDENTITY_CONTRACT_VERSION,
    require_bridge_to_xdex_utilization_capability,
    require_burn_intelligence_capability,
    require_cross_chain_provenance_capability,
    require_discovery_intelligence_capability,
    require_instant_x1_scan_capability,
    require_x1_normalized_asset_identity_capability,
)
from roberta.cmis.client import CMISClient
from roberta.cmis.contracts import CMISEnvelope, CMISOperation
from roberta.cmis.instant_scan import (
    CMISInstantX1ScanContractError,
    validate_instant_x1_scan_response,
)
from roberta.evidence_aware import evidence_context
from roberta.presentation import format_component_status_table
from roberta.pretrade_ux import build_pretrade_presentation
from roberta.risk_help import build_risk_help
from roberta.status_help import build_cmis_status_help
from roberta.time_utils import format_observed_at_utc, normalize_observed_at
from roberta.x1_scout.bridge_to_xdex_utilization import (
    X1BridgeToXdexContractError,
    build_x1_bridge_to_xdex_utilization,
)
from roberta.x1_scout.cross_chain_provenance import (
    X1CrossChainProvenanceContractError,
    build_x1_cross_chain_provenance,
)
from roberta.x1_scout.burn_intelligence import (
    X1BurnIntelligenceContractError,
    build_x1_burn_intelligence,
)
from roberta.x1_scout.discovery_intelligence import (
    X1DiscoveryIntelligenceContractError,
    build_x1_discovery_intelligence,
)
from roberta.x1_scout.concentration_warning_intelligence import (
    X1ConcentrationWarningContractError,
    build_x1_concentration_warning_intelligence,
)
from roberta.x1_scout.history_presentation import (
    build_historical_coverage_presentation,
)
from roberta.x1_scout.instant_scan_presentation import (
    build_instant_x1_scan_presentation,
)
from roberta.x1_scout.instant_scan_product_ux import (
    build_instant_x1_scan_product_view,
    render_instant_x1_scan_product_text,
)
from roberta.x1_scout.planner import (
    compare_asset_from_objective,
    enforce_plan,
    propose_plan,
    historical_mode_from_objective,
    rank_limit_from_objective,
    rank_metric_from_objective,
    select_cmis_operation,
)
from roberta.x1_scout.state import (
    X1ScoutInvestigation,
    X1ScoutReport,
    X1ScoutState,
)


INTERACTIVE_ALL_HISTORY_MAX_SIGNATURES = 1000


def plan_cmis_operation(state: X1ScoutState) -> dict[str, Any]:
    """Backward-compatible deterministic single-operation planning helper."""
    request = dict(state["request"])
    if "operation" not in request:
        request["operation"] = select_cmis_operation(request["objective"])
    return {"request": request, "status": "running"}


def make_plan_proposal_node(planner_model: Any | None) -> Callable[[X1ScoutState], dict[str, Any]]:
    def propose_plan_node(state: X1ScoutState) -> dict[str, Any]:
        request = state["request"]
        if "operation" in request or planner_model is None:
            return {"plan_proposal": None, "planner_error": None, "status": "running"}
        try:
            proposal = propose_plan(planner_model, request)
        except Exception as exc:
            return {
                "plan_proposal": None,
                "planner_error": f"{type(exc).__name__}: {exc}",
                "status": "running",
            }
        return {"plan_proposal": proposal, "planner_error": None, "status": "running"}

    return propose_plan_node


def enforce_plan_node(state: X1ScoutState) -> dict[str, Any]:
    plan = enforce_plan(
        state["request"],
        state.get("plan_proposal"),
        planner_error=state.get("planner_error"),
    )
    return {"plan": plan, "status": "running"}


def _dispatch_cmis_operation(
    cmis_client: CMISClient,
    request: dict[str, Any],
    operation: CMISOperation,
) -> CMISEnvelope:
    asset = request["asset"]
    objective = request["objective"]
    if operation == "instant_x1_scan":
        try:
            require_instant_x1_scan_capability(
                cmis_client.capabilities(),
                chain="x1",
            )
        except CMISCapabilityUnavailable as exc:
            return {
                "service": "instant_x1_scan",
                "chain": "x1",
                "status": "unavailable",
                "asset": {"query": asset},
                "data": {},
                "risk": None,
                "confidence": {},
                "sources": [],
                "observed_at": None,
                "warnings": [{
                    "code": "cmis_instant_x1_scan_unavailable",
                    "message": str(exc),
                }],
                "errors": [],
            }
        except CMISCapabilityContractError as exc:
            return {
                "service": "instant_x1_scan",
                "chain": "x1",
                "status": "unavailable",
                "asset": {"query": asset},
                "data": {},
                "risk": None,
                "confidence": {},
                "sources": [],
                "observed_at": None,
                "warnings": [{
                    "code": "cmis_instant_x1_scan_contract_unavailable",
                    "message": f"CMIS Instant X1 Scan contract unavailable: {exc}",
                }],
                "errors": [],
            }
        result = cmis_client.instant_x1_scan(chain="x1", asset=asset)
        try:
            return validate_instant_x1_scan_response(result)
        except CMISInstantX1ScanContractError as exc:
            return {
                "service": "instant_x1_scan",
                "chain": "x1",
                "status": "error",
                "asset": {"query": asset},
                "data": {},
                "risk": None,
                "confidence": {},
                "sources": [],
                "observed_at": None,
                "warnings": [],
                "errors": [{
                    "code": "invalid_cmis_instant_x1_scan_response",
                    "message": str(exc),
                }],
            }
    if operation == "market_report":
        return cmis_client.market_report(chain="x1", asset=asset)
    if operation == "rank":
        return cmis_client.rank(
            chain="x1",
            metric=rank_metric_from_objective(objective),
            limit=rank_limit_from_objective(objective),
        )
    if operation == "historical_compare":
        mode = historical_mode_from_objective(
            objective,
            compare_asset=request.get("compare_asset"),
        )
        return cmis_client.historical_compare(
            chain="x1",
            asset=asset,
            question=str(objective),
            mode=mode,
            compare_asset=(
                str(request["compare_asset"])
                if mode == "all_available_pair"
                else None
            ),
            provider_history_backfill=(False if mode != "window" else None),
            onchain_max_signatures=(
                INTERACTIVE_ALL_HISTORY_MAX_SIGNATURES
                if mode != "window"
                else None
            ),
        )
    if operation == "burn_intelligence":
        try:
            require_burn_intelligence_capability(
                cmis_client.capabilities(),
                chain="x1",
            )
        except CMISCapabilityUnavailable as exc:
            return {
                "service": "burn_intelligence",
                "chain": "x1",
                "status": "unavailable",
                "asset": {"query": asset},
                "data": {},
                "risk": None,
                "confidence": {},
                "sources": [],
                "observed_at": None,
                "warnings": [{
                    "code": "cmis_burn_intelligence_unavailable",
                    "message": str(exc),
                }],
                "errors": [],
            }
        except CMISCapabilityContractError as exc:
            return {
                "service": "burn_intelligence",
                "chain": "x1",
                "status": "unavailable",
                "asset": {"query": asset},
                "data": {},
                "risk": None,
                "confidence": {},
                "sources": [],
                "observed_at": None,
                "warnings": [{
                    "code": "cmis_burn_intelligence_contract_unavailable",
                    "message": f"CMIS Burn Intelligence contract unavailable: {exc}",
                }],
                "errors": [],
            }
        result = cmis_client.burn_intelligence(chain="x1", asset=asset)
        if result.get("status") in {"ok", "partial"}:
            try:
                build_x1_burn_intelligence(
                    result,
                    requested_asset=str(asset),
                )
            except X1BurnIntelligenceContractError as exc:
                return {
                    "service": "burn_intelligence",
                    "chain": "x1",
                    "status": "error",
                    "asset": dict(result.get("asset") or {"query": asset}),
                    "data": {},
                    "risk": None,
                    "confidence": {},
                    "sources": list(result.get("sources") or []),
                    "observed_at": result.get("observed_at"),
                    "warnings": list(result.get("warnings") or []),
                    "errors": [{
                        "code": "invalid_cmis_burn_intelligence_response",
                        "message": str(exc),
                    }],
                }
        return result
    if operation == "discovery_intelligence":
        try:
            require_discovery_intelligence_capability(
                cmis_client.capabilities(),
                chain="x1",
            )
        except (CMISCapabilityUnavailable, CMISCapabilityContractError) as exc:
            return {
                "service": "discovery_intelligence",
                "chain": "x1",
                "status": "unavailable",
                "asset": {"query": asset},
                "data": {},
                "risk": None,
                "confidence": {},
                "sources": [],
                "observed_at": None,
                "warnings": [{
                    "code": "cmis_discovery_intelligence_contract_unavailable",
                    "message": str(exc),
                }],
                "errors": [],
            }
        result = cmis_client.discovery_intelligence(chain="x1", asset=asset)
        if result.get("status") in {"partial", "unavailable"}:
            try:
                build_x1_discovery_intelligence(
                    result,
                    requested_asset=str(asset),
                )
            except X1DiscoveryIntelligenceContractError as exc:
                return {
                    "service": "discovery_intelligence",
                    "chain": "x1",
                    "status": "error",
                    "asset": dict(result.get("asset") or {"query": asset}),
                    "data": {},
                    "risk": None,
                    "confidence": {},
                    "sources": list(result.get("sources") or []),
                    "observed_at": result.get("observed_at"),
                    "warnings": list(result.get("warnings") or []),
                    "errors": [{
                        "code": "invalid_cmis_discovery_intelligence_response",
                        "message": str(exc),
                    }],
                }
        return result
    if operation == "tokenomics":
        return cmis_client.tokenomics(chain="x1", asset=asset)
    if operation == "risk_check":
        return cmis_client.risk_check(chain="x1", asset=asset)
    if operation == "verification_evidence":
        return cmis_client.verification_evidence(
            chain="x1",
            evidence_id=request.get("evidence_id"),
            fact_type=request.get("fact_type"),
            subject_id=request.get("subject_id"),
        )
    if operation == "concentration_change_intelligence":
        intelligence_evidence_id = request.get("intelligence_evidence_id")
        if intelligence_evidence_id is None:
            raise ValueError(
                "concentration_change_intelligence requires an exact intelligence_evidence_id"
            )
        return cmis_client.concentration_change_intelligence(
            chain="x1",
            asset=asset,
            intelligence_evidence_id=intelligence_evidence_id,
        )
    if operation == "concentration_warning_intelligence":
        required = {
            "intelligence_evidence_ids": request.get("intelligence_evidence_ids"),
            "warning_threshold_policy": request.get("warning_threshold_policy"),
            "warning_threshold_unit": request.get("warning_threshold_unit"),
            "warning_comparator": request.get("warning_comparator"),
            "warning_evaluated_at": request.get("warning_evaluated_at"),
            "warning_max_latest_age_seconds": request.get("warning_max_latest_age_seconds"),
            "warning_max_persistence_window_seconds": request.get(
                "warning_max_persistence_window_seconds"
            ),
        }
        missing = [key for key, value in required.items() if value is None]
        if missing:
            raise ValueError(
                "concentration_warning_intelligence missing explicit inputs: "
                + ", ".join(sorted(missing))
            )
        return cmis_client.concentration_warning_intelligence(
            chain="x1",
            asset=asset,
            intelligence_evidence_ids=required["intelligence_evidence_ids"],
            threshold_policy=required["warning_threshold_policy"],
            threshold_unit=required["warning_threshold_unit"],
            comparator=required["warning_comparator"],
            evaluated_at=required["warning_evaluated_at"],
            max_latest_age_seconds=required["warning_max_latest_age_seconds"],
            max_persistence_window_seconds=required[
                "warning_max_persistence_window_seconds"
            ],
        )
    if operation == "bridge_to_xdex_utilization":
        required = {
            "evidence_sha256": request.get("bridge_evidence_sha256"),
            "route_id": request.get("bridge_route_id"),
            "source_mint": request.get("bridge_source_mint"),
            "destination_mint": request.get("bridge_destination_mint"),
            "evaluated_at": request.get("bridge_evaluated_at"),
            "max_evidence_age_seconds": request.get(
                "bridge_max_evidence_age_seconds"
            ),
        }
        missing = [key for key, value in required.items() if value is None]
        if missing:
            raise ValueError(
                "bridge_to_xdex_utilization missing explicit inputs: "
                + ", ".join(sorted(missing))
            )
        try:
            require_bridge_to_xdex_utilization_capability(
                cmis_client.capabilities(),
                chain="x1",
            )
        except (CMISCapabilityUnavailable, CMISCapabilityContractError) as exc:
            return {
                "service": "bridge_to_xdex_utilization",
                "chain": "x1",
                "status": "unavailable",
                "asset": {"query": asset},
                "data": {},
                "risk": None,
                "confidence": {},
                "sources": [],
                "observed_at": None,
                "warnings": [{
                    "code": "cmis_bridge_to_xdex_contract_unavailable",
                    "message": str(exc),
                }],
                "errors": [],
            }
        return cmis_client.bridge_to_xdex_utilization(
            chain="x1",
            evidence_sha256=required["evidence_sha256"],
            route_id=required["route_id"],
            source_mint=required["source_mint"],
            destination_mint=required["destination_mint"],
            evaluated_at=required["evaluated_at"],
            max_evidence_age_seconds=required["max_evidence_age_seconds"],
        )
    if operation == "cross_chain_asset_provenance":
        required = {
            "evidence_sha256": request.get("provenance_evidence_sha256"),
            "current_asset_id": request.get("provenance_current_asset_id"),
            "current_asset_id_kind": request.get(
                "provenance_current_asset_id_kind"
            ),
        }
        missing = [key for key, value in required.items() if value is None]
        if missing:
            raise ValueError(
                "cross_chain_asset_provenance missing explicit inputs: "
                + ", ".join(sorted(missing))
            )
        try:
            require_cross_chain_provenance_capability(
                cmis_client.capabilities(),
                chain="x1",
            )
        except (CMISCapabilityUnavailable, CMISCapabilityContractError) as exc:
            return {
                "service": "cross_chain_asset_provenance",
                "chain": "x1",
                "status": "unavailable",
                "asset": {"query": asset},
                "data": {},
                "risk": None,
                "confidence": {},
                "sources": [],
                "observed_at": None,
                "warnings": [{
                    "code": "cmis_cross_chain_provenance_contract_unavailable",
                    "message": str(exc),
                }],
                "errors": [],
            }
        return cmis_client.cross_chain_asset_provenance(
            chain="x1",
            evidence_sha256=required["evidence_sha256"],
            current_asset_id=required["current_asset_id"],
            current_asset_id_kind=required["current_asset_id_kind"],
        )
    if operation == "pre_trade_check":
        action = request.get("action")
        amount_usd = request.get("amount_usd")
        if action is None or amount_usd is None:
            raise ValueError("pre_trade_check requires action and amount_usd in X1 Scout state")
        return cmis_client.pre_trade_check(
            chain="x1",
            asset=asset,
            action=action,
            amount_usd=amount_usd,
        )
    raise ValueError(f"Unsupported CMIS operation: {operation!r}")  # pragma: no cover


_BASE58_CHARS = frozenset(
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
)


def _looks_like_exact_x1_mint(value: object) -> bool:
    """Select identity preflight candidates without deciding chain identity."""
    text = str(value or "").strip()
    return bool(
        32 <= len(text) <= 44
        and all(char in _BASE58_CHARS for char in text)
    )


def _accepted_normalized_identity(
    result: object,
    *,
    requested_asset: object,
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    """Validate CMIS identity output without recomputing reconciliation."""
    if not isinstance(result, Mapping):
        return None, None
    data = result.get("data")
    if not isinstance(data, Mapping):
        return None, None
    if data.get("identity_contract") != X1_ASSET_IDENTITY_CONTRACT_VERSION:
        return None, None

    normalized = data.get("normalized_identity")
    reconciliation = data.get("identity_reconciliation")
    if not isinstance(normalized, Mapping) or not isinstance(reconciliation, Mapping):
        return None, None
    if normalized.get("identity_root") != "mint":
        return None, None

    status = result.get("status")
    if status not in {"ok", "partial", "unavailable"}:
        return None, None

    requested = str(requested_asset or "").strip()
    if str(normalized.get("mint") or "").strip() != requested:
        return None, None

    verified = normalized.get("normalized_onchain_identity_verified")
    if not isinstance(verified, bool):
        return None, None

    reconciliation_state = reconciliation.get("state")
    accepted_states = {
        "agreement",
        "metaplex_only",
        "descriptor_conflict",
        "xdex_unavailable",
        "metadata_unavailable",
    }
    if reconciliation_state not in accepted_states:
        return None, None

    if reconciliation_state == "metadata_unavailable":
        if verified is not False:
            return None, None
    else:
        if verified is not True:
            return None, None
        if normalized.get("descriptor_source") != "metaplex_token_metadata":
            return None, None

    return dict(normalized), dict(reconciliation)


def make_cmis_calls_node(cmis_client: CMISClient) -> Callable[[X1ScoutState], dict[str, Any]]:
    def cmis_calls_node(state: X1ScoutState) -> dict[str, Any]:
        request = dict(state["request"])
        if "compare_asset" not in request:
            inferred_compare = compare_asset_from_objective(
                request.get("objective"),
                primary_asset=request.get("asset"),
            )
            if inferred_compare is not None:
                request["compare_asset"] = inferred_compare

        operations = state["plan"]["operations"]
        identity_result = None
        # Instant X1 Scan is an accepted CMIS composition service. Do not
        # recreate part of that composition with a separate Scout-side identity
        # request; preserve the single service result and its own identity section.
        if (
            "instant_x1_scan" not in operations
            and "bridge_to_xdex_utilization" not in operations
            and _looks_like_exact_x1_mint(request.get("asset"))
        ):
            try:
                require_x1_normalized_asset_identity_capability(
                    cmis_client.capabilities()
                )
            except (CMISCapabilityContractError, CMISCapabilityUnavailable):
                identity_result = None
            else:
                identity_result = cmis_client.asset_lookup(
                    chain="x1",
                    asset=str(request["asset"]),
                )

        results = [
            _dispatch_cmis_operation(cmis_client, request, operation)
            for operation in operations
        ]
        if not results:  # pragma: no cover
            raise RuntimeError("X1 Scout plan completed without a CMIS operation.")
        return {
            "request": request,
            "cmis_results": results,
            "cmis_result": results[-1],
            "cmis_identity_result": identity_result,
            "status": "running",
        }

    return cmis_calls_node


def make_cmis_call_node(cmis_client: CMISClient) -> Callable[[X1ScoutState], dict[str, Any]]:
    return make_cmis_calls_node(cmis_client)


def _summarize_cmis_result(
    result: CMISEnvelope,
    *,
    objective: object = None,
) -> X1ScoutInvestigation:
    service = result["service"]
    cmis_status = result["status"]
    observed_at = result["observed_at"]
    observed_at_iso = normalize_observed_at(observed_at)
    risk = dict(result["risk"]) if result["risk"] is not None else None
    confidence = dict(result["confidence"])
    risk_help = build_risk_help(risk, confidence)
    proof = evidence_context(result)
    historical_coverage_presentation = build_historical_coverage_presentation(result)
    instant_scan_presentation = build_instant_x1_scan_presentation(result)

    investigation: X1ScoutInvestigation = {
        "operation": service,
        "asset": dict(result["asset"]),
        "cmis_status": cmis_status,
        "cmis_status_help": build_cmis_status_help(service, cmis_status, confidence),
        "observed_at": observed_at,
        "observed_at_iso": observed_at_iso,
        "observed_at_display": format_observed_at_utc(observed_at_iso),
        "findings": {"data": dict(result["data"]), "risk": risk},
        "confidence": confidence,
        "evidence_context": proof,
        "risk_help": risk_help,
        "component_status_table": format_component_status_table(risk_help),
        "pretrade_presentation": build_pretrade_presentation(result, objective=objective),
        "sources": list(result["sources"]),
        "warnings": list(result["warnings"]),
        "errors": list(result["errors"]),
    }
    if historical_coverage_presentation is not None:
        investigation["historical_coverage_presentation"] = (
            historical_coverage_presentation
        )
    if instant_scan_presentation is not None:
        investigation["instant_x1_scan_presentation"] = instant_scan_presentation
    return investigation


def _xnt_symbol_scope_warning(
    requested_asset: object,
    results: list[CMISEnvelope],
) -> dict[str, object] | None:
    """Flag symbol-only XNT when CMIS resolves a wrapped representation.

    The Scout does not decide native/wrapped equivalence. It only preserves the
    CMIS descriptor and prevents a symbol-only request from silently collapsing
    distinct representations into one analytical subject.
    """

    if str(requested_asset or "").strip().upper() != "XNT":
        return None

    variants: list[dict[str, object]] = []
    wrapped_descriptor_seen = False
    for result in results:
        asset = result.get("asset")
        if not isinstance(asset, Mapping):
            continue
        descriptor = {
            key: asset.get(key)
            for key in ("symbol", "name", "mint")
            if asset.get(key) is not None
        }
        if descriptor and descriptor not in variants:
            variants.append(descriptor)
        name = str(asset.get("name") or "").strip().lower()
        if "wrapped" in name:
            wrapped_descriptor_seen = True

    if not wrapped_descriptor_seen:
        return None

    return {
        "code": "x1_xnt_native_wrapped_scope_unresolved",
        "message": (
            "The request used the symbol XNT, while at least one CMIS investigation "
            "resolved an asset descriptor containing 'Wrapped'. Native XNT and a "
            "wrapped/token representation must not be treated as identical without "
            "stronger identity evidence."
        ),
        "requested_asset": "XNT",
        "resolved_asset_variants": variants,
    }


def interpret_cmis_result(state: X1ScoutState) -> dict[str, Any]:
    """Preserve every CMIS result and attach deterministic presentation/evidence."""
    request = state["request"]
    results = state.get("cmis_results") or [state["cmis_result"]]
    investigations = [
        _summarize_cmis_result(result, objective=request["objective"])
        for result in results
    ]
    primary_result = results[-1]
    primary = investigations[-1]
    identity_result = state.get("cmis_identity_result")
    normalized_identity, identity_reconciliation = _accepted_normalized_identity(
        identity_result,
        requested_asset=request["asset"],
    )

    report_status: Literal["complete", "error"] = (
        "error"
        if any(
            investigation["cmis_status"] in {"unavailable", "ambiguous", "error"}
            for investigation in investigations
        )
        else "complete"
    )

    xnt_scope_warning = _xnt_symbol_scope_warning(
        request["asset"],
        list(results),
    )

    report: X1ScoutReport = {
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": request["asset"],
        "asset": (
            {
                key: normalized_identity.get(key)
                for key in ("symbol", "name", "mint")
                if normalized_identity.get(key) is not None
            }
            if normalized_identity is not None
            and normalized_identity.get("normalized_onchain_identity_verified") is True
            else dict(primary_result["asset"])
        ),
        "objective": request["objective"],
        "status": report_status,
        "plan": dict(state["plan"]),
        "investigations": investigations,
        "cmis_status": primary["cmis_status"],
        "cmis_status_help": primary["cmis_status_help"],
        "observed_at": primary["observed_at"],
        "observed_at_iso": primary["observed_at_iso"],
        "observed_at_display": primary["observed_at_display"],
        "findings": dict(primary["findings"]),
        "confidence": dict(primary["confidence"]),
        "evidence_context": dict(primary["evidence_context"]),
        "risk_help": primary["risk_help"],
        "component_status_table": primary["component_status_table"],
        "pretrade_presentation": primary["pretrade_presentation"],
        "source": {"service": "cmis", "operation": primary["operation"]},
        "sources": list(primary["sources"]),
        "warnings": [
            *(
                list(identity_result.get("warnings") or [])
                if isinstance(identity_result, Mapping)
                else []
            ),
            *([xnt_scope_warning] if xnt_scope_warning is not None else []),
            *list(primary["warnings"]),
        ],
        "errors": list(primary["errors"]),
    }
    historical_coverage_presentation = primary.get(
        "historical_coverage_presentation"
    )
    if historical_coverage_presentation is not None:
        report["historical_coverage_presentation"] = dict(
            historical_coverage_presentation
        )
    instant_scan_presentation = primary.get("instant_x1_scan_presentation")
    if instant_scan_presentation is not None:
        report["instant_x1_scan_presentation"] = dict(
            instant_scan_presentation
        )
        product_view = build_instant_x1_scan_product_view(report)
        if product_view is not None:
            report["instant_x1_scan_product_view"] = product_view
            report["instant_x1_scan_product_text"] = (
                render_instant_x1_scan_product_text(product_view)
            )
    if normalized_identity is not None:
        report["normalized_asset_identity"] = normalized_identity
        report["asset_identity_reconciliation"] = identity_reconciliation or {}
        if isinstance(identity_result, Mapping):
            identity_status = identity_result.get("status")
            if identity_status in {
                "ok",
                "partial",
                "unavailable",
                "ambiguous",
                "error",
            }:
                report["asset_identity_status"] = identity_status

    if primary_result.get("service") == "burn_intelligence" and primary_result.get("status") in {"ok", "partial"}:
        try:
            report["x1_burn_intelligence"] = build_x1_burn_intelligence(
                primary_result,
                requested_asset=str(request["asset"]),
            )
        except X1BurnIntelligenceContractError:
            # Dispatch validation should already have converted malformed
            # dedicated burn responses into a CMIS error envelope.
            pass

    if primary_result.get("service") == "discovery_intelligence" and primary_result.get("status") in {"partial", "unavailable"}:
        try:
            report["x1_discovery_intelligence"] = build_x1_discovery_intelligence(
                primary_result,
                requested_asset=str(request["asset"]),
            )
        except X1DiscoveryIntelligenceContractError:
            pass

    if primary_result.get("service") == "concentration_warning_intelligence" and primary_result.get("status") == "ok":
        try:
            report["x1_concentration_warning_intelligence"] = (
                build_x1_concentration_warning_intelligence(
                    primary_result,
                    requested_asset=str(request["asset"]),
                )
            )
        except X1ConcentrationWarningContractError:
            pass

    if primary_result.get("service") == "bridge_to_xdex_utilization" and primary_result.get("status") == "ok":
        expected_request = {
            "evidence_sha256": request.get("bridge_evidence_sha256"),
            "route_id": request.get("bridge_route_id"),
            "source_mint": request.get("bridge_source_mint"),
            "destination_mint": request.get("bridge_destination_mint"),
            "evaluated_at": request.get("bridge_evaluated_at"),
            "max_evidence_age_seconds": request.get(
                "bridge_max_evidence_age_seconds"
            ),
        }
        try:
            report["x1_bridge_to_xdex_utilization"] = (
                build_x1_bridge_to_xdex_utilization(
                    primary_result,
                    expected_request=expected_request,
                )
            )
        except X1BridgeToXdexContractError:
            pass

    if (
        primary_result.get("service") == "cross_chain_asset_provenance"
        and primary_result.get("status") == "ok"
    ):
        expected_request = {
            "evidence_sha256": request.get("provenance_evidence_sha256"),
            "current_asset_id": request.get("provenance_current_asset_id"),
            "current_asset_id_kind": request.get(
                "provenance_current_asset_id_kind"
            ),
        }
        try:
            report["x1_cross_chain_asset_provenance"] = (
                build_x1_cross_chain_provenance(
                    primary_result,
                    expected_request=expected_request,
                )
            )
        except X1CrossChainProvenanceContractError:
            pass

    compare_asset = request.get("compare_asset")
    if compare_asset is not None:
        report["requested_compare_asset"] = str(compare_asset)
    return {"report": report, "status": report_status}


def build_x1_scout_graph(cmis_client: CMISClient, planner_model: Any | None = None):
    builder = StateGraph(X1ScoutState)
    builder.add_node("propose_plan", make_plan_proposal_node(planner_model))
    builder.add_node("enforce_plan", enforce_plan_node)
    builder.add_node("cmis_calls", make_cmis_calls_node(cmis_client))
    builder.add_node("interpret", interpret_cmis_result)
    builder.add_edge(START, "propose_plan")
    builder.add_edge("propose_plan", "enforce_plan")
    builder.add_edge("enforce_plan", "cmis_calls")
    builder.add_edge("cmis_calls", "interpret")
    builder.add_edge("interpret", END)
    return builder.compile()
