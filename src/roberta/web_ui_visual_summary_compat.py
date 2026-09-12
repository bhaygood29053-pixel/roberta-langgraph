"""Faithful Option #2 renderer for Human ROBERTA asset intelligence.

The human answer remains narrative-first and evidence-bound. This presentation
layer parses only facts already present in ROBERTA's returned text and projects
asset-style answers into the approved Option #2 visual summary dashboard. It
does not call CMIS/providers, infer new chain facts, recompute risk, promote
freshness, or authorize execution.
"""
from __future__ import annotations

VISUAL_SUMMARY_COMPAT_SURFACE = "roberta-visual-summary-narrative-compat/v1"
VISUAL_SUMMARY_COMPAT_MARKER = 'id="roberta-visual-summary-narrative-compat-v1"'
VISUAL_SUMMARY_FIDELITY_MARKER = 'id="roberta-option2-faithful-v1"'
_ANCHOR = "function answerActions(chatId){"

_STYLE = r'''
<style id="roberta-option2-faithful-v1">
/* Faithful recreation of the approved "Option 2: Visual Summary Dashboard". */
.opt2Card{overflow:hidden;width:100%;border:1px solid rgba(70,126,255,.55);border-radius:22px;background:radial-gradient(circle at 10% 0,rgba(35,73,166,.22),transparent 28%),linear-gradient(180deg,#061224 0%,#050d1a 100%);box-shadow:0 22px 64px rgba(0,0,0,.34);color:#eef4ff}
.opt2Header{display:flex;align-items:center;justify-content:space-between;gap:22px;padding:18px 20px 16px;border-bottom:1px solid rgba(72,115,213,.24)}
.opt2Identity{display:flex;align-items:center;gap:14px;min-width:0}.opt2Logo{width:50px;height:50px;flex:0 0 50px;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle at 32% 24%,#686cff 0,#4250ff 38%,#173bb1 72%,#0b1f55 100%);box-shadow:0 0 26px rgba(74,87,255,.35);font-size:28px;font-weight:1000;color:#d9e4ff}.opt2Title{margin:0;color:#fff;font-size:20px;line-height:1.1;font-weight:950;letter-spacing:-.02em}.opt2Subtitle{margin:5px 0 0;color:#a9b9df;font-size:12px}
.opt2RiskRead{display:grid;grid-template-columns:auto auto;align-items:center;justify-items:end;gap:4px 10px;text-align:right;max-width:310px}.opt2RiskLabel{color:#a9b5d7;font-size:10px;letter-spacing:.1em;text-transform:uppercase}.opt2RiskReason{grid-column:1/-1;color:#b7c4e2;font-size:9px;line-height:1.4;max-width:270px}
.opt2Pill{display:inline-flex;align-items:center;justify-content:center;gap:4px;white-space:nowrap;border-radius:999px;border:1px solid rgba(119,138,184,.3);padding:4px 8px;font-size:9px;font-weight:950;line-height:1}.opt2Pill.good{color:#33f0a2;border-color:rgba(38,232,151,.55);background:rgba(13,96,68,.24)}.opt2Pill.warn{color:#ffd15e;border-color:rgba(255,188,48,.62);background:rgba(118,78,5,.25)}.opt2Pill.bad{color:#ff6f87;border-color:rgba(255,81,111,.56);background:rgba(118,24,44,.24)}.opt2Pill.unknown{color:#9b75ff;border-color:rgba(133,87,255,.58);background:rgba(60,38,122,.22)}.opt2Pill.neutral{color:#b9c5df;background:rgba(51,66,101,.22)}.opt2Pill.big{padding:6px 11px;font-size:12px;color:#111827;background:linear-gradient(180deg,#ffd66d,#ffb52d);border-color:#ffd064;box-shadow:0 0 20px rgba(255,183,45,.18)}
.opt2Body{display:grid;grid-template-columns:minmax(300px,.82fr) minmax(390px,1.18fr);gap:14px;padding:16px}.opt2PriceCard,.opt2Row,.opt2Take,.opt2Details{border:1px solid rgba(67,112,201,.34);background:linear-gradient(180deg,rgba(7,24,46,.92),rgba(4,15,31,.92));border-radius:15px}
.opt2PriceCard{padding:15px}.opt2PriceTop{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.opt2PriceLabel{display:block;color:#d9e4ff;font-size:13px;font-weight:850}.opt2PriceLine{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:5px}.opt2Price{font-size:44px;line-height:1;font-weight:1000;letter-spacing:-.04em;color:#fff}.opt2Delta{border-radius:999px;padding:4px 7px;font-size:10px;font-weight:950}.opt2Delta.pos{color:#27e69a;background:rgba(20,117,79,.28);border:1px solid rgba(41,223,147,.35)}.opt2Delta.neg{color:#ff6f87;background:rgba(124,31,48,.28);border:1px solid rgba(255,85,111,.35)}.opt2Spark{height:92px;margin-top:8px;border-bottom:1px solid rgba(62,105,190,.15);overflow:hidden}.opt2Spark svg{width:100%;height:100%;display:block}.opt2SparkHint{display:block;margin-top:-14px;text-align:right;color:#60749f;font-size:7px}
.opt2Metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin-top:13px}.opt2Metric{min-width:0;border:1px solid rgba(60,104,192,.27);background:rgba(4,15,31,.72);border-radius:10px;padding:10px}.opt2MetricValue{display:block;color:#fff;font-size:16px;font-weight:950;white-space:nowrap}.opt2MetricLabel{display:block;margin-top:4px;color:#c3cfee;font-size:9px}.opt2MetricChange{display:block;margin-top:3px;color:#31e49c;font-size:9px;font-weight:900}.opt2MetricChange.neg{color:#ff6f87}.opt2MetricChange.muted{color:#7082aa;font-weight:700}.opt2Drawdown{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:11px;padding:10px;border:1px solid rgba(55,94,173,.24);border-radius:9px;background:rgba(3,11,25,.62);color:#aebdde;font-size:9px}.opt2Drawdown strong{color:#ff617c;font-size:13px}
.opt2Stack{display:grid;gap:9px}.opt2Row{padding:10px 12px}.opt2RowHead{display:flex;align-items:center;gap:9px}.opt2Icon{width:28px;height:28px;flex:0 0 28px;display:grid;place-items:center;border-radius:8px;background:rgba(19,86,118,.2);color:#33e4b1;font-size:16px;font-weight:900}.opt2Icon.warn{color:#ffc542;background:rgba(123,82,8,.16)}.opt2Icon.unknown{color:#9876ff;background:rgba(71,49,133,.19)}.opt2RowTitle{color:#f3f6ff;font-size:11px;font-weight:900}.opt2RowSpacer{flex:1}.opt2TokenGrid{display:grid;grid-template-columns:1fr 1fr 1.35fr;gap:10px;margin:7px 0 0 37px}.opt2FactLabel{display:block;color:#91a2c9;font-size:8px}.opt2FactValue{display:block;margin-top:2px;color:#fff;font-size:10px;font-weight:850}.opt2FactValue.authority{color:#77bfff}
.opt2RiskGrid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:7px;margin:7px 0 0 37px}.opt2RiskItem{min-width:0;text-align:center;border:1px solid rgba(62,102,183,.28);background:rgba(3,14,29,.64);border-radius:9px;padding:7px 4px}.opt2RiskName{display:block;color:#a8b6d5;font-size:8px;margin-bottom:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.opt2RowText{margin:5px 0 0 37px;color:#b7c4e2;font-size:9px;line-height:1.42}
.opt2Take{grid-column:1/-1;display:grid;grid-template-columns:32px 1fr;gap:10px;padding:12px 14px;border-color:rgba(255,186,54,.7);background:linear-gradient(110deg,rgba(64,52,19,.3),rgba(6,18,39,.95) 48%)}.opt2Bot{width:30px;height:30px;display:grid;place-items:center;border-radius:9px;background:#b7c9ee;color:#17213b;font-size:17px}.opt2TakeLabel{color:#ffd361;font-size:11px;font-weight:1000}.opt2TakeText{margin-top:4px;color:#eef3ff;font-size:10px;line-height:1.55}.opt2EvidenceTag{display:inline-flex;margin-left:8px;vertical-align:middle}
.opt2Details{grid-column:1/-1;overflow:hidden;background:rgba(3,10,23,.6)}.opt2Details>summary{cursor:pointer;list-style:none;padding:9px 12px;color:#8fa3cf;font-size:9px;font-weight:850}.opt2Details>summary:before{content:'＋';margin-right:7px;color:#65bdf8}.opt2Details[open]>summary:before{content:'−'}.opt2DetailsBody{padding:10px 12px;border-top:1px solid rgba(60,101,180,.2);color:#b4c1df;font-size:9px;line-height:1.55}.opt2NeedList{margin:0 0 8px;padding-left:18px}.opt2Raw{margin:0}.opt2Footer{grid-column:1/-1;color:#63749d;font-size:8px;padding:0 2px}
.opt2Card .pos{color:#2ce49a}.opt2Card .neg{color:#ff6f87}.opt2Card code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;color:#b9d3ff}
@media(max-width:880px){.opt2Body{grid-template-columns:1fr}.opt2Take,.opt2Details,.opt2Footer{grid-column:1}.opt2Stack{grid-column:1}.opt2TokenGrid{grid-template-columns:1fr 1fr}.opt2RiskGrid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:560px){.opt2Header{align-items:flex-start;padding:14px}.opt2RiskRead{max-width:170px}.opt2Logo{width:42px;height:42px;flex-basis:42px}.opt2Title{font-size:17px}.opt2Body{padding:10px}.opt2Price{font-size:36px}.opt2Metrics{grid-template-columns:1fr 1fr}.opt2TokenGrid{margin-left:0}.opt2RiskGrid{margin-left:0;grid-template-columns:1fr 1fr}.opt2RowText{margin-left:0}.opt2Take{grid-template-columns:28px 1fr}.opt2Bot{width:28px;height:28px}}
</style>
'''

