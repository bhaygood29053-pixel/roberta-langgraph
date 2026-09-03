import copy

import pytest

from roberta.cmis.capabilities import (
    CMISCapabilityContractError,
    INSTANT_X1_SCAN_CONTRACT_VERSION,
    INSTANT_X1_SCAN_MIN_CMIS_CONTRACT_VERSION,
    require_instant_x1_scan_capability,
)
from roberta.cmis.instant_scan import validate_instant_x1_scan_response
from roberta.cmis.mock import MockCMISClient


def test_cmis_117_scan_v3_capability_and_payload_are_accepted():
    client = MockCMISClient()
    manifest = client.capabilities()

    capability = require_instant_x1_scan_capability(manifest)
    assert INSTANT_X1_SCAN_MIN_CMIS_CONTRACT_VERSION == "1.17.0"
    assert INSTANT_X1_SCAN_CONTRACT_VERSION == "instant_x1_scan/v3"
    assert capability["service_contract_version"] == "instant_x1_scan/v3"

    response = validate_instant_x1_scan_response(
        client.instant_x1_scan(chain="x1", asset="XNT")
    )
    history = response["data"]["sections"]["history"]
    assert history["provider_history_imported"] is True
    assert history["provider_history_backfill"]["status"] == "partial"
    assert history["coverage"]["onchain"]["status"] == "not_requested"
    assert history["full_asset_lifetime_verified"] is False
    assert history["continuous_coverage_verified"] is False
    market = response["data"]["sections"]["market"]
    freshness = market["freshness"]
    assert freshness["contract_version"] == "x1_current_market_freshness/v1"
    assert freshness["freshness_state"] == "NOT_VERIFIED"
    assert freshness["verified_field_count"] == 0
    assert market["price_freshness_verified"] is False
    assert market["liquidity_freshness_verified"] is False
    assert market["volume_24h_freshness_verified"] is False
    assert market["transactions_24h_freshness_verified"] is False
    assert response["data"]["execution_authorized"] is False


def test_scan_v3_capability_fails_closed_on_cmis_113():
    manifest = MockCMISClient().capabilities()
    stale = copy.deepcopy(manifest)
    stale["contract_version"] = "1.16.0"

    with pytest.raises(CMISCapabilityContractError):
        require_instant_x1_scan_capability(stale)


def test_scan_v3_rejects_lifetime_or_continuity_promotion():
    client = MockCMISClient()
    response = client.instant_x1_scan(chain="x1", asset="XNT")

    promoted = copy.deepcopy(response)
    promoted["data"]["sections"]["history"]["full_asset_lifetime_verified"] = True
    with pytest.raises(Exception, match="full asset lifetime"):
        validate_instant_x1_scan_response(promoted)

    promoted = copy.deepcopy(response)
    promoted["data"]["sections"]["history"]["continuous_coverage_verified"] = True
    with pytest.raises(Exception, match="continuous historical coverage"):
        validate_instant_x1_scan_response(promoted)


def test_scan_v3_accepts_verified_pair_lifetime_without_usd_promotion():
    client = MockCMISClient()
    response = client.instant_x1_scan(chain="x1", asset="XNT")
    promoted = copy.deepcopy(response)

    history = promoted["data"]["sections"]["history"]
    history.update(
        {
            "price_coverage_scope": "full_supported_pair_lifetime",
            "full_supported_pair_lifetime_verified": True,
            "continuous_pair_price_coverage_verified": True,
            "provider_range_complete_verified": True,
            "historical_quote_usd_equivalence_verified": False,
            "full_usd_lifetime_verified": False,
            "full_asset_lifetime_verified": False,
            "continuous_coverage_verified": False,
        }
    )
    limitations = promoted["data"]["limitations"]
    for item in (
        "provider_archive_completeness_not_verified",
        "history_does_not_imply_complete_asset_lifetime",
        "continuous_coverage_requires_separate_archive_completeness_proof",
    ):
        if item in limitations:
            limitations.remove(item)
    limitations.extend(
        [
            "full_supported_pair_lifetime_price_does_not_imply_other_metric_lifetimes",
            "historical_quote_usd_equivalence_not_verified",
        ]
    )

    accepted = validate_instant_x1_scan_response(promoted)
    accepted_history = accepted["data"]["sections"]["history"]
    assert accepted_history["full_supported_pair_lifetime_verified"] is True
    assert accepted_history["continuous_pair_price_coverage_verified"] is True
    assert accepted_history["provider_range_complete_verified"] is True
    assert accepted_history["historical_quote_usd_equivalence_verified"] is False
    assert accepted_history["full_usd_lifetime_verified"] is False
    assert accepted_history["full_asset_lifetime_verified"] is False


def test_scan_v3_rejects_inconsistent_pair_lifetime_promotion():
    client = MockCMISClient()
    response = client.instant_x1_scan(chain="x1", asset="XNT")
    promoted = copy.deepcopy(response)
    history = promoted["data"]["sections"]["history"]
    history.update(
        {
            "price_coverage_scope": "full_supported_pair_lifetime",
            "full_supported_pair_lifetime_verified": True,
            "continuous_pair_price_coverage_verified": False,
            "provider_range_complete_verified": True,
            "historical_quote_usd_equivalence_verified": False,
            "full_usd_lifetime_verified": False,
        }
    )

    with pytest.raises(Exception, match="pair continuity"):
        validate_instant_x1_scan_response(promoted)


def test_scan_v3_accepts_price_only_partial_freshness_and_rejects_global_promotion():
    response = MockCMISClient().instant_x1_scan(chain="x1", asset="XNT")
    market = response["data"]["sections"]["market"]
    freshness = market["freshness"]
    freshness.update(
        {
            "freshness_state": "PARTIAL",
            "collection_freshness_verified": True,
            "provider_price_fact_time_verified": True,
            "current_market_freshness_verified": False,
            "verified_field_count": 1,
        }
    )
    freshness["fields"]["price_usd"]["freshness_verified"] = True
    freshness["fields"]["price_usd"]["reason"] = (
        "timestamped_provider_price_matches_current_market_price"
    )
    market["price_freshness_verified"] = True

    accepted = validate_instant_x1_scan_response(response)
    accepted_market = accepted["data"]["sections"]["market"]
    assert accepted_market["freshness"]["freshness_state"] == "PARTIAL"
    assert accepted_market["price_freshness_verified"] is True
    assert accepted_market["liquidity_freshness_verified"] is False

    promoted = copy.deepcopy(response)
    promoted_market = promoted["data"]["sections"]["market"]
    promoted_freshness = promoted_market["freshness"]
    promoted_freshness["fields"]["liquidity_usd"]["freshness_verified"] = True
    promoted_freshness["fields"]["liquidity_usd"]["reason"] = "unexpected_promotion"
    promoted_freshness["verified_field_count"] = 2
    promoted_market["liquidity_freshness_verified"] = True

    with pytest.raises(Exception, match="must not promote liquidity"):
        validate_instant_x1_scan_response(promoted)
