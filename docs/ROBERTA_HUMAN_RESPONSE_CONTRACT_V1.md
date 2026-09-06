# ROBERTA Human Response Contract v1

Status: implementation for ROBERTA Issue #377.

Contract version: **roberta_human_response/v1**

## Purpose

Human Response Contract v1 is a deterministic presentation contract between the
accepted ROBERTA decision/opinion layers and final human prose.

It does not replace:

- roberta_decision/v1, which preserves accepted Scout/CMIS facts and risk;
- roberta_opinion/v1, which owns ROBERTA's recommendation, conviction, evidence
  quality, counterevidence requirement, and view-invalidating conditions.

Instead, Human Response Contract v1 says how accepted facts and an accepted
opinion are organized for a normal person.

The authority chain remains:

~~~
User
  -> ROBERTA
    -> Chain Scout
      -> CMIS
        -> verified provider / RPC evidence
~~~

Facts authority: **chain_scout_cmis**

Judgment authority: **roberta**

Execution: **unauthorized**

## The central rule

**Fact verification is not economic interpretation.**

A verified measurement answers:

> Did the accepted evidence establish this fact?

A ROBERTA economic assessment answers:

> What does that established fact mean for the user's decision?

Those two states must never collapse into one label.

Bad:

~~~
Liquidity: PASS — $12.81
~~~

Human Response v1:

~~~
verification_state = VERIFIED
fact = $12.81 verified liquidity
economic_assessment = extremely thin and economically inadequate for meaningful trading
~~~

This prevents a machine PASS/VERIFIED token from being misunderstood as
"economically healthy."

## Contract placement

~~~
roberta_decision/v1
  + roberta_opinion/v1
       |
       v
roberta_human_response/v1
       |
       v
Human renderer
~~~

Issue #377 defines the public presentation schema and validator.

Protected roberta-core Issue #72 will later populate the canonical presentation
planning fields from accepted Decision Object + Opinion evidence.

Issue #378 will later turn the validated contract into Quick / Normal / Deep
Dive prose.

## Required top-level fields

A material decision Human Response carries:

| Field | Meaning |
|---|---|
| contract_version | Must equal roberta_human_response/v1 |
| response_depth | quick, normal, or deep_dive |
| direct_answer | The answer/judgment ROBERTA will lead with |
| recommendation | Exact recommendation from accepted roberta_opinion/v1 |
| conviction | Exact conviction from accepted roberta_opinion/v1 |
| evidence_quality | Exact summary from accepted roberta_opinion/v1 |
| facts_authority | Must remain chain_scout_cmis |
| judgment_authority | Must remain roberta |
| read_only | Must be true |
| execution_authorized | Must be false |
| verification_and_interpretation_separated | Must be true |
| fact_values_recomputed | Must be false |
| primary_decision_driver | Most important accepted evidence for this decision |
| supporting_observations | 1-4 for quick; 2-4 for normal/deep_dive |
| counterevidence_status | present, none_material, or unavailable |
| counterevidence | Material evidence against ROBERTA's view when present |
| important_unknowns | Decision-relevant missing/stale/conflicting evidence |
| evidence_profile | Human-readable proof dimensions |
| what_would_change_my_mind | 1-5 evidence-bound invalidating/improving conditions |
| technical_detail | Progressive-disclosure availability/reference |

## Observation structure

Evidence-bearing presentation observations use:

~~~
{
  "fact_ref": "market.liquidity_usd",
  "verification_state": "VERIFIED",
  "interpretation": "Only about $13 of liquidity is verified.",
  "economic_assessment": "Extremely thin and economically inadequate for meaningful trading",
  "source_fact_json": "{\"value\":12.81,\"currency\":\"USD\",\"verified\":true}"
}
~~~

### fact_ref

A stable reference to the accepted Decision Object / Scout / CMIS fact.

It is not a new fact source.

### verification_state

The accepted evidence state.

Human Response v1 does not rename VERIFIED into "safe" or WARN into "bad
liquidity."

### interpretation

Natural explanation of what the accepted fact says.

### economic_assessment

ROBERTA's bounded decision meaning.

For the primary decision driver this is mandatory.

A machine status token such as PASS, WARN, FAIL, VERIFIED, UNKNOWN, or STALE is
not a valid economic assessment.

### source_fact_json

Optional.

When raw source JSON is carried, it must be validated against an accepted
source-fact map as an **exact string**. Human Response v1 does not parse and
reserialize it before comparison. Reordered keys, changed whitespace, numeric
normalization, or changed values fail the exact-match check.

This is the public #377 mechanism for the acceptance requirement:

**existing CMIS/Scout facts preserved byte-for-byte where carried.**

The normal Human renderer should still prefer fact_ref + interpretation and
keep raw source JSON behind technical disclosure.

## Opinion consistency

When the accepted roberta_opinion/v1 envelope is supplied to the validator,
these three Human Response fields must match it exactly:

- recommendation;
- conviction;
- evidence_quality.

