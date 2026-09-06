"""Deterministic Human ROBERTA renderer for Human Intelligence Experience v1.

The renderer accepts the protected canonical Human Response Decision Object as
data. It does not import protected source, call CMIS/Scouts/models, recalculate
facts, or change the accepted ROBERTA opinion.

Quick / Normal / Deep Dive are presentation depths only.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from roberta.human_response_contract import (
    CONTRACT_VERSION as HUMAN_RESPONSE_CONTRACT,
    HumanResponseContractError,
    validate_human_response_contract,
)

HUMAN_RESPONSE_DECISION_CONTRACT = "roberta_human_response_decision/v1"
HUMAN_RENDERER_CONTRACT = "roberta_human_renderer/v1"

_ALLOWED_DEPTHS = frozenset({"quick", "normal", "deep_dive"})

_DIRECT_ANSWERS = {
    "STRONGLY_AVOID": "I'd strongly avoid this right now.",
    "AVOID": "I wouldn't trade this right now.",
    "WAIT": "I'd wait before acting.",
    "WATCH": "I'd watch this rather than act right now.",
    "ACCUMULATE_CAUTIOUSLY": "I'd only accumulate this cautiously.",
    "BUY": "I'd be comfortable buying under the evidence I have.",
    "STRONGLY_FAVOR": "I'd strongly favor this under the evidence I have.",
    "HOLD": "I'd hold for now.",
    "REDUCE": "I'd reduce exposure.",
    "EXIT": "I'd exit this position.",
    "INSUFFICIENT_EVIDENCE": "I don't have enough evidence to support a trade decision yet.",
}

_STATE_LANGUAGE = {
    "VERY_HIGH": "very high",
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
    "VERY_STRONG": "very strong",
    "STRONG": "strong",
    "MODERATE": "moderate",
    "WEAK": "weak",
    "VERIFIED": "verified",
    "UNVERIFIED": "not verified",
    "NOT_VERIFIED": "not verified",
    "PARTIAL": "partially verified",
    "UNAVAILABLE": "unavailable",
    "UNKNOWN": "unknown",
    "CONFLICTED": "conflicted",
    "STALE": "stale",
    "NOT_APPLICABLE": "not applicable",
    "ACCEPTED_SOURCE_STATE": "accepted source state",
    "WARN": "warning evidence",
    "OK": "accepted",
}


class HumanResponseRenderError(ValueError):
    """Raised when a protected response-decision object cannot be rendered safely."""


def _mapping(value: object, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise HumanResponseRenderError(f"{field} must be an object")
    return value


def _list(value: object, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise HumanResponseRenderError(f"{field} must be a list")
    return list(value)


def _text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HumanResponseRenderError(f"{field} must be non-empty text")
    return value.strip()


def _state(value: object) -> str:
    token = str(value or "UNKNOWN").strip().upper()
    return _STATE_LANGUAGE.get(token, token.replace("_", " ").lower())


def _subject_label(response_decision: Mapping[str, Any]) -> str | None:
    subject = response_decision.get("subject")
    if not isinstance(subject, Mapping):
        return None
    for key in ("symbol", "name", "requested_asset", "mint", "identity_key"):
        value = subject.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _direct_answer(response_decision: Mapping[str, Any]) -> str:
    recommendation = _text(
        response_decision.get("recommendation"),
        "recommendation",
    ).upper()
    base = _DIRECT_ANSWERS.get(recommendation)
    if base is None:
        raise HumanResponseRenderError(
            f"unsupported recommendation for Human renderer: {recommendation}"
        )
    subject = _subject_label(response_decision)
    if subject is None:
        return base

    replacements = {
        "I wouldn't trade this right now.": f"I wouldn't trade {subject} right now.",
        "I'd strongly avoid this right now.": f"I'd strongly avoid {subject} right now.",
        "I'd wait before acting.": f"I'd wait before acting on {subject}.",
        "I'd watch this rather than act right now.": f"I'd watch {subject} rather than act right now.",
        "I'd only accumulate this cautiously.": f"I'd only accumulate {subject} cautiously.",
        "I'd be comfortable buying under the evidence I have.": f"I'd be comfortable buying {subject} under the evidence I have.",
        "I'd strongly favor this under the evidence I have.": f"I'd strongly favor {subject} under the evidence I have.",
        "I'd hold for now.": f"I'd hold {subject} for now.",
        "I'd reduce exposure.": f"I'd reduce exposure to {subject}.",
        "I'd exit this position.": f"I'd exit the {subject} position.",
        "I don't have enough evidence to support a trade decision yet.": (
            f"I don't have enough evidence to support a trade decision on {subject} yet."
        ),
    }
    return replacements.get(base, base)


def _public_observation(item: Mapping[str, Any]) -> dict[str, object]:
    result: dict[str, object] = {
        "fact_ref": _text(item.get("fact_ref"), "observation.fact_ref"),
        "verification_state": _text(
            item.get("verification_state"),
            "observation.verification_state",
        ),
        "interpretation": _text(
            item.get("interpretation"),
            "observation.interpretation",
        ),
    }
    economic = item.get("economic_assessment")
    if economic is not None:
        result["economic_assessment"] = _text(
            economic,
            "observation.economic_assessment",
        )
    return result


def build_public_human_response_contract(
    response_decision: Mapping[str, Any],
    *,
    response_depth: str | None = None,
) -> dict[str, object]:
    """Project the protected response-decision into accepted public #377 shape."""

    root = _mapping(response_decision, "response_decision")
    if root.get("contract_version") != HUMAN_RESPONSE_DECISION_CONTRACT:
        raise HumanResponseRenderError(
            "renderer requires roberta_human_response_decision/v1"
        )
    if root.get("facts_authority") != "chain_scout_cmis":
        raise HumanResponseRenderError("facts_authority must remain chain_scout_cmis")
    if root.get("judgment_authority") != "roberta":
        raise HumanResponseRenderError("judgment_authority must remain roberta")
    if root.get("read_only") is not True:
        raise HumanResponseRenderError("read_only must remain true")
    if root.get("fact_values_recomputed") is not False:
        raise HumanResponseRenderError("fact_values_recomputed must remain false")
    if root.get("execution_authorized") is not False:
        raise HumanResponseRenderError("execution_authorized must remain false")

    depth = response_depth or _text(root.get("response_depth"), "response_depth")
    if depth not in _ALLOWED_DEPTHS:
        raise HumanResponseRenderError(
            f"response_depth must be one of {sorted(_ALLOWED_DEPTHS)}"
        )
    eligible = _list(
        root.get("response_depth_eligibility"),
        "response_depth_eligibility",
    )
    if depth not in eligible:
        raise HumanResponseRenderError(
            f"response depth {depth} is not eligible for this response"
        )

    primary = _public_observation(
        _mapping(root.get("primary_decision_driver"), "primary_decision_driver")
    )
    supporting_raw = _list(root.get("supporting_evidence"), "supporting_evidence")
    supporting = [
        _public_observation(_mapping(item, f"supporting_evidence[{index}]"))
        for index, item in enumerate(supporting_raw)
    ]

    counter_raw = _list(root.get("counterevidence"), "counterevidence")
    counter = [
        _public_observation(_mapping(item, f"counterevidence[{index}]"))
        for index, item in enumerate(counter_raw)
    ]

    unknown_raw = _list(root.get("important_unknowns"), "important_unknowns")
    unknowns: list[dict[str, object]] = []
    for index, item in enumerate(unknown_raw):
        value = _mapping(item, f"important_unknowns[{index}]")
        unknowns.append(
            {
                "unknown_ref": _text(
                    value.get("unknown_ref"),
                    f"important_unknowns[{index}].unknown_ref",
                ),
                "explanation": _text(
                    value.get("explanation"),
                    f"important_unknowns[{index}].explanation",
                ),
            }
        )

    profile_raw = _list(root.get("evidence_profile"), "evidence_profile")
    profile: list[dict[str, object]] = []
    for index, item in enumerate(profile_raw):
        value = _mapping(item, f"evidence_profile[{index}]")
        state = _text(value.get("state"), f"evidence_profile[{index}].state").upper()
        profile.append(
            {
                "dimension": _text(
                    value.get("dimension"),
                    f"evidence_profile[{index}].dimension",
                ),
                "state": state,
                "explanation": (
                    f"{str(value.get('dimension')).replace('_', ' ').strip().title()} "
                    f"is {_state(state)}."
                ),
            }
        )

    conditions_raw = _list(
        root.get("what_would_change_my_mind"),
        "what_would_change_my_mind",
    )
    conditions: list[dict[str, object]] = []
    for index, item in enumerate(conditions_raw):
        value = _mapping(item, f"what_would_change_my_mind[{index}]")
        conditions.append(
            {
                "condition": _text(
                    value.get("condition"),
                    f"what_would_change_my_mind[{index}].condition",
                ),
                "fact_refs": [
                    _text(ref, f"what_would_change_my_mind[{index}].fact_refs")
                    for ref in _list(
                        value.get("fact_refs"),
                        f"what_would_change_my_mind[{index}].fact_refs",
                    )
                ],
            }
        )

    technical = _mapping(root.get("technical_detail"), "technical_detail")
    technical_public = {
        "available": technical.get("available") is True,
        "reference": (
            technical.get("reference")
            if technical.get("available") is True
            else None
        ),
    }

    payload: dict[str, object] = {
        "contract_version": HUMAN_RESPONSE_CONTRACT,
        "response_depth": depth,
        "direct_answer": _direct_answer(root),
        "recommendation": _text(root.get("recommendation"), "recommendation"),
        "conviction": _text(root.get("conviction"), "conviction"),
        "evidence_quality": _text(root.get("evidence_quality"), "evidence_quality"),
        "facts_authority": "chain_scout_cmis",
        "judgment_authority": "roberta",
        "read_only": True,
        "execution_authorized": False,
        "verification_and_interpretation_separated": True,
        "fact_values_recomputed": False,
        "primary_decision_driver": primary,
        "supporting_observations": supporting,
        "counterevidence_status": _text(
            root.get("counterevidence_status"),
            "counterevidence_status",
        ),
        "counterevidence": counter,
        "important_unknowns": unknowns,
        "evidence_profile": profile,
        "what_would_change_my_mind": conditions,
        "technical_detail": technical_public,
    }

    try:
        return validate_human_response_contract(payload)
    except HumanResponseContractError as exc:
        raise HumanResponseRenderError(
            f"protected response-decision cannot satisfy public Human Response Contract v1: {exc}"
        ) from exc


