# ROBERTA Human Intelligence Experience v1

Status: **PLANNED / ACTIVE IMPLEMENTATION PROGRAM**

Parent issue: #376

Implementation issues:
- #377 — Human Response Contract v1
- `roberta-core#72` — Canonical Human Response Decision Object v1 — **ACCEPTED** via protected PR #74 / merge `cff1be5bf95c29ac163dc9228bfdf4c1056762dd`
- #378 — Human language renderer + Quick / Normal / Deep Dive response modes — **ACCEPTED** via public PR #388 / merge `ee52d60079571d349a45299fc524d0ea972412f3` + protected `roberta-core` PR #76 / merge `971c49b675b5dee43d5b6d002a86b61a1a951811`
- #379 — Conversational continuity for evidence-bound follow-up decisions — **NEXT EXACT GATE**
- #380 — Human Response Learning Corpus + response-quality evaluator
- #381 — Website progressive evidence disclosure + human decision labels

## 1. Why this exists

ROBERTA already has accepted answer-first synthesis, Opinion v1, Claim Integrity, progressive technical disclosure, X1 Scout / CMIS authority separation, and multiple specialist intelligence surfaces.

The next product gap is not another large evidence source. It is making existing intelligence consistently feel like a strong human analyst:

- answer the actual question first;
- explain what matters most;
- separate verified facts from ROBERTA's judgment;
- acknowledge useful counterevidence;
- state uncertainty naturally;
- say what would change the judgment;
- continue a conversation without repeating a full machine report;
- expose raw receipts only when useful.

This program builds on closed issues #33, #45, and #51. It does not reopen or duplicate them.

## 2. Non-negotiable authority model

```text
User
  -> ROBERTA
    -> Chain Scout
      -> CMIS
        -> verified provider / RPC evidence
```

CMIS owns deterministic facts, freshness, provenance, verification state, risk primitives, historical evidence, and bounded calculations.

Chain Scouts preserve chain-specific meaning and scope.

ROBERTA owns judgment, prioritization, explanation, conversational continuity, and final synthesis.

The Human Response Layer may change **presentation and emphasis**. It may not change the underlying evidence.

## 3. Target response anatomy

For a material decision, the default Human response should generally be:

1. **Direct judgment**
2. **Primary decision driver**
3. **2-4 material supporting observations**
4. **Relevant counterevidence / positives**
5. **Important unknowns**
6. **Conviction and evidence profile**
7. **What would change my mind**
8. Optional technical detail / evidence receipts

Not every answer requires every section. Quick factual questions should remain short.

## 4. Core semantic distinction

### Verification is not economic meaning

Bad:

`Liquidity PASS — $12.81`

Better:

- Liquidity measurement: **VERIFIED**
- Verified liquidity: **$12.81**
- ROBERTA assessment: **extremely thin / economically inadequate**

The same principle applies to mint authority, freshness, volume, activity, provenance, regulatory evidence, bridge evidence, and historical coverage.

## 5. Human judgment vocabulary

When deterministic policy permits, ROBERTA may use first-person judgment such as:

- "I'd avoid this right now."
- "I'd wait."
- "I don't like this setup."
- "I'm cautiously positive."
- "XNT looks safer to trade than AGI under the evidence I have."
- "I can't verify that yet."
- "The number may be correct, but I can't confirm that it's current."
- "This trade clearly moved this pool; I can't prove it moved the whole market."

ROBERTA must never use natural language to overstate evidence.

## 6. Response-depth modes

### Quick
Direct answer, 1-2 reasons, key uncertainty.

### Normal
Default human mode:
- direct judgment;
- primary driver;
- supporting evidence;
- counterevidence;
- important unknowns;
- conviction;
- what changes ROBERTA's mind.

### Deep Dive
Adds:
- exact evidence profile;
- history/freshness;
- provenance/source scope;
- technical caveats;
- receipts and timestamps where useful.

### Machine
Existing structured Decision Object / service contract. No requirement to sound conversational.

## 7. Canonical Human Response Decision Object

Protected `roberta-core#72` owns the canonical response-planning fields.

Minimum concepts:

```text
direct_answer
recommendation_family
primary_decision_driver
supporting_evidence[]
counterevidence[]
important_unknowns[]
conviction
evidence_profile
what_would_change_my_mind[]
response_depth_eligibility
technical_detail_available
```

These fields prioritize accepted evidence. They do not recompute CMIS facts.

## 8. Evidence profile

Do not reduce evidence quality to a simple count such as "7/12 = 58%" as the primary human signal.

Preferred profile:

```text
Identity: strong
Supply/control: strong
Market activity: weak
Freshness: unverified
Independent corroboration: missing
History: unavailable
```

A numerical proof score may remain available in technical detail when useful.

## 9. Counterevidence

Material recommendations should acknowledge facts that push in the opposite direction.

Example:

> Freeze authority is disabled and supply data checks out. Those are positives, but they don't outweigh the lack of a functioning market.

Counterevidence exists to improve honesty, not to force false balance.

## 10. What would change my mind

For material opinions, this becomes a signature ROBERTA behavior.

Avoid / wait example:
- deeper verified liquidity;
- meaningful trading activity;
- fresh independently corroborated market data;
- changed mint/control state.

Positive recommendation example:
- liquidity deterioration;
- concentration increase;
- major verified selling;
- freshness failure;
- source conflict.

The condition must be tied to accepted evidence, not generic advice.

## 11. Conversational continuity

ROBERTA should handle:

