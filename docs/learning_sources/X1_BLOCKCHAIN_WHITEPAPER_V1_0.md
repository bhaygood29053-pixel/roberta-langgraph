# X1 Blockchain Whitepaper v1.0 — Learning System Source Manifest

Last reconciled: 2026-08-26 (America/New_York)

Status: **accepted static Learning System source onboarding for Issue #137.**

## Source identity

- Formal title: **X1 Blockchain: Architecting Economic Efficiency in Layer-1 Protocol Design**
- Publisher: **X1 Labs**
- Authors: **Jack Levin and Axel Eckerbom**
- Whitepaper version: **v1.0**
- Publication date shown by the supplied document: **January 2025**
- Supplied PDF page count: **13**
- Supplied PDF SHA-256: `a9023893572e057c62628c50e3fd9c3827fe6eec88ae8862e318375233a7e316`

The PDF was supplied directly by the user for Learning System onboarding. This source's **curated package loader** uses a pinned UTF-8 Markdown transcription rather than directly ingesting the PDF through the original Phase 1 text-source path. This source package therefore does **not** claim that the PDF binary itself was the Phase 1 stored text artifact for this curated onboarding.

Merged PR #228 later added a separate autonomous local-source path that can accept a selected PDF directly, preserve/hash the original PDF, and deterministically extract pages for source mastery. That newer generic intake path does not retroactively change this whitepaper package's established PDF/transcript provenance contract.

## Ingestible artifact

The ingestible artifact for this curated source package is the deterministic concatenation, in numeric order, of:

- `src/roberta/learning/sources/x1_blockchain_whitepaper_v1_0.part0.md`
- `src/roberta/learning/sources/x1_blockchain_whitepaper_v1_0.part1.md`
- `src/roberta/learning/sources/x1_blockchain_whitepaper_v1_0.part2.md`
- `src/roberta/learning/sources/x1_blockchain_whitepaper_v1_0.part3.md`

Together these resources form one normalized UTF-8 Markdown transcription of the supplied document. The SHA-256 over the exact concatenated UTF-8 bytes is:

`6e98dc574d252f4d74f45eda1823b3fd8b050760fa7f1a00b8d5e2e567cd57ec`

The transcript preserves the source title, authors, version/date information, section hierarchy, body text, bullets, figure captions, and references. PDF line wrapping and line-break hyphenation are normalized for deterministic Markdown parsing and chunking. Figure artwork is not converted into generated prose; only source-visible captions are retained in the transcript.

The runtime loader pins both the transcript digest and supplied-PDF digest so a packaged transcript mismatch fails closed before source ingestion.

## Learning System classification

The source is ingested as:

```text
authority_class = primary
approval_status = approved
status = approved
knowledge_scope = static_architecture_and_protocol_design
```

The original user request to add the supplied whitepaper is the approval basis for this source onboarding. This approval applies to inclusion as static source material; it does not grant the document any live-state or execution authority.

## Authority boundary

The whitepaper contains design and protocol claims about X1 Blockchain, including validator economics, leader selection, consensus, dynamic base fees, staking-related fee adjustments, MEV handling, and transaction-thread scheduling.

These are static source claims. They must not be treated as authoritative evidence for current:

- token price, liquidity, volume, supply, burns, holders, or wallet state;
- current validator counts, stake distribution, Nakamoto coefficient, or live performance;
- current transaction fees, fee parameters, block capacity, or active implementation status;
- current authorities, current risk scores, or current CMIS/provider capability state.

Fresh accepted X1 Scout -> CMIS -> X1 Provider evidence remains authoritative for freshness-sensitive state.

## Non-goals

This curated source onboarding does not itself add a general PDF parser, OCR pipeline, semantic figure interpreter, HXMP promotion path, CMIS trust change, or Controlled Execution capability.

The separate accepted autonomous PDF intake from PR #228 remains subject to its own immutable source/provenance, no-OCR-only, source-mastery, and authority-boundary contracts.
