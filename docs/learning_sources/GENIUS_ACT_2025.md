# GENIUS Act 2025 — Learning System Source Manifest

Issue: ROBERTA #363

Status: **candidate source on the #363 implementation branch; not accepted on
main until review/merge and source-integrity acceptance.**

## Identity

- Formal title: Guiding and Establishing National Innovation for U.S. Stablecoins Act
- Short title: GENIUS Act
- Public Law: 119-27
- Approved: July 18, 2025
- Primary publisher/source: U.S. Government Publishing Office / GovInfo
- Canonical record: https://www.govinfo.gov/app/details/PLAW-119publ27
- Statutory citation: 139 Stat. 419

## Learning classification

```text
authority_class = primary
knowledge_scope = static_regulatory_framework
live_state_authority = false
cmis_override_authorized = false
compliance_conclusion_authorized = false
execution_authorized = false
```

The public shell stores only this source manifest. The actual Learning Plane source binding and ingestible source bytes belong in the protected `roberta-core` repository under the Phase 6 ownership boundary.

The protected implementation must bind an exact GovInfo artifact before source ingestion. A summary or public-shell Markdown capsule is not allowed to masquerade as the primary-law artifact.

## Freshness boundary

The law's identity and enacted text are static. Current regulator rulemaking,
issuer status, license status, reserve disclosures, asset/bridge identity, and
other changing facts must come from current accepted sources, with CMIS
remaining the verified evidence authority for ROBERTA-facing operational use.

## First proof case

The first reasoning fixture distinguishes USDC from USDC.X. It explicitly
prevents underlying-asset evidence from erasing bridge/custody dependencies.

## Non-goals

This onboarding does not provide legal advice, decide compliance, authorize
transactions, or promote `regulatory_evidence/v1` as a live public CMIS
service.
