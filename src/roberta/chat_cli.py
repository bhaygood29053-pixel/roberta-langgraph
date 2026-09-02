"""Interactive terminal conversation with Roberta."""

from __future__ import annotations

import shlex

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from roberta.chat_ui import (
    LINE,
    SERVICE_MENU,
    STATUS_KEY,
    SUBLINE,
    activity_request,
    automatic_status_summary,
    burn_request,
    discovery_request,
    what_changed_request,
    compare_request,
    concentration_request,
    evidence_request,
    format_terminal_text,
    full_request,
    history_request,
    liquidity_request,
    overview_request,
    pretrade_request,
    rank_request,
    risk_request,
    tokenomics_request,
)
from roberta.config import RobertaChainSettings
from roberta.private_core import build_graph
from roberta.models import create_runtime_model
from roberta.tools import get_roberta_tools


def _message_text(message: object) -> str:
    text = getattr(message, "text", None)
    if isinstance(text, str) and text:
        return text
    content = getattr(message, "content", "")
    return content if isinstance(content, str) else str(content)


def _prompt_asset(label: str = "Asset") -> str:
    while True:
        value = input(f"{label}: ").strip()
        if value:
            return value


def _prompt_limit() -> int:
    value = input("Limit [10]: ").strip()
    if not value:
        return 10
    try:
        return max(1, min(int(value), 50))
    except ValueError:
        print("Using default limit 10.")
        return 10


def _prompt_pretrade() -> str:
    asset = _prompt_asset()
    action = input("Action (BUY/SELL): ").strip().upper()
    if action not in {"BUY", "SELL"}:
        raise ValueError("Pre-trade action must be BUY or SELL.")
    amount_text = input("USD amount: ").strip().replace(",", "").replace("$", "")
    amount = float(amount_text)
    if amount <= 0:
        raise ValueError("USD amount must be greater than zero.")
    return pretrade_request(asset, action, amount)


def _menu_request(choice: str) -> str | None:
    if choice == "1":
        return overview_request(_prompt_asset())
    if choice == "2":
        return compare_request(_prompt_asset("Asset 1"), _prompt_asset("Asset 2"))
    if choice == "3":
        return risk_request(_prompt_asset())
    if choice == "4":
        return tokenomics_request(_prompt_asset())
    if choice == "5":
        return liquidity_request(_prompt_asset())
    if choice == "6":
        return history_request(_prompt_asset())
    if choice == "7":
        return activity_request(_prompt_asset())
    if choice == "8":
        asset = _prompt_asset()
        evidence_id = input("CMIS intelligence evidence id (ie_...): ").strip()
        if not evidence_id.startswith("ie_"):
            raise ValueError("Concentration Change requires an exact CMIS ie_ evidence id.")
        return concentration_request(asset, evidence_id)
    if choice == "9":
        metric = input(
            "Metric (volume/liquidity/holders/safety/gainers/losers/trending): "
        ).strip().lower()
        return rank_request(metric or "volume", _prompt_limit())
    if choice == "10":
        return _prompt_pretrade()
    if choice == "11":
        return evidence_request(_prompt_asset())
    if choice == "12":
        return full_request(_prompt_asset())
    if choice == "13":
        print()
        print(LINE)
        print(STATUS_KEY)
        print(LINE)
        return None
    if choice == "14":
        return burn_request(_prompt_asset())
    if choice == "15":
        return discovery_request(_prompt_asset())
    if choice == "16":
        return what_changed_request(_prompt_asset())
    raise ValueError("Choose a service number from 1 through 16.")


