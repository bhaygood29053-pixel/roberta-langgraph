# CMIS Roadmap Sync — refreshed 2026-08-20

This document is Roberta's current integration snapshot of **CMIS — Cross-Chain Market Intelligence Service**. It is a consumption guide for Roberta and Chain Scouts, not a second CMIS roadmap and not authority to promote unaccepted CMIS work.

## Source-of-truth rule

CMIS remains authoritative for freshness-sensitive market, tokenomics, verification, provenance, proof quality, deterministic risk, historical intelligence, bounded pre-trade facts, and accepted read-only intelligence-service outputs. Roberta may interpret accepted results but must not manufacture stronger facts, recompute CMIS proof/risk, or infer capability from draft work.

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

## Current project position

- **Roberta Phase 10 — More Specialists / Providers: complete.**
- **Roberta Post-Phase-10 Evidence-Aware Intelligence & User Experience: complete.**
- **CMIS Phase 10 — Solana read-only provider foundation: complete.**
- **CMIS Evidence Receipts + Proof Score: complete.**
- **CMIS X1 evidence-capability boundary: complete and fail-closed.**
- **CMIS deterministic pre-trade trade-size analysis: complete.**
- **CMIS Phase 11 — read-only Verified Intelligence foundation: complete.**
- **CMIS Phase 12 — `concentration_change_intelligence/v1`: accepted as the first promoted X1-only read-only intelligence service.**
- **Roberta Phase 11 — Controlled Execution: locked / not started.**

CMIS and Roberta use different phase numbering. CMIS Phase 12 does not imply Roberta Controlled Execution.

## Shared Scout / CMIS architecture

```text
Roberta
  ├── X1 Scout -> CMIS -> X1 / XDEX providers
  └── Solana Scout -> CMIS -> Solana providers
```

Do not duplicate CMIS per chain. The Scout → CMIS boundary is guarded by `GET /v1/cmis/capabilities`.

The accepted boundary now requires capability schema `1` and **CMIS contract `1.9.0` or compatible newer**. Missing, malformed, incompatible, or non-callable state fails closed.

## Shared service contract

The CMIS public service surface includes, subject to per-chain capability state:

- `asset_lookup`;
- `market_report`;
- `rank`;
- `historical_compare`;
- `tokenomics`;
- `risk_check`;
- `pre_trade_check`;
- `verification_evidence`;
- `concentration_change_intelligence`.

A service appearing in the shared contract does not imply every chain supports it or that every Scout may invoke it autonomously.

## X1 status

X1 is the more mature CMIS surface, but evidence completeness remains fact- and scope-specific. Roberta preserves verified/bounded/partial/unavailable/conflict/insufficient-evidence states rather than treating Scout availability as global completeness.

CMIS Phase 12 promotes for X1:

```text
service: concentration_change_intelligence
contract: concentration_change_intelligence/v1
accepted conclusion: top_account_concentration_change
state: bounded
callable: true
read_only: true
public_service_promoted: true
scout_reliance_promoted: true
execution_authorized: false
```

The trust root is canonical CMIS-owned intelligence evidence addressed by exact `intelligence_evidence_id`, not caller-supplied proof objects. The service preserves top-token-account scope and does not establish unique holders or beneficial owners. Optional explicit/versioned concentration-threshold policy is deterministic policy evaluation, not risk or behavioral interpretation.

## Solana status

Solana Phase 10 is complete as a bounded read-only provider/Scout path with exact identity, SPL Token/Token-2022 handling, configured Jupiter/Helius/DEX Screener evidence, cross-source checks, provenance-safe history, and capability-gated services.

Solana is not assumed to have X1 parity. The new `concentration_change_intelligence` service is explicitly **unavailable/non-callable on Solana** with public/Scout promotion false and `execution_authorized=false`. No Solana request may fall back to X1.

## Verification evidence and proof quality

Roberta has an accepted constrained `verification_evidence` path. Roberta and Chain Scouts preserve verification state, Evidence Receipt provenance, Proof Score, scope, freshness, disagreements, limitations, unresolved fields, data-quality reasons, and promotion state.

Risk and proof quality remain separate dimensions.

## Phase 11 foundation vs Phase 12 promotion

The Phase 11 `intelligence_foundation` remains read-only and **unpromoted as a whole**:

```text
public_service_promoted = false
scout_reliance_promoted = false
```

Phase 12 does not widen that foundation. It promotes exactly one separately contracted X1 service. Broader concentration snapshots, wallet activity, generic sanitized history, generic evidence-bound conclusions, public intelligence-evidence storage/upload, and generic `verified_intelligence` remain non-public/non-automatic.

Roberta must not infer insider, whale, bot, accumulator, distributor, market-maker, manipulator, ownership, relationship, or intent labels from the Phase 11 foundation or the Phase 12 concentration-change service.

## Evidence-aware Roberta behavior

The Post-Phase-10 evidence-aware UX milestone remains complete. Roberta uses answer-first synthesis while preserving CMIS facts, proof, risk, policy observations, and missing evidence as separate concepts. Cross-chain evidence may be compared but not merged into a synthetic proof/risk/safety grade.

## Pre-trade analysis status

The deterministic trade-size milestone previously tracked as CMIS Issue #99 is complete. Advanced execution-related fields remain evidence-gated. Missing evidence remains unavailable and is never converted into zero or an LLM estimate.

```text
analysis_only = true
execution_authorized = false
```

A CMIS `PASS` is not permission to trade.

## Memory, policy, and approval boundaries

```text
HXMP / durable memory -> stable context and explicit policy
CMIS                  -> current verified facts and evidence
Policy code           -> deterministic rule result
LLM                    -> explanation / synthesis only
```

Fresh accepted CMIS/provider evidence overrides remembered/checkpointed live-market snapshots. Human approval remains exact-proposal review, not a reusable signing credential.

## Controlled Execution remains locked

Roberta Phase 11 Controlled Execution has **not started**. No current CMIS/Scout result—including Phase 12 concentration intelligence—Roberta policy decision, or human-review state authorizes transaction preparation as an execution path, wallet signing, broadcasting, custody, live swaps, autonomous trading, bridge/value transfer, or autonomous value movement.

## Current coordination rule

```text
CMIS
  -> deepen verified X1/Solana evidence
  -> promote future intelligence services only through explicit service-specific contracts
  -> preserve Phase 11 foundation non-promotion
  -> keep execution unauthorized

Roberta
  -> consume capability-gated X1/Solana Scout results
  -> preserve Evidence Receipts / Proof Scores / risk / policy distinctions
  -> never infer cross-chain capability parity
  -> keep Controlled Execution locked
```

## Core integration principle

**CMIS determines what verified evidence supports now.**

**Chain Scouts determine what those accepted CMIS facts mean within their respective chains.**

**Roberta determines what those specialist findings mean for the user and across chains, subject to policy and approval boundaries.**
