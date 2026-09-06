import copy

import pytest

from roberta.human_response_contract import (
    CONTRACT_VERSION,
    HumanResponseContractError,
    validate_human_response_contract,
)


def _source_facts():
    return {
        "market.liquidity_usd": '{"value":12.81,"currency":"USD","verified":true}',
        "market.volume_24h_usd": '{"value":0.0,"window":"24h","verified":true}',
        "market.transactions_24h": '{"value":0,"window":"24h","verified":true}',
        "token.mint_authority": '{"status":"active","verified":true}',
        "token.freeze_authority": '{"status":"none","verified":true}',
    }


def _opinion():
    return {
        "contract_version": "roberta_opinion/v1",
        "recommendation": "AVOID",
        "recommendation_strength": "MODERATE",
        "evidence_quality": "LOW",
    }


def _observation(
    fact_ref,
    verification_state,
    interpretation,
    *,
    source_fact_json=None,
    economic_assessment=None,
):
    value = {
        "fact_ref": fact_ref,
        "verification_state": verification_state,
        "interpretation": interpretation,
    }
    if source_fact_json is not None:
        value["source_fact_json"] = source_fact_json
    if economic_assessment is not None:
        value["economic_assessment"] = economic_assessment
    return value


def _payload(depth="normal"):
    source = _source_facts()
    return {
        "contract_version": CONTRACT_VERSION,
        "response_depth": depth,
        "direct_answer": "I wouldn't trade X1X right now.",
        "recommendation": "AVOID",
        "conviction": "MODERATE",
        "evidence_quality": "LOW",
        "facts_authority": "chain_scout_cmis",
        "judgment_authority": "roberta",
        "read_only": True,
        "execution_authorized": False,
        "verification_and_interpretation_separated": True,
        "fact_values_recomputed": False,
        "primary_decision_driver": _observation(
            "market.liquidity_usd",
            "VERIFIED",
            "Only about $13 of liquidity is verified.",
            source_fact_json=source["market.liquidity_usd"],
            economic_assessment="Extremely thin and economically inadequate for meaningful trading",
        ),
        "supporting_observations": [
            _observation(
                "market.volume_24h_usd",
                "VERIFIED",
                "Verified measured 24h volume is zero.",
                source_fact_json=source["market.volume_24h_usd"],
            ),
            _observation(
                "token.mint_authority",
                "VERIFIED",
                "The mint authority is still active.",
                source_fact_json=source["token.mint_authority"],
                economic_assessment="Additional supply can technically be created",
            ),
        ],
        "counterevidence_status": "present",
        "counterevidence": [
            _observation(
                "token.freeze_authority",
                "VERIFIED",
                "Freeze authority is disabled.",
                source_fact_json=source["token.freeze_authority"],
                economic_assessment="This removes freeze-authority risk but does not offset the market weakness",
            )
        ],
        "important_unknowns": [
            {
                "unknown_ref": "market.current_freshness",
                "explanation": "Current price, liquidity, volume, and transaction freshness are not fully verified.",
            },
            {
                "unknown_ref": "market.independent_corroboration",
                "explanation": "No independent market source currently corroborates the snapshot.",
            },
        ],
        "evidence_profile": [
            {
                "dimension": "identity_and_supply",
                "state": "STRONG",
                "explanation": "Supply and control facts are verified.",
            },
            {
                "dimension": "market_activity",
                "state": "WEAK",
                "explanation": "The measured market has effectively no verified activity.",
            },
            {
                "dimension": "freshness",
                "state": "UNVERIFIED",
                "explanation": "Current market freshness is incomplete.",
            },
        ],
        "what_would_change_my_mind": [
            {
                "condition": "Meaningfully deeper verified liquidity appears.",
                "fact_refs": ["market.liquidity_usd"],
            },
            {
                "condition": "Fresh independently corroborated market activity becomes available.",
                "fact_refs": [
                    "market.volume_24h_usd",
                    "market.transactions_24h",
                    "market.current_freshness",
                    "market.independent_corroboration",
                ],
            },
            {
                "condition": "The mint-authority state is rechecked and materially improves.",
                "fact_refs": ["token.mint_authority"],
            },
        ],
        "technical_detail": {
            "available": True,
            "reference": "roberta_decision/v1#evidence",
        },
    }


def test_x1x_style_normal_contract_is_valid_and_detached():
    payload = _payload()
    validated = validate_human_response_contract(
        payload,
        opinion=_opinion(),
        source_fact_json=_source_facts(),
    )

    assert validated == payload
    assert validated is not payload
    validated["direct_answer"] = "changed"
    assert payload["direct_answer"] == "I wouldn't trade X1X right now."


