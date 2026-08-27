"""Deterministic runtime contracts for recommendation-style Oracle synthesis.

These helpers do not calculate market facts or write the user's recommendation.
They carry the accepted decision-quality contract into the *post-specialist*
Oracle call and reject only obvious presentation failures such as raw service
dumps or orchestration-first prose. Chain Scouts/CMIS remain authoritative for
every current fact and deterministic conclusion.
"""

from __future__ import annotations

from roberta.recommendation_policy import recommendation_evidence_plan


_TECHNICAL_DETAIL_CUES = (
    "technical",
    "details",
    "detail",
    "sources",
    "source",
    "verification",
    "verify",
    "raw",
    "receipt",
    "provenance",
    "mint address",
)

_DIAGNOSTIC_FIRST_PREFIXES = (
    "cmis",
    "x1 scout",
    "solana scout",
    "liquidity scout",
    "market service:",
    "service:",
    "status:",
    "verified price:",
    "i have the results from",
    "let me synthesize",
    "the specialist report",
    "the scout returned",
    "```",
)


def technical_decision_detail_requested(objective: object) -> bool:
    """Return whether the user explicitly asked for deeper evidence detail."""

    text = " ".join(str(objective or "").strip().lower().split())
    return bool(text) and any(cue in text for cue in _TECHNICAL_DETAIL_CUES)


def build_decision_synthesis_system_message(objective: object) -> str | None:
    """Build a task-specific, non-authorizing post-Scout synthesis contract.

    ``None`` means the request is not a recognized recommendation family and the
    ordinary Oracle path remains unchanged. The returned text is instructions for
    presentation only; it never promotes evidence, computes risk, or authorizes a
    pre-trade/execution operation.
    """

    plan = recommendation_evidence_plan(objective)
    intent = str(plan["intent"])
    if intent == "general":
        return None

    required_services = ", ".join(str(item) for item in plan["required_services"]) or "none"
    evidence_categories = ", ".join(
        str(item) for item in plan["required_evidence_categories"]
    ) or "none"
    technical_requested = technical_decision_detail_requested(objective)
    full_assessment = intent == "full_assessment"
    answer_shape = (
        "Present a structured full assessment covering asset identity/scope, current market, "
        "ecosystem position/rank, tokenomics, all-available verified history, Risk, Evidence "
        "quality, and material limitations. Do not compress the assessment into only 2-4 reasons."
        if full_assessment
        else (
            "Then give only 2-4 material evidence-backed reasons that directly answer the user."
        )
    )
    detail_mode = (
        "The user explicitly requested technical/evidence detail, so fuller provenance, "
        "timestamps, source/conflict detail, and diagnostic fields may be shown when useful."
        if technical_requested
        else
        "Use progressive disclosure: do not dump raw envelopes, receipt IDs, provider codes, "
        "source lists, raw timestamps, or technical diagnostics unless they materially change "
        "the answer."
    )

    return (
        "Deterministic Roberta decision-synthesis contract for this post-specialist answer:\n"
        f"- recognized_intent: {intent}\n"
        f"- required_evidence_services: {required_services}\n"
        f"- required_evidence_categories: {evidence_categories}\n"
        "- Lead with the recommendation, conclusion, or blocker immediately; do not lead with "
        "CMIS/Scout diagnostics or orchestration narration.\n"
        f"- {answer_shape}\n"
        "- State Risk and Evidence quality as separate dimensions. Do not infer a risk level "
        "from PASS/WARN/BLOCK, proof strength, liquidity, volume, or missing fields.\n"
        "- Surface important unknown, stale, conflicting, ambiguous, unavailable, or insufficient "
        "evidence that could change the decision. Missing evidence remains unknown, never zero.\n"
        "- Preserve every authoritative CMIS fact/status/warning/conflict/timestamp/provenance/"
        "unavailable state that you choose to surface; never recalculate, reconcile, strengthen, "
        "weaken, or replace a deterministic conclusion.\n"
        f"- {detail_mode}\n"
        "- This synthesis is read-only and non-authorizing. It does not grant pre_trade_check, "
        "transaction construction, signing, broadcasting, custody, autonomous execution, or value "
        "movement authority.\n"
        "- User -> Roberta -> Chain Scout -> CMIS -> Chain Provider remains the authority path."
    )


def _risk_evidence_dimensions_disclosed(content: str) -> bool:
    normalized = " ".join(content.lower().split())
    return "risk" in normalized and "evidence quality" in normalized


def decision_response_violation(objective: object, content: object) -> str | None:
    """Detect clear violations of the normal recommendation presentation contract.

    This remains conservative about writing style and substantive correctness. It
    only enforces structural presentation requirements that are already part of
    the accepted Decision Quality contract. Technical/raw requests are exempt
    because the user explicitly asked for deeper diagnostics.
    """

    plan = recommendation_evidence_plan(objective)
    if plan["intent"] == "general" or technical_decision_detail_requested(objective):
        return None
    if not isinstance(content, str) or not content.strip():
        return "empty_decision_response"

    stripped = content.lstrip()
    if stripped.startswith(("{", "[")):
        return "raw_service_dump"

    first_line = next(
        (line.strip().lower() for line in stripped.splitlines() if line.strip()),
        "",
    )
    if any(first_line.startswith(prefix) for prefix in _DIAGNOSTIC_FIRST_PREFIXES):
        return "diagnostic_or_orchestration_first"
    if not _risk_evidence_dimensions_disclosed(stripped):
        return "risk_evidence_separation_not_disclosed"
    return None


def build_decision_retry_system_message(violation: str) -> str:
    """Return one deterministic correction instruction for a decision-quality violation."""

    stale_instruction = (
        " The specialist evidence explicitly failed freshness verification. Explicitly tell the "
        "user that the evidence is stale or not fresh; do not soften that into merely saying live "
        "data is unavailable or that current facts are missing."
        if violation == "stale_evidence_not_disclosed"
        else ""
    )
    separation_instruction = (
        " Explicitly include the separate user-facing dimensions `Risk:` and `Evidence quality:`. "
        "If either dimension is unavailable, say so without inferring a value from the other."
        if violation == "risk_evidence_separation_not_disclosed"
        else ""
    )
    return (
        "The previous recommendation draft violated Roberta's deterministic decision-presentation "
        f"contract ({violation}). Rewrite the answer once using the same specialist evidence. "
        "Lead with the recommendation/conclusion/blocker, then 2-4 material reasons, keep Risk "
        "separate from Evidence quality, surface important unknowns, and do not expose raw JSON, "
        "service-envelope diagnostics, planner/orchestration narration, or execution authority. "
        "Do not invent or recalculate any CMIS fact."
        f"{stale_instruction}{separation_instruction}"
    )


def decision_synthesis_failure_text() -> str:
    """Fail closed if two model drafts violate the deterministic presentation contract."""

    return (
        "I have specialist evidence, but I cannot present a recommendation safely because the "
        "response synthesis did not satisfy the decision-quality contract. I will not hide a "
        "material evidence limitation, expose a raw service dump, or invent a cleaner conclusion. "
        "No transaction or execution is authorized."
    )


__all__ = [
    "build_decision_retry_system_message",
    "build_decision_synthesis_system_message",
    "decision_response_violation",
    "decision_synthesis_failure_text",
    "technical_decision_detail_requested",
]