def _primary_sentence(contract: Mapping[str, Any]) -> str:
    primary = _mapping(contract.get("primary_decision_driver"), "primary_decision_driver")
    interpretation = _text(primary.get("interpretation"), "primary.interpretation")
    economic = primary.get("economic_assessment")
    if isinstance(economic, str) and economic.strip():
        economic_text = economic.strip()
        if economic_text.rstrip(".") == interpretation.rstrip("."):
            return f"The biggest reason is {interpretation[0].lower() + interpretation[1:] if interpretation else interpretation}"
        return (
            "The biggest reason is "
            f"{interpretation[0].lower() + interpretation[1:] if interpretation else interpretation} "
            f"For me, that means {economic_text[0].lower() + economic_text[1:] if economic_text else economic_text}."
        )
    return f"The biggest reason is {interpretation[0].lower() + interpretation[1:] if interpretation else interpretation}"


def _supporting_sentence(item: Mapping[str, Any]) -> str:
    interpretation = _text(item.get("interpretation"), "supporting.interpretation")
    economic = item.get("economic_assessment")
    if isinstance(economic, str) and economic.strip():
        return f"{interpretation.rstrip('.')} — {economic.strip().rstrip('.')}."
    return interpretation.rstrip(".") + "."


def _unknown_sentence(item: Mapping[str, Any]) -> str:
    explanation = _text(item.get("explanation"), "unknown.explanation")
    normalized = explanation.strip()
    if normalized.lower().startswith(("i ", "i'm", "i cannot", "i can't")):
        return normalized.rstrip(".") + "."
    return f"I still can't fully rely on this point: {normalized.rstrip('.')}."


