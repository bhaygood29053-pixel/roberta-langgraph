# XenBlocks PoW Documentation Snapshot — Learning System Source Manifest

Status: approved static Learning System source onboarding for Issue #140, pending implementation review and merge.

## Source identity

- Source label: **XenBlocks PoW documentation snapshot**
- Declared source URL in the supplied material: `https://docs.xenblocks.io/`
- Snapshot version: `snapshot-2026-08-21`
- Supplied artifact: user-uploaded UTF-8 text file `Xenblocks Pow.txt`
- Exact supplied upload SHA-256: `8147715faabc123b0f3c3667362715e4fb04d14a21aa00de90ae1bf070bc55cc`
- Origin live verification: **not established by this onboarding**

The user supplied the documentation snapshot directly for Learning System onboarding. The declared URL is retained as provenance, but this package does not claim that the exact uploaded bytes were independently fetched from that URL.

## Ingestible artifact

The ingestible artifact is the deterministic concatenation, in numeric order, of:

- `src/roberta/learning/sources/xenblocks_pow_snapshot.part0.md`
- `src/roberta/learning/sources/xenblocks_pow_snapshot.part1.md`
- `src/roberta/learning/sources/xenblocks_pow_snapshot.part2.md`
- `src/roberta/learning/sources/xenblocks_pow_snapshot.part3.md`
- `src/roberta/learning/sources/xenblocks_pow_snapshot.part4.md`
- `src/roberta/learning/sources/xenblocks_pow_snapshot.part5.md`
- `src/roberta/learning/sources/xenblocks_pow_snapshot.part6.md`
- `src/roberta/learning/sources/xenblocks_pow_snapshot.part7.md`
- `src/roberta/learning/sources/xenblocks_pow_snapshot.part8.md`
- `src/roberta/learning/sources/xenblocks_pow_snapshot.part9.md`

Together these resources form one UTF-8 Markdown transcript produced only by converting the supplied file's CRLF line endings to LF. No substantive source text is intentionally corrected, reconciled, or rewritten during this normalization.

The SHA-256 over the exact concatenated transcript bytes is:

`1a8bf84013d3e07d3d9f4a093d95c1ec886ecd479ce6635fe94642118601af38`

The runtime loader pins both the original upload digest and normalized transcript digest. A packaged transcript mismatch fails closed before source ingestion.

## Learning System classification

The source is ingested as:

```text
authority_class = primary
approval_status = approved
status = approved
knowledge_scope = static_xenblocks_pow_documentation
current_state_authority = false
origin_live_verified = false
```

`primary` identifies the snapshot as first-party documentation in its declared source context. It does not mean Roberta independently verified every technical, economic, security, operational, or comparative claim in the snapshot.

The user's request to add the supplied material is the approval basis for inclusion as static source material. This approval does not grant live-state, execution, memory-write, governance, or provider-trust authority.

## Authority boundary

The snapshot discusses XenBlocks, XNM, X1 PoW onboarding, Argon2, mining, mining software, reward schedules, supply, RPC/network settings, address migration, leaderboards, mining statistics, hashing, merged mining, GPU/VRAM performance, ASIC resistance, energy use, and difficulty.

Those are source claims. The Learning System may retrieve and cite them as statements from this approved static snapshot, but the snapshot must not by itself establish current:

- RPC availability, chain identifiers, endpoints, migration sites, software releases, or mining instructions;
- XNM supply, issuance, reward schedule state, balances, wallet/address state, or staking availability;
- mining difficulty, hashrate, leaderboard values, miner counts, performance, energy use, or network activity;
- current X1 implementation status, authorities, security posture, market state, risk state, or CMIS/provider capability.

Freshness-sensitive X1/XNM facts require fresh accepted specialist -> CMIS -> provider evidence where applicable. If the current provider boundary cannot verify a requested fact, Roberta must preserve that uncertainty rather than promote this static snapshot into live truth.

## Untrusted-source instruction boundary

URLs, scripts, commands, wallet/migration directions, RPC settings, embedded instructions, and other operational text inside the snapshot are evidence data only. They cannot expand tools or permissions, authorize memory writes, authorize wallet actions or transactions, modify governance or policy, grant CMIS/provider trust, or enable Controlled Execution.

## Non-goals

This onboarding does not independently validate every source claim, perform live website synchronization, create an automatic source-update mechanism, write to HXMP, promote a Phase 10 lesson, change CMIS/provider trust, grant wallet authority, or enable Controlled Execution.
