"""Public deterministic Tokenized Equity Human renderer for ROBERTA #427.

Consumes only a protected roberta_tokenized_equity_human_plan/v1 data object.
It does not import protected source, call CMIS/providers, reconstruct Machine
facts, add a recommendation/risk/legal/investment conclusion, or authorize
execution.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any

TOKENIZED_EQUITY_HUMAN_PLAN_CONTRACT = "roberta_tokenized_equity_human_plan/v1"
TOKENIZED_EQUITY_HUMAN_RESPONSE_CONTRACT = "roberta_tokenized_equity_human_response/v1"

_ALLOWED_DEPTHS = ("quick", "normal", "deep_dive")
_SECTION_ORDER = (
    "what_it_is",
    "ownership_exposure",
    "rights",
    "dependencies",
    "lineage",
    "market",
    "evidence",
    "wallet",
    "unknowns",
)
_QUICK_SECTIONS = (
    "what_it_is",
    "ownership_exposure",
    "rights",
    "evidence",
    "unknowns",
)
_ALLOWED_STATES = frozenset(
    {
        "VERIFIED",
        "AUTHORIZED",
        "MIXED",
        "DENIED",
        "CONDITIONAL",
        "EVIDENCE_REQUIRED",
        "NOT_APPLICABLE",
        "UNKNOWN",
    }
)


class TokenizedEquityHumanRenderError(ValueError):
    """Raised when a protected Tokenized Equity Human plan is unsafe to render."""


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise TokenizedEquityHumanRenderError(f"{field} must be a mapping")
    return value


def _sequence(value: Any, field: str) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(
        value, (str, bytes, bytearray, Mapping)
    ):
        raise TokenizedEquityHumanRenderError(f"{field} must be a list")
    return list(value)


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TokenizedEquityHumanRenderError(f"{field} must be non-empty text")
    return value.strip()


def _validate_section(value: Any, index: int) -> dict[str, Any]:
    section = deepcopy(dict(_mapping(value, f"sections[{index}]")))
    expected_key = _SECTION_ORDER[index]
    if section.get("key") != expected_key:
        raise TokenizedEquityHumanRenderError(
            f"sections[{index}].key must be {expected_key}"
        )
    _text(section.get("heading"), f"sections[{index}].heading")
    state = _text(section.get("state"), f"sections[{index}].state").upper()
    if state not in _ALLOWED_STATES:
        raise TokenizedEquityHumanRenderError(
            f"sections[{index}].state is unsupported"
        )
    summary = _text(section.get("summary"), f"sections[{index}].summary")
    refs = _sequence(section.get("technical_refs"), f"sections[{index}].technical_refs")
    limitations = _sequence(
        section.get("limitations"), f"sections[{index}].limitations"
    )
    if any(not isinstance(item, str) or not item.strip() for item in refs):
        raise TokenizedEquityHumanRenderError(
            f"sections[{index}].technical_refs must contain text"
        )
    if any(not isinstance(item, str) or not item.strip() for item in limitations):
        raise TokenizedEquityHumanRenderError(
            f"sections[{index}].limitations must contain text"
        )
    for flag in ("new_fact_added", "authority_widened"):
        if section.get(flag) is not False:
            raise TokenizedEquityHumanRenderError(
                f"sections[{index}].{flag} must remain false"
            )
    section["state"] = state
    section["summary"] = summary
    section["technical_refs"] = [str(item).strip() for item in refs]
    section["limitations"] = [str(item).strip() for item in limitations]
    return section


def validate_tokenized_equity_human_plan(value: Any) -> dict[str, Any]:
    plan = deepcopy(dict(_mapping(value, "human_plan")))
    if plan.get("contract_version") != TOKENIZED_EQUITY_HUMAN_PLAN_CONTRACT:
        raise TokenizedEquityHumanRenderError("Human plan contract mismatch")
    if plan.get("workflow") != "x1_tokenized_equity_intelligence":
        raise TokenizedEquityHumanRenderError("Human plan workflow mismatch")
    if plan.get("chain") != "x1":
        raise TokenizedEquityHumanRenderError("Human plan must remain X1-only")
    if plan.get("source_machine_contract") != "roberta_tokenized_equity_machine/v1":
        raise TokenizedEquityHumanRenderError("Human plan Machine contract mismatch")
    if plan.get("facts_authority") != "chain_scout_cmis":
        raise TokenizedEquityHumanRenderError(
            "facts_authority must remain chain_scout_cmis"
        )
    if plan.get("synthesis_authority") != "roberta":
        raise TokenizedEquityHumanRenderError(
            "synthesis_authority must remain roberta"
        )
    if plan.get("explanation_authority") != "roberta":
        raise TokenizedEquityHumanRenderError(
            "explanation_authority must remain roberta"
        )
    for field in (
        "recommendation",
        "risk_conclusion",
        "legal_conclusion",
        "investment_conclusion",
    ):
        if plan.get(field) is not None:
            raise TokenizedEquityHumanRenderError(f"{field} must remain null")
    for field, expected in (
        ("fact_values_recomputed", False),
        ("claim_authority_widened", False),
        ("new_chain_fact_added", False),
        ("read_only", True),
        ("execution_authorized", False),
    ):
        if plan.get(field) is not expected:
            raise TokenizedEquityHumanRenderError(
                f"{field} must remain {str(expected).lower()}"
            )

    eligibility = _sequence(
        plan.get("response_depth_eligibility"), "response_depth_eligibility"
    )
    if tuple(eligibility) != _ALLOWED_DEPTHS:
        raise TokenizedEquityHumanRenderError(
            "response_depth_eligibility must preserve quick/normal/deep_dive order"
        )

    subject = deepcopy(dict(_mapping(plan.get("subject"), "subject")))
    _text(subject.get("asset_mint"), "subject.asset_mint")

    raw_sections = _sequence(plan.get("sections"), "sections")
    if len(raw_sections) != len(_SECTION_ORDER):
        raise TokenizedEquityHumanRenderError(
            "Human plan must contain the exact nine-section answer order"
        )
    sections = [
        _validate_section(raw, index) for index, raw in enumerate(raw_sections)
    ]

    unknowns = deepcopy(dict(_mapping(plan.get("unknowns"), "unknowns")))
    required_claims = _sequence(
        unknowns.get("evidence_required_claims"),
        "unknowns.evidence_required_claims",
    )
    rights = _sequence(
        unknowns.get("evidence_required_rights_dimensions"),
        "unknowns.evidence_required_rights_dimensions",
    )
    strengthen = _mapping(
        unknowns.get("what_evidence_would_strengthen"),
        "unknowns.what_evidence_would_strengthen",
    )
    if any(not isinstance(item, str) or not item for item in required_claims + rights):
        raise TokenizedEquityHumanRenderError(
            "unknown evidence-required entries must contain text"
        )
    if any(
        not isinstance(key, str)
        or not key
        or not isinstance(item, str)
        or not item.strip()
        for key, item in strengthen.items()
    ):
        raise TokenizedEquityHumanRenderError(
            "what_evidence_would_strengthen must map text keys to text values"
        )
    if unknowns.get("unknown_converted_to_false_or_zero") is not False:
        raise TokenizedEquityHumanRenderError(
            "unknown_converted_to_false_or_zero must remain false"
        )

    plan["subject"] = subject
    plan["sections"] = sections
    plan["unknowns"] = unknowns
    return plan


def build_tokenized_equity_human_response(
    human_plan: Mapping[str, Any],
    *,
    response_depth: str = "normal",
) -> dict[str, Any]:
    plan = validate_tokenized_equity_human_plan(human_plan)
    if response_depth not in _ALLOWED_DEPTHS:
        raise TokenizedEquityHumanRenderError(
            f"response_depth must be one of {_ALLOWED_DEPTHS}"
        )

    visible_keys = set(_QUICK_SECTIONS) if response_depth == "quick" else set(_SECTION_ORDER)
    visible = [
        deepcopy(section)
        for section in plan["sections"]
        if section["key"] in visible_keys
    ]

    if response_depth != "deep_dive":
        for section in visible:
            section["technical_refs"] = []
            section["limitations"] = []

    return {
        "contract_version": TOKENIZED_EQUITY_HUMAN_RESPONSE_CONTRACT,
        "workflow": "x1_tokenized_equity_intelligence",
        "chain": "x1",
        "response_depth": response_depth,
        "title": "What exactly am I buying?",
        "status": plan.get("status"),
        "subject": deepcopy(plan["subject"]),
        "sections": visible,
        "unknowns": deepcopy(plan["unknowns"]),
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


def _subject_label(subject: Mapping[str, Any]) -> str:
    for key in ("symbol", "name", "asset_mint"):
        value = subject.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return "this tokenized asset"


def render_tokenized_equity_human(
    human_plan: Mapping[str, Any],
    *,
    response_depth: str = "normal",
) -> str:
    response = build_tokenized_equity_human_response(
        human_plan,
        response_depth=response_depth,
    )
    subject = _subject_label(_mapping(response["subject"], "subject"))
    lines = [
        "ROBERTA — WHAT EXACTLY AM I BUYING?",
        f"Asset: {subject}",
        "",
    ]

    for raw in response["sections"]:
        section = _mapping(raw, "section")
        lines.append(str(section["heading"]).upper())
        lines.append(f"{section['state']}: {section['summary']}")
        if response_depth == "deep_dive":
            refs = list(section.get("technical_refs") or [])
            limits = list(section.get("limitations") or [])
            if refs:
                lines.append("Evidence refs: " + "; ".join(str(item) for item in refs))
            if limits:
                lines.append("Limits: " + "; ".join(str(item) for item in limits))
        lines.append("")

    if response_depth == "deep_dive":
        unknowns = _mapping(response.get("unknowns"), "unknowns")
        strengthen = _mapping(
            unknowns.get("what_evidence_would_strengthen"),
            "unknowns.what_evidence_would_strengthen",
        )
        if strengthen:
            lines.append("WHAT WOULD STRENGTHEN THE EVIDENCE")
            for key, value in strengthen.items():
                lines.append(f"- {key}: {value}")
            lines.append("")

    lines.extend(
        [
            "ROBERTA did not add a trade recommendation, legal conclusion, risk conclusion, or investment conclusion.",
            "Proof strength remains separate from risk.",
            "Analysis only — execution authorized: false.",
        ]
    )
    return "\n".join(lines).rstrip()


__all__ = [
    "TOKENIZED_EQUITY_HUMAN_PLAN_CONTRACT",
    "TOKENIZED_EQUITY_HUMAN_RESPONSE_CONTRACT",
    "TokenizedEquityHumanRenderError",
    "build_tokenized_equity_human_response",
    "render_tokenized_equity_human",
    "validate_tokenized_equity_human_plan",
]
