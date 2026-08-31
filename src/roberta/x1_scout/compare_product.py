"""Deterministic X1 Compare product contract.

This module aligns two already-validated Instant X1 Scan product views and,
optionally, one CMIS all_available_pair historical result. It does not fetch
providers, recompute CMIS facts, create a combined risk score, average proof
quality, or infer missing holder/concentration data.
"""

from __future__ import annotations

from collections.abc import Mapping
import math
from numbers import Real
from typing import Any

from roberta.x1_scout.instant_scan_product_ux import PRODUCT_VIEW_CONTRACT


X1_COMPARE_CONTRACT = "x1_compare/v1"


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _numeric(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    if isinstance(value, int):
        # Python integers are finite and arbitrary precision; converting a very
        # large integer to float can overflow.
        return True
    if isinstance(value, float):
        return math.isfinite(value)
    try:
        return math.isfinite(value)
    except (TypeError, ValueError, OverflowError):
        return False


def _verified_relation(left: object, right: object) -> dict[str, object]:
    left_item = _mapping(left)
    right_item = _mapping(right)
    left_value = left_item.get("value")
    right_value = right_item.get("value")
    comparable = (
        left_item.get("verified") is True
        and right_item.get("verified") is True
        and _numeric(left_value)
        and _numeric(right_value)
    )
    relation = "not_comparable"
    if comparable:
        if left_value > right_value:
            relation = "left_higher"
        elif left_value < right_value:
            relation = "right_higher"
        else:
            relation = "equal"
    return {
        "left": dict(left_item),
        "right": dict(right_item),
        "comparable": comparable,
        "relation": relation,
    }


def _holder_relation(
    left_holder: Mapping[str, Any],
    right_holder: Mapping[str, Any],
) -> dict[str, object]:
    left_semantics = left_holder.get("holder_semantics")
    right_semantics = right_holder.get("holder_semantics")
    result = _verified_relation(
        left_holder.get("holders"),
        right_holder.get("holders"),
    )
    semantics_match = (
        isinstance(left_semantics, Mapping)
        and isinstance(right_semantics, Mapping)
        and dict(left_semantics) == dict(right_semantics)
    )
    if not semantics_match:
        result["comparable"] = False
        result["relation"] = "not_comparable"
    result["semantics_match"] = semantics_match
    return result


def _validate_scan_product_view(
    view: Mapping[str, Any],
    *,
    side: str,
) -> None:
    if view.get("contract_version") != PRODUCT_VIEW_CONTRACT:
        raise ValueError(f"{side} comparison input is not an accepted Instant X1 Scan view")
    if view.get("product") != "instant_x1_scan" or view.get("chain") != "x1":
        raise ValueError(f"{side} comparison input must remain an X1 Instant X1 Scan")
    if view.get("execution_authorized") is not False:
        raise ValueError(f"{side} comparison input must preserve execution_authorized=false")


_BASE58_CHARS = frozenset(
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
)


def _looks_like_x1_mint(value: object) -> bool:
    text = str(value or "").strip()
    return bool(
        32 <= len(text) <= 44
        and all(char in _BASE58_CHARS for char in text)
    )


def _same_identity_text(left: object, right: object) -> bool:
    left_text = str(left or "").strip()
    right_text = str(right or "").strip()
    if not left_text or not right_text:
        return False
    if _looks_like_x1_mint(left_text) or _looks_like_x1_mint(right_text):
        return left_text == right_text
    return left_text.casefold() == right_text.casefold()


def _verified_mint(view: Mapping[str, Any]) -> str | None:
    identity = _mapping(view.get("identity"))
    if identity.get("verified") is not True:
        return None
    mint = str(identity.get("mint") or "").strip()
    return mint or None


def _same_verified_asset(
    left_scan: Mapping[str, Any],
    right_scan: Mapping[str, Any],
) -> bool:
    left_mint = _verified_mint(left_scan)
    right_mint = _verified_mint(right_scan)
    return (
        left_mint is not None
        and right_mint is not None
        and _same_identity_text(left_mint, right_mint)
    )


def _scan_matches_requested_asset(
    scan: Mapping[str, Any],
    *,
    requested_asset: str,
) -> bool:
    scan_request = str(scan.get("requested_asset") or "").strip()
    if scan_request:
        if not _same_identity_text(scan_request, requested_asset):
            return False

    identity = _mapping(scan.get("identity"))
    verified_mint = _verified_mint(scan)
    if _looks_like_x1_mint(requested_asset):
        return (
            verified_mint is not None
            and _same_identity_text(verified_mint, requested_asset)
        )

    # For symbol/name requests, the scan's own requested_asset is the strongest
    # orientation binding because CMIS owns alias->mint resolution. Older
    # product views may lack it, so fall back to verified identity descriptors.
    if scan_request:
        return True
    return any(
        _same_identity_text(identity.get(key), requested_asset)
        for key in ("symbol", "name", "mint")
    )


def _history_identity_matches_scan(
    history_asset: object,
    *,
    requested_asset: str,
    scan: Mapping[str, Any],
) -> bool:
    if not isinstance(history_asset, Mapping):
        return False

    history_mint = str(history_asset.get("mint") or "").strip()
    verified_mint = _verified_mint(scan)
    if history_mint and verified_mint:
        return _same_identity_text(history_mint, verified_mint)

    identity = _mapping(scan.get("identity"))
    observed = [
        history_asset.get("symbol"),
        history_asset.get("name"),
        history_asset.get("mint"),
    ]
    expected = [
        requested_asset,
        scan.get("requested_asset"),
        identity.get("symbol"),
        identity.get("name"),
        identity.get("mint"),
    ]
    return any(
        _same_identity_text(observed_value, expected_value)
        for observed_value in observed
        for expected_value in expected
    )


def _pair_history_projection(
    result: Mapping[str, Any] | None,
    *,
    left_requested_asset: str,
    right_requested_asset: str,
    left_scan: Mapping[str, Any],
    right_scan: Mapping[str, Any],
) -> dict[str, object] | None:
    if result is None:
        return None
    if result.get("service") != "historical_compare" or result.get("chain") != "x1":
        raise ValueError("Compare pair history must be an X1 CMIS historical_compare result")

    status = result.get("status")
    if status not in {"ok", "partial", "unavailable", "ambiguous", "error"}:
        raise ValueError("Compare pair history returned an unsupported CMIS status")

    data = result.get("data")
    if not isinstance(data, Mapping):
        raise ValueError("Compare pair history data must be an object")
    mode = data.get("mode")
    if mode is not None and mode != "all_available_pair":
        raise ValueError("Compare pair history must use CMIS all_available_pair mode")

    if status in {"ok", "partial"}:
        if mode != "all_available_pair":
            raise ValueError("Compare pair history must use CMIS all_available_pair mode")

        primary_asset = (
            data.get("asset")
            if isinstance(data.get("asset"), Mapping)
            else result.get("asset")
        )
        if not _history_identity_matches_scan(
            primary_asset,
            requested_asset=left_requested_asset,
            scan=left_scan,
        ):
            raise ValueError(
                "Compare pair history primary asset does not match the left comparison asset"
            )

        secondary_asset = data.get("compare_asset")
        if isinstance(secondary_asset, Mapping):
            secondary_matches = _history_identity_matches_scan(
                secondary_asset,
                requested_asset=right_requested_asset,
                scan=right_scan,
            )
        else:
            compare_request = data.get("compare_asset_request")
            secondary_matches = _same_identity_text(
                compare_request,
                right_requested_asset,
            )
        if not secondary_matches:
            raise ValueError(
                "Compare pair history secondary asset does not match the right comparison asset"
            )

        envelope_asset = result.get("asset")
        if isinstance(envelope_asset, Mapping) and not _history_identity_matches_scan(
            envelope_asset,
            requested_asset=left_requested_asset,
            scan=left_scan,
        ):
            raise ValueError(
                "Compare pair history envelope asset does not match the left comparison asset"
            )

    return {
        "asset": (
            dict(result["asset"])
            if isinstance(result.get("asset"), Mapping)
            else None
        ),
        "status": status,
        "data": dict(data),
        "confidence": dict(_mapping(result.get("confidence"))),
        "sources": list(result.get("sources") or []),
        "observed_at": result.get("observed_at"),
        "warnings": list(result.get("warnings") or []),
        "errors": list(result.get("errors") or []),
        "evidence_receipt": (
            dict(result["evidence_receipt"])
            if isinstance(result.get("evidence_receipt"), Mapping)
            else None
        ),
        "proof_score": (
            dict(result["proof_score"])
            if isinstance(result.get("proof_score"), Mapping)
            else None
        ),
    }


def build_x1_compare_product_view(
    *,
    left_requested_asset: str,
    right_requested_asset: str,
    left_scan: Mapping[str, Any],
    right_scan: Mapping[str, Any],
    pair_history: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    """Build a two-asset comparison without synthesizing unavailable facts."""

    left_requested = str(left_requested_asset or "").strip()
    right_requested = str(right_requested_asset or "").strip()
    if not left_requested or not right_requested:
        raise ValueError("X1 Compare requires two explicit requested assets")
    if _same_identity_text(left_requested, right_requested):
        raise ValueError("X1 Compare requires two distinct requested assets")

    _validate_scan_product_view(left_scan, side="left")
    _validate_scan_product_view(right_scan, side="right")
    if not _scan_matches_requested_asset(
        left_scan,
        requested_asset=left_requested,
    ):
        raise ValueError(
            "left Instant X1 Scan does not match the left requested asset"
        )
    if not _scan_matches_requested_asset(
        right_scan,
        requested_asset=right_requested,
    ):
        raise ValueError(
            "right Instant X1 Scan does not match the right requested asset"
        )
    if _same_verified_asset(left_scan, right_scan):
        raise ValueError(
            "X1 Compare inputs resolve to the same verified asset mint"
        )

    left_market = _mapping(left_scan.get("market"))
    right_market = _mapping(right_scan.get("market"))
    left_holders = _mapping(left_scan.get("holder_concentration"))
    right_holders = _mapping(right_scan.get("holder_concentration"))

    return {
        "contract_version": X1_COMPARE_CONTRACT,
        "product": "x1_compare",
        "chain": "x1",
        "requested_assets": {
            "left": left_requested,
            "right": right_requested,
        },
        "left": dict(left_scan),
        "right": dict(right_scan),
        "comparison": {
            "price_usd": _verified_relation(
                left_market.get("price_usd"),
                right_market.get("price_usd"),
            ),
            "liquidity_usd": _verified_relation(
                left_market.get("liquidity_usd"),
                right_market.get("liquidity_usd"),
            ),
            "volume_24h_usd": _verified_relation(
                left_market.get("volume_24h_usd"),
                right_market.get("volume_24h_usd"),
            ),
            "transactions_24h": _verified_relation(
                left_market.get("transactions_24h"),
                right_market.get("transactions_24h"),
            ),
            "holders": _holder_relation(left_holders, right_holders),
        },
        "risk": {
            "left": dict(_mapping(left_scan.get("risk"))),
            "right": dict(_mapping(right_scan.get("risk"))),
            "combined_score": None,
            "combined_recommendation": None,
        },
        "evidence": {
            "left": dict(_mapping(left_scan.get("evidence"))),
            "right": dict(_mapping(right_scan.get("evidence"))),
            "combined_proof_score": None,
            "proof_score_separate_from_risk": True,
        },
        "pair_history": _pair_history_projection(
            pair_history,
            left_requested_asset=left_requested,
            right_requested_asset=right_requested,
            left_scan=left_scan,
            right_scan=right_scan,
        ),
        "execution_authorized": False,
    }


def _relation_text(label: str, comparison: object) -> str:
    item = _mapping(comparison)
    relation = item.get("relation")
    if item.get("comparable") is not True:
        return f"{label}: not comparable from verified evidence"
    if relation == "left_higher":
        return f"{label}: left higher"
    if relation == "right_higher":
        return f"{label}: right higher"
    return f"{label}: equal"


def render_x1_compare_product_text(view: Mapping[str, Any]) -> str:
    """Render a compact comparison while preserving unknown/non-comparable state."""

    if view.get("contract_version") != X1_COMPARE_CONTRACT:
        raise ValueError("unsupported X1 Compare product contract")
    if view.get("execution_authorized") is not False:
        raise ValueError("X1 Compare must preserve execution_authorized=false")

    requested = _mapping(view.get("requested_assets"))
    comparison = _mapping(view.get("comparison"))
    left = _mapping(view.get("left"))
    right = _mapping(view.get("right"))
    left_risk = _mapping(_mapping(view.get("risk")).get("left"))
    right_risk = _mapping(_mapping(view.get("risk")).get("right"))
    pair_history = view.get("pair_history")

    lines = [
        f"X1 Compare — {requested.get('left')} vs {requested.get('right')}",
        f"Left status: {left.get('status') or 'unknown'}",
        f"Right status: {right.get('status') or 'unknown'}",
        "",
        "Verified comparisons",
        _relation_text("Price USD", comparison.get("price_usd")),
        _relation_text("Liquidity USD", comparison.get("liquidity_usd")),
        _relation_text("24h Volume USD", comparison.get("volume_24h_usd")),
        _relation_text("24h Transactions", comparison.get("transactions_24h")),
        _relation_text("Holders", comparison.get("holders")),
        "",
        "Risk (kept separate)",
        f"Left: {left_risk.get('recommendation') or 'unknown'}",
        f"Right: {right_risk.get('recommendation') or 'unknown'}",
        "Combined risk: not calculated",
        "",
        "Evidence",
        "Proof scores remain separate per asset and separate from risk.",
    ]

    if isinstance(pair_history, Mapping):
        lines.extend(
            [
                "",
                "Pair history",
                f"CMIS status: {pair_history.get('status') or 'unknown'}",
                "History calculations: CMIS all_available_pair only",
            ]
        )
    return "\n".join(lines)


__all__ = [
    "X1_COMPARE_CONTRACT",
    "build_x1_compare_product_view",
    "render_x1_compare_product_text",
]