def _shortcut_request(user_text: str) -> str | None:
    parts = shlex.split(user_text)
    command = parts[0].lower()
    args = parts[1:]

    if command == "/overview":
        return overview_request(args[0] if args else _prompt_asset())
    if command == "/compare":
        if len(args) >= 2:
            return compare_request(args[0], args[1])
        return compare_request(_prompt_asset("Asset 1"), _prompt_asset("Asset 2"))
    if command == "/risk":
        return risk_request(args[0] if args else _prompt_asset())
    if command == "/tokenomics":
        return tokenomics_request(args[0] if args else _prompt_asset())
    if command == "/burn":
        return burn_request(args[0] if args else _prompt_asset())
    if command == "/discovery":
        return discovery_request(args[0] if args else _prompt_asset())
    if command in {"/changed", "/whatchanged"}:
        return what_changed_request(args[0] if args else _prompt_asset())
    if command == "/liquidity":
        return liquidity_request(args[0] if args else _prompt_asset())
    if command == "/history":
        return history_request(args[0] if args else _prompt_asset())
    if command == "/activity":
        return activity_request(args[0] if args else _prompt_asset())
    if command == "/concentration":
        if len(args) >= 2:
            asset, evidence_id = args[0], args[1]
        else:
            asset = _prompt_asset()
            evidence_id = input("CMIS intelligence evidence id (ie_...): ").strip()
        if not evidence_id.startswith("ie_"):
            raise ValueError("Concentration Change requires an exact CMIS ie_ evidence id.")
        return concentration_request(asset, evidence_id)
    if command == "/rank":
        metric = args[0].lower() if args else "volume"
        limit = 10
        if len(args) >= 2:
            limit = max(1, min(int(args[1]), 50))
        return rank_request(metric, limit)
    if command == "/pretrade":
        if len(args) >= 3:
            asset = args[0]
            action = args[1].upper()
            if action not in {"BUY", "SELL"}:
                raise ValueError("Pre-trade action must be BUY or SELL.")
            amount = float(args[2].replace(",", "").replace("$", ""))
            if amount <= 0:
                raise ValueError("USD amount must be greater than zero.")
            return pretrade_request(asset, action, amount)
        return _prompt_pretrade()
    if command == "/evidence":
        return evidence_request(args[0] if args else _prompt_asset())
    if command == "/full":
        return full_request(args[0] if args else _prompt_asset())
    return user_text


def main() -> None:
    settings = RobertaChainSettings.from_env()

    print()
    print(LINE)
    print("ROBERTA STARTING")
    print(LINE)

    oracle_model = create_runtime_model()
    x1_model = create_runtime_model()
    solana_model = create_runtime_model() if settings.solana_provider_enabled else None

    tools = get_roberta_tools(
        x1_planner_model=x1_model,
        solana_planner_model=solana_model,
        solana_provider_enabled=settings.solana_provider_enabled,
    )
    graph = build_graph(model=oracle_model, tools=tools)
    history: list[object] = []

    print()
    print(LINE)
    print("ROBERTA ONLINE")
    print(LINE)
    print(SERVICE_MENU)
    print(LINE)

    while True:
        print()
        print(LINE)
        try:
            user_text = input("YOU: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nROBERTA SESSION ENDED")
            print(LINE)
            break

        print(SUBLINE)
        if not user_text:
            continue

        command = user_text.lower()

        if command in {"/exit", "/quit", "exit", "quit"}:
            print("\nROBERTA\n" + SUBLINE)
            print("  Goodbye.")
            print(LINE)
            break

        if command == "/new":
            history = []
            print("\nNEW CONVERSATION STARTED")
            print(LINE)
            continue

        if command == "/menu":
            print()
            print(SERVICE_MENU)
            print(LINE)
            continue

        if command == "/key":
            print()
            print(STATUS_KEY)
            print(LINE)
            continue

        try:
            if user_text in {str(number) for number in range(1, 15)}:
                expanded_request = _menu_request(user_text)
                if expanded_request is None:
                    continue
            elif user_text.startswith("/"):
                expanded_request = _shortcut_request(user_text)
            else:
                expanded_request = user_text
        except (ValueError, IndexError) as exc:
            print()
            print("REQUEST ERROR")
            print(SUBLINE)
            print(format_terminal_text(str(exc)))
            print(LINE)
            continue

        if expanded_request != user_text:
            print()
            print("REQUEST")
            print(SUBLINE)
            print(format_terminal_text(expanded_request))

        request_messages = [
            *history,
            HumanMessage(content=expanded_request),
        ]

        try:
            result = graph.invoke(
                {
                    "messages": request_messages,
                    "status": "running",
                }
            )
        except Exception as exc:
            print()
            print("ROBERTA ERROR")
            print(SUBLINE)
            print(format_terminal_text(f"{type(exc).__name__}: {exc}"))
            print(LINE)
            continue

        messages = result["messages"]
        new_messages = messages[len(request_messages):]

        for message in new_messages:
            if isinstance(message, AIMessage) and message.tool_calls:
                print()
                print("ROBERTA DELEGATING")
                print(SUBLINE)
                for call in message.tool_calls:
                    print(f"  -> {call.get('name', 'tool')}")

            elif isinstance(message, ToolMessage):
                print()
                print("TOOL COMPLETED")
                print(SUBLINE)
                print(f"  {message.name}")

                status_summary = automatic_status_summary(message.content)
                if status_summary:
                    print()
                    print("AUTOMATIC STATUS & ALERTS")
                    print(SUBLINE)
                    print(format_terminal_text(status_summary))

            elif isinstance(message, AIMessage):
                content = _message_text(message)
                if content:
                    print()
                    print("ROBERTA")
                    print(SUBLINE)
                    print()
                    print(format_terminal_text(content))

        print()
        print(LINE)
        history = messages


if __name__ == "__main__":
    main()
