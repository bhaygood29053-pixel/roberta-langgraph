"""Deterministic help text for CMIS risk results."""

from collections.abc import Mapping
from typing import Any


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _reason_suffix(reasons: list[str], flags: list[str]) -> str:
    parts: list[str] = []
    if reasons:
        parts.append("Reasons: " + "; ".join(reasons))
    if flags:
        parts.append("Flags: " + ", ".join(flags))
    return " ".join(parts)


def build_risk_help(
    risk: Mapping[str, Any] | None,
    confidence: Mapping[str, Any] | None = None,
) -> dict[str, object] | None:
    """Build presentation-neutral explanations without redefining CMIS policy."""

    if risk is None:
        return None

    confidence_data = confidence or {}
    recommendation = risk.get("recommendation", risk.get("outcome"))
    reasons = _string_list(risk.get("reasons"))
    flags = _string_list(risk.get("flags"))

    recommendation_help: dict[str, object] = {
        "value": recommendation,
        "reasons": reasons,
        "flags": flags,
    }
    if recommendation is None:
        recommendation_help["meaning"] = (
            "No deterministic CMIS recommendation token was returned."
        )
    else:
        suffix = _reason_suffix(reasons, flags)
        recommendation_help["meaning"] = (
            f"CMIS returned recommendation/status {recommendation}."
            + (f" {suffix}" if suffix else "")
        )

    score = risk.get("score")
    score_verified = risk.get("score_verified")
    score_reason = risk.get("score_reason")
    score_help: dict[str, object] = {
        "value": score,
        "verified": score_verified,
        "reason": score_reason,
    }
    if score is None or score_verified is not True:
        detail = (
            f" Reason: {score_reason}."
            if isinstance(score_reason, str) and score_reason.strip()
            else ""
        )
        score_help["meaning"] = (
            "No verified numeric risk score is available."
            f"{detail} Do not convert the categorical recommendation into a number."
        )
    else:
        score_help["meaning"] = (
            f"CMIS returned verified numeric risk score {score}. "
            "Interpret the number only according to CMIS policy; do not remap its scale."
        )

    risk_confidence = risk.get("confidence")
    if isinstance(risk_confidence, Mapping):
        merged_confidence: Mapping[str, Any] = risk_confidence
    else:
        merged_confidence = confidence_data

    verified_checks = merged_confidence.get("verified_checks")
    total_checks = merged_confidence.get("total_checks")
    ratio = merged_confidence.get("verification_ratio")
    level = merged_confidence.get("level")
    confidence_help: dict[str, object] = {
        "level": level,
        "verified_checks": verified_checks,
        "total_checks": total_checks,
        "verification_ratio": ratio,
    }
    if (
        isinstance(verified_checks, int)
        and not isinstance(verified_checks, bool)
        and isinstance(total_checks, int)
        and not isinstance(total_checks, bool)
        and total_checks > 0
    ):
        pct = (
            f"{float(ratio) * 100:.0f}%"
            if isinstance(ratio, (int, float)) and not isinstance(ratio, bool)
            else "ratio unavailable"
        )
        confidence_help["meaning"] = (
            f"{verified_checks} of {total_checks} verification checks were satisfied "
            f"({pct}). This measures evidence coverage, not the probability that the asset is safe."
        )
    elif level is not None:
        confidence_help["meaning"] = (
            f"CMIS confidence level is {level}. Verification-count details were not returned. "
            "Confidence describes evidence coverage/verification, not the probability that the asset is safe."
        )
    else:
        confidence_help["meaning"] = (
            "CMIS did not return enough confidence metadata to explain verification coverage."
        )

    components_help: dict[str, object] = {}
    components = risk.get("components")
    if isinstance(components, Mapping):
        for name, raw_component in components.items():
            if not isinstance(name, str) or not isinstance(raw_component, Mapping):
                continue
            status = raw_component.get("status")
            component_reasons = _string_list(raw_component.get("reasons"))
            component_flags = _string_list(raw_component.get("flags"))
            suffix = _reason_suffix(component_reasons, component_flags)
            meaning = (
                f"CMIS component status is {status}."
                if status is not None
                else "CMIS did not return a component status."
            )
            if suffix:
                meaning += f" {suffix}"
            components_help[name] = {
                "status": status,
                "reasons": component_reasons,
                "flags": component_flags,
                "meaning": meaning,
            }

    return {
        "recommendation": recommendation_help,
        "score": score_help,
        "confidence": confidence_help,
        "components": components_help,
    }
