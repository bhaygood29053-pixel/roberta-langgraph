"""Deterministic presentation projection for CMIS historical coverage.

This module never creates market facts. It projects CMIS-supplied coverage
fields into a compact presentation contract so downstream Roberta synthesis
does not collapse missing or partial history into a fabricated zero-history
claim.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _positive_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return parsed if parsed > 0 else 0


def _metric_observation_count(profile: Mapping[str, Any], metric: str) -> int:
    metrics = _mapping(profile.get("metrics"))
    record = _mapping(metrics.get(metric))
    return _positive_int(record.get("observation_count"))


def _market_history_available(profile: Mapping[str, Any]) -> bool:
    if _positive_int(profile.get("available_metric_count")) > 0:
        return True
    if profile.get("first_verified_observed_at") is not None:
        return True
    if profile.get("last_verified_observed_at") is not None:
        return True
    if profile.get("provider_history_imported") is True:
        return True

    metrics = _mapping(profile.get("metrics"))
    for record in metrics.values():
        if isinstance(record, Mapping) and _positive_int(
            record.get("observation_count")
        ) > 0:
            return True
    return False


def _onchain_history_available(coverage: Mapping[str, Any]) -> bool:
    status = str(coverage.get("status") or "").strip().lower()
    if status not in {"full", "partial", "ok"}:
        return False
    if coverage.get("rpc_visible_mint_history_complete") is True:
        return True
    if _positive_int(coverage.get("signatures_scanned")) > 0:
        return True
    for field in (
        "oldest_verified_slot",
        "newest_verified_slot",
        "oldest_verified_time",
        "newest_verified_time",
    ):
        if coverage.get(field) is not None:
            return True
    return False


def _market_projection(
    profile: Mapping[str, Any],
    market_coverage: Mapping[str, Any],
) -> dict[str, object]:
    provider = _mapping(
        profile.get("provider_price_history")
        or market_coverage.get("provider_price_history")
    )
    return {
        "status": (
            market_coverage.get("status")
            if market_coverage
            else profile.get("status")
        ),
        "history_available": _market_history_available(profile),
        "first_verified_observed_at": (
            market_coverage.get("first_verified_observed_at")
            if market_coverage.get("first_verified_observed_at") is not None
            else profile.get("first_verified_observed_at")
        ),
        "last_verified_observed_at": (
            market_coverage.get("last_verified_observed_at")
            if market_coverage.get("last_verified_observed_at") is not None
            else profile.get("last_verified_observed_at")
        ),
        "coverage_seconds": (
            market_coverage.get("coverage_seconds")
            if market_coverage.get("coverage_seconds") is not None
            else profile.get("coverage_seconds")
        ),
        "available_metric_count": _positive_int(
            profile.get("available_metric_count")
        ),
        "multi_point_metric_count": _positive_int(
            profile.get("multi_point_metric_count")
        ),
        "price_observation_count": _metric_observation_count(profile, "price"),
        "provider_history_imported": (
            profile.get("provider_history_imported") is True
            or market_coverage.get("provider_history_imported") is True
        ),
        "provider_price_history": dict(provider) if provider else None,
        "full_asset_lifetime_verified": (
            profile.get("full_asset_lifetime_verified") is True
        ),
        "continuous_coverage_verified": (
            profile.get("continuous_coverage_verified") is True
        ),
    }


def _onchain_projection(coverage: Mapping[str, Any]) -> dict[str, object]:
    return {
        "status": coverage.get("status"),
        "history_available": _onchain_history_available(coverage),
        "coverage_scope": coverage.get("coverage_scope"),
        "first_available_block": coverage.get("first_available_block"),
        "oldest_verified_slot": coverage.get("oldest_verified_slot"),
        "newest_verified_slot": coverage.get("newest_verified_slot"),
        "oldest_verified_time": coverage.get("oldest_verified_time"),
        "newest_verified_time": coverage.get("newest_verified_time"),
        "signatures_scanned": coverage.get("signatures_scanned"),
        "rpc_visible_mint_history_complete": (
            coverage.get("rpc_visible_mint_history_complete") is True
        ),
        "asset_wide_activity_verified": (
            coverage.get("asset_wide_activity_verified") is True
        ),
        "archival_completeness_verified": (
            coverage.get("archival_completeness_verified") is True
        ),
        "full_asset_lifetime_verified": (
            coverage.get("full_asset_lifetime_verified") is True
        ),
    }


def build_historical_coverage_presentation(
    result: Any,
) -> dict[str, object] | None:
    """Project accepted CMIS all-available coverage into presentation metadata."""

    if not isinstance(result, Mapping):
        return None
    if result.get("service") != "historical_compare":
        return None

    data = _mapping(result.get("data"))
    mode = str(data.get("mode") or "").strip().lower()
    if mode not in {"all_available", "all_available_pair"}:
        return None

    if mode == "all_available_pair":
        primary = _mapping(data.get("primary_profile"))
        secondary = _mapping(data.get("secondary_profile"))
        primary_available = _market_history_available(primary)
        secondary_available = _market_history_available(secondary)
        comparable = _positive_int(data.get("comparable_metric_count")) > 0
        verified_history_available = (
            primary_available or secondary_available or comparable
        )
        return {
            "mode": mode,
            "interpretation": (
                "verified_pair_history_available"
                if verified_history_available
                else "verified_pair_history_unavailable_or_unproven"
            ),
            "verified_history_available": verified_history_available,
            "must_not_describe_missing_history_as_zero": True,
            "full_asset_lifetime_verified": (
                data.get("full_asset_lifetime_verified") is True
            ),
            "continuous_coverage_verified": (
                data.get("continuous_coverage_verified") is True
            ),
            "primary_market_history_available": primary_available,
            "secondary_market_history_available": secondary_available,
            "common_verified_history_comparable": comparable,
            "comparable_metric_count": _positive_int(
                data.get("comparable_metric_count")
            ),
        }

    coverage = _mapping(data.get("coverage"))
    market_coverage = _mapping(coverage.get("market"))
    onchain_coverage = _mapping(coverage.get("onchain"))
    market = _market_projection(data, market_coverage)
    onchain = _onchain_projection(onchain_coverage)
    verified_history_available = (
        market["history_available"] is True
        or onchain["history_available"] is True
    )
    full_lifetime = data.get("full_asset_lifetime_verified") is True
    if full_lifetime:
        interpretation = "verified_complete_lifetime_history"
    elif verified_history_available:
        interpretation = "verified_partial_history"
    else:
        interpretation = "verified_history_unavailable_or_unproven"

    return {
        "mode": mode,
        "interpretation": interpretation,
        "verified_history_available": verified_history_available,
        "must_not_describe_missing_history_as_zero": True,
        "full_asset_lifetime_verified": full_lifetime,
        "continuous_coverage_verified": (
            data.get("continuous_coverage_verified") is True
        ),
        "market": market,
        "onchain": onchain,
    }


__all__ = ["build_historical_coverage_presentation"]
