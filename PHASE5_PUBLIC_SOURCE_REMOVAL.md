# Phase 5 — Public Protected-Source Removal

Status: **COMPLETE**

Phase 5 removed the protected ROBERTA implementation and runtime-support assets
from the current public repository HEAD after exact private-core parity and
source-stripped execution had already been proven.

## Current public state

Public repository: `bhaygood29053-pixel/roberta-langgraph`

Phase 5 merged-main commit:
`b17c8311fff384e85953ca244558f5b32fd056f3`

The current public `src/roberta` tree no longer contains the protected Phase 5
set:

- `learning/**`
- `memory/**`
- `policy/**`
- `prompts/**`
- `specialists/**`
- `graph.py`
- `decision_synthesis.py`
- `evidence_aware.py`
- `readiness_intelligence.py`
- `recommendation_policy.py`
- `pretrade_ux.py`

Total removed from current public HEAD: **131 files**.

Before removal, the intended protected/runtime-support set was verified
**131 / 131 exact** against `roberta-core`. Sixteen learning support assets
that were still public-only were migrated into the private core first and
included as private package data.

The public adapter `src/roberta/private_core.py` remains and fails closed when
the required private distribution is unavailable or contract-incompatible.

## Cross-repository evidence

CMIS protected implementation had already been removed from current public
`cmis` main at:

`1aab91b5be99ccf2c399b0302c18b0b10a8546fd`

Final merged-main Phase 5 Public Source Removal Gate:

- Actions run `33250303382` — **SUCCESS**
- `PHASE5_ROBERTA_PUBLIC_PROTECTED_SOURCE_ABSENT=PASS`
- `PHASE5_CMIS_PUBLIC_PROTECTED_SOURCE_ABSENT=PASS`
- `PHASE5_PUBLIC_BOUNDARY_FILES_PRESENT=PASS`
- `PHASE5_PUBLIC_SOURCE_REMOVAL=PASS`
- `PUBLIC_FALLBACK_USED=FALSE`
- `EXECUTION_AUTHORIZED=FALSE`
- `HISTORICAL_CLEANUP_COMPLETE=FALSE`

Evidence artifact:
- name: `phase5-public-source-removal-evidence`
- artifact id: `9714149562`
- digest: `sha256:0fa71c6fd2642ea6dc3e0840a127527ac687e2a44a8a489c6b75074a2c645a32`

The same run rebuilt both private cores from the protected migration baselines,
overlaid the current public shells, and reran the Phase 3 and Phase 4
end-to-end proofs successfully.

Additional merged-main regression evidence:

- ROBERTA deterministic tests `33250303376` — **SUCCESS**
- Phase 4 Split Integration Gate `33250303391` — **SUCCESS**
- PR Phase 3 Required Private Core Validation `33250256319` — **SUCCESS**

The read-only readiness workflow also successfully installed the public shell
with the private ROBERTA runtime after Phase 5. Its deployment-enforcement jobs
remain dependent on external readiness configuration and are separate from the
Phase 5 source-removal gate.

## Safety boundary

The authority chain remains:

**User -> ROBERTA -> Chain Scout -> CMIS -> Chain Provider**

Phase 5 does not authorize execution, signing, broadcasting, custody,
autonomous value movement, new fact authority, or new service promotion.

## Historical exposure

Phase 5 changes the **current public HEAD only**.

Protected blobs still exist in older public Git history until the separate
Phase 6 historical cleanup is completed. That cleanup cannot revoke copies
already cloned, forked, cached, or downloaded.
