# Roberta Engineering Workflow

Status: **repository-authoritative engineering workflow**

Tracking: Issue #98, first implementation slice under parent Issue #97.

This document is the default engineering process for meaningful Roberta changes by human or AI contributors. It governs how accepted work moves from roadmap intent to merged code or documentation without widening Roberta's authority by accident.

It does not replace fact-specific contracts, roadmap gates, readiness documents, security boundaries, or CMIS contracts. Those remain authoritative for their own scope. This workflow defines how contributors must use those authorities when changing Roberta.

## Canonical authority boundary

Every change must preserve the current hierarchy unless a separately accepted roadmap/architecture decision explicitly changes it:

```text
User / transport
  -> Roberta
    -> Chain Scout
      -> CMIS
        -> Chain Provider / verified source
```

Roberta owns orchestration, user policy, specialist selection, memory use, cross-chain coordination, approval boundaries, and final user-facing synthesis.

Chain Scouts own chain-specific planning and interpretation while preserving CMIS facts, evidence, provenance, limitations, and uncertainty.

CMIS owns deterministic verified market/blockchain facts, evidence, Evidence Receipts, Proof Scores, deterministic risk, historical intelligence, capability eligibility, and bounded analysis-only pre-trade calculations.

Providers remain beneath CMIS and are not trust roots merely because they return data.

## Required engineering flow

Meaningful work should follow this sequence:

```text
Roadmap gate
  -> issue/spec
  -> agreed public seam / contract
  -> narrow tracer-bullet slice
  -> behavior-first test
  -> RED -> GREEN where practical
  -> targeted verification
  -> full deterministic suite / CI
  -> three-axis review
  -> merge
  -> roadmap reconciliation
```

Small typo-only or mechanically safe documentation changes may compress the test steps, but they do not bypass authority/safety review or source-of-truth reconciliation.

## 1. Roadmap gate

Before implementation, identify the accepted roadmap item, readiness gate, parent issue, or explicit architecture decision that authorizes the work.

If the idea is not currently authorized, classify it as backlog, research, experiment, or proposed roadmap work rather than silently widening the active scope.

A roadmap reference is not permission to broaden adjacent authority. Implement only the accepted slice.

Controlled Execution remains locked unless a separate accepted roadmap gate explicitly starts it.

## 2. Issue/spec before code

Non-trivial implementation starts from an issue or equivalent accepted specification that defines, as applicable:

- the problem to solve;
- expected observable behavior;
- the authority owner for each fact/decision involved;
- the public seam, contract, or interface being changed;
- required failure and degraded-evidence behavior;
- non-goals and forbidden scope;
- acceptance tests or acceptance criteria;
- dependencies/blockers;
- execution/safety implications.

If these are materially ambiguous, resolve the contract before expanding implementation.

Do not use implementation details as a substitute for a missing behavioral contract.

## 3. Prefer narrow tracer-bullet slices

Large work should be split into independently verifiable vertical slices that cross only the layers necessary to prove one useful behavior.

Prefer:

```text
one accepted user/system behavior
  -> smallest public seam change
    -> deterministic coverage
      -> exact verification
```

Avoid broad horizontal rewrites such as building every storage layer, every abstraction, or every specialist hook before one end-to-end behavior can be demonstrated.

Each slice should make blockers explicit. A blocked later slice must not be smuggled into the current PR through speculative architecture.

## 4. Behavior-first testing

Tests should primarily exercise accepted observable behavior at the narrowest stable public seam.

Good tests prove things such as:

- accepted input produces the required output/decision;
- malformed or unauthorized input fails closed;
- missing evidence remains missing rather than becoming zero/false;
- risk and Proof Score remain separate;
- chain-specific evidence remains isolated;
- an unavailable capability does not silently fall back;
- memory/checkpoint state does not replace fresh market truth;
- execution authority remains false when the contract is read-only.

Avoid tests that merely repeat implementation internals, assert constants with no behavioral value, or become tautological copies of the production code.

## 5. RED -> GREEN where practical

For behavior changes, prefer this loop:

