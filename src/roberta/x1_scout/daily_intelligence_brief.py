"""Typed X1 Daily Intelligence Brief foundation for ROBERTA #412.

This module projects the already accepted non-promoted CMIS
x1_intelligence_brief_inputs/v1 foundation into an X1 Scout product view and a
ROBERTA Decision Object input contract. It performs no provider access, no
market/risk arithmetic, no event-time substitution, no free-form LLM synthesis,
and no execution.

The accepted CMIS foundation is intentionally non-runtime here. Live X1 Scout
reliance remains blocked on CMIS #637.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any


CMIS_BRIEF_INPUTS_CONTRACT = "x1_intelligence_brief_inputs/v1"
X1_DAILY_BRIEF_CONTRACT = "x1_daily_intelligence_brief/v1"
ROBERTA_DAILY_BRIEF_DECISION_INPUT_CONTRACT = (
    "roberta_daily_intelligence_brief_decision_input/v1"
)
ROBERTA_DAILY_BRIEF_CLAIM_INTEGRITY_CONTRACT = (
    "roberta_daily_intelligence_brief_claim_integrity/v1"
)

_BASE58 = frozenset(
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
)
_ALLOWED_PRIORITIES = {
    "persistent_warning",
    "large_verified_activity",
    "new_verified_observation",
    "informational",
}
_ALLOWED_SOURCE_SERVICES = {
    "concentration_warning_intelligence",
    "large_trade_discovery",
    "discovery_intelligence",
}
_EXPECTED_SOURCE_CONTRACTS = {
    "concentration_warning_intelligence": "concentration_warning_intelligence/v1",
    "large_trade_discovery": "large_trade_discovery/v1",
    "discovery_intelligence": "discovery_intelligence/v1",
}
_LARGE_TRADE_REQUIRED_FALSE = {
    "global_x1_dex_trade_ranking_authorized",
    "wallet_owner_identity_inference_authorized",
    "whale_insider_manipulator_label_authorized",
    "intent_inference_authorized",
    "coordinated_wallet_inference_authorized",
    "whole_market_price_impact_claim_authorized",
    "volume_causality_claim_authorized",
    "automatic_risk_conclusion_authorized",
    "trade_recommendation_authorized",
}


class X1DailyIntelligenceBriefContractError(ValueError):
    """Raised when CMIS brief inputs cannot satisfy ROBERTA #412."""


def _mapping(name: str, value: Any) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise X1DailyIntelligenceBriefContractError(f"{name} must be a mapping")
    return value


def _sequence(name: str, value: Any) -> list[Any]:
    if not isinstance(value, Sequence) or isinstance(
        value, (str, bytes, bytearray, Mapping)
    ):
        raise X1DailyIntelligenceBriefContractError(f"{name} must be a list")
    return list(value)


def _text(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise X1DailyIntelligenceBriefContractError(
            f"{name} must be normalized non-empty text"
        )
    return value


def _mint(value: Any) -> str:
    text = _text("subject mint", value)
    if not (32 <= len(text) <= 44 and all(char in _BASE58 for char in text)):
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief requires exact address-shaped X1 mint subjects"
        )
    return text


def _require_false(name: str, value: Any) -> None:
    if value is not False:
        raise X1DailyIntelligenceBriefContractError(f"{name} must remain false")


def _require_true(name: str, value: Any) -> None:
    if value is not True:
        raise X1DailyIntelligenceBriefContractError(f"{name} must remain true")


