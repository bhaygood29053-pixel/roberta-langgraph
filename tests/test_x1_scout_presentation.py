"""Integration tests for X1 Scout presentation metadata."""

from roberta.cmis.mock import MockCMISClient
from roberta.x1_scout.graph import build_x1_scout_graph


def test_x1_scout_attaches_status_time_and_component_presentation() -> None:
    cmis = MockCMISClient(observed_at="2026-08-15T23:37:12.909297Z")
    scout = build_x1_scout_graph(cmis)

    result = scout.invoke(
        {
            "request": {
                "asset": "AGI",
                "objective": "assess market risk",
            },
            "status": "running",
        }
    )

    report = result["report"]
    assert report["observed_at"] == "2026-08-15T23:37:12.909297Z"
    assert report["observed_at_iso"] == "2026-08-15T23:37:12.909297Z"
    assert report["observed_at_display"] == "2026-08-15 | 23:37:12 UTC"
    assert report["cmis_status"] == "partial"
    assert report["cmis_status_help"]["status"] == "partial"
    assert "verification checks are incomplete" in report["cmis_status_help"]["meaning"]
    assert report["component_status_table"] is None
