# Phase 6 — Historical Git Cleanup and Migration Closure

Status: **FINAL VALIDATION**

Phase 6 rewrote the active public ROBERTA branch/tag history to remove the
protected ROBERTA implementation paths from every reachable public ref while
preserving the public repository's branch/tag structure.

## Rewritten history

Historical cleanup workflow:
- Actions run `33252100878` — **SUCCESS**
- pre-rewrite ref-map artifact: `phase6-roberta-pre-rewrite-refs`
  - artifact id: `9714673659`
  - digest: `sha256:3a24bfb53e7eafc184385b00a07ce29c4b08c766a43e940324446a700db37490`
- post-rewrite ref-map artifact: `phase6-roberta-post-rewrite-refs`
  - artifact id: `9714676327`
  - digest: `sha256:fd115956b4cce3361b3b731437f45696bb8fc16ee27c1291224d5ee041eba005`

The rewrite removed these protected paths from all rewritten branch/tag
histories:
- `src/roberta/learning/**`
- `src/roberta/memory/**`
- `src/roberta/policy/**`
- `src/roberta/prompts/**`
- `src/roberta/specialists/**`
- `src/roberta/graph.py`
- `src/roberta/decision_synthesis.py`
- `src/roberta/evidence_aware.py`
- `src/roberta/readiness_intelligence.py`
- `src/roberta/recommendation_policy.py`
- `src/roberta/pretrade_ux.py`

The rewrite gate verified the pre-rewrite main commit was no longer reachable
from the rewritten local refs, verified no protected path remained in any
rewritten head/tag, force-pushed the rewritten refs, and verified the remote ref
count was preserved.

## Steady-state public boundary

Migration-era Phase 3/4/5 public reconstruction workflows were retired. The
public repository no longer reconstructs private implementation from historical
public commits.

The normal public test workflow now verifies:
- protected ROBERTA paths are absent from current public HEAD;
- `roberta-private-core` remains mandatory;
- missing private core fails closed;
- no public fallback exists;
- execution authorization remains false.

Closure-branch public-boundary test: Actions run `33252371119` — **SUCCESS**.

Readiness replay is now a deployment/private-runtime responsibility. The public
manual readiness workflow checks the deployment boundary without reconstructing
private code.

## Safety boundary

The authority chain remains:

**User -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider**

No execution, signing, broadcasting, custody, autonomous value movement, new
fact authority, or new service promotion is authorized by this migration.

## Important limitation

This rewrite removes protected paths from the public repository's active
branch/tag history. It cannot revoke copies already cloned, forked, cached, or
downloaded, and Git hosting infrastructure may retain unreachable objects for
some period after refs are rewritten.

Phase 6 is complete once this closure state is merged to `main` and the same
public-boundary test passes from merged `main`.