def _validated_coverage(value: Any, *, item_count: int) -> dict[str, Any]:
    coverage = deepcopy(dict(_mapping("coverage", value)))
    _require_true(
        "coverage.component_response_matrix_complete",
        coverage.get("component_response_matrix_complete"),
    )
    _require_false(
        "coverage.complete_x1_ecosystem_coverage_verified",
        coverage.get("complete_x1_ecosystem_coverage_verified"),
    )
    if coverage.get("included_item_count") != item_count:
        raise X1DailyIntelligenceBriefContractError(
            "coverage included_item_count must match item count"
        )
    for key in (
        "requested_subject_count",
        "resolved_subject_count",
        "requested_service_count",
        "included_item_count",
        "outside_window_item_count",
        "duplicate_exact_component_responses_collapsed",
    ):
        value = coverage.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise X1DailyIntelligenceBriefContractError(
                f"coverage {key} must be a non-negative integer"
            )
    if coverage["resolved_subject_count"] != coverage["requested_subject_count"]:
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief foundation requires every requested subject to resolve exactly"
        )
    if coverage.get("window_end_exclusive") is not True:
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief must preserve start-inclusive/end-exclusive window semantics"
        )
    for key in (
        "input_service_classes_requested",
        "input_service_classes_evaluated",
        "partial_service_classes",
        "unavailable_service_classes",
        "error_or_ambiguous_service_classes",
    ):
        values = _sequence(f"coverage.{key}", coverage.get(key))
        if any(not isinstance(item, str) or not item for item in values):
            raise X1DailyIntelligenceBriefContractError(
                f"coverage.{key} must contain service names"
            )
    if sorted(coverage["input_service_classes_requested"]) != sorted(
        coverage["input_service_classes_evaluated"]
    ):
        raise X1DailyIntelligenceBriefContractError(
            "requested and evaluated Daily Brief service classes must match"
        )
    return coverage


def _validate_item(item: Mapping[str, Any], *, subjects: set[str]) -> dict[str, Any]:
    result = deepcopy(dict(item))
    _text("brief_item_id", result.get("brief_item_id"))
    subject = _mint(result.get("subject_mint"))
    if subject not in subjects:
        raise X1DailyIntelligenceBriefContractError(
            "brief item subject is outside the accepted subject set"
        )

    service = _text("brief item source_service", result.get("source_service"))
    if service not in _ALLOWED_SOURCE_SERVICES:
        raise X1DailyIntelligenceBriefContractError(
            "brief item source service is not accepted for Daily Brief v1"
        )
    if result.get("source_contract_version") != _EXPECTED_SOURCE_CONTRACTS[service]:
        raise X1DailyIntelligenceBriefContractError(
            f"brief item source contract mismatch for {service}"
        )
    priority = result.get("priority")
    if priority not in _ALLOWED_PRIORITIES:
        raise X1DailyIntelligenceBriefContractError(
            "brief item priority is not accepted"
        )
    if isinstance(result.get("priority_rank"), bool) or not isinstance(
        result.get("priority_rank"), int
    ):
        raise X1DailyIntelligenceBriefContractError(
            "brief item priority_rank must be integer"
        )
    _text("brief item fact_time", result.get("fact_time"))
    _text("brief item event_key", result.get("event_key"))
    _mapping("brief item facts", result.get("facts"))
    _require_true(
        "brief item proof_strength_separate_from_risk",
        result.get("proof_strength_separate_from_risk"),
    )
    _require_false(
        "brief item priority_is_risk_severity",
        result.get("priority_is_risk_severity"),
    )
    _require_false(
        "brief item complete_x1_ecosystem_coverage_verified",
        result.get("complete_x1_ecosystem_coverage_verified"),
    )
    _require_false(
        "brief item execution_authorized",
        result.get("execution_authorized"),
    )

    facts = _mapping("brief item facts", result.get("facts"))
    if service == "concentration_warning_intelligence":
        _require_false(
            "warning_level_is_risk_severity",
            facts.get("warning_level_is_risk_severity"),
        )
        if facts.get("risk_interpretation") is not None:
            raise X1DailyIntelligenceBriefContractError(
                "Daily Brief must not add concentration risk interpretation"
            )
    elif service == "large_trade_discovery":
        if facts.get("real_world_wallet_owner_verified") is not False:
            raise X1DailyIntelligenceBriefContractError(
                "Daily Brief must not promote real-world wallet ownership"
            )
        boundaries = _mapping(
            "large-trade evidence boundaries", facts.get("evidence_boundaries")
        )
        for field in _LARGE_TRADE_REQUIRED_FALSE:
            _require_false(
                f"large-trade evidence boundary {field}",
                boundaries.get(field),
            )
    elif service == "discovery_intelligence":
        if facts.get("token_launch_time") is not None:
            raise X1DailyIntelligenceBriefContractError(
                "Daily Brief must not promote Discovery first observation to launch time"
            )
        _require_false(
            "token_launch_time_verified",
            facts.get("token_launch_time_verified"),
        )
        discovery_coverage = _mapping(
            "Discovery item coverage", facts.get("coverage")
        )
        _require_false(
            "Discovery continuous_coverage_verified",
            discovery_coverage.get("continuous_coverage_verified"),
        )
        _require_false(
            "Discovery archive_completeness_verified",
            discovery_coverage.get("archive_completeness_verified"),
        )
    return result


