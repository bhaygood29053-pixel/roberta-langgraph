# ROBERTA Website v2

ROBERTA now uses a human-first website rather than a technical capability dashboard.

The website is served by the existing ROBERTA bridge process and keeps the existing public API boundary:

```text
GET  /
GET  /healthz
POST /v1/roberta
{"message":"..."}
```

No browser -> CMIS or browser -> provider authority path is introduced.

## Public website

The first page explains ROBERTA in plain English:

> Ask about a token, trade, wallet, or market move.

It presents six condensed services that match what ordinary users are most likely to request:

1. **Check a Token** — current token health, market context, liquidity, activity, structure, recent changes, and available evidence.
2. **Compare Tokens** — side-by-side comparison of two assets.
3. **Should I Buy or Sell?** — evidence-bounded ROBERTA opinion before a proposed trade.
4. **Check Risk** — liquidity, concentration, authority, unusual-activity, freshness, evidence, and trade-size concerns.
5. **Track Wallets & Big Trades** — verified public-wallet activity, important transactions, volume contribution, and pool-level price impact where supported.
6. **Ask ROBERTA** — free-form natural-language access. ROBERTA selects the appropriate specialist path automatically.

Every service includes human-readable example questions. Selecting an example opens the chat workspace and pre-fills the composer.

The old technical service catalog, roadmap/status band, filter UI, and public contract-name navigation have been removed from the website rather than merely hidden.

## Human and agent entry

The public page provides:

- **Enter Human Chat / Open ROBERTA**
- **Agent / API Access**

Both lead to the same ROBERTA truth and evidence boundary.

Human entry opens the chat workspace directly.

Agent entry opens the chat workspace and the Connection panel, which shows the existing `POST /v1/roberta` endpoint and optional bearer-token configuration.

Agent access does not create wallet, transaction, policy, CMIS, provider, or execution authority.

## Chat workspace

After entry, the public marketing page is replaced by a dedicated ROBERTA workspace containing:

- **New Chat**
- **Clear Chat**
- persistent **Chat History**
- history grouped into **Today** and **Previous**
- **Clear Chat History**
- the six human service shortcuts
- example prompts
- always-available free-form chat
- connection health
- simple **X1**, **Scout -> CMIS**, and **Read-only** labels
- answer-label reminders for **Evidence**, **Risk**, **Freshness**, and **Opinion**
- a return control for **About ROBERTA**

Chat history is stored only in browser local storage. Connection settings and the selected workspace mode are stored in browser session storage.

## Response presentation

The website preserves human-readable formatting for ROBERTA responses, including:

- recommendation / conviction / evidence-quality lines;
- section headings;
- PASS / WARN / BLOCK and related evidence states;
- signed positive and negative values.

Opinion-bearing questions continue to be decided by ROBERTA's accepted opinion layer. The browser does not calculate recommendations or deterministic risk.

## Architecture

The authority path remains:

```text
User / Agent
  -> ROBERTA
    -> Chain Scout
      -> CMIS
        -> verified provider/source
```

The website is a presentation and transport surface only.

ROBERTA may analyze and recommend, but the website does not sign transactions, broadcast transactions, move funds, execute swaps, or authorize autonomous value movement.

## Keeping the website current

Merged repository capability is the source of truth.

When ROBERTA gains a new accepted backend capability, the preferred website policy is:

1. determine whether it strengthens one of the six existing human services;
2. update that service's description or examples only when users gain a meaningful new question they can reliably ask;
3. avoid adding a new public service merely because a new internal contract exists;
4. keep incomplete, experimental, failing-gate, or unaccepted functionality off the public website;
5. update this document and the website contract tests with any material product-surface change.

This keeps the website simple while allowing ROBERTA's internal intelligence surface to continue expanding.
