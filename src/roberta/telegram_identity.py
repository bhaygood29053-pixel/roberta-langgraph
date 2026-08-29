"""Telegram identity and authorization helpers for ROBERTA."""

from __future__ import annotations

import os

OWNER_ID_ENV = "ROBERTA_TELEGRAM_OWNER_ID"


def owner_id_from_env(value: str | None = None) -> int:
    """Return the configured Telegram owner user id.

    The owner id is configuration, not a secret, but it must come from runtime
    configuration rather than being hard-coded into the public repository.
    """

    raw = str(value if value is not None else os.getenv(OWNER_ID_ENV, "")).strip()
    if not raw:
        raise RuntimeError(f"{OWNER_ID_ENV} is required.")
    try:
        owner_id = int(raw)
    except ValueError as exc:
        raise RuntimeError(f"{OWNER_ID_ENV} must be an integer Telegram user id.") from exc
    if owner_id <= 0:
        raise RuntimeError(f"{OWNER_ID_ENV} must be a positive Telegram user id.")
    return owner_id


def is_authorized_user(user_id: int | None, *, owner_id: int) -> bool:
    """Return whether Telegram authenticated the configured owner."""

    return isinstance(user_id, int) and user_id == owner_id


def telegram_thread_id(*, user_id: int, chat_id: int) -> str:
    """Return a stable LangGraph thread id for one private Telegram chat."""

    return f"telegram:{user_id}:{chat_id}"


__all__ = [
    "OWNER_ID_ENV",
    "is_authorized_user",
    "owner_id_from_env",
    "telegram_thread_id",
]
