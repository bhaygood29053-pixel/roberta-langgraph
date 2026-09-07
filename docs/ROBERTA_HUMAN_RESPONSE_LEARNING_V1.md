# ROBERTA Human Response Learning + Quality Evaluator v1

Status: implementation for ROBERTA #380.

Evaluator contract:

\`roberta_human_response_quality/v1\`

Corpus:

\`evals/human_response_learning_v1.json\`

## Purpose

The Human Response Learning Corpus teaches ROBERTA **how a strong answer should
behave** without teaching the corpus to act as blockchain truth.

It measures:

- response hierarchy;
- wording quality;
- evidence discipline;
- uncertainty disclosure;
- counterevidence;
- what-would-change-my-mind conditions;
- causal restraint;
- execution restraint;
- multi-turn continuity behavior.

It does not verify current market facts.

## Corpus authority

Every corpus record is:

\`authority=evaluation_input_only\`

\`live_market_authority=false\`

\`execution_authorized=false\`

All fixture values are synthetic/non-live.

A corpus example may contain a price, liquidity amount, burn amount, risk state,
bridge observation, regulatory state, or historical change only as a static
evaluation fixture. That value may never satisfy a user request for current
blockchain evidence.

Fresh/current truth remains:

\`User -> ROBERTA -> Chain Scout -> CMIS -> accepted provider/RPC evidence\`

## Size and coverage

v1 contains **100 scenarios** across 12 families:

1. token assessment — 10;
2. risk versus evidence quality — 8;
3. pre-trade / trade-size decisions — 10;
4. token comparisons — 8;
5. Large-Trade / price-impact explanation — 8;
6. history / WHAT CHANGED? — 8;
7. bridge / cross-chain intelligence — 8;
8. concentration warnings — 6;
9. burn intelligence — 6;
10. GENIUS Act / regulatory evidence — 8;
11. stale/conflicted/missing evidence — 8;
12. conversational follow-ups — 12.

The follow-up family includes:

- "Why?";
- "$50 instead?";
- "Compare that to XNT.";
- "Has that changed?";
- "Why are you worried about liquidity?";
- "Would you change your mind if the mint were revoked?";
- explicit chain switching;
- technical-detail follow-ups;
- simplified follow-ups;
- saved-investigation rechecks;
- sell-size changes;
- "What changed since yesterday?".

## Evaluator dimensions

Every candidate receives an explicit PASS/FAIL for:

1. \`answer_first\`
2. \`natural_wording\`
3. \`correct_opinion_family\`
4. \`primary_driver_surfaced\`
5. \`no_jargon_dump\`
6. \`fact_fidelity\`
7. \`uncertainty_fidelity\`
8. \`counterevidence\`
9. \`what_would_change_my_mind\`
10. \`no_unsupported_causality\`
11. \`no_execution_authority\`
12. \`continuity_fidelity\`

## Hard failures versus quality failures

Hard failures are:

- wrong recommendation family;
- fact-fidelity failure;
- missing material uncertainty;
- unsupported causality;
- execution-boundary violation;
- continuity/freshness-boundary failure.

Other failures are response-quality failures.

The overall v1 gate requires every applicable dimension to pass. Separating hard
and quality failures makes diagnosis explicit without allowing a good style score
to hide an evidence or safety failure.

## Actionable failure reasons

Examples:

- \`answer_not_first\`
- \`unnatural_or_overlong\`
- \`recommendation_family_mismatch\`
- \`primary_driver_missing\`
- \`internal_jargon_exposed\`
- \`fact_required_anchor_missing_or_forbidden_claim\`
- \`uncertainty_missing\`
- \`material_counterevidence_missing\`
- \`change_mind_condition_missing\`
- \`unsupported_causality\`
- \`execution_boundary_violation\`
- \`continuity_or_freshness_boundary_failed\`

The evaluator returns the dimension, code, severity, and human-readable reason.
There is no opaque model-judge score.

## Fact fidelity

Each synthetic case defines explicit evidence anchors that must remain present and
forbidden claims that must remain absent.

This does not prove that the fixture itself is a live fact. It proves only that a
candidate response stayed faithful to the fixture it was asked to render.

## Opinion fidelity

Material decision cases bind the expected Opinion-v1 recommendation family.

Changing an \`AVOID\` fixture to \`BUY\`, for example, is a hard failure even if
the prose sounds polished.

## Causality

Large-Trade and burn cases explicitly reject statements such as:

- "the wallet caused the whole market";
- "the burn caused the price";

unless a future accepted evidence contract actually proves that scope.

Pool-local mechanical effects may be described when the fixture supports them.

## Regulatory boundary

Regulatory cases allow normal caution such as:

> I can't label this compliant or non-compliant.

They reject affirmative compliance or legal-advice claims.

## Continuity evaluation

Multi-turn cases evaluate runtime metadata in addition to prose.

When a follow-up changes or rechecks freshness-sensitive state, the reference
candidate requires:

\`fresh_evidence_requested=true\`

\`market_values_inherited=false\`

Stable referents such as asset, chain, action, and changed trade amount must match
the scenario.

A "Why?" explanation may use historical judgment context without a new market
lookup, but still requires:

\`market_values_inherited=false\`

## Manual review

\`evals/human_response_learning_v1_review.md\`

contains one representative case from every family so the expected Human ROBERTA
voice can be reviewed without reading all 100 JSON records.

## Learning rule

The corpus may improve:

- wording;
- prioritization;
- explanation style;
- response depth;
- conversational continuity;
- evidence discipline.

It may not become:

- current market evidence;
- provider truth;
- CMIS truth;
- a risk result;
- a legal/compliance verdict;
- wallet identity/intent evidence;
- execution authority.

## Execution boundary

\`execution_authorized=false\`
