# X1 Intelligence Gateway — Future Roberta Roadmap

Status: **FUTURE / BLOCKED UNTIL THE LEARNING SYSTEM IS COMPLETE**

Target owner: Roberta

This roadmap defines a future Roberta sub-agent that communicates with a user-authorized agent created on the X1 Intelligence Network. It is intentionally not an active implementation milestone. The work begins only after the Roberta Learning System is accepted complete under the authoritative `docs/LANGGRAPH_ROADMAP.md` and all in-flight Learning System/source-library gates are reconciled on `main`.

The gateway is a communication/collaboration specialist. It is not a second CMIS, not a second Chain Scout, and not an execution authority.

## Goal

Give Roberta a transport-neutral sub-agent capable of securely communicating with an external X1 Intelligence agent, preserving exact remote-agent identity and response provenance, and escalating freshness-sensitive blockchain claims through the existing X1 Scout -> CMIS verification path before Roberta treats them as verified current facts.

Target interaction:

```text
User
  -> Roberta
    -> X1 Intelligence Gateway
      -> verified transport
        -> user-authorized X1 Intelligence agent
      <- remote response + provenance
    <- normalized external-agent report
  -> when live verification is required:
       X1 Scout
         -> CMIS
           -> accepted provider evidence
  -> Roberta final synthesis
```

## Canonical authority boundary

The accepted live-state hierarchy remains unchanged:

```text
User -> Roberta -> Chain Scout -> CMIS -> Chain Provider / verified source
```

The X1 Intelligence Gateway is a parallel collaboration path beneath Roberta:

```text
Roberta -> X1 Intelligence Gateway -> external X1 Intelligence agent
```

Remote-agent output is classified as **external-agent intelligence** until separately verified where verification is required.

The external agent must not:

- bypass Roberta to direct CMIS;
- create or replace CMIS Evidence Receipts or Proof Scores;
- become a trusted live-state provider by implication;
- change CMIS capability promotion or provider-trust state;
- write verified lessons into the Learning System by implication;
- authorize HXMP writes, governance changes, wallet actions, transaction execution, or Controlled Execution.

## Prerequisites / start gate

Implementation may begin only after all of the following are true:

1. the Roberta Learning System is declared complete in the authoritative roadmap;
2. Learning System retention, source-library/catalog, durability, and conversational source-management gates that remain part of the accepted Learning System plan are reconciled on `main`;
3. active source-onboarding/provenance blockers are reconciled;
4. the X1 Intelligence Network exposes at least one reproducible, documented communication path that can be contract-tested;
5. an exact user-authorized remote-agent identity can be bound to that transport without relying on display name alone;
6. a separate implementation issue/spec is accepted before runtime code begins.

Pyramid/training work does not automatically block this phase unless the authoritative roadmap explicitly makes it a Learning System completion dependency.

## Phase A — Interface discovery and contract acceptance

Status: FUTURE

Purpose: establish what communication interface actually exists before writing an adapter.

Required work:

- document the exact supported transport(s) exposed by the X1 Intelligence Network at implementation time;
- prefer documented/reproducible interfaces over guessed private endpoints;
- identify authentication, agent addressing, request/response correlation, timeout, replay, rate-limit, and delivery semantics;
- distinguish Telegram, xChat, API, websocket, webhook, or other transports as separate capability contracts rather than assuming equivalence;
- document whether communication is request/response, asynchronous message delivery, group messaging, or event streaming;
- classify every discovered interface as VERIFIED, PARTIAL, BLOCKED, or UNAVAILABLE.

Acceptance:

- one exact transport contract is accepted;
- no guessed endpoint or undocumented control path is promoted;
- secrets/private keys are not committed to source control;
- no wallet, transaction, or execution authority is introduced.

## Phase B — Remote-agent identity and provenance foundation

Status: FUTURE

Create deterministic typed contracts such as:

- `RemoteAgentIdentity`;
- `RemoteAgentTransportBinding`;
- `RemoteAgentRequest`;
- `RemoteAgentResponse`;
- `RemoteAgentProvenance`;
- `RemoteAgentCapabilityState`.

Identity must bind to the strongest exact identifier supported by the accepted transport, such as an agent id, wallet/address identity, verified bot/account id, or another accepted canonical identifier. Display names alone are insufficient when ambiguous.

Every response must preserve at least:

- exact remote-agent identity;
- exact transport/contract/version;
- request id / correlation id;
- sent/received timestamps where the transport supports them;
- conversation/thread/group identity where applicable;
- raw/normalized response hash;
- capability/availability state;
- transport limitations and unresolved fields;
- classification as external-agent intelligence rather than CMIS-verified fact.

Tampered, stale, identity-mismatched, replayed, or uncorrelated responses must fail closed.

## Phase C — First communication adapter

Status: FUTURE

Implement exactly one transport first.

Selection rule:

- choose the simplest transport that is officially supported, reproducible, and contract-testable at implementation time;
- Telegram may be a practical first adapter if it remains the easiest documented deployment/communication path;
- native xChat may be preferred when its exact client/protocol contract is documented and testable;
- do not hard-code the Roberta domain model to either transport.

Provider-neutral interface concept:

```text
send(request) -> delivery result
receive/correlate(request_id) -> remote response
health/capabilities() -> explicit transport state
```

Required behavior:

- exact remote-agent target binding;
- deterministic request ids;
- bounded timeout/retry policy;
- duplicate/replay detection;
- response size/type limits;
- explicit unavailable/partial/error states;
- no silent fallback to a different remote agent or transport;
- secrets supplied through accepted runtime secret handling only.

## Phase D — Roberta routing and specialist integration

Status: FUTURE

Add `X1 Intelligence Gateway` as a Roberta specialist.

Roberta owns the decision to call it. The gateway owns only remote-agent communication and provenance normalization.

Examples of eligible tasks:

- ask the remote agent what it has researched or observed;
- ask it to summarize its own memory/context;
- request a bounded investigation or opinion;
- coordinate a research task with the remote agent;
- retrieve a response from a named collaboration thread/group.

The gateway must not independently decide that a remote claim is verified market/blockchain truth.

Roberta should expose the source class when useful, for example:

```text
Remote X1 agent reports: <claim>
Verification state: external-agent intelligence / not yet CMIS-verified
```

## Phase E — CMIS verification escalation

Status: FUTURE

Introduce deterministic escalation rules for freshness-sensitive claims.

Examples that require the existing live-evidence hierarchy when Roberta needs current verified truth:

- price, liquidity, volume, supply, burns, balances, holders/concentration;
- validator/network/RPC availability or current configuration;
- active software/network version;
- current token authorities/tokenomics state;
- current bridge status/capacity/fees;
- current wallet/on-chain activity;
- market/risk/pre-trade facts.

Flow:

```text
external-agent claim
  -> Roberta classification
  -> X1 Scout
  -> CMIS
  -> accepted provider evidence
  -> Roberta reconciliation
```

Possible user-facing outcomes include:

- remote claim verified;
- remote claim partially supported;
- remote claim conflicts with accepted evidence;
- remote claim cannot currently be verified;
- claim is opinion/analysis rather than a verifiable fact.

CMIS remains the trust root for the facts it owns.

## Phase F — Native xChat transport

Status: FUTURE / SEPARATELY GATED

Add native xChat only after its exact protocol/client/security assumptions are reviewed and accepted.

Required review areas include:

- recipient identity/key binding;
- sender authentication;
- key rotation;
- replay protection;
- message correlation/order;
- compromised-directory risks;
- transport confidentiality/integrity assumptions;
- recovery behavior when identities or keys change.

If a wallet identity is required for Roberta messaging, use a dedicated messaging identity/wallet with no unnecessary funds or execution permissions. Do not reuse a primary funded wallet merely for messaging convenience.

## Phase G — Multi-agent collaboration

Status: FUTURE / SEPARATELY GATED

After one-to-one communication is proven, support bounded collaborative workflows such as:

```text
Roberta
  -> X1 Intelligence Gateway
      -> remote X1 agent A
      -> remote X1 agent B
  -> X1 Scout / CMIS verification as needed
  -> final synthesis
```

Potential capabilities:

- research-team requests;
- parallel independent remote-agent opinions;
- named group/thread collaboration;
- disagreement reporting;
- provenance-preserving multi-agent summaries.

Do not convert multiple agent agreement into independent factual verification. Agent consensus is not CMIS source independence.

## Phase H — Optional remote-action proposals

Status: FUTURE / NOT AUTHORIZED BY THIS ROADMAP

A remote agent may eventually return a proposed action, but proposal transport is not execution authority.

Example:

```text
Remote agent proposes action
  -> X1 Intelligence Gateway records proposal + provenance
  -> Roberta evaluates
  -> existing policy/human-review boundary
  -> STOP unless a separately accepted Controlled Execution phase authorizes the exact action
```

This roadmap does not authorize transaction construction, wallet signing, broadcasting, custody, trading, bridge transfer, autonomous value movement, remote tool execution with privileged credentials, or broad delegated wallet authority.

## Security model

Minimum controls:

1. remote-agent messages are untrusted external input;
2. prompt/instruction content in remote messages cannot change tool permissions or authority boundaries;
3. secrets and private keys never appear in logs, prompts, source control, or response provenance;
4. remote-agent identity and transport binding are exact and auditable;
5. no caller may substitute a different agent response under an accepted identity;
6. timeouts, duplicates, replays, partial delivery, and ambiguous correlation remain explicit;
7. remote memory remains owned by the remote agent unless a separately accepted export contract exists;
8. Roberta does not obtain the remote agent's private key or vault decryption authority;
9. a communication wallet/identity, if required, is isolated from funded execution wallets;
10. every authority-bearing action remains behind its separately accepted Roberta gate.

## Learning System boundary

The gateway does not automatically promote remote-agent messages into Learning System source truth or verified lessons.

If a remote message contains useful static information, a future explicit source-onboarding path may preserve it as a provenance-bearing external source only after the accepted Learning System source-management rules allow it.

If a remote interaction reveals a useful procedural lesson, it still must traverse the accepted Learning System evaluation/verification/retention path. The remote agent cannot self-approve a lesson.

## CMIS / Chain Scout boundary

The gateway never replaces the X1 Scout.

```text
X1 Intelligence Gateway = communicate/collaborate with remote agent
X1 Scout                 = chain-specific planning/interpretation
CMIS                     = deterministic current facts/evidence/risk/capability truth
Roberta                  = coordination, policy, final synthesis
```

Direct remote-agent -> CMIS access is not part of this roadmap.

## Initial acceptance test set

Before calling the first gateway production-ready, prove at minimum:

1. correct remote agent receives an exact request;
2. wrong/ambiguous identity fails closed;
3. response is correlated to the exact request;
4. duplicate/replayed response is detected;
5. timeout/unavailable state is explicit;
6. malformed/tampered response cannot become accepted output;
7. remote prompt-injection content cannot expand Roberta permissions;
8. external-agent claims remain marked with external provenance;
9. live-state verification routes through X1 Scout -> CMIS rather than being self-certified;
10. CMIS disagreement remains visible;
11. no Learning System retention occurs by implication;
12. no secret/private key leaks into logs or provenance;
13. no transaction/signing/broadcast/custody/value-movement path exists;
14. exact-head deterministic tests and independent Spec, Code/Architecture, and Authority/Safety review pass.

## Recommended implementation order after Learning System completion

1. accept interface-discovery/spec issue;
2. verify one exact X1 Intelligence transport;
3. implement remote-agent identity/provenance contracts;
4. implement one minimal communication adapter;
5. integrate the gateway as a Roberta specialist;
6. add external-agent trust labeling and CMIS escalation rules;
7. run deterministic/adversarial readiness tests;
8. promote one-to-one communication only;
9. separately evaluate native xChat;
10. separately evaluate multi-agent/group collaboration;
11. leave action execution locked until Controlled Execution receives its own future authorization.

## Product outcome

The desired mature architecture is:

```text
                           User
                            |
                         Roberta
                 ___________|____________
                |           |            |
             X1 Scout   X1 Intelligence  Learning System
                |         Gateway
               CMIS          |
                |      external X1 agent(s)
          X1 providers
```

This creates a useful separation of intelligence sources:

- remote agents contribute research, memory, collaboration, and opinions;
- the Learning System contributes provenance-bound static knowledge and separately verified learning;
- CMIS contributes current deterministic blockchain/market evidence;
- Roberta remains the single coordinator and final user-facing voice.

## Non-goals

This roadmap does not authorize:

- Controlled Execution;
- transaction preparation/signing/broadcasting;
- custody/trading/bridge value movement;
- autonomous remote tool execution;
- wallet/private-key sharing between Roberta and the remote agent;
- direct remote-agent CMIS/provider access;
- remote-agent self-verification of current facts;
- automatic Learning System/HXMP memory promotion;
- provider-trust or capability-manifest mutation;
- behavioral/ownership/intent/fraud/manipulation labels without separate accepted evidence contracts.
