"""Deterministic help text for CMIS envelope statuses."""

from collections.abc import Mapping
from typing import Any


def build_cmis_status_help(
    service: object,
    status: object,
    confidence: Mapping[str, Any] | None = None,
) -> dict[str, object] | None:
    """Explain CMIS service completeness without redefining risk outcomes."""

    service_text = str(service or "").strip()
    status_text = str(status or "").strip().lower()
    if not status_text:
        return None

    confidence_data = confidence or {}
    verified = confidence_data.get("verified_checks")
    total = confidence_data.get("total_checks")
    counts = ""
    if (
        isinstance(verified, int)
        and not isinstance(verified, bool)
        and isinstance(total, int)
        and not isinstance(total, bool)
        and total > 0
    ):
        incomplete = max(total - verified, 0)
        counts = (
            f" {verified} of {total} verification checks are satisfied"
            f"; {incomplete} remain incomplete."
        )

    if status_text == "ok":
        meaning = (
            f"CMIS completed {service_text or 'the requested service'} with its "
            "required verification checks complete."
        )
        if service_text in {"risk_check", "pre_trade_check"}:
            meaning += (
                " Service status describes evidence completeness, not the risk "
                "recommendation; an authoritative WARN or BLOCK can still have "
                "CMIS status ok."
            )
    elif status_text == "partial":
        meaning = (
            f"CMIS completed {service_text or 'the requested service'}, but one or "
            "more verification checks are incomplete."
            f"{counts}"
        )
        if service_text in {"risk_check", "pre_trade_check"}:
            meaning += (
                " Service status describes evidence completeness, not the risk "
                "recommendation; a fully verified WARN or BLOCK can still have "
                "CMIS status ok."
            )
        else:
            meaning += " See confidence and warnings for the incomplete evidence."
    elif status_text == "unavailable":
        meaning = (
            f"CMIS could not produce a usable {service_text or 'service'} result "
            "because required verified input or a provider dependency was unavailable."
        )
    elif status_text == "ambiguous":
        meaning = (
            "CMIS could not uniquely resolve the requested asset. No single asset "
            "result should be assumed until the identity is disambiguated."
        )
    elif status_text == "error":
        meaning = (
            f"CMIS encountered a validation or service error while processing "
            f"{service_text or 'the request'}. Treat the requested result as unavailable."
        )
    else:
        meaning = (
            f"CMIS returned service status {status_text}. No deterministic status "
            "definition is registered in Roberta for this value."
        )

    return {
        "service": service_text or None,
        "status": status_text,
        "meaning": meaning,
    }