def validate_cmis_brief_inputs_foundation(value: Any) -> dict[str, Any]:
    """Validate the accepted non-promoted CMIS #635 foundation."""

    source = deepcopy(dict(_mapping("CMIS brief inputs", value)))
    if source.get("contract_version") != CMIS_BRIEF_INPUTS_CONTRACT:
        raise X1DailyIntelligenceBriefContractError(
            "CMIS Daily Brief source contract mismatch"
        )
    if source.get("chain") != "x1":
        raise X1DailyIntelligenceBriefContractError(
            "Daily Intelligence Brief v1 is X1-only"
        )
    _require_true("CMIS brief inputs read_only", source.get("read_only"))
    _require_false(
        "CMIS brief inputs public_service_promoted",
        source.get("public_service_promoted"),
    )
    _require_false(
        "CMIS brief inputs scout_reliance_promoted",
        source.get("scout_reliance_promoted"),
    )
    _require_false(
        "CMIS brief inputs execution_authorized",
        source.get("execution_authorized"),
    )
    _require_false(
        "CMIS brief inputs priority_is_risk_severity",
        source.get("priority_is_risk_severity"),
    )
    _require_true(
        "CMIS brief inputs proof_score_separate_from_risk",
        source.get("proof_score_separate_from_risk"),
    )
    _require_false(
        "CMIS brief inputs missing_evidence_zero_filled",
        source.get("missing_evidence_zero_filled"),
    )
    _require_false(
        "CMIS brief inputs complete_x1_ecosystem_coverage_verified",
        source.get("complete_x1_ecosystem_coverage_verified"),
    )

    subjects = [_mint(item) for item in _sequence("subjects", source.get("subjects"))]
    if not subjects or len(set(subjects)) != len(subjects):
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief subjects must be non-empty and unique"
        )
    requested_services = _sequence(
        "requested_services", source.get("requested_services")
    )
    if sorted(requested_services) != sorted(_ALLOWED_SOURCE_SERVICES):
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief v1 foundation requires the accepted three-service source set"
        )

    window = _mapping("window", source.get("window"))
    _text("window.start", window.get("start"))
    _text("window.end", window.get("end"))
    _require_true("window.end_exclusive", window.get("end_exclusive"))
    duration = window.get("duration_seconds")
    if isinstance(duration, bool) or not isinstance(duration, int):
        raise X1DailyIntelligenceBriefContractError(
            "window duration_seconds must be integer"
        )
    if duration <= 0 or duration > 86400:
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief window must be >0 and <=86400 seconds"
        )

    raw_items = _sequence("items", source.get("items"))
    items = [
        _validate_item(_mapping(f"items[{index}]", raw), subjects=set(subjects))
        for index, raw in enumerate(raw_items)
    ]
    ids = [item["brief_item_id"] for item in items]
    if len(set(ids)) != len(ids):
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief item ids must be unique"
        )
    coverage = _validated_coverage(source.get("coverage"), item_count=len(items))
    if coverage["requested_subject_count"] != len(subjects):
        raise X1DailyIntelligenceBriefContractError(
            "coverage requested_subject_count must match subjects"
        )
    if coverage["requested_service_count"] != len(requested_services):
        raise X1DailyIntelligenceBriefContractError(
            "coverage requested_service_count must match requested_services"
        )
    return source


def _presentation_basis(item: Mapping[str, Any]) -> dict[str, Any]:
    priority = item["priority"]
    if priority == "persistent_warning":
        explanation = (
            "A persistent verified warning is present in the bounded evidence. "
            "This is attention priority, not risk severity."
        )
    elif priority == "large_verified_activity":
        explanation = (
            "A large verified transaction is present in the accepted bounded "
            "market scope. Size alone does not prove ownership, intent, manipulation, or causality."
        )
    elif priority == "new_verified_observation":
        explanation = (
            "CMIS recorded a new verified observation in the bounded Discovery "
            "scope. It is not proof of launch time or complete history."
        )
    else:
        explanation = (
            "A verified informational state is present in the bounded CMIS evidence."
        )
    return {
        "brief_item_id": item["brief_item_id"],
        "priority": priority,
        "basis_type": "roberta_presentation_basis",
        "explanation": explanation,
        "new_chain_fact_added": False,
        "risk_conclusion_added": False,
        "causality_added": False,
    }