def _counter_sentence(item: Mapping[str, Any]) -> str:
    interpretation = _text(item.get("interpretation"), "counter.interpretation")
    economic = item.get("economic_assessment")
    if isinstance(economic, str) and economic.strip():
        return (
            f"{interpretation.rstrip('.')}. "
            f"{economic.strip()[0].upper() + economic.strip()[1:].rstrip('.')}."
        )
    return interpretation.rstrip(".") + "."


def _conviction_sentence(contract: Mapping[str, Any]) -> str:
    conviction = _state(contract.get("conviction"))
    evidence = _state(contract.get("evidence_quality"))
    return f"My conviction is {conviction}, and the evidence quality is {evidence}."


def _change_line(contract: Mapping[str, Any]) -> str:
    conditions = _list(
        contract.get("what_would_change_my_mind"),
        "what_would_change_my_mind",
    )
    phrases = [
        _text(
            _mapping(item, "change_condition").get("condition"),
            "change_condition.condition",
        ).rstrip(".")
        for item in conditions[:4]
    ]
    return "What would change my mind: " + "; ".join(phrases) + "."


def _evidence_profile_lines(contract: Mapping[str, Any]) -> list[str]:
    lines = ["Evidence profile:"]
    for item in _list(contract.get("evidence_profile"), "evidence_profile"):
        value = _mapping(item, "evidence_profile item")
        dimension = _text(value.get("dimension"), "evidence_profile.dimension")
        state = _state(value.get("state"))
        lines.append(f"- {dimension.replace('_', ' ').title()}: {state}")
    return lines


