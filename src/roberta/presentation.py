"""Deterministic terminal presentation helpers for specialist reports."""

from collections.abc import Mapping
from textwrap import wrap
from typing import Any


_COMPONENT_WIDTH = 18
_STATUS_WIDTH = 10
_MEANING_WIDTH = 66


def _wrapped(value: object, width: int) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return [""]
    return wrap(
        text,
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [""]


def _center(value: object, width: int) -> str:
    return str(value or "").center(width)


def format_component_status_table(
    risk_help: Mapping[str, Any] | None,
) -> str | None:
    """Return one fixed-width centered table from deterministic risk help."""

    if not isinstance(risk_help, Mapping):
        return None
    components = risk_help.get("components")
    if not isinstance(components, Mapping) or not components:
        return None

    def border(char: str = "-") -> str:
        return (
            f"+{char * (_COMPONENT_WIDTH + 2)}"
            f"+{char * (_STATUS_WIDTH + 2)}"
            f"+{char * (_MEANING_WIDTH + 2)}+"
        )

    lines = [
        border(),
        (
            f"| {_center('COMPONENT', _COMPONENT_WIDTH)} "
            f"| {_center('STATUS', _STATUS_WIDTH)} "
            f"| {_center('WHAT THIS MEANS', _MEANING_WIDTH)} |"
        ),
        border("="),
    ]

    for name, raw_component in components.items():
        if not isinstance(name, str) or not isinstance(raw_component, Mapping):
            continue
        component_lines = _wrapped(name.replace("_", " ").title(), _COMPONENT_WIDTH)
        status_lines = _wrapped(
            raw_component.get("status") or "Unavailable",
            _STATUS_WIDTH,
        )
        meaning_lines = _wrapped(
            raw_component.get("meaning")
            or "No deterministic component explanation was returned.",
            _MEANING_WIDTH,
        )
        row_height = max(
            len(component_lines),
            len(status_lines),
            len(meaning_lines),
        )
        for index in range(row_height):
            component = component_lines[index] if index < len(component_lines) else ""
            status = status_lines[index] if index < len(status_lines) else ""
            meaning = meaning_lines[index] if index < len(meaning_lines) else ""
            lines.append(
                f"| {_center(component, _COMPONENT_WIDTH)} "
                f"| {_center(status, _STATUS_WIDTH)} "
                f"| {_center(meaning, _MEANING_WIDTH)} |"
            )
        lines.append(border())

    return "\n".join(lines) if len(lines) > 3 else None
