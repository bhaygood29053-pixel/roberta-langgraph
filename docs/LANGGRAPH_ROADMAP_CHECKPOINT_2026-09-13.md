# ROBERTA Roadmap Checkpoint — 2026-09-13

This checkpoint supersedes the active-execution state in `docs/LANGGRAPH_ROADMAP_CHECKPOINT_2026-09-12.md` where it conflicts with newer Cohort 001 evidence and later Evaluation Laboratory acceptance. Historical accepted capability records remain unchanged.

## Current phase

ROBERTA is in **public beta / Cohort 001 evidence-driven remediation**.

Accepted/observed product evidence now includes:

- C01 exact-token investigation: **PASS**.
- C02 wallet relationship: **FAIL / supported workflow unavailable** — bounded wallet-pair discovery is still required upstream in CMIS #686 before ROBERTA #472 can rerun frozen C02.
- C04 Smart Route / Pre-Trade: **Human authority-wording defect observed** — ROBERTA #473 remains the Human correction gate.
- C05 Daily Intelligence Brief: the public capability-normalization defect is fixed on current public `main`, and protected ROBERTA structurally preserves Daily Brief intent; the remaining live blocker is protected CMIS Large-Trade Discovery exceeding the 90-second Human runtime budget in `cmis-core` #76 / PR #77. C05 is not PASS until that protected runtime gate is accepted, assembled, and the exact frozen prompt passes.
- C07 evidence drill-down: **PARTIAL** — evidence boundaries are preserved, but Quick/Normal presentation still leaks backend implementation language; ROBERTA #476 tracks the Human presentation fix.

The beta is now testing whether accepted backend capabilities form complete, useful Human workflows rather than merely counting accepted services.

## Immediate execution order

1. **CMIS protected #76 / PR #77** — make Daily-Brief Large-Trade evidence nonblocking without widening the 90-second product budget or weakening evidence semantics; then rerun frozen C05 through assembled ROBERTA.
2. **CMIS #686** — bounded X1 wallet-pair relationship discovery v1.
3. **ROBERTA #472** — adopt accepted wallet-pair discovery through X1 Scout / ROBERTA and rerun frozen C02.
4. **ROBERTA #473** — repair Smart Route recommendation-vs-execution Human wording and rerun frozen C04.
5. **ROBERTA #476** — preserve C07 evidence fidelity while removing backend implementation language from Quick/Normal evidence drill-downs.
6. Complete the remaining accepted Cohort 001 scoring/reruns without rewriting frozen prompts or rubrics.
7. Generate the content-free Cohort 001 closeout summary, rank observed gaps by frequency x impact, and move to commercial proof only after first-cohort evidence is reconciled.

## Accepted baseline remains

- core X1 intelligence, Instant X1 Scan, compare/history/burn/discovery;
- verified wallet trade, price-impact, Large-Trade Discovery contracts;
- cross-chain provenance / Bridge-to-XDEX;
- GENIUS Act learning + Live Regulatory Intelligence;
- X1 Daily Intelligence Brief contract/product surface;
- Tokenized Equity / RWA end-to-end through Human “What exactly am I buying?”;
- Smart Route Phase 1 + 2 through Ask ROBERTA / website;
- Human ROBERTA v2 runtime enforcement;
- Option #2 dashboard / narrative compatibility;
- Public Beta Product Proof + Cohort Preflight.

## Current source-of-truth trackers

- master roadmap: ROBERTA #246;
- cohort protocol: ROBERTA #462;
- cohort runtime/scoring: ROBERTA #466;
- C02 remediation: CMIS #686 -> ROBERTA #472;
- C04 remediation: ROBERTA #473;
- C05 runtime remediation: `cmis-core` #76 / PR #77 -> assembled ROBERTA rerun;
- C07 Human presentation remediation: ROBERTA #476.

## Evaluation Laboratory

`roberta-eval` has advanced from the earlier LAB #71 checkpoint through **LAB #91**.

The accepted offline Human-remediation/root-cause chain now covers terminal closure/reopen adjudication, parent-child recurrence lineage, generational regression detection, evidence-backed root-cause investigation, correlation-only evidence acquisition, pre-registered falsifiable DIRECT-evidence experiments, deterministic controlled execution, pinned ROBERTA artifact materialization/offline sandboxing, and candidate-patch qualification through a `PR_ELIGIBLE` promotion package.

LAB #91 does **not** create or merge a production `roberta-langgraph` remediation PR. A later explicit production-promotion gate would still be required.

Broad live LAB #21/#22 campaigns remain paused unless explicitly resumed. The lab supports Cohort-derived Human defects rather than replacing real-user product testing.

## Supporting / deferred

- Telegram PR #264 — lower priority.
- XenBlocks source #140 / PR #141 — blocked on exact-byte source preservation.
- X1Labs Intelligence Scout PR #190 — planning only / post-Learning System sequencing.
- Learning Plane scheduling #275 / protected PR #11 — supporting; not a Cohort blocker.
- protected current-X1 delegation PR `roberta-core` #90 — open/unaccepted until its own live acceptance path.
- CMIS #458 / PR #549 X1Scroll archival qualification — credential-dependent; do not promote without live proof.
- Controlled Execution — locked.

## Canonical repository inventory

The active project now has five canonical repositories:

- `bhaygood29053-pixel/roberta-langgraph`
- `bhaygood29053-pixel/roberta-core`
- `bhaygood29053-pixel/cmis`
- `bhaygood29053-pixel/cmis-core`
- `bhaygood29053-pixel/roberta-eval`

The former `liquidity-scout` repository path redirects to `bhaygood29053-pixel/cmis`; do not maintain it as a separate repository checkpoint.

## Repository heads observed immediately before this reconciliation

- `roberta-langgraph`: `becb264b8026b5cbbf99f0d12dea62463510c6ee`
- `roberta-core`: `8f957e2b09338dd8d918df5150b64286bcdc5dba`
- `roberta-eval`: `85b07b1f2f9451d2baa62d4b05e4218a0d3b0f38`
- `cmis`: `a64e1fab39e7db69605381c75a7d3bbd7d94c0a4`
- `cmis-core`: `4b87eb9554393cdce61278d151d5405eac8787ca`

## Product direction

Primary entry point remains **Ask ROBERTA**.

Core behaviors remain **Investigate / Ask / Compare / Watch / Discover / Brief**.

The immediate product priority is closing the concrete Human workflow gaps exposed by Cohort 001, rerunning the same frozen scenarios, and measuring whether users find ROBERTA useful enough to return and pay. Broad speculative intelligence should not displace those product-proof gates.

`execution_authorized=false` remains invariant.
