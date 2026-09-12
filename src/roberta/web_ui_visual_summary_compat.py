"""Compatibility renderer for Human ROBERTA visual-summary dashboard v2.

The accepted human answer contract is intentionally narrative-first. This overlay
parses only facts already present in ROBERTA's returned text and projects them
into the Option #2 visual-summary dashboard. It does not call providers, infer
new facts, recompute risk, promote freshness, or authorize execution.
"""
from __future__ import annotations

VISUAL_SUMMARY_COMPAT_SURFACE = "roberta-visual-summary-narrative-compat/v1"
VISUAL_SUMMARY_COMPAT_MARKER = 'id="roberta-visual-summary-narrative-compat-v1"'
_ANCHOR = "function answerActions(chatId){"

_SCRIPT = r'''
/* id="roberta-visual-summary-narrative-compat-v1" */
var _robertaVisualSummaryBaseFormatter=formatIntelligenceCard;
function vscPlain(v){return intelPlain(v)}
function vscLine(raw,re){var lines=String(raw||'').split('\n');for(var i=0;i<lines.length;i++){if(re.test(vscPlain(lines[i])))return lines[i].trim()}return''}
function vscMatch(text,re){var m=vscPlain(text).match(re);return m?(m[1]||'').trim():''}
function vscSigned(direction,value){if(!value)return'';return /^down$/i.test(direction)?'-'+value.replace(/^[+-]/,''):'+'+value.replace(/^[+-]/,'')}
function vscBullets(raw,headingRe,stopRe){var lines=String(raw||'').split('\n'),active=false,out=[];for(var i=0;i<lines.length;i++){var p=vscPlain(lines[i]);if(!active&&headingRe.test(p)){active=true;continue}if(active&&stopRe.test(p))break;if(active&&/^[-•]\s+/.test(lines[i].trim()))out.push(lines[i].trim().replace(/^[-•]\s+/,''))}return out}
function vscRiskComponents(raw){var line=vscLine(raw,/Component statuses\s*:/i)||vscLine(raw,/Risk components?\s*:/i),out=[];['Liquidity','Activity','History','Tokenomics','Freshness'].forEach(function(name){var m=vscPlain(line).match(new RegExp('\\b'+name+'\\s+(PASS|WARN|WARNING|BLOCK|PARTIAL|UNKNOWN|UNVERIFIED)','i'));if(m)out.push({name:name,status:m[1].toUpperCase()})});return out}
function vscMetricCard(label,value,sub){if(!value)return'';return'<div class="intelMetric"><span class="intelMetricLabel">'+escapeHtml(label)+'</span><span class="intelMetricValue">'+intelInline(value)+'</span>'+(sub?'<span class="intelMetricSub">'+intelInline(sub)+'</span>':'')+'</div>'}
function vscNarrativeDashboard(text){
  var raw=String(text||'').replace(/\r/g,'').trim();if(!raw)return'';
  var lines=raw.split('\n'),first='';for(var i=0;i<lines.length;i++){if(lines[i].trim()){first=vscPlain(lines[i]);break}}
  var dash=first.indexOf(' — '),title=dash>0?first.slice(0,dash).trim():first,subtitle=dash>0?first.slice(dash+3).trim():'';
  var headline=vscLine(raw,/^The headline\s*:/i),summary=headline?vscPlain(headline).replace(/^The headline\s*:\s*/i,''):subtitle;
  var riskLine=vscLine(raw,/Deterministic risk recommendation\s*:/i)||vscLine(raw,/Risk recommendation\s*:/i),risk=vscMatch(riskLine,/\b(PASS|WARN|WARNING|BLOCK|UNKNOWN)\b/i).toUpperCase();if(risk==='WARNING')risk='WARN';if(!risk){var rm=vscPlain(raw).match(/\b(WARN|BLOCK)\b/);risk=rm?rm[1].toUpperCase():''}
  var supports=vscBullets(raw,/^What (?:the )?evidence supports\s*:?$/i,/^(?:What's|What is) missing|^Evidence quality|^Bottom line/i);
  var missing=vscBullets(raw,/^(?:What's|What is) missing or unverified\s*:?$/i,/^Evidence quality|^Bottom line/i);
  var priceLine=supports.find(function(x){return /\bPrice\b/i.test(x)})||vscLine(raw,/\bPrice\s+~?\$?[\d,.]+/i);
  var liquidityLine=supports.find(function(x){return /\bLiquidity\b/i.test(x)})||vscLine(raw,/\bLiquidity\s+~?\$?[\d,.]+/i);
  var tokenLine=supports.find(function(x){return /\bTokenomics\s*:/i.test(x)})||vscLine(raw,/\bTokenomics\s*:/i);
  var freshnessLine=missing.find(function(x){return /freshness/i.test(x)})||vscLine(raw,/Live market freshness/i);
  var holderLine=missing.find(function(x){return /Holder count|concentration|distribution/i.test(x)})||vscLine(raw,/Holder count|top-account concentration/i);
  var price=vscMatch(priceLine,/\bPrice\s+~?([$€£]?\s?[\d,.]+)/i);if(price&&!/^[$€£]/.test(price))price='$'+price;
  var liquidity=vscMatch(liquidityLine,/\bLiquidity\s+~?([$€£]?\s?[\d,.]+[KMBT]?)/i);if(liquidity&&!/^[$€£]/.test(liquidity))liquidity='$'+liquidity;
  var volume=vscMatch(liquidityLine,/24h volume\s+~?([$€£]?\s?[\d,.]+[KMBT]?)/i)||vscMatch(raw,/24h volume\s+~?([$€£]?\s?[\d,.]+[KMBT]?)/i);if(volume&&!/^[$€£]/.test(volume))volume='$'+volume;
  var transactions=vscMatch(liquidityLine,/~?([\d,]+)\s+transactions?\b/i)||vscMatch(raw,/~?([\d,]+)\s+transactions?\b/i),lps=vscMatch(liquidityLine,/across\s+([\d,]+)\s+LPs?\b/i);
  var pcm=vscPlain(priceLine).match(/\b(up|down)\s+~?([\d,.]+%)/i),priceChange=pcm?vscSigned(pcm[1],pcm[2]):'';
  var vcm=vscPlain(liquidityLine).match(/\bVolume is\s+(up|down)\s+~?([\d,.]+%)/i),volumeChange=vcm?vscSigned(vcm[1],vcm[2]):'';
  var drawdown=vscMatch(priceLine,/max drawdown[^-+\d]{0,40}([-−+]?\d[\d,.]*%)/i)||vscMatch(raw,/max drawdown[^-+\d]{0,40}([-−+]?\d[\d,.]*%)/i);
  var total=vscMatch(tokenLine,/total supply\s+~?([\d,.]+\s*[KMBT]?)/i),circulating=vscMatch(tokenLine,/circulating\s+~?([\d,.]+\s*[KMBT]?)/i),authority=/mint and freeze authority are not applicable|no active mint\/freeze authority/i.test(vscPlain(tokenLine))?'Not applicable':'Not verified';
  var components=vscRiskComponents(raw),evidenceLine=vscLine(raw,/^Evidence quality\s*:/i),evidenceStatus=vscMatch(evidenceLine,/^Evidence quality\s*:\s*(STRONG|MODERATE|WEAK|VERIFIED|PARTIAL|UNKNOWN)/i).toUpperCase(),evidenceDetail=evidenceLine?vscPlain(evidenceLine).replace(/^Evidence quality\s*:\s*(?:STRONG|MODERATE|WEAK|VERIFIED|PARTIAL|UNKNOWN)\s*[—:-]?\s*/i,''):'';
  var bottomLine=vscLine(raw,/^Bottom line\s*:/i),bottom=bottomLine?vscPlain(bottomLine).replace(/^Bottom line\s*:\s*/i,''):'';
  if(!(price||liquidity||volume||transactions)||!supports.length)return'';
  var html='<div class="robertaIntelCard"><div class="intelHero"><div class="intelIdentity"><div class="intelMark">R</div><div><div class="intelEyebrow">ROBERTA read</div><h3 class="intelTitle">'+escapeHtml(title||'ROBERTA')+'</h3><p class="intelSummary">'+intelInline(summary||subtitle)+'</p></div></div><div class="intelRisk"><div class="intelRiskLabel">Risk read</div>'+(risk?intelPill(risk):'')+'<span class="intelRiskReason">'+intelInline(freshnessLine?freshnessLine:(summary||''))+'</span></div></div>';
  html+='<div class="intelDashboard"><section class="intelPanel"><div class="intelPanelTitle"><span>Market</span><small>returned evidence</small></div><div class="intelPriceRow"><div><span class="intelPriceLabel">Price</span><strong class="intelPrice">'+intelInline(price||'Unknown')+'</strong>'+intelDelta(priceChange)+'</div>'+(priceChange?intelTrendSvg(priceChange):'')+'</div><div class="intelMetrics">'+vscMetricCard('Liquidity',liquidity,lps?lps+' LPs':'')+vscMetricCard('24h volume',volume,volumeChange||'')+vscMetricCard('Transactions',transactions,'24h')+'</div>'+(drawdown?'<div class="intelDrawdown"><span>Max drawdown (sampled)</span><strong>'+intelInline(drawdown)+'</strong></div>':'')+'</section>';
  html+='<div class="intelRight"><section class="intelMini"><div class="intelMiniTitle"><span class="intelIcon">T</span><span>Tokenomics</span></div><div class="intelFacts"><div class="intelFactRow"><span>Total supply</span><strong>'+escapeHtml(total||'Unknown')+'</strong></div><div class="intelFactRow"><span>Circulating</span><strong>'+escapeHtml(circulating||'Unknown')+'</strong></div><div class="intelFactRow"><span>Mint / freeze</span><strong>'+escapeHtml(authority)+'</strong></div></div></section>';
  html+='<section class="intelMini"><div class="intelMiniTitle"><span class="intelIcon">R</span><span>Risk components</span></div><div class="intelRiskGrid">'+components.map(function(c){return'<div class="intelRiskItem"><span class="intelRiskName">'+escapeHtml(c.name)+'</span>'+intelPill(c.status)+'</div>'}).join('')+'</div></section>';
  html+='<section class="intelMini"><div class="intelMiniTitle"><span class="intelIcon">F</span><span>Live market freshness</span>'+intelPill(freshnessLine?'WARN':'UNKNOWN')+'</div><div class="intelMiniText">'+intelInline(freshnessLine||'No freshness statement returned.')+'</div></section>';
  html+='<section class="intelMini"><div class="intelMiniTitle"><span class="intelIcon">H</span><span>Holders / concentration</span>'+intelPill('UNKNOWN')+'</div><div class="intelMiniText">'+intelInline(holderLine||'No holder or concentration statement returned.')+'</div></section></div>';
  if(evidenceLine)html+='<div class="intelEvidence"><span class="intelEvidenceLabel">Evidence</span>'+intelPill(evidenceStatus||'UNKNOWN')+'<span class="intelEvidenceText">'+intelInline(evidenceDetail)+'</span></div>';
  if(bottom)html+='<div class="intelBottomLine"><div class="intelBottomLineLabel">ROBERTA\'S TAKE</div><div class="intelBottomLineText">'+intelInline(bottom)+'</div></div>';
  if(missing.length)html+='<details class="intelDisclosure"><summary>What ROBERTA still needs <span class="intelDisclosureCount">'+missing.length+'</span></summary><div class="intelDisclosureBody"><ul class="intelNeedList">'+missing.map(function(x){return'<li>'+intelInline(x)+'</li>'}).join('')+'</ul></div></details>';
  html+='<details class="intelDisclosure"><summary>Full ROBERTA response</summary><div class="intelDisclosureBody"><p class="intelParagraph">'+intelInline(raw).replace(/\n/g,'<br>')+'</p></div></details><div class="intelFooter"><span>Analysis only</span><span>Details stay available below</span></div></div></div>';return html
}
formatIntelligenceCard=function(text){var dashboard=vscNarrativeDashboard(text);return dashboard||_robertaVisualSummaryBaseFormatter(text)};
'''

def apply_visual_summary_narrative_compat(html: str) -> str:
    """Make dashboard v2 robust to the accepted narrative human-answer format."""
    result = str(html or "")
    if VISUAL_SUMMARY_COMPAT_MARKER in result:
        return result
    if 'id="roberta-intelligence-card-v2"' not in result:
        raise RuntimeError("ROBERTA visual-summary dashboard v2 must be applied first.")
    if _ANCHOR not in result:
        raise RuntimeError("ROBERTA answer-actions anchor is unavailable.")
    return result.replace(_ANCHOR, _SCRIPT + "\n" + _ANCHOR, 1)

__all__ = ["VISUAL_SUMMARY_COMPAT_MARKER", "VISUAL_SUMMARY_COMPAT_SURFACE", "apply_visual_summary_narrative_compat"]
