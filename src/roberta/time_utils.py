"""Deterministic timestamp normalization and display helpers."""

from datetime import datetime, timezone
from math import isfinite


def normalize_observed_at(value: object | None) -> str | None:
    """Return a canonical UTC timestamp without guessing unsupported values.

    Numeric values are interpreted as Unix epoch seconds. Existing non-empty
    strings are preserved verbatim because CMIS may already provide a canonical
    representation. Unsupported, empty, non-finite, or out-of-range values
    return ``None`` rather than asking an LLM to infer a date.
    """

    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, str):
        return value if value.strip() else None

    if isinstance(value, (int, float)):
        numeric = float(value)
        if not isfinite(numeric):
            return None
        try:
            observed = datetime.fromtimestamp(numeric, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
        return observed.isoformat(timespec="microseconds").replace("+00:00", "Z")

    return None


def format_observed_at_utc(value: object | None) -> str | None:
    """Render a verified timezone-aware timestamp as a compact UTC display."""

    normalized = normalize_observed_at(value)
    if normalized is None:
        return None

    candidate = normalized.strip()
    if candidate.endswith("Z"):
        candidate = candidate[:-1] + "+00:00"

    try:
        observed = datetime.fromisoformat(candidate)
    except ValueError:
        return None

    if observed.tzinfo is None:
        return None

    observed = observed.astimezone(timezone.utc)
    return observed.strftime("%Y-%m-%d | %H:%M:%S UTC")
