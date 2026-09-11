"""Clean, progressive-disclosure rendering for ROBERTA human chat answers.

This overlay keeps the conversation-first base UI stable while presenting long
verified token answers as an executive intelligence card. The browser only
reorganizes text ROBERTA already returned; it does not calculate market facts,
risk, freshness, evidence quality, or recommendations.
"""

from __future__ import annotations

from types import ModuleType

INTELLIGENCE_CARD_SURFACE = "roberta-intelligence-card/v1"
INTELLIGENCE_CARD_MARKER = 'id="roberta-intelligence-card-v1"'
CLEAN_HUMAN_OUTPUT_MARKER = "ROBERTA CLEAN CHAT CONTRACT v1"

_RENDER_HOOK_OLD = (
    "if(role==='assistant')d.innerHTML=decisionSummary(text)+formatAssistant(text);"
    "else d.textContent=text;"
)
_RENDER_HOOK_NEW = (
    "if(role==='assistant')d.innerHTML=formatIntelligenceCard(text);"
    "else d.textContent=text;"
)
_FORMATTER_ANCHOR = "function answerActions(chatId){"

_CARD_STYLE = r'''
<style id="roberta-intelligence-card-v1">
/* Executive intelligence card: answer first, detail on demand. */
.msgWrap.assistant{width:100%!important;max-width:min(96%,940px)!important}
.msg.assistant{width:100%;padding:0!important;background:transparent!important;border:0!important;white-space:normal!important;color:#e9edff!important}
.robertaIntelCard{width:100%;overflow:hidden;border:1px solid rgba(126,151,255,.17);border-radius:20px;background:linear-gradient(180deg,rgba(13,20,45,.96),rgba(8,13,31,.96));box-shadow:0 18px 46px rgba(0,0,0,.18)}
.intelHero{padding:17px 18px 14px;border-bottom:1px solid rgba(126,151,255,.11);background:linear-gradient(120deg,rgba(53,91,195,.10),rgba(118,72,191,.06) 55%,transparent)}
.intelEyebrow{color:#7d8ab1;font-size:8px;font-weight:900;letter-spacing:.13em;text-transform:uppercase;margin-bottom:7px}
.intelTitleRow{display:flex;align-items:center;gap:9px;flex-wrap:wrap}.intelTitle{margin:0;color:#fff;font-size:18px;line-height:1.2;letter-spacing:-.02em}.intelSummary{margin:7px 0 0;color:#b7c0dd;font-size:12px;line-height:1.55;max-width:780px}
.intelPill{display:inline-flex;align-items:center;gap:5px;padding:4px 8px;border:1px solid rgba(135,150,190,.18);border-radius:999px;background:rgba(120,135,170,.08);color:#c6cee5;font-size:8px;font-weight:900;letter-spacing:.04em;white-space:nowrap}.intelPill:before{content:"";width:6px;height:6px;border-radius:50%;background:#93a0bd}.intelPill.good{color:#83e7b7;border-color:rgba(89,211,146,.26);background:rgba(49,140,93,.10)}.intelPill.good:before{background:#68dfa6}.intelPill.warn{color:#ffd27f;border-color:rgba(255,203,104,.25);background:rgba(156,111,26,.10)}.intelPill.warn:before{background:#f6c453}.intelPill.bad{color:#ff98a4;border-color:rgba(255,118,132,.26);background:rgba(157,45,60,.10)}.intelPill.bad:before{background:#ff7e8d}.intelPill.neutral{color:#b9c2dd}
.intelBody{padding:14px 16px 16px;display:grid;gap:12px}.intelSection{border:1px solid rgba(126,151,255,.10);background:rgba(7,12,28,.54);border-radius:15px;padding:12px}.intelSectionTitle{display:flex;align-items:center;justify-content:space-between;gap:8px;color:#dce4ff;font-size:9px;font-weight:900;letter-spacing:.09em;text-transform:uppercase;margin:0 0 9px}.intelObserved{color:#6f7c9f;font-size:8px;font-weight:700;letter-spacing:0;text-transform:none}
.metricGrid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:7px}.intelMetric{min-width:0;border:1px solid rgba(126,151,255,.10);background:rgba(11,17,38,.82);border-radius:12px;padding:9px}.intelMetricLabel{display:block;color:#7582a7;font-size:7px;font-weight:900;letter-spacing:.07em;text-transform:uppercase}.intelMetricValue{display:block;color:#f4f7ff;font-size:13px;font-weight:900;margin-top:3px;overflow-wrap:anywhere}
.intelFactList,.intelSignalList,.intelNeedList{display:grid;gap:7px;margin:0;padding:0;list-style:none}.intelFact,.intelSignal,.intelNeed{position:relative;padding-left:14px;color:#c2cbe5;font-size:11px;line-height:1.55}.intelFact:before,.intelSignal:before,.intelNeed:before{content:"";position:absolute;left:1px;top:.64em;width:5px;height:5px;border-radius:50%;background:#6bbfff}.intelSignal strong{color:#fff}.intelNeed:before{background:#d9ae5b}.intelFact:before{background:#73dca9}
.intelEvidence{display:flex;align-items:center;gap:8px;flex-wrap:wrap;border:1px solid rgba(126,151,255,.10);background:rgba(8,13,31,.68);border-radius:14px;padding:10px 11px}.intelEvidenceLabel{color:#7885aa;font-size:8px;font-weight:900;letter-spacing:.10em;text-transform:uppercase}.intelEvidenceText{color:#9ba7c8;font-size:10px;line-height:1.45;flex:1;min-width:180px}
.intelBottomLine{border:1px solid rgba(89,180,255,.18);background:linear-gradient(115deg,rgba(38,105,178,.11),rgba(76,65,163,.07));border-radius:15px;padding:12px 13px}.intelBottomLineLabel{color:#72cbff;font-size:8px;font-weight:900;letter-spacing:.11em;text-transform:uppercase;margin-bottom:5px}.intelBottomLineText{color:#f4f7ff;font-size:12px;line-height:1.55;font-weight:700}
.intelDisclosure{border:1px solid rgba(126,151,255,.10);background:rgba(7,11,27,.48);border-radius:13px;overflow:hidden}.intelDisclosure>summary{list-style:none;cursor:pointer;padding:10px 12px;color:#aab5d4;font-size:9px;font-weight:900}.intelDisclosure>summary::-webkit-details-marker{display:none}.intelDisclosure>summary:before{content:"＋";color:#72cbff;margin-right:7px}.intelDisclosure[open]>summary:before{content:"−"}.intelDisclosureCount{color:#657297;font-size:8px;font-weight:700;margin-left:5px}.intelDisclosureBody{border-top:1px solid rgba(126,151,255,.08);padding:10px 12px}.intelMore{margin-top:8px}
.intelParagraph{margin:0;color:#bcc6e1;font-size:11px;line-height:1.6}.intelParagraph+.intelParagraph{margin-top:7px}.robertaIntelCard strong{color:#fff}.robertaIntelCard code{border:1px solid rgba(126,151,255,.12);background:rgba(4,8,20,.78);border-radius:5px;padding:1px 4px;color:#9bdcff;font-size:.9em}.robertaIntelCard .entityLink{font-size:inherit}.robertaIntelCard .machineStatusToken{display:none}
.intelFooter{display:flex;align-items:center;gap:8px;flex-wrap:wrap;color:#687598;font-size:8px;padding-top:1px}.intelFooter span{display:inline-flex;align-items:center;gap:5px}.intelFooter span+span:before{content:"•";color:#465270;margin-right:3px}
@media(max-width:900px){.metricGrid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:620px){.msgWrap.assistant{max-width:100%!important}.intelHero{padding:14px}.intelBody{padding:12px}.metricGrid{grid-template-columns:repeat(2,minmax(0,1fr))}.intelTitle{font-size:16px}.intelSummary{font-size:11px}}
</style>
'''