def test_source_fact_json_must_match_byte_for_byte_when_carried():
    payload = _payload()
    payload["primary_decision_driver"]["source_fact_json"] = (
        '{"verified":true,"currency":"USD","value":12.81}'
    )

    with pytest.raises(HumanResponseContractError, match="byte-match"):
        validate_human_response_contract(
            payload,
            opinion=_opinion(),
            source_fact_json=_source_facts(),
        )


def test_source_fact_json_cannot_be_carried_without_validation_source():
    with pytest.raises(HumanResponseContractError, match="requires source_fact_json"):
        validate_human_response_contract(_payload(), opinion=_opinion())


def test_human_response_must_preserve_opinion_recommendation_conviction_and_quality():
    payload = _payload()
    payload["recommendation"] = "WAIT"

    with pytest.raises(HumanResponseContractError, match="recommendation"):
        validate_human_response_contract(
            payload,
            opinion=_opinion(),
            source_fact_json=_source_facts(),
        )


def test_primary_driver_cannot_reuse_machine_status_as_economic_meaning():
    payload = _payload()
    payload["primary_decision_driver"]["economic_assessment"] = "PASS"

    with pytest.raises(HumanResponseContractError, match="human economic meaning"):
        validate_human_response_contract(
            payload,
            opinion=_opinion(),
            source_fact_json=_source_facts(),
        )


def test_normal_requires_two_to_four_supporting_observations():
    payload = _payload()
    payload["supporting_observations"] = payload["supporting_observations"][:1]

    with pytest.raises(HumanResponseContractError, match="2-4 items"):
        validate_human_response_contract(
            payload,
            opinion=_opinion(),
            source_fact_json=_source_facts(),
        )


def test_quick_allows_one_supporting_observation_and_one_profile_dimension():
    payload = _payload(depth="quick")
    payload["supporting_observations"] = payload["supporting_observations"][:1]
    payload["evidence_profile"] = payload["evidence_profile"][:1]

    validated = validate_human_response_contract(
        payload,
        opinion=_opinion(),
        source_fact_json=_source_facts(),
    )
    assert validated["response_depth"] == "quick"


def test_counterevidence_status_prevents_fake_balance():
    payload = _payload()
    payload["counterevidence_status"] = "none_material"
    payload["counterevidence"] = []

    validated = validate_human_response_contract(
        payload,
        opinion=_opinion(),
        source_fact_json=_source_facts(),
    )
    assert validated["counterevidence_status"] == "none_material"

    broken = copy.deepcopy(payload)
    broken["counterevidence"] = [
        _observation(
            "token.freeze_authority",
            "VERIFIED",
            "Freeze authority is disabled.",
        )
    ]
    with pytest.raises(HumanResponseContractError, match="must be empty"):
        validate_human_response_contract(
            broken,
            opinion=_opinion(),
            source_fact_json=_source_facts(),
        )


def test_material_decision_requires_evidence_bound_change_conditions():
    payload = _payload()
    payload["what_would_change_my_mind"] = []

    with pytest.raises(HumanResponseContractError, match="1-5"):
        validate_human_response_contract(
            payload,
            opinion=_opinion(),
            source_fact_json=_source_facts(),
        )


def test_technical_detail_reference_is_progressive_disclosure_only():
    payload = _payload()
    payload["technical_detail"] = {"available": False, "reference": None}

    validated = validate_human_response_contract(
        payload,
        opinion=_opinion(),
        source_fact_json=_source_facts(),
    )
    assert validated["technical_detail"] == {"available": False, "reference": None}


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("facts_authority", "roberta", "facts_authority"),
        ("judgment_authority", "cmis", "judgment_authority"),
        ("read_only", False, "read_only"),
        ("execution_authorized", True, "execution_authorized"),
        (
            "verification_and_interpretation_separated",
            False,
            "verification_and_interpretation_separated",
        ),
        ("fact_values_recomputed", True, "fact_values_recomputed"),
    ],
)
def test_authority_and_execution_invariants_fail_closed(field, value, error):
    payload = _payload()
    payload[field] = value

    with pytest.raises(HumanResponseContractError, match=error):
        validate_human_response_contract(
            payload,
            opinion=_opinion(),
            source_fact_json=_source_facts(),
        )


def test_actual_opinion_v1_recommendation_strength_is_accepted():
    payload = _payload()
    payload["evidence_profile"][0]["state"] = "LOW"

    validated = validate_human_response_contract(
        payload,
        opinion=_opinion(),
        source_fact_json=_source_facts(),
    )

    assert validated["conviction"] == "MODERATE"
    assert validated["evidence_quality"] == "LOW"
