# Human Approval — Phase 9

## Purpose

Phase 9 adds a resumable human-review boundary between Roberta's analysis/policy layers and any future consequential execution layer.

It does **not** add transaction signing, broadcasting, value movement, wallet permission changes, or execution authority.

## Authority boundary

```text
Phase 8 deterministic policy
        ↓
approval_required
        ↓
application supplies exact proposal + exact review scope
        ↓
ApprovalRequest
        ↓
LangGraph interrupt()
        ↓
human approve / reject / edit / request_more_evidence
        ↓
validated ApprovalOutcome
        ↓
deterministic next-step class
```

`approved` means the human reviewed one exact request/proposal/scope binding. It is not a reusable signing credential, wallet permission, execution token, or blanket future authorization.

## Exact proposal and scope binding

Every request carries:

- `request_id`
- `action_type`
- human-readable summary
- explicit scope
- exact JSON proposal
- deterministic policy reasons
- optional evidence summary

The proposal is canonicalized as sorted compact JSON and bound to `proposal_sha256`.

A second `binding_sha256` binds together:

```text
request_id
+ action_type
+ declared scope
+ proposal_sha256
```

An approval response must carry the exact request id, proposal hash, and binding hash. Changing the proposal changes both hashes. Changing only the declared scope leaves the proposal hash unchanged but changes the binding hash, so approval cannot silently widen scope.

Proposal JSON is recursively frozen after request construction. Checkpoint/interrupt payloads receive detached ordinary JSON copies, so mutating a source dict or UI payload cannot change the in-memory request behind an established hash.

## Canonical resume payload

`build_approval_resume_payload()` copies the exact request/proposal/binding identifiers into a resume mapping while the caller supplies the human decision. This avoids UI/runtime layers independently rebuilding security-sensitive identifiers.

## Explicit decisions only

Supported decisions:

- `approve`
- `reject`
- `edit`
- `request_more_evidence`

Approval resume input must be an explicit mapping. Booleans and yes-like strings do not count as approval. Unknown resume fields fail closed.

An `edit` must include a new proposal. The result is `edited`, not `approved`, and the changed proposal receives a new proposal hash, new binding hash, and new review request before it can be approved.

## LangGraph interrupt contract

The approval node uses dynamic `interrupt()` and an injected checkpointer. Resume uses `Command(resume=...)` with the same `thread_id`.

LangGraph restarts an interrupted node from the beginning after resume. For that reason, everything before `interrupt()` in Roberta's approval node is deterministic validation/serialization only. There are no writes, transaction-preparation side effects, signatures, broadcasts, or value movement before the interrupt.

The public `resume_approval()` helper pre-validates a decision against the paused checkpoint before sending `Command(resume=...)`. This is important because a resume value belongs to the interrupted task; malformed/mismatched input must not be delivered to that task and poison a later retry.

A fresh graph instance can resume a paused approval when it uses the same checkpointer backend and thread id. Invalid/mismatched input is rejected before delivery, and the paused request remains available for a later valid response.

## Single-request thread isolation

Checkpoint state is thread-scoped. An approval response for request A cannot be borrowed by request B in another thread because the runtime and resumed node both validate the paused request id, proposal hash, and binding hash.

An approval thread is single-request context. A pending or completed approval thread cannot be overwritten/reused for another request; a new request receives a new thread id.

A completed approval cannot be resumed again through the runtime helper.

## Secret handling

Approval proposals and checkpoint/interrupt payloads reject common secret-bearing field names, including nested variants of:

- private keys
- seed phrases / mnemonics
- keypairs
- signing keys
- encryption keys
- passwords
- credentials / API keys
- secrets

Public transaction/proposal data may be reviewed; signing secrets must remain outside approval checkpoint payloads. Do not put secrets in free-text feedback either.

## Deterministic next step

A validated outcome maps to a workflow class:

```text
approved      → proceed
rejected      → stop
edited        → re_review
more_evidence → research
```

This routing has no execution behavior. `proceed` means only that a later phase may consider the exact approved proposal. Phase 11 must independently revalidate and consume the exact approval binding before signing/broadcasting exists.

## Phase 8 bridge

`approval_request_from_policy()` accepts only a Phase 8 `PolicyDecision` whose status is `approval_required`.

Policy does not manufacture the proposal or scope. The application must explicitly supply them. This prevents a generic rule such as “value movement requires approval” from becoming permission for an unspecified transaction.

## Edit re-review

An edited proposal:

1. must belong to the previous request,
2. must bind to the previous proposal and approval-scope binding,
3. must differ from the previous proposal hash,
4. receives a new request id,
5. therefore receives a new binding hash,
6. preserves previous scope/policy/evidence context unless the application deliberately constructs a different request.

No approval carries over automatically from the previous proposal.

## Current checkpoint vs durable memory

Approval requests/decisions are current task/thread execution state and belong in LangGraph checkpoints by default.

HXMP stores durable long-term context such as approval **rules**, but a past approval decision must not become permanent authorization for current/future actions. If an audit record is later stored durably, it must be explicitly non-authorizing historical/audit context.

## Production persistence

Tests use `InMemorySaver`. Production checkpointer storage remains an injected runtime dependency; Phase 9 does not force a particular database.

## Phase 11 contract

When controlled execution is eventually introduced, it must not treat `ApprovalOutcome(status="approved")` as sufficient by itself. The execution layer must at minimum revalidate:

- exact request identity
- exact proposal hash
- exact approval binding hash
- declared approved scope
- current execution preconditions/freshness where required
- that the approval is being consumed only for the intended action

No broad wallet authority is created by Phase 9.