Human Response v1 cannot silently turn AVOID into WAIT, MODERATE conviction
into STRONG, or WEAK evidence into MODERATE.

## Primary decision driver

The primary driver answers:

> What matters most to this decision?

It must point to accepted evidence and must provide a distinct human economic
assessment.

Example for X1X:

~~~
fact_ref: market.liquidity_usd
verification_state: VERIFIED
interpretation: Only about $13 of liquidity is verified.
economic_assessment: Extremely thin and economically inadequate for meaningful trading.
~~~

A primary driver is presentation prioritization. It is not new risk arithmetic.

## Supporting observations

Quick mode requires 1-4.

Normal and Deep Dive require 2-4.

The limit is deliberate: normal human responses should surface the most
material evidence rather than dump every receipt.

## Counterevidence without fake balance

The contract requires an explicit counterevidence status:

- **present** — one or more material facts push against ROBERTA's view;
- **none_material** — no material counterevidence is present in the accepted
  evidence;
- **unavailable** — evidence is insufficient to establish counterevidence.

If status is present, the list must not be empty.

If status is none_material or unavailable, the list must be empty.

This prevents the renderer from inventing a positive merely to appear balanced.

## Important unknowns

Unknowns remain unknown.

Examples:

- current liquidity freshness not verified;
- independent market corroboration missing;
- history unavailable;
- source conflict unresolved.

The Human Response Layer may explain why an unknown matters. It may not convert
it into zero, false, safe, dangerous, or any other invented fact.

## Evidence profile

Evidence profile replaces simple pass-count arithmetic as the primary human
proof explanation.

Example:

~~~
Identity / supply: STRONG
Market activity: WEAK
Freshness: UNVERIFIED
Independent corroboration: UNAVAILABLE
History: UNAVAILABLE
~~~

Accepted v1 profile states are:

- STRONG
- MODERATE
- WEAK
- VERIFIED
- PARTIAL
- UNVERIFIED
- UNAVAILABLE
- CONFLICTED
- STALE
- NOT_APPLICABLE
- UNKNOWN

A proof score or check count may still appear under technical detail.

## What would change my mind

Every material decision contract carries between 1 and 5 evidence-bound
conditions.

Each condition names one or more fact references that would need to change or
be newly established.

Example:

~~~
condition: Meaningfully deeper verified liquidity appears.
fact_refs:
  - market.liquidity_usd
~~~

This keeps ROBERTA's judgment falsifiable rather than rhetorical.

## Response depth

### quick

- direct answer;
- primary driver;
- at least one supporting observation;
- at least one evidence-profile dimension;
- evidence-bound change conditions.

### normal

Default future Human renderer target:

- direct answer;
- primary driver;
- 2-4 supporting observations;
- material counterevidence;
- important unknowns;
- evidence profile;
- what would change ROBERTA's mind.

### deep_dive

Same semantic contract as normal, with a future renderer allowed to expose more
provenance, timestamps, source scope, history, receipts, and technical detail.

Machine ROBERTA remains a separate structured projection and is not redefined
by this public Human Response contract.

## X1X acceptance example

The contract can represent the X1X assessment without calling "$12.81
liquidity" a liquidity PASS.

Expected future normal prose:

> **I wouldn't trade X1X right now.**
>
> The biggest problem is that there barely appears to be a functioning market.
> I can verify only about $13 of liquidity, and the measured 24-hour period
> shows no trading activity. The mint authority is also still active.
>
> Freeze authority is disabled and supply data checks out, but those positives
> don't offset the market weakness.
>
> **What would change my mind:** deeper verified liquidity, real trading
> activity, fresh independently corroborated market data, and an updated
> mint-authority check.

The exact prose is not the #377 contract. The structured evidence fidelity and
response hierarchy are.

## Fail-closed conditions

Validation fails when, among other cases:

- contract version is wrong;
- facts authority moves away from Chain Scout / CMIS;
- judgment authority moves away from ROBERTA;
- read_only becomes false;
- execution_authorized becomes true;
- fact_values_recomputed becomes true;
- verification/interpretation separation is disabled;
- the primary economic assessment is merely a machine status token;
- normal/deep-dive response lacks 2 material supporting observations;
- counterevidence status contradicts its list;
- evidence profile is malformed;
- no evidence-bound what-would-change-my-mind condition exists;
- carried source_fact_json does not byte-match the accepted source fact;
- accepted Opinion recommendation/conviction/evidence-quality fields change.

## Explicit non-goals

Issue #377 does not:

- select the primary driver from live evidence;
- compute conviction;
- compute evidence quality;
- change recommendation policy;
- rewrite roberta_opinion/v1;
- render final prose;
- implement conversational continuity;
- train the learning corpus;
- calculate risk;
- calculate legal compliance;
- calculate market facts;
- authorize execution.

Those responsibilities remain with their accepted owners and later #376
implementation slices.

## Execution boundary

Human Response Contract v1 is read-only.

~~~
execution_authorized=false
~~~
