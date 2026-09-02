from copy import deepcopy

import pytest

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.discovery_intelligence import (
    X1DiscoveryIntelligenceContractError,
    build_x1_discovery_intelligence,
)
from roberta.x1_scout.graph import build_x1_scout_graph


def test_scout_routes_discovery_through_cmis_without_launch_inference() -> None:
    client = MockCMISClient()
    report = build_x1_scout_graph(client).invoke(
        {"request": {"asset": "AGI", "objective": "discovery history", "operation": "discovery_intelligence"}}
    )["report"]
    product = report["x1_discovery_intelligence"]
    assert client.calls[-1]["operation"] == "discovery_intelligence"
    assert product["contract_version"] == "x1_discovery_intelligence/v1"
    assert product["discovery"]["verified_observation_count"] == 2
    assert product["discovery"]["token_launch_time"] is None
    assert product["execution_authorized"] is False


def test_adapter_rejects_first_observation_promoted_to_launch() -> None:
    result = MockCMISClient().discovery_intelligence(chain="x1", asset="AGI")
    weakened = deepcopy(result)
    weakened["data"]["token_launch_time"] = 100
    with pytest.raises(X1DiscoveryIntelligenceContractError):
        build_x1_discovery_intelligence(weakened)