def build_x1_daily_intelligence_brief(
    cmis_brief_inputs: Mapping[str, Any],
) -> dict[str, Any]:
    """Project the accepted CMIS foundation into a typed X1 Scout brief."""

    source = validate_cmis_brief_inputs_foundation(cmis_brief_inputs)
    items = deepcopy(list(source["items"]))
    coverage = deepcopy(dict(source["coverage"]))

    evidence = [
        {
            "brief_item_id": item["brief_item_id"],
            "subject_mint": item["subject_mint"],
            "source_service": item["source_service"],
            "source_contract_version": item["source_contract_version"],
            "source_status": item.get("source_status"),
            "fact_time": item["fact_time"],
            "source_freshness": deepcopy(item.get("source_freshness")),
            "source_confidence": deepcopy(item.get("source_confidence") or {}),
            "source_sources": deepcopy(item.get("source_sources") or []),
            "source_warnings": deepcopy(item.get("source_warnings") or []),
            "source_errors": deepcopy(item.get("source_errors") or []),
            "risk": deepcopy(item.get("risk")),
        }
        for item in items
    ]

    unknowns = {
        "complete_x1_ecosystem_coverage_verified": False,
        "partial_service_classes": deepcopy(
            coverage["partial_service_classes"]
        ),
        "unavailable_service_classes": deepcopy(
            coverage["unavailable_service_classes"]
        ),
        "error_or_ambiguous_service_classes": deepcopy(
            coverage["error_or_ambiguous_service_classes"]
        ),
        "outside_window_item_count": coverage["outside_window_item_count"],
        "empty_brief_means_no_activity_on_x1": False,
        "missing_evidence_zero_filled": False,
    }

    watch_next = [
        {
            "brief_item_id": item["brief_item_id"],
            "subject_mint": item["subject_mint"],
            "source_service": item["source_service"],
            "reason": item["priority"],
            "prediction_added": False,
        }
        for item in items
        if item["priority"] in {
            "persistent_warning",
            "large_verified_activity",
            "new_verified_observation",
        }
    ]

    return {
        "contract_version": X1_DAILY_BRIEF_CONTRACT,
        "product": "x1_daily_intelligence_brief",
        "chain": "x1",
        "status": (
            "partial"
            if (
                coverage["partial_service_classes"]
                or coverage["unavailable_service_classes"]
                or coverage["error_or_ambiguous_service_classes"]
            )
            else "ok"
        ),
        "subjects": deepcopy(list(source["subjects"])),
        "window": deepcopy(dict(source["window"])),
        "what_changed": items,
        "why_it_matters_basis": [_presentation_basis(item) for item in items],
        "evidence": evidence,
        "unknowns": unknowns,
        "what_to_watch_next": watch_next,
        "coverage": coverage,
        "source_contract": CMIS_BRIEF_INPUTS_CONTRACT,
        "source_brief_inputs_id": source.get("brief_inputs_id"),
        "facts_authority": "chain_scout_cmis",
        "judgment_authority": "roberta",
        "runtime_reliance_authorized": False,
        "public_runtime_dependency": "cmis#637",
        "complete_x1_ecosystem_coverage_verified": False,
        "proof_score_separate_from_risk": True,
        "priority_is_risk_severity": False,
        "execution_authorized": False,
    }


