"""Presentation projection for the accepted CMIS Instant X1 Scan contract.

This module never recomputes market facts, proof quality, risk, holder
semantics, concentration, or historical coverage. It only projects fields
already returned by CMIS so X1 Scout can expose the flagship scan coherently.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from roberta.cmis.capabilities import INSTANT_X1_SCAN_CONTRACT_VERSION


def build_instant_x1_scan_presentation(
    result: Mapping[str, Any],
) -> dict[str, object] | None:
    """Project the accepted scan payload without changing CMIS semantics."""

    if result.get("service") != "instant_x1_scan":
        return None
    if result.get("status") not in {"ok", "partial"}:
        return None
    data = result.get("data")
    if not isinstance(data, Mapping):
        return None
    if data.get("contract_version") != INSTANT_X1_SCAN_CONTRACT_VERSION:
        return None

    sections = data.get("sections")
    limitations = data.get("limitations")
    if not isinstance(sections, Mapping) or not isinstance(limitations, list):
        return None

    projected_sections: dict[str, object] = {}
    for name in (
        "identity",
        "market",
        "tokenomics",
        "holder_concentration",
        "history",
        "risk",
        "evidence",
    ):
        value = sections.get(name)
        if isinstance(value, Mapping):
            projected_sections[name] = dict(value)

    return {
        "contract_version": data.get("contract_version"),
        "read_only": data.get("read_only"),
        "sections": projected_sections,
        "limitations": list(limitations),
        "execution_authorized": data.get("execution_authorized"),
    }


__all__ = ["build_instant_x1_scan_presentation"]
