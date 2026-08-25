from __future__ import annotations

from .autonomous_source import resolve_local_trusted_source


_INSTALLED = False


def install_autonomous_trusted_source_resolver() -> None:
    """Extend curriculum validation with the independent local autonomous registry.

    Built-in registered user sources retain precedence. A package cannot register
    itself: the fallback resolves only an independently hashed record under
    ~/.roberta/autonomous_sources (or ROBERTA_AUTONOMOUS_SOURCE_ROOT).
    """

    global _INSTALLED
    if _INSTALLED:
        return
    from . import curriculum_io

    original = curriculum_io._default_trusted_source_resolver

    def resolver(source_key: str):
        trusted = original(source_key)
        if trusted is not None:
            return trusted
        return resolve_local_trusted_source(source_key)

    resolver.__name__ = "_autonomous_aware_trusted_source_resolver"
    curriculum_io._default_trusted_source_resolver = resolver
    _INSTALLED = True
