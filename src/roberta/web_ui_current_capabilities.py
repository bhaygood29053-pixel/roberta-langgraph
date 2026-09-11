"""Human-facing overlay for the newest accepted ROBERTA capability surface.

The large conversation-first UI intentionally remains stable. This module adds a
small current-capabilities surface at package load so accepted backend progress
can be reflected without turning the website into an internal service catalog.
It also carries small human-facing workspace refinements that should survive
future capability updates without rewriting the large base UI.
No CMIS/provider names or raw contract identifiers are exposed to website users.
"""

from __future__ import annotations

WEBSITE_CAPABILITY_SURFACE = "roberta-website-capabilities/2026-09-11"
WEBSITE_CAPABILITY_MARKER = 'data-capability-surface="roberta-website-capabilities/2026-09-11"'
WORKSPACE_CHAT_FOCUS_MARKER = 'id="chat-focus-workspace-v1"'

_HERO_OLD = (
    '<p class="heroLead">She will investigate it, explain what she found, and tell you what she thinks. '
    'Ask about tokens, wallets, liquidity, trades, burns, bridges, risk, or activity without learning a technical tool first.</p>'
)
_HERO_NEW = (
    '<p class="heroLead">She will investigate it, explain what she found, and tell you what she thinks. '
    'Ask about tokens, wallets, relationships, liquidity, trades, burns, bridges, tokenized equities, risk, '
    'daily X1 intelligence, or unusual activity without learning a technical tool first.</p>'
)

_CURRENT_CAPABILITIES = r'''
    <section id="current-capabilities" class="section" data-capability-surface="roberta-website-capabilities/2026-09-11">
      <div class="shell">
        <div class="sectionHead">
          <div><div class="kicker">Current accepted capabilities</div><h2>More of ROBERTA is now available through one conversation.</h2></div>
          <p>The website stays simple while ROBERTA automatically works through the verified evidence needed for the question. Missing evidence stays explicit instead of being guessed.</p>
        </div>
        <div class="helpGrid">
          <article class="helpCard"><h3>Pre-trade intelligence</h3><p>Assess trade size, liquidity, activity, verified price-impact evidence, risk, freshness, and what execution evidence is still unavailable.</p><button data-ask-now="Evaluate a $500 AGI buy before I trade and show me the verified evidence and anything still unavailable.">Example: Evaluate a trade →</button></article>
          <article class="helpCard"><h3>Wallet relationships</h3><p>Verify direct wallet-to-wallet interactions, connected transactions, first observed interaction, and token amounts without inventing ownership or intent.</p><button data-ask-now="Did these two wallets directly interact? Show me the verified transactions connecting them.">Example: Compare two wallets →</button></article>
          <article class="helpCard"><h3>Tokenized equities &amp; RWAs</h3><p>Investigate provenance, wrapper layers, backing and rights evidence, custody, activity, and cross-chain lineage. Accepted Machine synthesis preserves evidence-required and denied states instead of reconstructing missing facts.</p><button data-ask-now="What exactly am I buying with this tokenized equity? Show provenance, rights, backing, custody, and evidence limits.">Example: Explain a tokenized equity →</button></article>
          <article class="helpCard"><h3>X1 Daily Intelligence Brief</h3><p>Ask for a concise X1 intelligence brief that separates verified activity, priority, uncertainty, judgment, and evidence limits.</p><button data-ask-now="Give me today's X1 intelligence brief and tell me what matters most.">Example: Today's X1 brief →</button></article>
          <article class="helpCard"><h3>Large trades &amp; price impact</h3><p>Investigate verified large trades, public-wallet attribution when available, exact pool-local effects, volume contribution, and the next verified pool trade.</p><button data-ask-now="Show me the most important recent large trades and any verified pool-local price impact.">Example: Investigate large trades →</button></article>
          <article class="helpCard"><h3>Evidence-complete answers</h3><p>Every supported investigation carries its available evidence, proof quality, freshness, and explicit missing or unavailable evidence before ROBERTA synthesizes a judgment.</p><button data-ask-now="Show me the evidence package behind your last answer, including what is verified, partial, blocked, or unavailable.">Example: Inspect the evidence package →</button></article>
        </div>
      </div>
    </section>
'''

_EXTRA_HERO_EXAMPLES = (
    '          <button class="heroExample" data-ask-now="Give me today\'s X1 intelligence brief.">Give me today\'s X1 intelligence brief.</button>\n'
    '          <button class="heroExample" data-ask-now="What exactly am I buying with this tokenized equity?">What exactly am I buying with this tokenized equity?</button>\n'
)

_EXTRA_SIDE_SERVICES = (
    '        <button class="sideService" data-fill="Give me today\'s X1 intelligence brief and tell me what matters most."><b>Daily Brief</b><span>Verified activity, priority, judgment, unknowns</span></button>\n'
    '        <button class="sideService" data-fill="What exactly am I buying with this tokenized equity? Show provenance, rights, backing, custody, and evidence limits."><b>Tokenized Equities</b><span>Provenance, rights, backing, Machine synthesis</span></button>\n'
    '        <button class="sideService" data-fill="Did these two wallets directly interact? Show the verified transactions connecting them."><b>Wallet Relationships</b><span>Observed direct interactions and transfers</span></button>\n'
)

