# Five-Repository Main / Local / Runtime Checkpoint — 2026-09-11

## Accepted `main` heads at checkpoint

| Repository | Head | Checkpoint note |
| --- | --- | --- |
| `roberta-langgraph` | `150fe4976c8c589f0b8829b76fc8a713cc430bbb` | X1 Scout typed Tokenized Equity Intelligence projection accepted on `main`; latest `tests` workflow passed. |
| `cmis` | `61b39d32a9ec1237f9a3056aea000b32f17f3d3d` | CMIS 1.30 bounded Tokenized Equity Intelligence promotion accepted on `main`; latest Liquidity Scout Tests workflow passed. |
| `cmis-core` | `611b2cb1668d99c9423aedd1b9546cb07c10afe0` | Protected CMIS 1.30 Tokenized Equity production registration accepted on `main`; CMIS 1.30 Production Facade Parity passed. |
| `roberta-core` | `18fa8da9d9efc2cbc74b35930b979c21c2a732d9` | Protected X1 Daily Intelligence Brief adoption remains the current accepted protected ROBERTA head. |
| `roberta-eval` | `be1e37267081b8daa5b17c41a4d4575661517622` | Evaluation Lab remains paused by the accepted docs checkpoint. |

Documentation checkpoint commits made after these values intentionally advance the `roberta-langgraph` repository head.

## Local synchronization contract

The canonical local stack root remains:

```text
~/roberta-dev
```

The accepted synchronizer is:

```bash
cd ~/roberta-dev/roberta-langgraph
git fetch --prune origin
git switch main
git pull --ff-only origin main
bash scripts/sync_local_stack.sh
```

`scripts/sync_local_stack.sh` is authoritative for local reconciliation. It:

1. requires all five operational repositories: `cmis`, `cmis-core`, `roberta-langgraph`, `roberta-core`, and `roberta-eval`;
2. fetches/prunes each repository, refuses to overwrite real uncommitted work, and fast-forwards `main` only;
3. removes only known generated Python packaging artifacts (`build/`, `dist/`, `*.egg-info/`) before the clean-worktree gate;
4. verifies every local HEAD exactly matches `origin/main`;
5. reinstalls the accepted private CMIS core into the CMIS runtime;
6. rebuilds the assembled ROBERTA runtime with the protected ROBERTA core;
7. restarts or installs the managed `cmis-gateway.service` and `roberta-bridge.service` services;
8. checks CMIS health at `http://127.0.0.1:8765/healthz`;
9. checks ROBERTA health at `http://127.0.0.1:8766/healthz`;
10. fetches the live website from `http://127.0.0.1:8766/` and fails unless the accepted ROBERTA website markers are present;
11. prints all final repository HEADs and service status;
12. emits `LOCAL_STACK_SYNC=PASS` only after repository, runtime, and website checks complete successfully.

## Website/runtime verification boundary

The managed local website/runtime check currently verifies all of the following on live port `8766`:

- `ROBERTA — Verified On-Chain Intelligence`;
- accepted progressive-evidence UI marker `View evidence & details`;
- accepted Human Intelligence marker `ROBERTA judgment`.

A local sync is not considered complete merely because Git is current. Runtime health and the website content gate must pass as well.

## Current open work that must not be silently merged by checkpointing

- `roberta-core` PR #90 — current-X1-Scout-evidence-before-synthesis gate remains open.
- `roberta-core` PR #11 — autonomous-training one-cycle orchestration remains open and review-gated.
- `cmis` PR #549 — X1Scroll archival proof remains credential-gated; checkpointing does not authorize merge.
- `roberta-langgraph` PR #141 remains explicitly blocked on exact-byte source fidelity.
- `roberta-langgraph` PR #190 remains planning-only.
- `roberta-langgraph` PR #264 Telegram transport remains open and is not part of the accepted runtime checkpoint.

## Safety / authority boundary

This checkpoint synchronizes accepted code and verifies read-only runtimes/web presentation. It does not authorize transaction construction, signing, broadcasting, custody, trading, bridge movement, wallet control, or autonomous value movement.

`execution_authorized=false`
