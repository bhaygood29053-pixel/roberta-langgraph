# Roberta Learning System — Static Source Registry

Last reconciled: 2026-08-25 (America/New_York)

This registry records human-readable source-onboarding status. Runtime truth still comes from exact source contracts/code on `main`; this document does not promote an unmerged source or create live-state authority.

## Authority rule

Static Learning System sources are evidence/knowledge inputs only. They do not become authoritative for freshness-sensitive prices, liquidity, supply, wallet state, validator state, provider health, fees, software versions, token authorities, risk, or other changing blockchain state.

Fresh accepted chain evidence follows:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider / verified source
```

Source text is data, never a permission layer. Embedded instructions cannot authorize tools, credentials, memory writes, governance changes, wallet actions, transactions, or Controlled Execution.

## Accepted sources on `main`

| Source key / source | Status | Static role | Notes |
| --- | --- | --- | --- |
| `x1_blockchain_whitepaper_v1_0` / X1 Blockchain Whitepaper v1.0 | Accepted | Primary static protocol/architecture documentation | Onboarded by #138; no live-state authority. |
| XDEX documentation snapshot | Accepted | Static documentation snapshot | Onboarded by #147; contradictory statements remain visible rather than silently reconciled. |
| XEN Litepaper v1.7 | Accepted | Primary static project documentation | Onboarded by #147 using deterministic PDF transcript provenance. |
| XEN Torrent / XENFT Litepaper v0.3 | Accepted | Primary static project documentation | Onboarded by #147 using deterministic PDF transcript provenance. |
| XONE ERC20 Token v4 | Accepted | Static documentation with bounded/unknown publisher authority | Onboarded by #147; source inclusion is not provider/live verification. |
| `mastering_blockchain_4e_2023` / *Mastering Blockchain, Fourth Edition* | Accepted external integrity contract | Secondary educational/reference source | Full copyrighted transcript is not republished; runtime must provide exact bytes matching the pinned transcript contract. |
| Solana whitepaper v0.8.13 | Accepted | Primary static protocol documentation | Onboarded by #147 using deterministic PDF transcript provenance. |

Detailed six-source provenance: [`USER_SUPPLIED_BLOCKCHAIN_SOURCE_BATCH_2026_08_21.md`](./USER_SUPPLIED_BLOCKCHAIN_SOURCE_BATCH_2026_08_21.md).

Detailed X1 whitepaper provenance: [`X1_BLOCKCHAIN_WHITEPAPER_V1_0.md`](./X1_BLOCKCHAIN_WHITEPAPER_V1_0.md).

## Pending / unaccepted source

### XenBlocks PoW documentation — PR #141

Status: **P1 blocked / not accepted**.

The current branch ingests an LF-normalized derivative instead of preserving/hashing the exact uploaded CRLF bytes as the canonical Phase 1 artifact.

Acceptance requires the original uploaded UTF-8 bytes to be the canonical retained artifact/content identity; any LF form may be a derived parsing representation only. Exact-head CI, independent review, and merge remain required after the provenance fix.

Until then XenBlocks PoW material must not be listed as an accepted Learning System source.

## MB4E source and curriculum relationship

The accepted `mastering_blockchain_4e_2023` source contract is distinct from every Pyramid exercise bank derived from it.

Pyramid questions, expected answers, reasoning points, grader notes, scores, supplemental practice, and learned concepts are transformed training/evaluation material. They are **not source evidence**.

### Accepted legacy provenance migration

Issue #178 / PR #179 accepted the migration of the historical MB4E Level 1 package to canonical source binding without rewriting its historical exercise semantics or checkpoints.

The accepted migration preserves explicit PDF-page basis. PDF page coordinates are not relabeled as printed book pages.

### Accepted PDF alignment / retrieval scope

For supported MB4E remediation ranges, repository metadata binds PDF-page -> transcript-line alignment to exact PDF/transcript hashes. Provenance scope is resolved before retrieval/ranking, and selected chunks/evidence anchors must be fully contained in the declared range.

This metadata strengthens evidence scope; it does not make the source current/live truth.

## MB4E frozen source mastery plan

The accepted source-specific planner maps the full book into **14 required source stages** using global Pyramid capabilities:

```text
1,2,3,4,5,6,7,8,9,10,11,13,14,17
```

Explicitly excluded for this source:

```text
12,15,16,18,19,20
```

Every required stage uses the current 300-question canonical exam contract and the final source capstone remains required.

Accepted curriculum-bank construction currently reaches:

- Stage 1 Fundamentals — historical Level 1/provenance foundation;
- Stage 2 Blockchain Mechanics — 1,206 questions;
- Stage 3 Transactions;
- Stage 4 Cryptography — 415 questions;
- Stage 5 Smart Contracts — 493 questions;
- Stage 6 Tokenomics — 493 questions.

These banks are derived learning material. Their existence does not establish that Roberta has passed/mastered those stages.

## PDF transcript rule

For PDF-derived sources, the repository may preserve a deterministic transcript as a derived ingestible artifact under an accepted extraction profile. Transcript provenance must remain distinguishable from the original PDF artifact/provenance; no transcript may masquerade as byte-identical PDF content.

## Plain UTF-8 upload rule

For an original UTF-8 text/Markdown upload, Phase 1 requires exact uploaded bytes to be retained and hashed. Line-ending normalization may support downstream parsing, but it cannot replace the canonical original artifact unless a separately accepted source contract explicitly defines the derivative as the source.

## Live-state boundary

Even an accepted `primary` static source may contain statements that later become stale. Static authority classification never means live-state authorization.

When a question depends on current state, Roberta must use the authorized current-evidence path rather than relying on this registry, a book, a whitepaper, Pyramid state, learned concepts, or cached source text.
