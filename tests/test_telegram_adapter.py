import ast
import inspect

from langchain_core.messages import AIMessage

import roberta.telegram_adapter as telegram_adapter
from roberta.telegram_adapter import RobertaTelegramService, split_telegram_reply


class FakeGraph:
    def __init__(self):
        self.calls = []

    def invoke(self, inputs, config=None):
        self.calls.append((inputs, config))
        return {
            "messages": [
                *inputs["messages"],
                AIMessage(content="Verified response"),
            ]
        }


def test_service_invokes_one_explicit_thread():
    graph = FakeGraph()
    service = RobertaTelegramService(graph)

    reply = service.ask("hello", thread_id="telegram:1:1")

    assert reply == "Verified response"
    assert graph.calls[0][1] == {"configurable": {"thread_id": "telegram:1:1"}}


def test_split_telegram_reply_preserves_content():
    original = ("alpha " * 900).strip()
    chunks = split_telegram_reply(original, limit=1000)

    assert len(chunks) > 1
    assert all(len(chunk) <= 1000 for chunk in chunks)
    assert " ".join(chunks).split() == original.split()


def test_telegram_transport_cannot_import_cmis_or_direct_http_clients():
    """Telegram must always enter through ROBERTA, never CMIS/providers directly."""

    tree = ast.parse(inspect.getsource(telegram_adapter))
    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_modules.add(node.module)

    forbidden_roots = {
        "cmis",
        "requests",
        "httpx",
        "aiohttp",
        "urllib",
        "http.client",
    }

    violations = sorted(
        module
        for module in imported_modules
        if any(
            module == forbidden or module.startswith(f"{forbidden}.")
            for forbidden in forbidden_roots
        )
    )

    assert not violations, (
        "Telegram is a ROBERTA transport only and must never connect directly "
        f"to CMIS/providers: {violations}"
    )
