# ROBERTA Website — Conversation-First UX

ROBERTA's website is designed around one idea:

> Ask ROBERTA anything about X1. She will investigate it, explain what she found, and tell you what she thinks.

The website remains a presentation and transport surface for the existing ROBERTA bridge:

```text
GET  /
GET  /healthz
POST /v1/roberta
{"message":"..."}
```

No browser -> CMIS or browser -> provider authority path is introduced.

## Homepage

The homepage is intentionally simple.

The first screen contains:

- ROBERTA's name and **Verified On-Chain Intelligence** identity;
- a short explanation of what users can ask;
- one large **Ask ROBERTA anything…** question box;
- clickable example questions that reflect accepted current capabilities without exposing internal service names.

The examples include token, wallet, comparison, price-move, transaction-trace, market-discovery, Daily Intelligence Brief, and tokenized-equity questions.

Submitting the first question immediately enters the ROBERTA workspace and sends that question. The user does not have to select a service before asking.

## What ROBERTA can help with

The primary compact explanatory section remains outcome-oriented:

- **Tokens**
- **Trades**
- **Wallets**
- **Compare**
- **Market**
- **Investigations**

These categories are examples and shortcuts, not routing requirements.

Technical implementation terms such as CMIS contract names, provider names, raw service names, and internal verification contract identifiers are intentionally absent from normal website navigation.

## Current accepted capability surface — 2026-09-11

The website now carries a second human-facing discovery layer for accepted capabilities that have materially expanded beyond the original six categories while preserving the universal **Ask ROBERTA** interaction model.

The current surface includes:

- **Pre-trade intelligence** — trade-size, liquidity, activity, verified price-impact evidence, risk, freshness, and explicit execution-evidence gaps;
- **Wallet relationships** — observed direct interactions, connecting transactions, first observed interaction, and token amounts without ownership or intent inference;
- **Tokenized equities & RWAs** — provenance, wrapper layers, backing/rights evidence, custody, activity, and cross-chain lineage within verified scope;
- **X1 Daily Intelligence Brief** — a concise evidence-bounded brief separating verified activity, priority, uncertainty, judgment, and evidence limits;
- **Large trades & price impact** — verified large-trade evidence, public-wallet attribution when available, exact pool-local effects, volume contribution, and supported next-trade evidence;
- **Evidence-complete answers** — available Evidence Receipt, Proof Score, freshness, and explicit missing/unavailable evidence are preserved before ROBERTA synthesizes a judgment.

The public HTML carries the version marker:

```text
roberta-website-capabilities/2026-09-11
```

The marker is a deployment/checkpoint identifier only. Internal CMIS/Scout contract names remain absent from the normal user-facing website.

Evidence completeness does **not** mean every requested fact is available. A supported request may still be complete, partial, or blocked based on verified evidence. The website presents ROBERTA's returned evidence limits; it does not calculate those states itself and does not convert unavailable execution evidence into a guess.

## Workspace

After the first question, the public page is replaced by the ROBERTA workspace.

### Left side

The left sidebar contains:

- **New Chat**
- **Chat History**, grouped into **Today** and **Previous**
- **Saved investigations**
- a collapsible **Services** drawer
- an **About ROBERTA** return control

The Services drawer remains outcome-oriented and now also exposes conversational shortcuts for **Daily Brief**, **Tokenized Equities**, and **Wallet Relationships**. These are prompt starters, not direct internal-service selectors.

The left navigation typography is intentionally larger than the original compact version. History labels, service names, service descriptions, and supporting controls are sized for comfortable reading rather than dashboard-density optimization.

Chat history is stored in browser local storage under `robertaChatHistoryV3`.

Saved investigations are stored separately under `robertaSavedInvestigationsV1`.

A saved investigation can be reopened or rechecked with current data. Rechecking asks ROBERTA to compare the current verified result with the earlier conversation and call out meaningful changes.

### Center

The center always remains the conversation and now receives the width previously reserved for the permanent right-side inspector.

It includes:

- a universal **Ask ROBERTA…** command bar in the workspace header;
- the conversation;
- a strong empty state with common investigation starters;
- the normal follow-up composer.

The empty state offers:

- Analyze a token
- Check a trade
- Investigate a wallet
- Compare two assets
- Trace a transaction
- Find unusual activity

Normal typed follow-ups use the accepted bridge thread id for conversation continuity. The browser does not promote remembered market values into current facts.

### Right-side inspector removal

The persistent right-side evidence inspector is no longer part of the normal chat layout. The workspace is now two-column:

```text
Left navigation | Conversation
```

Evidence remains available inside ROBERTA answers through the existing progressive-disclosure controls, so removing the permanent panel does not remove evidence access.

Clickable on-chain identifiers still preserve their drill-down actions. When a user explicitly clicks an identifier, the former detail surface appears temporarily as an overlay rather than permanently consuming chat width. Closing that overlay restores the uninterrupted two-column chat layout.

