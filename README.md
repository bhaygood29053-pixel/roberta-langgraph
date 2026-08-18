# Roberta LangGraph

Roberta is the top-level Oracle, policy-aware coordinator, and normal user-facing voice for the multi-agent system.

Current accepted hierarchy:

```text
User / MoltGrid Signal
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

Roberta does not call provider APIs directly and does not reproduce CMIS market, risk, verification, evidence-receipt, or proof-score calculations.

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
- Phase 11 Controlled Execution — **locked / not started**

See [`docs/LANGGRAPH_ROADMAP.md`](./docs/LANGGRAPH_ROADMAP.md) for the authoritative roadmap.

## Evidence-aware intelligence

Roberta consumes the CMIS evidence-quality contract introduced in CMIS `>=1.7.0`.

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

Roberta requires the CMIS capability manifest to advertise evidence receipt schema 1, proof score schema 1, `risk_separate_from_proof=true`, and `missing_evidence_is_unknown=true`.

Provider-reported information remains provider-reported until CMIS records independent verification. Missing evidence remains unknown/unproven.

Detailed behavior is documented in [`docs/EVIDENCE_AWARE_INTELLIGENCE.md`](./docs/EVIDENCE_AWARE_INTELLIGENCE.md).

## Answer-first user experience

Recommendation-style responses are designed to prioritize:

1. conclusion / recommendation / blocker;
2. the most important evidence-backed reasons;
3. risk when CMIS actually provides a dedicated risk level;
4. evidence quality / proof strength;
5. important missing evidence;
6. deeper technical evidence on request.

Pre-trade responses use a deterministic finalizer instead of passing the result through a second free-form LLM rewrite.

`PASS`, `WARN`, and `BLOCK` are not automatically HIGH/MEDIUM/LOW risk levels. If CMIS does not provide a dedicated risk level, Roberta keeps the risk level unknown instead of inventing one.

## Recommendation evidence planning

Roberta deterministically identifies evidence needs for common questions such as:

- buy/sell recommendations;
- trade-size questions;
- safer-asset comparisons;
- what-changed questions;
- liquidity-risk questions;
- LP questions;
- price-move questions.

X1 Scout incorporates the allowed read-only evidence requirements into its deterministic planning. Recommendation wording cannot silently enable explicit `pre_trade_check` or any execution capability.

## X1 evidence capability boundary

Remaining X1 provider limitations are explicit CMIS capability states rather than facts Roberta may guess.

Examples include:

- canonical native-XNT translation: verified;
- token-account concentration: bounded and not equivalent to wallet/holder concentration;
- direct XDEX history semantics: unavailable until proven;
- direct XDEX quote semantics: unavailable until proven;
- X1.Ninja SSE access handshake: bounded, while live-event semantics remain unavailable;
- bridge candidate-URL provenance: bounded, while current bridge operational/route/fee/capacity/lifecycle facts remain unavailable without an accepted machine-readable contract.

Roberta preserves these boundaries and does not upgrade them through model interpretation.

## Wallet / whale safety boundary

Roberta may consume future deterministic wallet primitives from CMIS, but it may not label a wallet as an insider, whale, bot, accumulator, distributor, market maker, manipulator, dumper, or equivalent until CMIS supplies accepted primitives and a later classification contract explicitly permits the label.

Facts and interpretations remain separate.

## Cross-chain evidence boundary

X1 and Solana Scout reports preserve separate chain-specific evidence contexts.

Roberta may compare the evidence returned by each chain, but it may not:

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

Phase 11 has **not started**.

Roberta currently has no authority for:

- transaction construction as an execution path;
- wallet signing;
- transaction broadcasting;
- custody;
- swap execution;
- autonomous trading;
- autonomous value movement;
- broad delegated wallet authority.

Research, recommendations, deterministic policy, human review, pre-trade analysis, and future simulation must not be interpreted as execution authorization.

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

The CMIS implementation remains in the separate `liquidity-scout` repository.

Start CMIS there:

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

Run the explicit CMIS integration tests while CMIS is running:

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

## Near-term work

The most important current dependency is CMIS deterministic pre-trade trade-size/impact analysis (Liquidity Scout Issue #99). Roberta should consume that structured evidence and explain it; it should not duplicate the CMIS calculations.

After the evidence/pre-trade foundation is mature, wallet activity primitives and verified wallet/whale intelligence can be added under explicit evidence contracts.
