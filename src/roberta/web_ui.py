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
  --bg:#050712;--bg2:#080c1d;--panel:#0b1024;--panel2:#10172f;--line:rgba(132,155,255,.18);
  --text:#f7f8ff;--muted:#98a4c8;--blue:#55b7ff;--violet:#8c5cff;--cyan:#5ae5ff;--green:#75e0aa;
  --amber:#ffd27f;--red:#ff8b98;--shadow:0 26px 90px rgba(0,0,0,.38);--radius:26px;
}
*{box-sizing:border-box}
html{scroll-behavior:smooth;background:var(--bg)}
body{margin:0;color:var(--text);background:
  radial-gradient(circle at 18% 8%,rgba(68,91,218,.18),transparent 24%),
  radial-gradient(circle at 82% 10%,rgba(132,68,218,.12),transparent 20%),
  linear-gradient(180deg,var(--bg),#060919 48%,#040610);
  font:15px/1.55 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
body:before{content:"";position:fixed;inset:0;z-index:-1;pointer-events:none;background-image:
  linear-gradient(rgba(105,128,240,.028) 1px,transparent 1px),
  linear-gradient(90deg,rgba(105,128,240,.028) 1px,transparent 1px);
  background-size:68px 68px;mask-image:linear-gradient(to bottom,#000,transparent 84%)}
button,input,textarea{font:inherit}
button{cursor:pointer}
a{color:inherit}
.shell{width:min(1180px,calc(100% - 36px));margin:auto}
.hidden{display:none!important}

.topbar{position:sticky;top:0;z-index:40;background:rgba(5,7,18,.84);backdrop-filter:blur(22px);border-bottom:1px solid rgba(130,153,255,.12)}
.topbarInner{height:76px;display:flex;align-items:center;justify-content:space-between;gap:20px}
.brand{display:flex;align-items:center;gap:12px}
.brandMark,.workspaceMark{width:42px;height:42px;border-radius:12px;display:grid;place-items:center;font-weight:900;
  background:linear-gradient(145deg,#4aa8ff,#8159ff 62%,#b04cff);box-shadow:0 0 32px rgba(78,111,255,.28)}
.brandText b{display:block;letter-spacing:.28em;font-size:15px}
.brandText span{display:block;color:var(--muted);font-size:8px;letter-spacing:.13em;margin-top:3px}
.nav{display:flex;align-items:center;gap:4px}
.nav button{border:0;background:transparent;color:#c7cdef;padding:9px 12px;border-radius:999px;font-size:11px;letter-spacing:.08em;text-transform:uppercase}
.nav button:hover{background:rgba(103,129,255,.08);color:#fff}
.actions{display:flex;align-items:center;gap:8px}
.btn{border:1px solid var(--line);background:rgba(10,15,34,.78);color:var(--text);padding:10px 15px;border-radius:999px;font-weight:800}
.btn:hover{border-color:rgba(85,183,255,.48);box-shadow:0 10px 30px rgba(67,88,206,.14)}
.btn.primary{border-color:transparent;background:linear-gradient(100deg,#327fff,#6d58ff 52%,#a546ff);box-shadow:0 0 30px rgba(79,88,255,.25)}
.btn.ghost{background:transparent}
.btn.small{padding:7px 10px;font-size:10px}

.hero{min-height:calc(100vh - 76px);display:flex;align-items:center;position:relative;overflow:hidden;padding:54px 0}
.heroGrid{position:absolute;inset:0;pointer-events:none;background:
 radial-gradient(circle at 66% 48%,rgba(53,85,211,.16),transparent 29%),
 radial-gradient(circle at 78% 42%,rgba(135,62,219,.12),transparent 24%)}
.heroLayout{position:relative;z-index:1;display:grid;grid-template-columns:1.02fr .98fr;gap:48px;align-items:center}
.eyebrow{display:inline-flex;align-items:center;gap:8px;border:1px solid rgba(104,151,255,.24);background:rgba(11,18,44,.72);
  color:#a9cfff;border-radius:999px;padding:7px 11px;font-size:9px;font-weight:900;letter-spacing:.14em;text-transform:uppercase}
.eyebrow:before{content:"✦";color:var(--cyan)}
.hero h1{font-size:clamp(58px,8vw,104px);line-height:.9;letter-spacing:-.065em;margin:24px 0 20px}
.hero h1 span{background:linear-gradient(90deg,#eef5ff,#67c8ff 40%,#9566ff 76%,#e3a7ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.heroTag{font-size:clamp(20px,2.2vw,31px);line-height:1.18;letter-spacing:-.03em;margin:0 0 16px;max-width:700px}
.heroLead{color:var(--muted);font-size:16px;max-width:680px;margin:0}
.heroButtons{display:flex;gap:10px;flex-wrap:wrap;margin-top:28px}
.heroPrinciples{display:flex;gap:12px;flex-wrap:wrap;margin-top:26px}
.heroPrinciples span{border:1px solid rgba(127,151,255,.13);background:rgba(9,13,32,.66);border-radius:999px;padding:7px 10px;color:#9aa6ca;font-size:9px}
.heroPrinciples b{color:#e8edff}

.orbital{position:relative;min-height:560px;display:grid;place-items:center}
.orbital:before{content:"";position:absolute;width:430px;height:430px;border-radius:50%;background:radial-gradient(circle,rgba(67,123,255,.18),rgba(104,63,208,.08) 46%,transparent 70%);filter:blur(4px)}
.orbitRing{position:absolute;border:1px solid rgba(107,132,255,.17);border-radius:50%}
.r1{width:320px;height:320px;animation:spin 22s linear infinite}
.r2{width:430px;height:430px;animation:spinReverse 30s linear infinite}
.r3{width:530px;height:530px;opacity:.5;animation:spin 44s linear infinite}
.core{position:relative;width:235px;height:235px;border-radius:50%;display:grid;place-items:center;background:
 radial-gradient(circle at 42% 34%,rgba(116,204,255,.42),transparent 20%),
 radial-gradient(circle at 60% 62%,rgba(131,73,255,.28),transparent 40%),
 rgba(8,13,34,.9);border:1px solid rgba(101,161,255,.35);box-shadow:0 0 70px rgba(56,88,255,.2)}
.core:before,.core:after{content:"";position:absolute;border-radius:50%;border:1px dashed rgba(103,176,255,.22)}
.core:before{inset:18px;animation:spin 18s linear infinite}.core:after{inset:43px;animation:spinReverse 14s linear infinite}
.coreLetter{font-size:68px;font-weight:900;background:linear-gradient(145deg,#88dcff,#a06bff);-webkit-background-clip:text;background-clip:text;color:transparent}
.node{position:absolute;min-width:112px;border:1px solid rgba(111,153,255,.21);background:rgba(8,13,32,.82);backdrop-filter:blur(12px);border-radius:16px;padding:9px 11px;box-shadow:0 15px 35px rgba(0,0,0,.25)}
.node b{display:block;font-size:9px;letter-spacing:.1em}.node span{display:block;color:#8290b8;font-size:8px;margin-top:2px}
.n1{left:4%;top:17%}.n2{right:0;top:24%}.n3{left:0;bottom:25%}.n4{right:5%;bottom:17%}.n5{left:40%;top:3%}.n6{left:40%;bottom:1%}
.liveFlag{position:absolute;bottom:46px;left:50%;transform:translateX(-50%);border:1px solid rgba(93,214,169,.2);background:rgba(11,28,27,.7);color:#95ecc1;border-radius:999px;padding:7px 10px;font-size:8px;letter-spacing:.12em;font-weight:900}
.liveFlag:before{content:"";display:inline-block;width:6px;height:6px;border-radius:50%;background:#66dfa8;margin-right:7px;box-shadow:0 0 0 5px rgba(102,223,168,.08)}
@keyframes spin{to{transform:rotate(360deg)}}@keyframes spinReverse{to{transform:rotate(-360deg)}}

.section{padding:92px 0}
.section.alt{background:rgba(9,13,31,.38);border-top:1px solid rgba(124,150,255,.08);border-bottom:1px solid rgba(124,150,255,.08)}
.sectionHead{display:grid;grid-template-columns:1fr .85fr;gap:32px;align-items:end;margin-bottom:34px}
.kicker{color:#6fc7ff;font-size:10px;letter-spacing:.15em;font-weight:900;text-transform:uppercase}
.sectionHead h2{font-size:clamp(36px,4.8vw,60px);line-height:1;letter-spacing:-.045em;margin:9px 0 0}
.sectionHead p{color:var(--muted);font-size:15px;margin:0}
.services{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:17px}
.service{border:1px solid rgba(126,151,255,.17);background:linear-gradient(180deg,rgba(11,17,40,.94),rgba(7,11,27,.95));border-radius:24px;padding:22px;min-height:340px;display:flex;flex-direction:column;box-shadow:0 18px 50px rgba(0,0,0,.17)}
.service:hover{transform:translateY(-3px);border-color:rgba(85,183,255,.38);transition:.18s}
.service.featured{border-color:rgba(86,191,255,.38);box-shadow:0 22px 55px rgba(58,80,221,.12)}
.serviceIcon{width:46px;height:46px;border-radius:14px;display:grid;place-items:center;background:linear-gradient(145deg,rgba(67,144,255,.18),rgba(144,74,255,.19));border:1px solid rgba(115,155,255,.2);font-size:18px}
.service h3{font-size:19px;margin:18px 0 8px}.service p{color:var(--muted);font-size:12.5px;margin:0 0 18px}
.examplesTitle{margin-top:auto;color:#7481aa;font-size:8px;letter-spacing:.12em;font-weight:900;text-transform:uppercase;margin-bottom:7px}
.example{width:100%;text-align:left;border:1px solid rgba(124,151,255,.13);background:rgba(8,13,31,.7);color:#c8d0ee;border-radius:12px;padding:8px 10px;margin-top:6px;font-size:10px}
.example:hover{background:rgba(17,25,55,.86);border-color:rgba(88,191,255,.38);color:#fff}

.trustGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.trustCard{border:1px solid rgba(126,151,255,.15);background:rgba(9,14,33,.78);border-radius:22px;padding:22px}
.trustCard i{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;font-style:normal;background:rgba(76,123,255,.13);color:#88d5ff}
.trustCard h3{font-size:16px;margin:16px 0 7px}.trustCard p{color:var(--muted);font-size:12px;margin:0}
.cta{border:1px solid rgba(112,146,255,.22);border-radius:34px;padding:48px;background:
 radial-gradient(circle at 82% 24%,rgba(137,70,255,.18),transparent 28%),
 radial-gradient(circle at 12% 70%,rgba(62,159,255,.13),transparent 32%),
 rgba(8,13,31,.88);display:grid;grid-template-columns:1fr auto;gap:26px;align-items:center}
.cta h2{font-size:clamp(31px,4vw,50px);line-height:1;letter-spacing:-.04em;margin:0 0 10px}
.cta p{color:var(--muted);margin:0}
.footer{padding:30px 0 44px;color:#6f7b9f;font-size:9px}
.footerInner{display:flex;justify-content:space-between;gap:18px;flex-wrap:wrap}

#workspace{display:none;min-height:100vh}
.workspaceMode #landing{display:none}
.workspaceMode #workspace{display:block}
.workspaceGrid{min-height:100vh;display:grid;grid-template-columns:290px minmax(0,1fr)}
.sidebar{position:sticky;top:0;height:100vh;overflow:auto;border-right:1px solid rgba(128,154,255,.13);background:rgba(5,9,23,.97);padding:20px 16px;display:flex;flex-direction:column}
.workspaceBrand{display:flex;align-items:center;gap:10px;padding:2px 2px 16px}
.workspaceBrand b{display:block;letter-spacing:.18em;font-size:13px}.workspaceBrand span{display:block;color:#7d89ad;font-size:8px;margin-top:2px}
.sidebarTitle{color:#69769d;font-size:8px;letter-spacing:.13em;font-weight:900;text-transform:uppercase;margin:18px 4px 7px}
.historyList{display:grid;gap:5px;max-height:29vh;overflow:auto}
.historyGroup{color:#637097;font-size:8px;text-transform:uppercase;letter-spacing:.12em;padding:6px 5px 2px}
.historyItem{border:1px solid rgba(123,148,255,.11);background:rgba(10,15,34,.64);color:#dce1f7;border-radius:12px;padding:8px 9px;text-align:left;width:100%}
.historyItem:hover{border-color:rgba(85,183,255,.3);background:rgba(15,22,49,.78)}
.historyItem b{display:block;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.historyItem span{display:block;color:#707c9f;font-size:8px;margin-top:2px}
.sideLink{border:0;background:transparent;color:#8390b7;text-align:left;padding:6px 3px;font-size:9px}.sideLink:hover{color:#fff}
.sideServices{display:grid;gap:6px}
.sideService{border:1px solid rgba(122,149,255,.11);background:rgba(9,14,32,.66);color:#e8ebfb;border-radius:12px;padding:9px 10px;text-align:left}
.sideService:hover{border-color:rgba(83,186,255,.33);background:rgba(16,23,50,.8)}
.sideService b{display:block;font-size:9.5px}.sideService span{display:block;color:#727fa5;font-size:8px;margin-top:2px}
.labelKey{display:flex;flex-wrap:wrap;gap:4px}
.labelKey span,.routeChip{border:1px solid rgba(126,151,255,.13);border-radius:999px;padding:4px 7px;color:#8592b8;font-size:7px}
.backAbout{margin-top:auto}

.workspaceMain{min-width:0;height:100vh;display:flex;flex-direction:column;background:
 radial-gradient(circle at 74% 0,rgba(71,80,200,.1),transparent 31%),#060918}
.workspaceHeader{min-height:72px;border-bottom:1px solid rgba(126,151,255,.12);display:flex;align-items:center;justify-content:space-between;gap:16px;padding:13px 20px;background:rgba(6,9,23,.82);backdrop-filter:blur(18px)}
.workspaceHeading b{display:block;letter-spacing:.15em;font-size:13px}.workspaceHeading span{display:block;color:#7d88aa;font-size:9px;margin-top:2px}
.workspaceHeaderActions{display:flex;align-items:center;gap:6px;flex-wrap:wrap;justify-content:flex-end}
.health{display:inline-flex;align-items:center;border:1px solid rgba(126,151,255,.13);border-radius:999px;padding:6px 9px;color:#8d99bd;font-size:8px}
.health:before{content:"";width:6px;height:6px;border-radius:50%;background:#8992a8;margin-right:6px}
.health.online{color:#8ce9ba;border-color:rgba(94,220,159,.2)}.health.online:before{background:#68dfa6;box-shadow:0 0 0 4px rgba(104,223,166,.08)}
.health.offline{color:#ff9aa4;border-color:rgba(255,118,132,.2)}.health.offline:before{background:#ff7e8d}
.chatArea{min-height:0;flex:1;display:flex;flex-direction:column;width:min(1050px,100%);margin:0 auto;padding:18px 24px 12px}
.messages{flex:1;min-height:0;overflow:auto;border:1px solid rgba(126,151,255,.11);border-bottom:0;border-radius:24px 24px 0 0;background:linear-gradient(180deg,rgba(8,12,28,.74),rgba(6,9,21,.92));padding:22px;display:flex;flex-direction:column;gap:13px}
.msg{max-width:88%;padding:13px 15px;border-radius:17px;white-space:pre-wrap;word-break:break-word}
.msg.user{align-self:flex-end;background:linear-gradient(105deg,#356ff1,#7157ef);color:#fff;border-bottom-right-radius:5px}
.msg.assistant{align-self:flex-start;background:rgba(12,18,40,.9);border:1px solid rgba(126,151,255,.13);color:#e6eafc;border-bottom-left-radius:5px}
.msg.system{align-self:center;color:#7480a3;font-size:9px;padding:4px}
.msgTitle{display:block;color:#fff;font-size:10px;font-weight:900;text-transform:uppercase;letter-spacing:.08em;margin:3px 0 5px}
.opinionLine{display:block;margin:3px 0}.opinionLine strong{color:#7fcfff}
.statusToken{display:inline-flex;align-items:center;padding:1px 6px;border-radius:999px;border:1px solid rgba(135,150,190,.18);background:rgba(120,135,170,.08);color:#aeb7d3;font-size:.88em;font-weight:900}
.statusToken.good{color:#7ce4ae;border-color:rgba(89,211,146,.22);background:rgba(49,140,93,.1)}
.statusToken.warn{color:#ffd27f;border-color:rgba(255,203,104,.2);background:rgba(156,111,26,.1)}
.statusToken.bad{color:#ff909d;border-color:rgba(255,118,132,.2);background:rgba(157,45,60,.1)}
.pos{color:#77e2ad;font-weight:900}.neg{color:#ff8f9a;font-weight:900}
.composer{border:1px solid rgba(126,151,255,.11);background:rgba(8,12,29,.94);border-radius:0 0 24px 24px;padding:13px;display:grid;grid-template-columns:1fr auto;gap:9px}
.composer textarea{resize:vertical;min-height:76px;max-height:180px;border:1px solid rgba(126,151,255,.15);background:#050817;color:#eef1ff;border-radius:16px;padding:13px 14px;outline:none}
.composer textarea:focus{border-color:rgba(79,185,255,.42)}
.boundary{text-align:center;color:#606b8d;font-size:8px;padding:8px 0 0}

.settings{display:none;position:fixed;z-index:90;right:20px;top:82px;width:min(390px,calc(100vw - 40px));background:#0b1024;border:1px solid rgba(126,151,255,.2);border-radius:22px;padding:18px;box-shadow:var(--shadow)}
.settings.open{display:block}.settings h3{margin:0 0 12px;font-size:16px}.field{display:grid;gap:5px;margin-top:10px}.field label{color:#8d98ba;font-size:9px}.field input{border:1px solid rgba(126,151,255,.16);background:#060918;color:#eef1ff;border-radius:12px;padding:10px 11px;outline:none}.settingNote{color:#6e7a9d;font-size:8px;margin-top:10px}
.agentBox{border:1px solid rgba(96,190,255,.17);background:rgba(9,20,38,.72);border-radius:14px;padding:11px;margin-top:12px}.agentBox b{font-size:9px}.agentBox code{display:block;color:#9bdcff;font-size:9px;margin-top:4px;word-break:break-all}

@media(max-width:980px){
  .nav{display:none}.heroLayout{grid-template-columns:1fr}.orbital{min-height:500px}.services{grid-template-columns:repeat(2,1fr)}
  .sectionHead{grid-template-columns:1fr}.trustGrid{grid-template-columns:1fr}.cta{grid-template-columns:1fr}.workspaceGrid{grid-template-columns:245px minmax(0,1fr)}
  .routeChip{display:none}
}
@media(max-width:720px){
  .shell{width:min(100% - 24px,1180px)}.topbarInner{height:68px}.brandText span{display:none}.hero{padding:44px 0}.hero h1{font-size:62px}
  .orbital{min-height:420px;transform:scale(.82);margin:-40px -40px}.services{grid-template-columns:1fr}.section{padding:66px 0}
  .workspaceGrid{display:block}.sidebar{position:relative;height:auto;max-height:none;border-right:0;border-bottom:1px solid rgba(126,151,255,.12)}
  .historyList{max-height:170px}.sideServices{grid-template-columns:repeat(2,1fr)}.backAbout{margin-top:12px}.workspaceMain{height:auto;min-height:100vh}
  .workspaceHeader{align-items:flex-start;flex-direction:column}.workspaceHeaderActions{justify-content:flex-start}.chatArea{min-height:74vh;padding:12px}.messages{min-height:54vh}
}
@media(max-width:480px){
  .actions .ghost{display:none}.heroButtons{display:grid}.heroButtons .btn{width:100%}.sideServices{grid-template-columns:1fr}.composer{grid-template-columns:1fr}.orbital{transform:scale(.68);margin:-80px -100px}
}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}.r1,.r2,.r3,.core:before,.core:after{animation:none!important}}
</style>
</head>
<body>
<div id="landing">
  <header class="topbar">
    <div class="shell topbarInner">
      <div class="brand">
        <div class="brandMark">R</div>
        <div class="brandText"><b>ROBERTA</b><span>VERIFIED ON-CHAIN INTELLIGENCE</span></div>
      </div>
      <nav class="nav">
        <button data-scroll="about">About</button>
        <button data-scroll="services">Services</button>
        <button data-scroll="trust">Why ROBERTA</button>
      </nav>
      <div class="actions">
        <button class="btn ghost" id="agentEntryTop">Agent Access</button>
        <button class="btn primary" id="humanEntryTop">Open ROBERTA</button>
      </div>
    </div>
  </header>

  <main>
    <section id="about" class="hero">
      <div class="heroGrid"></div>
      <div class="shell heroLayout">
        <div>
          <div class="eyebrow">Verified On-Chain Intelligence</div>
          <h1><span>ROBERTA</span></h1>
          <p class="heroTag">Ask about a token, trade, wallet, or market move.</p>
          <p class="heroLead">ROBERTA checks available blockchain evidence, explains what matters in plain English, and gives you a clear assessment. You do not need to know which blockchain tool to use.</p>
          <div class="heroButtons">
            <button class="btn primary" id="humanEntryHero">Enter Human Chat</button>
            <button class="btn" id="agentEntryHero">Agent / API Access</button>
          </div>
          <div class="heroPrinciples">
            <span><b>Ask naturally</b> — no commands required</span>
            <span><b>Evidence-aware</b> — unknowns stay visible</span>
            <span><b>Read-only</b> — you stay in control</span>
          </div>
        </div>

        <div class="orbital" aria-label="ROBERTA intelligence network">
          <div class="orbitRing r1"></div><div class="orbitRing r2"></div><div class="orbitRing r3"></div>
          <div class="core"><div class="coreLetter">R</div></div>
          <div class="node n1"><b>TOKENS</b><span>market + structure</span></div>
          <div class="node n2"><b>RISK</b><span>evidence-bounded</span></div>
          <div class="node n3"><b>WALLETS</b><span>public activity</span></div>
          <div class="node n4"><b>TRADES</b><span>pool impact</span></div>
          <div class="node n5"><b>HISTORY</b><span>what changed</span></div>
          <div class="node n6"><b>EVIDENCE</b><span>freshness + proof</span></div>
          <div class="liveFlag">ROBERTA INTELLIGENCE NETWORK</div>
        </div>
      </div>
    </section>

    <section id="services" class="section alt">
      <div class="shell">
        <div class="sectionHead">
          <div><div class="kicker">What you can ask</div><h2>Six simple ways to use ROBERTA.</h2></div>
          <p>Pick a service when you want an idea of what to ask. You can always skip the menu and type a normal question instead.</p>
        </div>
        <div class="services">
          <article class="service">
            <div class="serviceIcon">◈</div><h3>Check a Token</h3>
            <p>Get a quick health check covering market conditions, liquidity, activity, token details, recent changes, and available evidence.</p>
            <div class="examplesTitle">Try asking</div>
            <button class="example" data-example="Check AGI.">“Check AGI.”</button>
            <button class="example" data-example="How is XNT doing right now?">“How is XNT doing?”</button>
            <button class="example" data-example="What should I know about this token?">“What should I know about this token?”</button>
          </article>

          <article class="service">
            <div class="serviceIcon">⇄</div><h3>Compare Tokens</h3>
            <p>Compare two tokens side by side on liquidity, risk, market activity, history, structure, and other verified differences.</p>
            <div class="examplesTitle">Try asking</div>
            <button class="example" data-example="Which looks better right now, XNT or AGI?">“Which looks better, XNT or AGI?”</button>
            <button class="example" data-example="Which token has stronger liquidity, XNT or AGI?">“Which has stronger liquidity?”</button>
            <button class="example" data-example="Which is safer right now, XNT or AGI?">“Which is safer right now?”</button>
          </article>

          <article class="service">
            <div class="serviceIcon">↗</div><h3>Should I Buy or Sell?</h3>
            <p>Tell ROBERTA the trade you are considering. She checks the evidence and explains whether she thinks you should proceed, wait, reduce the size, or avoid it.</p>
            <div class="examplesTitle">Try asking</div>
            <button class="example" data-example="Should I buy $500 of AGI right now?">“Should I buy $500 of AGI?”</button>
            <button class="example" data-example="Should I sell 100,000 XNT right now?">“Should I sell 100,000 XNT?”</button>
            <button class="example" data-example="Would you make this trade?">“Would you make this trade?”</button>
          </article>

          <article class="service">
            <div class="serviceIcon">◇</div><h3>Check Risk</h3>
            <p>Look for thin liquidity, concentration, token controls, unusual activity, stale data, missing evidence, and trade-size problems.</p>
            <div class="examplesTitle">Try asking</div>
            <button class="example" data-example="Is AGI risky right now?">“Is this token risky?”</button>
            <button class="example" data-example="Could I get stuck trying to sell AGI?">“Could I get stuck selling?”</button>
            <button class="example" data-example="What worries you about AGI?">“What worries you about AGI?”</button>
          </article>

          <article class="service">
            <div class="serviceIcon">◎</div><h3>Track Wallets &amp; Big Trades</h3>
            <p>Understand verified public-wallet activity, important buys and sells, transaction timing, volume contribution, and pool-level price impact when supported by evidence.</p>
            <div class="examplesTitle">Try asking</div>
            <button class="example" data-example="Did a big wallet just buy AGI?">“Did a big wallet just buy AGI?”</button>
            <button class="example" data-example="Did this transaction move the pool price?">“Did this trade move the pool price?”</button>
            <button class="example" data-example="Where did these tokens go?">“Where did these tokens go?”</button>
          </article>

          <article class="service featured">
            <div class="serviceIcon">✦</div><h3>Ask ROBERTA</h3>
            <p>Ask your question normally. ROBERTA chooses the appropriate token, market, wallet, burn, history, bridge, risk, or evidence intelligence automatically.</p>
            <div class="examplesTitle">Try asking</div>
            <button class="example" data-example="What happened to AGI today?">“What happened to AGI today?”</button>
            <button class="example" data-example="Why did the price jump?">“Why did the price jump?”</button>
            <button class="example" data-example="How much XNT was burned this week?">“How much XNT was burned this week?”</button>
          </article>
        </div>
      </div>
    </section>

    <section id="trust" class="section">
      <div class="shell">
        <div class="sectionHead">
          <div><div class="kicker">Why ROBERTA</div><h2>Clear answers without hiding uncertainty.</h2></div>
          <p>ROBERTA is designed to give the useful conclusion first while keeping evidence quality, risk, freshness, and important unknowns separate.</p>
        </div>
        <div class="trustGrid">
          <article class="trustCard"><i>✓</i><h3>Checks the evidence</h3><p>Fresh accepted evidence wins over remembered values. Missing or conflicting information stays visible instead of being guessed.</p></article>
          <article class="trustCard"><i>◎</i><h3>Gives a clear opinion</h3><p>For decision questions, ROBERTA can tell you what she thinks, explain why, show the strongest counterevidence, and say what would change her mind.</p></article>
          <article class="trustCard"><i>↗</i><h3>You stay in control</h3><p>ROBERTA analyzes and recommends. She does not sign transactions, move funds, or execute trades from this website.</p></article>
        </div>
      </div>
    </section>

    <section class="section alt">
      <div class="shell">
        <div class="cta">
          <div><h2>Ask ROBERTA the way you would ask an analyst.</h2><p>No tool selection required. Start with the question you actually care about.</p></div>
          <button class="btn primary" id="humanEntryBottom">Open ROBERTA</button>
        </div>
      </div>
    </section>
  </main>

  <footer class="footer"><div class="shell footerInner"><span>ROBERTA — Verified On-Chain Intelligence</span><span>User / Agent → ROBERTA → Chain Scout → CMIS → verified provider/source</span></div></footer>
</div>

<section id="workspace" aria-label="ROBERTA chat workspace">
  <div class="workspaceGrid">
    <aside class="sidebar">
      <div class="workspaceBrand"><div class="workspaceMark">R</div><div><b>ROBERTA</b><span>Verified On-Chain Intelligence</span></div></div>
      <button class="btn primary" id="newChat">+ New Chat</button>

      <div class="sidebarTitle">Chat history</div>
      <div id="historyList" class="historyList"></div>
      <button class="sideLink" id="clearHistory">Clear chat history</button>

      <div class="sidebarTitle">Services</div>
      <div class="sideServices">
        <button class="sideService" data-example="Check AGI."><b>Check a Token</b><span>Quick token health check</span></button>
        <button class="sideService" data-example="Which looks better right now, XNT or AGI?"><b>Compare Tokens</b><span>Compare two assets</span></button>
        <button class="sideService" data-example="Should I buy $500 of AGI right now?"><b>Should I Buy or Sell?</b><span>Opinion before a trade</span></button>
        <button class="sideService" data-example="Is AGI risky right now?"><b>Check Risk</b><span>Find important problems</span></button>
        <button class="sideService" data-example="Did a big wallet just buy AGI?"><b>Track Wallets &amp; Big Trades</b><span>Wallet and transaction activity</span></button>
        <button class="sideService" data-example="What happened to AGI today?"><b>Ask ROBERTA</b><span>Ask anything normally</span></button>
      </div>

      <div class="sidebarTitle">Answer labels</div>
      <div class="labelKey"><span>Evidence</span><span>Risk</span><span>Freshness</span><span>Opinion</span></div>
      <button class="sideLink backAbout" id="backAbout">← About ROBERTA</button>
    </aside>

    <div class="workspaceMain">
      <header class="workspaceHeader">
        <div class="workspaceHeading"><b>ROBERTA</b><span>Ask about a token, trade, wallet, or market move.</span></div>
        <div class="workspaceHeaderActions">
          <div id="health" class="health">Checking ROBERTA</div>
          <span class="routeChip">X1</span><span class="routeChip">Scout → CMIS</span><span class="routeChip">Read-only</span>
          <button class="btn small" id="settingsBtn">Connection</button>
          <button class="btn small" id="clearChat">Clear chat</button>
        </div>
      </header>

      <div class="chatArea">
        <div id="messages" class="messages"></div>
        <div class="composer">
          <textarea id="composer" rows="4" placeholder="Ask ROBERTA anything… e.g. “Should I buy $500 of AGI?”"></textarea>
          <button class="btn primary" id="send">Send</button>
        </div>
        <div class="boundary">Analysis and recommendations only. ROBERTA does not execute transactions from this website.</div>
      </div>
    </div>
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

var HISTORY_KEY='robertaChatHistoryV2';
var HISTORY_LIMIT=80;
var currentChatId=null;
var sending=false;
var $=function(s){return document.querySelector(s)};

function apiBase(){return($('#apiBase').value||'').trim().replace(/\/$/,'')}
function apiUrl(path){return apiBase()?apiBase()+path:path}
function apiHeaders(){var h={'Content-Type':'application/json'},k=$('#apiKey').value.trim();if(k)h.Authorization='Bearer '+k;return h}

function enterWorkspace(mode,example){
  document.body.classList.add('workspaceMode');
  sessionStorage.setItem('robertaWorkspaceMode',mode||'human');
  if(mode==='agent')$('#settings').classList.add('open');
  if(example)$('#composer').value=example;
  setTimeout(function(){$('#composer').focus()},30);
}
function leaveWorkspace(){
  document.body.classList.remove('workspaceMode');
  sessionStorage.removeItem('robertaWorkspaceMode');
  $('#settings').classList.remove('open');
  window.scrollTo({top:0,behavior:'smooth'});
}
function useExample(text){enterWorkspace('human',text)}

function escapeHtml(text){return String(text==null?'':text).replace(/[&<>"']/g,function(ch){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]})}
function statusClass(v){
  v=String(v||'').toLowerCase().replace(/[^a-z]/g,'');
  if(['pass','verified','ok','clear','available','strong'].indexOf(v)>=0)return'good';
  if(['warn','partial','watch','caution','moderate'].indexOf(v)>=0)return'warn';
  if(['block','error','unverified','unavailable','notverified','weak'].indexOf(v)>=0)return'bad';
  return'';
}
function formatAssistant(text){
  var lines=String(text||'').split('\n'),out=[];
  lines.forEach(function(line){
    var safe=escapeHtml(line);
    if(/^(My recommendation|Conviction|Evidence quality|My view|Best evidence against my view|What would change my mind)\s*:/i.test(line.trim())){
      var p=safe.split(':'),label=p.shift();out.push('<span class="opinionLine"><strong>'+label+':</strong>'+(p.length?' '+p.join(':'):'')+'</span>');return;
    }
    if(/^\s*[A-Z][A-Z0-9 &?\/—-]{2,}:?\s*$/.test(line.trim())){out.push('<span class="msgTitle">'+safe.replace(/:$/,'')+'</span>');return}
    safe=safe.replace(/\b(PASS|WARN|BLOCK|PARTIAL|VERIFIED|UNVERIFIED|UNAVAILABLE|NOT VERIFIED|WATCH|CLEAR|CAUTION|ERROR|AVAILABLE|STRONG|MODERATE|WEAK)\b/g,function(m){return'<span class="statusToken '+statusClass(m)+'">'+m+'</span>'});
    safe=safe.replace(/(^|[\s(])([+]\d[\d,]*(?:\.\d+)?%?)(?=$|[\s),.;])/g,'$1<span class="pos">$2</span>');
    safe=safe.replace(/(^|[\s(])(-\d[\d,]*(?:\.\d+)?%?)(?=$|[\s),.;])/g,'$1<span class="neg">$2</span>');
    out.push(safe);
  });
  return out.join('\n');
}
function addMessage(role,text){
  var d=document.createElement('div');d.className='msg '+role;
  if(role==='assistant')d.innerHTML=formatAssistant(text);else d.textContent=text;
  $('#messages').appendChild(d);$('#messages').scrollTop=$('#messages').scrollHeight;return d;
}
function starter(){return "I'm ready. Ask me about a token, trade, wallet, market move, risk, burn, history, bridge activity, or anything else you want me to investigate."}

function loadHistory(){try{var raw=localStorage.getItem(HISTORY_KEY),v=raw?JSON.parse(raw):[];return Array.isArray(v)?v:[]}catch(e){return[]}}
function saveHistory(items){try{localStorage.setItem(HISTORY_KEY,JSON.stringify(items.slice(0,HISTORY_LIMIT)))}catch(e){}}
function titleFor(text){var t=String(text||'').replace(/\s+/g,' ').trim();return t.length>54?t.slice(0,51)+'…':t||'Untitled chat'}
function renderHistory(){
  var list=$('#historyList'),items=loadHistory();
  if(!items.length){list.innerHTML='<div style="color:#667294;font-size:9px;padding:6px">No saved chats yet.</div>';return}
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
function renderChat(messages){
  $('#messages').innerHTML='';
  if(!Array.isArray(messages)||!messages.length){addMessage('assistant',starter());return}
  messages.forEach(function(m){if(m&&m.role&&typeof m.text==='string')addMessage(m.role,m.text)});
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
  currentChatId=id;renderChat(item.messages);enterWorkspace('human');
}
function newChat(){currentChatId=null;renderChat([]);$('#composer').value='';$('#composer').focus()}
function clearCurrent(){currentChatId=null;renderChat([]);$('#composer').value=''}
function clearHistory(){saveHistory([]);currentChatId=null;renderHistory();renderChat([])}
function restoreLatest(){var items=loadHistory();if(items.length){currentChatId=items[0].id;renderChat(items[0].messages)}else renderChat([])}

function busy(v){sending=v;$('#send').disabled=v;$('#send').textContent=v?'Working…':'Send'}
async function health(){
  var h=$('#health');
  try{var r=await fetch(apiUrl('/healthz')),d=await r.json();if(r.ok&&d.status==='ok'){h.className='health online';h.textContent='ROBERTA online';return}throw 0}
  catch(e){h.className='health offline';h.textContent='ROBERTA offline'}
}
async function send(text){
  text=(text||'').trim();if(!text||sending)return;
  var chatId=beginRecord(text);addMessage('user',text);$('#composer').value='';busy(true);
  var wait=addMessage('system','ROBERTA is checking accepted evidence…');
  try{
    var r=await fetch(apiUrl('/v1/roberta'),{method:'POST',headers:apiHeaders(),body:JSON.stringify({message:text})});
    var d=await r.json().catch(function(){return{}});
    wait.remove();
    var reply=!r.ok?((d.error&&d.error.message)||('Request failed ('+r.status+')')):(d.reply||'ROBERTA returned no reply.');
    addMessage('assistant',reply);appendRecord(chatId,'assistant',reply);
  }catch(e){
    wait.remove();var reply='I could not reach the ROBERTA bridge. Verify that it is running and check Connection settings.';
    addMessage('assistant',reply);appendRecord(chatId,'assistant',reply);
  }finally{busy(false);health()}
}

document.addEventListener('click',function(e){
  var sc=e.target.closest('[data-scroll]');if(sc){var target=document.getElementById(sc.dataset.scroll);if(target)target.scrollIntoView({behavior:'smooth'})}
  var ex=e.target.closest('[data-example]');if(ex)useExample(ex.dataset.example);
  var hi=e.target.closest('[data-chat-id]');if(hi)openSaved(hi.dataset.chatId);
});
['humanEntryTop','humanEntryHero','humanEntryBottom'].forEach(function(id){var n=document.getElementById(id);if(n)n.onclick=function(){enterWorkspace('human')}});
['agentEntryTop','agentEntryHero'].forEach(function(id){var n=document.getElementById(id);if(n)n.onclick=function(){enterWorkspace('agent')}});
$('#backAbout').onclick=leaveWorkspace;
$('#newChat').onclick=newChat;$('#clearChat').onclick=clearCurrent;$('#clearHistory').onclick=clearHistory;
$('#settingsBtn').onclick=function(){$('#settings').classList.toggle('open')};
$('#send').onclick=function(){send($('#composer').value)};
$('#composer').addEventListener('keydown',function(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send($('#composer').value)}});
$('#apiBase').value=sessionStorage.getItem('robertaApiBase')||'';$('#apiKey').value=sessionStorage.getItem('robertaApiKey')||'';
$('#apiBase').onchange=function(){sessionStorage.setItem('robertaApiBase',this.value.trim());health()};
$('#apiKey').onchange=function(){sessionStorage.setItem('robertaApiKey',this.value)};
document.addEventListener('keydown',function(e){if(e.key==='Escape')$('#settings').classList.remove('open')});

renderHistory();restoreLatest();health();setInterval(health,30000);
var mode=sessionStorage.getItem('robertaWorkspaceMode');if(mode)enterWorkspace(mode);
})();
</script>
</body>
</html>'''


def web_ui_bytes() -> bytes:
    return ROBERTA_WEB_UI_HTML.encode("utf-8")


__all__ = ["ROBERTA_WEB_UI_HTML", "web_ui_bytes"]
