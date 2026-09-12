from roberta.human_response_renderer import (
    HUMAN_RESPONSE_DECISION_CONTRACT,
    _plain_language_text,
    render_human_response,
)


def _observation(fact_ref, interpretation, *, economic_assessment=None):
    item = {
        "fact_ref": fact_ref,
        "verification_state": "NOT_VERIFIED",
        "interpretation": interpretation,
    }
    if economic_assessment is not None:
        item["economic_assessment"] = economic_assessment
    return item


def _technical_response_decision(depth="normal"):
    return {
        "contract_version": HUMAN_RESPONSE_DECISION_CONTRACT,
        "source_decision_contract": "roberta_decision/v1",
        "source_opinion_contract": "roberta_opinion/v1",
        "workflow": "instant_x1_scan",
        "subject": {"symbol": "TEST"},
        "response_depth": depth,
        "response_depth_eligibility": ["quick", "normal", "deep_dive"],
        "recommendation": "INSUFFICIENT_EVIDENCE",
        "recommendation_family": "insufficient_evidence",
        "conviction": "LOW",
        "evidence_quality": "WEAK",
        "primary_decision_driver": _observation(
            "facts.market.risk",
            "The CMIS deterministic risk result is unavailable while liquidity is $13.",
            economic_assessment="The verification state is NOT_VERIFIED",
        ),
        "supporting_evidence": [
            _observation(
                "facts.market.source",
                "The Chain Scout source contract has no provider corroboration.",
            ),
            _observation(
                "facts.market.activity",
                "Measured market activity remains unavailable.",
            ),
        ],
        "counterevidence_status": "present",
        "counterevidence": [
            _observation(
                "facts.asset.identity",
                "Asset identity itself is verified.",
                economic_assessment="That does not resolve the missing risk evidence",
            )
        ],
        "important_unknowns": [
            {
                "unknown_ref": "unknowns.freshness",
                "explanation": "The freshness state is NOT_VERIFIED and provider fact time is unavailable.",
            }
        ],
        "evidence_profile": [
            {
                "dimension": "freshness",
                "state": "PARTIAL",
            },
            {
                "dimension": "proof_strength",
                "state": "WEAK",
            },
        ],
        "what_would_change_my_mind": [
            {
                "condition": "Independent corroboration and a current deterministic risk result become available.",
                "fact_refs": ["facts.market.risk"],
            }
        ],
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


def test_plain_language_transform_preserves_values_and_uncertainty_tokens():
    source = (
        "CMIS deterministic risk result is unavailable at $13. "
        "The freshness state is NOT_VERIFIED."
    )

    rendered = _plain_language_text(source, depth="normal")

    assert "evidence service" in rendered
    assert "risk assessment" in rendered
    assert "whether the data is current" in rendered
    assert "$13" in rendered
    assert "NOT_VERIFIED" in rendered


def test_normal_runtime_hides_engineering_language_without_changing_evidence():
    text = render_human_response(_technical_response_decision(), response_depth="normal")

    assert text.startswith(
        "I don't have enough evidence to support a trade decision on TEST yet."
    )
    assert "$13" in text
    assert "NOT_VERIFIED" in text
    assert "risk assessment" in text
    assert "evidence service" in text
    assert "chain analysis" in text
    assert "source details" in text
    assert "confirmation from another source" in text
    assert "whether the data is current" in text
    assert "when the source data was observed" in text

    assert "deterministic risk result" not in text.lower()
    assert "freshness state" not in text.lower()
    assert "verification state" not in text.lower()
    assert "source contract" not in text.lower()
    assert "provider corroboration" not in text.lower()
    assert "provider fact time" not in text.lower()
    assert "cmis" not in text.lower()
    assert "chain scout" not in text.lower()


def test_quick_runtime_uses_same_plain_language_boundary():
    text = render_human_response(_technical_response_decision(), response_depth="quick")

    assert "$13" in text
    assert "risk assessment" in text
    assert "whether the data is current" in text
    assert "deterministic risk result" not in text.lower()
    assert "freshness state" not in text.lower()
    assert "cmis" not in text.lower()


def test_deep_dive_retains_precise_technical_language():
    text = render_human_response(_technical_response_decision(), response_depth="deep_dive")

    assert "CMIS deterministic risk result" in text
    assert "verification state is NOT_VERIFIED" in text
    assert "Chain Scout source contract" in text
    assert "provider corroboration" in text
    assert "freshness state is NOT_VERIFIED" in text
    assert "provider fact time is unavailable" in text
    assert "Source contract: instant_x1_scan_product_view/v1" in text
    assert "Facts remain Chain Scout / CMIS authority" in text