1. add one focused test that fails for the intended reason;
2. confirm the failure reflects the missing behavior, not a broken environment;
3. implement the minimum change that satisfies the accepted contract;
4. make the focused test pass;
5. continue with the next narrow slice.

Documentation-only changes do not require artificial failing tests. Existing deterministic verification still applies when the documentation changes executable commands, configuration, contract claims, or test expectations.

## 6. Targeted verification during implementation

Run the smallest relevant deterministic test set while working so failures stay attributable to the current slice.

Examples include:

- the directly affected test module;
- the affected Scout/CMIS client contract tests;
- readiness/evaluation tests for the changed behavior;
- static/configuration validation for deployment or workflow changes.

A targeted pass is a development checkpoint, not the final merge gate.

## 7. Exact-head full verification before merge

Before merge, verify the exact PR head rather than relying on an earlier local commit or stale CI result.

For code-bearing changes, the expected default is the full deterministic suite plus repository CI unless the issue defines a stricter accepted gate.

Current deterministic local baseline:

```bash
python -m pytest -v -m 'not live and not cmis_live'
```

Opt-in live/model/provider tests are separate evidence lanes and must not be substituted for deterministic CI. When a roadmap/readiness gate requires a live configured run, record that result independently with its provenance and scope.

Do not treat skipped required cases as passing when the acceptance gate says they must execute.

## 8. Three-axis PR readiness gate

Every non-trivial PR must be reviewed independently on all three axes below.

Passing one axis does not compensate for failing another. A PR is not merge-ready while any required axis fails.

### Axis 1 — Spec fidelity

Review the diff against the originating issue, accepted contract, and non-goals.

Confirm that:

- all required behavior is present;
- failure/degraded-state semantics match the specification;
- no material requirement is silently omitted;
- no unrelated feature or authority is added;
- public interfaces remain within the accepted scope;
- acceptance criteria are actually demonstrated, not merely claimed;
- documentation describes what the implementation really does.

Questions to ask:

- Did we build the requested behavior rather than a nearby behavior?
- Did we preserve explicit unknown/unavailable/partial states?
- Did we accidentally solve an unapproved future phase too?

### Axis 2 — Code / architecture quality

Review maintainability and architectural fit independently of whether tests pass.

Confirm that:

- naming reflects the accepted domain/authority;
- seams/interfaces are narrow and testable;
- coupling is not increased unnecessarily;
- provider/specialist boundaries remain replaceable;
- logic is not duplicated across Roberta, Scouts, and CMIS;
- abstractions are justified by current behavior rather than speculative future use;
- error paths are explicit and fail safely;
- tests are behavior-oriented and maintainable;
- documentation has one clear authority rather than competing copies.

Questions to ask:

- Is this the smallest design that cleanly supports the accepted slice?
- Did we create a second source of truth?
- Did convenience introduce hidden coupling or duplicated deterministic logic?

### Axis 3 — Authority / safety boundary

Review authority separately from correctness and code quality.

The diff must not accidentally allow Roberta or a Scout to become a new deterministic trust root.

Explicitly check that the change does **not**:

- make Roberta manufacture, recalculate, strengthen, or weaken CMIS market facts, deterministic risk, Evidence Receipts, or Proof Scores;
- let a Chain Scout bypass CMIS and call a provider as a trust shortcut;
- upgrade provider-reported information into independently verified truth without an accepted CMIS contract;
- convert missing/unknown/unavailable evidence into zero, false, empty-success, or an LLM estimate;
- treat HXMP, checkpoints, conversation history, or cached history as current market/risk/tokenomics/wallet truth;
- merge X1 and Solana evidence into one synthetic provenance set, Proof Score, freshness state, deterministic risk value, or safety grade;
- silently broaden a capability from one chain/service/scope to another;
- turn analysis-only behavior into transaction preparation, signing, broadcasting, custody, trading, bridge transfer, or autonomous value movement;
- treat human approval as reusable or broad wallet authority;
- weaken fail-closed authentication, capability, identity, evidence, or approval checks.

Fresh accepted CMIS/provider evidence overrides remembered/checkpointed/conversational live-market values.

