"""Local web interface for ROBERTA — Verified On-Chain Intelligence."""

from __future__ import annotations

ROBERTA_WEB_UI_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light">
<title>ROBERTA — Verified On-Chain Intelligence</title>
<style>
:root{
  --ink:#101326;--ink2:#242945;--muted:#69708a;--paper:#fbfbff;--white:#ffffff;
  --line:#e5e7f0;--violet:#5a4cff;--violet2:#7468ff;--cyan:#bff6ff;--sky:#dfeeff;
  --lav:#e6e1ff;--mint:#c9f7e5;--amber:#fff0c7;--red:#ffdddd;--shadow:0 20px 70px rgba(42,37,104,.12);
  --greenText:#138a57;--greenBg:#e8f8f0;--greenLine:#bcebd4;
  --redText:#c53d46;--redBg:#fff0f1;--redLine:#f2c5c8;
  --amberText:#9b6b00;--amberBg:#fff7df;--amberLine:#efd99c;
  --grayText:#667085;--grayBg:#f3f4f7;--grayLine:#dfe2e8
}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.6 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
button,input,select,textarea{font:inherit}.page{min-height:100vh;overflow:hidden}.shell{width:min(1240px,calc(100% - 40px));margin:auto}
.siteNav{position:sticky;top:0;z-index:30;background:rgba(251,251,255,.88);backdrop-filter:blur(20px);border-bottom:1px solid rgba(229,231,240,.85)}
.navInner{height:78px;display:flex;align-items:center;justify-content:space-between;gap:20px}.brand{display:flex;align-items:center;gap:12px;font-weight:900;letter-spacing:-.02em}
.brandMark{width:46px;height:46px;border-radius:16px;display:grid;place-items:center;background:var(--ink);color:#fff;font-size:18px;box-shadow:0 8px 22px rgba(16,19,38,.16)}
.brandText b{display:block;font-size:17px;line-height:1}.brandText small{display:block;color:var(--muted);font-size:10px;margin-top:5px;font-weight:700;letter-spacing:.04em}
.navLinks{display:flex;gap:6px;align-items:center}.navLinks button{border:0;background:transparent;color:var(--ink2);font-weight:750;padding:10px 13px;border-radius:999px;cursor:pointer}.navLinks button:hover{background:#f0f1f8}
.navActions{display:flex;align-items:center;gap:9px}.pill{display:inline-flex;align-items:center;border:1px solid var(--line);background:#fff;border-radius:999px;padding:8px 12px;color:var(--muted);font-size:12px;white-space:nowrap}.dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#999;margin-right:7px}.online .dot{background:#33c783;box-shadow:0 0 0 5px rgba(51,199,131,.12)}.offline .dot{background:#e45555}
.btn{border:1px solid var(--line);background:#fff;color:var(--ink);padding:11px 17px;border-radius:999px;cursor:pointer;font-weight:800;transition:.18s}.btn:hover{transform:translateY(-1px);box-shadow:0 10px 25px rgba(37,39,72,.08)}.primary{border-color:var(--ink);background:var(--ink);color:#fff}.soft{background:#f0efff;border-color:#dcd8ff;color:#4035c8}
.hero{position:relative;padding:92px 0 72px}.hero:before{content:"";position:absolute;width:680px;height:680px;border-radius:50%;left:50%;top:-310px;transform:translateX(-50%);background:radial-gradient(circle,#c6f5ff 0,#ddd9ff 42%,rgba(251,251,255,0) 72%);filter:blur(10px);opacity:.95;pointer-events:none}
.heroGrid{position:absolute;inset:0;background-image:linear-gradient(rgba(91,76,255,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(91,76,255,.035) 1px,transparent 1px);background-size:48px 48px;mask-image:linear-gradient(to bottom,#000,transparent 72%);pointer-events:none}
.heroInner{position:relative;text-align:center;max-width:1040px;margin:auto}.heroBadge{display:inline-flex;align-items:center;gap:9px;padding:7px 14px;border:1px solid rgba(90,76,255,.18);background:rgba(255,255,255,.78);border-radius:999px;color:#4b42b9;font-size:12px;font-weight:900;letter-spacing:.08em;text-transform:uppercase;box-shadow:0 8px 30px rgba(90,76,255,.07)}
.heroBadge:before{content:"✦";font-size:12px}.hero h1{font-size:clamp(46px,7vw,88px);line-height:.98;letter-spacing:-.066em;margin:24px auto 22px;max-width:1000px}.hero h1 span{background:linear-gradient(90deg,#5145e6,#4d7dff,#45b9d9);-webkit-background-clip:text;background-clip:text;color:transparent}
.heroLead{font-size:clamp(17px,2vw,21px);line-height:1.55;color:var(--muted);max-width:780px;margin:0 auto}.heroBtns{display:flex;justify-content:center;gap:10px;flex-wrap:wrap;margin-top:30px}
.heroStage{margin:62px auto 0;max-width:1080px;position:relative}.stageGlow{position:absolute;inset:8% 5% -8%;background:linear-gradient(120deg,rgba(90,76,255,.28),rgba(191,246,255,.7),rgba(201,247,229,.55));filter:blur(55px);border-radius:50%;z-index:0}
.stageCard{position:relative;z-index:1;border:1px solid rgba(180,183,212,.65);background:rgba(255,255,255,.88);backdrop-filter:blur(18px);border-radius:34px;padding:28px;box-shadow:var(--shadow);overflow:hidden}.stageTop{display:flex;justify-content:space-between;gap:18px;align-items:center;padding-bottom:22px;border-bottom:1px solid var(--line)}.stageTitle{display:flex;align-items:center;gap:12px}.stageOrb{width:52px;height:52px;border-radius:17px;background:linear-gradient(145deg,var(--lav),var(--cyan));display:grid;place-items:center;font-size:21px;font-weight:1000}.stageTitle b{display:block;font-size:17px}.stageTitle small{color:var(--muted)}
.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;align-items:stretch;margin-top:24px}.flowNode{position:relative;border:1px solid var(--line);background:#fff;border-radius:22px;padding:18px 14px;text-align:left;min-height:126px}.flowNode strong{display:block;font-size:13px;margin-bottom:7px}.flowNode span{color:var(--muted);font-size:11px}.flowNode:not(:last-child):after{content:"→";position:absolute;right:-12px;top:46%;z-index:3;width:24px;height:24px;border-radius:50%;background:var(--ink);color:#fff;display:grid;place-items:center;font-size:11px}.flowNode.hot{background:linear-gradient(145deg,#f0efff,#f7feff);border-color:#d9d3ff}.microLabel{display:inline-flex;border-radius:999px;padding:4px 7px;background:#f2f3f8;color:#626a82;font-size:9px;font-weight:900;text-transform:uppercase;letter-spacing:.07em;margin-bottom:10px}
.section{padding:86px 0}.section.alt{background:#fff}.sectionHead{display:grid;grid-template-columns:1fr 1fr;gap:32px;align-items:end;margin-bottom:34px}.eyebrow{font-size:11px;text-transform:uppercase;letter-spacing:.13em;font-weight:950;color:#5145e6}.sectionHead h2{font-size:clamp(34px,4vw,57px);line-height:1.02;letter-spacing:-.045em;margin:8px 0 0;max-width:680px}.sectionHead p{color:var(--muted);font-size:16px;max-width:540px;margin:0 0 5px auto}
.trustStrip{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.trustCard{border:1px solid var(--line);border-radius:28px;padding:25px;background:#fff}.trustIcon{width:44px;height:44px;border-radius:15px;display:grid;place-items:center;background:var(--lav);margin-bottom:22px;font-weight:900}.trustCard:nth-child(2) .trustIcon{background:var(--cyan)}.trustCard:nth-child(3) .trustIcon{background:var(--mint)}.trustCard h3{font-size:18px;margin:0 0 8px}.trustCard p{margin:0;color:var(--muted);font-size:13px}
.serviceTools{display:flex;gap:14px;justify-content:space-between;align-items:center;margin-bottom:22px;flex-wrap:wrap}.search{width:min(380px,100%)}.search input{width:100%;border:1px solid var(--line);background:#fff;color:var(--ink);padding:13px 16px;border-radius:999px;outline:none;box-shadow:0 6px 20px rgba(40,42,78,.04)}.filters{display:flex;gap:7px;flex-wrap:wrap}.filter{border:1px solid var(--line);background:#fff;color:var(--muted);border-radius:999px;padding:8px 12px;cursor:pointer;font-size:11px;font-weight:800}.filter.active{background:var(--ink);color:#fff;border-color:var(--ink)}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.svc{border:1px solid var(--line);background:#fff;border-radius:28px;padding:22px;min-height:236px;display:flex;flex-direction:column;transition:.2s;box-shadow:0 6px 24px rgba(41,44,84,.025)}.svc:hover{transform:translateY(-4px);box-shadow:0 22px 44px rgba(43,45,92,.09);border-color:#d3d2e8}.svcTop{display:flex;justify-content:space-between;gap:10px}.ico{width:48px;height:48px;border-radius:16px;background:linear-gradient(145deg,var(--lav),#f4f2ff);display:grid;place-items:center;font-weight:950;font-size:16px}.svc:nth-child(3n+2) .ico{background:linear-gradient(145deg,var(--cyan),#f4fdff)}.svc:nth-child(3n) .ico{background:linear-gradient(145deg,var(--mint),#f5fffb)}.tag{border:1px solid #d8d5ff;border-radius:999px;padding:5px 9px;color:#5448d6;background:#f3f1ff;font-size:9px;height:max-content;font-weight:900;text-transform:uppercase;letter-spacing:.06em}.tag.advanced,.tag.configured{background:#fff8e7;border-color:#f0dfab;color:#8f6817}.svc h3{font-size:18px;line-height:1.2;margin:20px 0 9px}.svc p{font-size:12.5px;color:var(--muted);margin:0}.svcFoot{margin-top:auto;padding-top:20px;display:flex;justify-content:space-between;align-items:center;color:#8a90a5;font-size:10px}.run{border:0;background:transparent;color:#5145e6;font-weight:900;cursor:pointer}
.productBand{border-radius:36px;background:var(--ink);color:#fff;padding:52px;position:relative;overflow:hidden}.productBand:after{content:"";position:absolute;width:420px;height:420px;border-radius:50%;right:-120px;top:-180px;background:radial-gradient(circle,#6e63ff,#3e4278 45%,transparent 70%);opacity:.8}.bandGrid{position:relative;z-index:1;display:grid;grid-template-columns:1.05fr .95fr;gap:44px;align-items:center}.productBand h2{font-size:clamp(36px,5vw,64px);line-height:1;letter-spacing:-.05em;margin:10px 0 18px}.productBand p{color:#c8cbdd;max-width:590px}.stateList{display:grid;gap:9px}.stateItem{border:1px solid rgba(255,255,255,.13);background:rgba(255,255,255,.055);border-radius:18px;padding:15px 16px;color:#cfd2e2;font-size:12px}.stateItem strong{color:#fff}.stateItem.ok strong{color:#a9f0ce}.stateItem.gate strong{color:#ffe0a3}.crossChain{margin-top:18px;position:relative;z-index:1;border:1px solid rgba(255,255,255,.13);background:rgba(255,255,255,.045);border-radius:24px;padding:20px}.crossChainHead{display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:15px}.crossChainHead b{font-size:14px}.crossChainHead span{color:#b8bdd2;font-size:10px}.crossSteps{display:grid;grid-template-columns:repeat(5,1fr);gap:9px}.crossStep{border:1px solid rgba(255,255,255,.11);background:rgba(255,255,255,.045);border-radius:16px;padding:12px;min-height:106px}.crossStep strong{display:block;font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#a9f0ce;margin-bottom:6px}.crossStep span{font-size:10px;color:#c8cbdd}.crossStep.pending strong{color:#ffe0a3}.crossStep.pending{border-color:rgba(255,224,163,.28)}
.chatLayout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:18px}.chat,.info{border:1px solid var(--line);background:#fff;border-radius:30px;overflow:hidden;box-shadow:0 18px 50px rgba(41,44,84,.07)}.chatHead{padding:18px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px}.chatHeadActions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.chatTitle{font-size:17px;font-weight:950;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:4px}.messages{height:650px;min-height:650px;overflow:auto;padding:24px;display:flex;flex-direction:column;gap:14px;background:linear-gradient(180deg,#fcfcff,#f8f9ff)}.msg{max-width:90%;padding:14px 16px;border-radius:18px;white-space:pre-wrap;word-break:break-word}.msg.user{align-self:flex-end;background:var(--ink);color:#fff;border-bottom-right-radius:6px}.msg.assistant{align-self:flex-start;background:#fff;border:1px solid var(--line);color:var(--ink2);border-bottom-left-radius:6px}.msg.system{align-self:center;color:var(--muted);font-size:11px;padding:3px}.msgTitle{display:block;font-weight:950;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px;margin:2px 0 5px;color:var(--ink)}.statusToken{display:inline-flex;align-items:center;padding:1px 7px;border-radius:999px;border:1px solid var(--grayLine);background:var(--grayBg);color:var(--grayText);font-weight:900;font-size:.9em}.statusToken.pass,.statusToken.verified,.statusToken.ok,.statusToken.clear,.statusToken.available,.statusToken.strong{background:var(--greenBg);border-color:var(--greenLine);color:var(--greenText)}.statusToken.warn,.statusToken.partial,.statusToken.watch,.statusToken.caution,.statusToken.moderate{background:var(--amberBg);border-color:var(--amberLine);color:var(--amberText)}.statusToken.block,.statusToken.error,.statusToken.unverified,.statusToken.unavailable,.statusToken.notverified,.statusToken.weak{background:var(--redBg);border-color:var(--redLine);color:var(--redText)}.signedPositive{color:var(--greenText);font-weight:900}.signedNegative{color:var(--redText);font-weight:900}.composer{border-top:1px solid var(--line);padding:16px;display:grid;grid-template-columns:1fr auto;gap:10px}.composer textarea{resize:vertical;min-height:100px;max-height:260px;border:1px solid var(--line);background:#f8f9fd;color:var(--ink);border-radius:18px;padding:14px 15px;outline:none}.info{padding:22px}.info h3{font-size:18px;margin:0 0 12px}.infoBlock{border-top:1px solid var(--line);padding:15px 0}.infoBlock:first-of-type{border-top:0}.infoBlock b{display:block;color:var(--ink);font-size:10px;text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px}.infoBlock span{color:var(--muted);font-size:12px}.historyPanel{border-bottom:1px solid var(--line);background:#fbfbfe;padding:12px 14px;display:none}.historyPanel.open{display:block}.historyTop{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}.historyTop b{font-size:12px}.historyList{display:grid;gap:7px;max-height:220px;overflow:auto}.historyItem{border:1px solid var(--line);background:#fff;border-radius:14px;padding:9px 11px;cursor:pointer;text-align:left}.historyItem:hover{border-color:#cbc7ff;background:#f9f8ff}.historyItemTitle{display:block;font-weight:900;text-decoration:underline;text-underline-offset:2px;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.historyItemTime{display:block;color:var(--muted);font-size:9px;margin-top:2px}.historyEmpty{color:var(--muted);font-size:11px;padding:8px}.btn.small{padding:7px 10px;font-size:10px}
.settings{display:none;position:fixed;z-index:60;right:24px;top:86px;width:min(390px,calc(100vw - 48px));background:#fff;border:1px solid var(--line);border-radius:24px;padding:18px;box-shadow:var(--shadow)}.settings.open{display:block}.settings h3{margin:0 0 12px}.settings .field+.field{margin-top:10px}.note{color:var(--muted);font-size:10px;margin-top:10px}
.modalBg{display:none;position:fixed;inset:0;z-index:70;background:rgba(16,19,38,.52);backdrop-filter:blur(8px);padding:18px;place-items:center}.modalBg.open{display:grid}.modal{width:min(640px,100%);max-height:90vh;overflow:auto;background:#fff;border:1px solid var(--line);border-radius:30px;box-shadow:var(--shadow)}.modalHead{padding:22px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:12px}.modalHead h3{margin:0;font-size:22px}.modalHead p{color:var(--muted);font-size:12px;margin:5px 0 0}.close{width:36px;height:36px;border:1px solid var(--line);border-radius:50%;background:#fff;color:var(--ink);cursor:pointer}.form{padding:20px;display:grid;gap:14px}.field{display:grid;gap:6px}.field label{color:var(--ink2);font-size:11px;font-weight:800}.field input,.field select{border:1px solid var(--line);background:#fbfbfe;color:var(--ink);padding:12px 13px;border-radius:14px;outline:none}.modalActions{padding:0 20px 20px;display:flex;justify-content:flex-end;gap:8px}
.footer{padding:34px 0 48px;border-top:1px solid var(--line);color:var(--muted);font-size:11px}.footerInner{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}
@media(max-width:1050px){.navLinks{display:none}.flow{grid-template-columns:1fr 1fr}.flowNode:not(:last-child):after{display:none}.crossSteps{grid-template-columns:1fr 1fr}.grid{grid-template-columns:repeat(2,1fr)}.sectionHead{grid-template-columns:1fr}.sectionHead p{margin:0}.bandGrid{grid-template-columns:1fr}.chatLayout{grid-template-columns:1fr}.info{display:none}.trustStrip{grid-template-columns:1fr}}
@media(max-width:680px){.crossSteps{grid-template-columns:1fr}.crossChainHead{align-items:flex-start;flex-direction:column}.shell{width:min(100% - 24px,1240px)}.navInner{height:68px}.brandText small,.navActions .pill{display:none}.hero{padding:64px 0 52px}.hero h1{font-size:48px}.stageCard{padding:18px;border-radius:24px}.stageTop{align-items:flex-start;flex-direction:column}.flow{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.section{padding:62px 0}.sectionHead h2{font-size:39px}.serviceTools{align-items:stretch;flex-direction:column}.search{width:100%}.productBand{padding:30px 22px;border-radius:28px}.heroBtns{display:grid}.heroBtns .btn{width:100%}.composer{grid-template-columns:1fr}.navActions .btn{padding:9px 12px}.messages{height:520px;min-height:520px}}
</style>

<style id="roberta-visual-redesign">
:root{
  --ink:#f4f6ff;--ink2:#d9def7;--muted:#98a1c8;--paper:#050817;--white:#0a0f24;
  --line:rgba(126,150,255,.18);--violet:#7a5cff;--violet2:#945eff;--cyan:#4dc8ff;--sky:#0b1736;
  --lav:#17143d;--mint:#0f2d31;--amber:#2f2611;--red:#31131a;--shadow:0 24px 80px rgba(0,0,0,.42);
  --greenText:#7ef0bb;--greenBg:rgba(31,120,82,.16);--greenLine:rgba(91,221,158,.24);
  --redText:#ff8b96;--redBg:rgba(150,44,58,.16);--redLine:rgba(255,117,131,.24);
  --amberText:#ffd47f;--amberBg:rgba(145,105,23,.16);--amberLine:rgba(255,207,112,.24);
  --grayText:#aab2d0;--grayBg:rgba(140,150,190,.10);--grayLine:rgba(164,177,222,.18)
}
html{background:#050817}
body{
  color:var(--ink);
  background:
    radial-gradient(circle at 22% 8%,rgba(56,82,196,.18),transparent 24%),
    radial-gradient(circle at 78% 12%,rgba(115,58,211,.12),transparent 22%),
    linear-gradient(180deg,#050817 0%,#070a19 45%,#050714 100%);
  font-family:"Avenir Next","Century Gothic","Trebuchet MS",Inter,ui-sans-serif,system-ui,sans-serif
}
body:before{content:"";position:fixed;inset:0;pointer-events:none;z-index:-1;background-image:linear-gradient(rgba(92,122,255,.028) 1px,transparent 1px),linear-gradient(90deg,rgba(92,122,255,.028) 1px,transparent 1px);background-size:72px 72px;mask-image:linear-gradient(to bottom,rgba(0,0,0,.65),transparent 82%)}
.siteNav{background:rgba(5,8,23,.82);border-bottom:1px solid rgba(118,139,255,.14);backdrop-filter:blur(24px) saturate(140%)}
.navInner{height:82px}.brand{letter-spacing:.22em}.brandMark{border-radius:8px;background:linear-gradient(145deg,#5aa8ff,#8e4dff);box-shadow:0 0 28px rgba(103,103,255,.28);font-weight:800}.brandText b{font-size:18px;letter-spacing:.32em;font-weight:500}.brandText small{color:#9fa9d6;letter-spacing:.16em}
.navLinks button{color:#f7f8ff;font-weight:500;letter-spacing:.06em;text-transform:uppercase;font-size:12px}.navLinks button:hover{background:rgba(105,127,255,.08);color:#67c9ff}
.pill{background:rgba(11,16,38,.84);border-color:rgba(139,158,255,.2);color:#aeb8dc}.btn{background:rgba(10,15,37,.72);border-color:rgba(126,150,255,.28);color:#f7f8ff}.btn:hover{box-shadow:0 12px 35px rgba(54,87,255,.16);border-color:rgba(88,194,255,.46)}.primary{background:linear-gradient(100deg,#347dff 0%,#744dff 55%,#a147ff 100%);border-color:transparent;box-shadow:0 0 30px rgba(90,89,255,.24)}.soft{background:rgba(19,28,64,.82);border-color:rgba(78,191,255,.36);color:#bcecff}
.hero.robertaHero{padding:0;min-height:calc(100vh - 82px);display:flex;align-items:center;overflow:hidden}.robertaHero:before{display:none}.robertaHero .heroGrid{background-size:80px 80px;opacity:.65;mask-image:linear-gradient(to right,transparent 0,#000 15%,#000 82%,transparent 100%)}.heroSplit{position:relative;display:grid;grid-template-columns:minmax(390px,.82fr) minmax(560px,1.18fr);align-items:center;gap:22px;min-height:calc(100vh - 82px);padding:48px 0}.heroCopy{position:relative;z-index:4;padding:34px 0 44px}.heroCopy .heroBadge{background:transparent;border:0;padding:0;color:#66c9ff;box-shadow:none;letter-spacing:.28em;font-weight:500}.heroCopy .heroBadge:before{display:none}.heroCopy h1{font-size:clamp(72px,8vw,126px);letter-spacing:.055em;margin:14px 0 12px;max-width:none;font-weight:300}.heroCopy h1 span{background:linear-gradient(90deg,#ffffff 0%,#edf5ff 36%,#7bc9ff 82%,#936bff 100%);-webkit-background-clip:text;background-clip:text;color:transparent;text-shadow:0 0 45px rgba(83,159,255,.08)}.heroTagline{font-size:clamp(20px,2vw,28px);line-height:1.45;max-width:650px;margin:0 0 26px;color:#f2f5ff;font-weight:300}.heroCopy .heroLead{font-size:15px;line-height:1.8;color:#929bc0;max-width:610px;margin:0}.heroCopy .heroBtns{justify-content:flex-start;margin-top:28px}.heroSignals{display:flex;flex-wrap:wrap;gap:10px;margin-top:30px}.heroSignals span{display:inline-flex;align-items:center;gap:6px;border:1px solid rgba(101,132,255,.17);border-radius:999px;padding:8px 11px;background:rgba(8,13,31,.56);color:#8f99c1;font-size:10px;letter-spacing:.04em}.heroSignals b{color:#dce8ff;font-weight:600}
.heroVisual{position:relative;z-index:2;height:min(720px,76vh);min-height:560px;border-left:1px solid rgba(111,139,255,.10);isolation:isolate}.heroVisual:before{content:"";position:absolute;inset:4% 0 3% 4%;border-radius:50%;background:radial-gradient(circle at 49% 50%,rgba(41,91,255,.13),transparent 32%),radial-gradient(circle at 76% 48%,rgba(120,64,255,.09),transparent 28%);filter:blur(8px);z-index:-1}.heroVisual canvas{position:absolute;inset:0;width:100%;height:100%;display:block}.heroCoreMark{position:absolute;right:14%;top:43%;width:104px;height:104px;border-radius:50%;display:grid;place-items:center;font-size:48px;font-weight:800;font-style:italic;color:#785cff;background:radial-gradient(circle at 50% 45%,rgba(43,71,178,.44),rgba(5,9,25,.93) 68%);border:1px solid rgba(101,183,255,.7);box-shadow:0 0 26px rgba(42,143,255,.34),inset 0 0 24px rgba(93,74,255,.28);text-shadow:0 0 24px rgba(125,90,255,.65);transform:translate(50%,-50%)}.heroCoreMark:after{content:"";position:absolute;inset:-28px;border-radius:50%;border:1px solid rgba(96,127,255,.20);animation:corePulse 4s ease-in-out infinite}
.heroOrbitLabel{position:absolute;display:grid;grid-template-columns:38px auto;grid-template-rows:auto auto;column-gap:9px;align-items:center;color:#edf1ff;font-size:9px;letter-spacing:.08em;text-shadow:0 0 12px rgba(0,0,0,.8);pointer-events:none}.heroOrbitLabel small{grid-column:2;color:#8c98c1;font-size:8px;letter-spacing:.10em}.orbitIcon{grid-row:1/3;width:38px;height:38px;border:1px solid rgba(95,155,255,.55);border-radius:50%;display:grid;place-items:center;color:#b9e8ff;background:rgba(8,14,34,.78);box-shadow:0 0 18px rgba(79,100,255,.20);font-size:15px}.orbitMarket{right:7%;top:16%}.orbitRisk{right:0;top:31%}.orbitBridge{right:-1%;top:62%}.orbitProof{right:10%;bottom:11%}.orbitFresh{right:39%;bottom:7%}.orbitBurn{right:48%;top:24%}.motionStatus{position:absolute;left:4%;bottom:4%;display:flex;align-items:center;gap:8px;color:#7180b3;font-size:8px;letter-spacing:.22em}.motionStatus span{width:6px;height:6px;border-radius:50%;background:#55cfff;box-shadow:0 0 12px #55cfff;animation:statusBlink 2s ease-in-out infinite}
@keyframes corePulse{0%,100%{transform:scale(.95);opacity:.35}50%{transform:scale(1.08);opacity:.72}}@keyframes statusBlink{0%,100%{opacity:.35}50%{opacity:1}}
.section{position:relative}.section.alt{background:rgba(7,10,26,.64);border-top:1px solid rgba(117,139,255,.10);border-bottom:1px solid rgba(117,139,255,.10)}.sectionHead p,.trustCard p,.svc p,.infoBlock span,.note{color:#929bc0}.eyebrow{color:#66c9ff;letter-spacing:.22em;font-weight:600}.trustCard,.svc,.chat,.info,.modal,.historyItem{background:linear-gradient(180deg,rgba(13,18,43,.92),rgba(8,13,31,.92));border-color:rgba(122,145,255,.17);box-shadow:0 16px 44px rgba(0,0,0,.20)}.trustCard:hover,.svc:hover{border-color:rgba(86,192,255,.35);box-shadow:0 22px 55px rgba(18,47,123,.20)}.trustIcon,.ico{background:linear-gradient(145deg,rgba(50,89,204,.30),rgba(116,66,226,.22));color:#8ed9ff;border:1px solid rgba(105,162,255,.22)}.trustCard:nth-child(2) .trustIcon,.trustCard:nth-child(3) .trustIcon,.svc:nth-child(3n+2) .ico,.svc:nth-child(3n) .ico{background:linear-gradient(145deg,rgba(38,117,184,.22),rgba(103,58,194,.18))}.search input,.field input,.field select,.composer textarea{background:#080d21;border-color:rgba(122,145,255,.18);color:#eef2ff}.filter{background:#090f25;border-color:rgba(122,145,255,.18);color:#9da7cd}.filter.active{background:linear-gradient(100deg,#347dff,#744dff);border-color:transparent}.tag{background:rgba(82,68,220,.14);border-color:rgba(123,111,255,.28);color:#b4a8ff}.tag.advanced,.tag.configured{background:rgba(154,108,22,.12);border-color:rgba(240,194,91,.25);color:#ffd47f}.productBand{background:linear-gradient(140deg,#080d23,#101536 60%,#15113b);border:1px solid rgba(119,143,255,.18)}.messages{background:linear-gradient(180deg,#060a19,#080d20)}.msg.assistant{background:#0d132d;border-color:rgba(122,145,255,.18);color:#dce2fb}.msg.user{background:linear-gradient(100deg,#285dca,#6541cc)}.historyPanel{background:#080d20;border-color:rgba(122,145,255,.14)}.settings{background:#0a1027;border-color:rgba(122,145,255,.20)}.footer{border-color:rgba(122,145,255,.13)}
@media(max-width:1180px){.heroSplit{grid-template-columns:1fr;gap:0;padding-top:56px}.hero.robertaHero{min-height:auto}.heroCopy{text-align:center;padding-bottom:8px}.heroCopy .heroLead,.heroTagline{margin-left:auto;margin-right:auto}.heroCopy .heroBtns,.heroSignals{justify-content:center}.heroVisual{height:600px;min-height:520px;border-left:0}.heroCoreMark{right:19%}.orbitRisk,.orbitBridge{right:3%}}
@media(max-width:760px){.heroSplit{padding-top:32px}.heroCopy h1{font-size:clamp(56px,18vw,84px)}.heroTagline{font-size:19px}.heroVisual{height:470px;min-height:430px;margin:0 -8px}.heroCoreMark{width:78px;height:78px;font-size:36px;right:19%;top:45%}.heroOrbitLabel{transform:scale(.82);transform-origin:center}.orbitMarket{right:2%;top:10%}.orbitRisk{right:-3%;top:28%}.orbitBridge{right:-4%;top:67%}.orbitProof{right:4%;bottom:6%}.orbitFresh{right:38%;bottom:2%}.orbitBurn{right:48%;top:17%}.heroSignals{display:none}}
@media(prefers-reduced-motion:reduce){.heroCoreMark:after,.motionStatus span{animation:none!important}}
</style>

<style id="roberta-wind-wrap-v2">
.heroVisual{
  background:
    radial-gradient(circle at 51% 46%,rgba(47,104,255,.10),transparent 24%),
    radial-gradient(circle at 74% 45%,rgba(121,72,255,.07),transparent 20%);
}
.heroVisual:after{
  content:"";
  position:absolute;
  left:5%;
  top:8%;
  width:63%;
  height:84%;
  pointer-events:none;
  background:linear-gradient(90deg,rgba(5,8,23,.94),rgba(5,8,23,0) 38%);
  opacity:.18;
  mix-blend-mode:multiply;
}
.heroVisual canvas{filter:saturate(1.08) contrast(1.03)}
.heroCoreMark{right:13%;top:46%}
.orbitMarket{right:5%;top:12%}.orbitRisk{right:-1%;top:29%}.orbitBridge{right:-2%;top:62%}.orbitProof{right:8%;bottom:8%}.orbitFresh{right:38%;bottom:5%}.orbitBurn{right:45%;top:22%}
@media(max-width:1180px){
  .heroCoreMark{right:18%;top:46%}
}
@media(max-width:760px){
  .heroCoreMark{right:17%;top:46%}
  .orbitMarket{right:0;top:8%}.orbitRisk{right:-5%;top:26%}.orbitBridge{right:-5%;top:66%}
}
</style>

</head>
<body>
<div class="page">
  <header class="siteNav">
    <div class="shell navInner">
      <div class="brand">
        <div class="brandMark">R</div>
        <div class="brandText"><b>ROBERTA</b><small>VERIFIED ON-CHAIN INTELLIGENCE</small></div>
      </div>
      <nav class="navLinks">
        <button data-go="home">About</button>
        <button data-go="services">Intelligence</button>
        <button data-go="trust">Research</button>
        <button data-go="roadmap">Roadmap</button>
        <button data-go="chat">Contact</button>
      </nav>
      <div class="navActions">
        <div id="health" class="pill"><span class="dot"></span>Checking ROBERTA…</div>
        <button class="btn" id="settingsBtn">Connection</button>
      </div>
    </div>
  </header>

  <div id="settings" class="settings">
    <h3>Connection</h3>
    <div class="field"><label>ROBERTA bridge URL</label><input id="apiBase" placeholder="Same origin"></div>
    <div class="field"><label>Bearer token (if configured)</label><input id="apiKey" type="password" autocomplete="off" placeholder="ROBERTA_API_KEY"></div>
    <div class="note">Connection values stay in this browser tab only. Default loopback use needs no token.</div>
  </div>

  <main>
    <section id="home" class="hero robertaHero">
      <div class="heroGrid" aria-hidden="true"></div>
      <div class="shell heroSplit">
        <div class="heroCopy">
          <div class="heroBadge">VERIFIED ON-CHAIN INTELLIGENCE</div>
          <h1><span>ROBERTA</span></h1>
          <p class="heroTagline">Evidence-first intelligence for X1, cross-chain routes, market structure, and risk.</p>
          <p class="heroLead">ROBERTA coordinates the accepted Scout → CMIS evidence path, preserves exact asset identity and uncertainty, and explains what can be proven without turning analysis into execution.</p>
          <div class="heroBtns">
            <button class="btn primary" data-svc="full">Explore Capabilities</button>
            <button class="btn soft" data-go="chat">Ask ROBERTA</button>
            <button class="btn" data-svc="scan">Instant X1 Scan</button>
          </div>
          <div class="heroSignals" aria-label="ROBERTA operating principles">
            <span><b>CMIS 1.18</b> verified path</span>
            <span><b>Human + Machine</b> one truth</span>
            <span><b>Read-only</b> execution remains unauthorized · execution_authorized=false</span>
          </div>
        </div>

        <div class="heroVisual" aria-label="Animated ROBERTA intelligence field">
          <canvas id="robertaHeroCanvas" role="img" aria-label="Animated luminous profile with wind-like intelligence ribbons wrapping from the head and fading behind it"></canvas>
          <div class="heroCoreMark" aria-hidden="true">R</div>
          <div class="heroOrbitLabel orbitMarket"><span class="orbitIcon">▥</span><b>MARKET</b><small>INTELLIGENCE</small></div>
          <div class="heroOrbitLabel orbitRisk"><span class="orbitIcon">◇</span><b>RISK</b><small>ANALYSIS</small></div>
          <div class="heroOrbitLabel orbitBridge"><span class="orbitIcon">↔</span><b>CROSS-CHAIN</b><small>ROUTES</small></div>
          <div class="heroOrbitLabel orbitProof"><span class="orbitIcon">✓</span><b>VERIFIED</b><small>EVIDENCE</small></div>
          <div class="heroOrbitLabel orbitFresh"><span class="orbitIcon">◷</span><b>FRESHNESS</b><small>BY FIELD</small></div>
          <div class="heroOrbitLabel orbitBurn"><span class="orbitIcon">△</span><b>BURN</b><small>INTELLIGENCE</small></div>
          <div class="motionStatus"><span></span>LIVE VERIFIED NETWORK</div>
        </div>
      </div>
    </section>

    <section id="trust" class="section alt">
      <div class="shell">
        <div class="sectionHead">
          <div><div class="eyebrow">Built for trust</div><h2>Verified intelligence without hiding the uncertainty.</h2></div>
          <p>ROBERTA is designed to distinguish what is verified, what is merely observed, and what is still unavailable—so a polished answer never outruns the evidence.</p>
        </div>
        <div class="trustStrip">
          <article class="trustCard"><div class="trustIcon">✓</div><h3>Evidence before confidence</h3><p>Fresh accepted CMIS/provider evidence overrides remembered or learned live values. Missing evidence stays UNKNOWN or UNAVAILABLE.</p></article>
          <article class="trustCard"><div class="trustIcon">◇</div><h3>Proof stays separate from risk</h3><p>Evidence quality and deterministic risk are different dimensions. Strong proof can still support a WARN or BLOCK result.</p></article>
          <article class="trustCard"><div class="trustIcon">↗</div><h3>Analysis, not execution</h3><p>Website actions never call CMIS directly. Signing, broadcast, custody, swaps, bridge transfers and autonomous value movement remain unauthorized.</p></article>
        </div>
      </div>
    </section>

    <section id="services" class="section">
      <div class="shell">
        <div class="sectionHead">
          <div><div class="eyebrow">Capabilities</div><h2>One ROBERTA. A full suite of accepted intelligence services.</h2></div>
          <p>Choose a capability instead of memorizing commands. Each card sends a bounded request through the same ROBERTA → Scout → CMIS authority path.</p>
        </div>
        <div class="serviceTools">
          <div id="filters" class="filters"></div>
          <div class="search"><input id="search" type="search" placeholder="Search ROBERTA capabilities…"></div>
        </div>
        <div id="grid" class="grid"></div>
      </div>
    </section>

    <section id="roadmap" class="section alt">
      <div class="shell">
        <div class="productBand">
          <div class="bandGrid">
            <div>
              <div class="eyebrow" style="color:#aeb2ff">Current product state</div>
              <h2>X1-first today. Multi-chain by verified adoption.</h2>
              <p>ROBERTA expands only when the evidence contract and chain-specific authority path are accepted. The interface deliberately does not imply feature parity where it does not exist.</p>
              <div class="heroBtns" style="justify-content:flex-start"><button class="btn" data-svc="key">View status key</button><button class="btn soft" data-go="chat">Ask about availability</button></div>
            </div>
            <div class="stateList">
              <div class="stateItem ok"><strong>Accepted X1:</strong> Instant X1 Scan v3, Burn, Discovery, What Changed, Compare and current-market freshness.</div>
              <div class="stateItem ok"><strong>Accepted warning:</strong> CMIS 1.18 pull-only Concentration Warning through ROBERTA.</div>
              <div class="stateItem ok"><strong>Warp evidence:</strong> Exact route/config semantics, real settled-transfer pairing, wallet-history corroboration, and current message-universe closure are accepted foundations.</div>
              <div class="stateItem gate"><strong>Still gated:</strong> Route-wide 24h/7d/30d bridge-flow totals and verified bridged supply remain unavailable. Active sequence: CMIS #441 → #409 → #410 → ROBERTA #314.</div>
              <div class="stateItem ok"><strong>Solana:</strong> Market, tokenomics and risk only when the accepted provider path is explicitly configured.</div>
              <div class="stateItem"><strong>Learning:</strong> The Learning Command Center remains a separate read-only operator surface; this market UI does not start or mutate training.</div>
            </div>
          </div>
          <div class="crossChain">
            <div class="crossChainHead"><div><b>Warp / cross-chain evidence progress</b><br><span>Accepted CMIS foundations are visible here, but they are not yet a runnable ROBERTA bridge-flow service.</span></div><span>CMIS 1.18 · September 3 checkpoint</span></div>
            <div class="crossSteps">
              <div class="crossStep"><strong>Accepted</strong><span>Exact official Warp config semantics for provenance-qualified mint pairs.</span></div>
              <div class="crossStep"><strong>Accepted</strong><span>Canonical settled events from exact on-chain OutgoingMsg / IncomingMsg pairing.</span></div>
              <div class="crossStep"><strong>Accepted</strong><span>Wallet-history response semantics as corroboration only, not settlement authority.</span></div>
              <div class="crossStep"><strong>Accepted</strong><span>Current Warp message-universe counter/account closure.</span></div>
              <div class="crossStep pending"><strong>Active gate</strong><span>#441 retention proof → finish #409 flow + supply → #410 utilization → ROBERTA #314 adoption.</span></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="chat" class="section">
      <div class="shell">
        <div class="sectionHead">
          <div><div class="eyebrow">Conversational intelligence</div><h2>Ask ROBERTA the way you would ask an analyst.</h2></div>
          <p>Normal-language access reaches the same verified intelligence core as the service cards. ROBERTA chooses the appropriate specialist path.</p>
        </div>
        <div class="chatLayout">
          <div class="chat">
            <div class="chatHead">
              <div><div class="chatTitle">ROBERTA</div><div style="color:var(--muted);font-size:10px">Verified On-Chain Intelligence</div></div>
              <div class="chatHeadActions"><button id="historyBtn" class="btn small">Previous chats</button><button id="clearChat" class="btn small">Clear chat</button><span class="tag">Analysis only</span></div>
            </div>
            <div id="historyPanel" class="historyPanel">
              <div class="historyTop"><b>Previous chats</b><button id="clearHistory" class="btn small">Clear history</button></div>
              <div id="historyList" class="historyList"></div>
            </div>
            <div id="messages" class="messages"></div>
            <div class="composer"><textarea id="composer" rows="4" placeholder="Ask ROBERTA anything about an accepted intelligence service…"></textarea><button id="send" class="btn primary">Send</button></div>
          </div>
          <aside class="info">
            <h3>Trust model</h3>
            <div class="infoBlock"><b>Fresh facts</b><span>Accepted CMIS/provider evidence overrides remembered or learned live values.</span></div>
            <div class="infoBlock"><b>Unknowns</b><span>Missing evidence stays UNKNOWN / UNAVAILABLE. It is never zero-filled.</span></div>
            <div class="infoBlock"><b>Human-first output</b><span>Normal answers group related evidence gaps, hide internal diagnostic codes, and show only the three highest-priority missing items that materially affect the conclusion. Full audit detail remains in the underlying evidence.</span></div>
            <div class="infoBlock"><b>Proof vs risk</b><span>Evidence quality is separate from deterministic risk.</span></div>
            <div class="infoBlock"><b>Execution</b><span>No result authorizes signing, broadcast, custody, swaps, bridge transfers, or autonomous value movement. Execution remains unauthorized.</span></div>
          </aside>
        </div>
      </div>
    </section>
  </main>

  <footer class="footer">
    <div class="shell footerInner"><span>ROBERTA — Verified On-Chain Intelligence</span><span>User → ROBERTA → Chain Scout → CMIS → verified provider/source</span></div>
  </footer>
</div>

<div id="modalBg" class="modalBg"><div class="modal"><div class="modalHead"><div><h3 id="modalTitle"></h3><p id="modalDesc"></p></div><button id="close" class="close">×</button></div><form id="serviceForm"><div id="formFields" class="form"></div><div class="modalActions"><button id="cancel" type="button" class="btn">Cancel</button><button type="submit" class="btn primary">Send to ROBERTA</button></div></form></div></div>
<script>
var services=[
{id:'scan',name:'Instant X1 Scan',icon:'⚡',cat:'Core',status:'Available',desc:'Accepted X1 scan covering identity, market, tokenomics, history, risk, evidence quality and field-scoped freshness.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Run an Instant X1 Scan for '+v.asset+'. Use X1 Scout and the accepted instant_x1_scan/v3 path. Keep proof separate from risk and show unavailable fields.'}},
{id:'overview',name:'Asset Overview',icon:'◈',cat:'Core',status:'Available',desc:'Verified current snapshot and asset context with explicit limitations.',fields:[['asset','Asset / mint','text','e.g. XNT']],prompt:function(v){return 'Give me the ROBERTA asset overview for '+v.asset+'. Route through the appropriate Scout and CMIS; do not estimate missing values.'}},
{id:'compare',name:'Compare Two Assets',icon:'⇄',cat:'Market',status:'Available',desc:'Current and overlapping-history comparison without recomputing accepted facts outside CMIS.',fields:[['asset1','First asset','text','e.g. XNT'],['asset2','Second asset','text','e.g. AGI']],prompt:function(v){return 'Compare '+v.asset1+' and '+v.asset2+' through ROBERTA. Use accepted CMIS comparison and history services. Keep unavailable or non-comparable metrics explicit.'}},
{id:'risk',name:'Risk Assessment',icon:'◇',cat:'Risk',status:'Available',desc:'Deterministic CMIS risk result with exact reasons and evidence limitations.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Run a deterministic ROBERTA risk assessment for '+v.asset+'. Preserve the exact CMIS risk result, reasons, proof status and missing evidence.'}},
{id:'solana-market',name:'Solana Market Report',icon:'S',cat:'Solana',chain:'Solana',status:'Configured',desc:'Accepted read-only Solana market report for an exact mint when the Solana provider path is enabled.',fields:[['asset','Exact Solana mint','text','Paste exact mint']],prompt:function(v){return 'Give me the verified Solana market report for exact mint '+v.asset+' through ROBERTA -> Solana Scout -> CMIS. Do not guess from a symbol and do not fall back to X1. If the accepted Solana provider path is disabled or unavailable, return that state explicitly.'}},
{id:'solana-tokenomics',name:'Solana Tokenomics',icon:'S',cat:'Solana',chain:'Solana',status:'Configured',desc:'Accepted read-only Solana tokenomics and authority facts for an exact mint, including Token-2022 identity where supported.',fields:[['asset','Exact Solana mint','text','Paste exact mint']],prompt:function(v){return 'Analyze verified Solana tokenomics and authorities for exact mint '+v.asset+' through ROBERTA -> Solana Scout -> CMIS. Preserve SPL Token vs Token-2022 identity and return unavailable fields explicitly. Do not infer by symbol.'}},
{id:'solana-risk',name:'Solana Risk Assessment',icon:'S',cat:'Solana',chain:'Solana',status:'Configured',desc:'Accepted deterministic read-only Solana risk assessment for an exact mint when configured.',fields:[['asset','Exact Solana mint','text','Paste exact mint']],prompt:function(v){return 'Run the accepted deterministic Solana risk assessment for exact mint '+v.asset+' through ROBERTA -> Solana Scout -> CMIS. Keep risk separate from evidence quality, do not infer by symbol, and do not fall back to X1.'}},
{id:'tokenomics',name:'Tokenomics & Authorities',icon:'◎',cat:'Asset',status:'Available',desc:'Supply, mint/freeze authority and other structural token facts where verified.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Analyze tokenomics and authorities for '+v.asset+' through ROBERTA and CMIS. Distinguish verified, provider-reported and unavailable fields.'}},
{id:'liquidity',name:'Liquidity Analysis',icon:'≈',cat:'Market',status:'Available',desc:'Liquidity structure and supported pool/route evidence with exact scope.',fields:[['asset','Asset / mint','text','e.g. XNT']],prompt:function(v){return 'Run ROBERTA liquidity analysis for '+v.asset+'. Show verified liquidity, pool structure, evidence scope, freshness and limitations.'}},
{id:'history',name:'Historical Analysis',icon:'◷',cat:'History',status:'Available',desc:'Verified windows and all-available observations with explicit gaps and lifetime limits.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Run ROBERTA historical analysis for '+v.asset+'. Use accepted CMIS history and all-available observations when useful. Do not imply continuous or lifetime coverage unless verified.'}},
{id:'activity',name:'Market Activity',icon:'⌁',cat:'Market',status:'Available',desc:'Bounded transaction and market-activity observations where accepted evidence supports them.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Show verified market activity for '+v.asset+' through ROBERTA. Preserve the exact scope and freshness of the activity evidence.'}},
{id:'concentration',name:'Concentration Change',icon:'◉',cat:'Intelligence',status:'Advanced',desc:'CMIS-owned concentration-change intelligence by evidence ID; concentration is not beneficial ownership.',fields:[['asset','Asset / mint','text','e.g. AGI'],['evidence','Intelligence evidence ID','text','ie_…']],prompt:function(v){return 'Run ROBERTA concentration change intelligence for '+v.asset+' using CMIS intelligence evidence id '+v.evidence+'. Do not infer beneficial ownership, intent, fraud, manipulation or risk from concentration alone.'}},
{id:'warning',name:'Concentration Warning',icon:'!',cat:'Intelligence',status:'Advanced',desc:'CMIS 1.18 pull-only WATCH/CLEAR warning. Push delivery remains unauthorized.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Check the current pull-only concentration warning intelligence for '+v.asset+' through ROBERTA using accepted CMIS 1.18 concentration_warning_intelligence/v1. If required CMIS-owned evidence ids or persistence inputs are unavailable, state exactly what is missing. Keep WATCH/CLEAR separate from risk.'}},
{id:'rank',name:'Rank X1 Assets',icon:'≋',cat:'Market',status:'Available',desc:'Rank X1 assets across the bounded XDEX universe by an accepted metric.',fields:[['metric','Metric','select','liquidity|volume|activity'],['limit','Result limit','number','10']],prompt:function(v){return 'Rank X1 assets by '+v.metric+' and return the top '+(v.limit||10)+' through ROBERTA. Preserve universe and scope limits and do not fabricate missing metrics.'}},
{id:'pretrade',name:'Pre-Trade Analysis',icon:'↗',cat:'Risk',status:'Available',desc:'Read-only requested-size analysis using verified liquidity and route facts where supported.',fields:[['asset','Asset / mint','text','e.g. AGI'],['side','Side','select','BUY|SELL'],['usd','USD amount','number','500']],prompt:function(v){return 'Run a ROBERTA pre-trade analysis for a '+v.side+' of '+v.asset+' with requested notional $'+v.usd+'. Use accepted CMIS pre_trade_check. Explain trade-size and liquidity constraints plus missing evidence. Analysis only; no execution.'}},
{id:'evidence',name:'Evidence Quality Report',icon:'✓',cat:'Evidence',status:'Available',desc:'Provenance, verification, freshness, conflicts, Proof Score and unresolved fields.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Give me an evidence quality report for '+v.asset+' through ROBERTA. Focus on provenance, verification, freshness, conflicts, Proof Score, scope and unresolved fields. Do not equate proof strength with safety.'}},
{id:'burn',name:'Burn Intelligence',icon:'△',cat:'Intelligence',status:'Available',desc:'Verified observed cumulative burn plus 1h / 24h / 7d / 30d windows and supported comparisons.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Run ROBERTA Burn Intelligence for '+v.asset+'. Show verified observed cumulative burn, 1h/24h/7d/30d windows, event counts and supported period-over-period changes. Distinguish observed coverage from complete lifetime burn.'}},
{id:'discovery',name:'Discovery Intelligence',icon:'⌖',cat:'Intelligence',status:'Available',desc:'First and latest verified observations, counts, coverage bounds and elapsed observed history.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Run ROBERTA Discovery Intelligence for '+v.asset+'. Show first and latest verified observations, observation count, coverage bounds and elapsed observed history. Do not relabel first observation as token launch or inception.'}},
{id:'changed',name:'What Changed?',icon:'Δ',cat:'History',status:'Available',desc:'Change summary from accepted current/history evidence without invented deltas or causal claims.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Tell me what changed for '+v.asset+' using ROBERTA\'s accepted What Changed workflow. Use verified current and historical evidence only and do not invent causes.'}},
{id:'full',name:'Full Assessment',icon:'▣',cat:'Core',status:'Available',desc:'Broad assessment combining relevant accepted market, risk, tokenomics, history and evidence services.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Run a full ROBERTA assessment for '+v.asset+'. Use relevant accepted Scout -> CMIS services, preserve unknowns and limitations, and give the answer first with evidence underneath.'}},
{id:'key',name:'Alert & Status Key',icon:'?',cat:'Evidence',status:'Available',desc:'Explains risk, CMIS status, verification, proof strength, freshness and execution labels.',fields:[],prompt:function(){return 'Show me ROBERTA\'s alert and status key, including risk, CMIS status, verification, proof strength, freshness, common warnings and execution meaning.'}},
{id:'chat',name:'Ask Anything',icon:'✦',cat:'Core',status:'Available',desc:'Normal question; ROBERTA selects the appropriate specialist and verified-data path.',fields:[['question','Question','text','e.g. Is AGI getting stronger?']],prompt:function(v){return v.question}}
];
var HUMAN_SERVICE_POLICY=' Present this in Human ROBERTA mode. Lead with the answer and the few facts that matter most. Round display values to useful human precision without changing the underlying facts. Group related freshness gaps into one LIVE MARKET FRESHNESS statement. Use WHAT ROBERTA STILL NEEDS for no more than three prioritized, decision-relevant missing items. Do not expose raw snake_case limitation codes, internal contract invariants, implementation diagnostics, or duplicate caveats in the normal answer. Do not repeat freshness warnings inside RISK after LIVE MARKET FRESHNESS. Hide an unavailable numeric risk score unless I explicitly ask about risk scoring or technical details. Use EVIDENCE QUALITY instead of a raw evidence-status dump and end with a plain-English BOTTOM LINE. Preserve every material unknown, conflict, WARN/BLOCK reason, and execution boundary; keep audit-level detail in the underlying structured evidence unless I explicitly ask for technical details.';
var cats=['All','Core','Market','Risk','Asset','History','Intelligence','Solana','Evidence'],activeCat='All',activeService=null,sending=false;
function el(s){return document.querySelector(s)}function base(){return(el('#apiBase').value||'').trim().replace(/\/$/,'')}function url(p){return base()?base()+p:p}function headers(){var h={'Content-Type':'application/json'},k=el('#apiKey').value.trim();if(k)h.Authorization='Bearer '+k;return h}
function renderFilters(){el('#filters').innerHTML=cats.map(function(c){return '<button class="filter '+(c===activeCat?'active':'')+'" data-cat="'+c+'">'+c+'</button>'}).join('')}
function render(){var q=el('#search').value.trim().toLowerCase(),list=services.filter(function(s){return(activeCat==='All'||s.cat===activeCat)&&(!q||(s.name+' '+s.desc+' '+s.cat).toLowerCase().indexOf(q)>=0)});el('#grid').innerHTML=list.map(function(s){return '<article class="svc"><div class="svcTop"><div class="ico">'+s.icon+'</div><span class="tag '+((s.status==='Advanced'||s.status==='Configured')?'configured':'')+'">'+s.status+'</span></div><h3>'+s.name+'</h3><p>'+s.desc+'</p><div class="svcFoot"><span>'+(s.chain||'X1')+' · Read-only</span><button class="run" data-svc="'+s.id+'">Run →</button></div></article>'}).join('')||'<div style="color:var(--muted)">No matching services.</div>'}
function field(f){var n=f[0],l=f[1],t=f[2],p=f[3];if(t==='select'){return '<div class="field"><label>'+l+'</label><select name="'+n+'" required>'+p.split('|').map(function(x){return '<option value="'+x+'">'+x+'</option>'}).join('')+'</select></div>'}return '<div class="field"><label>'+l+'</label><input name="'+n+'" type="'+t+'" placeholder="'+p+'" required '+(t==='number'?'min="0" step="any"':'')+'></div>'}
function openSvc(id){activeService=services.find(function(s){return s.id===id});if(!activeService)return;el('#modalTitle').textContent=activeService.name;el('#modalDesc').textContent=activeService.desc;el('#formFields').innerHTML=activeService.fields.length?activeService.fields.map(field).join(''):'<div style="color:var(--muted)">No additional input is required.</div>';el('#modalBg').classList.add('open')}
function closeSvc(){el('#modalBg').classList.remove('open');activeService=null}
function humanServicePrompt(text,id){return(id==='key'||id==='chat')?text:text+HUMAN_SERVICE_POLICY}
var CHAT_HISTORY_KEY='robertaChatHistoryV1',CHAT_HISTORY_LIMIT=80,currentChatId=null;
function escapeHtml(text){return String(text==null?'':text).replace(/[&<>"']/g,function(ch){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]})}
function statusClass(value){var v=String(value||'').toLowerCase().replace(/[^a-z]/g,'');if(['pass','verified','ok','clear','available','strong'].indexOf(v)>=0)return v;if(['warn','partial','watch','caution','moderate'].indexOf(v)>=0)return v;if(['block','error','unverified','unavailable','notverified','weak'].indexOf(v)>=0)return v;return''}
function formatAssistant(text){
  var lines=String(text||'').split('\n'),out=[];
  lines.forEach(function(line){
    var safe=escapeHtml(line);
    if(/^\s*[A-Z][A-Z0-9 &?\/—-]{2,}:?\s*$/.test(line.trim())){out.push('<span class="msgTitle">'+safe.replace(/:$/,'')+'</span>');return}
    safe=safe.replace(/\b(PASS|WARN|BLOCK|PARTIAL|VERIFIED|UNVERIFIED|UNAVAILABLE|NOT VERIFIED|WATCH|CLEAR|CAUTION|ERROR|AVAILABLE|STRONG|MODERATE|WEAK)\b/g,function(m){var cls=statusClass(m);return'<span class="statusToken '+cls+'">'+m+'</span>'});
    safe=safe.replace(/(^|[\s(])([+]\d[\d,]*(?:\.\d+)?%?)(?=$|[\s),.;])/g,'$1<span class="signedPositive">$2</span>');
    safe=safe.replace(/(^|[\s(])(-\d[\d,]*(?:\.\d+)?%?)(?=$|[\s),.;])/g,'$1<span class="signedNegative">$2</span>');
    out.push(safe)
  });
  return out.join('\n')
}
function msg(role,text){var d=document.createElement('div');d.className='msg '+role;if(role==='assistant')d.innerHTML=formatAssistant(text);else d.textContent=text;el('#messages').appendChild(d);el('#messages').scrollTop=el('#messages').scrollHeight;return d}
function starter(){return'I’m ready. Choose a capability above or ask a normal question about X1 market conditions, risk, tokenomics, history, burns, discovery, concentration, evidence, or pre-trade analysis.'}
function loadHistory(){try{var raw=localStorage.getItem(CHAT_HISTORY_KEY);var parsed=raw?JSON.parse(raw):[];return Array.isArray(parsed)?parsed:[]}catch(e){return[]}}
function saveHistory(items){try{localStorage.setItem(CHAT_HISTORY_KEY,JSON.stringify(items.slice(0,CHAT_HISTORY_LIMIT)))}catch(e){}}
function chatTitle(text){var t=String(text||'').replace(/\s+/g,' ').trim();return t.length>58?t.slice(0,55)+'…':t||'Untitled chat'}
function renderHistory(){var list=el('#historyList'),items=loadHistory();if(!items.length){list.innerHTML='<div class="historyEmpty">No saved chats yet.</div>';return}list.innerHTML=items.map(function(item){var when=item.createdAt?new Date(item.createdAt).toLocaleString():'';return'<button class="historyItem" data-chat-id="'+escapeHtml(item.id)+'"><span class="historyItemTitle">'+escapeHtml(item.title)+'</span><span class="historyItemTime">'+escapeHtml(when)+'</span></button>'}).join('')}
function renderChat(messages){el('#messages').innerHTML='';if(!Array.isArray(messages)||!messages.length){msg('assistant',starter());return}messages.forEach(function(item){if(item&&item.role&&typeof item.text==='string')msg(item.role,item.text)})}
function recordUserMessage(userText){var items=loadHistory(),item=currentChatId?items.find(function(x){return x.id===currentChatId}):null;if(!item){currentChatId='chat-'+Date.now()+'-'+Math.random().toString(36).slice(2,8);item={id:currentChatId,title:chatTitle(userText),createdAt:new Date().toISOString(),messages:[]};items.unshift(item)}item.messages.push({role:'user',text:userText});saveHistory(items);renderHistory();return currentChatId}
function appendSavedChat(id,role,text){var items=loadHistory(),item=items.find(function(x){return x.id===id});if(!item)return;item.messages.push({role:role,text:text});saveHistory(items);renderHistory()}
function openSavedChat(id){var item=loadHistory().find(function(x){return x.id===id});if(!item)return;currentChatId=id;renderChat(item.messages);el('#historyPanel').classList.remove('open')}
function restoreLatestChat(){var items=loadHistory();if(items.length){currentChatId=items[0].id;renderChat(items[0].messages)}else renderChat([])}
function clearCurrentChat(){currentChatId=null;renderChat([]);el('#composer').value=''}
function clearAllHistory(){saveHistory([]);currentChatId=null;renderHistory();renderChat([])}
function busy(v){sending=v;el('#send').disabled=v;el('#send').textContent=v?'Working…':'Send'}
async function health(){var h=el('#health');try{var r=await fetch(url('/healthz'));var d=await r.json();if(r.ok&&d.status==='ok'){h.className='pill online';h.innerHTML='<span class="dot"></span>ROBERTA online';return}throw 0}catch(e){h.className='pill offline';h.innerHTML='<span class="dot"></span>ROBERTA offline'}}
async function send(text){text=(text||'').trim();if(!text||sending)return;var chatId=recordUserMessage(text);msg('user',text);el('#composer').value='';busy(true);var wait=msg('system','ROBERTA is checking accepted evidence…');try{var r=await fetch(url('/v1/roberta'),{method:'POST',headers:headers(),body:JSON.stringify({message:text})}),d=await r.json().catch(function(){return{}});wait.remove();var reply=!r.ok?((d.error&&d.error.message)||('Request failed ('+r.status+')')):(d.reply||'ROBERTA returned no reply.');msg('assistant',reply);appendSavedChat(chatId,'assistant',reply)}catch(e){wait.remove();var reply='I could not reach the ROBERTA bridge. Verify that it is running and check Connection settings.';msg('assistant',reply);appendSavedChat(chatId,'assistant',reply)}finally{busy(false);health()}}
renderFilters();render();renderHistory();restoreLatestChat();health();setInterval(health,30000);
document.addEventListener('click',function(e){var s=e.target.closest('[data-svc]');if(s)openSvc(s.dataset.svc);var g=e.target.closest('[data-go]');if(g)document.getElementById(g.dataset.go).scrollIntoView({behavior:'smooth'});var c=e.target.closest('[data-cat]');if(c){activeCat=c.dataset.cat;renderFilters();render()}});
el('#search').addEventListener('input',render);el('#close').onclick=closeSvc;el('#cancel').onclick=closeSvc;el('#modalBg').addEventListener('click',function(e){if(e.target===el('#modalBg'))closeSvc()});
el('#serviceForm').addEventListener('submit',function(e){e.preventDefault();if(!activeService)return;var data=Object.fromEntries(new FormData(e.currentTarget).entries()),p=humanServicePrompt(activeService.prompt(data),activeService.id);closeSvc();document.getElementById('chat').scrollIntoView({behavior:'smooth'});send(p)});
el('#send').onclick=function(){send(el('#composer').value)};el('#composer').addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(el('#composer').value)}});
el('#historyBtn').onclick=function(){el('#historyPanel').classList.toggle('open');renderHistory()};el('#clearChat').onclick=clearCurrentChat;el('#clearHistory').onclick=clearAllHistory;el('#historyList').addEventListener('click',function(e){var item=e.target.closest('[data-chat-id]');if(item)openSavedChat(item.dataset.chatId)});
el('#settingsBtn').onclick=function(){el('#settings').classList.toggle('open')};el('#apiBase').value=sessionStorage.getItem('robertaApiBase')||'';el('#apiKey').value=sessionStorage.getItem('robertaApiKey')||'';el('#apiBase').onchange=function(){sessionStorage.setItem('robertaApiBase',this.value.trim());health()};el('#apiKey').onchange=function(){sessionStorage.setItem('robertaApiKey',this.value);health()};
</script>

<script>
(function(){
  'use strict';
  var canvas=document.getElementById('robertaHeroCanvas');
  if(!canvas)return;
  var ctx=canvas.getContext('2d',{alpha:true,desynchronized:true});
  if(!ctx)return;

  var motionQuery=window.matchMedia?window.matchMedia('(prefers-reduced-motion: reduce)'):null;
  var reduceMotion=!!(motionQuery&&motionQuery.matches);
  var dpr=Math.min(window.devicePixelRatio||1,2);
  var w=0,h=0,raf=0,visible=!document.hidden;
  var headDots=[],windRibbons=[],windMotes=[],stars=[];
  var pointer={x:0,y:0,active:false};

  function rand(a,b){return a+Math.random()*(b-a)}
  function clamp(v,a,b){return Math.max(a,Math.min(b,v))}
  function lerp(a,b,t){return a+(b-a)*t}

  function headPath(){
    var p=new Path2D();
    p.moveTo(w*.43,h*.15);
    p.bezierCurveTo(w*.52,h*.11,w*.59,h*.17,w*.605,h*.26);
    p.bezierCurveTo(w*.62,h*.32,w*.615,h*.36,w*.63,h*.40);
    p.bezierCurveTo(w*.647,h*.425,w*.67,h*.438,w*.645,h*.455);
    p.bezierCurveTo(w*.626,h*.466,w*.628,h*.48,w*.646,h*.492);
    p.bezierCurveTo(w*.657,h*.502,w*.647,h*.517,w*.628,h*.522);
    p.bezierCurveTo(w*.641,h*.538,w*.634,h*.555,w*.616,h*.565);
    p.bezierCurveTo(w*.598,h*.576,w*.599,h*.608,w*.58,h*.635);
    p.bezierCurveTo(w*.558,h*.667,w*.535,h*.672,w*.525,h*.70);
    p.bezierCurveTo(w*.515,h*.73,w*.53,h*.79,w*.56,h*.86);
    p.bezierCurveTo(w*.50,h*.87,w*.42,h*.85,w*.36,h*.79);
    p.bezierCurveTo(w*.315,h*.745,w*.295,h*.68,w*.292,h*.60);
    p.bezierCurveTo(w*.287,h*.48,w*.295,h*.35,w*.335,h*.245);
    p.bezierCurveTo(w*.36,h*.19,w*.392,h*.158,w*.43,h*.15);
    p.closePath();
    return p;
  }

  function insideHead(x,y){
    var path=headPath();
    return ctx.isPointInPath(path,x,y);
  }

  // Used by tests and by the wind field to anchor ribbons to the back contour.
  function profilePoint(t){
    t=clamp(t,0,1);
    var x=w*(.315+.025*Math.sin(t*Math.PI));
    var y=h*(.24+t*.49);
    return{x:x,y:y};
  }

  function build(){
    headDots=[];windRibbons=[];windMotes=[];stars=[];
    var area=w*h;
    var target=clamp(Math.floor(area/3200),125,260);
    var tries=0;
    while(headDots.length<target&&tries<target*20){
      tries++;
      var x=rand(w*.29,w*.665),y=rand(h*.13,h*.84);
      if(insideHead(x,y)){
        headDots.push({
          ox:x,oy:y,x:x,y:y,
          r:rand(.45,1.35),
          phase:rand(0,Math.PI*2),
          speed:rand(.28,.78)
        });
      }
    }

    // Seven broad stream bands: deliberately sparse so they read as wind, never hair.
    var ys=[.25,.32,.40,.49,.58,.66,.73];
    for(var i=0;i<ys.length;i++){
      var anchor=profilePoint((ys[i]-.24)/.49);
      windRibbons.push({
        sx:anchor.x+w*.025,
        sy:h*ys[i],
        c1x:w*rand(.245,.285),
        c1y:h*(ys[i]+rand(-.06,.06)),
        c2x:w*rand(.12,.19),
        c2y:h*(ys[i]+rand(-.11,.11)),
        ex:w*rand(-.10,.035),
        ey:h*(ys[i]+rand(-.15,.15)),
        phase:rand(0,Math.PI*2),
        amp:h*rand(.012,.033),
        width:rand(2.4,5.8),
        alpha:rand(.30,.58),
        speed:rand(.24,.48)
      });
    }

    for(var m=0;m<56;m++){
      var band=m%windRibbons.length;
      windMotes.push({
        band:band,
        u:Math.random(),
        speed:rand(.035,.085),
        phase:rand(0,Math.PI*2),
        size:rand(.7,1.9)
      });
    }

    for(var s=0;s<clamp(Math.floor(area/15000),38,90);s++){
      stars.push({x:rand(0,w),y:rand(0,h),r:rand(.3,1),phase:rand(0,Math.PI*2)});
    }
  }

  function resize(){
    var r=canvas.getBoundingClientRect();
    w=Math.max(1,r.width);h=Math.max(1,r.height);
    dpr=Math.min(window.devicePixelRatio||1,2);
    canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    build();
    draw(performance.now(),true);
  }

  function cubicPoint(q,u,wave){
    var mt=1-u;
    var p0x=q.sx,p0y=q.sy;
    var p1x=q.c1x,p1y=q.c1y+wave;
    var p2x=q.c2x,p2y=q.c2y-wave*.62;
    var p3x=q.ex,p3y=q.ey+wave*.25;
    return{
      x:mt*mt*mt*p0x+3*mt*mt*u*p1x+3*mt*u*u*p2x+u*u*u*p3x,
      y:mt*mt*mt*p0y+3*mt*mt*u*p1y+3*mt*u*u*p2y+u*u*u*p3y
    };
  }

  function drawWind(t){
    ctx.save();
    ctx.globalCompositeOperation='lighter';

    // Faint wrap arcs ride over the rear crown before peeling backward.
    for(var a=0;a<3;a++){
      var y=h*(.29+a*.13);
      var shift=Math.sin(t*.38+a*1.7)*h*.012;
      var wrap=ctx.createLinearGradient(w*.27,0,w*.53,0);
      wrap.addColorStop(0,'rgba(76,107,255,0)');
      wrap.addColorStop(.42,'rgba(76,151,255,.17)');
      wrap.addColorStop(.78,'rgba(105,213,255,.52)');
      wrap.addColorStop(1,'rgba(167,102,255,.12)');
      ctx.beginPath();
      ctx.moveTo(w*.285,y+shift);
      ctx.bezierCurveTo(w*.35,y-h*.11+shift,w*.48,y-h*.10+shift,w*.545,y-h*.025+shift);
      ctx.strokeStyle=wrap;
      ctx.lineWidth=1.2+a*.35;
      ctx.stroke();
    }

    for(var i=0;i<windRibbons.length;i++){
      var q=windRibbons[i];
      var wave=Math.sin(t*q.speed+q.phase)*q.amp;
      var grad=ctx.createLinearGradient(q.ex,0,q.sx,0);
      grad.addColorStop(0,'rgba(50,92,255,0)');
      grad.addColorStop(.18,'rgba(66,114,255,'+(q.alpha*.12)+')');
      grad.addColorStop(.52,'rgba(73,150,255,'+(q.alpha*.46)+')');
      grad.addColorStop(.82,'rgba(89,211,255,'+(q.alpha*.90)+')');
      grad.addColorStop(1,'rgba(170,98,255,'+(q.alpha*.34)+')');

      ctx.beginPath();
      ctx.moveTo(q.sx,q.sy);
      ctx.bezierCurveTo(q.c1x,q.c1y+wave,q.c2x,q.c2y-wave*.62,q.ex,q.ey+wave*.25);
      ctx.strokeStyle=grad;
      ctx.lineWidth=q.width*2.9;
      ctx.globalAlpha=.10;
      ctx.stroke();

      ctx.globalAlpha=1;
      ctx.beginPath();
      ctx.moveTo(q.sx,q.sy);
      ctx.bezierCurveTo(q.c1x,q.c1y+wave,q.c2x,q.c2y-wave*.62,q.ex,q.ey+wave*.25);
      ctx.strokeStyle=grad;
      ctx.lineWidth=q.width;
      ctx.stroke();

      // A single luminous core keeps each ribbon fluid and airy.
      ctx.beginPath();
      ctx.moveTo(q.sx,q.sy);
      ctx.bezierCurveTo(q.c1x,q.c1y+wave*.7,q.c2x,q.c2y-wave*.45,q.ex,q.ey+wave*.18);
      ctx.strokeStyle='rgba(131,220,255,'+(q.alpha*.48)+')';
      ctx.lineWidth=.65;
      ctx.stroke();
    }

    for(var m=0;m<windMotes.length;m++){
      var mote=windMotes[m],r=windRibbons[mote.band];
      var u=(mote.u+t*mote.speed)%1;
      // Travel from the head toward the back; fade completely before the far end.
      var p=cubicPoint(r,u,Math.sin(t*r.speed+r.phase)*r.amp);
      var fade=Math.sin(Math.PI*u);
      var alpha=.75*fade*(1-u*.55);
      ctx.beginPath();
      ctx.arc(p.x,p.y,mote.size*(.7+fade*.55),0,Math.PI*2);
      ctx.fillStyle='rgba(110,213,255,'+alpha+')';
      ctx.fill();
    }
    ctx.restore();
  }

  function drawHead(t){
    var path=headPath();

    ctx.save();
    ctx.shadowBlur=30;
    ctx.shadowColor='rgba(63,145,255,.42)';
    var fill=ctx.createRadialGradient(w*.51,h*.43,10,w*.48,h*.48,w*.31);
    fill.addColorStop(0,'rgba(24,68,168,.26)');
    fill.addColorStop(.52,'rgba(12,36,94,.18)');
    fill.addColorStop(1,'rgba(5,9,25,.22)');
    ctx.fillStyle=fill;
    ctx.fill(path);
    ctx.restore();

    // Fine internal network/points, but no strands attached to the scalp.
    ctx.save();
    ctx.globalCompositeOperation='lighter';
    ctx.clip(path);
    for(var i=0;i<headDots.length;i++){
      var p=headDots[i];
      var pulse=.62+.38*Math.sin(t*p.speed+p.phase);
      var dx=0,dy=0;
      if(pointer.active&&!reduceMotion){
        var vx=p.ox-pointer.x,vy=p.oy-pointer.y,d=Math.sqrt(vx*vx+vy*vy);
        if(d<95&&d>1){var push=(95-d)/95*2.4;dx=vx/d*push;dy=vy/d*push}
      }
      p.x=p.ox+dx+Math.sin(t*.20+p.phase)*.35;
      p.y=p.oy+dy+Math.cos(t*.18+p.phase)*.35;
      ctx.beginPath();
      ctx.arc(p.x,p.y,p.r*(.8+pulse*.35),0,Math.PI*2);
      ctx.fillStyle='rgba(111,196,255,'+(.28+.58*pulse)+')';
      ctx.fill();
    }
    for(var j=0;j<36;j++){
      var p1=headDots[(j*7)%headDots.length],p2=headDots[(j*13+9)%headDots.length];
      var dx2=p1.x-p2.x,dy2=p1.y-p2.y;
      if(dx2*dx2+dy2*dy2<5200){
        ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);
        ctx.strokeStyle='rgba(77,145,255,.075)';ctx.lineWidth=.5;ctx.stroke();
      }
    }
    ctx.restore();

    // Clean luminous silhouette.
    ctx.save();
    ctx.shadowBlur=18;
    ctx.shadowColor='rgba(74,164,255,.88)';
    var edge=ctx.createLinearGradient(w*.31,0,w*.66,0);
    edge.addColorStop(0,'rgba(60,102,255,.18)');
    edge.addColorStop(.58,'rgba(82,171,255,.72)');
    edge.addColorStop(1,'rgba(218,242,255,.98)');
    ctx.strokeStyle=edge;
    ctx.lineWidth=1.5;
    ctx.stroke(path);
    ctx.restore();

    // Facial contour accents.
    ctx.save();
    ctx.globalCompositeOperation='lighter';
    ctx.strokeStyle='rgba(175,229,255,.56)';
    ctx.lineWidth=.75;
    ctx.beginPath();
    ctx.moveTo(w*.586,h*.315);
    ctx.bezierCurveTo(w*.608,h*.34,w*.607,h*.376,w*.625,h*.402);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(w*.607,h*.49);
    ctx.bezierCurveTo(w*.625,h*.492,w*.631,h*.502,w*.616,h*.51);
    ctx.stroke();
    ctx.restore();
  }

  function drawOrbit(t){
    ctx.save();ctx.globalCompositeOperation='lighter';
    var cx=w*.84,cy=h*.47,maxR=Math.min(w,h)*.235;
    for(var r=1;r<=3;r++){
      ctx.beginPath();ctx.arc(cx,cy,maxR*(.40+r*.22),0,Math.PI*2);
      ctx.strokeStyle='rgba(104,117,255,'+(r===2?.15:.08)+')';
      ctx.lineWidth=.7;ctx.stroke();
    }
    for(var n=0;n<14;n++){
      var ang=n/14*Math.PI*2+t*.028*(n%2?1:-1),rr=maxR*(.53+(n%3)*.15);
      var nx=cx+Math.cos(ang)*rr,ny=cy+Math.sin(ang)*rr;
      ctx.beginPath();ctx.arc(nx,ny,n%4===0?2:1,0,Math.PI*2);
      ctx.fillStyle=n%4===0?'rgba(183,77,255,.88)':'rgba(72,201,255,.72)';
      ctx.fill();
    }
    ctx.restore();
  }

  function draw(ts,force){
    if(!force&&!visible)return;
    var t=ts*.001;
    ctx.clearRect(0,0,w,h);

    var bg=ctx.createRadialGradient(w*.47,h*.47,10,w*.47,h*.47,w*.42);
    bg.addColorStop(0,'rgba(29,69,178,.11)');
    bg.addColorStop(.55,'rgba(28,31,104,.04)');
    bg.addColorStop(1,'rgba(5,8,23,0)');
    ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);

    for(var s=0;s<stars.length;s++){
      var st=stars[s],sa=.07+.16*(.5+.5*Math.sin(t*.55+st.phase));
      ctx.beginPath();ctx.arc(st.x,st.y,st.r,0,Math.PI*2);
      ctx.fillStyle='rgba(111,176,255,'+sa+')';ctx.fill();
    }

    // Back wind first, then head, so the ribbons appear to peel naturally from behind it.
    drawWind(t);
    drawHead(t);
    drawOrbit(t);

    if(!reduceMotion&&visible)raf=requestAnimationFrame(draw);
  }

  function start(){
    if(reduceMotion){draw(performance.now(),true);return}
    cancelAnimationFrame(raf);
    raf=requestAnimationFrame(draw);
  }

  document.addEventListener('visibilitychange',function(){
    visible=!document.hidden;
    if(visible)start();else cancelAnimationFrame(raf);
  });
  canvas.addEventListener('pointermove',function(e){
    var r=canvas.getBoundingClientRect();
    pointer.x=e.clientX-r.left;pointer.y=e.clientY-r.top;pointer.active=true;
  });
  canvas.addEventListener('pointerleave',function(){pointer.active=false});
  if('ResizeObserver'in window)new ResizeObserver(resize).observe(canvas.parentElement);
  else window.addEventListener('resize',resize);
  if(motionQuery&&motionQuery.addEventListener){
    motionQuery.addEventListener('change',function(e){
      reduceMotion=e.matches;
      if(reduceMotion){cancelAnimationFrame(raf);draw(performance.now(),true)}else start();
    });
  }

  resize();
  start();
})();
</script>

</body></html>'''


def web_ui_bytes() -> bytes:
    return ROBERTA_WEB_UI_HTML.encode("utf-8")


__all__ = ["ROBERTA_WEB_UI_HTML", "web_ui_bytes"]
