"""Conversation-first web interface for ROBERTA — Verified On-Chain Intelligence."""

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
  --bg:#050712;--bg2:#070b1a;--panel:#0a1023;--panel2:#0f1730;--line:rgba(130,154,255,.17);
  --text:#f6f8ff;--muted:#96a2c5;--blue:#58baff;--violet:#8b5cff;--cyan:#5ce6ff;
  --green:#79e2ad;--amber:#ffd27f;--red:#ff8c99;--shadow:0 26px 90px rgba(0,0,0,.38);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;background:var(--bg)}
body{margin:0;color:var(--text);background:
  radial-gradient(circle at 17% 7%,rgba(61,89,218,.17),transparent 24%),
  radial-gradient(circle at 84% 10%,rgba(132,65,219,.11),transparent 20%),
  linear-gradient(180deg,var(--bg),#060919 50%,#040610);
  font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
body:before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background-image:
  linear-gradient(rgba(106,130,240,.026) 1px,transparent 1px),
  linear-gradient(90deg,rgba(106,130,240,.026) 1px,transparent 1px);
  background-size:70px 70px;mask-image:linear-gradient(to bottom,#000,transparent 84%)}
button,input,textarea{font:inherit}
button{cursor:pointer}
.shell{width:min(1160px,calc(100% - 36px));margin:auto}
.hidden{display:none!important}

.topbar{position:sticky;top:0;z-index:50;background:rgba(5,7,18,.84);backdrop-filter:blur(22px);border-bottom:1px solid rgba(130,153,255,.11)}
.topbarInner{height:74px;display:flex;align-items:center;justify-content:space-between;gap:18px}
.brand{display:flex;align-items:center;gap:11px}
.brandMark,.workspaceMark{width:41px;height:41px;border-radius:12px;display:grid;place-items:center;font-weight:900;background:linear-gradient(145deg,#4aa8ff,#805aff 62%,#b14cff);box-shadow:0 0 30px rgba(78,111,255,.26)}
.brandText b{display:block;letter-spacing:.27em;font-size:14px}.brandText span{display:block;color:var(--muted);font-size:8px;letter-spacing:.13em;margin-top:3px}
.nav{display:flex;align-items:center;gap:4px}.nav button{border:0;background:transparent;color:#c2cae9;padding:9px 11px;border-radius:999px;font-size:10px;letter-spacing:.08em;text-transform:uppercase}.nav button:hover{background:rgba(103,129,255,.08);color:#fff}
.actions{display:flex;align-items:center;gap:8px}
.btn{border:1px solid var(--line);background:rgba(10,15,34,.78);color:var(--text);padding:10px 15px;border-radius:999px;font-weight:800}.btn:hover{border-color:rgba(85,183,255,.48);box-shadow:0 10px 30px rgba(67,88,206,.14)}.btn.primary{border-color:transparent;background:linear-gradient(100deg,#327fff,#6d58ff 52%,#a546ff);box-shadow:0 0 30px rgba(79,88,255,.24)}.btn.small{padding:7px 10px;font-size:9px}.btn.icon{width:34px;height:34px;padding:0;display:grid;place-items:center}

.hero{min-height:calc(100vh - 74px);display:grid;place-items:center;position:relative;overflow:hidden;padding:52px 0}
.heroAura{position:absolute;inset:0;pointer-events:none;background:
 radial-gradient(circle at 50% 42%,rgba(56,91,219,.18),transparent 24%),
 radial-gradient(circle at 63% 35%,rgba(136,63,219,.10),transparent 24%)}
.heroInner{position:relative;z-index:1;text-align:center;max-width:940px;margin:auto}
.eyebrow{display:inline-flex;align-items:center;gap:8px;border:1px solid rgba(104,151,255,.23);background:rgba(11,18,44,.70);color:#a9cfff;border-radius:999px;padding:7px 11px;font-size:9px;font-weight:900;letter-spacing:.14em;text-transform:uppercase}.eyebrow:before{content:"✦";color:var(--cyan)}
.hero h1{font-size:clamp(62px,9vw,110px);line-height:.88;letter-spacing:-.067em;margin:23px 0 18px}.hero h1 span{background:linear-gradient(90deg,#eff5ff,#68c8ff 40%,#9667ff 76%,#e1a7ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.heroTag{font-size:clamp(21px,2.5vw,32px);line-height:1.2;letter-spacing:-.03em;margin:0 auto 13px;max-width:860px}.heroLead{color:var(--muted);font-size:15px;max-width:760px;margin:0 auto}
.askBox{margin:31px auto 0;max-width:850px;border:1px solid rgba(109,150,255,.28);background:linear-gradient(180deg,rgba(12,18,42,.93),rgba(7,11,27,.95));border-radius:23px;padding:12px;display:grid;grid-template-columns:1fr auto;gap:9px;box-shadow:0 26px 80px rgba(24,39,120,.21)}
.askBox textarea{resize:none;min-height:68px;max-height:150px;border:0;background:transparent;color:#f4f6ff;padding:10px 11px;outline:none;font-size:16px}.askBox textarea::placeholder{color:#7180aa}.askBox .btn{align-self:end;margin-bottom:3px}
.heroExamples{display:flex;justify-content:center;gap:7px;flex-wrap:wrap;margin:14px auto 0;max-width:900px}.heroExample{border:1px solid rgba(126,151,255,.13);background:rgba(8,13,31,.70);color:#b7c0e0;border-radius:999px;padding:7px 10px;font-size:9px}.heroExample:hover{border-color:rgba(85,183,255,.38);color:#fff;background:rgba(15,23,50,.82)}
.heroFoot{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;margin-top:25px}.heroFoot span{border:1px solid rgba(127,151,255,.12);background:rgba(8,13,31,.58);border-radius:999px;padding:6px 9px;color:#8f9abc;font-size:8px}.heroFoot b{color:#e8edff}

.section{padding:86px 0}.section.alt{background:rgba(9,13,31,.36);border-top:1px solid rgba(124,150,255,.08);border-bottom:1px solid rgba(124,150,255,.08)}
.sectionHead{display:grid;grid-template-columns:1fr .86fr;gap:28px;align-items:end;margin-bottom:31px}.kicker{color:#6fc7ff;font-size:9px;letter-spacing:.15em;font-weight:900;text-transform:uppercase}.sectionHead h2{font-size:clamp(34px,4.6vw,55px);line-height:1;letter-spacing:-.045em;margin:8px 0 0}.sectionHead p{color:var(--muted);font-size:14px;margin:0}
.helpGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.helpCard{border:1px solid rgba(126,151,255,.14);background:rgba(9,14,33,.76);border-radius:20px;padding:19px}.helpCard h3{font-size:15px;margin:0 0 5px}.helpCard p{color:var(--muted);font-size:11px;margin:0 0 13px}.helpCard button{border:0;background:transparent;color:#75cfff;padding:0;font-size:9px;font-weight:900}
.trustGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.trustCard{border:1px solid rgba(126,151,255,.14);background:rgba(9,14,33,.76);border-radius:20px;padding:20px}.trustCard i{width:36px;height:36px;border-radius:11px;display:grid;place-items:center;font-style:normal;background:rgba(76,123,255,.13);color:#89d5ff}.trustCard h3{font-size:15px;margin:15px 0 6px}.trustCard p{color:var(--muted);font-size:11px;margin:0}
.footer{padding:28px 0 42px;color:#6f7b9f;font-size:8px}.footerInner{display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap}

#workspace{display:none;min-height:100vh}.workspaceMode #landing{display:none}.workspaceMode #workspace{display:block}
.workspaceGrid{min-height:100vh;display:grid;grid-template-columns:260px minmax(0,1fr) 310px}
.sidebar{position:sticky;top:0;height:100vh;overflow:auto;border-right:1px solid rgba(128,154,255,.12);background:rgba(5,9,23,.97);padding:18px 14px;display:flex;flex-direction:column}
.workspaceBrand{display:flex;align-items:center;gap:9px;padding:2px 2px 14px}.workspaceBrand b{display:block;letter-spacing:.18em;font-size:12px}.workspaceBrand span{display:block;color:#7d89ad;font-size:7px;margin-top:2px}
.sidebarTitle{color:#69769d;font-size:8px;letter-spacing:.13em;font-weight:900;text-transform:uppercase;margin:17px 4px 6px}
.historyList,.savedList{display:grid;gap:5px;max-height:25vh;overflow:auto}.historyGroup{color:#637097;font-size:8px;text-transform:uppercase;letter-spacing:.12em;padding:6px 5px 2px}
.historyItem,.savedItem{border:1px solid rgba(123,148,255,.11);background:rgba(10,15,34,.64);color:#dce1f7;border-radius:11px;padding:8px 9px;text-align:left;width:100%}.historyItem:hover,.savedItem:hover{border-color:rgba(85,183,255,.3);background:rgba(15,22,49,.78)}.historyItem b,.savedItem b{display:block;font-size:9px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.historyItem span,.savedItem span{display:block;color:#707c9f;font-size:7px;margin-top:2px}
.savedRow{display:grid;grid-template-columns:1fr auto;gap:4px}.recheckBtn{border:1px solid rgba(126,151,255,.11);background:rgba(9,14,31,.64);color:#73cfff;border-radius:10px;padding:0 7px;font-size:8px}
.sideLink{border:0;background:transparent;color:#8390b7;text-align:left;padding:6px 3px;font-size:8px}.sideLink:hover{color:#fff}
.servicesToggle{display:flex;align-items:center;justify-content:space-between;width:100%;border:0;background:transparent;color:#b8c1df;padding:0 4px 6px;font-size:9px;font-weight:900}.sideServices{display:grid;gap:5px}.sideServices.closed{display:none}
.sideService{border:1px solid rgba(122,149,255,.11);background:rgba(9,14,32,.66);color:#e8ebfb;border-radius:11px;padding:8px 9px;text-align:left}.sideService:hover{border-color:rgba(83,186,255,.33);background:rgba(16,23,50,.8)}.sideService b{display:block;font-size:9px}.sideService span{display:block;color:#727fa5;font-size:7px;margin-top:2px}
.backAbout{margin-top:auto}

.workspaceMain{min-width:0;height:100vh;display:flex;flex-direction:column;background:radial-gradient(circle at 72% 0,rgba(71,80,200,.10),transparent 30%),#060918}
.workspaceHeader{min-height:68px;border-bottom:1px solid rgba(126,151,255,.11);display:grid;grid-template-columns:auto minmax(240px,1fr) auto;align-items:center;gap:12px;padding:10px 16px;background:rgba(6,9,23,.84);backdrop-filter:blur(18px)}
.workspaceHeading b{display:block;letter-spacing:.15em;font-size:12px}.workspaceHeading span{display:block;color:#7d88aa;font-size:8px;margin-top:1px}
.commandBar{display:grid;grid-template-columns:1fr auto;gap:6px;border:1px solid rgba(126,151,255,.14);background:#050817;border-radius:999px;padding:4px 5px 4px 12px}.commandBar input{border:0;outline:none;background:transparent;color:#edf1ff;font-size:10px;min-width:0}.commandBar input::placeholder{color:#66739b}.commandBar button{border:0;background:linear-gradient(100deg,#337fff,#7556ef);color:#fff;border-radius:999px;padding:6px 10px;font-size:8px;font-weight:900}
.workspaceHeaderActions{display:flex;align-items:center;gap:5px}.health{display:inline-flex;align-items:center;border:1px solid rgba(126,151,255,.12);border-radius:999px;padding:6px 8px;color:#8d99bd;font-size:7px}.health:before{content:"";width:5px;height:5px;border-radius:50%;background:#8992a8;margin-right:5px}.health.online{color:#8ce9ba;border-color:rgba(94,220,159,.2)}.health.online:before{background:#68dfa6;box-shadow:0 0 0 4px rgba(104,223,166,.08)}.health.offline{color:#ff9aa4;border-color:rgba(255,118,132,.2)}.health.offline:before{background:#ff7e8d}

.chatArea{min-height:0;flex:1;display:flex;flex-direction:column;width:100%;margin:0 auto;padding:14px 18px 10px}
.messages{flex:1;min-height:0;overflow:auto;border:1px solid rgba(126,151,255,.10);border-bottom:0;border-radius:22px 22px 0 0;background:linear-gradient(180deg,rgba(8,12,28,.72),rgba(6,9,21,.92));padding:19px;display:flex;flex-direction:column;gap:12px}
.msgWrap{max-width:90%;display:flex;flex-direction:column;gap:5px}.msgWrap.user{align-self:flex-end;align-items:flex-end}.msgWrap.assistant{align-self:flex-start;align-items:flex-start}
.msg{padding:12px 14px;border-radius:16px;white-space:pre-wrap;word-break:break-word}.msg.user{background:linear-gradient(105deg,#356ff1,#7157ef);color:#fff;border-bottom-right-radius:5px}.msg.assistant{background:rgba(12,18,40,.90);border:1px solid rgba(126,151,255,.12);color:#e6eafc;border-bottom-left-radius:5px}.msg.system{align-self:center;color:#7480a3;font-size:8px;padding:4px}
.msgTitle{display:block;color:#fff;font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;margin:4px 0 6px}.opinionLine,.factLine,.uncertainLine,.confidenceLine{display:block;margin:4px 0}.opinionLine strong{color:#83d0ff}.factLine strong{color:#7fe5b1}.uncertainLine strong{color:#ffd27f}.confidenceLine strong{color:#c3a6ff}
.statusToken{display:inline-flex;align-items:center;padding:1px 6px;border-radius:999px;border:1px solid rgba(135,150,190,.18);background:rgba(120,135,170,.08);color:#aeb7d3;font-size:.88em;font-weight:900}.statusToken.good{color:#7ce4ae;border-color:rgba(89,211,146,.22);background:rgba(49,140,93,.1)}.statusToken.warn{color:#ffd27f;border-color:rgba(255,203,104,.2);background:rgba(156,111,26,.1)}.statusToken.bad{color:#ff909d;border-color:rgba(255,118,132,.2);background:rgba(157,45,60,.1)}
.pos{color:#77e2ad;font-weight:900}.neg{color:#ff8f9a;font-weight:900}
.entityLink{display:inline;border:0;background:transparent;color:#70cbff;padding:0;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:2px;font:inherit;cursor:pointer}
.answerActions{display:flex;gap:5px;flex-wrap:wrap}.answerActions button{border:1px solid rgba(126,151,255,.12);background:rgba(8,13,31,.72);color:#9facca;border-radius:999px;padding:5px 8px;font-size:7px}.answerActions button:hover{border-color:rgba(85,183,255,.35);color:#fff}

.emptyState{margin:auto;max-width:720px;width:100%;text-align:center;padding:22px}.emptyState h2{font-size:clamp(27px,4vw,42px);letter-spacing:-.04em;margin:0 0 8px}.emptyState p{color:#8793b8;font-size:11px;margin:0 0 18px}.emptyGrid{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.emptyGrid button{border:1px solid rgba(126,151,255,.13);background:rgba(10,15,34,.68);color:#d8def4;border-radius:14px;padding:12px;text-align:left;font-size:9px}.emptyGrid button:hover{border-color:rgba(85,183,255,.34);background:rgba(16,24,52,.8)}.emptyHint{margin-top:15px;color:#69769b;font-size:9px}

.investigating{align-self:flex-start;border:1px solid rgba(105,162,255,.16);background:rgba(9,15,36,.88);border-radius:16px;padding:12px 14px;min-width:260px}.investigating b{display:block;font-size:10px;margin-bottom:7px}.investigateStep{display:flex;align-items:center;gap:7px;color:#7986aa;font-size:8px;margin-top:5px}.investigateStep:before{content:"○";color:#657199}.investigateStep.done{color:#a6b0cf}.investigateStep.done:before{content:"✓";color:#72dda8}.investigateStep.active{color:#c2d8ff}.investigateStep.active:before{content:"●";color:#62c7ff}

.composer{border:1px solid rgba(126,151,255,.10);background:rgba(8,12,29,.94);border-radius:0 0 22px 22px;padding:11px;display:grid;grid-template-columns:1fr auto;gap:8px}.composer textarea{resize:vertical;min-height:70px;max-height:170px;border:1px solid rgba(126,151,255,.14);background:#050817;color:#eef1ff;border-radius:15px;padding:12px 13px;outline:none}.composer textarea:focus{border-color:rgba(79,185,255,.42)}.boundary{text-align:center;color:#606b8d;font-size:7px;padding:7px 0 0}

.inspector{position:sticky;top:0;height:100vh;overflow:auto;border-left:1px solid rgba(126,151,255,.12);background:rgba(6,10,25,.97);padding:16px 14px;transition:.2s}
.inspector.collapsed{width:52px;padding:14px 8px;overflow:hidden}.inspector.collapsed .inspectorContent,.inspector.collapsed .inspectorTitle span{display:none}.inspector.collapsed .inspectorTitle{justify-content:center}
.inspectorTitle{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:14px}.inspectorTitle b{font-size:11px;letter-spacing:.08em}.inspectorTitle span{display:block;color:#7885a9;font-size:7px;margin-top:2px}
.inspectorBlock{border-top:1px solid rgba(126,151,255,.10);padding:12px 0}.inspectorBlock:first-child{border-top:0}.inspectorBlock h4{font-size:8px;text-transform:uppercase;letter-spacing:.12em;color:#707da4;margin:0 0 7px}.inspectorValue{color:#cad2ed;font-size:9px}.inspectorNote{color:#7380a3;font-size:8px;line-height:1.5}
.detailChips{display:flex;gap:5px;flex-wrap:wrap}.detailChip{border:1px solid rgba(126,151,255,.12);border-radius:999px;padding:4px 7px;color:#97a4c8;font-size:7px}.detailChip.good{color:#7ce4ae;border-color:rgba(89,211,146,.2)}.detailChip.warn{color:#ffd27f;border-color:rgba(255,203,104,.2)}.detailChip.bad{color:#ff909d;border-color:rgba(255,118,132,.2)}
.inspectorActions{display:grid;gap:5px}.inspectorActions button{border:1px solid rgba(126,151,255,.12);background:rgba(9,14,32,.65);color:#b7c1df;border-radius:11px;padding:8px 9px;text-align:left;font-size:8px}.inspectorActions button:hover{border-color:rgba(84,186,255,.33);color:#fff}.entityDetail{word-break:break-all;color:#7fcfff;font-size:8px}

.settings{display:none;position:fixed;z-index:90;right:20px;top:78px;width:min(390px,calc(100vw - 40px));background:#0b1024;border:1px solid rgba(126,151,255,.2);border-radius:22px;padding:17px;box-shadow:var(--shadow)}.settings.open{display:block}.settings h3{margin:0 0 11px;font-size:15px}.field{display:grid;gap:5px;margin-top:9px}.field label{color:#8d98ba;font-size:8px}.field input{border:1px solid rgba(126,151,255,.16);background:#060918;color:#eef1ff;border-radius:11px;padding:9px 10px;outline:none}.settingNote{color:#6e7a9d;font-size:7px;margin-top:9px}.agentBox{border:1px solid rgba(96,190,255,.17);background:rgba(9,20,38,.72);border-radius:13px;padding:10px;margin-top:11px}.agentBox b{font-size:8px}.agentBox code{display:block;color:#9bdcff;font-size:8px;margin-top:4px;word-break:break-all}

@media(max-width:1160px){.workspaceGrid{grid-template-columns:235px minmax(0,1fr) 270px}.workspaceHeader{grid-template-columns:auto 1fr}.workspaceHeaderActions{grid-column:1/-1;justify-content:flex-end}.helpGrid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:940px){.nav{display:none}.sectionHead{grid-template-columns:1fr}.trustGrid{grid-template-columns:1fr}.workspaceGrid{grid-template-columns:220px minmax(0,1fr)}.inspector{position:fixed;right:0;top:0;z-index:70;width:min(320px,90vw);box-shadow:-20px 0 60px rgba(0,0,0,.35)}.inspector.collapsed{width:44px}.helpGrid{grid-template-columns:1fr}}
@media(max-width:720px){.shell{width:min(100% - 24px,1160px)}.topbarInner{height:66px}.brandText span{display:none}.hero{padding:40px 0}.hero h1{font-size:62px}.askBox{grid-template-columns:1fr}.askBox .btn{width:100%}.section{padding:64px 0}.workspaceGrid{display:block}.sidebar{position:relative;height:auto;max-height:none;border-right:0;border-bottom:1px solid rgba(126,151,255,.11)}.historyList,.savedList{max-height:150px}.sideServices{grid-template-columns:repeat(2,1fr)}.backAbout{margin-top:12px}.workspaceMain{height:auto;min-height:100vh}.workspaceHeader{grid-template-columns:1fr;align-items:stretch}.workspaceHeaderActions{justify-content:flex-start}.commandBar{order:3}.chatArea{min-height:74vh;padding:10px}.messages{min-height:53vh}.emptyGrid{grid-template-columns:1fr}.inspector{display:none}.composer{grid-template-columns:1fr}}
@media(max-width:480px){.actions #agentEntryTop{display:none}.heroExamples{display:grid}.heroExample{width:100%}.sideServices{grid-template-columns:1fr}}
</style>
</head>
<body>

<div id="landing">
  <header class="topbar">
    <div class="shell topbarInner">
      <div class="brand"><div class="brandMark">R</div><div class="brandText"><b>ROBERTA</b><span>VERIFIED ON-CHAIN INTELLIGENCE</span></div></div>
      <nav class="nav"><button data-scroll="about">About</button><button data-scroll="help">What she can do</button><button data-scroll="trust">Why ROBERTA</button></nav>
      <div class="actions"><button class="btn" id="agentEntryTop">Agent Access</button><button class="btn primary" id="humanEntryTop">Open ROBERTA</button></div>
    </div>
  </header>

  <main>
    <section id="about" class="hero">
      <div class="heroAura"></div>
      <div class="shell heroInner">
        <div class="eyebrow">Verified On-Chain Intelligence</div>
        <h1><span>ROBERTA</span></h1>
        <p class="heroTag">Ask ROBERTA anything about X1.</p>
        <p class="heroLead">She will investigate it, explain what she found, and tell you what she thinks. Ask about tokens, wallets, liquidity, trades, burns, bridges, risk, or activity without learning a technical tool first.</p>

        <div class="askBox">
          <textarea id="landingAsk" rows="2" placeholder="Ask ROBERTA anything…"></textarea>
          <button id="landingSend" class="btn primary">Ask ROBERTA →</button>
        </div>

        <div class="heroExamples">
          <button class="heroExample" data-ask-now="Should I buy $500 of AGI?">Should I buy $500 of AGI?</button>
          <button class="heroExample" data-ask-now="What happened to this wallet?">What happened to this wallet?</button>
          <button class="heroExample" data-ask-now="Compare XNT and AGI.">Compare XNT and AGI.</button>
          <button class="heroExample" data-ask-now="Why did this token price move?">Why did this token price move?</button>
          <button class="heroExample" data-ask-now="Trace this transaction.">Trace this transaction.</button>
          <button class="heroExample" data-ask-now="Show me the safest liquid tokens on X1.">Show me the safest liquid tokens on X1.</button>
        </div>

        <div class="heroFoot"><span><b>Normal questions</b> instead of commands</span><span><b>Verified facts</b> separated from judgment</span><span><b>Read-only</b> analysis and recommendations</span></div>
      </div>
    </section>

    <section id="help" class="section alt">
      <div class="shell">
        <div class="sectionHead">
          <div><div class="kicker">What can ROBERTA help with?</div><h2>The technical complexity stays underneath.</h2></div>
          <p>You can simply describe what you want to know. These categories are examples, not required modes.</p>
        </div>
        <div class="helpGrid">
          <article class="helpCard"><h3>Tokens</h3><p>Price, liquidity, volume, token activity, recent changes, and other verified facts.</p><button data-ask-now="Check AGI and tell me what matters right now.">Example: Check AGI →</button></article>
          <article class="helpCard"><h3>Trades</h3><p>Check a trade before you make it and understand possible market impact.</p><button data-ask-now="Should I buy $500 of AGI right now?">Example: Check a $500 buy →</button></article>
          <article class="helpCard"><h3>Wallets</h3><p>Investigate public wallet activity, recent transactions, and related transfers.</p><button data-ask-now="Investigate this wallet and explain its recent activity.">Example: Investigate a wallet →</button></article>
          <article class="helpCard"><h3>Compare</h3><p>Compare tokens, liquidity, activity, risk, or other supported evidence.</p><button data-ask-now="Compare XNT and AGI and tell me which looks stronger.">Example: Compare XNT and AGI →</button></article>
          <article class="helpCard"><h3>Market</h3><p>Find unusual activity, large trades, market changes, and verified price-impact evidence.</p><button data-ask-now="Show me important recent market activity on X1.">Example: Find unusual activity →</button></article>
          <article class="helpCard"><h3>Investigations</h3><p>Trace transactions, burns, bridges, movement of funds, and supported historical changes.</p><button data-ask-now="Trace this transaction and explain where the tokens went.">Example: Trace a transaction →</button></article>
        </div>
      </div>
    </section>

    <section id="trust" class="section">
      <div class="shell">
        <div class="sectionHead">
          <div><div class="kicker">Why ROBERTA</div><h2>Here is what happened, why it matters, and what she thinks.</h2></div>
          <p>Evidence stays inspectable, but the center of the product remains a normal conversation rather than a blockchain dashboard.</p>
        </div>
        <div class="trustGrid">
          <article class="trustCard"><i>✓</i><h3>Facts stay facts</h3><p>Verified facts, ROBERTA's assessment, uncertainty, and confidence are presented as different things instead of being blended together.</p></article>
          <article class="trustCard"><i>◎</i><h3>Clear judgment</h3><p>When you ask for a decision, ROBERTA can give a clear recommendation, explain why, show counterevidence, and state what would change her mind.</p></article>
          <article class="trustCard"><i>↗</i><h3>You remain in control</h3><p>ROBERTA can analyze and recommend. This website does not sign, broadcast, move funds, or execute trades.</p></article>
        </div>
      </div>
    </section>
  </main>

  <footer class="footer"><div class="shell footerInner"><span>ROBERTA — Verified On-Chain Intelligence</span><span>Conversation first. Evidence available when you want to inspect it.</span></div></footer>
</div>

<section id="workspace" aria-label="ROBERTA workspace">
  <div class="workspaceGrid">
    <aside class="sidebar">
      <div class="workspaceBrand"><div class="workspaceMark">R</div><div><b>ROBERTA</b><span>Verified On-Chain Intelligence</span></div></div>
      <button class="btn primary" id="newChat">+ New Chat</button>

      <div class="sidebarTitle">Chat history</div>
      <div id="historyList" class="historyList"></div>
      <button class="sideLink" id="clearHistory">Clear chat history</button>

      <div class="sidebarTitle">Saved investigations</div>
      <div id="savedList" class="savedList"></div>

      <div class="sidebarTitle">
        <button class="servicesToggle" id="servicesToggle"><span>Services</span><span id="servicesChevron">−</span></button>
      </div>
      <div id="sideServices" class="sideServices">
        <button class="sideService" data-fill="Check this token and tell me what matters right now."><b>Tokens</b><span>Price, liquidity, activity, structure</span></button>
        <button class="sideService" data-fill="Check this trade before I make it and tell me the market impact."><b>Trades</b><span>Trade size and market impact</span></button>
        <button class="sideService" data-fill="Investigate this wallet and explain its recent activity."><b>Wallets</b><span>Activity and related transfers</span></button>
        <button class="sideService" data-fill="Compare these two assets and tell me the important differences."><b>Compare</b><span>Assets, liquidity, activity, risk</span></button>
        <button class="sideService" data-fill="Find unusual recent market activity and important large trades."><b>Market</b><span>Changes, large trades, unusual activity</span></button>
        <button class="sideService" data-fill="Trace this transaction and explain where the funds or tokens moved."><b>Investigations</b><span>Transactions, burns, bridges, flows</span></button>
      </div>

      <button class="sideLink backAbout" id="backAbout">← About ROBERTA</button>
    </aside>

    <div class="workspaceMain">
      <header class="workspaceHeader">
        <div class="workspaceHeading"><b>ROBERTA</b><span>The center stays a conversation.</span></div>
        <div class="commandBar"><input id="commandInput" placeholder="Ask ROBERTA…"><button id="commandSend">Ask</button></div>
        <div class="workspaceHeaderActions">
          <div id="health" class="health">Checking ROBERTA</div>
          <button class="btn small" id="settingsBtn">Connection</button>
          <button class="btn small" id="clearChat">Clear</button>
        </div>
      </header>

      <div class="chatArea">
        <div id="messages" class="messages"></div>
        <div class="composer">
          <textarea id="composer" rows="4" placeholder="Ask a follow-up, or ask ROBERTA something new…"></textarea>
          <button class="btn primary" id="send">Send</button>
        </div>
        <div class="boundary">Analysis and recommendations only. ROBERTA does not execute transactions from this website.</div>
      </div>
    </div>

    <aside id="inspector" class="inspector">
      <div class="inspectorTitle">
        <div><b>Evidence &amp; details</b><span>Optional — conversation remains primary</span></div>
        <button class="btn icon small" id="inspectorToggle" aria-label="Collapse evidence panel">›</button>
      </div>
      <div class="inspectorContent">
        <div class="inspectorBlock">
          <h4>Current answer</h4>
          <div id="inspectorSummary" class="inspectorNote">Ask ROBERTA a question. Evidence, confidence, and useful follow-ups will appear here when available.</div>
        </div>
        <div class="inspectorBlock">
          <h4>Answer labels</h4>
          <div id="detailChips" class="detailChips"><span class="detailChip">Evidence</span><span class="detailChip">Risk</span><span class="detailChip">Freshness</span><span class="detailChip">Opinion</span></div>
        </div>
        <div class="inspectorBlock">
          <h4>Selected on-chain identifier</h4>
          <div id="entityDetail" class="inspectorNote">Click a wallet, transaction, pool, program, or other long on-chain identifier in an answer to investigate it.</div>
        </div>
        <div class="inspectorBlock">
          <h4>Investigate further</h4>
          <div class="inspectorActions">
            <button data-followup="evidence">View evidence behind the answer</button>
            <button data-followup="simple">Explain this simply</button>
            <button data-followup="technical">Show technical detail</button>
            <button data-followup="chart">Show a useful chart if verified data supports one</button>
            <button data-followup="recheck">Recheck with current data</button>
          </div>
        </div>
        <div class="inspectorBlock">
          <h4>Sources &amp; charts</h4>
          <div class="inspectorNote">ROBERTA only exposes source detail or chart-ready evidence when the underlying answer supports it. The interface does not invent missing sources or time-series data.</div>
        </div>
      </div>
    </aside>
  </div>
</section>

<div id="settings" class="settings">
  <h3>ROBERTA Connection</h3>
  <div class="field"><label>ROBERTA bridge URL</label><input id="apiBase" placeholder="Same origin"></div>
  <div class="field"><label>Bearer token (if configured)</label><input id="apiKey" type="password" autocomplete="off" placeholder="ROBERTA_API_KEY"></div>
  <div class="agentBox"><b>Agent endpoint</b><code>POST /v1/roberta {"message":"..."}</code></div>
  <div class="settingNote">Connection values stay in this browser tab only. Default loopback use requires no token.</div>
</div>

<script>
(function(){
'use strict';

var HISTORY_KEY='robertaChatHistoryV3';
var SAVED_KEY='robertaSavedInvestigationsV1';
var HISTORY_LIMIT=80;
var currentChatId=null;
var currentEntity='';
var sending=false;
var $=function(s){return document.querySelector(s)};

function apiBase(){return($('#apiBase').value||'').trim().replace(/\/$/,'')}
function apiUrl(path){return apiBase()?apiBase()+path:path}
function apiHeaders(){var h={'Content-Type':'application/json'},k=$('#apiKey').value.trim();if(k)h.Authorization='Bearer '+k;return h}

function enterWorkspace(mode){
  document.body.classList.add('workspaceMode');
  sessionStorage.setItem('robertaWorkspaceMode',mode||'human');
  if(mode==='agent')$('#settings').classList.add('open');
  setTimeout(function(){$('#composer').focus()},25);
}
function leaveWorkspace(){
  document.body.classList.remove('workspaceMode');
  sessionStorage.removeItem('robertaWorkspaceMode');
  $('#settings').classList.remove('open');
  window.scrollTo({top:0,behavior:'smooth'});
}
function askFromLanding(text){
  text=(text||'').trim();if(!text)return;
  enterWorkspace('human');
  send(text);
}

function escapeHtml(text){return String(text==null?'':text).replace(/[&<>"']/g,function(ch){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]})}
function statusClass(v){
  v=String(v||'').toLowerCase().replace(/[^a-z]/g,'');
  if(['pass','verified','ok','clear','available','strong','high'].indexOf(v)>=0)return'good';
  if(['warn','partial','watch','caution','moderate','medium'].indexOf(v)>=0)return'warn';
  if(['block','error','unverified','unavailable','notverified','weak','limited'].indexOf(v)>=0)return'bad';
  return'';
}
function formatAssistant(text){
  var lines=String(text||'').split('\n'),out=[];
  lines.forEach(function(line){
    var trim=line.trim(),safe=escapeHtml(line);
    if(/^(ROBERTA['’]S ANSWER|Why|What I found|What could change my mind|What would change my mind|You may also want to ask)\s*:??$/i.test(trim)){
      out.push('<span class="msgTitle">'+safe.replace(/:$/,'')+'</span>');return;
    }
    if(/^(My recommendation|My view|ROBERTA['’]s assessment)\s*:/i.test(trim)){
      var p=safe.split(':'),label=p.shift();out.push('<span class="opinionLine"><strong>'+label+':</strong>'+(p.length?' '+p.join(':'):'')+'</span>');return;
    }
    if(/^(Verified fact|What I found)\s*:/i.test(trim)){
      var fp=safe.split(':'),fl=fp.shift();out.push('<span class="factLine"><strong>'+fl+':</strong>'+(fp.length?' '+fp.join(':'):'')+'</span>');return;
    }
    if(/^(Uncertain|Unknown)\s*:/i.test(trim)){
      var up=safe.split(':'),ul=up.shift();out.push('<span class="uncertainLine"><strong>'+ul+':</strong>'+(up.length?' '+up.join(':'):'')+'</span>');return;
    }
    if(/^(Confidence|Conviction|Evidence quality)\s*:/i.test(trim)){
      var cp=safe.split(':'),cl=cp.shift();out.push('<span class="confidenceLine"><strong>'+cl+':</strong>'+(cp.length?' '+cp.join(':'):'')+'</span>');return;
    }
    if(/^\s*[A-Z][A-Z0-9 &?\/—-]{2,}:?\s*$/.test(trim)){out.push('<span class="msgTitle">'+safe.replace(/:$/,'')+'</span>');return}
    safe=safe.replace(/\b([1-9A-HJ-NP-Za-km-z]{32,90})\b/g,'<button class="entityLink" data-entity="$1">$1</button>');
    safe=safe.replace(/\b(PASS|WARN|BLOCK|PARTIAL|VERIFIED|UNVERIFIED|UNAVAILABLE|NOT VERIFIED|WATCH|CLEAR|CAUTION|ERROR|AVAILABLE|STRONG|MODERATE|WEAK|HIGH|LIMITED)\b/g,function(m){return'<span class="statusToken '+statusClass(m)+'">'+m+'</span>'});
    safe=safe.replace(/(^|[\s(])([+]\d[\d,]*(?:\.\d+)?%?)(?=$|[\s),.;])/g,'$1<span class="pos">$2</span>');
    safe=safe.replace(/(^|[\s(])(-\d[\d,]*(?:\.\d+)?%?)(?=$|[\s),.;])/g,'$1<span class="neg">$2</span>');
    out.push(safe);
  });
  return out.join('\n');
}
function answerActions(chatId){
  return '<div class="answerActions">'+
    '<button data-followup="evidence">Evidence</button>'+
    '<button data-followup="simple">Explain Simply</button>'+
    '<button data-followup="technical">Technical Detail</button>'+
    '<button data-followup="chart">Chart</button>'+
    '<button data-followup="compare">Compare Token</button>'+
    '<button data-followup="wallet">Check Wallet</button>'+
    '<button data-save-chat="'+escapeHtml(chatId||'')+'">Save Investigation</button>'+
    '</div>';
}
function addMessage(role,text,chatId){
  var wrap=document.createElement('div');wrap.className='msgWrap '+role;
  var d=document.createElement('div');d.className='msg '+role;
  if(role==='assistant')d.innerHTML=formatAssistant(text);else d.textContent=text;
  wrap.appendChild(d);
  if(role==='assistant')wrap.insertAdjacentHTML('beforeend',answerActions(chatId));
  $('#messages').appendChild(wrap);$('#messages').scrollTop=$('#messages').scrollHeight;return wrap;
}
function renderEmpty(){
  $('#messages').innerHTML='<div class="emptyState"><h2>What do you want to know?</h2><p>Start an investigation or just ask ROBERTA in your own words.</p><div class="emptyGrid">'+
  '<button data-fill="Analyze this token and tell me what matters right now.">Analyze a token</button>'+
  '<button data-fill="Check this trade before I make it.">Check a trade</button>'+
  '<button data-fill="Investigate this wallet and explain what it has been doing.">Investigate a wallet</button>'+
  '<button data-fill="Compare these two assets and tell me the important differences.">Compare two assets</button>'+
  '<button data-fill="Trace this transaction and explain where the funds or tokens moved.">Trace a transaction</button>'+
  '<button data-fill="Find unusual recent activity that matters.">Find unusual activity</button>'+
  '</div><div class="emptyHint">Or just ask ROBERTA in your own words.</div></div>';
}
function renderChat(messages,chatId){
  $('#messages').innerHTML='';
  if(!Array.isArray(messages)||!messages.length){renderEmpty();updateInspector('');return}
  messages.forEach(function(m){if(m&&m.role&&typeof m.text==='string')addMessage(m.role,m.text,chatId)});
  var last=[].concat(messages).reverse().find(function(m){return m&&m.role==='assistant'});if(last)updateInspector(last.text);
}

function loadHistory(){try{var raw=localStorage.getItem(HISTORY_KEY),v=raw?JSON.parse(raw):[];return Array.isArray(v)?v:[]}catch(e){return[]}}
function saveHistory(items){try{localStorage.setItem(HISTORY_KEY,JSON.stringify(items.slice(0,HISTORY_LIMIT)))}catch(e){}}
function loadSaved(){try{var raw=localStorage.getItem(SAVED_KEY),v=raw?JSON.parse(raw):[];return Array.isArray(v)?v:[]}catch(e){return[]}}
function saveSaved(items){try{localStorage.setItem(SAVED_KEY,JSON.stringify(items.slice(0,40)))}catch(e){}}
function titleFor(text){var t=String(text||'').replace(/\s+/g,' ').trim();return t.length>54?t.slice(0,51)+'…':t||'Untitled investigation'}
function renderHistory(){
  var list=$('#historyList'),items=loadHistory();
  if(!items.length){list.innerHTML='<div style="color:#667294;font-size:8px;padding:5px">No chats yet.</div>';return}
  var today=new Date().toDateString(),groups={Today:[],Previous:[]};
  items.forEach(function(item){var d=item.createdAt?new Date(item.createdAt):null;groups[d&&d.toDateString()===today?'Today':'Previous'].push(item)});
  list.innerHTML=['Today','Previous'].map(function(name){
    if(!groups[name].length)return'';
    return'<div class="historyGroup">'+name+'</div>'+groups[name].map(function(item){
      var when=item.createdAt?new Date(item.createdAt).toLocaleString():'';
      return'<button class="historyItem" data-chat-id="'+escapeHtml(item.id)+'"><b>'+escapeHtml(item.title)+'</b><span>'+escapeHtml(when)+'</span></button>';
    }).join('');
  }).join('');
}
function renderSaved(){
  var list=$('#savedList'),saved=loadSaved(),history=loadHistory();
  if(!saved.length){list.innerHTML='<div style="color:#667294;font-size:8px;padding:5px">Nothing saved yet.</div>';return}
  list.innerHTML=saved.map(function(s){
    var item=history.find(function(h){return h.id===s.id}),title=item?item.title:(s.title||'Saved investigation');
    return'<div class="savedRow"><button class="savedItem" data-chat-id="'+escapeHtml(s.id)+'"><b>'+escapeHtml(title)+'</b><span>'+escapeHtml(s.savedAt?new Date(s.savedAt).toLocaleDateString():'Saved')+'</span></button><button class="recheckBtn" title="Recheck with current data" data-recheck-chat="'+escapeHtml(s.id)+'">↻</button></div>';
  }).join('');
}
function beginRecord(userText){
  var items=loadHistory(),item=currentChatId?items.find(function(x){return x.id===currentChatId}):null;
  if(!item){currentChatId='chat-'+Date.now()+'-'+Math.random().toString(36).slice(2,8);item={id:currentChatId,title:titleFor(userText),createdAt:new Date().toISOString(),messages:[]};items.unshift(item)}
  item.messages.push({role:'user',text:userText});saveHistory(items);renderHistory();return currentChatId;
}
function appendRecord(id,role,text){
  var items=loadHistory(),item=items.find(function(x){return x.id===id});if(!item)return;
  item.messages.push({role:role,text:text});saveHistory(items);renderHistory();
}
function openSaved(id){
  var item=loadHistory().find(function(x){return x.id===id});if(!item)return;
  currentChatId=id;renderChat(item.messages,id);enterWorkspace('human');
}
function newChat(){currentChatId=null;renderEmpty();$('#composer').value='';$('#commandInput').value='';updateInspector('');$('#composer').focus()}
function clearCurrent(){currentChatId=null;renderEmpty();$('#composer').value='';$('#commandInput').value='';updateInspector('')}
function clearHistory(){saveHistory([]);saveSaved([]);currentChatId=null;renderHistory();renderSaved();renderEmpty();updateInspector('')}
function restoreLatest(){var items=loadHistory();if(items.length){currentChatId=items[0].id;renderChat(items[0].messages,currentChatId)}else renderEmpty()}
function saveInvestigation(id){
  id=id||currentChatId;if(!id)return;
  var history=loadHistory(),item=history.find(function(h){return h.id===id});if(!item)return;
  var saved=loadSaved().filter(function(s){return s.id!==id});saved.unshift({id:id,title:item.title,savedAt:new Date().toISOString()});saveSaved(saved);renderSaved();
}

function extractField(text,label){
  var re=new RegExp('^'+label+'\\s*:\\s*(.+)$','im'),m=String(text||'').match(re);return m?m[1].trim():'';
}
function updateInspector(text){
  if(!text){$('#inspectorSummary').textContent='Ask ROBERTA a question. Evidence, confidence, and useful follow-ups will appear here when available.';$('#detailChips').innerHTML='<span class="detailChip">Evidence</span><span class="detailChip">Risk</span><span class="detailChip">Freshness</span><span class="detailChip">Opinion</span>';return}
  var rec=extractField(text,'My recommendation')||extractField(text,"ROBERTA['’]s assessment");
  var conf=extractField(text,'Confidence')||extractField(text,'Conviction');
  var ev=extractField(text,'Evidence quality');
  var risk=extractField(text,'Risk');
  var fresh=extractField(text,'Freshness');
  var summary=[];
  if(rec)summary.push('View: '+rec);if(conf)summary.push('Confidence: '+conf);if(ev)summary.push('Evidence: '+ev);if(risk)summary.push('Risk: '+risk);if(fresh)summary.push('Freshness: '+fresh);
  $('#inspectorSummary').textContent=summary.length?summary.join(' · '):'ROBERTA answered. Use the actions below to inspect evidence, request simpler wording, technical detail, or a chart when supported.';
  var chips=[];
  [['Evidence',ev],['Risk',risk],['Freshness',fresh],['Opinion',rec],['Confidence',conf]].forEach(function(x){
    var cls=statusClass(x[1]);chips.push('<span class="detailChip '+cls+'">'+escapeHtml(x[0]+(x[1]?': '+x[1]:''))+'</span>');
  });
  $('#detailChips').innerHTML=chips.join('');
}

function openEntity(value){
  currentEntity=value;$('#entityDetail').innerHTML='<div class="entityDetail">'+escapeHtml(value)+'</div><div class="inspectorActions" style="margin-top:8px"><button data-entity-action="investigate">Investigate this identifier</button><button data-entity-action="trace">Trace related activity</button><button data-entity-action="recent">Show recent transactions/activity</button></div>';
  $('#inspector').classList.remove('collapsed');
}
function followupPrompt(kind){
  var map={
    evidence:'Show me the evidence behind your previous answer. Separate verified facts, uncertainty, freshness, sources, and any material limitations. Keep the explanation human-readable.',
    simple:'Explain your previous answer much more simply, as if I am a normal crypto holder who does not want technical implementation details.',
    technical:'Show the technical detail behind your previous answer, including the relevant evidence scope, calculations, limitations, and on-chain identifiers where supported.',
    chart:'If verified time-series or ordered transaction data supports it, show me the most useful chart for your previous answer and explain the important markers. Do not invent chart data if it is unavailable.',
    compare:'Based on the asset in your previous answer, suggest a useful comparison and compare it with the most relevant other supported asset. Ask me for the second asset if it cannot be inferred safely.',
    wallet:'If a public wallet or transaction is relevant to your previous answer, investigate its supported on-chain activity. Do not infer real-world identity.',
    recheck:'Recheck this investigation using current verified data. Compare the current result with what you previously told me and call out meaningful changes only.'
  };return map[kind]||'Continue investigating the previous answer.';
}
function sendFollowup(kind){send(followupPrompt(kind))}
function sendEntityAction(kind){
  if(!currentEntity)return;
  var p=kind==='trace'?'Trace the on-chain activity related to this identifier: '+currentEntity+'. Explain the path and limitations.':
        kind==='recent'?'Show recent verified transactions or activity for this on-chain identifier: '+currentEntity+'.':
        'Investigate this on-chain identifier and tell me what it is, what it has been doing, and what can be verified: '+currentEntity+'.';
  send(p);
}

function startInvestigation(){
  var box=document.createElement('div');box.className='investigating';
  box.innerHTML='<b>ROBERTA is investigating…</b><div class="investigateStep active">Routing your question</div><div class="investigateStep">Checking available verified evidence</div><div class="investigateStep">Reviewing relevant activity and history</div><div class="investigateStep">Preparing a clear answer</div>';
  $('#messages').appendChild(box);$('#messages').scrollTop=$('#messages').scrollHeight;
  var idx=0,steps=box.querySelectorAll('.investigateStep');
  var timer=setInterval(function(){if(idx<steps.length){steps[idx].classList.remove('active');steps[idx].classList.add('done');idx++;if(idx<steps.length)steps[idx].classList.add('active')}},800);
  return{el:box,timer:timer};
}
function stopInvestigation(state){if(!state)return;clearInterval(state.timer);if(state.el&&state.el.parentNode)state.el.remove()}

function busy(v){sending=v;$('#send').disabled=v;$('#commandSend').disabled=v;$('#send').textContent=v?'Working…':'Send';$('#commandSend').textContent=v?'…':'Ask'}
async function health(){
  var h=$('#health');
  try{var r=await fetch(apiUrl('/healthz')),d=await r.json();if(r.ok&&d.status==='ok'){h.className='health online';h.textContent='ROBERTA online';return}throw 0}
  catch(e){h.className='health offline';h.textContent='ROBERTA offline'}
}
async function send(text){
  text=(text||'').trim();if(!text||sending)return;
  enterWorkspace('human');
  var chatId=beginRecord(text);
  addMessage('user',text,chatId);
  $('#composer').value='';$('#commandInput').value='';busy(true);
  var progress=startInvestigation();
  try{
    var r=await fetch(apiUrl('/v1/roberta'),{method:'POST',headers:apiHeaders(),body:JSON.stringify({message:text,thread_id:chatId})});
    var d=await r.json().catch(function(){return{}});
    stopInvestigation(progress);
    var reply=!r.ok?((d.error&&d.error.message)||('Request failed ('+r.status+')')):(d.reply||'ROBERTA returned no reply.');
    addMessage('assistant',reply,chatId);appendRecord(chatId,'assistant',reply);updateInspector(reply);
  }catch(e){
    stopInvestigation(progress);
    var reply='I could not reach the ROBERTA bridge. Verify that it is running and check Connection settings.';
    addMessage('assistant',reply,chatId);appendRecord(chatId,'assistant',reply);updateInspector(reply);
  }finally{busy(false);health()}
}

document.addEventListener('click',function(e){
  var sc=e.target.closest('[data-scroll]');if(sc){var target=document.getElementById(sc.dataset.scroll);if(target)target.scrollIntoView({behavior:'smooth'})}
  var now=e.target.closest('[data-ask-now]');if(now)askFromLanding(now.dataset.askNow);
  var fill=e.target.closest('[data-fill]');if(fill){enterWorkspace('human');$('#composer').value=fill.dataset.fill;$('#composer').focus()}
  var hi=e.target.closest('[data-chat-id]');if(hi)openSaved(hi.dataset.chatId);
  var fu=e.target.closest('[data-followup]');if(fu)sendFollowup(fu.dataset.followup);
  var save=e.target.closest('[data-save-chat]');if(save)saveInvestigation(save.dataset.saveChat);
  var recheck=e.target.closest('[data-recheck-chat]');if(recheck){openSaved(recheck.dataset.recheckChat);setTimeout(function(){sendFollowup('recheck')},60)}
  var ent=e.target.closest('[data-entity]');if(ent)openEntity(ent.dataset.entity);
  var ea=e.target.closest('[data-entity-action]');if(ea)sendEntityAction(ea.dataset.entityAction);
});
$('#landingSend').onclick=function(){askFromLanding($('#landingAsk').value)};
$('#landingAsk').addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();askFromLanding(this.value)}});
$('#humanEntryTop').onclick=function(){enterWorkspace('human')};
$('#agentEntryTop').onclick=function(){enterWorkspace('agent')};
$('#backAbout').onclick=leaveWorkspace;
$('#newChat').onclick=newChat;$('#clearChat').onclick=clearCurrent;$('#clearHistory').onclick=clearHistory;
$('#settingsBtn').onclick=function(){$('#settings').classList.toggle('open')};
$('#inspectorToggle').onclick=function(){$('#inspector').classList.toggle('collapsed');this.textContent=$('#inspector').classList.contains('collapsed')?'‹':'›'};
$('#servicesToggle').onclick=function(){$('#sideServices').classList.toggle('closed');$('#servicesChevron').textContent=$('#sideServices').classList.contains('closed')?'+':'−'};
$('#send').onclick=function(){send($('#composer').value)};
$('#composer').addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(this.value)}});
$('#commandSend').onclick=function(){send($('#commandInput').value)};
$('#commandInput').addEventListener('keydown',function(e){if(e.key==='Enter'){e.preventDefault();send(this.value)}});
$('#apiBase').value=sessionStorage.getItem('robertaApiBase')||'';$('#apiKey').value=sessionStorage.getItem('robertaApiKey')||'';
$('#apiBase').onchange=function(){sessionStorage.setItem('robertaApiBase',this.value.trim());health()};
$('#apiKey').onchange=function(){sessionStorage.setItem('robertaApiKey',this.value)};
document.addEventListener('keydown',function(e){if(e.key==='Escape')$('#settings').classList.remove('open')});

renderHistory();renderSaved();restoreLatest();health();setInterval(health,30000);
var mode=sessionStorage.getItem('robertaWorkspaceMode');if(mode)enterWorkspace(mode);
})();
</script>
</body>
</html>'''


def web_ui_bytes() -> bytes:
    return ROBERTA_WEB_UI_HTML.encode("utf-8")


__all__ = ["ROBERTA_WEB_UI_HTML", "web_ui_bytes"]
