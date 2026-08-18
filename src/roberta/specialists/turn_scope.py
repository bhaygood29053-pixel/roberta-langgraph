"""Message-scope helpers for freshness-sensitive specialist evidence.

A LangGraph thread can contain many user turns. Current policy evaluation must
never reuse a Scout ToolMessage from an earlier user turn merely because that
message remains in checkpoint history.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from langchain_core.messages import HumanMessage


def _is_user_message(message: object) -> bool:
    if isinstance(message, HumanMessage):
        return True
    if isinstance(message, Mapping):
        return message.get("role") in {"user", "human"}
    return getattr(message, "type", None) == "human"


def current_user_turn_messages(messages: Sequence[Any]) -> list[Any]:
    """Return messages after the latest user/human message.

    No user marker means no current-turn evidence. This is intentionally
    fail-closed: a bare historical ToolMessage must not satisfy a current
    freshness-sensitive policy rule.
    """

    latest_user_index: int | None = None
    for index, message in enumerate(messages):
        if _is_user_message(message):
            latest_user_index = index
    if latest_user_index is None:
        return []
    return list(messages[latest_user_index + 1 :])


__all__ = ["current_user_turn_messages"]