- "Why?"
- "What about $50 instead?"
- "Compare that to XNT."
- "What changed since yesterday?"
- "Would you change your mind if the mint were revoked?"

Rules:

- thread context can resolve referents;
- durable context can preserve identity/preferences when safe;
- freshness-sensitive facts must be reacquired when the new question requires current evidence;
- remembered price/liquidity/volume never becomes current truth;
- focused follow-ups should not repeat the entire prior assessment.

## 12. Learning system

Issue #380 owns the Human Response Learning Corpus.

The corpus teaches:

- response hierarchy;
- wording quality;
- prioritization;
- uncertainty language;
- counterevidence handling;
- follow-up behavior;
- evidence-safe judgment.

It does **not** teach ROBERTA current market facts.

Initial target: at least **75 deterministic scenarios**, expanding to 100+.

Coverage includes:

- X1X-style microscopic liquidity / zero-activity case;
- high risk + strong evidence;
- unknown risk + weak evidence;
- stale evidence;
- source conflict;
- active mint authority;
- token comparisons;
- amount-bound pre-trade follow-ups;
- liquidity deterioration;
- concentration warnings;
- large trades / pool price impact;
- bridge/cross-chain;
- burn intelligence;
- history / WHAT CHANGED?;
- regulatory intelligence / GENIUS Act;
- multi-turn follow-ups.

## 13. Response-quality evaluator

The evaluator must report actionable dimensions, not only one opaque score.

Required dimensions:

- answer first;
- natural wording;
- correct opinion family;
- primary driver surfaced;
- fact fidelity;
- uncertainty fidelity;
- counterevidence when material;
- what-would-change-my-mind when material;
- jargon control;
- no raw provider dump;
- no unsupported causality;
- no fake real-world wallet identity/intent;
- no legal advice/compliance label;
- no execution authority.

## 14. Website integration

Issue #381 owns progressive disclosure.

Default Human display should emphasize:

- ROBERTA's judgment;
- why;
- risk;
- evidence quality;
- primary driver;
- important unknowns;
- what would change ROBERTA's mind.

Exact CMIS/Scout receipts, timestamps, provider names, and machine statuses belong behind **View Evidence** / technical detail unless needed to understand the answer.

The browser must continue to call ROBERTA. It must not calculate risk, compliance, or market intelligence itself.

## 15. Target X1X response

The exact wording is not contractual, but the product target is:

> **I wouldn't trade X1X right now.**
>
> The biggest problem is that there barely appears to be a functioning market. I can verify only about **$12.81 of liquidity**, and the measured 24-hour period shows **no volume and no transactions**. With liquidity that thin, even a small trade could move the pool dramatically.
>
> I'm also cautious because the **mint authority is still active**, meaning additional supply can technically be created. I also can't confirm that the current price, liquidity, volume, and transaction data are fresh, and I don't have independent market confirmation.
>
> Freeze authority is disabled and the supply information checks out, but those positives aren't enough to offset the market weakness.
>
> **My view:** Avoid for now.
> **Conviction:** Moderate — the negative evidence is meaningful, but current market freshness is incomplete.
>
> **What would change my mind:** significantly deeper liquidity, actual trading activity, fresh independently verified market data, and an updated mint-authority check.

## 16. Implementation order

### Phase A — Contract
#377 — **ACCEPTED** via PR #384 / merge `8ec6fbf1274543e54c2c04508fe968044c72d989`

The public [ROBERTA Human Response Contract v1](./ROBERTA_HUMAN_RESPONSE_CONTRACT_V1.md) and `roberta_human_response/v1` validator are accepted. The contract consumes accepted `roberta_opinion/v1`; it does not create a second recommendation system.

### Phase B — Protected decision object
`roberta-core#72` — **ACCEPTED** via protected PR #74 / merge `cff1be5bf95c29ac163dc9228bfdf4c1056762dd`

The protected `roberta_human_response_decision/v1` object now carries source-bound primary driver, supporting evidence, counterevidence, important unknowns, conviction, evidence profile, evidence-bound change-my-mind conditions, recommendation family, technical-detail availability, and response-depth eligibility without recomputing CMIS facts.

### Phase C — Human renderer
#378 — **ACCEPTED** via public PR #388 / merge `ee52d60079571d349a45299fc524d0ea972412f3` and protected runtime PR #76 / merge `971c49b675b5dee43d5b6d002a86b61a1a951811`.

Quick / Normal / Deep Dive human prose is now deterministic over the accepted public `roberta_human_response/v1` contract and protected `roberta_human_response_decision/v1` object. The renderer is documented in [ROBERTA_HUMAN_LANGUAGE_RENDERER_V1.md](./ROBERTA_HUMAN_LANGUAGE_RENDERER_V1.md). Protected runtime adoption requires the rendered output to remain inside Claim Integrity and falls back to the previous accepted response otherwise.

### Phase D — Continuity
#379 — **NEXT EXACT GATE**

Add evidence-safe multi-turn follow-up handling.



### Phase E — Learning and QA
#380

Build the 75+ scenario corpus and evaluator. Use failures to harden the implementation.

### Phase F — Website
#381

Add progressive evidence disclosure and human decision labels.

## 17. Acceptance gate

Human Intelligence Experience v1 is accepted only when:

- all implementation issues are merged;
- public and protected tests are green on exact accepted heads;
- at least 75 scenario cases pass;
- multi-turn stale-evidence tests fail closed;
- X1X-style output meets the human hierarchy without changing CMIS facts;
- technical detail remains available;
- Human and Machine outputs remain semantically consistent;
- no execution authority is introduced.

`execution_authorized=false`
