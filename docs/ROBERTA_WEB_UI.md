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
- six clickable example questions.

The examples include token, wallet, comparison, price-move, transaction-trace, and market-discovery questions.

Submitting the first question immediately enters the ROBERTA workspace and sends that question. The user does not have to select a service before asking.

## What ROBERTA can help with

A compact explanatory section uses outcome-oriented categories:

- **Tokens**
- **Trades**
- **Wallets**
- **Compare**
- **Market**
- **Investigations**

These categories are examples and shortcuts, not routing requirements.

Technical implementation terms such as CMIS contract names, provider names, raw service names, and internal verification contract identifiers are intentionally absent from normal website navigation.

## Workspace

After the first question, the public page is replaced by the ROBERTA workspace.

### Left side

The left sidebar contains:

- **New Chat**
- **Chat History**, grouped into **Today** and **Previous**
- **Saved investigations**
- a collapsible **Services** drawer
- an **About ROBERTA** return control

Chat history is stored in browser local storage under `robertaChatHistoryV3`.

Saved investigations are stored separately under `robertaSavedInvestigationsV1`.

A saved investigation can be reopened or rechecked with current data. Rechecking asks ROBERTA to compare the current verified result with the earlier conversation and call out meaningful changes.

### Center

The center always remains the conversation.

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

Normal typed follow-ups carry a small amount of recent browser-local conversation context into the next `/v1/roberta` request. The visible user message remains unchanged.

### Right side

The right panel is optional and collapsible.

It contains:

- current-answer summary;
- evidence / risk / freshness / opinion / confidence labels when those fields can be read from the answer;
- selected on-chain identifier detail;
- evidence and explanation follow-up actions;
- source/chart guidance.

The conversation remains primary. On smaller screens, the evidence panel is hidden rather than squeezing the chat.

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

Clicking one opens the detail panel with follow-up options such as:

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

## Facts, judgment, uncertainty, and confidence

The website reinforces ROBERTA's evidence model by visually separating:

- verified facts;
- ROBERTA's assessment;
- uncertainty;
- confidence / conviction;
- evidence quality.

Risk and evidence quality remain different dimensions.

The browser never turns a PASS, high confidence, or strong evidence label into trade permission.

## Execution boundary

ROBERTA may analyze, investigate, compare, and recommend.

The website does not:

- sign transactions;
- broadcast transactions;
- move funds;
- execute swaps;
- execute bridge transfers;
- grant autonomous value-movement authority.

## Keeping the website current

Merged repository capability remains the website source of truth.

When ROBERTA gains a new accepted backend capability:

1. prefer strengthening an existing human outcome rather than exposing a new technical service name;
2. add or change examples only when the new question can be answered reliably;
3. keep incomplete, experimental, failing-gate, or unaccepted functionality off the public website;
4. preserve the conversation-first UX even as internal intelligence becomes more sophisticated;
5. update this document and the website contract tests with any material public-surface change.


## Human Intelligence Experience — progressive disclosure

ROBERTA #381 adds human-first website presentation on top of the accepted Human
Response and conversational-continuity contracts.

The conversation now presents a compact ROBERTA judgment label when the accepted
ROBERTA direct-answer vocabulary already supplies one. Risk, evidence quality,
freshness, and conviction remain separate display concepts.

Raw machine statuses remain visually neutral rather than being promoted into
economic meaning.

Evidence and technical detail are available through native keyboard-safe
details / summary disclosure controls. Those controls request evidence from
ROBERTA; the browser does not call CMIS/providers or calculate risk, compliance,
freshness, or market facts.

See ROBERTA_WEB_PROGRESSIVE_DISCLOSURE_V1.md.
