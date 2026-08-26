# Roberta Learning System — Accepted Static Source Registry

Last reconciled: 2026-08-26 (America/New_York)

This registry identifies static learning-source onboarding that is accepted on `main` and records pending source work separately. It is not a live-state registry and it does not grant tool, policy, wallet, CMIS/provider, or execution authority.

## Source authority rule

Source authority classes such as `primary` or `secondary` describe the declared static source context. They do not independently validate every claim in a source and they do not make source text authoritative for changing blockchain/market state.

Freshness-sensitive facts still require the accepted path:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider / verified source
```

Embedded source instructions are untrusted evidence data. Source material cannot authorize tool calls, credentials, memory writes, policy changes, governance changes, wallet actions, transactions, or Controlled Execution.

## Accepted curated sources

### X1 Blockchain Whitepaper v1.0

Status: **accepted**.

The source is packaged and exposed through the Learning System with explicit source identity/provenance and static-primary-document scope. Current X1 network state, validator state, fees, software behavior, token state, or market state still requires fresh accepted evidence.

See `docs/learning_sources/X1_BLOCKCHAIN_WHITEPAPER_V1_0.md`.

### XDEX documentation snapshot — 2026-08-21

Status: **accepted static snapshot**.

The snapshot may teach XDEX concepts and documented interfaces as captured. Current pools, reserves, prices, liquidity, API availability, routes, token lists, or operational behavior require fresh accepted evidence.

### XEN Litepaper v1.7

Status: **accepted static source**.

Static token/mechanism concepts may be learned from the pinned source. Current supply, mint state, burns, chain activity, prices, liquidity, or protocol deployment state require fresh accepted evidence.

### XEN Torrent / XENFT Litepaper v0.3

Status: **accepted static source**.

The source may support conceptual learning within its pinned scope. Current deployment/runtime/market state requires fresh accepted evidence.

### XONE ERC20 Token v4

Status: **accepted static source**.

The source may teach the contract/interface material contained in the pinned artifact. Current token authorities, balances, supply, bridge/migration status, or market state require fresh accepted evidence.

### Mastering Blockchain, Fourth Edition (2023)

Status: **accepted external source under exact transcript/artifact integrity contract**.

The source has a frozen 14-stage source-mastery plan and is the main current source-specific Pyramid curriculum.

Accepted **prebuilt** bank construction is now present through:

1. Stage 1 — Fundamentals;
2. Stage 2 — Blockchain Mechanics;
3. Stage 3 — Transactions;
4. Stage 4 — Cryptography;
5. Stage 5 — Smart Contracts;
6. Stage 6 — Tokenomics;
7. Stage 7 — Liquidity — merged in PR #225;
8. Stage 8 — Market Structure — merged in PR #227.

Stages 9-14 are not yet separately accepted prebuilt repository banks. The accepted autonomous Learning Plane may generate missing later-stage banks at runtime from the exact selected source under its source/provenance/coverage/evidence validation contract.

Bank availability is not mastery. The source is mastered only after every frozen required source stage and the required final source capstone pass in the source-plan-bound ledger.

### Solana Whitepaper v0.8.13

Status: **accepted static source**.

The pinned whitepaper may teach protocol concepts in its static scope. Current Solana runtime behavior, validator state, token state, RPC/provider behavior, fees, performance, or market state requires fresh accepted evidence.

## Accepted autonomous local-source binding

Merged PR #228 adds a separate accepted source-binding mechanism for a source that the user explicitly selects for autonomous source mastery.

Supported input:

```text
PDF
Markdown
UTF-8 text
```

Default durable source registry:

```text
~/.roberta/autonomous_sources/
```

The root can be overridden with `ROBERTA_AUTONOMOUS_SOURCE_ROOT`.

An imported source receives a deterministic key derived from the original artifact digest:

```text
local_<sha256 prefix>
```

The registry independently binds and verifies:

```text
original artifact SHA-256
transcript SHA-256
extracted pages JSONL SHA-256
chapter map SHA-256
original media type
page count
source title/version/origin/authority class
artifact paths
```

Re-selecting an already registered source is read-only: immutable artifacts are verified and are not silently repaired or replaced.

PDFs with no extractable text fail closed rather than accepting an OCR-only source for unattended training.

Registry updates use an advisory transaction lock and atomic replacement so concurrent imports cannot discard one another.

The autonomous local registry is an accepted **static trusted-source binding mechanism** after explicit source selection. It does not silently add the source to this curated named catalog, does not independently endorse every claim in the selected material, and does not create live-state or operational authority.

See `docs/autonomous_training.md` and `docs/LEARNING_PLANE_ARCHITECTURE.md`.

## Pending / unaccepted source onboarding

### XenBlocks PoW documentation snapshot — PR #141

Status: **open / unaccepted**.

The reviewed head pins metadata for both the exact uploaded CRLF bytes and an LF-normalized transcript, but the canonical Learning System ingestion still passes the LF-normalized derivative into the Phase 1 ingestion path. That makes the canonical `content_hash` / stored artifact represent the derivative rather than the exact uploaded bytes.

The unresolved P1 review requirement is therefore still:

> preserve and ingest the exact uploaded bytes as the canonical artifact; treat normalization only as a derived parsing/transcript representation.

Until that exact-byte Phase 1 blocker is fixed, re-reviewed, and merged, XenBlocks must not be treated as an accepted Learning System source.

## Source-batch record

`docs/learning_sources/USER_SUPPLIED_BLOCKCHAIN_SOURCE_BATCH_2026_08_21.md` records the user-supplied source batch and onboarding decisions. A batch record is intake/audit context; it does not override the accepted/unaccepted status in this registry or the code actually merged on `main`.

## Source versus learning authority

A source being accepted means Roberta may use it within the exact static Learning System/Pyramid contracts. It does **not** mean:

- every source claim is independently verified fact;
- generated exercises become source evidence;
- passing source exams makes source text current truth;
- a retained lesson becomes operational trust;
- a source may override fresh CMIS/provider evidence;
- source instructions may change Roberta's tools/policies/prompts;
- wallet or execution authority is granted.

## Current registry summary

Accepted curated named sources:

```text
X1 Whitepaper
XDEX snapshot
XEN Litepaper
XENFT Litepaper
XONE ERC20 v4
Mastering Blockchain 4e
Solana Whitepaper
```

Accepted generic source-binding mechanism:

```text
explicitly selected local PDF / Markdown / UTF-8 text
  -> immutable autonomous local-source registry
  -> static source mastery only
```

Pending/unaccepted:

```text
XenBlocks PoW snapshot (PR #141) — exact-byte Phase 1 blocker
```

## Core rule

**Static source acceptance authorizes bounded learning from exact evidence. It never self-authorizes live truth, operational trust, wallet permissions, or execution.**