_CARD_FORMATTER_JS = r'''
function intelPlain(value){
  return String(value==null?'':value).replace(/\*\*/g,'').replace(/__/g,'').replace(/`/g,'').trim();
}
function intelTone(value){
  var v=normalizedToken(value);
  if(['pass','verified','clear','available','strong','low','verylow'].indexOf(v)>=0)return'good';
  if(['warn','warning','caution','partial','moderate','medium','limited','unknown'].indexOf(v)>=0)return'warn';
  if(['block','blocked','fail','failed','error','unavailable','unverified','notverified','weak','high','veryhigh','critical'].indexOf(v)>=0)return'bad';
  return'neutral';
}
function intelPill(value){
  var v=intelPlain(value).replace(/[.,;:]+$/,'');
  return '<span class="intelPill '+intelTone(v)+'">'+escapeHtml(v)+'</span>';
}
function intelInline(value){
  var safe=escapeHtml(String(value==null?'':value));
  safe=safe.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>');
  safe=safe.replace(/__(.+?)__/g,'<strong>$1</strong>');
  safe=safe.replace(/`([^`]+)`/g,'<code>$1</code>');
  safe=safe.replace(/\*\*/g,'').replace(/__/g,'');
  safe=safe.replace(/\b(PASS|WARN|BLOCK|PARTIAL|VERIFIED|UNVERIFIED|UNAVAILABLE|NOT VERIFIED|WATCH|CLEAR|CAUTION|ERROR|AVAILABLE|STRONG|MODERATE|WEAK|HIGH|LIMITED|UNKNOWN)\b/g,function(m){return intelPill(m)});
  safe=safe.replace(/\b([1-9A-HJ-NP-Za-km-z]{32,90})\b/g,'<button class="entityLink" data-entity="$1">$1</button>');
  safe=safe.replace(/(^|[\s(])([+]\d[\d,]*(?:\.\d+)?%?)(?=$|[\s),.;])/g,'$1<span class="pos">$2</span>');
  safe=safe.replace(/(^|[\s(])(-\d[\d,]*(?:\.\d+)?%?)(?=$|[\s),.;])/g,'$1<span class="neg">$2</span>');
  return safe;
}
function intelBulletText(line){return String(line||'').trim().replace(/^[-•]\s*/, '').trim()}
function intelHeadingType(line){
  var p=intelPlain(line).replace(/:$/,'').trim();
  if(/^Verified facts(?:\s*\([^)]*\))?$/i.test(p))return'verified';
  if(/^What actually matters$/i.test(p))return'matters';
  if(/^WHAT ROBERTA STILL NEEDS$/i.test(p)||/^What ROBERTA still needs$/i.test(p))return'needs';
  if(/^Evidence quality\s*:/i.test(intelPlain(line)))return'evidence';
  if(/^BOTTOM LINE\s*:/i.test(intelPlain(line)))return'bottom';
  if(/^[A-Z][A-Z0-9 &?\/—-]{2,}$/.test(p))return'generic';
  return'';
}
function intelObservedFromHeading(line){
  var m=intelPlain(line).match(/observed\s+([^)]+)\)/i);return m?m[1].trim():'';
}
function intelMetricFromSegment(segment){
  var p=intelPlain(segment).replace(/[.]$/,'').trim(),m;
  m=p.match(/^(Price|Liquidity|24h volume|24h transactions)\s+(.+)$/i);
  if(m)return{label:m[1],value:m[2]};
  m=p.match(/^(\d[\d,]*)\s+LPs?$/i);
  if(m)return{label:'LPs',value:m[1]};
  return null;
}
function intelMetricGrid(items){
  if(!items.length)return{html:'',consumed:false};
  var first=intelBulletText(items[0]),segments=first.split(';').map(function(x){return x.trim()}).filter(Boolean),metrics=[];
  if(segments.length<2)return{html:'',consumed:false};
  segments.forEach(function(segment){var metric=intelMetricFromSegment(segment);if(metric)metrics.push(metric)});
  if(metrics.length<3)return{html:'',consumed:false};
  var html='<div class="metricGrid">'+metrics.slice(0,5).map(function(metric){return'<div class="intelMetric"><span class="intelMetricLabel">'+escapeHtml(metric.label)+'</span><span class="intelMetricValue">'+intelInline(metric.value)+'</span></div>'}).join('')+'</div>';
  return{html:html,consumed:true};
}
function intelList(items,cls,itemCls){
  if(!items.length)return'';
  return '<ul class="'+cls+'">'+items.map(function(item){return'<li class="'+itemCls+'">'+intelInline(intelBulletText(item))+'</li>'}).join('')+'</ul>';
}
function intelVerified(lines,observed){
  var bullets=lines.filter(function(line){return /^[-•]\s+/.test(String(line||'').trim())}),other=lines.filter(function(line){return line.trim()&&!/^[-•]\s+/.test(line.trim())}),grid=intelMetricGrid(bullets),rest=grid.consumed?bullets.slice(1):bullets.slice(),visible=rest.slice(0,3),extra=rest.slice(3),html='<section class="intelSection"><div class="intelSectionTitle"><span>Verified snapshot</span>'+(observed?'<span class="intelObserved">Observed '+escapeHtml(observed)+'</span>':'')+'</div>';
  if(grid.html)html+=grid.html;
  if(visible.length)html+='<div class="intelMore">'+intelList(visible,'intelFactList','intelFact')+'</div>';
  if(other.length)html+='<div class="intelMore">'+other.map(function(line){return'<p class="intelParagraph">'+intelInline(line)+'</p>'}).join('')+'</div>';
  if(extra.length)html+='<details class="intelDisclosure intelMore"><summary>More verified facts <span class="intelDisclosureCount">'+extra.length+'</span></summary><div class="intelDisclosureBody">'+intelList(extra,'intelFactList','intelFact')+'</div></details>';
  return html+'</section>';
}
function intelMatters(lines){
  var bullets=lines.filter(function(line){return /^[-•]\s+/.test(String(line||'').trim())}),other=lines.filter(function(line){return line.trim()&&!/^[-•]\s+/.test(line.trim())}),visible=bullets.slice(0,3),extra=bullets.slice(3),html='<section class="intelSection"><div class="intelSectionTitle"><span>What matters</span></div>';
  if(visible.length)html+=intelList(visible,'intelSignalList','intelSignal');
  if(other.length)html+=other.map(function(line){return'<p class="intelParagraph">'+intelInline(line)+'</p>'}).join('');
  if(extra.length)html+='<details class="intelDisclosure intelMore"><summary>More verified context <span class="intelDisclosureCount">'+extra.length+'</span></summary><div class="intelDisclosureBody">'+intelList(extra,'intelSignalList','intelSignal')+'</div></details>';
  return html+'</section>';
}
function intelNeeds(lines){
  var items=lines.filter(function(line){return line.trim()});
  return '<details class="intelDisclosure"><summary>What ROBERTA still needs <span class="intelDisclosureCount">'+items.length+'</span></summary><div class="intelDisclosureBody">'+intelList(items,'intelNeedList','intelNeed')+'</div></details>';
}
function intelEvidence(line){
  var p=intelPlain(line),value=p.replace(/^Evidence quality\s*:\s*/i,''),m=value.match(/^(STRONG|MODERATE|WEAK|VERIFIED|PARTIAL|UNKNOWN)\b/i),status=m?m[1]:'EVIDENCE',detail=m?value.slice(m[0].length).replace(/^\s*[—:-]\s*/,''):value;
  return '<div class="intelEvidence"><span class="intelEvidenceLabel">Evidence</span>'+intelPill(status)+(detail?'<span class="intelEvidenceText">'+intelInline(detail)+'</span>':'')+'</div>';
}
function intelBottom(line){
  var text=intelPlain(line).replace(/^BOTTOM LINE\s*:\s*/i,'');
  return '<div class="intelBottomLine"><div class="intelBottomLineLabel">ROBERTA</div><div class="intelBottomLineText">'+intelInline(text)+'</div></div>';
}
function intelGenericSection(title,lines){
  var items=lines.filter(function(line){return line.trim()}),bullets=items.filter(function(line){return /^[-•]\s+/.test(line.trim())}),paras=items.filter(function(line){return !/^[-•]\s+/.test(line.trim())}),html='<section class="intelSection"><div class="intelSectionTitle"><span>'+escapeHtml(intelPlain(title).replace(/:$/,''))+'</span></div>';
  if(bullets.length)html+=intelList(bullets,'intelFactList','intelFact');
  if(paras.length)html+=paras.map(function(line){return'<p class="intelParagraph">'+intelInline(line)+'</p>'}).join('');
  return html+'</section>';
}
function formatIntelligenceCard(text){
  var raw=String(text||'').replace(/\r/g,'').trim();
  if(!raw)return'<div class="robertaIntelCard"><div class="intelBody"><p class="intelParagraph">ROBERTA returned no reply.</p></div></div>';
  var lines=raw.split('\n'),firstIndex=lines.findIndex(function(line){return line.trim()});if(firstIndex<0)firstIndex=0;
  var first=intelPlain(lines[firstIndex]),title='ROBERTA',summary='',dash=first.indexOf(' — '),riskMatch=first.match(/\b(BLOCK|WARN|PASS|UNKNOWN)\b/i);
  if(dash>0){title=first.slice(0,dash).trim();summary=first.slice(dash+3).trim().replace(/^what matters right now\s*:\s*/i,'')}
  else{summary=first;}
  var risk=riskMatch?riskMatch[1].toUpperCase():'';
  var html='<div class="robertaIntelCard"><div class="intelHero"><div class="intelEyebrow">ROBERTA read</div><div class="intelTitleRow"><h3 class="intelTitle">'+escapeHtml(title)+'</h3>'+(risk?intelPill(risk):'')+'</div>'+(summary?'<p class="intelSummary">'+intelInline(summary)+'</p>':'')+'</div><div class="intelBody">';
  var i=firstIndex+1,observed='';
  while(i<lines.length){
    if(!lines[i].trim()){i++;continue}
    var type=intelHeadingType(lines[i]);
    if(type==='evidence'){html+=intelEvidence(lines[i]);i++;continue}
    if(type==='bottom'){html+=intelBottom(lines[i]);i++;continue}
    if(type){
      var heading=lines[i],block=[],j=i+1;if(type==='verified')observed=intelObservedFromHeading(heading);
      while(j<lines.length&&!intelHeadingType(lines[j])){block.push(lines[j]);j++}
      if(type==='verified')html+=intelVerified(block,observed);
      else if(type==='matters')html+=intelMatters(block);
      else if(type==='needs')html+=intelNeeds(block);
      else html+=intelGenericSection(heading,block);
      i=j;continue
    }
    var paragraph=[];
    while(i<lines.length&&!intelHeadingType(lines[i])){if(lines[i].trim())paragraph.push(lines[i]);i++}
    if(paragraph.length)html+=paragraph.map(function(line){return'<p class="intelParagraph">'+intelInline(line)+'</p>'}).join('');
  }
  html+='<div class="intelFooter"><span>Analysis only</span><span>Details stay available below</span></div></div></div>';
  return html;
}
'''

