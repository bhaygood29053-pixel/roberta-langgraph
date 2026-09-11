# Checkpoint — System-Wide Evidence Completion v1

Date: 2026-09-11 (America/New_York)

Status: **ACCEPTED ON MAIN**

## Accepted merge chain

| Repository | Accepted change | Main merge SHA |
| --- | --- | --- |
| `cmis-core` | Protected system-wide Evidence Completion producer | `3ca00f41821b88451efae949e9e58909398cfdad` |
| `cmis` | Public `cmis_evidence_complete_response/v1` contract documentation | `32066433d05b49a9278ecd4a8aecfbcd0bd3aa30` |
| `roberta-core` | Protected validation/projection of CMIS Evidence Completion | `170d9394c440532c559bad9a171f2a952e185538` |
| `roberta-langgraph` | Public CMIS envelope typing + system-wide ROBERTA adoption | `2c63cd55e8136475714a4fd3d2c54488e9126f9e` |

All coordinated PR acceptance suites passed before merge. Post-merge CMIS, CMIS Core, ROBERTA Core, and ROBERTA public-shell tests also passed for the accepted merge heads.

## Product invariant

Every normal service response routed through:

```text
User -> ROBERTA -> Chain Scout -> CMIS
```

now passes through the same protected CMIS evidence post-processing path. CMIS centrally attaches:

- Evidence Receipt v1;
- Proof Score v1;
- `cmis_evidence_complete_response/v1`.

The public CMIS shell separately attaches the accepted top-level response-freshness contract. Existing Chain Scout reports already consume ROBERTA's protected `evidence_context`, so the completion state is inherited system-wide without adding one routing patch per service.

## Completion states

- `COMPLETE` — no material unresolved evidence remains inside the exact returned service scope.
- `PARTIAL` — useful evidence exists, but material evidence is stale, conflicting, unknown, incomplete, or unavailable.
- `BLOCKED` — the requested service result is unavailable, ambiguous, or error-like and the requested judgment must fail closed.

## Critical distinction

Evidence Completion does **not** mean that every CMIS service is called for every user question, and it does not manufacture capabilities that do not exist.

It guarantees that the returned service scope identifies what CMIS actually verified and what remains unavailable. For example, a pre-trade response may be `PARTIAL` when identity, current market evidence, liquidity, trade-size analysis, freshness, Evidence Receipt, and Proof Score are available while expected slippage, route quality, fee modeling, or transaction simulation remain unproven.

ROBERTA must distinguish:

```text
checked_and_unavailable
```

from:

```text
not_present_in_the_returned_evidence_scope
```

and must never convert either condition into a model estimate, zero, or a stronger proof/risk claim.

## Safety invariants

The completion contract may not:

- rewrite service facts;
- recompute risk;
- strengthen Proof Score;
- turn missing evidence into a fact;
- convert `PARTIAL` or `BLOCKED` to `COMPLETE`;
- authorize execution.

The accepted boundary remains:

```text
risk_separate_from_proof = true
facts_recomputed = false
risk_recomputed = false
status_rewritten = false
execution_authorized = false
```

## Local/runtime handoff

GitHub acceptance does not by itself prove the user's WSL runtime has pulled these merge heads. The canonical local refresh remains:

```bash
cd ~/roberta-dev/roberta-langgraph
git fetch --prune origin
git switch main
git pull --ff-only origin main
bash scripts/sync_local_stack.sh
```

Local acceptance requires the script to finish with `LOCAL_STACK_SYNC=PASS` after syncing all five operational repositories, rebuilding the protected overlays, restarting CMIS/ROBERTA, and checking the live website/runtime.
