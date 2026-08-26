from __future__ import annotations

from roberta.learning.dashboard_option_a import apply_option_a_layout


def test_option_a_layout_adds_command_center_without_inventing_live_cmis_metrics() -> None:
    html = """<!doctype html><html><head><style>.card{}</style></head><body><main>
<header><div><h1>Learning Command Center</h1><div class="subtitle">Blockchain Reasoning Pyramid • Training Ledger • Diagnostics</div></div></header>
<section class="health"></section>
<section class="metrics"></section>
<section class="grid"><article class="card"><h2>20-Level Pyramid</h2><div id="pyramid" class="pyramid"></div></article></section>
<div>/api/summary</div>
</main><script></script></body></html>"""
    data = {
        "failure_event_total": 3,
        "latest_run": {"status": "active"},
        "source_mastery": {"available": True},
    }
    services = {"roberta": {"status": "online", "detail": "ok"}}

    rendered = apply_option_a_layout(html, data, services)

    assert "Coordinated Intelligence for Smarter Decisions" in rendered
    assert "Authority Flow" in rendered
    assert "Verified Information Flow" in rendered
    assert "X1 SCOUT" in rendered
    assert "SOLANA SCOUT" in rendered
    assert "CMIS Services (7)" in rendered
    assert "asset_lookup" in rendered
    assert "pre_trade_check" in rendered
    assert "CMIS PROVIDER HEALTH" in rendered
    assert "NOT CONNECTED" in rendered
    assert "3 recorded learning failure event(s)" in rendered
    assert "OPTION A" in rendered
    assert "option-a-roberta-avatar" in rendered
    assert "/api/summary" in rendered
    assert "Provider Health 100%" not in rendered
    assert "DATA FRESHNESS</span><strong>12s" not in rendered


def test_option_a_layout_preserves_unknown_source_truthfully() -> None:
    html = """<html><head><style></style></head><body><main><header></header>
<section class="health"></section><section class="metrics"></section><section class="grid"></section>
</main><script></script></body></html>"""
    data = {
        "failure_event_total": 0,
        "latest_run": None,
        "source_mastery": {"available": False},
    }

    rendered = apply_option_a_layout(html, data, {"roberta": {"status": "offline"}})

    assert "Source mastery metadata is unavailable" in rendered
    assert "Roberta bridge is offline" in rendered
    assert "CMIS provider telemetry" in rendered
    assert "NOT CONNECTED" in rendered
