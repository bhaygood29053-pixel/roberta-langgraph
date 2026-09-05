# Start Here — ROBERTA ↔ CMIS Architecture Sync

Last reconciled: 2026-09-05 (America/New_York)

For current cross-project architecture and status, read in this order:

1. `ROBERTA_CMIS_SOURCE_SYNC_BASELINE.md`
2. `docs/CURRENT_PROJECT_STATUS.md`
3. `docs/LANGGRAPH_ROADMAP.md`
4. `docs/CMIS_CONTRACT.md`
5. `docs/CMIS_ROADMAP_SYNC_2026-08-17.md`
6. `docs/CHECKPOINT_2026-09-05_FOUR_REPOS.md`
7. `docs/LEARNING_PLANE_ARCHITECTURE.md`

Authority model:

`User -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider / verified source`

Current upstream gates:

- CMIS PR #469 — final Bridge-to-XDEX #410 evidence; exact-head live final workflow green, PR still open.
- CMIS PR #470 — final five-pool X1.Ninja USD-liquidity semantic proof.
- CMIS Issue #477 — internal Web Discovery browser-capture slice; discovery-only.
- ROBERTA #314 — waits for accepted/promoted CMIS cross-chain contracts.

Earlier dated status/reconciliation files are historical snapshots and must not override the living roadmap/current-status files.

Controlled Execution remains locked.

`execution_authorized=false`
