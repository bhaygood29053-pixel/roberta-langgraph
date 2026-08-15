"""Deterministic timestamp normalization helpers."""

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
