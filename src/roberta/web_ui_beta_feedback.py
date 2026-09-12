"""Optional public-beta feedback controls for the conversation-first ROBERTA UI.

The controls are rendered only when the bridge returns a beta_response_id, which
only occurs when privacy-safe beta storage is explicitly configured. Feedback
contains categorical choices plus the random response id; no prompt or answer
text is sent to the beta endpoint.
"""

from __future__ import annotations

BETA_FEEDBACK_SURFACE = "roberta-beta-feedback/2026-09-12"
BETA_FEEDBACK_MARKER = "function showBetaFeedback(responseId)"

_STYLE = r'''
<style id="roberta-beta-feedback-v1">
.betaFeedback{align-self:flex-start;display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin:0 0 3px 2px;padding:5px 7px;border:1px solid rgba(126,151,255,.10);background:rgba(7,11,27,.72);border-radius:12px;color:#7f8aae;font-size:8px}
.betaFeedback b{color:#aeb7d6;font-size:8px;font-weight:800;margin-right:2px}
.betaFeedback button{border:1px solid rgba(126,151,255,.13);background:rgba(12,18,40,.82);color:#aeb9dc;border-radius:999px;padding:4px 7px;font-size:8px}
.betaFeedback button:hover{border-color:rgba(85,183,255,.36);color:#fff}
.betaFeedback.sent{color:#78dca8}.betaFeedback.sent button{display:none}
</style>
'''

_FUNCTIONS = r'''
async function submitBetaFeedback(responseId,helpful,clarity,container){
  if(!responseId||!container||container.dataset.sent==='1')return;
  var inspector=$('#inspector');
  var drilled=!!(inspector&&inspector.classList.contains('entityOpen'));
  var payload={response_id:responseId,helpful:helpful,clarity:clarity,evidence_drill_down:drilled};
  try{
    var r=await fetch(apiUrl('/v1/beta-feedback'),{method:'POST',headers:apiHeaders(),body:JSON.stringify(payload)});
    var d=await r.json().catch(function(){return{}});
    if(!r.ok||d.recorded!==true)return;
    container.dataset.sent='1';container.classList.add('sent');container.querySelector('b').textContent='Thanks — feedback recorded';
  }catch(e){}
}
function showBetaFeedback(responseId){
  if(typeof responseId!=='string'||!/^[0-9a-f]{32}$/.test(responseId))return;
  var wrap=document.createElement('div');wrap.className='betaFeedback';wrap.dataset.betaResponseId=responseId;
  wrap.innerHTML='<b>Was this useful?</b>'+
    '<button data-beta-choice="useful">Useful</button>'+
    '<button data-beta-choice="technical">Too technical</button>'+
    '<button data-beta-choice="missing">Missing evidence</button>';
  wrap.querySelector('[data-beta-choice="useful"]').onclick=function(){submitBetaFeedback(responseId,true,'clear',wrap)};
  wrap.querySelector('[data-beta-choice="technical"]').onclick=function(){submitBetaFeedback(responseId,false,'too_technical',wrap)};
  wrap.querySelector('[data-beta-choice="missing"]').onclick=function(){submitBetaFeedback(responseId,false,'missing_evidence',wrap)};
  $('#messages').appendChild(wrap);$('#messages').scrollTop=$('#messages').scrollHeight;
}
'''

_SEND_OLD = "addMessage('assistant',reply,chatId);appendRecord(chatId,'assistant',reply);updateInspector(reply);"
_SEND_NEW = _SEND_OLD + "if(r.ok&&typeof d.beta_response_id==='string')showBetaFeedback(d.beta_response_id);"
_FUNCTION_ANCHOR = "async function send(text){"


def apply_beta_feedback_surface(html: str) -> str:
    """Add privacy-safe opt-in beta feedback without changing intelligence flow."""

    updated = str(html)
    if BETA_FEEDBACK_MARKER in updated:
        return updated
    if _FUNCTION_ANCHOR not in updated:
        raise RuntimeError("ROBERTA web send function drifted before beta feedback overlay.")
    if _SEND_OLD not in updated:
        raise RuntimeError("ROBERTA assistant reply boundary drifted before beta feedback overlay.")
    if "</head>" not in updated:
        raise RuntimeError("ROBERTA web head boundary drifted before beta feedback overlay.")

    updated = updated.replace("</head>", _STYLE + "\n</head>", 1)
    updated = updated.replace(_FUNCTION_ANCHOR, _FUNCTIONS + "\n" + _FUNCTION_ANCHOR, 1)
    updated = updated.replace(_SEND_OLD, _SEND_NEW, 1)
    return updated


__all__ = [
    "BETA_FEEDBACK_MARKER",
    "BETA_FEEDBACK_SURFACE",
    "apply_beta_feedback_surface",
]
