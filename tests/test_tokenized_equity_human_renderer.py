from __future__ import annotations

from copy import deepcopy

import pytest

from roberta.tokenized_equity_human_renderer import (
    TOKENIZED_EQUITY_HUMAN_RESPONSE_CONTRACT,
    TokenizedEquityHumanRenderError,
    build_tokenized_equity_human_response,
    render_tokenized_equity_human,
    validate_tokenized_equity_human_plan,
)


def _section(key: str, heading: str, state: str, summary: str) -> dict[str, object]:
    return {
        "key": key,
        "heading": heading,
        "state": state,
        "summary": summary,
        "technical_refs": [f"machine.sections.{key}"],
        "limitations": [f"{key}_authority_is_bounded"],
        "new_fact_added": False,
        "authority_widened": False,
    }


def _plan() -> dict[str, object]:
    return {
        "contract_version": "roberta_tokenized_equity_human_plan/v1",
        "workflow": "x1_tokenized_equity_intelligence",
        "chain": "x1",
        "status": "partial",
        "source_machine_contract": "roberta_tokenized_equity_machine/v1",
        "subject": {
            "asset_mint": "11111111111111111111111111111111",
            "symbol": "ACMEX",
            "name": "Acme Tokenized Equity",
        },
        "sections": [
            _section(
                "what_it_is",
                "What it is",
                "VERIFIED",
                "The exact X1 token identity is verified; the representation description does not establish legal equivalence to the underlying share.",
            ),
            _section(
                "ownership_exposure",
                "What you actually own or are exposed to",
                "EVIDENCE_REQUIRED",
                "The evidence does not establish shareholder or beneficial ownership of the underlying company.",
            ),
            _section(
                "rights",
                "What rights exist",
                "MIXED",
                "Voting rights are DENIED, dividend rights are CONDITIONAL, and redemption remains EVIDENCE_REQUIRED.",
            ),
            _section(
                "dependencies",
                "Who or what you depend on",
                "VERIFIED",
                "Issuer and custody dependencies are described from evidence, without claiming backing sufficiency or custody safety.",
            ),
            _section(
                "lineage",
                "Where it came from",
                "VERIFIED",
                "A qualified route configuration is verified; observed asset movement and adoption are not verified by that configuration alone.",
            ),
            _section(
                "market",
                "What the market evidence says",
                "VERIFIED",
                "Liquidity, volume, transfers, trades, and price observations keep their exact source semantics; a reference price is not an executed price.",
            ),
            _section(
                "evidence",
                "How strong or fresh the evidence is",
                "MIXED",
                "Proof Score describes evidence strength and remains separate from risk; freshness and conflicts remain explicit.",
            ),
            _section(
                "wallet",
                "Observed wallet activity",
                "NOT_APPLICABLE",
                "No authorized matching transaction-scoped wallet observation is included in this answer.",
            ),
            _section(
                "unknowns",
                "What remains unknown",
                "EVIDENCE_REQUIRED",
                "Ownership and redemption evidence are still required and have not been converted to false or zero.",
            ),
        ],
        "unknowns": {
            "evidence_required_claims": ["ownership_exposure"],
            "evidence_required_rights_dimensions": ["redemption_rights"],
            "what_evidence_would_strengthen": {
                "ownership_exposure": "accepted authoritative ownership/exposure evidence",
                "holder_rights_dimensions": "accepted authoritative redemption-rights evidence",
            },
            "unknown_converted_to_false_or_zero": False,
        },
        "response_depth_eligibility": ["quick", "normal", "deep_dive"],
        "facts_authority": "chain_scout_cmis",
        "synthesis_authority": "roberta",
        "explanation_authority": "roberta",
        "recommendation": None,
        "risk_conclusion": None,
        "legal_conclusion": None,
        "investment_conclusion": None,
        "fact_values_recomputed": False,
        "claim_authority_widened": False,
        "new_chain_fact_added": False,
        "read_only": True,
        "execution_authorized": False,
    }


def test_plan_validates_without_inventing_decision_authority():
    source = _plan()
    before = deepcopy(source)
    validated = validate_tokenized_equity_human_plan(source)
    assert source == before
    assert validated["recommendation"] is None
    assert validated["risk_conclusion"] is None
    assert validated["legal_conclusion"] is None
    assert validated["investment_conclusion"] is None
    assert validated["execution_authorized"] is False


def test_quick_normal_and_deep_dive_preserve_progressive_disclosure():
    quick = build_tokenized_equity_human_response(_plan(), response_depth="quick")
    normal = build_tokenized_equity_human_response(_plan(), response_depth="normal")
    deep = build_tokenized_equity_human_response(_plan(), response_depth="deep_dive")

    assert quick["contract_version"] == TOKENIZED_EQUITY_HUMAN_RESPONSE_CONTRACT
    assert [row["key"] for row in quick["sections"]] == [
        "what_it_is",
        "ownership_exposure",
        "rights",
        "evidence",
        "unknowns",
    ]
    assert len(normal["sections"]) == 9
    assert len(deep["sections"]) == 9
    assert all(row["technical_refs"] == [] for row in normal["sections"])
    assert all(row["limitations"] == [] for row in normal["sections"])
    assert deep["sections"][0]["technical_refs"]
    assert deep["sections"][0]["limitations"]


def test_human_text_keeps_denied_conditional_and_evidence_required_explicit():
    text = render_tokenized_equity_human(_plan(), response_depth="normal")
    assert "DENIED" in text
    assert "CONDITIONAL" in text
    assert "EVIDENCE_REQUIRED" in text
    assert "shareholder or beneficial ownership" in text
    assert "reference price is not an executed price" in text
    assert "Proof Score" in text
    assert "execution authorized: false" in text


def test_deep_dive_exposes_evidence_refs_limits_and_strengthening_evidence():
    text = render_tokenized_equity_human(_plan(), response_depth="deep_dive")
    assert "Evidence refs:" in text
    assert "Limits:" in text
    assert "WHAT WOULD STRENGTHEN THE EVIDENCE" in text
    assert "accepted authoritative ownership/exposure evidence" in text


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("recommendation", "BUY", "recommendation must remain null"),
        ("risk_conclusion", "LOW", "risk_conclusion must remain null"),
        ("legal_conclusion", "SHAREHOLDER", "legal_conclusion must remain null"),
        ("investment_conclusion", "ATTRACTIVE", "investment_conclusion must remain null"),
        ("execution_authorized", True, "execution_authorized must remain false"),
        ("claim_authority_widened", True, "claim_authority_widened must remain false"),
        ("fact_values_recomputed", True, "fact_values_recomputed must remain false"),
    ],
)
def test_renderer_fails_closed_on_authority_widening(field, value, match):
    source = _plan()
    source[field] = value
    with pytest.raises(TokenizedEquityHumanRenderError, match=match):
        validate_tokenized_equity_human_plan(source)


def test_renderer_rejects_section_authority_widening():
    source = _plan()
    source["sections"][4]["authority_widened"] = True
    with pytest.raises(TokenizedEquityHumanRenderError, match="authority_widened"):
        validate_tokenized_equity_human_plan(source)


def test_renderer_rejects_wrong_section_order():
    source = _plan()
    source["sections"][0], source["sections"][1] = (
        source["sections"][1],
        source["sections"][0],
    )
    with pytest.raises(TokenizedEquityHumanRenderError, match="sections\[0\].key"):
        validate_tokenized_equity_human_plan(source)