def build_daily_brief_decision_input(
    brief: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the public typed input for protected roberta_decision/v1 synthesis."""

    if not isinstance(brief, Mapping):
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief decision input requires an X1 Daily Brief product"
        )
    if brief.get("contract_version") != X1_DAILY_BRIEF_CONTRACT:
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief decision input source contract mismatch"
        )
    if brief.get("product") != "x1_daily_intelligence_brief":
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief decision input source product mismatch"
        )
    if brief.get("chain") != "x1":
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief decision input is X1-only"
        )
    _require_false(
        "Daily Brief runtime_reliance_authorized",
        brief.get("runtime_reliance_authorized"),
    )
    _require_false(
        "Daily Brief complete_x1_ecosystem_coverage_verified",
        brief.get("complete_x1_ecosystem_coverage_verified"),
    )
    _require_true(
        "Daily Brief proof_score_separate_from_risk",
        brief.get("proof_score_separate_from_risk"),
    )
    _require_false(
        "Daily Brief priority_is_risk_severity",
        brief.get("priority_is_risk_severity"),
    )
    _require_false(
        "Daily Brief execution_authorized",
        brief.get("execution_authorized"),
    )

    return {
        "contract_version": ROBERTA_DAILY_BRIEF_DECISION_INPUT_CONTRACT,
        "workflow": "x1_daily_intelligence_brief",
        "chain": "x1",
        "status": brief.get("status"),
        "subjects": deepcopy(list(brief.get("subjects") or [])),
        "window": deepcopy(dict(_mapping("Daily Brief window", brief.get("window")))),
        "facts": {
            "what_changed": deepcopy(list(brief.get("what_changed") or [])),
        },
        "presentation_basis": deepcopy(
            list(brief.get("why_it_matters_basis") or [])
        ),
        "evidence": deepcopy(list(brief.get("evidence") or [])),
        "unknowns": deepcopy(dict(_mapping("Daily Brief unknowns", brief.get("unknowns")))),
        "watch_candidates": deepcopy(
            list(brief.get("what_to_watch_next") or [])
        ),
        "coverage": deepcopy(dict(_mapping("Daily Brief coverage", brief.get("coverage")))),
        "source_contracts": [X1_DAILY_BRIEF_CONTRACT, CMIS_BRIEF_INPUTS_CONTRACT],
        "facts_authority": "chain_scout_cmis",
        "judgment_authority": "roberta",
        "decision_policy_applied": False,
        "claim_integrity_required": True,
        "runtime_reliance_authorized": False,
        "complete_x1_ecosystem_coverage_verified": False,
        "execution_authorized": False,
    }


def build_daily_brief_claim_integrity(
    decision_input: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate Daily Brief truth boundaries before protected narrative synthesis."""

    if not isinstance(decision_input, Mapping):
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief Claim Integrity requires a decision input"
        )
    if (
        decision_input.get("contract_version")
        != ROBERTA_DAILY_BRIEF_DECISION_INPUT_CONTRACT
    ):
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief Claim Integrity source contract mismatch"
        )
    if decision_input.get("facts_authority") != "chain_scout_cmis":
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief facts authority must remain chain_scout_cmis"
        )
    if decision_input.get("judgment_authority") != "roberta":
        raise X1DailyIntelligenceBriefContractError(
            "Daily Brief judgment authority must remain roberta"
        )
    _require_false(
        "Daily Brief decision policy_applied",
        decision_input.get("decision_policy_applied"),
    )
    _require_true(
        "Daily Brief claim_integrity_required",
        decision_input.get("claim_integrity_required"),
    )
    _require_false(
        "Daily Brief decision runtime_reliance_authorized",
        decision_input.get("runtime_reliance_authorized"),
    )
    _require_false(
        "Daily Brief decision complete_x1_ecosystem_coverage_verified",
        decision_input.get("complete_x1_ecosystem_coverage_verified"),
    )
    _require_false(
        "Daily Brief decision execution_authorized",
        decision_input.get("execution_authorized"),
    )

    facts = _mapping("Daily Brief decision facts", decision_input.get("facts"))
    for index, raw in enumerate(
        _sequence("Daily Brief decision what_changed", facts.get("what_changed"))
    ):
        _validate_item(
            _mapping(f"Daily Brief decision item[{index}]", raw),
            subjects=set(decision_input.get("subjects") or []),
        )

    presentation = _sequence(
        "Daily Brief presentation_basis",
        decision_input.get("presentation_basis"),
    )
    for index, raw in enumerate(presentation):
        row = _mapping(f"presentation_basis[{index}]", raw)
        if row.get("basis_type") != "roberta_presentation_basis":
            raise X1DailyIntelligenceBriefContractError(
                "Daily Brief presentation basis must remain explicitly ROBERTA-owned"
            )
        _require_false(
            f"presentation_basis[{index}].new_chain_fact_added",
            row.get("new_chain_fact_added"),
        )
        _require_false(
            f"presentation_basis[{index}].risk_conclusion_added",
            row.get("risk_conclusion_added"),
        )
        _require_false(
            f"presentation_basis[{index}].causality_added",
            row.get("causality_added"),
        )

    unknowns = _mapping(
        "Daily Brief decision unknowns", decision_input.get("unknowns")
    )
    _require_false(
        "unknowns.complete_x1_ecosystem_coverage_verified",
        unknowns.get("complete_x1_ecosystem_coverage_verified"),
    )
    _require_false(
        "unknowns.empty_brief_means_no_activity_on_x1",
        unknowns.get("empty_brief_means_no_activity_on_x1"),
    )
    _require_false(
        "unknowns.missing_evidence_zero_filled",
        unknowns.get("missing_evidence_zero_filled"),
    )

    return {
        "contract_version": ROBERTA_DAILY_BRIEF_CLAIM_INTEGRITY_CONTRACT,
        "status": "PASS",
        "workflow": "x1_daily_intelligence_brief",
        "source_contracts": deepcopy(list(decision_input["source_contracts"])),
        "facts_authority": "chain_scout_cmis",
        "judgment_authority": "roberta",
        "checks": {
            "whole_x1_coverage_not_claimed": True,
            "empty_brief_not_promoted_to_no_x1_activity": True,
            "priority_separate_from_risk": True,
            "proof_score_separate_from_risk": True,
            "wallet_ownership_not_inferred": True,
            "whale_insider_manipulation_not_inferred": True,
            "causality_not_inferred": True,
            "discovery_first_observation_not_launch_time": True,
            "presentation_basis_not_promoted_to_chain_fact": True,
            "runtime_reliance_not_authorized_before_cmis_637": True,
        },
        "provider_truth_certified": False,
        "execution_authorized": False,
    }


