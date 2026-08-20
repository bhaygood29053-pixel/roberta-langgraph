# Roberta LangGraph

Roberta is the top-level Oracle, policy-aware coordinator, and normal user-facing voice for the multi-agent system.

Current accepted hierarchy:

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider
```

Current chain specialists:

```text
Roberta
  ├── X1 Scout
  │     -> CMIS -> X1/XDEX providers
  └── Solana Scout
        -> CMIS -> Solana providers
```

Roberta does not call provider APIs directly and does not reproduce CMIS market, risk, verification, evidence-receipt, proof-score, or deterministic pre-trade calculations.

## Repository boundary

CMIS is maintained in the separate GitHub repository:

```text
bhaygood29053-pixel/cmis
```

That repository was historically named `liquidity-scout`. The canonical project identity is now **CMIS — Cross-Chain Market Intelligence Service**.

The CMIS implementation still uses the internal Python namespace `liquidity_scout` for compatibility. Repository identity and Python package identity are intentionally separate during the staged migration.

## Current roadmap status

- Phase 1 Core Agent Loop — complete
- Phase 2 Provider-Neutral Model Loop — complete
- Phase 3 X1 Scout Boundary — complete
- Phase 4 CMIS / X1 Provider Integration — complete
- Phase 5 X1 Evidence Completeness — bounded by explicit CMIS capability states
- Phase 6 Agentic X1 Scout Planning — complete
- Phase 7A Thread / Checkpoint Persistence — complete
- Phase 7B HXMP Durable Memory — complete
- Phase 8 Oracle Policy — complete
- Phase 9 Human in the Loop — complete
- Phase 10 More Specialists / Providers — complete
- Post-Phase-10 Evidence-Aware Intelligence & User Experience — complete
- first promoted CMIS 1.9 X1 Verified Intelligence adoption/readiness — complete
- Solana Read-Only Production Readiness — complete for the exact currently accepted Scout surface
- CMIS deterministic descriptive classification foundation — complete, internal/non-promoted
- CMIS deterministic wallet-relationship evidence foundation — complete, internal/non-promoted with explicit non-ownership semantics
- next shared read-only intelligence milestone — evidence-backed alert contracts
- Phase 11 Controlled Execution — **locked / not started**

See [`docs/LANGGRAPH_ROADMAP.md`](./docs/LANGGRAPH_ROADMAP.md) for the authoritative Roberta roadmap.

CMIS has its own phase numbering. CMIS Phase 11 refers to its completed **read-only Verified Intelligence foundation**; that is separate from Roberta Phase 11 Controlled Execution.

## Evidence-aware intelligence

Roberta consumes the CMIS evidence-quality and capability contracts.

Chain Scout reports preserve CMIS evidence context including, where available:

- verification status;
- proof strength and category reasons;
- evidence scope;
- freshness;
- source disagreements;
- limitations;
- unresolved fields;
- source provenance;
- risk separately from proof strength.

Roberta requires the CMIS capability manifest to advertise the accepted evidence receipt/proof-score contract and the read-only intelligence-foundation boundary required by the current Scout client.

Provider-reported information remains provider-reported until CMIS records independent verification. Missing evidence remains unknown/unproven.

Detailed behavior is documented in [`docs/EVIDENCE_AWARE_INTELLIGENCE.md`](./docs/EVIDENCE_AWARE_INTELLIGENCE.md).

## Answer-first user experience

Recommendation-style responses prioritize:

1. conclusion / recommendation / blocker;
2. the most important evidence-backed reasons;
3. risk when CMIS actually provides a dedicated risk level;
4. evidence quality / proof strength;
5. important missing evidence;
6. deeper technical evidence on request.

Pre-trade responses use deterministic finalization rather than passing the structured result through a second free-form rewrite.

`PASS`, `WARN`, and `BLOCK` are not automatically HIGH/MEDIUM/LOW risk levels. If CMIS does not provide a dedicated risk level, Roberta keeps risk unknown rather than inventing one.

## Recommendation evidence planning

Roberta deterministically identifies evidence needs for common questions such as:

- buy/sell recommendations;
- trade-size questions;
- safer-asset comparisons;
- what-changed questions;
- liquidity-risk questions;
- LP questions;
- price-move questions.

Chain Scouts incorporate allowed read-only evidence requirements into their deterministic planning. Recommendation wording cannot silently enable execution capability.

## X1 evidence capability boundary

Remaining X1 provider limitations are explicit CMIS capability states rather than facts Roberta may guess.

Examples include facts that are:

- independently verified;
- bounded to a narrower evidence scope;
- unavailable until semantics are proven.

Roberta preserves those boundaries and does not upgrade missing or partial provider evidence through model interpretation.

## Wallet / behavioral safety boundary

CMIS now has both the original neutral wallet-activity/concentration foundation and two newer accepted internal deterministic contracts:

- descriptive classification of the exact concentration direction proven by canonical CMIS evidence;
- direct wallet-relationship evidence for verified observed token-transfer interactions between exact chain identities.

Those newer contracts remain **internal/read-only/non-promoted**. They do not create Roberta/Scout operations and do not authorize behavioral or ownership interpretation.

Roberta may not label a wallet as an insider, whale, bot, accumulator, distributor, market maker, manipulator, dumper, scammer, common owner, beneficial owner, or equivalent merely because the internal classification or relationship evidence exists. The wallet-relationship foundation proves only observed direct interaction and explicitly does not prove common ownership, beneficial ownership, coordinated control, intent, or complete graph/history coverage.

Facts and interpretations remain separate.

## Promoted Verified Intelligence boundary

The current promoted CMIS intelligence service remains `concentration_change_intelligence/v1` on X1 under CMIS `1.9.0`. Roberta uses it only through X1 Scout after validating the exact service/promotion capability contract.

The internal descriptive-classification and wallet-relationship foundations are separate from that promoted service and may not be called or relied upon through the public Scout boundary unless a later accepted promotion contract explicitly changes their status.

## Early-warning boundary

Evidence-backed alerts are the next shared read-only intelligence milestone. A future CMIS alert contract must define exact evidence scope, freshness, threshold/policy identity, persistence or repetition semantics, triggering observations, deterministic identity, limitations, and fail-closed behavior before any alert is eligible for public-service or Scout-reliance promotion.

An alert may report only the condition actually proven. It may not silently imply whale/insider/bot/common-owner activity, manipulation, fraud/scam, coordinated behavior, intent, or execution authority.

Roberta adoption of any future alert service requires a separate promotion/adoption/readiness step.

## Cross-chain evidence boundary

X1 and Solana Scout reports preserve separate chain-specific evidence contexts.

Roberta may compare evidence returned by each chain, but it may not:

- merge source lists into one synthetic source set;
- apply one chain's scope/freshness to another chain;
- recompute CMIS proof strength;
- recompute CMIS market risk;
- create a synthetic cross-chain safety grade;
- substitute X1 facts for missing Solana facts or vice versa.

## Durable memory and policy

HXMP and LangGraph checkpoints are not authoritative sources for current market facts.

```text
HXMP / durable memory -> stable context and explicit policy
CMIS                  -> current verified facts and evidence
Policy code           -> deterministic rule result
LLM                    -> explanation / synthesis only
```

Fresh verified CMIS/provider evidence overrides remembered or checkpointed live-market snapshots.

## Human approval boundary

Phase 9 supports resumable human review with exact proposal/scope binding.

An approval means a human reviewed one exact proposal. It is not a reusable signing credential and does not grant broad future wallet authority.

## Controlled execution boundary

Roberta Phase 11 has **not started**.

Roberta currently has no authority for:

- transaction construction as an execution path;
- wallet signing;
- transaction broadcasting;
- custody;
- swap execution;
- autonomous trading;
- autonomous value movement;
- broad delegated wallet authority.

Research, recommendations, deterministic policy, human review, CMIS pre-trade analysis, deterministic intelligence classification, wallet-relationship evidence, and any future read-only alert contract must not be interpreted as execution authorization.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,deepseek]'
```

