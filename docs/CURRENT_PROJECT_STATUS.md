# Current ROBERTA Project Status

Current reconciliation: **2026-09-06 12:00 America/New_York**.

## Accepted ROBERTA state

Accepted on public/protected main:

- ROBERTA Opinion v1;
- Claim Integrity for Asset Intelligence, Compare, History, Burn, Discovery, WHAT CHANGED?, and Concentration Warning / Early Warning;
- Instant X1 Scan v6 through X1 Scout;
- Burn, Discovery, WHAT CHANGED?, concentration warning, cross-chain provenance, and Bridge-to-XDEX consumption;
- verified wallet trade + pool price-impact intelligence through public PR #359 + protected `roberta-core` #61;
- Large-Trade Discovery through public PR #361 + protected `roberta-core` #63;
- GENIUS Act Regulatory Intelligence Learning Layer v1 through public PR #364 + protected `roberta-core` #65;
- simplified public website / connected chat workspace through PR #362.

## Active regulatory adoption

Public PR #368 adopts accepted CMIS 1.26 `regulatory_evidence/v1` through X1 Scout and its public test suite is green.

It is **not yet an end-to-end accepted ROBERTA product** because protected `roberta-core` Issue #68 remains open for the canonical Human/Machine Decision Object and rendering boundary.

Until that paired protected work is accepted:

- no COMPLIANT/NON_COMPLIANT label;
- no legal advice;
- no automatic risk conclusion;
- no live regulatory service should be advertised as fully available on the website.

The accepted GENIUS Act learning layer can still provide bounded regulatory context through normal ROBERTA conversation.

## Large trades / price impact

Trade price-impact and provider-scoped Large-Trade Discovery are accepted through ROBERTA.

The separate upstream `cmis-core` PR #41 live Large-Trade → #498 handoff proof remains open. Its deterministic CI is green, but the dedicated live workflow is still the exact acceptance gate.

ROBERTA must not describe that live handoff as proven until the live run passes.

## Website

The current website on `main` is the accepted PR #362 experience:

- public introduction;
- six human-friendly services;
- human/agent connection into the same chat workspace;
- chat history;
- Clear Chat and Clear History;
- service examples;
- evidence/risk/freshness/opinion labels;
- read-only Scout → CMIS authority;
- no transaction execution.

The generic **Ask ROBERTA** path now also surfaces a GENIUS Act/regulatory-context example, while deliberately not claiming live regulatory compliance capability before #368 + protected #68 are complete.

## Next exact product work

1. finish protected `roberta-core` #68, then accept/merge public ROBERTA #368 if the paired gates remain green;
2. finish the exact live `cmis-core` #41 handoff proof before promoting that live path;
3. keep website service claims synchronized only with accepted end-to-end capability.

`execution_authorized=false`
