"""Local web interface for ROBERTA — Verified On-Chain Intelligence."""

from __future__ import annotations

ROBERTA_WEB_UI_HTML = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
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
.chatLayout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:18px}.chat,.info{border:1px solid var(--line);background:#fff;border-radius:30px;overflow:hidden;box-shadow:0 18px 50px rgba(41,44,84,.07)}.chatHead{padding:18px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px}.chatHeadActions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.chatTitle{font-size:17px;font-weight:950;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:4px}.messages{height:650px;min-height:650px;overflow:auto;padding:24px;display:flex;flex-direction:column;gap:14px;background:linear-gradient(180deg,#fcfcff,#f8f9ff)}.msg{max-width:90%;padding:14px 16px;border-radius:18px;white-space:pre-wrap;word-break:break-word}.msg.user{align-self:flex-end;background:var(--ink);color:#fff;border-bottom-right-radius:6px}.msg.assistant{align-self:flex-start;background:#fff;border:1px solid var(--line);color:var(--ink2);border-bottom-left-radius:6px}.msg.system{align-self:center;color:var(--muted);font-size:11px;padding:3px}.msgTitle{display:block;font-weight:950;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px;margin:2px 0 5px;color:var(--ink)}.statusToken{display:inline-flex;align-items:center;padding:1px 7px;border-radius:999px;border:1px solid var(--grayLine);background:var(--grayBg);color:var(--grayText);font-weight:900;font-size:.9em}.statusToken.pass,.statusToken.verified,.statusToken.ok,.statusToken.clear,.statusToken.available,.statusToken.strong{background:var(--greenBg);border-color:var(--greenLine);color:var(--greenText)}.statusToken.warn,.statusToken.partial,.statusToken.watch,.statusToken.caution,.statusToken.moderate{background:var(--amberBg);border-color:var(--amberLine);color:var(--amberText)}.statusToken.block,.statusToken.error,.statusToken.unverified,.statusToken.unavailable,.statusToken.notverified,.statusToken.weak{background:var(--redBg);border-color:var(--redLine);color:var(--redText)}.signedPositive{color:var(--greenText);font-weight:900}.signedNegative{color:var(--redText);font-weight:900}.opinionLine{display:block;margin:2px 0 5px;font-weight:850;color:var(--ink)}.opinionLine strong{color:#75cfff}.composer{border-top:1px solid var(--line);padding:16px;display:grid;grid-template-columns:1fr auto;gap:10px}.composer textarea{resize:vertical;min-height:100px;max-height:260px;border:1px solid var(--line);background:#f8f9fd;color:var(--ink);border-radius:18px;padding:14px 15px;outline:none}.info{padding:22px}.info h3{font-size:18px;margin:0 0 12px}.infoBlock{border-top:1px solid var(--line);padding:15px 0}.infoBlock:first-of-type{border-top:0}.infoBlock b{display:block;color:var(--ink);font-size:10px;text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px}.infoBlock span{color:var(--muted);font-size:12px}.historyPanel{border-bottom:1px solid var(--line);background:#fbfbfe;padding:12px 14px;display:none}.historyPanel.open{display:block}.historyTop{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}.historyTop b{font-size:12px}.historyList{display:grid;gap:7px;max-height:220px;overflow:auto}.historyItem{border:1px solid var(--line);background:#fff;border-radius:14px;padding:9px 11px;cursor:pointer;text-align:left}.historyItem:hover{border-color:#cbc7ff;background:#f9f8ff}.historyItemTitle{display:block;font-weight:900;text-decoration:underline;text-underline-offset:2px;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.historyItemTime{display:block;color:var(--muted);font-size:9px;margin-top:2px}.historyEmpty{color:var(--muted);font-size:11px;padding:8px}.btn.small{padding:7px 10px;font-size:10px}
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
<style id="human-workspace-ui">
body:not(.workspaceMode) #chat{display:none}
.workspaceMode .siteNav,.workspaceMode #home,.workspaceMode #trust,.workspaceMode #services,.workspaceMode .footer{display:none!important}
.workspaceMode .page{min-height:100vh;overflow:visible}
.humanServiceGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}
.humanSvc{border:1px solid rgba(126,150,255,.2);background:linear-gradient(180deg,rgba(12,18,43,.92),rgba(8,12,29,.94));border-radius:28px;padding:24px;min-height:360px;box-shadow:0 18px 45px rgba(0,0,0,.18);display:flex;flex-direction:column}
.humanSvc.featured{border-color:rgba(88,194,255,.42);box-shadow:0 20px 55px rgba(59,86,255,.14)}
.humanSvcIcon{width:48px;height:48px;border-radius:15px;display:grid;place-items:center;background:linear-gradient(145deg,rgba(71,136,255,.24),rgba(144,66,255,.22));border:1px solid rgba(115,154,255,.22);font-size:18px}
.humanSvc h3{font-size:20px;margin:18px 0 8px}.humanSvc p{color:var(--muted);font-size:13px;margin:0 0 20px}
.exampleLabel{margin-top:auto;color:#7883ae;font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px}
.exampleChip{display:block;width:100%;text-align:left;border:1px solid rgba(126,150,255,.16);background:rgba(10,15,37,.7);color:#cbd4f7;border-radius:13px;padding:9px 11px;margin-top:7px;cursor:pointer;font-size:11px}
.exampleChip:hover{border-color:rgba(78,191,255,.42);background:rgba(20,30,67,.86);color:#fff}
.workspaceSection{padding:0;min-height:100vh;background:#050817}
.workspaceShell{min-height:100vh;display:grid;grid-template-columns:310px minmax(0,1fr)}
.workspaceSidebar{position:sticky;top:0;height:100vh;overflow:auto;border-right:1px solid rgba(126,150,255,.14);background:rgba(6,10,26,.97);padding:22px 18px;display:flex;flex-direction:column;gap:10px}
.workspaceBrand{display:flex;align-items:center;gap:11px;padding:3px 2px 16px}.workspaceBrandMark{width:38px;height:38px;border-radius:10px;display:grid;place-items:center;background:linear-gradient(145deg,#5aa8ff,#8e4dff);font-weight:900}.workspaceBrand b{display:block;letter-spacing:.18em}.workspaceBrand small{display:block;color:var(--muted);font-size:9px;margin-top:2px}
.workspaceWide{width:100%;margin-bottom:6px}.workspaceGroupTitle{color:#7480aa;font-size:9px;font-weight:950;text-transform:uppercase;letter-spacing:.14em;margin:10px 2px 3px}.serviceTitle{margin-top:18px}
.workspaceHistory{max-height:28vh;overflow:auto;display:grid;gap:6px}.workspaceHistory .historyItem{background:rgba(12,17,39,.74);border-color:rgba(126,150,255,.13);color:var(--ink)}.workspaceHistory .historyItemTitle{text-decoration:none}.historyGroupTitle{color:#6e7aa7;font-size:9px;font-weight:900;text-transform:uppercase;letter-spacing:.12em;padding:7px 3px 2px}
.sidebarTextButton{border:0;background:transparent;color:#8e99c1;text-align:left;padding:5px 2px;cursor:pointer;font-size:10px}.sidebarTextButton:hover{color:#fff}
.workspaceServices{display:grid;gap:7px}.workspaceServices button{border:1px solid rgba(126,150,255,.13);background:rgba(10,15,35,.7);color:var(--ink);border-radius:14px;padding:10px 11px;text-align:left;cursor:pointer}.workspaceServices button:hover{border-color:rgba(78,191,255,.38);background:rgba(18,27,60,.82)}.workspaceServices b{display:block;font-size:11px}.workspaceServices span{display:block;color:#7f8bb5;font-size:9px;margin-top:2px}
.workspaceLabelKey{margin-top:10px}.workspaceLabelKey>span{display:inline-flex;border:1px solid rgba(126,150,255,.15);border-radius:999px;color:#909bc3;padding:4px 7px;margin:4px 3px 0 0;font-size:8px}.backHome{margin-top:auto;padding-top:14px}
.workspaceMain{min-width:0;height:100vh;display:flex;flex-direction:column;background:radial-gradient(circle at 70% 0,rgba(73,74,190,.11),transparent 30%),#060918}
.workspaceTopbar{min-height:76px;border-bottom:1px solid rgba(126,150,255,.14);display:flex;justify-content:space-between;align-items:center;gap:16px;padding:14px 22px;background:rgba(6,9,24,.84);backdrop-filter:blur(18px)}
.workspaceTopTitle b{display:block;font-size:16px;letter-spacing:.12em}.workspaceTopTitle span{display:block;color:var(--muted);font-size:10px;margin-top:2px}.workspaceTopActions{display:flex;align-items:center;gap:7px;flex-wrap:wrap;justify-content:flex-end}
.workspaceRouteLabel{display:inline-flex;border:1px solid rgba(126,150,255,.15);border-radius:999px;padding:6px 9px;color:#9da8cf;font-size:9px;white-space:nowrap}
.workspaceChat{min-height:0;flex:1;display:flex;flex-direction:column;max-width:1100px;width:100%;margin:0 auto;padding:20px 26px 14px}
.workspaceChat .messages{height:auto;min-height:0;flex:1;border:1px solid rgba(126,150,255,.12);border-bottom:0;border-radius:24px 24px 0 0;background:linear-gradient(180deg,rgba(8,12,30,.74),rgba(6,9,23,.9));padding:24px}
.workspaceChat .composer{border:1px solid rgba(126,150,255,.12);border-top:1px solid rgba(126,150,255,.16);background:rgba(8,12,30,.92);border-radius:0 0 24px 24px;padding:14px}
.workspaceChat .composer textarea{min-height:76px;max-height:180px;background:rgba(4,7,19,.86);border-color:rgba(126,150,255,.18)}
.workspaceBoundary{text-align:center;color:#66729b;font-size:9px;padding-top:8px}
.workspaceMode .settings{top:18px}
@media(max-width:1050px){.humanServiceGrid{grid-template-columns:repeat(2,minmax(0,1fr))}.workspaceShell{grid-template-columns:260px minmax(0,1fr)}.workspaceRouteLabel{display:none}}
@media(max-width:760px){.humanServiceGrid{grid-template-columns:1fr}.workspaceShell{display:block}.workspaceSidebar{position:relative;width:100%;height:auto;max-height:none;border-right:0;border-bottom:1px solid rgba(126,150,255,.14)}.workspaceHistory{max-height:180px}.workspaceServices{grid-template-columns:repeat(2,minmax(0,1fr))}.workspaceMain{height:auto;min-height:100vh}.workspaceTopbar{align-items:flex-start;flex-direction:column}.workspaceTopActions{justify-content:flex-start}.workspaceChat{min-height:75vh;padding:12px}.workspaceChat .messages{min-height:55vh}.backHome{margin-top:12px}}
@media(max-width:520px){.workspaceServices{grid-template-columns:1fr}.workspaceTopActions .pill{display:inline-flex}}
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
        <button data-go="services">Services</button>
        <button data-go="trust">Why ROBERTA</button>
      </nav>
      <div class="navActions">
        <button class="btn primary" id="connectNav">Open ROBERTA</button>
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
          <p class="heroTagline">Your on-chain research assistant for tokens, trades, wallets, market moves, and risk.</p>
          <p class="heroLead">Ask ROBERTA a normal question. She checks the available blockchain evidence, explains what matters in plain English, and gives you a clear assessment without executing a trade for you.</p>
          <div class="heroBtns">
            <button class="btn primary" id="connectHuman">Enter Human Chat</button>
            <button class="btn soft" id="connectAgent">Agent / API Access</button>
          </div>
          <div class="heroSignals" aria-label="ROBERTA operating principles">
            <span><b>Ask naturally</b> no commands required</span>
            <span><b>Evidence-aware</b> unknowns stay visible</span>
            <span><b>Read-only</b> you remain in control</span>
          </div>
        </div>

        <div class="heroVisual" aria-label="Animated ROBERTA intelligence field">
          <canvas id="robertaHeroCanvas" role="img" aria-label="Animated particle profile with flowing evidence paths"></canvas>
          <div class="heroCoreMark" aria-hidden="true">R</div>
          <div class="heroOrbitLabel orbitMarket"><span class="orbitIcon">▥</span><b>MARKET</b><small>INTELLIGENCE</small></div>
          <div class="heroOrbitLabel orbitRisk"><span class="orbitIcon">◇</span><b>RISK</b><small>ANALYSIS</small></div>
          <div class="heroOrbitLabel orbitBridge"><span class="orbitIcon">↔</span><b>WALLETS</b><small>& TRADES</small></div>
          <div class="heroOrbitLabel orbitProof"><span class="orbitIcon">✓</span><b>VERIFIED</b><small>EVIDENCE</small></div>
          <div class="heroOrbitLabel orbitFresh"><span class="orbitIcon">◷</span><b>FRESHNESS</b><small>BY FIELD</small></div>
          <div class="heroOrbitLabel orbitBurn"><span class="orbitIcon">△</span><b>BURNS</b><small>& HISTORY</small></div>
          <div class="motionStatus"><span></span>ROBERTA INTELLIGENCE NETWORK</div>
        </div>
      </div>
    </section>

    <section id="trust" class="section alt">
      <div class="shell">
        <div class="sectionHead">
          <div><div class="eyebrow">Why ROBERTA</div><h2>Clear answers without hiding what the evidence cannot prove.</h2></div>
          <p>ROBERTA is designed for people who want the useful conclusion first, with the evidence and important limitations underneath.</p>
        </div>
        <div class="trustStrip">
          <article class="trustCard"><div class="trustIcon">✓</div><h3>Checks the evidence</h3><p>ROBERTA uses accepted on-chain intelligence and keeps missing, stale, or conflicting information visible instead of filling the gaps with guesses.</p></article>
          <article class="trustCard"><div class="trustIcon">◎</div><h3>Gives you a clear view</h3><p>For decision questions, ROBERTA can tell you what she thinks, explain why, show the strongest evidence against her view, and say what would change her mind.</p></article>
          <article class="trustCard"><div class="trustIcon">↗</div><h3>You stay in control</h3><p>ROBERTA analyzes and recommends. She does not sign transactions, move funds, or execute trades from this website.</p></article>
        </div>
      </div>
    </section>

    <section id="services" class="section">
      <div class="shell">
        <div class="sectionHead">
          <div><div class="eyebrow">What you can ask</div><h2>Seven simple ways to use ROBERTA.</h2></div>
          <p>You never have to choose a technical blockchain tool. Pick a service for ideas, or just ask ROBERTA normally and she will select the right intelligence path.</p>
        </div>
        <div class="humanServiceGrid">
          <article class="humanSvc">
            <div class="humanSvcIcon">◈</div>
            <h3>Check a Token</h3>
            <p>Get a quick health check covering the market, liquidity, activity, token details, recent changes, and available evidence.</p>
            <div class="exampleLabel">Try asking</div>
            <button class="exampleChip" data-example="Check AGI.">“Check AGI.”</button>
            <button class="exampleChip" data-example="How is XNT doing right now?">“How is XNT doing?”</button>
            <button class="exampleChip" data-example="What should I know about this token?">“What should I know about this token?”</button>
          </article>
          <article class="humanSvc">
            <div class="humanSvcIcon">⇄</div>
            <h3>Compare Tokens</h3>
            <p>Compare two tokens side by side on liquidity, risk, market activity, history, structure, and other verified differences.</p>
            <div class="exampleLabel">Try asking</div>
            <button class="exampleChip" data-example="Which looks better right now, XNT or AGI?">“Which looks better, XNT or AGI?”</button>
            <button class="exampleChip" data-example="Which token has stronger liquidity, XNT or AGI?">“Which has stronger liquidity?”</button>
            <button class="exampleChip" data-example="Which is safer right now, XNT or AGI?">“Which is safer right now?”</button>
          </article>
          <article class="humanSvc">
            <div class="humanSvcIcon">↗</div>
            <h3>Should I Buy or Sell?</h3>
            <p>Tell ROBERTA the trade you are considering. She checks the evidence and explains whether she thinks you should proceed, wait, reduce the size, or avoid it.</p>
            <div class="exampleLabel">Try asking</div>
            <button class="exampleChip" data-example="Should I buy $500 of AGI right now?">“Should I buy $500 of AGI?”</button>
            <button class="exampleChip" data-example="Should I sell 100,000 XNT right now?">“Should I sell 100,000 XNT?”</button>
            <button class="exampleChip" data-example="Would you make this trade?">“Would you make this trade?”</button>
          </article>
          <article class="humanSvc">
            <div class="humanSvcIcon">◇</div>
            <h3>Check Risk</h3>
            <p>Look for thin liquidity, concentration, token controls, unusual activity, stale data, missing evidence, and trade-size problems.</p>
            <div class="exampleLabel">Try asking</div>
            <button class="exampleChip" data-example="Is AGI risky right now?">“Is this token risky?”</button>
            <button class="exampleChip" data-example="Could I get stuck trying to sell AGI?">“Could I get stuck selling?”</button>
            <button class="exampleChip" data-example="What worries you about AGI?">“What worries you about AGI?”</button>
          </article>
          <article class="humanSvc">
            <div class="humanSvcIcon">◎</div>
            <h3>Track Wallets &amp; Big Trades</h3>
            <p>Understand verified public-wallet activity, important buys and sells, transaction timing, volume contribution, and pool-level price impact when the evidence supports it.</p>
            <div class="exampleLabel">Try asking</div>
            <button class="exampleChip" data-example="Did a big wallet just buy AGI?">“Did a big wallet just buy AGI?”</button>
            <button class="exampleChip" data-example="Did this transaction move the pool price?">“Did this trade move the pool price?”</button>
            <button class="exampleChip" data-example="Where did these tokens go?">“Where did these tokens go?”</button>
          </article>
          <article class="humanSvc featured">
            <div class="humanSvcIcon">✦</div>
            <h3>Ask ROBERTA</h3>
            <p>Ask your question normally. ROBERTA chooses the appropriate token, market, wallet, burn, history, bridge, risk, or evidence intelligence automatically.</p>
            <div class="exampleLabel">Try asking</div>
            <button class="exampleChip" data-example="What happened to AGI today?">“What happened to AGI today?”</button>
            <button class="exampleChip" data-example="Why did the price jump?">“Why did the price jump?”</button>
            <button class="exampleChip" data-example="How much XNT was burned this week?">“How much XNT was burned this week?”</button>
          </article>
        </div>
      </div>
    </section>

    

    <section id="chat" class="workspaceSection" aria-label="ROBERTA chat workspace">
      <div class="workspaceShell">
        <aside class="workspaceSidebar">
          <div class="workspaceBrand"><span class="workspaceBrandMark">R</span><div><b>ROBERTA</b><small>Verified On-Chain Intelligence</small></div></div>
          <button id="newChat" class="btn primary workspaceWide">+ New Chat</button>

          <div class="workspaceGroupTitle">Chat history</div>
          <div id="historyList" class="historyList workspaceHistory"></div>
          <button id="clearHistory" class="sidebarTextButton">Clear chat history</button>

          <div class="workspaceGroupTitle serviceTitle">Services</div>
          <div class="workspaceServices">
            <button data-example="Check AGI."><b>Check a Token</b><span>Quick token health check</span></button>
            <button data-example="Which looks better right now, XNT or AGI?"><b>Compare Tokens</b><span>Compare two assets</span></button>
            <button data-example="Should I buy $500 of AGI right now?"><b>Should I Buy or Sell?</b><span>Opinion before a trade</span></button>
            <button data-example="Is AGI risky right now?"><b>Check Risk</b><span>Find important problems</span></button>
            <button data-example="Did a big wallet just buy AGI?"><b>Track Wallets &amp; Big Trades</b><span>Wallet and transaction activity</span></button>
            <button data-example="What does the GENIUS Act mean for USDC.X?"><b>Understand Regulations</b><span>Verified regulatory context</span></button>\n            <button data-example="What happened to AGI today?"><b>Ask ROBERTA</b><span>Ask anything normally</span></button>
          </div>

          <div class="workspaceLabelKey">
            <div class="workspaceGroupTitle">Answer labels</div>
            <span>Evidence</span><span>Risk</span><span>Freshness</span><span>Opinion</span>
          </div>
          <button id="backHome" class="sidebarTextButton backHome">← About ROBERTA</button>
        </aside>

        <div class="workspaceMain">
          <header class="workspaceTopbar">
            <div class="workspaceTopTitle"><b>ROBERTA</b><span>Ask about a token, trade, wallet, market move, or regulation.</span></div>
            <div class="workspaceTopActions">
              <div id="health" class="pill"><span class="dot"></span>Checking ROBERTA…</div>
              <span class="workspaceRouteLabel">X1</span>
              <span class="workspaceRouteLabel">Scout → CMIS</span>
              <span class="workspaceRouteLabel">Read-only</span>
              <button class="btn small" id="settingsBtn">Connection</button>
              <button id="clearChat" class="btn small">Clear chat</button>
            </div>
          </header>

          <div class="workspaceChat">
            <div id="messages" class="messages"></div>
            <div class="composer">
              <textarea id="composer" rows="4" placeholder="Ask ROBERTA anything… e.g. “Should I buy $500 of AGI?”"></textarea>
              <button id="send" class="btn primary">Send</button>
            </div>
            <div class="workspaceBoundary">Analysis and recommendations only. ROBERTA does not execute transactions from this website.</div>
          </div>
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
{id:'scan',name:'Instant X1 Scan',icon:'⚡',cat:'Core',status:'Available',desc:'Accepted X1 scan covering identity, market, tokenomics, history, risk, evidence quality and field-scoped freshness.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Run an Instant X1 Scan for '+v.asset+'. Use X1 Scout and the accepted instant_x1_scan/v6 path. Keep proof separate from risk and show unavailable fields.'}},
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
{id:'regulatory',name:'Regulatory Intelligence',icon:'§',cat:'Intelligence',status:'Available',desc:'Verified regulatory-framework evidence and bounded applicability for supported X1 assets. No legal advice or compliance label.',fields:[['asset','Asset / exact mint','text','e.g. USDC.X'],['framework','Framework','text','GENIUS Act']],prompt:function(v){return 'Run ROBERTA Regulatory Intelligence for '+v.asset+' under '+v.framework+'. Use X1 Scout operation=\'regulatory_evidence\' and accepted x1_regulatory_intelligence/v1. Preserve exact mint, jurisdiction/framework, rulemaking state, freshness, source provenance, applicability and representation dependencies. Do not give legal advice, do not label the asset COMPLIANT or NON_COMPLIANT, do not create an automatic risk conclusion, and keep execution unauthorized.'}},\n{id:'full',name:'Full Assessment',icon:'▣',cat:'Core',status:'Available',desc:'Broad assessment combining relevant accepted market, risk, tokenomics, history and evidence services.',fields:[['asset','Asset / mint','text','e.g. AGI']],prompt:function(v){return 'Run a full ROBERTA assessment for '+v.asset+'. Use relevant accepted Scout -> CMIS services, preserve unknowns and limitations, and give the answer first with evidence underneath.'}},
{id:'key',name:'Alert & Status Key',icon:'?',cat:'Evidence',status:'Available',desc:'Explains risk, CMIS status, verification, proof strength, freshness and execution labels.',fields:[],prompt:function(){return 'Show me ROBERTA\'s alert and status key, including risk, CMIS status, verification, proof strength, freshness, common warnings and execution meaning.'}},
{id:'opinion',name:'ROBERTA Opinion',icon:'◎',cat:'Core',status:'Available',desc:'Evidence-bounded judgment for decision questions using the accepted roberta_opinion/v1 contract.',fields:[['question','Decision question','text','e.g. Should I buy AGI?']],prompt:function(v){return 'Answer this decision question using the accepted ROBERTA Opinion Contract v1: '+v.question+' Lead with My recommendation, then Conviction, Evidence quality, My view, Best evidence against my view, and What would change my mind. Preserve Scout -> CMIS fact/risk authority and keep execution unauthorized.'}},
{id:'chat',name:'Ask Anything',icon:'✦',cat:'Core',status:'Available',desc:'Normal question; ROBERTA selects the appropriate specialist and verified-data path.',fields:[['question','Question','text','e.g. Is AGI getting stronger?']],prompt:function(v){return v.question}}
];
var HUMAN_SERVICE_POLICY=' Present this in Human ROBERTA mode. Lead with the answer and the few facts that matter most. Round display values to useful human precision without changing the underlying facts. Group related freshness gaps into one LIVE MARKET FRESHNESS statement. Use WHAT ROBERTA STILL NEEDS for no more than three prioritized, decision-relevant missing items. Do not expose raw snake_case limitation codes, internal contract invariants, implementation diagnostics, or duplicate caveats in the normal answer. Do not repeat freshness warnings inside RISK after LIVE MARKET FRESHNESS. Hide an unavailable numeric risk score unless I explicitly ask about risk scoring or technical details. Use EVIDENCE QUALITY instead of a raw evidence-status dump and end with a plain-English BOTTOM LINE. For opinion-bearing decision intents, apply the accepted roberta_opinion/v1 presentation contract: the first non-empty line is My recommendation: <TOKEN>, followed by Conviction, Evidence quality, My view, substantive Best evidence against my view, and What would change my mind. ROBERTA may disagree with the user and must not manufacture artificial neutrality. Recommendation strength is separate from evidence quality. Preserve every material unknown, conflict, WARN/BLOCK reason, and execution boundary; keep audit-level detail in the underlying structured evidence unless I explicitly ask for technical details.';
var cats=['All','Core','Market','Risk','Asset','History','Intelligence','Solana','Evidence'],activeCat='All',activeService=null,sending=false;
function el(s){return document.querySelector(s)}function base(){return(el('#apiBase').value||'').trim().replace(/\/$/,'')}function url(p){return base()?base()+p:p}function headers(){var h={'Content-Type':'application/json'},k=el('#apiKey').value.trim();if(k)h.Authorization='Bearer '+k;return h}
function renderFilters(){var f=el('#filters');if(!f)return;f.innerHTML=cats.map(function(c){return '<button class="filter '+(c===activeCat?'active':'')+'" data-cat="'+c+'">'+c+'</button>'}).join('')}
function render(){var search=el('#search'),grid=el('#grid');if(!search||!grid)return;var q=search.value.trim().toLowerCase(),list=services.filter(function(s){return(activeCat==='All'||s.cat===activeCat)&&(!q||(s.name+' '+s.desc+' '+s.cat).toLowerCase().indexOf(q)>=0)});grid.innerHTML=list.map(function(s){return '<article class="svc"><div class="svcTop"><div class="ico">'+s.icon+'</div><span class="tag '+((s.status==='Advanced'||s.status==='Configured')?'configured':'')+'">'+s.status+'</span></div><h3>'+s.name+'</h3><p>'+s.desc+'</p><div class="svcFoot"><span>'+(s.chain||'X1')+' · Read-only</span><button class="run" data-svc="'+s.id+'">Run →</button></div></article>'}).join('')||'<div style="color:var(--muted)">No matching services.</div>'}
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
    if(/^(My recommendation|Conviction|Evidence quality|My view)\s*:/i.test(line.trim())){var parts=safe.split(':');var label=parts.shift();out.push('<span class="opinionLine"><strong>'+label+':</strong>'+(parts.length?(' '+parts.join(':')):'')+'</span>');return}
    if(/^\s*[A-Z][A-Z0-9 &?\/—-]{2,}:?\s*$/.test(line.trim())){out.push('<span class="msgTitle">'+safe.replace(/:$/,'')+'</span>');return}
    safe=safe.replace(/\b(PASS|WARN|BLOCK|PARTIAL|VERIFIED|UNVERIFIED|UNAVAILABLE|NOT VERIFIED|WATCH|CLEAR|CAUTION|ERROR|AVAILABLE|STRONG|MODERATE|WEAK)\b/g,function(m){var cls=statusClass(m);return'<span class="statusToken '+cls+'">'+m+'</span>'});
    safe=safe.replace(/(^|[\s(])([+]\d[\d,]*(?:\.\d+)?%?)(?=$|[\s),.;])/g,'$1<span class="signedPositive">$2</span>');
    safe=safe.replace(/(^|[\s(])(-\d[\d,]*(?:\.\d+)?%?)(?=$|[\s),.;])/g,'$1<span class="signedNegative">$2</span>');
    out.push(safe)
  });
  return out.join('\n')
}
function msg(role,text){var d=document.createElement('div');d.className='msg '+role;if(role==='assistant')d.innerHTML=formatAssistant(text);else d.textContent=text;el('#messages').appendChild(d);el('#messages').scrollTop=el('#messages').scrollHeight;return d}
function starter(){return'I’m ready. Ask me about a token, trade, wallet, market move, risk, burn, history, bridge activity, regulation, or anything else you want me to investigate. You can also choose one of the simple services on the left for examples.'}
function loadHistory(){try{var raw=localStorage.getItem(CHAT_HISTORY_KEY);var parsed=raw?JSON.parse(raw):[];return Array.isArray(parsed)?parsed:[]}catch(e){return[]}}
function saveHistory(items){try{localStorage.setItem(CHAT_HISTORY_KEY,JSON.stringify(items.slice(0,CHAT_HISTORY_LIMIT)))}catch(e){}}
function chatTitle(text){var t=String(text||'').replace(/\s+/g,' ').trim();return t.length>58?t.slice(0,55)+'…':t||'Untitled chat'}
function renderHistory(){var list=el('#historyList'),items=loadHistory();if(!items.length){list.innerHTML='<div class="historyEmpty">No saved chats yet.</div>';return}var today=new Date().toDateString(),groups={Today:[],Previous:[]};items.forEach(function(item){var d=item.createdAt?new Date(item.createdAt):null;groups[d&&d.toDateString()===today?'Today':'Previous'].push(item)});list.innerHTML=['Today','Previous'].map(function(label){var group=groups[label];if(!group.length)return'';return'<div class="historyGroupTitle">'+label+'</div>'+group.map(function(item){var when=item.createdAt?new Date(item.createdAt).toLocaleString():'';return'<button class="historyItem" data-chat-id="'+escapeHtml(item.id)+'"><span class="historyItemTitle">'+escapeHtml(item.title)+'</span><span class="historyItemTime">'+escapeHtml(when)+'</span></button>'}).join('')}).join('')}
function renderChat(messages){el('#messages').innerHTML='';if(!Array.isArray(messages)||!messages.length){msg('assistant',starter());return}messages.forEach(function(item){if(item&&item.role&&typeof item.text==='string')msg(item.role,item.text)})}
function recordUserMessage(userText){var items=loadHistory(),item=currentChatId?items.find(function(x){return x.id===currentChatId}):null;if(!item){currentChatId='chat-'+Date.now()+'-'+Math.random().toString(36).slice(2,8);item={id:currentChatId,title:chatTitle(userText),createdAt:new Date().toISOString(),messages:[]};items.unshift(item)}item.messages.push({role:'user',text:userText});saveHistory(items);renderHistory();return currentChatId}
function appendSavedChat(id,role,text){var items=loadHistory(),item=items.find(function(x){return x.id===id});if(!item)return;item.messages.push({role:role,text:text});saveHistory(items);renderHistory()}
function openSavedChat(id){var item=loadHistory().find(function(x){return x.id===id});if(!item)return;currentChatId=id;renderChat(item.messages)}
function restoreLatestChat(){var items=loadHistory();if(items.length){currentChatId=items[0].id;renderChat(items[0].messages)}else renderChat([])}
function clearCurrentChat(){currentChatId=null;renderChat([]);el('#composer').value=''}
function clearAllHistory(){saveHistory([]);currentChatId=null;renderHistory();renderChat([])}
function enterWorkspace(mode,focusComposer){document.body.classList.add('workspaceMode');sessionStorage.setItem('robertaWorkspaceMode',mode||'human');if(mode==='agent')el('#settings').classList.add('open');if(focusComposer!==false)setTimeout(function(){el('#composer').focus()},30)}
function leaveWorkspace(){document.body.classList.remove('workspaceMode');sessionStorage.removeItem('robertaWorkspaceMode');el('#settings').classList.remove('open');window.scrollTo({top:0,behavior:'smooth'})}
function useExample(text){enterWorkspace('human',false);el('#composer').value=text;setTimeout(function(){el('#composer').focus()},30)}
function busy(v){sending=v;el('#send').disabled=v;el('#send').textContent=v?'Working…':'Send'}
async function health(){var h=el('#health');try{var r=await fetch(url('/healthz'));var d=await r.json();if(r.ok&&d.status==='ok'){h.className='pill online';h.innerHTML='<span class="dot"></span>ROBERTA online';return}throw 0}catch(e){h.className='pill offline';h.innerHTML='<span class="dot"></span>ROBERTA offline'}}
async function send(text){text=(text||'').trim();if(!text||sending)return;var chatId=recordUserMessage(text);msg('user',text);el('#composer').value='';busy(true);var wait=msg('system','ROBERTA is checking accepted evidence…');try{var r=await fetch(url('/v1/roberta'),{method:'POST',headers:headers(),body:JSON.stringify({message:text})}),d=await r.json().catch(function(){return{}});wait.remove();var reply=!r.ok?((d.error&&d.error.message)||('Request failed ('+r.status+')')):(d.reply||'ROBERTA returned no reply.');msg('assistant',reply);appendSavedChat(chatId,'assistant',reply)}catch(e){wait.remove();var reply='I could not reach the ROBERTA bridge. Verify that it is running and check Connection settings.';msg('assistant',reply);appendSavedChat(chatId,'assistant',reply)}finally{busy(false);health()}}
renderFilters();render();renderHistory();restoreLatestChat();var savedWorkspaceMode=sessionStorage.getItem('robertaWorkspaceMode');if(savedWorkspaceMode)enterWorkspace(savedWorkspaceMode,false);health();setInterval(health,30000);
document.addEventListener('click',function(e){var s=e.target.closest('[data-svc]');if(s)openSvc(s.dataset.svc);var g=e.target.closest('[data-go]');if(g)document.getElementById(g.dataset.go).scrollIntoView({behavior:'smooth'});var c=e.target.closest('[data-cat]');if(c){activeCat=c.dataset.cat;renderFilters();render()}var x=e.target.closest('[data-example]');if(x)useExample(x.dataset.example)});
var searchBox=el('#search');if(searchBox)searchBox.addEventListener('input',render);el('#close').onclick=closeSvc;el('#cancel').onclick=closeSvc;el('#modalBg').addEventListener('click',function(e){if(e.target===el('#modalBg'))closeSvc()});
el('#serviceForm').addEventListener('submit',function(e){e.preventDefault();if(!activeService)return;var data=Object.fromEntries(new FormData(e.currentTarget).entries()),p=humanServicePrompt(activeService.prompt(data),activeService.id);closeSvc();document.getElementById('chat').scrollIntoView({behavior:'smooth'});send(p)});
el('#send').onclick=function(){send(el('#composer').value)};el('#composer').addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(el('#composer').value)}});
el('#newChat').onclick=clearCurrentChat;el('#clearChat').onclick=clearCurrentChat;el('#clearHistory').onclick=clearAllHistory;el('#historyList').addEventListener('click',function(e){var item=e.target.closest('[data-chat-id]');if(item)openSavedChat(item.dataset.chatId)});el('#backHome').onclick=leaveWorkspace;el('#connectHuman').onclick=function(){enterWorkspace('human')};el('#connectAgent').onclick=function(){enterWorkspace('agent')};el('#connectNav').onclick=function(){enterWorkspace('human')};
el('#settingsBtn').onclick=function(){el('#settings').classList.toggle('open')};el('#apiBase').value=sessionStorage.getItem('robertaApiBase')||'';el('#apiKey').value=sessionStorage.getItem('robertaApiKey')||'';el('#apiBase').onchange=function(){sessionStorage.setItem('robertaApiBase',this.value.trim());health()};el('#apiKey').onchange=function(){sessionStorage.setItem('robertaApiKey',this.value);health()};
</script>

<script>
(function(){
  'use strict';
  var canvas=document.getElementById('robertaHeroCanvas');
  if(!canvas)return;
  var ctx=canvas.getContext('2d',{alpha:true,desynchronized:true});
  if(!ctx)return;

  var reduceMotion=window.matchMedia&&window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var dpr=Math.min(window.devicePixelRatio||1,2);
  var w=0,h=0,raf=0,last=0,visible=!document.hidden;
  var particles=[],strands=[],stars=[];
  var pointer={x:0,y:0,active:false};

  function rand(a,b){return a+Math.random()*(b-a)}
  function clamp(v,a,b){return Math.max(a,Math.min(b,v))}
  function resize(){
    var r=canvas.getBoundingClientRect(); w=Math.max(1,r.width); h=Math.max(1,r.height);
    dpr=Math.min(window.devicePixelRatio||1,2);
    canvas.width=Math.round(w*dpr); canvas.height=Math.round(h*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    build();
    draw(performance.now(),true);
  }

  function profilePoint(t){
    var cx=w*.46,cy=h*.51,rx=w*.21,ry=h*.31;
    var a=t*Math.PI*2;
    var x=cx+Math.cos(a)*rx, y=cy+Math.sin(a)*ry;
    if(Math.cos(a)>.2){
      var front=(Math.cos(a)-.2)/.8;
      x+=front*w*.045;
      if(y<cy-h*.02&&y>cy-h*.16)x+=front*w*.025;
      if(y>cy+h*.08&&y<cy+h*.18)x-=front*w*.024;
    }
    return{x:x,y:y};
  }

  function insideHead(x,y){
    var cx=w*.46,cy=h*.51,rx=w*.205,ry=h*.30;
    var nx=(x-cx)/rx,ny=(y-cy)/ry;
    var base=nx*nx+ny*ny<1;
    if(!base)return false;
    if(nx>.18){
      var bulge=.14*Math.sin((ny+.15)*8)-.04*ny;
      return nx<.93+bulge;
    }
    return true;
  }

  function build(){
    particles=[];strands=[];stars=[];
    var area=w*h;
    var pc=clamp(Math.floor(area/1900),180,540);
    var attempts=0;
    while(particles.length<pc&&attempts<pc*12){
      attempts++;
      var x=rand(w*.19,w*.69), y=rand(h*.17,h*.84);
      if(insideHead(x,y)){
        particles.push({x:x,y:y,ox:x,oy:y,r:rand(.55,1.55),phase:rand(0,Math.PI*2),speed:rand(.25,.9)});
      }
    }
    var sc=clamp(Math.floor(w/22),26,54);
    for(var i=0;i<sc;i++){
      var t=rand(.40,.72);
      var p=profilePoint(t);
      var len=rand(w*.17,w*.39);
      strands.push({sx:p.x-w*.06,sy:p.y,cp1x:p.x-len*.24,cp1y:p.y+rand(-70,70),cp2x:p.x-len*.62,cp2y:p.y+rand(-95,95),ex:p.x-len,ey:p.y+rand(-115,115),phase:rand(0,Math.PI*2),amp:rand(5,19),speed:rand(.35,.8),alpha:rand(.16,.46)});
    }
    for(var j=0;j<clamp(Math.floor(area/12000),45,110);j++)stars.push({x:rand(0,w),y:rand(0,h),r:rand(.35,1.2),phase:rand(0,6.28)});
  }

  function lineGlow(x1,y1,x2,y2,a){
    var g=ctx.createLinearGradient(x1,y1,x2,y2);
    g.addColorStop(0,'rgba(67,196,255,'+a+')');
    g.addColorStop(.55,'rgba(92,106,255,'+(a*.85)+')');
    g.addColorStop(1,'rgba(166,73,255,0)');
    ctx.strokeStyle=g;
  }

  function draw(ts,force){
    if(!force&&!visible)return;
    var t=ts*.001;
    ctx.clearRect(0,0,w,h);

    var bg=ctx.createRadialGradient(w*.51,h*.5,10,w*.51,h*.5,w*.42);
    bg.addColorStop(0,'rgba(33,72,183,.13)'); bg.addColorStop(.5,'rgba(34,32,111,.055)'); bg.addColorStop(1,'rgba(5,8,23,0)');
    ctx.fillStyle=bg;ctx.fillRect(0,0,w,h);

    for(var s=0;s<stars.length;s++){
      var st=stars[s],sa=.12+.22*(.5+.5*Math.sin(t*.65+st.phase));
      ctx.beginPath();ctx.arc(st.x,st.y,st.r,0,Math.PI*2);ctx.fillStyle='rgba(116,184,255,'+sa+')';ctx.fill();
    }

    ctx.save();ctx.globalCompositeOperation='lighter';
    for(var k=0;k<strands.length;k++){
      var q=strands[k],wave=Math.sin(t*q.speed+q.phase)*q.amp;
      ctx.beginPath();ctx.moveTo(q.sx,q.sy);
      ctx.bezierCurveTo(q.cp1x,q.cp1y+wave,q.cp2x,q.cp2y-wave*.7,q.ex,q.ey+wave);
      lineGlow(q.sx,q.sy,q.ex,q.ey,q.alpha);
      ctx.lineWidth=.55+(k%4===0?.7:0);ctx.stroke();
      if(k%5===0){
        var tt=(t*q.speed*.13+q.phase)%1;
        var mt=1-tt,u=tt;
        var mx=mt*mt*mt*q.sx+3*mt*mt*u*q.cp1x+3*mt*u*u*q.cp2x+u*u*u*q.ex;
        var my=mt*mt*mt*q.sy+3*mt*mt*u*(q.cp1y+wave)+3*mt*u*u*(q.cp2y-wave*.7)+u*u*u*(q.ey+wave);
        ctx.beginPath();ctx.arc(mx,my,1.7,0,Math.PI*2);ctx.fillStyle='rgba(99,213,255,.85)';ctx.fill();
      }
    }

    for(var i=0;i<particles.length;i++){
      var p=particles[i],pulse=.65+.35*Math.sin(t*p.speed+p.phase);
      var dx=0,dy=0;
      if(pointer.active&&!reduceMotion){
        var px=p.ox-pointer.x,py=p.oy-pointer.y,dist=Math.sqrt(px*px+py*py);
        if(dist<120&&dist>1){var push=(120-dist)/120*5;dx=px/dist*push;dy=py/dist*push}
      }
      p.x=p.ox+dx+Math.sin(t*.35+p.phase)*.65;p.y=p.oy+dy+Math.cos(t*.29+p.phase)*.65;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r*(.85+pulse*.35),0,Math.PI*2);
      ctx.fillStyle='rgba('+(110+Math.floor(60*pulse))+','+(175+Math.floor(55*pulse))+',255,'+(.35+.55*pulse)+')';ctx.fill();
      if(i%18===0){ctx.beginPath();ctx.arc(p.x,p.y,p.r*4.2,0,Math.PI*2);ctx.fillStyle='rgba(80,122,255,.035)';ctx.fill()}
    }

    var connections=particles.length>350?85:60;
    for(var a=0;a<connections;a++){
      var p1=particles[(a*7)%particles.length],p2=particles[(a*13+17)%particles.length];
      var ddx=p1.x-p2.x,ddy=p1.y-p2.y,dist2=ddx*ddx+ddy*ddy;
      if(dist2<7200){ctx.beginPath();ctx.moveTo(p1.x,p1.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='rgba(85,158,255,.055)';ctx.lineWidth=.5;ctx.stroke()}
    }

    var cx=w*.84,cy=h*.47,maxR=Math.min(w,h)*.24;
    for(var r=1;r<=3;r++){ctx.beginPath();ctx.arc(cx,cy,maxR*(.40+r*.22),0,Math.PI*2);ctx.strokeStyle='rgba(104,117,255,'+(r===2?.16:.09)+')';ctx.lineWidth=.7;ctx.stroke()}
    for(var n=0;n<16;n++){
      var ang=n/16*Math.PI*2+t*.035*(n%2?1:-1),rr=maxR*(.52+(n%3)*.15);
      var nx=cx+Math.cos(ang)*rr,ny=cy+Math.sin(ang)*rr;
      ctx.beginPath();ctx.arc(nx,ny,n%5===0?2.1:1.1,0,Math.PI*2);ctx.fillStyle=n%4===0?'rgba(183,77,255,.9)':'rgba(72,201,255,.75)';ctx.fill();
      if(n%4===0){ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(nx,ny);ctx.strokeStyle='rgba(79,142,255,.07)';ctx.lineWidth=.6;ctx.stroke()}
    }
    ctx.restore();

    if(!reduceMotion&&visible)raf=requestAnimationFrame(draw);
  }

  function start(){if(reduceMotion){draw(performance.now(),true);return}cancelAnimationFrame(raf);raf=requestAnimationFrame(draw)}
  document.addEventListener('visibilitychange',function(){visible=!document.hidden;if(visible)start();else cancelAnimationFrame(raf)});
  canvas.addEventListener('pointermove',function(e){var r=canvas.getBoundingClientRect();pointer.x=e.clientX-r.left;pointer.y=e.clientY-r.top;pointer.active=true});
  canvas.addEventListener('pointerleave',function(){pointer.active=false});
  if('ResizeObserver'in window)new ResizeObserver(resize).observe(canvas.parentElement);else window.addEventListener('resize',resize);
  resize();start();
})();
</script>

</body></html>'''


def web_ui_bytes() -> bytes:
    return ROBERTA_WEB_UI_HTML.encode("utf-8")


__all__ = ["ROBERTA_WEB_UI_HTML", "web_ui_bytes"]
