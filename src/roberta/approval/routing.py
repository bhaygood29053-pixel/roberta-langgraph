"""Deterministic next-step routing after a human approval review."""

from __future__ import annotations

from typing import Literal, Mapping, Any

ApprovalNextStep = Literal["proceed", "stop", "re_review", "research"]


def approval_next_step(outcome: Mapping[str, Any]) -> ApprovalNextStep:
    """Map a validated approval outcome to the only allowed next workflow class.

    This function does not execute the next step. In particular, ``proceed`` is
    not signing/broadcasting authority; Phase 11 must revalidate and consume the
    exact approved proposal within its own execution safeguards.
    """

    if not isinstance(outcome, Mapping):
        raise TypeError("approval outcome must be a mapping")
    status = outcome.get("status")
    if status == "approved":
        return "proceed"
    if status == "rejected":
        return "stop"
    if status == "edited":
        return "re_review"
    if status == "more_evidence":
        return "research"
    raise ValueError(f"unsupported approval outcome status: {status!r}")
