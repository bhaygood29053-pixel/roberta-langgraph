# Roberta Learning System — Static Source Registry

Last reconciled: 2026-08-23 (America/New_York)

This registry records human-readable source-onboarding status. Runtime truth still comes from the exact source contracts and code on `main`; this document does not promote an unmerged source or create live-state authority.

## Authority rule

Static Learning System sources are evidence/knowledge inputs only. They do not become authoritative for freshness-sensitive prices, liquidity, supply, wallet state, validator state, provider health, fees, software versions, token authorities, risk, or other changing blockchain state.

Fresh accepted chain evidence follows:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider
```

Source text is always treated as data, never as a permission layer. Embedded instructions cannot authorize tools, credentials, memory writes, governance changes, wallet actions, transactions, or Controlled Execution.

## Accepted sources on `main`

| Source key / source | Status | Static source role | Notes |
| --- | --- | --- | --- |
| `x1_blockchain_whitepaper_v1_0` / X1 Blockchain Whitepaper v1.0 | Accepted | Primary static protocol/architecture documentation | Onboarded by PR #138. Static provenance does not establish current X1 runtime/market state. |
| XDEX documentation snapshot | Accepted | Static documentation snapshot; authority class remains bounded by its accepted source contract | Onboarded in PR #147. Contradictory source statements remain visible rather than silently reconciled. |
| XEN Litepaper v1.7 | Accepted | Primary static project documentation | Onboarded in PR #147 from deterministic PDF transcript provenance. |
| XEN Torrent / XENFT Litepaper v0.3 | Accepted | Primary static project documentation | Onboarded in PR #147 from deterministic PDF transcript provenance. |
| XONE ERC20 Token v4 | Accepted | Static documentation with unknown/bounded source authority pending any stronger independent publisher/origin proof | Onboarded in PR #147. Source inclusion is not provider/live-state verification. |
| `mastering_blockchain_4e_2023` / *Mastering Blockchain, Fourth Edition* | Accepted external integrity contract | Secondary educational reference | Onboarded in PR #147. The full copyrighted transcript is not republished; callers must supply exact bytes matching the pinned transcript contract. |
| Solana whitepaper v0.8.13 | Accepted | Primary static protocol documentation | Onboarded in PR #147 from deterministic PDF transcript provenance. |

Detailed accepted provenance for the six-source batch is in [`USER_SUPPLIED_BLOCKCHAIN_SOURCE_BATCH_2026_08_21.md`](./USER_SUPPLIED_BLOCKCHAIN_SOURCE_BATCH_2026_08_21.md).

Detailed X1 whitepaper provenance is in [`X1_BLOCKCHAIN_WHITEPAPER_V1_0.md`](./X1_BLOCKCHAIN_WHITEPAPER_V1_0.md).

## Pending / unaccepted sources

### XenBlocks PoW documentation — PR #141

Status: **pending / P1 blocked / not accepted on `main`**.

The source onboarding currently fails the Phase 1 exact-byte contract because the implementation ingests an LF-normalized derivative instead of preserving/hashing the exact uploaded CRLF bytes as the canonical source artifact.

Acceptance requires:

1. exact uploaded UTF-8 bytes retained as the canonical artifact;
2. `content_hash` / `artifact_ref` derived from those exact bytes;
3. any LF-normalized representation treated only as a derived parsing artifact;
4. exact-head deterministic CI;
5. independent review with no blocker;
6. merge to `main`.

Until then XenBlocks PoW material must not be listed as an accepted Learning System source.

## MB4E curriculum/provenance relationship

The accepted `mastering_blockchain_4e_2023` source contract is distinct from any Pyramid curriculum package derived from that source.

Pyramid exercises are transformed training/evaluation material and are not source evidence. They may contain source references/locators, but expected answers, reasoning points, grader notes, scores, and practice questions do not become source truth.

PR #179 proposes a migration of the legacy MB4E Level 1 curriculum package to stronger canonical source binding while preserving historical semantic identity and explicit PDF-page coordinate basis. That migration remains unaccepted until its open review findings are fixed and the PR merges.

## PDF transcript rule

For PDF-derived sources, the repository may preserve a deterministic transcript as a derived ingestible artifact under the accepted extraction profile. Transcript provenance must remain distinguishable from the original PDF artifact/provenance; no transcript is allowed to masquerade as byte-identical PDF content.

## Plain UTF-8 upload rule

For an original UTF-8 text/Markdown upload, Phase 1 requires the exact uploaded bytes to be retained and hashed. Line-ending normalization may be useful downstream, but it cannot replace the canonical original artifact unless a separate accepted source contract explicitly defines that derivative as the source being onboarded.

## Live-state boundary

Even an accepted `primary` static source may describe values or configuration that later change. Static authority classification does not mean live-state authorization.

When a question depends on current state, Roberta must use the authorized current-evidence path rather than relying on this registry, a book, a whitepaper, Pyramid memory, or cached source text.
