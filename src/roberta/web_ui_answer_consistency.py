"""Deterministic browser-side consistency guard for ROBERTA human answers.

This overlay changes presentation text only. It never promotes CMIS evidence,
changes freshness state, recomputes facts, alters risk, or authorizes execution.
"""

from __future__ import annotations


ANSWER_CONSISTENCY_SURFACE = "roberta-answer-consistency/v1"
ANSWER_CONSISTENCY_MARKER = 'id="roberta-answer-consistency-v1"'

_RENDER_HOOK = (
    "if(role==='assistant')d.innerHTML=formatIntelligenceCard(text);"
    "else d.textContent=text;"
)
_ANCHOR = "function answerActions(chatId){"

# This fragment is inserted *inside* the website's existing main <script> block.
# It must therefore remain bare JavaScript. Wrapping it in another <script>
# element would cause the nested </script> to terminate the main script and the
# remaining JavaScript would be rendered as visible page text by the browser.
_SCRIPT = r'''
/* id="roberta-answer-consistency-v1" */
function normalizeRobertaHumanAnswer(value){
  var text=String(value==null?'':value);
  var freshnessNotVerified=(
    /live market freshness is not fully verified/i.test(text)||
    /currentness is unverified/i.test(text)||
    /current[- ]state freshness (?:wasn't|was not|isn't|is not) confirmed/i.test(text)||
    /freshness (?:is|are) (?:not verified|unverified)/i.test(text)||
    /freshness[^.\n]{0,80}(?:NOT_VERIFIED|not verified|unverified)/i.test(text)||
    /current[- ]market freshness check came back NOT_VERIFIED/i.test(text)
  );
  if(freshnessNotVerified){
    text=text.replace(/latest verified observations/gi,'latest accepted/stored observations; currentness is unverified');
    text=text.replace(/last verified observation/gi,'latest accepted/stored observation; currentness is unverified');
    text=text.replace(/verified market snapshot/gi,'accepted/stored market snapshot; currentness is unverified');
    text=text.replace(/current verified values/gi,'latest accepted/stored values; currentness is unverified');
    text=text.replace(/treat (?:these|them) as (?:a )?recent snapshot, not a live quote/gi,'treat these as accepted/stored observations; currentness is unverified');
    text=text.replace(/stale-ish snapshot/gi,'snapshot with unverified currentness');
  }
  text=text.replace(/\*\*Evidence\s*weak\*\*\s*[\.:]?/gi,'**Evidence quality: WEAK.** ');
  text=text.replace(/Evidence\s*weak\s*proof strength/gi,'Evidence quality: WEAK; proof strength');
  text=text.replace(/Evidenceweakproof strength/gi,'Evidence quality: WEAK; proof strength');
  return text;
}
var _robertaBaseFormatIntelligenceCard=formatIntelligenceCard;
formatIntelligenceCard=function(text){
  return _robertaBaseFormatIntelligenceCard(normalizeRobertaHumanAnswer(text));
};
'''


def apply_answer_consistency_surface(html: str) -> str:
    """Normalize contradictory currentness wording before intelligence-card render."""

    result = str(html or "")
    if ANSWER_CONSISTENCY_MARKER in result:
        return result
    if _RENDER_HOOK not in result:
        raise ValueError("ROBERTA assistant render hook is unavailable")
    if _ANCHOR not in result:
        raise ValueError("ROBERTA answer-actions anchor is unavailable")

    return result.replace(_ANCHOR, _SCRIPT + "\n" + _ANCHOR, 1)


__all__ = [
    "ANSWER_CONSISTENCY_MARKER",
    "ANSWER_CONSISTENCY_SURFACE",
    "apply_answer_consistency_surface",
]
