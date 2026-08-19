# Roberta Decision Quality Roadmap Gate

Date: 2026-08-19
Tracking: issue #51

## Decision

The Decision Quality milestone is mature enough to exit feature-hardening and enter a **Read-Only Decision Production Readiness / Evaluation** milestone.

Do **not** start Phase 11 Controlled Execution from this milestone. Do **not** add another specialist merely because the current decision UX is mature.

The next roadmap phase should validate the accepted read-only decision stack end-to-end under representative production conditions before expanding authority or architecture.

## Evidence supporting this decision

Issue #51 was implemented incrementally through merged PRs #54, #56, #57, #58, #59, and #60. Each slice was gated on exact-head deterministic CI and no unresolved substantive review threads.

The accepted work now covers:

- real-user phrasing for buy/sell decisions, concrete trade-size questions, risk assessment, safer-asset comparison, liquidity risk, LP decisions, market changes, and price-move explanations;
- deterministic recommendation evidence requirements that an untrusted planner cannot omit;
- explicit rejection of autonomous `pre_trade_check`, signing, broadcasting, or execution-like substitutions;
- separate risk and evidence-quality dimensions;
- preservation of PASS/WARN/BLOCK without inventing a HIGH/MEDIUM/LOW risk level;
- stale, conflicting, insufficient, ambiguous, missing, and unavailable evidence states;
- null-versus-verified-zero semantics inherited from CMIS;
- cross-chain evidence isolation when X1 and Solana proof quality differs;
- malformed/tampered CMIS evidence metadata failing closed;
- checkpoint/HXMP historical context remaining non-authoritative for current market facts;
- answer-first post-Scout synthesis contracts for recognized recommendation families;
- normal-mode rejection/retry/fail-closed behavior for diagnostic-first, raw-dump, service-first, or orchestration-first model drafts;
- progressive technical disclosure when users explicitly request raw, technical, source, or verification details.

The latest accepted CMIS dependency relevant to this gate is commit `ce3ecd4a00852b244cbeb2769865af34357428ad`, which preserves missing verified asset-activity evidence as null rather than zero. Roberta's #51 regression coverage preserves that distinction through the Scout/user-decision path.

## Failure findings that shaped the milestone

The test corpus exposed three meaningful classes of product risk.

### 1. Natural-language coverage risk

Canonical demo phrases were too narrow for ordinary user wording. The fix was deterministic intent/evidence-plan expansion, not another agent or model layer.

### 2. Planner omission / authority-smuggling risk

An untrusted planner could propose incomplete or execution-like operations. Deterministic enforcement now restores required read-only evidence and rejects unauthorized operations.

### 3. Post-Scout presentation-compliance risk

Prompt-only answer-first behavior was not structurally strong enough for ordinary recommendation families. The narrow accepted fix was a task-specific synthesis brief plus a bounded rejection/retry/fail-closed guard for obvious diagnostic-first outputs. No generalized market formatter or new graph layer was required.

## Why the next phase is production-readiness evaluation

The remaining uncertainty is no longer primarily whether Roberta understands the decision contract. It is whether the accepted stack performs reliably with representative production models, real configured Scout/CMIS paths, normal latency, degraded providers, and realistic user conversations.

That should be measured before adding new authority or specialist breadth.

## Next milestone — Read-Only Decision Production Readiness / Evaluation

### Goal

Demonstrate that Roberta consistently turns verified Scout/CMIS evidence into useful, concise, evidence-aware decisions under realistic read-only operating conditions.

### Required evaluation areas

1. **Representative user-question suite**
   - buy/sell decisions;
   - trade-size questions;
   - risk questions;
   - safer-asset comparisons;
   - liquidity-risk questions;
   - LP decisions;
   - market-change questions;
   - price-move explanations;
   - explicit technical-detail follow-ups.

2. **Configured specialist paths**
   - X1 Scout against accepted CMIS capabilities;
   - Solana Scout only where its capability manifest and deployment configuration permit the requested read-only service;
   - no silent chain substitution.

3. **Production-model behavior**
   - verify answer-first ordering;
   - verify the diagnostic-first rejection/retry guard with the actual configured model;
   - measure retry/fail-closed frequency;
   - confirm general non-market questions remain unaffected by recommendation-specific guards.

4. **Evidence degradation and provider failure**
   - stale evidence;
   - partial/unavailable fields;
   - source conflicts;
   - provider errors/timeouts;
   - ambiguous asset identity;
   - insufficient proof;
   - null-versus-zero preservation;
   - capability-manifest rejection or unavailable service.

5. **Decision quality metrics**
   - correct recommendation intent classification;
   - required evidence gathered;
   - no unauthorized operation admitted;
   - answer-first compliance;
   - risk/evidence-quality separation;
   - important unknowns surfaced;
   - raw diagnostics hidden by default;
   - technical detail available on request;
   - factual/status/provenance preservation;
   - latency and retry count recorded separately from decision correctness.

6. **Trust-boundary verification**
   - `User -> Roberta -> Chain Scout -> CMIS -> Chain Provider` remains intact;
   - memory/checkpoints never satisfy current-market truth by themselves;
   - Roberta never recalculates or strengthens/weakens CMIS risk/proof conclusions;
   - no transaction construction, signing, broadcasting, custody, autonomous execution, or value movement.

## Exit criteria for production-readiness evaluation

The next milestone should not be considered complete merely because deterministic unit tests pass. It should require a documented evaluation corpus and reproducible results showing that:

- representative decision families complete through configured read-only specialist paths;
- production-model presentation guard behavior is acceptable and fail-closed under adversarial prompts;
- degraded-provider scenarios preserve uncertainty without fabricating facts;
- chain isolation is maintained;
- important unknowns are surfaced clearly;
- no execution boundary is crossed;
- observed latency/retry behavior is understood well enough for user-facing deployment;
- any remaining recurring failure mode is either fixed narrowly or documented as a deployment blocker.

## Explicitly deferred

The following are not authorized by completion of issue #51:

- Phase 11 Controlled Execution;
- transaction simulation as an execution precursor unless separately scoped and approved;
- transaction preparation;
- signing;
- broadcasting;
- wallet custody;
- autonomous trading;
- bridge transfer execution;
- broad wallet authority;
- additional specialists that are not justified by evaluation evidence.

## Roadmap conclusion

Roberta's next step should be to prove the quality and resilience of the accepted read-only decision stack in realistic operation. Only after that evidence exists should the roadmap decide whether the highest-value next phase is another specialist, deeper deterministic intelligence, deployment hardening, or a separately approved controlled-execution program.
