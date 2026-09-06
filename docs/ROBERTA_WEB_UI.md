# ROBERTA Local Web UI

The ROBERTA bridge serves a local browser interface from the same process that owns `/v1/roberta`.

## Start

Use the existing ROBERTA bridge command or systemd unit. With the default local configuration:

```text
http://127.0.0.1:8766/
```

Health remains available at:

```text
http://127.0.0.1:8766/healthz
```

The browser sends normal user requests only to:

```text
POST /v1/roberta
{"message":"..."}
```

The website does not create a browser -> CMIS or browser -> provider authority path.

## Product experience

The website now has two modes.

### 1. Public introduction

Before entering the workspace, the homepage explains who ROBERTA is and presents six human-friendly services:

1. **Check a Token** — quick token health and context.
2. **Compare Tokens** — side-by-side comparison of two assets.
3. **Should I Buy or Sell?** — ROBERTA's evidence-bounded opinion before a proposed trade.
4. **Check Risk** — important liquidity, concentration, authority, freshness, and evidence problems.
5. **Track Wallets & Big Trades** — verified public-wallet activity, important transactions, volume contribution, and pool-level price impact when supported.
6. **Ask ROBERTA** — normal-language access where ROBERTA selects the appropriate intelligence path automatically.

Each service includes plain-English examples. Selecting an example opens the chat workspace and places that example in the composer so the user can edit or send it.

The public page intentionally does **not** expose the full internal specialist catalog. Technical services remain implementation details behind ROBERTA.

### 2. Connected chat workspace

Choosing **Enter Human Chat**, **Agent / API Access**, or **Open ROBERTA** switches the page into a dedicated chat workspace.

The workspace includes:

- **New Chat**;
- persistent **Chat History**, grouped into **Today** and **Previous**;
- **Clear chat history**;
- **Clear chat** for the current conversation;
- the six human-friendly services with one-click example prompts;
- a free-form ROBERTA composer that is always available;
- connection health and simple route labels;
- answer-label reminders for **Evidence**, **Risk**, **Freshness**, and **Opinion**;
- an **About ROBERTA** control to return to the public introduction.

The selected workspace mode is kept in browser session storage, while chat history is kept in browser local storage.

## Human and agent access

**Human Chat** opens the conversational workspace directly.

**Agent / API Access** opens the same workspace and exposes the existing Connection panel. Agents still use the same ROBERTA public HTTP boundary rather than calling CMIS/provider services directly.

The website does not grant an agent new wallet, policy, transaction, or execution authority.

## Specialist services behind the simple interface

ROBERTA may use accepted specialist capabilities behind a human request, including the current Instant X1 Scan v6 path, comparison, risk, liquidity, history, burn, discovery, WHAT CHANGED?, concentration intelligence, pre-trade analysis, cross-chain intelligence, and accepted wallet/trade price-impact intelligence.

These contract names are intentionally hidden from ordinary website navigation. The user asks for an outcome; ROBERTA selects the specialist path.

## Trust boundary

The authority path remains:

```text
User / agent
  -> ROBERTA
    -> Chain Scout
      -> CMIS
        -> verified provider/source
```

Missing evidence remains unknown/unavailable. Evidence quality remains separate from deterministic risk. Public wallet addresses do not establish real-world identity. Pool-local price impact does not establish whole-market causality.

ROBERTA may analyze and recommend, but the website does not sign transactions, broadcast transactions, move funds, execute swaps, or authorize autonomous value movement.

## Authentication

Default loopback use requires no bearer token. If `ROBERTA_API_KEY` is configured, the Connection panel accepts the token. Connection values are stored only in browser session storage and are sent to `/v1/roberta`.

Do not expose the loopback bridge to an untrusted network merely to make the UI externally reachable.

## Animated ROBERTA field

The public introduction keeps the procedural ROBERTA intelligence animation. It is presentation only and does not change evidence, routing, risk, policy, wallet, or execution authority.

The renderer remains responsive, pauses when the page is hidden, respects `prefers-reduced-motion`, and caps device-pixel ratio and particle density.

## ROBERTA Opinion v1

Opinion-bearing questions continue through the accepted protected `roberta_opinion/v1` behavior.

Human ROBERTA is expected to lead with **My recommendation**, followed by **Conviction**, **Evidence quality**, **My view**, the strongest material evidence against that view, and **What would change my mind**.

Facts and deterministic risk remain Scout -> CMIS owned. Judgment remains ROBERTA-owned. The website does not calculate a recommendation itself.
