"""Roberta LangGraph coordinator."""

from __future__ import annotations

from importlib.util import find_spec as _find_spec
from pathlib import Path as _Path


def _extend_private_overlay_path() -> None:
    """Expose protected roberta modules from an installed private core.

    Normal wheel installs physically overlay the public shell and private
    distribution in one site-packages directory. Editable installs keep the
    source trees separate, so discover the installed roberta_core facade and
    add only its sibling roberta source directory to this package search path.

    If the private distribution is absent or malformed, this is a no-op and
    the existing private-core facade continues to fail closed.
    """

    try:
        spec = _find_spec("roberta_core")
    except (ImportError, ModuleNotFoundError, ValueError):
        return

    origin = getattr(spec, "origin", None) if spec is not None else None
    if not origin or origin in {"built-in", "frozen"}:
        return

    candidate = _Path(origin).resolve().parent.parent / "roberta"
    if not candidate.is_dir():
        return

    candidate_text = str(candidate)
    if candidate_text not in __path__:
        __path__.append(candidate_text)


_extend_private_overlay_path()

from roberta.private_core import build_graph
from roberta.state import RobertaState

__all__ = ["RobertaState", "build_graph"]
