"""Native Telegram transport for ROBERTA.

Telegram is a transport only. It may submit the authenticated owner's text to
ROBERTA and return ROBERTA's final assistant response, but it cannot select
tools, call CMIS directly, or bypass private-core orchestration.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from roberta.telegram_identity import (
    is_authorized_user,
    owner_id_from_env,
    telegram_thread_id,
)

TOKEN_ENV = "ROBERTA_TELEGRAM_TOKEN"
MAX_TELEGRAM_CHARS = 4000


def _message_text(message: object) -> str:
    text = getattr(message, "text", None)
    if isinstance(text, str) and text.strip():
        return text.strip()
    content = getattr(message, "content", "")
    return content.strip() if isinstance(content, str) else str(content).strip()


def _final_reply(result: Mapping[str, Any]) -> str:
    messages = result.get("messages")
    if not isinstance(messages, list):
        raise RuntimeError("Roberta graph returned no message list.")
    for item in reversed(messages):
        if isinstance(item, AIMessage) and not item.tool_calls:
            reply = _message_text(item)
            if reply:
                return reply
    raise RuntimeError("Roberta graph returned no final assistant reply.")


def split_telegram_reply(text: str, *, limit: int = MAX_TELEGRAM_CHARS) -> list[str]:
    """Split a long reply into Telegram-safe chunks without dropping content."""

    value = str(text or "").strip()
    if not value:
        return []
    if limit < 256:
        raise ValueError("Telegram reply limit must be at least 256 characters.")

    chunks: list[str] = []
    remaining = value
    while len(remaining) > limit:
        split_at = remaining.rfind("\n", 0, limit + 1)
        if split_at < limit // 2:
            split_at = remaining.rfind(" ", 0, limit + 1)
        if split_at < limit // 2:
            split_at = limit
        chunk = remaining[:split_at].rstrip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


def build_runtime_graph():
    """Build the required private-core ROBERTA graph for Telegram.

    Runtime-only imports stay inside this function so the public Telegram
    transport remains importable and testable when the protected implementation
    package is intentionally absent. This mirrors the existing HTTP bridge
    boundary: Telegram can only enter ROBERTA through the private-core facade.
    """

    try:
        from langgraph.checkpoint.memory import MemorySaver
    except ImportError as exc:
        raise RuntimeError("LangGraph MemorySaver is required for Telegram threads.") from exc

    from roberta.config import RobertaChainSettings
    from roberta.models import create_runtime_model
    from roberta.private_core import build_graph
    from roberta.tools import get_roberta_tools

    settings = RobertaChainSettings.from_env()
    oracle_model = create_runtime_model()
    x1_model = create_runtime_model()
    solana_model = create_runtime_model() if settings.solana_provider_enabled else None
    tools = get_roberta_tools(
        x1_planner_model=x1_model,
        solana_planner_model=solana_model,
        solana_provider_enabled=settings.solana_provider_enabled,
    )
    return build_graph(model=oracle_model, tools=tools, checkpointer=MemorySaver())


class RobertaTelegramService:
    """Application boundary between authenticated Telegram text and ROBERTA."""

    def __init__(self, graph: Any):
        self._graph = graph

    @classmethod
    def from_runtime(cls) -> "RobertaTelegramService":
        return cls(build_runtime_graph())

    def ask(self, message: str, *, thread_id: str) -> str:
        user_text = str(message or "").strip()
        if not user_text:
            raise ValueError("A non-empty Telegram message is required.")
        result = self._graph.invoke(
            {
                "messages": [HumanMessage(content=user_text)],
                "status": "running",
            },
            config={"configurable": {"thread_id": thread_id}},
        )
        if not isinstance(result, Mapping):
            raise RuntimeError("Roberta graph returned an invalid result.")
        return _final_reply(result)


def _token_from_env(value: str | None = None) -> str:
    token = str(value if value is not None else os.getenv(TOKEN_ENV, "")).strip()
    if not token:
        raise RuntimeError(f"{TOKEN_ENV} is required.")
    return token


def build_application(
    *,
    token: str,
    owner_id: int,
    service: RobertaTelegramService | None = None,
):
    """Build the python-telegram-bot polling application.

    The optional Telegram dependency is imported lazily so core/public-shell
    tests do not require the Telegram transport extra.
    """

    try:
        from telegram import Update
        from telegram.ext import Application, ContextTypes, MessageHandler, filters
    except ImportError as exc:
        raise RuntimeError(
            "Telegram support is not installed. Install with: pip install -e '.[telegram]'"
        ) from exc

    active_service = service or RobertaTelegramService.from_runtime()

    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        del context
        user = update.effective_user
        chat = update.effective_chat
        message = update.effective_message
        if user is None or chat is None or message is None:
            return

        # V1 is deliberately owner-only and private-chat-only. Bot-to-bot and
        # group participation are separate capabilities and cannot silently
        # inherit owner authorization.
        if getattr(chat, "type", None) != "private":
            return
        if not is_authorized_user(getattr(user, "id", None), owner_id=owner_id):
            await message.reply_text("Access denied.")
            return

        user_text = str(getattr(message, "text", "") or "").strip()
        if not user_text:
            return

        thread_id = telegram_thread_id(user_id=user.id, chat_id=chat.id)
        try:
            reply = await asyncio.to_thread(
                active_service.ask,
                user_text,
                thread_id=thread_id,
            )
        except Exception as exc:
            # Fail closed: do not expose prompts, credentials, provider payloads,
            # or stack traces through Telegram.
            await message.reply_text(
                f"ROBERTA could not complete the request ({type(exc).__name__})."
            )
            return

        for chunk in split_telegram_reply(reply):
            await message.reply_text(chunk)

    application = Application.builder().token(token).build()
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    return application


def main() -> None:
    token = _token_from_env()
    owner_id = owner_id_from_env()
    application = build_application(token=token, owner_id=owner_id)

    print("ROBERTA Telegram adapter starting")
    print("Transport: Telegram long polling")
    print("Authorization: private owner-only")
    print("Private core: required")
    print("OpenClaw dependency: none")
    application.run_polling(
        allowed_updates=["message"],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()


__all__ = [
    "MAX_TELEGRAM_CHARS",
    "RobertaTelegramService",
    "TOKEN_ENV",
    "build_application",
    "build_runtime_graph",
    "split_telegram_reply",
]
