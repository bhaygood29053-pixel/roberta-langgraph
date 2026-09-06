import copy

import pytest

from roberta.human_response_renderer import (
    HUMAN_RESPONSE_DECISION_CONTRACT,
    HumanResponseRenderError,
    build_public_human_response_contract,
    render_human_response,
)


def _observation(
    fact_ref,
    interpretation,
    *,
    source_value=None,
    verification_state="VERIFIED",
    economic_assessment=None,
):
    item = {
        "fact_ref": fact_ref,
        "source_value": source_value,
        "verification_state": verification_state,
        "interpretation": interpretation,
        "source_authority": "chain_scout_cmis",
    }
    if economic_assessment is not None:
        item["economic_assessment"] = economic_assessment
    return item


def _response_decision(recommendation="AVOID", depth="normal"):
    return {
        "contract_version": HUMAN_RESPONSE_DECISION_CONTRACT,
        "source_decision_contract": "roberta_decision/v1",
        "source_opinion_contract": "roberta_opinion/v1",
        "workflow": "instant_x1_scan",
        "subject": {
            "symbol": "X1X",
            "mint": "7z2PR1111111111111111111111111111111111N46",
        },
        "response_depth": depth,
        "response_depth_eligibility": ["quick", "normal", "deep_dive"],
        "recommendation": recommendation,
        "recommendation_family": "avoidance",
        "conviction": "MODERATE",
        "evidence_quality": "LOW",
        "primary_decision_driver": _observation(
            "facts.market.liquidity_usd",
            "Only about $13 of liquidity is verified.",
            source_value={"value": 12.81, "verified": True},
            economic_assessment=(
                "Extremely thin and economically inadequate for meaningful trading"
            ),
        ),
        "supporting_evidence": [
            _observation(
                "facts.market.volume_24h_usd",
                "Verified measured 24h volume is zero.",
                source_value={"value": 0.0, "verified": True},
            ),
            _observation(
                "facts.tokenomics.mint_authority",
                "The mint authority is still active.",
                source_value={
                    "value": "MintAuthority111111111111111111111111111",
                    "verified": True,
                },
                economic_assessment="Additional supply can technically be created",
            ),
        ],
        "counterevidence_status": "present",
        "counterevidence": [
            _observation(
                "facts.tokenomics.freeze_authority",
                "Freeze authority is disabled.",
                source_value={"value": None, "verified": True},
                economic_assessment=(
                    "This removes freeze-authority risk but does not by itself "
                    "offset the market weakness"
                ),
            )
        ],
        "important_unknowns": [
            {
                "unknown_ref": "unknowns.freshness",
                "source_value": "facts.market.freshness",
                "explanation": (
                    "Current price, liquidity, volume, and transaction freshness "
                    "are not fully verified."
                ),
            },
            {
                "unknown_ref": "unknowns.corroboration",
                "source_value": "independent market corroboration",
                "explanation": (
                    "No independent market source currently corroborates the snapshot."
                ),
            },
        ],
        "evidence_profile": [
            {
                "dimension": "opinion_evidence_quality",
                "state": "LOW",
                "source_ref": "opinion.evidence_quality",
                "source_value": "LOW",
            },
            {
                "dimension": "proof_strength",
                "state": "WEAK",
                "source_ref": "evidence.evidence_context.proof_strength",
                "source_value": "WEAK",
            },
            {
                "dimension": "freshness",
                "state": "PARTIAL",
                "source_ref": "facts.market.freshness.freshness_state",
                "source_value": "PARTIAL",
            },
        ],
        "what_would_change_my_mind": [
            {
                "condition": "Meaningfully deeper verified liquidity appears.",
                "fact_refs": ["facts.market.liquidity_usd"],
            },
            {
                "condition": "Fresh independently corroborated market activity becomes available.",
                "fact_refs": ["facts.market.freshness"],
            },
            {
                "condition": "Verified mint-control evidence materially improves.",
                "fact_refs": ["facts.tokenomics.mint_authority"],
            },
        ],
        "opinion_counterevidence_text": (
            "Freeze authority is disabled and supply data checks out."
        ),
        "opinion_what_would_change_my_mind_text": (
            "Deeper liquidity and fresh independent market evidence."
        ),
        "technical_detail": {
            "available": True,
            "reference": "roberta_decision/v1#evidence",
            "source_contract": "instant_x1_scan_product_view/v1",
        },
        "facts_authority": "chain_scout_cmis",
        "judgment_authority": "roberta",
        "read_only": True,
        "fact_values_recomputed": False,
        "execution_authorized": False,
    }


def test_normal_x1x_response_is_judgment_first_and_human():
    text = render_human_response(_response_decision())

    assert text.startswith("I wouldn't trade X1X right now.")
    assert "The biggest reason is only about $13 of liquidity is verified." in text
    assert "For me, that means extremely thin" in text
    assert "The mint authority is still active" in text
    assert "There is some evidence on the other side:" in text
    assert "Freeze authority is disabled." in text
    assert "What I'm still uncertain about:" in text
    assert "My conviction is moderate, and the evidence quality is low." in text
    assert "What would change my mind:" in text

    # Normal mode is human-first; internal contract/service vocabulary stays hidden.
    assert "instant_x1_scan_product_view/v1" not in text
    assert "roberta_decision/v1" not in text
    assert "chain_scout_cmis" not in text
    assert "execution_authorized" not in text