_CLEAN_CHAT_APPENDIX = (
    " ROBERTA CLEAN CHAT CONTRACT v1: for normal human single-asset answers, make the "
    "first screen selective rather than exhaustive. Lead with asset identity plus the "
    "current risk/decision status, one short plain-English summary, up to five key "
    "market metrics, and no more than three decision-relevant reasons. Put lower-priority "
    "facts, extra history, missing-evidence detail, and technical caveats after the main "
    "answer so the website can progressively disclose them. State EVIDENCE QUALITY once "
    "and end with one BOTTOM LINE. Do not repeat the same WARN, freshness, or evidence "
    "limitation in multiple sections. Preserve every material unknown and CMIS boundary, "
    "but prioritize the few facts that change the user's decision. Avoid decorative raw "
    "Markdown markers in prose; the web client owns visual emphasis."
)


def apply_intelligence_card_surface(html: str) -> str:
    """Project the clean intelligence-card presentation into the stable web UI."""

    if INTELLIGENCE_CARD_MARKER in html:
        return html

    updated = str(html)
    head_anchor = "</head>"
    if head_anchor not in updated:
        raise RuntimeError("ROBERTA website head contract drifted before intelligence-card overlay.")
    updated = updated.replace(head_anchor, _CARD_STYLE + "\n" + head_anchor, 1)

    if _FORMATTER_ANCHOR not in updated:
        raise RuntimeError("ROBERTA assistant formatter contract drifted before intelligence-card overlay.")
    updated = updated.replace(_FORMATTER_ANCHOR, _CARD_FORMATTER_JS + "\n" + _FORMATTER_ANCHOR, 1)

    if _RENDER_HOOK_OLD not in updated:
        raise RuntimeError("ROBERTA assistant render hook drifted before intelligence-card overlay.")
    updated = updated.replace(_RENDER_HOOK_OLD, _RENDER_HOOK_NEW, 1)
    return updated


def apply_clean_human_output_contract(chat_ui: ModuleType) -> None:
    """Tighten ROBERTA's human answer contract without changing CMIS semantics."""

    human = str(getattr(chat_ui, "HUMAN_ROBERTA_PRESENTATION_POLICY", ""))
    if CLEAN_HUMAN_OUTPUT_MARKER not in human:
        chat_ui.HUMAN_ROBERTA_PRESENTATION_POLICY = human + _CLEAN_CHAT_APPENDIX

    single = str(getattr(chat_ui, "SINGLE_ASSET_TERMINAL_STYLE", ""))
    if CLEAN_HUMAN_OUTPUT_MARKER not in single:
        chat_ui.SINGLE_ASSET_TERMINAL_STYLE = single + _CLEAN_CHAT_APPENDIX


__all__ = [
    "CLEAN_HUMAN_OUTPUT_MARKER",
    "INTELLIGENCE_CARD_MARKER",
    "INTELLIGENCE_CARD_SURFACE",
    "apply_clean_human_output_contract",
    "apply_intelligence_card_surface",
]
