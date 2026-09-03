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
.chatLayout{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:18px}.chat,.info{border:1px solid var(--line);background:#fff;border-radius:30px;overflow:hidden;box-shadow:0 18px 50px rgba(41,44,84,.07)}.chatHead{padding:18px 20px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;align-items:center;gap:12px}.chatHeadActions{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.chatTitle{font-size:17px;font-weight:950;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:4px}.messages{height:650px;min-height:650px;overflow:auto;padding:24px;display:flex;flex-direction:column;gap:14px;background:linear-gradient(180deg,#fcfcff,#f8f9ff)}.msg{max-width:90%;padding:14px 16px;border-radius:18px;white-space:pre-wrap;word-break:break-word}.msg.user{align-self:flex-end;background:var(--ink);color:#fff;border-bottom-right-radius:6px}.msg.assistant{align-self:flex-start;background:#fff;border:1px solid var(--line);color:var(--ink2);border-bottom-left-radius:6px}.msg.system{align-self:center;color:var(--muted);font-size:11px;padding:3px}.msgTitle{display:block;font-weight:950;text-decoration:underline;text-decoration-thickness:2px;text-underline-offset:3px;margin:2px 0 5px;color:var(--ink)}.statusToken{display:inline-flex;align-items:center;padding:1px 7px;border-radius:999px;border:1px solid var(--grayLine);background:var(--grayBg);color:var(--grayText);font-weight:900;font-size:.9em}.statusToken.pass,.statusToken.verified,.statusToken.ok,.statusToken.clear,.statusToken.available{background:var(--greenBg);border-color:var(--greenLine);color:var(--greenText)}.statusToken.warn,.statusToken.partial,.statusToken.watch,.statusToken.caution{background:var(--amberBg);border-color:var(--amberLine);color:var(--amberText)}.statusToken.block,.statusToken.error,.statusToken.unverified,.statusToken.unavailable,.statusToken.notverified{background:var(--redBg);border-color:var(--redLine);color:var(--redText)}.signedPositive{color:var(--greenText);font-weight:900}.signedNegative{color:var(--redText);font-weight:900}.composer{border-top:1px solid var(--line);padding:16px;display:grid;grid-template-columns:1fr auto;gap:10px}.composer textarea{resize:vertical;min-height:100px;max-height:260px;border:1px solid var(--line);background:#f8f9fd;color:var(--ink);border-radius:18px;padding:14px 15px;outline:none}.info{padding:22px}.info h3{font-size:18px;margin:0 0 12px}.infoBlock{border-top:1px solid var(--line);padding:15px 0}.infoBlock:first-of-type{border-top:0}.infoBlock b{display:block;color:var(--ink);font-size:10px;text-transform:uppercase;letter-spacing:.1em;margin-bottom:5px}.infoBlock span{color:var(--muted);font-size:12px}.historyPanel{border-bottom:1px solid var(--line);background:#fbfbfe;padding:12px 14px;display:none}.historyPanel.open{display:block}.historyTop{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:10px}.historyTop b{font-size:12px}.historyList{display:grid;gap:7px;max-height:220px;overflow:auto}.historyItem{border:1px solid var(--line);background:#fff;border-radius:14px;padding:9px 11px;cursor:pointer;text-align:left}.historyItem:hover{border-color:#cbc7ff;background:#f9f8ff}.historyItemTitle{display:block;font-weight:900;text-decoration:underline;text-underline-offset:2px;font-size:11px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.historyItemTime{display:block;color:var(--muted);font-size:9px;margin-top:2px}.historyEmpty{color:var(--muted);font-size:11px;padding:8px}.btn.small{padding:7px 10px;font-size:10px}
.settings{display:none;position:fixed;z-index:60;right:24px;top:86px;width:min(390px,calc(100vw - 48px));background:#fff;border:1px solid var(--line);border-radius:24px;padding:18px;box-shadow:var(--shadow)}.settings.open{display:block}.settings h3{margin:0 0 12px}.settings .field+.field{margin-top:10px}.note{color:var(--muted);font-size:10px;margin-top:10px}
.modalBg{display:none;position:fixed;inset:0;z-index:70;background:rgba(16,19,38,.52);backdrop-filter:blur(8px);padding:18px;place-items:center}.modalBg.open{display:grid}.modal{width:min(640px,100%);max-height:90vh;overflow:auto;background:#fff;border:1px solid var(--line);border-radius:30px;box-shadow:var(--shadow)}.modalHead{padding:22px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:12px}.modalHead h3{margin:0;font-size:22px}.modalHead p{color:var(--muted);font-size:12px;margin:5px 0 0}.close{width:36px;height:36px;border:1px solid var(--line);border-radius:50%;background:#fff;color:var(--ink);cursor:pointer}.form{padding:20px;display:grid;gap:14px}.field{display:grid;gap:6px}.field label{color:var(--ink2);font-size:11px;font-weight:800}.field input,.field select{border:1px solid var(--line);background:#fbfbfe;color:var(--ink);padding:12px 13px;border-radius:14px;outline:none}.modalActions{padding:0 20px 20px;display:flex;justify-content:flex-end;gap:8px}
.footer{padding:34px 0 48px;border-top:1px solid var(--line);color:var(--muted);font-size:11px}.footerInner{display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}
@media(max-width:1050px){.navLinks{display:none}.flow{grid-template-columns:1fr 1fr}.flowNode:not(:last-child):after{display:none}.crossSteps{grid-template-columns:1fr 1fr}.grid{grid-template-columns:repeat(2,1fr)}.sectionHead{grid-template-columns:1fr}.sectionHead p{margin:0}.bandGrid{grid-template-columns:1fr}.chatLayout{grid-template-columns:1fr}.info{display:none}.trustStrip{grid-template-columns:1fr}}
@media(max-width:680px){.crossSteps{grid-template-columns:1fr}.crossChainHead{align-items:flex-start;flex-direction:column}.shell{width:min(100% - 24px,1240px)}.navInner{height:68px}.brandText small,.navActions .pill{display:none}.hero{padding:64px 0 52px}.hero h1{font-size:48px}.stageCard{padding:18px;border-radius:24px}.stageTop{align-items:flex-start;flex-direction:column}.flow{grid-template-columns:1fr}.grid{grid-template-columns:1fr}.section{padding:62px 0}.sectionHead h2{font-size:39px}.serviceTools{align-items:stretch;flex-direction:column}.search{width:100%}.productBand{padding:30px 22px;border-radius:28px}.heroBtns{display:grid}.heroBtns .btn{width:100%}.composer{grid-template-columns:1fr}.navActions .btn{padding:9px 12px}.messages{height:520px;min-height:520px}}
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
        <button data-go="home">Overview</button>
        <button data-go="services">Capabilities</button>
        <button data-go="trust">Trust</button>
        <button data-go="chat">Ask ROBERTA</button>
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
    <section id="home" class="hero">
      <div class="heroGrid"></div>
      <div class="shell heroInner">
        <div class="heroBadge">ROBERTA intelligence platform</div>
        <h1>On-chain intelligence that <span>reasons with evidence.</span></h1>
        <p class="heroLead">Ask a question, run a verified assessment, or explore a specialist capability. ROBERTA coordinates the right Scout and CMIS evidence path while keeping unknowns, proof quality, and risk explicit.</p>
        <div class="heroBtns">
          <button class="btn primary" data-svc="full">Run Full Assessment</button>
          <button class="btn soft" data-svc="scan">Instant X1 Scan</button>
          <button class="btn" data-go="chat">Ask ROBERTA</button>
        </div>

        <div class="heroStage">
          <div class="stageGlow"></div>
          <div class="stageCard">
            <div class="stageTop">
              <div class="stageTitle"><div class="stageOrb">R</div><div><b>ROBERTA verification path</b><small>One governed path from question to evidence-backed answer</small></div></div>
              <div class="pill">CMIS 1.18 · Read-only intelligence</div>
            </div>
            <div class="flow">
              <div class="flowNode"><span class="microLabel">01</span><strong>You ask</strong><span>Natural language or a selected intelligence service.</span></div>
              <div class="flowNode hot"><span class="microLabel">02</span><strong>ROBERTA orchestrates</strong><span>Selects the accepted specialist path without exposing provider controls.</span></div>
              <div class="flowNode"><span class="microLabel">03</span><strong>Chain Scout</strong><span>Interprets X1 or configured Solana evidence without manufacturing facts.</span></div>
              <div class="flowNode"><span class="microLabel">04</span><strong>CMIS verifies</strong><span>Owns deterministic facts, evidence, proof and risk contracts.</span></div>
              <div class="flowNode"><span class="microLabel">05</span><strong>Answer</strong><span>Verified result with freshness, limitations and unknowns preserved.</span></div>
            </div>
          </div>
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

    <section class="section alt">
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
function statusClass(value){var v=String(value||'').toLowerCase().replace(/[^a-z]/g,'');if(['pass','verified','ok','clear','available'].indexOf(v)>=0)return v;if(['warn','partial','watch','caution'].indexOf(v)>=0)return v;if(['block','error','unverified','unavailable','notverified'].indexOf(v)>=0)return v;return''}
function formatAssistant(text){
  var lines=String(text||'').split('\n'),out=[];
  lines.forEach(function(line){
    var safe=escapeHtml(line);
    if(/^\s*[A-Z][A-Z0-9 &?\/—-]{2,}:?\s*$/.test(line.trim())){out.push('<span class="msgTitle">'+safe.replace(/:$/,'')+'</span>');return}
    safe=safe.replace(/\b(PASS|WARN|BLOCK|PARTIAL|VERIFIED|UNVERIFIED|UNAVAILABLE|NOT VERIFIED|WATCH|CLEAR|CAUTION|ERROR|AVAILABLE)\b/g,function(m){var cls=statusClass(m);return'<span class="statusToken '+cls+'">'+m+'</span>'});
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
</body></html>'''


def web_ui_bytes() -> bytes:
    return ROBERTA_WEB_UI_HTML.encode("utf-8")


__all__ = ["ROBERTA_WEB_UI_HTML", "web_ui_bytes"]
