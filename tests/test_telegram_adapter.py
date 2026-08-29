from langchain_core.messages import AIMessage

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
