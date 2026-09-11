"""Human-language guardrails for unverified current-market freshness."""

from __future__ import annotations

from types import ModuleType


FRESHNESS_LANGUAGE_MARKER = "ROBERTA FRESHNESS LANGUAGE CONTRACT v1"

_FRESHNESS_LANGUAGE_APPENDIX = (
    f" {FRESHNESS_LANGUAGE_MARKER}: when CMIS says current/live market freshness "
    "is PARTIAL, NOT_VERIFIED, UNKNOWN, STALE, or otherwise not fully verified, "
    "do not describe the affected snapshot or fields as a 'verified market snapshot', "
    "'latest verified observations', 'current verified values', or equivalent wording. "
    "Instead identify them as the latest accepted/stored observations and state that "
    "currentness is unverified. An observation timestamp proves when the observation "
    "was stored/seen; it does not by itself prove current-state freshness. Historical "
    "verified observations may still be called verified historical evidence when that "
    "scope is explicit. Never weaken or hide the underlying CMIS freshness status."
)


def apply_freshness_language_contract(chat_module: ModuleType) -> None:
    """Project one consistent freshness vocabulary into ROBERTA human output."""

    human = str(getattr(chat_module, "HUMAN_ROBERTA_PRESENTATION_POLICY", ""))
    if FRESHNESS_LANGUAGE_MARKER not in human:
        chat_module.HUMAN_ROBERTA_PRESENTATION_POLICY = (
            human + _FRESHNESS_LANGUAGE_APPENDIX
        )

    terminal = str(getattr(chat_module, "SINGLE_ASSET_TERMINAL_STYLE", ""))
    if FRESHNESS_LANGUAGE_MARKER not in terminal:
        chat_module.SINGLE_ASSET_TERMINAL_STYLE = (
            terminal + _FRESHNESS_LANGUAGE_APPENDIX
        )


__all__ = [
    "FRESHNESS_LANGUAGE_MARKER",
    "apply_freshness_language_contract",
]
