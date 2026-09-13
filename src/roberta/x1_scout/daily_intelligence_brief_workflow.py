"""Bounded product workflow for ROBERTA's X1 Daily Intelligence Brief.

The accepted CMIS Daily Brief contract requires one or more exact X1 mint
subjects. A network-level Human request does not provide those subjects, so X1
Scout selects a small deterministic scope from the already-accepted CMIS rank
service, then invokes the existing explicit ``x1_intelligence_brief_inputs``
Scout route.

Rank is used only to choose scope. It is never promoted into Daily Brief facts
or a whole-X1 coverage claim. Missing/invalid subject evidence fails closed.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from roberta.cmis.x1_intelligence_brief import SUPPORTED_COMPONENT_SERVICES


X1_DAILY_BRIEF_SCOPE_SELECTION_CONTRACT = (
    "x1_daily_intelligence_brief_scope_selection/v1"
)
DEFAULT_DAILY_BRIEF_SUBJECT_LIMIT = 5

_BASE58 = frozenset(
    "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
)


def _exact_x1_mint(value: object) -> str | None:
    text = str(value or "").strip()
    if 32 <= len(text) <= 44 and all(char in _BASE58 for char in text):
        return text
    return None


def _utc_now(value: datetime | None) -> datetime:
    current = value or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("Daily Brief clock must be timezone-aware")
    return current.astimezone(timezone.utc).replace(microsecond=0)


def _today_window(now: datetime | None) -> tuple[str, str]:
    end = _utc_now(now)
    start = end.replace(hour=0, minute=0, second=0)
    if end <= start:
        raise ValueError("Daily Brief today window is not yet positive")
    return (
        start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def _rank_subjects(rank_response: Mapping[str, Any], *, limit: int) -> list[str]:
    if rank_response.get("service") != "rank" or rank_response.get("chain") != "x1":
        return []
    if rank_response.get("status") not in {"ok", "partial"}:
        return []
    data = rank_response.get("data")
    if not isinstance(data, Mapping):
        return []
    rankings = data.get("rankings")
    if not isinstance(rankings, Sequence) or isinstance(
        rankings, (str, bytes, bytearray)
    ):
        return []

    subjects: list[str] = []
    for row in rankings:
        if not isinstance(row, Mapping):
            continue
        mint = _exact_x1_mint(row.get("mint"))
        if mint is None or mint in subjects:
            continue
        subjects.append(mint)
        if len(subjects) >= limit:
            break
    return subjects


def _selection(
    *,
    rank_response: Mapping[str, Any],
    requested_limit: int,
    selected_count: int,
    window_start: str | None,
    window_end: str | None,
    state: str,
    reason: str | None = None,
) -> dict[str, object]:
    value: dict[str, object] = {
        "contract_version": X1_DAILY_BRIEF_SCOPE_SELECTION_CONTRACT,
        "state": state,
        "selector_service": "rank",
        "selector_metric": "volume",
        "selector_basis": "top_verified_24h_volume",
        "requested_subject_limit": requested_limit,
        "selected_subject_count": selected_count,
        "selector_status": rank_response.get("status"),
        "window_basis": "current_utc_day",
        "window_start": window_start,
        "window_end": window_end,
        "complete_x1_ecosystem_coverage_verified": False,
        "rank_is_brief_fact": False,
        "read_only": True,
        "execution_authorized": False,
    }
    if reason:
        value["reason"] = reason
    return value


def _selection_failure_report(
    *,
    objective: str,
    rank_response: Mapping[str, Any],
    selection: Mapping[str, object],
) -> dict[str, object]:
    warnings = list(rank_response.get("warnings") or [])
    warnings.append(
        {
            "code": "x1_daily_brief_subject_selection_unavailable",
            "message": (
                "X1 Scout could not select a bounded set of exact verified X1 mint "
                "subjects for the Daily Brief. No subject was invented."
            ),
        }
    )
    return {
        "specialist": "x1_scout",
        "chain": "x1",
        "requested_asset": "X1",
        "requested_scope": "x1_daily_intelligence_brief",
        "objective": objective,
        "status": "unavailable",
        "cmis_status": rank_response.get("status") or "unavailable",
        "findings": {"daily_brief_scope_selection": deepcopy(dict(selection))},
        "confidence": deepcopy(dict(rank_response.get("confidence") or {})),
        "evidence_context": {},
        "source": {"service": "cmis", "operation": "rank"},
        "sources": deepcopy(list(rank_response.get("sources") or [])),
        "warnings": warnings,
        "errors": deepcopy(list(rank_response.get("errors") or [])),
        "daily_brief_scope_selection": deepcopy(dict(selection)),
        "complete_x1_ecosystem_coverage_verified": False,
        "read_only": True,
        "execution_authorized": False,
    }


def run_x1_daily_intelligence_brief_workflow(
    *,
    cmis_client: Any,
    scout_graph: Any,
    objective: str,
    now: datetime | None = None,
    subject_limit: int = DEFAULT_DAILY_BRIEF_SUBJECT_LIMIT,
) -> dict[str, object]:
    """Build one bounded current-UTC-day Daily Brief through accepted CMIS facts."""

    if not isinstance(subject_limit, int) or isinstance(subject_limit, bool):
        raise ValueError("Daily Brief subject_limit must be an integer")
    if subject_limit < 1 or subject_limit > 10:
        raise ValueError("Daily Brief subject_limit must be between 1 and 10")

    rank_response = cmis_client.rank(
        chain="x1",
        metric="volume",
        limit=subject_limit,
    )
    rank_mapping = rank_response if isinstance(rank_response, Mapping) else {}
    subjects = _rank_subjects(rank_mapping, limit=subject_limit)

    try:
        window_start, window_end = _today_window(now)
    except ValueError as exc:
        selection = _selection(
            rank_response=rank_mapping,
            requested_limit=subject_limit,
            selected_count=len(subjects),
            window_start=None,
            window_end=None,
            state="unavailable",
            reason=str(exc),
        )
        return _selection_failure_report(
            objective=objective,
            rank_response=rank_mapping,
            selection=selection,
        )

    if not subjects:
        selection = _selection(
            rank_response=rank_mapping,
            requested_limit=subject_limit,
            selected_count=0,
            window_start=window_start,
            window_end=window_end,
            state="unavailable",
            reason="no_exact_ranked_x1_mint_subjects",
        )
        return _selection_failure_report(
            objective=objective,
            rank_response=rank_mapping,
            selection=selection,
        )

    request = {
        "asset": subjects[0],
        "objective": str(objective or "").strip(),
        "operation": "x1_intelligence_brief_inputs",
        "daily_brief_subjects": subjects,
        "daily_brief_window_start": window_start,
        "daily_brief_window_end": window_end,
        "daily_brief_requested_services": list(SUPPORTED_COMPONENT_SERVICES),
    }
    result = scout_graph.invoke({"request": request, "status": "running"})
    report = result.get("report") if isinstance(result, Mapping) else None
    if not isinstance(report, Mapping):
        raise ValueError("X1 Scout Daily Brief route did not return a report")

    selection = _selection(
        rank_response=rank_mapping,
        requested_limit=subject_limit,
        selected_count=len(subjects),
        window_start=window_start,
        window_end=window_end,
        state="selected",
    )
    safe = deepcopy(dict(report))
    safe["requested_scope"] = "x1_daily_intelligence_brief"
    safe["daily_brief_scope_selection"] = selection
    safe["complete_x1_ecosystem_coverage_verified"] = False
    safe["execution_authorized"] = False
    return safe


__all__ = [
    "DEFAULT_DAILY_BRIEF_SUBJECT_LIMIT",
    "X1_DAILY_BRIEF_SCOPE_SELECTION_CONTRACT",
    "run_x1_daily_intelligence_brief_workflow",
]