_SCRIPT = r'''
/* id="roberta-visual-summary-narrative-compat-v1" */
var _robertaVisualSummaryBaseFormatter=formatIntelligenceCard;
function vscPlain(v){return String(v==null?'':v).replace(/\*\*/g,'').replace(/__/g,'').replace(/`/g,'').trim()}
function vscLine(raw,re){var lines=String(raw||'').replace(/\r/g,'').split('\n');for(var i=0;i<lines.length;i++){if(re.test(vscPlain(lines[i])))return lines[i].trim()}return''}
function vscMatch(text,re){var m=vscPlain(text).match(re);return m&&m[1]?(m[1]+'').trim():''}
function vscSigned(direction,value){if(!value)return'';return /^down$/i.test(direction)?'-'+value.replace(/^[+-]/,''):'+'+value.replace(/^[+-]/,'')}
function vscBullets(raw,headingRe,stopRe){var lines=String(raw||'').replace(/\r/g,'').split('\n'),active=false,out=[];for(var i=0;i<lines.length;i++){var p=vscPlain(lines[i]);if(!active&&headingRe.test(p)){active=true;continue}if(active&&stopRe.test(p))break;if(active&&/^[-•]\s+/.test(lines[i].trim()))out.push(lines[i].trim().replace(/^[-•]\s+/,''))}return out}
function vscTone(v){var s=vscPlain(v).toUpperCase();if(/PASS|VERIFIED|STRONG|CLEAR/.test(s))return'good';if(/WARN|WARNING|PARTIAL|MODERATE/.test(s))return'warn';if(/WEAK|BLOCK|FAIL|UNVERIFIED|UNAVAILABLE/.test(s))return'bad';if(/UNKNOWN|NOT VERIFIED|NOT_VERIFIED/.test(s))return'unknown';return'neutral'}
function vscPill(v,big){var s=vscPlain(v).replace(/[.,;:]+$/,'');var shown=s;if(/^WARNING$/i.test(s))shown='⚠ WARNING';else if(/^WARN$/i.test(s))shown='⚠ WARN';else if(/^WEAK$/i.test(s))shown='● WEAK';return'<span class="opt2Pill '+vscTone(s)+(big?' big':'')+'">'+escapeHtml(shown)+'</span>'}
function vscInline(v){var s=escapeHtml(String(v==null?'':v));s=s.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>').replace(/__(.+?)__/g,'<strong>$1</strong>').replace(/`([^`]+)`/g,'<code>$1</code>');s=s.replace(/\b(PASS|WARNING|WARN|BLOCK|PARTIAL|VERIFIED|UNVERIFIED|UNAVAILABLE|UNKNOWN|WEAK|STRONG)\b/g,function(m){return vscPill(m,false)});s=s.replace(/(^|[\s(])([+]\d[\d,.]*%?)(?=$|[\s),.;])/g,'$1<span class="pos">$2</span>').replace(/(^|[\s(])(-\d[\d,.]*%?)(?=$|[\s),.;])/g,'$1<span class="neg">$2</span>');return s}
function vscRiskComponents(raw){var line=vscLine(raw,/Component statuses\s*:/i)||vscLine(raw,/Risk components?\s*:/i),out=[];['Liquidity','Activity','History','Tokenomics','Freshness'].forEach(function(name){var m=vscPlain(line).match(new RegExp('\\b'+name+'\\s+(PASS|WARN|WARNING|BLOCK|PARTIAL|UNKNOWN|UNVERIFIED)','i'));out.push({name:name,status:m?m[1].toUpperCase():'UNKNOWN'})});return out}
function vscComponentStatus(components,name){for(var i=0;i<components.length;i++){if(components[i].name===name)return components[i].status}return'UNKNOWN'}
function vscLooksLikeAssetRead(raw){var p=vscPlain(raw);return /What (?:the )?evidence supports/i.test(p)||(/\bPrice\s+~?\$?[\d,.]+/i.test(p)&&/\bLiquidity\s+~?\$?[\d,.]+/i.test(p))||(/Tokenomics/i.test(p)&&/(?:Component statuses|Risk components)/i.test(p))}
function vscMetric(value,label,change){var cls=/^-/.test(change||'')?' neg':(!change?' muted':'');return'<div class="opt2Metric"><span class="opt2MetricValue">'+escapeHtml(value||'Unknown')+'</span><span class="opt2MetricLabel">'+escapeHtml(label)+'</span><span class="opt2MetricChange'+cls+'">'+escapeHtml(change||'change not verified')+'</span></div>'}
function vscSpark(change){var down=/^-/.test(change||'');var stroke=down?'#ff6f87':'#2ee5a0';var path=down?'M3 20 C14 13 22 28 33 22 S52 30 63 27 S81 39 93 32 S112 36 123 31 S142 24 153 28 S173 18 190 22':'M3 72 C14 60 22 66 33 58 S50 62 62 59 S78 74 91 60 S105 55 117 45 S135 50 146 41 S161 45 174 34 S184 30 190 25';return'<div class="opt2Spark"><svg viewBox="0 0 193 86" preserveAspectRatio="none" aria-label="24h direction visual; not an intraday price series"><defs><linearGradient id="opt2Fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="'+stroke+'" stop-opacity=".28"/><stop offset="1" stop-color="'+stroke+'" stop-opacity="0"/></linearGradient></defs><path d="'+path+' L190 86 L3 86 Z" fill="url(#opt2Fade)"/><path d="'+path+'" fill="none" stroke="'+stroke+'" stroke-width="2.3" stroke-linecap="round"/></svg></div><span class="opt2SparkHint">24h direction visual</span>'}
function vscNarrativeDashboard(text){
  var raw=String(text||'').replace(/\r/g,'').trim();if(!raw||!vscLooksLikeAssetRead(raw))return'';
  var lines=raw.split('\n'),first='';for(var i=0;i<lines.length;i++){if(lines[i].trim()){first=vscPlain(lines[i]);break}}
  var dash=first.indexOf(' — '),title=dash>0?first.slice(0,dash).trim():first;if(/^XNT\s*\(X1\)$/i.test(title))title='XNT (X1 native token)';
  var subtitle='What matters right now';
  var headline=vscLine(raw,/^The headline\s*:/i),headlineText=headline?vscPlain(headline).replace(/^The headline\s*:\s*/i,''):'';
  var supports=vscBullets(raw,/^What (?:the )?evidence supports\s*:?$/i,/^(?:What's|What is) missing|^Evidence quality|^Bottom line/i);
  var missing=vscBullets(raw,/^(?:What's|What is) missing or unverified\s*:?$/i,/^Evidence quality|^Bottom line/i);
  var priceLine=supports.find(function(x){return /^Price\b/i.test(vscPlain(x))})||vscLine(raw,/\bPrice\s+~?\$?[\d,.]+/i);
  var liquidityLine=supports.find(function(x){return /^Liquidity\b/i.test(vscPlain(x))})||vscLine(raw,/\bLiquidity\s+~?\$?[\d,.]+/i);
  var tokenLine=supports.find(function(x){return /^Tokenomics\s*:/i.test(vscPlain(x))})||vscLine(raw,/\bTokenomics\s*:/i);
  var riskLine=supports.find(function(x){return /Deterministic risk recommendation\s*:/i.test(vscPlain(x))})||vscLine(raw,/Deterministic risk recommendation\s*:/i)||vscLine(raw,/Risk recommendation\s*:/i);
  var freshnessLine=missing.find(function(x){return /freshness/i.test(vscPlain(x))})||vscLine(raw,/Live market freshness/i);
  var holderLine=missing.find(function(x){return /Holder count|concentration|distribution/i.test(vscPlain(x))})||vscLine(raw,/Holder count|top-account concentration/i);
  var price=vscMatch(priceLine,/\bPrice\s+~?([$€£]?\s?[\d,.]+)/i);if(price&&!/^[$€£]/.test(price))price='$'+price;
  var liquidity=vscMatch(liquidityLine,/\bLiquidity\s+~?([$€£]?\s?[\d,.]+[KMBT]?)/i);if(liquidity&&!/^[$€£]/.test(liquidity))liquidity='$'+liquidity;
  var volume=vscMatch(liquidityLine,/24h volume\s+~?([$€£]?\s?[\d,.]+[KMBT]?)/i)||vscMatch(raw,/24h volume\s+~?([$€£]?\s?[\d,.]+[KMBT]?)/i);if(volume&&!/^[$€£]/.test(volume))volume='$'+volume;
  var transactions=vscMatch(liquidityLine,/~?([\d,]+)\s+transactions?\b/i)||vscMatch(raw,/~?([\d,]+)\s+transactions?\b/i);
  var pcm=vscPlain(priceLine).match(/\b(up|down)\s+~?([\d,.]+%)/i),priceChange=pcm?vscSigned(pcm[1],pcm[2]):'';
  var lcm=vscPlain(raw).match(/\bLiquidity(?:\s+is)?\s+(up|down)\s+~?([\d,.]+%)/i),liquidityChange=lcm?vscSigned(lcm[1],lcm[2]):'';
  var vcm=vscPlain(liquidityLine).match(/\bVolume is\s+(up|down)\s+~?([\d,.]+%)/i),volumeChange=vcm?vscSigned(vcm[1],vcm[2]):'';
  var drawdown=vscMatch(priceLine,/max drawdown[^-+\d]{0,50}([-−+]?\d[\d,.]*%)/i)||vscMatch(raw,/max drawdown[^-+\d]{0,50}([-−+]?\d[\d,.]*%)/i);
  var total=vscMatch(tokenLine,/total supply\s+~?([\d,.]+\s*[KMBT]?)/i),circulating=vscMatch(tokenLine,/circulating(?: supply)?\s+~?([\d,.]+\s*[KMBT]?)/i);
  var authority=/mint and freeze authority are not applicable|no active mint\/freeze authority|mint\/freeze authority[^.]{0,40}not applicable/i.test(vscPlain(tokenLine))?'Not Applicable':'Not verified';
  var components=vscRiskComponents(raw),risk=vscMatch(riskLine,/\b(PASS|WARN|WARNING|BLOCK|UNKNOWN)\b/i).toUpperCase();if(risk==='WARN')risk='WARNING';if(!risk){var rm=vscPlain(raw).match(/\b(BLOCK|WARN|WARNING)\b/i);risk=rm?rm[1].toUpperCase():'UNKNOWN';if(risk==='WARN')risk='WARNING'}
  var freshnessStatus=vscComponentStatus(components,'Freshness');if(freshnessStatus==='UNKNOWN'&&/not fully verified|unverified/i.test(vscPlain(freshnessLine)))freshnessStatus='WARN';
  var holderStatus=/unavailable|unknown|not promoted|can't tell|cannot tell/i.test(vscPlain(holderLine))?'UNKNOWN':'UNKNOWN';
  var evidenceLine=vscLine(raw,/^Evidence quality\s*:/i),evidenceStatus=vscMatch(evidenceLine,/^Evidence quality\s*:\s*(STRONG|MODERATE|WEAK|VERIFIED|PARTIAL|UNKNOWN)/i).toUpperCase();
  var bottomLine=vscLine(raw,/^Bottom line\s*:/i),bottom=bottomLine?vscPlain(bottomLine).replace(/^Bottom line\s*:\s*/i,''):(headlineText||'ROBERTA returned an evidence-bounded assessment.');
  var riskReason='Evidence gaps remain.';var tokenStatus=vscComponentStatus(components,'Tokenomics');if(/mint\/burn/i.test(vscPlain(raw))&&/freshness/i.test(vscPlain(raw)))riskReason='Driven by unverified freshness and missing mint/burn activity.';else if(/WARN|WARNING/i.test(freshnessStatus)&&/WARN|WARNING/i.test(tokenStatus))riskReason='Driven by freshness and tokenomics evidence gaps.';else if(headlineText)riskReason=headlineText;
  var html='<div class="opt2Card"><div class="opt2Header"><div class="opt2Identity"><div class="opt2Logo">X</div><div><h3 class="opt2Title">'+escapeHtml(title||'ROBERTA asset read')+'</h3><p class="opt2Subtitle">'+escapeHtml(subtitle)+'</p></div></div><div class="opt2RiskRead"><span class="opt2RiskLabel">RISK READ</span>'+vscPill(risk||'UNKNOWN',true)+'<span class="opt2RiskReason">'+escapeHtml(riskReason)+'</span></div></div>';
  html+='<div class="opt2Body"><section class="opt2PriceCard"><span class="opt2PriceLabel">Price</span><div class="opt2PriceLine"><strong class="opt2Price">'+escapeHtml(price||'Unknown')+'</strong>'+(priceChange?'<span class="opt2Delta '+(/^-/.test(priceChange)?'neg':'pos')+'">'+escapeHtml(priceChange)+' (24h)</span>':'')+'</div>'+vscSpark(priceChange)+vscMetric(liquidity,'Liquidity',liquidityChange)+vscMetric(volume,'24h Volume',volumeChange)+vscMetric(transactions,'Transactions','')+(drawdown?'<div class="opt2Drawdown"><span>Max Drawdown (sampled)</span><strong>'+escapeHtml(drawdown)+'</strong></div>':'')+'</section>';
  html+='<div class="opt2Stack"><section class="opt2Row"><div class="opt2RowHead"><span class="opt2Icon">≋</span><span class="opt2RowTitle">Tokenomics</span></div><div class="opt2TokenGrid"><div><span class="opt2FactLabel">Total Supply</span><span class="opt2FactValue">'+escapeHtml(total||'Unknown')+'</span></div><div><span class="opt2FactLabel">Circulating</span><span class="opt2FactValue">'+escapeHtml(circulating||'Unknown')+'</span></div><div><span class="opt2FactLabel">Mint/Freeze Authority</span><span class="opt2FactValue authority">'+escapeHtml(authority)+'</span></div></div></section>';
  html+='<section class="opt2Row"><div class="opt2RowHead"><span class="opt2Icon">◆</span><span class="opt2RowTitle">Risk Components</span></div><div class="opt2RiskGrid">'+components.map(function(c){return'<div class="opt2RiskItem"><span class="opt2RiskName">'+escapeHtml(c.name)+'</span>'+vscPill(c.status,false)+'</div>'}).join('')+'</div></section>';
  html+='<section class="opt2Row"><div class="opt2RowHead"><span class="opt2Icon warn">⌁</span><span class="opt2RowTitle">Live Market Freshness</span><span class="opt2RowSpacer"></span>'+vscPill(freshnessStatus,false)+'</div><div class="opt2RowText">'+vscInline(freshnessLine||'Freshness was not independently verified in the returned answer.')+'</div></section>';
  html+='<section class="opt2Row"><div class="opt2RowHead"><span class="opt2Icon unknown">●</span><span class="opt2RowTitle">Holders / Concentration</span><span class="opt2RowSpacer"></span>'+vscPill(holderStatus,false)+'</div><div class="opt2RowText">'+vscInline(holderLine||'Holder and concentration evidence was not returned.')+'</div></section></div>';
  html+='<section class="opt2Take"><div class="opt2Bot">◉</div><div><span class="opt2TakeLabel">ROBERTA\'S TAKE</span>'+(evidenceStatus?'<span class="opt2EvidenceTag">'+vscPill(evidenceStatus,false)+'</span>':'')+'<div class="opt2TakeText">'+vscInline(bottom)+'</div></div></section>';
  html+='<details class="opt2Details"><summary>Evidence &amp; full ROBERTA response</summary><div class="opt2DetailsBody">'+(missing.length?'<ul class="opt2NeedList">'+missing.map(function(x){return'<li>'+vscInline(x)+'</li>'}).join('')+'</ul>':'')+'<p class="opt2Raw">'+vscInline(raw).replace(/\n/g,'<br>')+'</p></div></details><div class="opt2Footer">Analysis only — no trade execution. Visuals reorganize returned evidence; they do not add facts.</div></div></div>';
  return html
}
formatIntelligenceCard=function(text){var dashboard=vscNarrativeDashboard(text);return dashboard||_robertaVisualSummaryBaseFormatter(text)};
'''


