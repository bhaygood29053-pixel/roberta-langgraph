# Phase 3 — ROBERTA Private-Core Cutover

Status: **COMPLETE**

Public runtime entrypoints depend on `roberta.private_core`, which targets the
required private facade contract `roberta-private-core/v1`.

The following public paths route through the private-core adapter:
- HTTP bridge;
- chat CLI;
- live demo;
- readiness CLI;
- package-level `build_graph` export.

There is **no public graph fallback**. If `roberta-private-core` is missing or
contract-incompatible, graph construction fails closed.

## Phase 3 validation evidence

Required-private-core split validation passed in workflow run `33227923034`
with:
- `ROBERTA_PRIVATE_CORE_REQUIRED=1`;
- `CMIS_PRIVATE_CORE_REQUIRED=1`;
- protected ROBERTA and CMIS implementation removed from the assembled public
  shells before private-wheel installation;
- `roberta-private-core==0.2.0` and `cmis-private-core==0.2.0` installed;
- deterministic User -> ROBERTA -> X1 Scout -> CMIS HTTP -> private CMIS runtime
  completed;
- `ROBERTA_TO_X1_SCOUT=PASS`;
- `X1_SCOUT_TO_CMIS_HTTP=PASS`;
- `PUBLIC_FALLBACK_USED=FALSE`.

The fallback-free ROBERTA deterministic suite passed in run `33227923032`.

## Safety state

The authority hierarchy remains:
**User -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider**

ROBERTA remains orchestration/final-synthesis authority. Chain Scouts remain
interpretive. CMIS remains authoritative for deterministic verified
facts/evidence/risk. No execution, signing, broadcasting, custody, autonomous
value movement, new fact authority, or new service promotion is authorized.

Protected implementation remains in public Git HEAD until the dedicated source
removal phase. Historical Git cleanup is separate.

## Next phase

Phase 4 broadens split-runtime integration/CI coverage and operationalizes
private-package validation before protected public source is removed.
