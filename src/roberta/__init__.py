"""Roberta LangGraph coordinator."""

# Apply public product semantics before the protected graph is imported. This
# guarantees every later X1 Scout import sees the same native-XNT interpretation
# instead of binding the generic token renderer first.
from roberta import chat_ui as _chat_ui
from roberta.x1_scout import instant_scan_product_ux as _instant_scan_product_ux
from roberta.x1_native_asset_semantics import (
    apply_native_xnt_output_contract,
    apply_native_xnt_product_semantics,
)

apply_native_xnt_product_semantics(_instant_scan_product_ux)
apply_native_xnt_output_contract(_chat_ui)

from roberta.private_core import build_graph
from roberta.state import RobertaState
from roberta import web_ui as _web_ui
from roberta.web_ui_current_capabilities import apply_current_capability_surface
from roberta.web_ui_intelligence_cards import (
    apply_clean_human_output_contract,
    apply_intelligence_card_surface,
)
from roberta.web_ui_polarity_colors import (
    apply_polarity_color_surface,
    apply_polarity_output_contract,
)

# Keep the large conversation-first website stable while projecting the newest
# accepted capability surface into the rendered HTML. web_ui_bytes() reads the
# module global at request time, so both the live bridge and direct UI tests see
# the same current website.
_web_ui.ROBERTA_WEB_UI_HTML = apply_current_capability_surface(
    _web_ui.ROBERTA_WEB_UI_HTML
)
_web_ui.ROBERTA_WEB_UI_HTML = apply_intelligence_card_surface(
    _web_ui.ROBERTA_WEB_UI_HTML
)
_web_ui.ROBERTA_WEB_UI_HTML = apply_polarity_color_surface(
    _web_ui.ROBERTA_WEB_UI_HTML
)

# Human answers stay evidence-complete internally, but the default response is
# now selective: decision, key metrics, three main reasons, evidence quality,
# then progressively disclosed supporting detail. Directional changes retain an
# explicit sign so the UI can render positive changes green and negative red.
apply_clean_human_output_contract(_chat_ui)
apply_polarity_output_contract(_chat_ui)

__all__ = ["RobertaState", "build_graph"]