## Deterministic tests

```bash
python -m pytest -v -m 'not live and not cmis_live'
```

The deterministic suite covers the Oracle/tool loop, provider-neutral model injection, Chain Scout boundaries, CMIS capability validation, X1 and Solana evidence isolation, policy, persistence, durable-memory adapters, human approval, and evidence-aware response contracts.

## Provider-backed CMIS

The CMIS implementation is maintained in the separate `bhaygood29053-pixel/cmis` repository.

Start CMIS there with its current compatibility module path:

```bash
python -m liquidity_scout.cmis.http
```

Roberta defaults to:

```text
CMIS_BASE_URL=http://127.0.0.1:8765
```

Optional settings include:

```text
CMIS_TIMEOUT_SECONDS=30
CMIS_API_KEY=...
```

A non-loopback CMIS deployment should require Bearer authentication.

Run explicit CMIS integration tests while CMIS is running:

```bash
RUN_LIVE_CMIS_TESTS=1 python -m pytest -v -m cmis_live
```

Live tests should verify contracts/provenance rather than hard-code current market values.

## Model runtime

Set `DEEPSEEK_API_KEY` for the configured DeepSeek runtime path.

Opt-in live-model tests:

```bash
RUN_LIVE_MODEL_TESTS=1 python -m pytest -v -m live
```

Model-provider tests remain separate from deterministic provider/CMIS evidence verification.

## Local Roberta HTTP bridge

Start CMIS first, configure the model runtime, then start Roberta:

```bash
roberta-serve
```

Defaults:

```text
ROBERTA_HOST=127.0.0.1
ROBERTA_PORT=8766
```

Health check:

```bash
curl -s http://127.0.0.1:8766/healthz
```

The message endpoint is `POST /v1/roberta`. Transport callers provide the user message; they do not provide tool names, CMIS operations, market facts, proof scores, risk values, or execution controls.

A non-loopback bind should require `ROBERTA_API_KEY` and Bearer authentication.

## MoltGrid / Signal topology

The accepted user-facing topology is:

```text
CMIS        127.0.0.1:8765
  ↓
Roberta     127.0.0.1:8766
  ↓
MoltGrid / Signal listener
```

Roberta is the normal conversational voice. The transport layer owns admission/reply linkage/duplicate protection; Chain Scouts own chain-specific investigation; CMIS owns deterministic facts, evidence, proof quality, and risk.

If Roberta is unavailable, the normal user-facing transport should report availability failure rather than exposing raw CMIS output as the conversational response.

## Near-term boundary

The deterministic pre-trade trade-size milestone previously tracked as CMIS Issue #99 is complete. Roberta consumes CMIS's structured result and explains it; it does not duplicate the calculation.

Deterministic descriptive classification and wallet-relationship evidence are also complete inside CMIS at non-promoted read-only boundaries. The next shared milestone is evidence-backed alert contracts; additional cross-chain expansion and any eventual controlled execution must each be promoted through explicit evidence and safety contracts rather than inferred from existing foundations.