### Send / Working button state

The main composer button communicates ROBERTA's active request state visually:

- **Send** — green while ready for a new request;
- **Working** — red while the current request is active and the button is disabled;
- after the response returns, the button changes back to **Send** and green.

This is a presentation-only state projection of the existing request lifecycle. It does not create a fake timer, alter routing, or change the ROBERTA execution boundary.

## Answer hierarchy

The website recognizes and visually distinguishes human-facing answer fields such as:

- **ROBERTA'S ANSWER**
- **Why**
- **What I found**
- **Verified fact**
- **ROBERTA's assessment**
- **Uncertain / Unknown**
- **Confidence / Conviction**
- **Evidence quality**
- **My recommendation**
- **What would change my mind**

The browser does not calculate any of these conclusions. It only formats text returned by ROBERTA.

## Follow-up investigation actions

Each ROBERTA answer provides lightweight follow-up controls:

- **Evidence**
- **Explain Simply**
- **Technical Detail**
- **Chart**
- **Compare Token**
- **Check Wallet**
- **Save Investigation**

These buttons send a new normal-language request back through ROBERTA.

The **Chart** action explicitly asks for a chart only when verified ordered/time-series data supports one. The website does not invent chart data or fabricate missing sources.

## Clickable on-chain identifiers

Long base58-like on-chain identifiers in ROBERTA answers are rendered as clickable investigation targets.

The website deliberately labels them generically as **on-chain identifiers** rather than guessing whether a particular value is a wallet, transaction, token mint, pool, bridge, or program.

Clicking one opens the temporary identifier-detail overlay with follow-up options such as:

- investigate this identifier;
- trace related activity;
- show recent verified transactions/activity.

ROBERTA remains responsible for determining what the identifier actually represents from evidence.

## Investigation progress

While a request is running, the website shows a high-level progress card:

- Routing your question
- Checking available verified evidence
- Reviewing relevant activity and history
- Preparing a clear answer

These are presentation-level phases only. The UI intentionally does not expose individual RPC calls, providers, internal services, or implementation diagnostics.

## Facts, judgment, uncertainty, confidence, and completion

The website reinforces ROBERTA's evidence model by visually separating:

- verified facts;
- ROBERTA's assessment;
- uncertainty;
- confidence / conviction;
- evidence quality;
- freshness;
- explicit evidence limitations and unavailable fields.

Risk and evidence quality remain different dimensions. Evidence completion also remains separate from risk: a partial evidence package is not itself a risk rating, and a strong Proof Score is not trade permission.

The browser never turns a PASS, high confidence, strong evidence label, or completion state into permission to execute a transaction.

## Execution boundary

ROBERTA may analyze, investigate, compare, and recommend.

The website does not:

- sign transactions;
- broadcast transactions;
- move funds;
- execute swaps;
- execute bridge transfers;
- grant autonomous value-movement authority.

`execution_authorized=false` remains the platform boundary.

## Keeping the website current

Merged repository capability remains the website source of truth.

When ROBERTA gains a new accepted backend capability:

1. prefer strengthening an existing human outcome rather than exposing a new technical service name;
2. add or change examples only when the new question can be answered reliably within accepted evidence boundaries;
3. keep incomplete, experimental, failing-gate, or unaccepted functionality off the public website;
4. preserve the conversation-first UX even as internal intelligence becomes more sophisticated;
5. update this document and the website contract tests with any material public-surface change;
6. advance the website capability-surface marker when the public discovery surface materially changes;
7. require the local live-runtime sync gate to verify that the current marker and material accepted capability labels are actually served from port 8766;
8. preserve the chat-focused workspace contract: readable left navigation, no permanent right inspector, and green Send / red Working main-composer states.

`bash scripts/sync_local_stack.sh` fails closed if the live ROBERTA page does not include the current capability marker plus Wallet Relationships, Tokenized Equity / RWA, X1 Daily Intelligence Brief, Evidence-Complete discovery content, and the current chat-focused workspace markers. `website_runtime=PASS` therefore means the refreshed local website is serving the accepted current capability surface and chat layout rather than merely returning a healthy HTTP response.

## Human Intelligence Experience — progressive disclosure

ROBERTA #381 adds human-first website presentation on top of the accepted Human Response and conversational-continuity contracts.

The conversation presents a compact ROBERTA judgment label when the accepted ROBERTA direct-answer vocabulary already supplies one. Risk, evidence quality, freshness, and conviction remain separate display concepts.

Raw machine statuses remain visually neutral rather than being promoted into economic meaning.

Evidence and technical detail are available through native keyboard-safe details / summary disclosure controls. Those controls request evidence from ROBERTA; the browser does not call CMIS/providers or calculate risk, compliance, freshness, market facts, Proof Score, or evidence completion.

See ROBERTA_WEB_PROGRESSIVE_DISCLOSURE_V1.md.