def render_x1_daily_intelligence_brief_text(brief: Mapping[str, Any]) -> str:
    """Render a concise deterministic preview; protected ROBERTA owns final prose."""

    if brief.get("contract_version") != X1_DAILY_BRIEF_CONTRACT:
        raise X1DailyIntelligenceBriefContractError(
            "unsupported X1 Daily Intelligence Brief contract"
        )
    _require_false(
        "Daily Brief execution_authorized",
        brief.get("execution_authorized"),
    )
    subjects = ", ".join(str(item) for item in brief.get("subjects") or [])
    lines = [
        "X1 DAILY INTELLIGENCE BRIEF",
        f"Status: {str(brief.get('status') or 'unknown').upper()}",
        f"Subjects: {subjects or 'none'}",
        "",
        "WHAT CHANGED",
    ]
    items = list(brief.get("what_changed") or [])
    if not items:
        lines.append(
            "No supported verified brief item fell inside this exact bounded scope."
        )
    else:
        for item in items:
            lines.append(
                f"- {item.get('priority')}: {item.get('source_service')} "
                f"at {item.get('fact_time')} [{item.get('brief_item_id')}]"
            )

    lines.extend(["", "WHY IT MATTERS"])
    for row in brief.get("why_it_matters_basis") or []:
        lines.append(f"- {row.get('explanation')}")

    lines.extend([
        "",
        "EVIDENCE",
        f"Verified brief items: {len(brief.get('evidence') or [])}",
        "",
        "WHAT IS UNKNOWN / INCOMPLETE",
        "Complete X1 ecosystem coverage: NOT VERIFIED",
        "An empty bounded brief does not mean nothing happened on X1.",
        "",
        "WHAT TO WATCH NEXT",
    ])
    watch = list(brief.get("what_to_watch_next") or [])
    if not watch:
        lines.append("- No bounded watch candidate from this brief.")
    else:
        for row in watch:
            lines.append(
                f"- {row.get('source_service')} / {row.get('reason')} / "
                f"{row.get('brief_item_id')}"
            )
    lines.extend([
        "",
        "Live runtime reliance: NOT AUTHORIZED until CMIS #637 is accepted.",
        "Execution authorized: false",
    ])
    return "\n".join(lines)


__all__ = [
    "CMIS_BRIEF_INPUTS_CONTRACT",
    "ROBERTA_DAILY_BRIEF_CLAIM_INTEGRITY_CONTRACT",
    "ROBERTA_DAILY_BRIEF_DECISION_INPUT_CONTRACT",
    "X1_DAILY_BRIEF_CONTRACT",
    "X1DailyIntelligenceBriefContractError",
    "build_daily_brief_claim_integrity",
    "build_daily_brief_decision_input",
    "build_x1_daily_intelligence_brief",
    "render_x1_daily_intelligence_brief_text",
    "validate_cmis_brief_inputs_foundation",
]
