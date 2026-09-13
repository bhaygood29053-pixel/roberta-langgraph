from __future__ import annotations

import json

from langchain_core.messages import HumanMessage, ToolMessage

from roberta.beta_product_proof import build_automatic_outcome
from roberta.evaluation_telemetry import (
    EVALUATION_TELEMETRY_V2,
    extend_evaluation_telemetry_v2,
)


RESPONSE_ID = "0123456789abcdef0123456789abcdef"
SENSITIVE_ASSET = "81LkybSBLvXYMTF6azXohUWyBvDGUXznm4yiXPKYkDTJ"


def _base_telemetry() -> dict[str, object]:
    return {
        "evaluation_telemetry_version": "roberta_evaluation_telemetry/v1",
        "evaluation_evidence": {},
        "claims": [],
        "evidence_freshness": {
            "state": "UNAVAILABLE",
            "source_ref": None,
            "source_value": None,
        },
        "evidence_provenance": {},
        "execution_authorized": False,
    }


def _asset_intelligence_report(*, packet_execution_authorized: bool = False):
    packet = {
        "contract_version": "x1_asset_intelligence/v1",
        "product": "x1_asset_intelligence",
        "chain": "x1",
        "requested_asset": SENSITIVE_ASSET,
        "status": "partial",
        "subject": {
            "symbol": "PEPE",
            "mint": SENSITIVE_ASSET,
        },
        "source_products": {
            "instant_x1_scan": {"must_not_persist": SENSITIVE_ASSET},
            "burn_intelligence": None,
            "discovery_intelligence": None,
        },
        "identity_bindings": {},
        "available_sections": ["instant_x1_scan"],
        "unbound_sections": [],
        "unavailable_sections": ["burn_intelligence", "discovery_intelligence"],
        "source_statuses": {
            "instant_x1_scan": "partial",
            "burn_intelligence": "unavailable",
            "discovery_intelligence": "unavailable",
        },
        "source_contracts": {
            "instant_x1_scan": "instant_x1_scan_product_view/v3",
            "burn_intelligence": None,
            "discovery_intelligence": None,
        },
        "evidence_completion": {
            "baseline_required": [
                "instant_x1_scan",
                "burn_intelligence",
                "discovery_intelligence",
            ],
            "baseline_attempted": [
                "instant_x1_scan",
                "burn_intelligence",
                "discovery_intelligence",
            ],
            "baseline_products_returned": ["instant_x1_scan"],
            "all_baseline_attempts_terminal": True,
            "requested_enrichments": [],
            "returned_enrichments": [],
            "all_requested_enrichments_returned": True,
            "decision_input_ready": True,
        },
        "limitations": [],
        "facts_authority": "chain_scout_cmis",
        "judgment_authority": "roberta",
        "read_only": True,
        "execution_authorized": packet_execution_authorized,
    }
    return {
        "contract_version": "x1_asset_intelligence_workflow/v1",
        "product_contract_version": "x1_asset_intelligence/v1",
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": SENSITIVE_ASSET,
        "objective": "investigate this exact X1 token",
        "source": {
            "service": "x1_scout",
            "operation": "asset_intelligence",
        },
        "scan_report": {},
        "burn_report": {},
        "discovery_report": {},
        "pretrade_report": None,
        "investigations": [],
        "evidence_context": {
            "available": True,
            "verification_status": "PARTIAL",
            "freshness_verified": False,
            "category_coverage_percent": 60.0,
        },
        "execution_authorized": False,
        "status": "complete",
        "asset_intelligence_packet": packet,
        "asset_intelligence_packet_text": "must not be used for telemetry claims",
        "findings": packet,
        "warnings": [],
        "errors": [],
    }


def _messages(report):
    return [
        HumanMessage(content="Investigate this exact X1 token."),
        ToolMessage(
            content=json.dumps(report),
            tool_call_id="cohort-c01",
            name="x1_scout_investigate",
        ),
    ]


def test_v2_projects_first_class_x1_asset_intelligence_packet():
    telemetry = extend_evaluation_telemetry_v2(
        _base_telemetry(),
        _messages(_asset_intelligence_report()),
    )

    assert telemetry["evaluation_telemetry_version"] == EVALUATION_TELEMETRY_V2
    factual = telemetry["evaluation_evidence"]["factual_response"]
    assert factual["specialist"] == "x1_scout"
    assert factual["chain"] == "x1"
    assert factual["source"] == {
        "service": "x1_scout",
        "operation": "asset_intelligence",
    }
    assert telemetry["evaluation_evidence"]["evaluation_projection_integrity"]["status"] == "PASS"
    assert telemetry["execution_authorized"] is False
    assert "x1_asset_intelligence/v1" in telemetry["evidence_provenance"]["source_contracts"]

    record = build_automatic_outcome(
        telemetry,
        duration_ms=10_000,
        response_id=RESPONSE_ID,
        timestamp="2026-09-12T20:59:12Z",
    )
    assert record["workflow"] == "x1_scout:asset_intelligence"
    assert record["outcome"] == "evidence_required"
    assert record["evidence_quality"] == "LOW"
    assert record["explicit_unknown_count"] == 3
    assert record["execution_authorized"] is False
    assert record["content_persisted"] is False

    encoded = json.dumps(record)
    assert SENSITIVE_ASSET not in encoded
    assert "PEPE" not in encoded
    assert "must_not_persist" not in encoded


def test_v2_rejects_asset_intelligence_packet_that_widens_execution_authority():
    telemetry = extend_evaluation_telemetry_v2(
        _base_telemetry(),
        _messages(_asset_intelligence_report(packet_execution_authorized=True)),
    )

    assert "factual_response" not in telemetry["evaluation_evidence"]
    record = build_automatic_outcome(
        telemetry,
        duration_ms=1_000,
        response_id=RESPONSE_ID,
    )
    assert record["workflow"] == "unknown"
    assert record["outcome"] == "unavailable"
    assert record["execution_authorized"] is False
    assert record["content_persisted"] is False
