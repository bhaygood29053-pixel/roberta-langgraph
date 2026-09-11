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

_SCRIPT = r'''
<script id="roberta-answer-consistency-v1">
function normalizeRobertaHumanAnswer(value){
  var text=String(value==null?'':value);
  var freshnessNotVerified=(
    /live market freshness is not fully verified/i.test(text)||
    /currentness is unverified/i.test(text)||
    /current[- ]state freshness (?:wasn't|was not|isn't|is not) confirmed/i.test(text)
  );
  if(freshnessNotVerified){
    text=text.replace(/latest verified observations/gi,'latest accepted/stored observations; currentness is unverified');
    text=text.replace(/verified market snapshot/gi,'accepted/stored market snapshot; currentness is unverified');
    text=text.replace(/current verified values/gi,'latest accepted/stored values; currentness is unverified');
  }
  text=text.replace(/\*\*Evidenceweak\*\*\s*proof strength/gi,'**Evidence quality:** proof strength');
  text=text.replace(/Evidenceweakproof strength/gi,'Evidence quality: proof strength');
  return text;
}
var _robertaBaseFormatIntelligenceCard=formatIntelligenceCard;
formatIntelligenceCard=function(text){
  return _robertaBaseFormatIntelligenceCard(normalizeRobertaHumanAnswer(text));
};
</script>
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
