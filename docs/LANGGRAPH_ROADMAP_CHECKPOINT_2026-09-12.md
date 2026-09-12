# ROBERTA Roadmap Checkpoint — 2026-09-12

This checkpoint supersedes the **Live checkpoint** and **Active execution order** sections dated 2026-09-10 in `docs/LANGGRAPH_ROADMAP.md`. Historical architecture, authority, Learning System, and completed-work sections in that roadmap remain unchanged until the next consolidated rewrite.

## Current accepted flagship state

Tokenized Equity / RWA Intelligence is accepted end to end through X1 Scout, Claim Integrity, protected Machine synthesis, and the Human “What exactly am I buying?” explanation.

Final regression hardening is now accepted:

- public ROBERTA PR #445 merged as `f8ca20b52a3f41ef5678a0ded141127d19758fdd`;
- public `Tokenized Equity Final Hardening` passed on Python 3.11 and 3.12;
- public repository-wide tests passed on the exact PR head before merge;
- protected `roberta-core` PR #99 merged as `cb84b27684bc70cd10b54cadb1a6b6266d52ba2b`;
- protected `Tokenized Equity Final Hardening` passed on Python 3.11 and 3.12 against exact accepted public shell `f8ca20b52a3f41ef5678a0ded141127d19758fdd`;
- full private-core CI passed on Python 3.11 and 3.12 plus pinned-shell compatibility;
- Wallet Relationship, X1 Daily Intelligence Brief, existing Human Intelligence, website/chat capability surface, and protected/public overlay coexistence remain accepted;
- `execution_authorized=false` remains invariant.

ROBERTA #431 is therefore complete and parent #418 is eligible for closure.

## Active execution order

### 1. X1 Smart Route Intelligence — ACTIVE NEXT

Upstream: `bhaygood29053-pixel/cmis#681`  
Downstream adoption: `bhaygood29053-pixel/roberta-langgraph#444`

Dependency chain:

`CMIS #681 -> X1 Scout projection -> ROBERTA #444 Pre-Trade adoption -> public beta / product proof`

CMIS #681 is the active evidence task. It must first build a bounded deterministic `xdex_multi_hop_route_intelligence/v1` contract and independently corroborate material route facts against X1 mainnet evidence where possible.

Required boundaries:

- candidate route != global route optimality;
- provider route != independent verification;
- configured cross-DEX support != observed cross-DEX execution;
- quote freshness != reserve freshness;
- quoted output != executed output;
- minimum received != guaranteed fill;
- pool fee != all-in fee;
- unexplained arithmetic difference != router/platform fee;
- network fee remains separate unless prepared-transaction semantics are proven;
- `execution_authorized=false`.

After at least two accepted bounded routing providers/venues, CMIS may add `x1_route_comparison/v1` for an exact trade size and exact candidate set. `best_route` must never imply exhaustive X1-wide optimality unless completeness is independently proven.

### 2. ROBERTA #444 — QUEUED ON CMIS #681

Adopt accepted Smart Route evidence through X1 Scout into ROBERTA Pre-Trade.

Target user outcome:

> “What route would you use for this exact X1 trade, and why?”

ROBERTA may recommend and explain using bounded verified evidence. It may not construct, sign, broadcast, custody, bridge, trade, or move value.

### 3. Public beta / product proof — NEXT MAJOR PRODUCT PHASE

After Smart Route adoption:

- keep **Ask ROBERTA** as the primary entry point;
- preserve Investigate / Ask / Compare / Watch / Discover / Brief;
- test the improved Pre-Trade workflow with real users;
- measure repeat usage, unanswered questions, evidence drill-down, confusing answers, route/pre-trade demand, and willingness to pay;
- choose the first paid feature set and API/developer surface from observed use rather than adding unrelated backend contracts.

### 4. Supporting / lower-priority tracks

- Learning Plane scheduling #275 / protected `roberta-core` #11 — supporting, not a flagship blocker.
- Telegram #264 — lower priority; rebase/revalidate only if deliberately reprioritized.
- Evaluation Laboratory — paused by owner; do not resume LAB campaigns or eval-driven protected PR #90 without explicit instruction.
- Controlled Execution — locked; no transaction/value-moving authority.

## Product phase

ROBERTA has moved beyond the main architecture-build phase. The immediate remaining technical gap is a demonstrated user-facing one: evidence-backed exact-size X1 route analysis for Pre-Trade.

After that gap closes, the dominant uncertainty is product-market proof, not another broad backend expansion.

Last reconciled: **2026-09-12 America/New_York**.
