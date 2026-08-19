"""Deterministic runtime brief for recommendation-style Oracle synthesis.

The brief does not calculate market facts or write the user's recommendation.
It carries the accepted decision-quality contract into the *post-specialist*
Oracle call so ordinary recommendation families do not rely only on a global
prompt. Chain Scouts/CMIS remain authoritative for every current fact.
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
        "- Then give only 2-4 material evidence-backed reasons that directly answer the user.\n"
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


__all__ = [
    "build_decision_synthesis_system_message",
    "technical_decision_detail_requested",
]