def _technical_lines(
    contract: Mapping[str, Any],
    response_decision: Mapping[str, Any],
) -> list[str]:
    technical = _mapping(contract.get("technical_detail"), "technical_detail")
    if technical.get("available") is not True:
        return []
    source_technical = _mapping(
        response_decision.get("technical_detail"),
        "response_decision.technical_detail",
    )
    lines = ["Technical evidence:"]
    reference = technical.get("reference")
    if isinstance(reference, str) and reference.strip():
        lines.append(f"- Evidence reference: {reference.strip()}")
    source_contract = source_technical.get("source_contract")
    if isinstance(source_contract, str) and source_contract.strip():
        lines.append(f"- Source contract: {source_contract.strip()}")
    lines.append("- Facts remain Chain Scout / CMIS authority; this renderer does not recompute them.")
    lines.append("- Analysis only. Execution remains unauthorized.")
    return lines


def render_human_response(
    response_decision: Mapping[str, Any],
    *,
    response_depth: str | None = None,
) -> str:
    """Render validated Human ROBERTA prose from one protected response-decision."""

    contract = build_public_human_response_contract(
        response_decision,
        response_depth=response_depth,
    )
    depth = _text(contract.get("response_depth"), "response_depth")

    lines = [_text(contract.get("direct_answer"), "direct_answer"), ""]

    lines.append(_primary_sentence(contract))

    supporting = _list(
        contract.get("supporting_observations"),
        "supporting_observations",
    )
    support_limit = 1 if depth == "quick" else min(3, len(supporting))
    for item in supporting[:support_limit]:
        lines.append(_supporting_sentence(_mapping(item, "supporting observation")))

    unknowns = _list(contract.get("important_unknowns"), "important_unknowns")
    if depth == "quick":
        if unknowns:
            lines.extend(["", _unknown_sentence(_mapping(unknowns[0], "important unknown"))])
        lines.extend(["", _conviction_sentence(contract)])
        return "\n".join(lines).strip()

    counter_status = _text(
        contract.get("counterevidence_status"),
        "counterevidence_status",
    )
    counter = _list(contract.get("counterevidence"), "counterevidence")
    if counter_status == "present" and counter:
        lines.extend(["", "There is some evidence on the other side:"])
        for item in counter[:2]:
            lines.append(_counter_sentence(_mapping(item, "counterevidence item")))

    if unknowns:
        lines.extend(["", "What I'm still uncertain about:"])
        for item in unknowns[:3]:
            lines.append(_unknown_sentence(_mapping(item, "important unknown")))

    lines.extend(["", _conviction_sentence(contract), "", _change_line(contract)])

    if depth == "deep_dive":
        lines.extend(["", *_evidence_profile_lines(contract)])
        technical_lines = _technical_lines(contract, response_decision)
        if technical_lines:
            lines.extend(["", *technical_lines])

    return "\n".join(lines).strip()


__all__ = [
    "HUMAN_RENDERER_CONTRACT",
    "HUMAN_RESPONSE_DECISION_CONTRACT",
    "HumanResponseRenderError",
    "build_public_human_response_contract",
    "render_human_response",
]
