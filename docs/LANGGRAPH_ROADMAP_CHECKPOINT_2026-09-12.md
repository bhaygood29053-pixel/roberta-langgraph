# ROBERTA Roadmap Checkpoint — 2026-09-12

This checkpoint supersedes the stale **Live checkpoint** and **Active execution order** sections dated 2026-09-10 in `docs/LANGGRAPH_ROADMAP.md`. Historical architecture, authority, Learning System, and completed-work sections remain unchanged until the next consolidated rewrite.

## Current accepted flagship state

ROBERTA has completed the major backend/productization chain needed for a first public-beta cohort:

- Tokenized Equity / RWA intelligence is accepted end to end through X1 Scout, Claim Integrity, protected Machine synthesis, Human “What exactly am I buying?” explanation, and final hardening.
- X1 Smart Route is accepted through CMIS Phase 1 + Phase 2, X1 Scout projection, protected ROBERTA Pre-Trade adoption, and Ask ROBERTA/website exposure.
- Public Beta Product Proof v1 is accepted with privacy-safe, content-free outcome/feedback telemetry.
- Public Beta Cohort Preflight v1 is accepted; the seven-workflow scenario pack and PASS/PARTIAL/FAIL rubric are frozen.
- Human ROBERTA v2 plain-language enforcement and acceptance coverage are accepted for Quick/Normal, while Deep Dive remains the explicit technical surface.
- The selected Option #2 visual dashboard is accepted through PR #467 and now renders the current narrative asset-answer shape rather than falling back to the thin legacy snapshot card.
- Protected `roberta-core` has promoted its active compatibility baseline through ROBERTA #104 / PR #105; protected main is `7a380a95a21b52a66eed85577c39808bcd4cd6b2` at this checkpoint.
- `execution_authorized=false` remains invariant.

Public ROBERTA main observed for this checkpoint: `d9f03d4db7b4d1b7eedc75854e7eb4479ffecd75` (merge PR #467, faithful Option #2 visual dashboard).

## Active execution order

### 1. Cohort 001 — ACTIVE FLAGSHIP

Issue: `#466`  
Parent: `#462`

The code/preflight blocker is cleared. The dominant remaining product question is real user behavior.

Current setup state:

- actual-runtime cohort preflight: PASS;
- live cohort JSONL initially empty: PASS;
- accepted cohort-preflight merge present locally: PASS;
- moderator inputs frozen outside telemetry/GitHub: PASS;
- assembled `.venv-runtime` construction: PASS;
- current port `8766` owner identified as the accepted `roberta-bridge.service`: PASS;
- bridge health: PASS;
- verify `ROBERTA_BETA_PRODUCT_PROOF_PATH` is present in the already-running systemd process environment: STILL REQUIRED;
- valid Participant 1 / C01: NOT YET SCORED;
- at least one complete C01-C07 real-user run: NOT YET COMPLETE.

Do not add new backend intelligence during the participant run unless an observed user/evidence gap justifies a separate issue.

### 2. Cohort closeout / product proof — NEXT

After valid C01-C07 evidence exists:

1. generate the content-free `roberta_beta_cohort_summary/v1`;
2. rank observed product/evidence/Human-language failures by frequency x impact;
3. close or update parent #462 from actual cohort evidence;
4. choose the first commercial workflow, API surface, onboarding change, or new intelligence task from observed demand rather than feature speculation.

Initial beta targets remain directional until cohort size is recorded:

- helpful >= 70%;
- too-technical + confusing <= 20%;
- supported workflow unavailable <= 10%;
- would-use-again >= 60%;
- every EVIDENCE_REQUIRED answer names the missing evidence rather than guessing.

### 3. Human-language / presentation quality — SUPPORTING

Accepted Human v2 work now includes deterministic plain-language/runtime gates, Vale 3.21 downstream presentation checks, realistic service-family acceptance coverage, and zero-token offline replay support in `roberta-eval`.

Use repeated cohort `too_technical` / `confusing` evidence to extend permanent regressions. Presentation tooling must not rewrite facts, freshness, risk, recommendation authority, or execution boundaries.

### 4. Evaluation Laboratory — SPLIT STATUS

Broad live LAB #21/#22 campaigns remain paused unless explicitly resumed.

Offline Human-quality tooling is active/accepted and does not resume live campaigns:

- Human v2 zero-token language grading: accepted;
- batch/replay zero-token saved-run grading: accepted via `roberta-eval` PR #56 / merge `6fecbfd937a961dc07df0ecd0d5d6288a294e983`;
- grading remains advisory, factual-authority false, and makes zero judge-model/external calls.

Protected `roberta-core` #89 / PR #90 remains open/unaccepted current-X1 delegation remediation and must not be treated as accepted capability or merged merely because it exists.

### 5. CMIS / X1 intelligence expansion — EVIDENCE-DRIVEN, NOT FLAGSHIP

CMIS Smart Route Phase 1 + 2 are complete. Future cross-DEX execution evidence, a second bounded route candidate/provider, and `x1_route_comparison/v1` are future expansions and are not current beta blockers.

Provider/evidence research should proceed only where it closes a demonstrated product evidence gap.

### 6. Supporting / lower priority

- Learning Plane scheduling #275 / protected `roberta-core` #11 — supporting; current head still requires its own fresh acceptance gate before merge.
- Telegram #264 — lower priority / needs refresh.
- Learning System durable-source work remains queued behind accepted phase ordering; XenBlocks source onboarding remains blocked on exact-byte source preservation.
- Controlled Execution — locked; no transaction construction, signing, broadcasting, custody, trade execution, bridge execution, or value movement.

## Product phase

ROBERTA is now in **public beta / Cohort 001 activation**, not broad architecture build-out.

Active chain:

`Core intelligence ✅ -> Tokenized Equity ✅ -> Smart Route ✅ -> Ask ROBERTA ✅ -> Human v2 ✅ -> Beta measurement ✅ -> Cohort preflight ✅ -> #466 REAL USER COHORT ACTIVE -> commercial proof`

The dominant uncertainty is actual user usefulness and willingness to return/pay, not whether another backend contract can be built.

Last reconciled: **2026-09-12 America/New_York**.
