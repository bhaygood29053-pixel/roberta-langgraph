# ROBERTA Conversational Continuity v1

Status: implementation for ROBERTA #379.

## Goal

ROBERTA should understand short follow-ups such as:

- "Why?"
- "What about $50 instead?"
- "Compare that to XNT."
- "Has that changed?"
- "Would you change your mind if the mint were revoked?"

without forcing the user to restate the entire prior question and without
turning checkpointed market data into current truth.

## Transport boundary

The local HTTP bridge now accepts an optional:

\`thread_id\`

When supplied, the bridge invokes the already-accepted LangGraph checkpoint
path for that thread.

The website uses its existing chat ID as the bridge thread ID.

The browser no longer pastes recent assistant/user prose into the next message.
The exact visible follow-up is sent as the new user message.

This matters because historical assistant prose may contain old market values.
Those values belong to checkpoint history, not to the new user instruction.

## Local checkpoint implementation

The local bridge runtime uses \`InMemorySaver\`.

Therefore:

- continuity survives multiple requests while the bridge process remains alive;
- separate thread IDs remain isolated;
- the checkpoint state does not survive a bridge process restart;
- browser-local visible history may survive longer than runtime checkpoint state;
- this is not durable HXMP memory.

A future durable checkpoint backend can replace the in-memory backend without
changing the authority boundary.

## Authority boundary

Checkpoint state may preserve stable conversational context such as:

- prior asset referent;
- prior chain;
- prior trade side;
- prior requested amount;
- prior comparison referent;
- prior user question and ROBERTA judgment.

Checkpoint state does **not** establish current:

- price;
- liquidity;
- volume;
- transaction activity;
- market cap;
- holder state;
- risk score;
- freshness;
- regulatory state;
- wallet behavior.

Fresh/current decision evidence continues to require:

\`ROBERTA -> Chain Scout -> CMIS -> accepted provider/RPC evidence\`

## Protected resolver

Protected \`roberta-core\` implements:

\`roberta_conversation_continuity/v1\`

The resolver reads only stable request/routing fields from an accepted prior
specialist tool call. It never copies arbitrary tool arguments and explicitly
sets:

\`market_values_inherited=false\`

Supported first slice:

### Explanation

"Why?" / "Why are you worried about liquidity?"

ROBERTA may explain the basis of the earlier judgment without a new market
request, but must describe that evidence as the basis of the earlier answer and
must not imply it was reverified now.

### Trade resize

Prior:

"Should I buy $500 of AGI?"

Follow-up:

"What about $50 instead?"

The protected resolver carries forward:

- X1;
- AGI;
- BUY;

and replaces only the requested amount with $50.

The changed trade decision requires a new Scout/CMIS evidence pass.

### Referential compare

Prior asset: AGI

Follow-up:

"Compare that to XNT."

ROBERTA resolves AGI as the prior asset and performs a current first-class X1
Compare against XNT.

### Market recheck

"Has that changed?" / "Is that still true?" / "What changed since yesterday?"

The prior asset can be reused as identity context, but the prior market snapshot
cannot satisfy the current request. A new Scout request is mandatory.

### Hypothetical

"Would you change your mind if the mint were revoked?"

ROBERTA may reason about the prior judgment's invalidation conditions without
pretending the mint has actually been revoked.

## Fail-closed behavior

For freshness-sensitive follow-ups, the protected graph requires a current-turn
Chain Scout call.

If the model attempts to answer from checkpoint history instead:

1. one constrained retry requires the relevant Chain Scout;
2. if the retry still avoids fresh evidence, ROBERTA returns a bounded failure
   explaining that the earlier snapshot will not be reused as current truth.

A ToolMessage from an older user turn cannot satisfy this gate.

## Chain semantics

A stable referent remains on the prior chain unless the current user explicitly
names another chain.

An explicit chain switch prevents implicit inheritance.

## Execution boundary

Continuity changes conversation routing only.

It does not grant transaction construction, signing, submission, broadcasting,
custody, trading, or value movement.

\`execution_authorized=false\`