_WORKSPACE_CHAT_FOCUS_STYLE = r'''
<style id="chat-focus-workspace-v1">
/* Chat-first workspace: preserve the left navigation, reclaim the evidence column
   for the conversation, and make sidebar text comfortably readable. */
.workspaceGrid{grid-template-columns:270px minmax(0,1fr)!important}
.inspector{display:none!important}
.inspector.entityOpen{display:block!important;position:fixed!important;right:18px!important;top:86px!important;z-index:90!important;width:min(360px,calc(100vw - 36px))!important;height:auto!important;max-height:calc(100vh - 104px)!important;overflow:auto!important;box-shadow:-18px 18px 60px rgba(0,0,0,.45)!important}
.workspaceBrand b{font-size:15px!important}
.workspaceBrand span{font-size:10px!important;line-height:1.35}
.sidebarTitle{font-size:11px!important}
.historyItem b,.savedItem b{font-size:12px!important}
.historyItem span,.savedItem span{font-size:10px!important;line-height:1.35}
.recheckBtn{font-size:10px!important}
.sideLink{font-size:11px!important}
.servicesToggle{font-size:12px!important}
.sideService b{font-size:12px!important}
.sideService span{font-size:10px!important;line-height:1.4}

/* The main composer button communicates request state without changing request logic. */
#send{background:#15803d!important;border-color:#22c55e!important;color:#fff!important;opacity:1!important}
#send:disabled{background:#b91c1c!important;border-color:#ef4444!important;color:#fff!important;opacity:1!important}

@media(max-width:940px){.workspaceGrid{grid-template-columns:240px minmax(0,1fr)!important}.inspector.entityOpen{right:12px!important;top:78px!important}}
</style>
'''

_BUSY_OLD = "$('#send').textContent=v?'Working…':'Send'"
_BUSY_NEW = "$('#send').textContent=v?'Working':'Send'"
_OPEN_ENTITY_OLD = "$('#inspector').classList.remove('collapsed');"
_OPEN_ENTITY_NEW = "var inspector=$('#inspector');inspector.classList.add('entityOpen');inspector.classList.remove('collapsed');$('#inspectorToggle').setAttribute('aria-expanded','true');$('#inspectorToggle').setAttribute('aria-label','Close identifier details');"
_INSPECTOR_TOGGLE_OLD = "$('#inspectorToggle').onclick=function(){var collapsed=$('#inspector').classList.toggle('collapsed');this.textContent=collapsed?'‹':'›';this.setAttribute('aria-expanded',collapsed?'false':'true');this.setAttribute('aria-label',collapsed?'Expand evidence panel':'Collapse evidence panel')};"
_INSPECTOR_TOGGLE_NEW = "$('#inspectorToggle').onclick=function(){var inspector=$('#inspector');if(inspector.classList.contains('entityOpen')){inspector.classList.remove('entityOpen');this.textContent='›';this.setAttribute('aria-expanded','false');this.setAttribute('aria-label','Expand evidence panel');return}var collapsed=inspector.classList.toggle('collapsed');this.textContent=collapsed?'‹':'›';this.setAttribute('aria-expanded',collapsed?'false':'true');this.setAttribute('aria-label',collapsed?'Expand evidence panel':'Collapse evidence panel')};"


def apply_current_capability_surface(html: str) -> str:
    """Return the conversation-first UI with the latest accepted capability surface."""

    if WEBSITE_CAPABILITY_MARKER in html and WORKSPACE_CHAT_FOCUS_MARKER in html:
        return html

    updated = str(html)

    if WEBSITE_CAPABILITY_MARKER not in updated:
        if _HERO_OLD not in updated:
            raise RuntimeError("ROBERTA website hero contract drifted before capability overlay.")
        updated = updated.replace(_HERO_OLD, _HERO_NEW, 1)

        hero_anchor = (
            '          <button class="heroExample" data-ask-now="Show me the safest liquid tokens on X1.">'
            'Show me the safest liquid tokens on X1.</button>\n'
        )
        if hero_anchor not in updated:
            raise RuntimeError("ROBERTA website hero examples drifted before capability overlay.")
        updated = updated.replace(hero_anchor, hero_anchor + _EXTRA_HERO_EXAMPLES, 1)

        trust_anchor = '    <section id="trust" class="section">\n'
        if trust_anchor not in updated:
            raise RuntimeError("ROBERTA website trust section drifted before capability overlay.")
        updated = updated.replace(trust_anchor, _CURRENT_CAPABILITIES + "\n" + trust_anchor, 1)

        side_anchor = (
            '        <button class="sideService" data-fill="Trace this transaction and explain where the funds or tokens moved.">'
            '<b>Investigations</b><span>Transactions, burns, bridges, flows</span></button>\n'
        )
        if side_anchor not in updated:
            raise RuntimeError("ROBERTA website service drawer drifted before capability overlay.")
        updated = updated.replace(side_anchor, side_anchor + _EXTRA_SIDE_SERVICES, 1)

    if WORKSPACE_CHAT_FOCUS_MARKER not in updated:
        head_anchor = "</head>"
        if head_anchor not in updated:
            raise RuntimeError("ROBERTA website head contract drifted before workspace overlay.")
        updated = updated.replace(head_anchor, _WORKSPACE_CHAT_FOCUS_STYLE + "\n" + head_anchor, 1)

        for old, new, name in (
            (_BUSY_OLD, _BUSY_NEW, "busy state"),
            (_OPEN_ENTITY_OLD, _OPEN_ENTITY_NEW, "identifier detail"),
            (_INSPECTOR_TOGGLE_OLD, _INSPECTOR_TOGGLE_NEW, "identifier detail close"),
        ):
            if old not in updated:
                raise RuntimeError(f"ROBERTA website {name} contract drifted before workspace overlay.")
            updated = updated.replace(old, new, 1)

    return updated


__all__ = [
    "WEBSITE_CAPABILITY_MARKER",
    "WEBSITE_CAPABILITY_SURFACE",
    "WORKSPACE_CHAT_FOCUS_MARKER",
    "apply_current_capability_surface",
]
