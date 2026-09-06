# ROBERTA Human Language Renderer v1

Status: implementation for ROBERTA Issue #378.

Renderer contract: \`roberta_human_renderer/v1\`

Input contract: protected \`roberta_human_response_decision/v1\`

Public validation contract: \`roberta_human_response/v1\`

## Purpose

The Human Language Renderer turns the accepted protected response-planning
object into normal ROBERTA prose.

It is deliberately deterministic.

It does not:

- call CMIS;
- call Chain Scouts;
- call a model;
- calculate a new risk score;
- calculate a new evidence score;
- change freshness;
- change the recommendation;
- change conviction;
- change evidence quality;
- authorize execution.

The renderer changes **presentation only**.

## Voice

ROBERTA speaks in first person when an accepted Opinion v1 recommendation exists.

Examples:

- \`AVOID\` -> "I wouldn't trade this right now."
- \`WAIT\` -> "I'd wait before acting."
- \`WATCH\` -> "I'd watch this rather than act right now."
- \`BUY\` -> "I'd be comfortable buying under the evidence I have."
- \`REDUCE\` -> "I'd reduce exposure."
- \`INSUFFICIENT_EVIDENCE\` -> "I don't have enough evidence to support a trade decision yet."

When the protected object carries an exact subject label, the renderer uses it:

> I wouldn't trade X1X right now.

## Response modes

### Quick

Quick is intentionally short:

1. direct judgment;
2. primary reason;
3. one supporting observation;
4. one key uncertainty when present;
5. conviction + evidence quality.

Quick does not dump counterevidence sections, technical contracts, receipts, or
evidence-profile tables.

### Normal

Normal is the default Human ROBERTA mode:

1. direct judgment;
2. primary decision driver;
3. up to three supporting observations;
4. material counterevidence when it exists;
5. important unknowns;
6. conviction and evidence quality;
7. what would change ROBERTA's mind.

Normal hides internal contract/service vocabulary.

### Deep Dive

Deep Dive includes the Normal response plus:

- evidence profile;
- proof/freshness states;
- technical evidence reference;
- accepted source contract;
- explicit Chain Scout / CMIS fact-authority reminder;
- execution boundary.

Deep Dive exposes technical context without recomputing the underlying evidence.

## Verification state versus economic meaning

The renderer preserves the #377 rule:

**verification != economic assessment**

For example:

\`verified liquidity = $12.81\`

may render as:

> Only about $13 of liquidity is verified. For me, that means the market is
> extremely thin and economically inadequate for meaningful trading.

It must not render:

> Liquidity PASS.

## X1X target

Normal mode is designed to produce a response shaped like:

> **I wouldn't trade X1X right now.**
>
> The biggest reason is that only about $13 of liquidity is verified. For me,
> that means the market is extremely thin and economically inadequate for
> meaningful trading.
>
> Verified measured 24h volume is zero. The mint authority is still active —
> additional supply can technically be created.
>
> There is some evidence on the other side: freeze authority is disabled, but
> that does not by itself offset the market weakness.
>
> I'm still uncertain about current market freshness and independent
> corroboration.
>
> My conviction is moderate, and the evidence quality is low.
>
> **What would change my mind:** deeper verified liquidity; fresh independently
> corroborated market activity; improved verified mint-control evidence.

Exact prose is not contractual. Source fidelity, hierarchy, mode depth, and
authority boundaries are.

## Workflow coverage

The renderer is workflow-agnostic once it receives an accepted protected Human
Response Decision Object.

Regression coverage includes:

- buy/sell/risk/liquidity recommendation families;
- X1 Compare presentation objects;
- Instant X1 Scan;
- Burn Intelligence;
- Discovery/history;
- WHAT CHANGED?;
- concentration warning;
- cross-chain provenance;
- trade price impact;
- Large-Trade Discovery;
- regulatory intelligence.

The protected runtime decides whether a given current workflow has enough
accepted canonical evidence to construct the protected response-decision object.

## Progressive disclosure

Quick and Normal hide:

- raw service names;
- raw internal contract identifiers;
- provider dumps;
- receipt IDs;
- source envelopes.

Deep Dive may expose the accepted technical source contract and evidence
reference because the user explicitly requested deeper evidence.

## Fail-closed behavior

Rendering fails when:

- input is not \`roberta_human_response_decision/v1\`;
- fact authority is not \`chain_scout_cmis\`;
- judgment authority is not \`roberta\`;
- \`read_only\` is false;
- \`fact_values_recomputed\` is true;
- \`execution_authorized\` is true;
- selected response depth is ineligible;
- recommendation is not an accepted Opinion-v1 recommendation;
- protected data cannot satisfy the public #377 Human Response Contract.

## Execution boundary

\`execution_authorized=false\`
