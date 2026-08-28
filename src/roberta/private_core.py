"""Phase 3 adapter from the public ROBERTA shell to the private core.

Runtime entrypoints call this boundary instead of importing protected graph
implementation directly. During migration, the public graph remains a temporary
fallback so the source repository stays testable. Production cutover can fail
closed by setting ROBERTA_PRIVATE_CORE_REQUIRED=1.
"""

from __future__ import annotations

import os
from typing import Any

EXPECTED_PRIVATE_CONTRACT = "roberta-private-core/v1"


class PrivateCoreUnavailable(RuntimeError):
    """The required private ROBERTA core is absent or contract-incompatible."""


def private_core_required() -> bool:
    return os.getenv("ROBERTA_PRIVATE_CORE_REQUIRED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


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
        return None
    if getattr(api, "CUTOVER_CONTRACT", None) != EXPECTED_PRIVATE_CONTRACT:
        raise PrivateCoreUnavailable("ROBERTA private-core contract version is incompatible.")
    if not callable(getattr(api, "build_graph", None)):
        raise PrivateCoreUnavailable("ROBERTA private-core facade does not expose build_graph.")
    return api


def build_graph(*args: Any, **kwargs: Any):
    """Build ROBERTA through the private facade or the Phase 3 fallback."""
    private_api = _validated_private_api()
    if private_api is not None:
        return private_api.build_graph(*args, **kwargs)

    if private_core_required():
        raise PrivateCoreUnavailable(
            "ROBERTA_PRIVATE_CORE_REQUIRED is enabled but roberta-private-core is not installed."
        )

    # Transitional fallback only. It is removed once split validation passes and
    # before protected implementation is removed from public HEAD.
    from roberta.graph import build_graph as public_build_graph

    return public_build_graph(*args, **kwargs)


def private_core_status() -> dict[str, Any]:
    api = _load_private_api()
    return {
        "available": api is not None,
        "required": private_core_required(),
        "expected_contract": EXPECTED_PRIVATE_CONTRACT,
    }


__all__ = [
    "EXPECTED_PRIVATE_CONTRACT",
    "PrivateCoreUnavailable",
    "build_graph",
    "private_core_required",
    "private_core_status",
]
