"""Roberta-facing tool boundary for the X1 Scout specialist."""

import json
from typing import Any, Literal

from langchain_core.tools import BaseTool, StructuredTool

from roberta.cmis.client import CMISClient
from roberta.cmis.concentration_intelligence import normalize_intelligence_evidence_id
from roberta.cmis.contracts import TradeAction
from roberta.x1_scout.compare_workflow import run_x1_compare_workflow
from roberta.x1_scout.graph import build_x1_scout_graph
from roberta.x1_scout.what_changed_workflow import run_x1_what_changed_workflow
from roberta.x1_scout.planner import is_all_available_history_objective


def build_x1_scout_tool(
    cmis_client: CMISClient,
    planner_model: Any | None = None,
) -> BaseTool:
    """Expose X1 Scout to Roberta without exposing CMIS directly."""
    scout_graph = build_x1_scout_graph(cmis_client, planner_model=planner_model)

    def investigate_x1(
        asset: str,
        objective: str = "assess market risk",
        operation: Literal[
            "compare",
            "what_changed",
            "instant_x1_scan",
            "discovery_intelligence",
            "pre_trade_check",
            "concentration_change_intelligence",
        ] | None = None,
        action: TradeAction | None = None,
        amount_usd: float | None = None,
        intelligence_evidence_id: str | None = None,
        compare_asset: str | None = None,
        include_history: bool = False,
    ) -> str:
        """Delegate an X1-specific investigation to X1 Scout.

        Ordinary read-only objectives may cover current market data, tokenomics,
        risk, XDEX rankings, and historical comparisons. A full/complete/
        comprehensive assessment deterministically requires all five dimensions
        and uses all available verified history. For a global XDEX
        ranking with no single asset, use ``asset='XDEX'`` as the scope label.
        For a two-asset entire/full/lifetime-history comparison, copy the exact
        second user-supplied asset into ``compare_asset``.

        Natural requests for an Instant X1 Scan or quick/instant asset scan route
        to the accepted CMIS composition service through X1 Scout. Roberta may
        also request operation='instant_x1_scan' explicitly without adding market
        facts or provider shortcuts.

        For a first-class two-asset X1 comparison, use operation='compare' and
        copy the exact second user/trusted-context asset into compare_asset.
        Set include_history=true only when the user explicitly asks for full/
        entire/lifetime pair history; the history path uses CMIS
        all_available_pair and never reconstructs pair history locally.

        Pre-trade analysis and promoted concentration-change intelligence are
        explicit-request-only. Roberta must copy the exact user/trusted-context
        inputs and never invent a trade amount, side, or CMIS intelligence id.
        """

        request: dict[str, object] = {
            "asset": asset,
            "objective": objective,
        }
        if operation is None:
            if include_history:
                raise ValueError(
                    "include_history requires operation='compare'"
                )
            if action is not None or amount_usd is not None or intelligence_evidence_id is not None:
                raise ValueError(
                    "action/amount_usd/intelligence_evidence_id require an explicit operation"
                )
            if compare_asset is not None:
                normalized_compare = str(compare_asset or "").strip()
                if not normalized_compare:
                    raise ValueError("compare_asset must not be empty")
                if normalized_compare.lower() == str(asset or "").strip().lower():
                    raise ValueError("compare_asset must differ from asset")
                if not is_all_available_history_objective(objective):
                    raise ValueError(
                        "compare_asset is accepted only for entire/full/lifetime-history comparisons"
                    )
                request["compare_asset"] = normalized_compare
        elif operation == "compare":
            normalized_compare = str(compare_asset or "").strip()
            if not normalized_compare:
                raise ValueError("compare requires compare_asset")
            if action is not None or amount_usd is not None:
                raise ValueError(
                    "trade action/amount are not accepted for compare"
                )
            if intelligence_evidence_id is not None:
                raise ValueError(
                    "intelligence_evidence_id is not accepted for compare"
                )
            if type(include_history) is not bool:
                raise ValueError("include_history must be boolean")
            if include_history and not is_all_available_history_objective(objective):
                raise ValueError(
                    "include_history requires an explicit full/entire/lifetime-history objective"
                )
            compare_report = run_x1_compare_workflow(
                cmis_client=cmis_client,
                scout_graph=scout_graph,
                left_asset=str(asset or "").strip(),
                right_asset=normalized_compare,
                objective=objective,
                include_history=include_history,
            )
            return json.dumps(compare_report, sort_keys=True)
        elif operation == "what_changed":
            if include_history:
                raise ValueError("include_history is not accepted for what_changed")
            if compare_asset is not None:
                raise ValueError("compare_asset is not accepted for what_changed")
            if action is not None or amount_usd is not None:
                raise ValueError("trade action/amount are not accepted for what_changed")
            if intelligence_evidence_id is not None:
                raise ValueError("intelligence_evidence_id is not accepted for what_changed")
            report = run_x1_what_changed_workflow(
                cmis_client=cmis_client,
                scout_graph=scout_graph,
                asset=str(asset or "").strip(),
                objective=objective,
            )
            return json.dumps(report, sort_keys=True)
        elif operation == "instant_x1_scan":
            if include_history:
                raise ValueError("include_history is accepted only for compare")
            if compare_asset is not None:
                raise ValueError("compare_asset is not accepted for instant_x1_scan")
            if action is not None or amount_usd is not None:
                raise ValueError(
                    "trade action/amount are not accepted for instant_x1_scan"
                )
            if intelligence_evidence_id is not None:
                raise ValueError(
                    "intelligence_evidence_id is not accepted for instant_x1_scan"
                )
            request["operation"] = "instant_x1_scan"
        elif operation == "discovery_intelligence":
            if include_history or compare_asset is not None:
                raise ValueError("history/compare inputs are not accepted for discovery_intelligence")
            if action is not None or amount_usd is not None or intelligence_evidence_id is not None:
                raise ValueError("trade and intelligence-evidence inputs are not accepted for discovery_intelligence")
            request["operation"] = "discovery_intelligence"
        elif operation == "pre_trade_check":
            if include_history:
                raise ValueError("include_history is accepted only for compare")
            if compare_asset is not None:
                raise ValueError("compare_asset is not accepted for pre_trade_check")
            if intelligence_evidence_id is not None:
                raise ValueError(
                    "intelligence_evidence_id is not accepted for pre_trade_check"
                )
            if action is None or amount_usd is None:
                raise ValueError(
                    "pre_trade_check requires the user-supplied action and amount_usd"
                )
            if isinstance(amount_usd, bool) or amount_usd <= 0:
                raise ValueError("amount_usd must be greater than zero")
            request.update(
                {
                    "operation": "pre_trade_check",
                    "action": action,
                    "amount_usd": amount_usd,
                }
            )
        elif operation == "concentration_change_intelligence":
            if include_history:
                raise ValueError("include_history is accepted only for compare")
            if compare_asset is not None:
                raise ValueError(
                    "compare_asset is not accepted for concentration intelligence"
                )
            if action is not None or amount_usd is not None:
                raise ValueError(
                    "trade action/amount are not accepted for concentration intelligence"
                )
            evidence_id = normalize_intelligence_evidence_id(intelligence_evidence_id)
            request.update(
                {
                    "operation": "concentration_change_intelligence",
                    "intelligence_evidence_id": evidence_id,
                }
            )
        else:  # pragma: no cover - StructuredTool schema is narrower than runtime input
            raise ValueError("Unsupported explicit X1 Scout operation")

        result = scout_graph.invoke(
            {
                "request": request,
                "status": "running",
            }
        )
        report = result.get("report")
        if report is None:
            raise RuntimeError("X1 Scout completed without returning a report.")
        return json.dumps(report, sort_keys=True)

    return StructuredTool.from_function(
        func=investigate_x1,
        name="x1_scout_investigate",
        description=(
            "Delegate an X1-chain investigation to X1 Scout. Natural Instant X1 Scan or "
            "quick/instant asset-scan requests use the accepted CMIS instant_x1_scan/v2 "
            "composition through X1 Scout; operation='instant_x1_scan' is also available "
            "for an explicit flagship scan request. For a first-class two-asset current "
            "comparison. For Discovery Intelligence, use operation='discovery_intelligence'; "
            "it preserves verified observation bounds and never treats first observation as launch. "
            "comparison, use operation='compare' with the exact second asset in compare_asset. "
            "For WHAT CHANGED?, use operation='what_changed'; X1 Scout composes one validated "
            "Instant X1 Scan, one Burn Intelligence result, and one Discovery Intelligence result "
            "without locally calculating market changes or inferring causality. "
            "set include_history=true only for explicit full/entire/lifetime pair-history "
            "requests. Compare obtains two validated Instant X1 Scans and, when requested, "
            "one CMIS all_available_pair result without local fact/history recomputation. "
            "Ordinary objectives cover current market "
            "data, tokenomics, deterministic risk, XDEX rankings, and historical comparisons. "
            "Full/complete/comprehensive assessment or due-diligence "
            "objectives deterministically gather market_report, rank, tokenomics, "
            "historical_compare using all available verified history, and risk_check. "
            "All-available history reports include a deterministic "
            "historical_coverage_presentation: when verified_history_available is true, "
            "do not describe overall historical coverage as zero; full lifetime or continuous "
            "coverage may be claimed only when the corresponding CMIS flags are true. "
            "For a two-asset entire/full/lifetime-history comparison, copy the exact second "
            "asset into compare_asset so X1 Scout can issue one CMIS all_available_pair request. "
            "For an explicit user "
            "pre-trade question, use "
            "operation='pre_trade_check' and copy the exact BUY/SELL action and USD "
            "amount. For the promoted CMIS concentration-change intelligence service, "
            "use operation='concentration_change_intelligence' only when an exact "
            "CMIS-owned ie_ content id is present in the user request or trusted current "
            "context; copy it into intelligence_evidence_id and never invent one. "
            "X1 Scout obtains structured facts through CMIS only and never authorizes "
            "execution or adds whale/insider/bot/intent/ownership labels."
        ),
    )
