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


def test_cmis_114_scan_v2_capability_and_payload_are_accepted():
    client = MockCMISClient()
    manifest = client.capabilities()

    capability = require_instant_x1_scan_capability(manifest)
    assert INSTANT_X1_SCAN_MIN_CMIS_CONTRACT_VERSION == "1.14.0"
    assert INSTANT_X1_SCAN_CONTRACT_VERSION == "instant_x1_scan/v2"
    assert capability["service_contract_version"] == "instant_x1_scan/v2"

    response = validate_instant_x1_scan_response(
        client.instant_x1_scan(chain="x1", asset="XNT")
    )
    history = response["data"]["sections"]["history"]
    assert history["provider_history_imported"] is True
    assert history["provider_history_backfill"]["status"] == "partial"
    assert history["coverage"]["onchain"]["status"] == "not_requested"
    assert history["full_asset_lifetime_verified"] is False
    assert history["continuous_coverage_verified"] is False
    assert response["data"]["execution_authorized"] is False


def test_scan_v2_capability_fails_closed_on_cmis_113():
    manifest = MockCMISClient().capabilities()
    stale = copy.deepcopy(manifest)
    stale["contract_version"] = "1.13.0"

    with pytest.raises(CMISCapabilityContractError):
        require_instant_x1_scan_capability(stale)


def test_scan_v2_rejects_lifetime_or_continuity_promotion():
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
