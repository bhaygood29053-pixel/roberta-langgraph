"""LangGraph state for Roberta."""

from typing import Literal, NotRequired

from langgraph.graph import MessagesState


class RobertaState(MessagesState):
    """Execution state carried between Roberta graph nodes.

    ``messages`` is inherited from LangGraph's ``MessagesState`` and uses the
    framework's message reducer. Keep this schema small during Phase 1; add a
    field only when graph control flow genuinely needs it.
    """

    status: NotRequired[Literal["running", "complete", "error"]]
