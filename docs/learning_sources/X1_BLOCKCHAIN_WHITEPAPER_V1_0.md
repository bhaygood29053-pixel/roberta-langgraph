# X1 Blockchain Whitepaper v1.0 — Learning System Source Manifest

Status: approved static Learning System source onboarding for Issue #137.

## Source identity

- Formal title: **X1 Blockchain: Architecting Economic Efficiency in Layer-1 Protocol Design**
- Publisher: **X1 Labs**
- Authors: **Jack Levin and Axel Eckerbom**
- Whitepaper version: **v1.0**
- Publication date shown by the supplied document: **January 2025**
- Supplied PDF page count: **13**
- Supplied PDF SHA-256: `a9023893572e057c62628c50e3fd9c3827fe6eec88ae8862e318375233a7e316`

The PDF was supplied directly by the user for Learning System onboarding. The current accepted Learning System parser profile is UTF-8 Markdown, not PDF. This source package therefore does **not** claim that the PDF binary itself has been ingested through Phase 1 or parsed through Phase 2.

## Ingestible artifact

The ingestible artifact is the deterministic concatenation, in numeric order, of:

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

The user request to add the supplied whitepaper is the approval basis for this source onboarding. This approval applies to inclusion as static source material; it does not grant the document any live-state or execution authority.

## Authority boundary

The whitepaper contains design and protocol claims about X1 Blockchain, including validator economics, leader selection, consensus, dynamic base fees, staking-related fee adjustments, MEV handling, and transaction-thread scheduling.

These are static source claims. They must not be treated as authoritative evidence for current:

- token price, liquidity, volume, supply, burns, holders, or wallet state;
- current validator counts, stake distribution, Nakamoto coefficient, or live performance;
- current transaction fees, fee parameters, block capacity, or active implementation status;
- current authorities, current risk scores, or current CMIS/provider capability state.

Fresh accepted X1 Scout -> CMIS -> X1 Provider evidence remains authoritative for freshness-sensitive state.

## Non-goals

This source onboarding does not add a general PDF parser, OCR pipeline, PDF structure contract, semantic figure interpreter, HXMP promotion path, CMIS trust change, or Controlled Execution capability.