A PR that passes tests but widens authority without an accepted roadmap/contract decision **fails this axis and must not merge**.

## 9. Merge criteria

A non-trivial PR is merge-ready only when all applicable conditions are satisfied:

- accepted roadmap/issue scope is clear;
- requested behavior and failure semantics are implemented;
- targeted verification passes;
- exact-head full deterministic suite/required CI passes;
- any required readiness/live evidence is recorded with explicit provenance and scope;
- no substantive unresolved review thread remains;
- Spec Fidelity passes;
- Code/Architecture Quality passes;
- Authority/Safety Boundary passes;
- documentation and public contracts match the exact implementation;
- no unrelated files or scope are included.

Green CI alone is necessary evidence, not sufficient merge authorization.

## 10. Post-merge roadmap and documentation reconciliation

After accepted work merges, update source-of-truth documents so completed work is not still shown as pending, blocked, or future.

At minimum check:

- the originating issue/parent issue;
- `docs/LANGGRAPH_ROADMAP.md` when roadmap status changed;
- README status/pointers when user-facing project state changed;
- fact-specific contract/readiness documents;
- dependency/blocker statements in follow-on issues.

Do not rewrite historical evidence documents merely to make them look current. Reconcile the living source of truth and preserve historical records as historical records.

## Source-of-truth rules

Use one authority per concern and link to it rather than copying full policies across files.

Examples:

- this file owns the general engineering workflow and three-axis merge gate;
- `docs/LANGGRAPH_ROADMAP.md` owns current Roberta roadmap status;
- fact-specific readiness/gate documents own their accepted evidence and scope;
- CMIS contracts remain authoritative for deterministic market/evidence/risk semantics;
- HXMP/memory documents own durable-memory behavior;
- human-approval documents own approval semantics.

When two documents appear to conflict, resolve the ownership boundary rather than averaging the claims.

## AI-assisted development

AI contributors follow the same workflow as human contributors.

AI speed does not relax roadmap gating, issue/spec discipline, tests, review, or authority boundaries.

Before publishing a change, an AI contributor should be able to identify:

- the authorizing issue/roadmap gate;
- the exact files intentionally changed;
- the behavior proved by tests/evidence;
- the remaining non-goals/blockers;
- how all three review axes were evaluated.

Do not use broad automated edits, blanket staging, or unrelated cleanup to hide the true slice being reviewed.

## Explicit non-goals of this workflow

This governance document does not itself authorize:

- new runtime features;
- memory-policy widening;
- Technology Radar implementation;
- new provider trust;
- new CMIS public services;
- transaction simulation as an execution precursor;
- transaction preparation;
- signing;
- broadcasting;
- custody;
- live trading;
- bridge/value transfer;
- autonomous execution;
- broad delegated wallet authority.

Those require their own accepted roadmap gates and contracts.

## Compact review checklist

For each meaningful PR, reviewers should be able to answer **yes** to all applicable questions:

```text
SCOPE
[ ] Accepted roadmap/issue/spec exists.
[ ] Slice is narrow and non-goals are preserved.

VERIFICATION
[ ] Behavior-first coverage exists where applicable.
[ ] Targeted verification passes.
[ ] Exact-head full deterministic suite / required CI passes.

SPEC
[ ] Requested behavior and failure semantics are complete.

CODE / ARCHITECTURE
[ ] Design is maintainable, narrow, and avoids duplicated authority/logic.

AUTHORITY / SAFETY
[ ] User -> Roberta -> Chain Scout -> CMIS -> Provider remains intact.
[ ] No CMIS fact/risk/proof invention or provider trust bypass is introduced.
[ ] Missing remains unknown/unavailable rather than zero/false/estimated.
[ ] Memory does not substitute for fresh truth.
[ ] Cross-chain evidence is not merged into synthetic proof/risk.
[ ] Execution authority is not widened.

MERGE / RECONCILIATION
[ ] No substantive review blocker remains.
[ ] Source-of-truth docs/roadmap are reconciled after acceptance.
```

**Core rule:** prove the narrow behavior, preserve authority, and reconcile the source of truth after merge.