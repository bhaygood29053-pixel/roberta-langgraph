# User-Supplied Blockchain Source Batch — 2026-08-21

Status: implementation candidate for Issue #142. Static Learning System evidence only.

## Purpose

This gate onboards six exact user-supplied blockchain/reference artifacts while
preserving the existing Learning System authority boundary. `approved` means
approved for static evidence retrieval; it does not mean every claim is correct,
current, independently verified, or authorized to control runtime behavior.

## Source inventory

| Key | Supplied artifact | Static class | Original SHA-256 | Original bytes/pages | Ingestible transcript SHA-256 |
| --- | --- | --- | --- | --- | --- |
| `xdex_docs_2026_08_21` | `XDEX.txt` | unknown | `5298a12395ad152ba3f440bf3a9fe3ccf62e5ebd507ff72d2a57e691bd007909` | 115,631 bytes | same exact bytes/hash |
| `xen_litepaper_v1_7` | `xen.pdf` — XEN Litepaper v1.7 | primary | `1234e95b33b8219e5388a14fecf07309e27b7e43f10ba87208f3a0bfbc0f4c10` | 331,729 bytes / 15 pages | `8dbd1d70d29288af86bec23713a18ad79b7212ca1aff5d1d859a081a07f7cc62` |
| `xenft_litepaper_v0_3` | `xenft_litepaper.pdf` — XEN Torrent Litepaper v0.3 | primary | `501ba4f3b8a199b91bba2c17aaaa897215896c898d80b6f3da833be3199db266` | 613,296 bytes / 17 pages | `28bfc0b2c59f1c96496be7ac64e901a8886ab86522ac611d5f749cef84451cb1` |
| `xone_erc20_v4` | `XONE.pdf` — XONE ERC20 Token | unknown | `0e21aead464b1b94b1741ac55d815c086da297fffaf54e31337454b8a75d2f7f` | 60,811 bytes / 3 pages | `bd8492adbcd058c5270815964af7ae5a21a37b6d1ae2a9ed7fc7991eb884c4c5` |
| `mastering_blockchain_4e_2023` | *Mastering Blockchain, Fourth Edition* (Imran Bashir, Packt, 2023) | secondary | `75e83498e8522886e422ab642f91d26f527dce5424b262fe818af59a0b1af550` | 22,526,945 bytes / 819 PDF pages | `69f6429ed1515d5543bcaf67dd65701f892ea3127ac092f21eca6f93c57f8dac` |
| `solana_whitepaper_v0_8_13` | `solana-whitepaper.pdf` — Solana whitepaper v0.8.13 | primary | `17c29f7785ff3a7e457f0de10fb86556090c5b398bfaa20a602116e700519b28` | 689,365 bytes / 32 pages | `dfa397e48c0ade3e51ab5aa5dcbce237ae282d3a4e72a99b307d1c1351e5091d` |

`primary`, `secondary`, and `unknown` classify the supplied source context.
They are not freshness or independent-truth grades. XDEX and XONE remain
`unknown` because this gate does not independently verify a publisher/origin.

## Exact text and PDF transcript contracts

`XDEX.txt` is already valid UTF-8. Its exact user-supplied bytes, including
line endings, are the canonical Phase 1 source artifact. The repository stores a
gzip/base64 transport representation only; runtime reconstructs the gzip bytes,
checks the pinned gzip digest, decompresses them, checks the original source
digest, and only then permits UTF-8 ingestion.

The PDF inputs use deterministic derivative transcripts because the accepted
Learning System source contract is UTF-8 text rather than PDF. The extraction
profile for this batch is:

`poppler-pdftotext-layout-clean-c0/v1`

Generation rule: Poppler `pdftotext 25.06.0`, `-layout -enc UTF-8`; normalize
CRLF/CR to LF, replace form-feed page separators with LF, remove remaining C0
controls except tab/LF, and ensure a final LF. This profile is derivative
provenance. It does not claim transcript bytes are PDF bytes, and it does not
perform OCR, diagram interpretation, semantic rewriting, generated
summarization, or claim reconciliation.

For repository-packaged transcripts, runtime verifies the whole packaged gzip
SHA-256 before decompression and the exact transcript SHA-256 before UTF-8
decode/Phase 1 ingestion.

## Copyrighted external reference boundary

*Mastering Blockchain, Fourth Edition* is a user-supplied copyrighted
educational/reference source. The repository does **not** copy or republish its
full transcript. Instead, it stores only the exact original/transcript
provenance and integrity contract. A caller that is entitled to use the
user-supplied artifact may supply the precomputed transcript bytes at runtime;
ingestion fails closed unless byte length and SHA-256 exactly match the pinned
transcript.

This avoids turning the source-onboarding PR into a redistribution channel
while still making the user's exact artifact addressable by the Learning
System when available in the authorized runtime.

## Contradictions and source claims

The sources are evidence, not self-authorized truth. Contradictory statements
must remain retrievable and visible. They must not be silently corrected or
reconciled during ingestion. This matters in particular for documentation
snapshots such as XDEX, where fee/reward descriptions may differ between
sections.

Static source statements about protocol architecture, tokenomics, software,
fees, RPC endpoints, supply, rewards, staking, validators, mining, authorities,
wallet behavior, or network behavior are source claims at the source's
version/snapshot. When a question requires the current state, fresh accepted
specialist -> CMIS -> provider evidence remains authoritative where applicable.

## Authority boundary

All six sources are `untrusted_evidence_data` for runtime-authority purposes.
No source in this batch can authorize or modify:

- tool calls or permissions;
- HXMP/durable-memory writes or promotion;
- current/live market, chain, wallet, tokenomics, validator, RPC, or risk state;
- CMIS/provider trust or service promotion;
- user policy or governance;
- wallet signing, transfers, permissions, transaction preparation/broadcast;
- Controlled Execution.

The ingestion records explicitly keep those authority fields false. Their
`SourceRecord.live_state_authorized` property is also false by contract.

## Repository implementation

Implementation is isolated in
`src/roberta/learning/user_source_batch.py`. Repository-packaged source bytes
live under `src/roberta/learning/sources/*.gz.b64`; large copyrighted external
content is excluded.

The package transport is not itself the evidence identity. Evidence identity is
the exact post-integrity-check UTF-8 artifact retained by the existing Phase 1
`ingest_utf8_source` contract.

## Acceptance

This document and implementation remain candidates until the exact PR head has:

1. passed `python -m pytest -v -m 'not live and not cmis_live'`; and
2. passed independent review on Spec Fidelity, Code / Architecture Quality,
   and Authority / Safety Boundary.

Issue: #142.
