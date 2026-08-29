"""Public-shell adapter to the required private ROBERTA implementation.

Phase 3 cutover is fail-closed: public runtime entrypoints expose integration
surfaces while roberta-private-core owns graph/orchestration implementation.
There is no public graph fallback.
"""

from __future__ import annotations

from typing import Any

EXPECTED_PRIVATE_CONTRACT = "roberta-private-core/v1"


class PrivateCoreUnavailable(RuntimeError):
    """The required private ROBERTA core is absent or contract-incompatible."""


def private_core_required() -> bool:
    """Return True: ROBERTA private core is mandatory after Phase 3 cutover."""
    return True


def _load_private_api():
    try:
        from roberta_core import api
    except ModuleNotFoundError as exc:
        if exc.name == "roberta_core" or str(exc.name or "").startswith("roberta_core."):
            return None
        raise
    return api


def _validated_private_api():
    api = _load_private_api()
    if api is None:
        raise PrivateCoreUnavailable(
            "roberta-private-core is required but is not installed."
        )
    if getattr(api, "CUTOVER_CONTRACT", None) != EXPECTED_PRIVATE_CONTRACT:
        raise PrivateCoreUnavailable(
            "ROBERTA private-core contract version is incompatible."
        )
    if not callable(getattr(api, "build_graph", None)):
        raise PrivateCoreUnavailable(
            "ROBERTA private-core facade does not expose build_graph."
        )
    return api


def build_graph(*args: Any, **kwargs: Any):
    """Build ROBERTA only through the required private-core facade."""
    return _validated_private_api().build_graph(*args, **kwargs)


def private_core_status() -> dict[str, Any]:
    api = _load_private_api()
    return {
        "available": api is not None,
        "required": True,
        "source": "private" if api is not None else "unavailable",
        "expected_contract": EXPECTED_PRIVATE_CONTRACT,
    }


__all__ = [
    "EXPECTED_PRIVATE_CONTRACT",
    "PrivateCoreUnavailable",
    "build_graph",
    "private_core_required",
    "private_core_status",
]