def apply_visual_summary_narrative_compat(html: str) -> str:
    """Project narrative asset answers into the approved Option #2 layout."""
    result = str(html or "")
    if VISUAL_SUMMARY_COMPAT_MARKER in result and VISUAL_SUMMARY_FIDELITY_MARKER in result:
        return result
    if 'id="roberta-intelligence-card-v2"' not in result:
        raise RuntimeError("ROBERTA visual-summary dashboard v2 must be applied first.")
    if _ANCHOR not in result:
        raise RuntimeError("ROBERTA answer-actions anchor is unavailable.")
    if VISUAL_SUMMARY_FIDELITY_MARKER not in result:
        if "</head>" not in result:
            raise RuntimeError("ROBERTA document head is unavailable for Option #2 styling.")
        result = result.replace("</head>", _STYLE + "\n</head>", 1)
    if VISUAL_SUMMARY_COMPAT_MARKER not in result:
        result = result.replace(_ANCHOR, _SCRIPT + "\n" + _ANCHOR, 1)
    return result


__all__ = [
    "VISUAL_SUMMARY_COMPAT_MARKER",
    "VISUAL_SUMMARY_COMPAT_SURFACE",
    "VISUAL_SUMMARY_FIDELITY_MARKER",
    "apply_visual_summary_narrative_compat",
]
