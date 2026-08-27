"""Roberta-facing tool boundary for the X1 Scout specialist."""

import json
from typing import Any, Literal

from langchain_core.tools import BaseTool, StructuredTool

from roberta.cmis.client import CMISClient
from roberta.cmis.concentration_intelligence import normalize_intelligence_evidence_id
from roberta.cmis.contracts import TradeAction
from roberta.x1_scout.graph import build_x1_scout_graph
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
            "pre_trade_check",
            "concentration_change_intelligence",
        ] | None = None,
        action: TradeAction | None = None,
        amount_usd: float | None = None,
        intelligence_evidence_id: str | None = None,
        compare_asset: str | None = None,
    ) -> str:
        """Delegate an X1-specific investigation to X1 Scout.

        Ordinary read-only objectives may cover current market data, tokenomics,
        risk, XDEX rankings, and historical comparisons. For a global XDEX
        ranking with no single asset, use ``asset='XDEX'`` as the scope label.
        For a two-asset entire/full/lifetime-history comparison, copy the exact
        second user-supplied asset into ``compare_asset``.

        Pre-trade analysis and promoted concentration-change intelligence are
        explicit-request-only. Roberta must copy the exact user/trusted-context
        inputs and never invent a trade amount, side, or CMIS intelligence id.
        """

        request: dict[str, object] = {
            "asset": asset,
            "objective": objective,
        }
        if operation is None:
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
        elif operation == "pre_trade_check":
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
            "Delegate an X1-chain investigation to X1 Scout. Ordinary objectives cover "
            "current market data, tokenomics, deterministic risk, XDEX rankings, and "
            "historical comparisons. All-available history reports include a deterministic "
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
