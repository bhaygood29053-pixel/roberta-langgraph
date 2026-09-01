# ROBERTA Roadmap Reconciliation — 2026-09-01

This dated reconciliation advances the living ROBERTA roadmap without changing CMIS/provider authority, proof/risk semantics, wallet authority, or execution authority by documentation alone.

## Roadmap state

### Complete / accepted on public `main`

- X1 Scout decision-production foundation under the Roberta -> Scout -> CMIS path.
- CMIS `1.13.0` boundary adoption.
- First-class Instant X1 Scan through X1 Scout.
- Deterministic Instant X1 Scan product UX.
- Deterministic `x1_compare/v1` contract.
- First-class X1 Compare workflow with optional one-call CMIS pair history for explicit full-history intent.
- Human ROBERTA + Machine ROBERTA two-face product direction under one canonical fact/decision basis.
- Learning System Phases 1-10, autonomous source-grounded training, mastered-run replay safety, and authoritative read-only telemetry.
- Public-shell/private-core migration and historical source cleanup.

### Active / pending acceptance

- **Canonical ROBERTA Decision Object + Human/Machine renderers.** Both faces must render the same underlying Scout/CMIS facts, risk, proof, limitations, and execution state without recomputation.
- **BURN workflow.** CMIS burn metrics/circulation are accepted, but burn-time valuation remains pending upstream in CMIS #377; consumption remains gated.
- **Discovery / WHAT CHANGED? / Early Warning.** CMIS Discovery Ledger public #365 + private-core #6 remain pending; no local substitute is allowed.
- **Learning operations.** Protected `roberta-core` #10 scheduler/queue is accepted; protected #11 one-cycle orchestrator remains pending. Cooperative budget checkpoints and broader background scheduling remain later gates.
- **Telegram transport — PR #264.** Pending; must remain Roberta-owned transport with no direct CMIS/provider path and no OpenClaw dependency.

## Ordered next actions

1. Implement the Canonical ROBERTA Decision Object and cross-face consistency gate.
2. Harden Human SCAN and COMPARE presentation around the accepted product views.
3. Adopt BURN through X1 Scout only after CMIS burn-time valuation and consumption contracts are accepted.
4. Adopt Discovery / WHAT CHANGED? / Early Warning only after CMIS Discovery/history foundations are accepted.
5. Complete bounded Learning Plane one-cycle orchestration and cooperative resource checkpoints before any always-on scheduler.
6. Complete Telegram only if its owner/private-chat and Roberta-only routing gates pass.
7. Build X1 ecosystem/network brief workflows from accepted Scout/CMIS facts.
8. Maintain Solana as a secondary read-only portability track.
9. Keep Controlled Execution locked/not started.

## CMIS dependency rule

Roberta may orchestrate and render CMIS facts but must not recreate burn, valuation, historical comparison, Discovery, provider freshness, risk, or execution-quality truth locally. Missing evidence remains unknown and open CMIS investigations remain diagnostic until accepted.

`execution_authorized=false`

## Live GitHub reconciliation — 2026-09-01 11:20 America/New_York

### Accepted on `main`
- Canonical ROBERTA Decision Object v1 and Human/Machine projections remain accepted.
- X1 Instant Scan and Compare remain accepted product foundations.
- CMIS historical burn-time valuation is now accepted upstream.
- ROBERTA X1 Burn Intelligence v1 has advanced to the current hardening gate.

### Active gates
- **PR #295 — Harden X1 Burn Intelligence v1 projection contract:** open, clean, and CI green at head `ce5cb9bac4fd4b0f718ed3f043b979f570f87bfc`. This is the immediate productization gate.
- **CMIS #363:** delayed-vault evidence workflow remains in progress; ROBERTA must not treat the diagnostic branch as accepted product truth.
- **Discovery:** CMIS public #365 is clean, but protected `cmis-core` #6 has failing CI. ROBERTA Discovery remains blocked on that upstream pair.
- **Protected Learning Plane — `roberta-core` #11:** open/mergeable but unstable; private-core CI is failing on head `29f5c42c59398a4a1467ea04d81ddc0cb207f2d9`.
- **Telegram #264:** open but currently dirty/non-mergeable. Telegram remains transport-only and must route through ROBERTA; no OpenClaw dependency is accepted.

### Ordered next actions
1. Finish review and acceptance of ROBERTA #295.
2. Extend the canonical Decision Object with the accepted BURN tracer without recomputing CMIS burn facts.
3. Repair `roberta-core` #11 CI and complete bounded one-cycle training orchestration before broader unattended scheduling.
4. After CMIS Discovery Ledger acceptance, add ROBERTA Discovery / WHAT CHANGED? / Watch adapters one at a time.
5. Rebase/repair Telegram #264 only after the core product gates above.
6. Keep Solana secondary/read-only and Controlled Execution locked.

`execution_authorized=false`
