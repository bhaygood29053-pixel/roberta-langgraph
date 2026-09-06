"""Public Human Response Contract v1.

This module defines deterministic presentation-contract validation only. It does
not call CMIS, Chain Scouts, providers, models, or the protected ROBERTA core,
and it does not create a second opinion/risk engine.

The contract sits conceptually above accepted roberta_decision/v1 and
roberta_opinion/v1 outputs. It may prioritize accepted evidence for human
presentation, but it may not rewrite source facts or authorize execution.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

CONTRACT_VERSION = "roberta_human_response/v1"
OPINION_CONTRACT_VERSION = "roberta_opinion/v1"

RESPONSE_DEPTHS = frozenset({"quick", "normal", "deep_dive"})
COUNTEREVIDENCE_STATUSES = frozenset(
    {"present", "none_material", "unavailable"}
)
EVIDENCE_PROFILE_STATES = frozenset(
    {
        "STRONG",
        "MODERATE",
        "WEAK",
        "LOW",
        "MEDIUM",
        "HIGH",
        "VERY_HIGH",
        "VERIFIED",
        "PARTIAL",
        "UNVERIFIED",
        "UNAVAILABLE",
        "CONFLICTED",
        "STALE",
        "NOT_APPLICABLE",
        "UNKNOWN",
    }
)
_MACHINE_STATUS_TOKENS = frozenset(
    {
        "PASS",
        "WARN",
        "FAIL",
        "UNKNOWN",
        "OK",
        "PARTIAL",
        "UNAVAILABLE",
        "ERROR",
        "VERIFIED",
        "NOT_VERIFIED",
        "NOT VERIFIED",
        "STALE",
        "CONFLICTED",
    }
)


class HumanResponseContractError(ValueError):
    """Raised when a Human Response Contract payload is invalid."""


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise HumanResponseContractError(f"{field} must be an object")
    return value


def _string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HumanResponseContractError(f"{field} must be a non-empty string")
    return value


def _boolean(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise HumanResponseContractError(f"{field} must be boolean")
    return value


def _list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise HumanResponseContractError(f"{field} must be a list")
    return value


def _observation(
    value: Any,
    field: str,
    *,
    source_fact_json: Mapping[str, str] | None,
    require_economic_assessment: bool,
) -> None:
    item = _mapping(value, field)
    fact_ref = _string(item.get("fact_ref"), f"{field}.fact_ref")
    _string(item.get("verification_state"), f"{field}.verification_state")
    _string(item.get("interpretation"), f"{field}.interpretation")

    economic = item.get("economic_assessment")
    if require_economic_assessment:
        economic_text = _string(economic, f"{field}.economic_assessment")
        if economic_text.strip().upper() in _MACHINE_STATUS_TOKENS:
            raise HumanResponseContractError(
                f"{field}.economic_assessment must express human economic meaning, "
                "not reuse a machine verification/status token"
            )
    elif economic is not None:
        economic_text = _string(economic, f"{field}.economic_assessment")
        if economic_text.strip().upper() in _MACHINE_STATUS_TOKENS:
            raise HumanResponseContractError(
                f"{field}.economic_assessment must not reuse a machine status token"
            )

    raw = item.get("source_fact_json")
    if raw is not None:
        if not isinstance(raw, str):
            raise HumanResponseContractError(
                f"{field}.source_fact_json must be an exact JSON string when supplied"
            )
        if source_fact_json is None:
            raise HumanResponseContractError(
                f"{field}.source_fact_json requires source_fact_json validation input"
            )
        if fact_ref not in source_fact_json:
            raise HumanResponseContractError(
                f"{field}.fact_ref is not present in the accepted source-fact map"
            )
        if raw != source_fact_json[fact_ref]:
            raise HumanResponseContractError(
                f"{field}.source_fact_json does not byte-match the accepted source fact"
            )


def _validate_opinion_consistency(
    payload: Mapping[str, Any],
    opinion: Mapping[str, Any] | None,
) -> None:
    if opinion is None:
        return
    if opinion.get("contract_version") != OPINION_CONTRACT_VERSION:
        raise HumanResponseContractError(
            "opinion must be an accepted roberta_opinion/v1 envelope"
        )
    expected = {
        "recommendation": opinion.get("recommendation"),
        "conviction": (
            opinion.get("conviction")
            if opinion.get("conviction") is not None
            else opinion.get("recommendation_strength")
        ),
        "evidence_quality": opinion.get("evidence_quality"),
    }
    for field, value in expected.items():
        if payload.get(field) != value:
            raise HumanResponseContractError(
                f"{field} must exactly preserve the accepted opinion envelope"
            )


def validate_human_response_contract(
    payload: Mapping[str, Any],
    *,
    opinion: Mapping[str, Any] | None = None,
    source_fact_json: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """Validate and return a detached Human Response Contract v1 payload.

    opinion may be supplied to prove that recommendation, conviction, and
    evidence-quality summary exactly match the accepted roberta_opinion/v1
    envelope.

    source_fact_json may be supplied when an observation carries raw
    source_fact_json. The validator compares the strings exactly; no JSON
    parsing, numeric normalization, or rewriting is performed.
    """

    root = _mapping(payload, "payload")
    if root.get("contract_version") != CONTRACT_VERSION:
        raise HumanResponseContractError(
            f"contract_version must be {CONTRACT_VERSION}"
        )

    depth = _string(root.get("response_depth"), "response_depth")
    if depth not in RESPONSE_DEPTHS:
        raise HumanResponseContractError(
            f"response_depth must be one of {sorted(RESPONSE_DEPTHS)}"
        )

    _string(root.get("direct_answer"), "direct_answer")
    _string(root.get("recommendation"), "recommendation")
    _string(root.get("conviction"), "conviction")
    _string(root.get("evidence_quality"), "evidence_quality")

    if root.get("facts_authority") != "chain_scout_cmis":
        raise HumanResponseContractError(
            "facts_authority must remain chain_scout_cmis"
        )
    if root.get("judgment_authority") != "roberta":
        raise HumanResponseContractError("judgment_authority must remain roberta")
    if _boolean(root.get("read_only"), "read_only") is not True:
        raise HumanResponseContractError("read_only must be true")
    if _boolean(root.get("execution_authorized"), "execution_authorized") is not False:
        raise HumanResponseContractError("execution_authorized must be false")
    if (
        _boolean(
            root.get("verification_and_interpretation_separated"),
            "verification_and_interpretation_separated",
        )
        is not True
    ):
        raise HumanResponseContractError(
            "verification_and_interpretation_separated must be true"
        )
    if _boolean(root.get("fact_values_recomputed"), "fact_values_recomputed") is not False:
        raise HumanResponseContractError("fact_values_recomputed must be false")

    _observation(
        root.get("primary_decision_driver"),
        "primary_decision_driver",
        source_fact_json=source_fact_json,
        require_economic_assessment=True,
    )

    supporting = _list(root.get("supporting_observations"), "supporting_observations")
    min_supporting = 1 if depth == "quick" else 2
    if not min_supporting <= len(supporting) <= 4:
        raise HumanResponseContractError(
            f"supporting_observations must contain {min_supporting}-4 items for {depth}"
        )
    for index, item in enumerate(supporting):
        _observation(
            item,
            f"supporting_observations[{index}]",
            source_fact_json=source_fact_json,
            require_economic_assessment=False,
        )

    counter_status = _string(
        root.get("counterevidence_status"), "counterevidence_status"
    )
    if counter_status not in COUNTEREVIDENCE_STATUSES:
        raise HumanResponseContractError(
            "counterevidence_status must be present, none_material, or unavailable"
        )
    counter = _list(root.get("counterevidence"), "counterevidence")
    if len(counter) > 4:
        raise HumanResponseContractError("counterevidence must contain at most 4 items")
    if counter_status == "present" and not counter:
        raise HumanResponseContractError(
            "counterevidence_status=present requires counterevidence"
        )
    if counter_status != "present" and counter:
        raise HumanResponseContractError(
            "counterevidence must be empty unless counterevidence_status=present"
        )
    for index, item in enumerate(counter):
        _observation(
            item,
            f"counterevidence[{index}]",
            source_fact_json=source_fact_json,
            require_economic_assessment=False,
        )

    unknowns = _list(root.get("important_unknowns"), "important_unknowns")
    if len(unknowns) > 5:
        raise HumanResponseContractError(
            "important_unknowns must contain at most 5 items"
        )
    for index, item in enumerate(unknowns):
        unknown = _mapping(item, f"important_unknowns[{index}]")
        _string(unknown.get("unknown_ref"), f"important_unknowns[{index}].unknown_ref")
        _string(unknown.get("explanation"), f"important_unknowns[{index}].explanation")

    profile = _list(root.get("evidence_profile"), "evidence_profile")
    min_profile = 1 if depth == "quick" else 2
    if len(profile) < min_profile:
        raise HumanResponseContractError(
            f"evidence_profile must contain at least {min_profile} dimensions for {depth}"
        )
    seen_dimensions: set[str] = set()
    for index, item in enumerate(profile):
        entry = _mapping(item, f"evidence_profile[{index}]")
        dimension = _string(
            entry.get("dimension"), f"evidence_profile[{index}].dimension"
        )
        if dimension in seen_dimensions:
            raise HumanResponseContractError(
                "evidence_profile dimensions must be unique"
            )
        seen_dimensions.add(dimension)
        state = _string(entry.get("state"), f"evidence_profile[{index}].state")
        if state not in EVIDENCE_PROFILE_STATES:
            raise HumanResponseContractError(
                f"evidence_profile[{index}].state is not an accepted profile state"
            )
        _string(
            entry.get("explanation"), f"evidence_profile[{index}].explanation"
        )

    change_conditions = _list(
        root.get("what_would_change_my_mind"), "what_would_change_my_mind"
    )
    if not 1 <= len(change_conditions) <= 5:
        raise HumanResponseContractError(
            "what_would_change_my_mind must contain 1-5 evidence-bound conditions"
        )
    for index, item in enumerate(change_conditions):
        condition = _mapping(item, f"what_would_change_my_mind[{index}]")
        _string(
            condition.get("condition"),
            f"what_would_change_my_mind[{index}].condition",
        )
        fact_refs = _list(
            condition.get("fact_refs"),
            f"what_would_change_my_mind[{index}].fact_refs",
        )
        if not fact_refs:
            raise HumanResponseContractError(
                f"what_would_change_my_mind[{index}].fact_refs must not be empty"
            )
        for ref_index, ref in enumerate(fact_refs):
            _string(
                ref,
                f"what_would_change_my_mind[{index}].fact_refs[{ref_index}]",
            )

    technical = _mapping(root.get("technical_detail"), "technical_detail")
    available = _boolean(technical.get("available"), "technical_detail.available")
    reference = technical.get("reference")
    if available:
        _string(reference, "technical_detail.reference")
    elif reference is not None:
        raise HumanResponseContractError(
            "technical_detail.reference must be null when technical detail is unavailable"
        )

    _validate_opinion_consistency(root, opinion)
    return deepcopy(dict(root))