def test_quick_mode_is_concise_and_keeps_one_key_uncertainty():
    text = render_human_response(_response_decision(), response_depth="quick")

    assert text.startswith("I wouldn't trade X1X right now.")
    assert "Verified measured 24h volume is zero." in text
    assert "The mint authority is still active." not in text
    assert "Current price, liquidity, volume, and transaction freshness" in text
    assert "There is some evidence on the other side:" not in text
    assert "What would change my mind:" not in text
    assert "Evidence profile:" not in text
    assert "Technical evidence:" not in text


def test_deep_dive_adds_evidence_profile_and_technical_boundary():
    text = render_human_response(_response_decision(), response_depth="deep_dive")

    assert "Evidence profile:" in text
    assert "- Opinion Evidence Quality: low" in text
    assert "- Proof Strength: weak" in text
    assert "- Freshness: partially verified" in text
    assert "Technical evidence:" in text
    assert "Evidence reference: roberta_decision/v1#evidence" in text
    assert "Source contract: instant_x1_scan_product_view/v1" in text
    assert "this renderer does not recompute them" in text
    assert "Execution remains unauthorized." in text


@pytest.mark.parametrize(
    ("recommendation", "expected"),
    [
        ("STRONGLY_AVOID", "I'd strongly avoid X1X right now."),
        ("AVOID", "I wouldn't trade X1X right now."),
        ("WAIT", "I'd wait before acting on X1X."),
        ("WATCH", "I'd watch X1X rather than act right now."),
        ("ACCUMULATE_CAUTIOUSLY", "I'd only accumulate X1X cautiously."),
        ("BUY", "I'd be comfortable buying X1X under the evidence I have."),
        ("STRONGLY_FAVOR", "I'd strongly favor X1X under the evidence I have."),
        ("HOLD", "I'd hold X1X for now."),
        ("REDUCE", "I'd reduce exposure to X1X."),
        ("EXIT", "I'd exit the X1X position."),
        (
            "INSUFFICIENT_EVIDENCE",
            "I don't have enough evidence to support a X1X trade decision yet.",
        ),
    ],
)
def test_first_person_recommendation_vocabulary(recommendation, expected):
    value = _response_decision(recommendation=recommendation)
    value["recommendation_family"] = "test-family"

    text = render_human_response(value, response_depth="quick")
    assert text.startswith(expected)


def test_public_contract_projection_preserves_opinion_and_authority():
    source = _response_decision()
    before = copy.deepcopy(source)

    contract = build_public_human_response_contract(source)

    assert contract["contract_version"] == "roberta_human_response/v1"
    assert contract["recommendation"] == "AVOID"
    assert contract["conviction"] == "MODERATE"
    assert contract["evidence_quality"] == "LOW"
    assert contract["facts_authority"] == "chain_scout_cmis"
    assert contract["judgment_authority"] == "roberta"
    assert contract["read_only"] is True
    assert contract["fact_values_recomputed"] is False
    assert contract["execution_authorized"] is False
    assert source == before


def test_renderer_never_turns_verified_into_economic_pass():
    text = render_human_response(_response_decision())

    assert "liquidity: PASS" not in text
    assert "Liquidity: PASS" not in text
    assert "economically inadequate" in text


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("facts_authority", "roberta", "facts_authority"),
        ("judgment_authority", "cmis", "judgment_authority"),
        ("read_only", False, "read_only"),
        ("fact_values_recomputed", True, "fact_values_recomputed"),
        ("execution_authorized", True, "execution_authorized"),
    ],
)
def test_renderer_fails_closed_on_authority_mutation(field, value, match):
    response = _response_decision()
    response[field] = value

    with pytest.raises(HumanResponseRenderError, match=match):
        render_human_response(response)


def test_renderer_rejects_ineligible_depth():
    response = _response_decision()
    response["response_depth_eligibility"] = ["quick", "normal"]

    with pytest.raises(HumanResponseRenderError, match="not eligible"):
        render_human_response(response, response_depth="deep_dive")


def test_renderer_rejects_machine_status_as_primary_economic_meaning():
    response = _response_decision()
    response["primary_decision_driver"]["economic_assessment"] = "PASS"

    with pytest.raises(HumanResponseRenderError, match="Human Response Contract"):
        render_human_response(response)


@pytest.mark.parametrize(
    ("workflow", "source_contract"),
    [
        ("instant_x1_scan", "instant_x1_scan_product_view/v1"),
        ("x1_burn_intelligence", "x1_burn_intelligence/v1"),
        ("x1_discovery_intelligence", "x1_discovery_intelligence/v1"),
        ("x1_what_changed", "x1_what_changed/v1"),
        ("x1_concentration_warning_intelligence", "x1_concentration_warning_intelligence/v1"),
        ("x1_cross_chain_asset_provenance", "x1_cross_chain_asset_provenance/v1"),
        ("x1_trade_price_impact_intelligence", "x1_trade_price_impact_intelligence/v1"),
        ("x1_large_trade_discovery", "x1_large_trade_discovery/v1"),
        ("x1_regulatory_intelligence", "x1_regulatory_intelligence/v1"),
    ],
)
def test_renderer_is_workflow_agnostic_across_accepted_intelligence_families(
    workflow,
    source_contract,
):
    response = _response_decision()
    response["workflow"] = workflow
    response["technical_detail"]["source_contract"] = source_contract

    normal = render_human_response(response)
    deep = render_human_response(response, response_depth="deep_dive")

    assert normal.startswith("I wouldn't trade X1X right now.")
    assert source_contract not in normal
    assert source_contract in deep
    assert "Execution remains unauthorized." in deep
