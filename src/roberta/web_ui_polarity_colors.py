"""Directional number coloring for ROBERTA human chat.

Signed changes are presentation-only: explicit positive changes render green and
explicit negative changes render red. The browser does not infer direction from
unsigned market values or calculate any delta.
"""

from __future__ import annotations

from types import ModuleType

POLARITY_COLOR_SURFACE = "roberta-polarity-colors/v1"
POLARITY_COLOR_MARKER = 'id="roberta-polarity-colors-v1"'
POLARITY_OUTPUT_MARKER = "ROBERTA POLARITY OUTPUT CONTRACT v1"

_POLARITY_STYLE = r'''
<style id="roberta-polarity-colors-v1">
/* Directional deltas: negative red, positive green. */
.robertaIntelCard .neg,.msg.assistant .neg{color:#ff6b78!important;font-weight:900!important}
.robertaIntelCard .pos,.msg.assistant .pos{color:#63e6a6!important;font-weight:900!important}
</style>
'''

_INTEL_INLINE_REPLACEMENT = r'''function intelInline(value){
  var safe=escapeHtml(String(value==null?'':value));
  safe=safe.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  safe=safe.replace(/__(.+?)__/g,'<strong>$1</strong>');
  safe=safe.replace(/`([^`]+)`/g,'<code>$1</code>');
  safe=safe.replace(/\*\*/g,'').replace(/__/g,'');
  safe=safe.replace(/\b(PASS|WARN|BLOCK|PARTIAL|VERIFIED|UNVERIFIED|UNAVAILABLE|NOT VERIFIED|WATCH|CLEAR|CAUTION|ERROR|AVAILABLE|STRONG|MODERATE|WEAK|HIGH|LIMITED|UNKNOWN)\b/g,function(m){return intelPill(m)});
  safe=safe.replace(/\b([1-9A-HJ-NP-Za-km-z]{32,90})\b/g,'<button class="entityLink" data-entity="$1">$1</button>');
  /* Include HTML tag boundaries so **-16.2%** and **+16.2%** are colored too. */
  safe=safe.replace(/(^|[\s(>])([+]\d[\d,]*(?:\.\d+)?%?)(?=$|[\s<),.;])/g,'$1<span class="pos">$2</span>');
  safe=safe.replace(/(^|[\s(>])([-−]\d[\d,]*(?:\.\d+)?%?)(?=$|[\s<),.;])/g,'$1<span class="neg">$2</span>');
  return safe;
}
'''

_POLARITY_OUTPUT_APPENDIX = (
    " ROBERTA POLARITY OUTPUT CONTRACT v1: for directional numeric changes or "
    "deltas shown to a human, preserve an explicit sign: use + for a positive "
    "change and - for a negative change (for example +16.2% or -16.2%). "
    "Do not add a positive or negative sign to unsigned facts such as current "
    "price, liquidity, volume, balances, supply, or counts unless the underlying "
    "verified fact is itself a directional change. This is presentation only and "
    "must not infer or calculate a delta that CMIS/ROBERTA did not provide."
)


def apply_polarity_color_surface(html: str) -> str:
    """Apply explicit green/red rendering to signed directional values."""

    if POLARITY_COLOR_MARKER in html:
        return html

    updated = str(html)
    head_anchor = "</head>"
    if head_anchor not in updated:
        raise RuntimeError("ROBERTA website head contract drifted before polarity overlay.")
    updated = updated.replace(head_anchor, _POLARITY_STYLE + "\n" + head_anchor, 1)

    start_marker = "function intelInline(value){"
    end_marker = "function intelBulletText(line){"
    start = updated.find(start_marker)
    end = updated.find(end_marker, start)
    if start < 0 or end < 0:
        raise RuntimeError("ROBERTA intelligence-card formatter drifted before polarity overlay.")
    updated = updated[:start] + _INTEL_INLINE_REPLACEMENT + updated[end:]
    return updated


def apply_polarity_output_contract(chat_module: ModuleType) -> None:
    """Require explicit signs for verified directional changes in human output."""

    current = str(chat_module.HUMAN_ROBERTA_PRESENTATION_POLICY)
    if POLARITY_OUTPUT_MARKER in current:
        return

    updated = current + _POLARITY_OUTPUT_APPENDIX
    chat_module.HUMAN_ROBERTA_PRESENTATION_POLICY = updated
    chat_module.SINGLE_ASSET_TERMINAL_STYLE = (
        str(chat_module.SINGLE_ASSET_TERMINAL_STYLE) + _POLARITY_OUTPUT_APPENDIX
    )


__all__ = [
    "POLARITY_COLOR_MARKER",
    "POLARITY_COLOR_SURFACE",
    "POLARITY_OUTPUT_MARKER",
    "apply_polarity_color_surface",
    "apply_polarity_output_contract",
]
