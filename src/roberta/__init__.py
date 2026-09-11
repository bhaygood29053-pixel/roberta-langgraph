"""Roberta LangGraph coordinator."""

from roberta.private_core import build_graph
from roberta.state import RobertaState
from roberta import web_ui as _web_ui
from roberta.web_ui_current_capabilities import apply_current_capability_surface

# Keep the large conversation-first website stable while projecting the newest
# accepted capability surface into the rendered HTML. web_ui_bytes() reads the
# module global at request time, so both the live bridge and direct UI tests see
# the same current website.
_web_ui.ROBERTA_WEB_UI_HTML = apply_current_capability_surface(
    _web_ui.ROBERTA_WEB_UI_HTML
)

__all__ = ["RobertaState", "build_graph"]
