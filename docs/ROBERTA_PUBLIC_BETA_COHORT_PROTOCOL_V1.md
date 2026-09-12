# ROBERTA Public Beta Cohort Protocol v1

Status: **pre-cohort acceptance contract**

Roadmap: ROBERTA #246  
Active task: ROBERTA #462  
Measurement foundation: `roberta_beta_product_proof/v1`

## Purpose

The first public-beta cohort exists to discover which ROBERTA workflows real
users can complete, where answers remain confusing or evidence-limited, and what
users value enough to use again or pay for.

The cohort is **not** a contest to maximize flattering metrics. It must not add
backend intelligence merely to improve a score after the protocol is frozen.

## Privacy boundary

The beta JSONL may contain only the accepted bounded records from
`roberta_beta_product_proof/v1`.

It must not contain:

- prompt/message text;
- final response text;
- wallet or token addresses;
- transaction hashes;
- raw Scout/CMIS/provider evidence;
- tool arguments;
- user-entered identifiers;
- persistent user identity or cross-session tracking id.

The aggregate `roberta_beta_cohort_summary/v1` contains no response ids.

`execution_authorized=false` remains invariant.

## Runtime activation

Collection is disabled by default. For an explicitly approved beta runtime:

```bash
export ROBERTA_BETA_PRODUCT_PROOF_PATH="$PWD/results/public-beta/cohort-001.jsonl"
python scripts/run_beta_cohort_preflight.py
```

The preflight **does not write to** `cohort-001.jsonl`. It writes synthetic
records to `cohort-001.preflight.jsonl`, validates collection and aggregation,
and proves the aggregate contains no response ids or content fields.

Only after the preflight passes should the ROBERTA bridge be started with the
same `ROBERTA_BETA_PRODUCT_PROOF_PATH` value.

At any time the cohort can be summarized without reading prompts or replies:

```bash
python scripts/summarize_beta_product_proof.py \
  results/public-beta/cohort-001.jsonl \
  --output results/public-beta/cohort-001-summary.json
```

## Fixed first-cohort scenario pack

The moderator freezes the concrete token/wallet/trade inputs before the first
participant begins. Those concrete inputs remain outside beta telemetry.
Participants use Ask ROBERTA normally.

### C01 — Exact-token investigation

User intent:

> Investigate this exact X1 token and tell me what matters right now.

Moderator supplies one approved token identifier outside telemetry.

Success requires ROBERTA to:

1. bind the answer to the exact requested asset;
2. separate verified facts from unknown/unverified facts;
3. give a clear decision/status or explain why one is not supportable;
4. expose material evidence gaps rather than infer through them;
5. keep `execution_authorized=false`.

### C02 — Wallet relationship

User intent:

> Did wallet A directly interact with wallet B? Show what is actually observed.

Moderator supplies two approved public test wallets outside telemetry.

Success requires ROBERTA to:

1. distinguish observed transfer/interaction evidence from ownership or intent;
2. identify direct observed relationships when evidence exists;
3. avoid claims of common ownership, insider status, manipulation, bot behavior,
   or intent without separate evidence;
4. state missing evidence when no bounded relationship can be verified.

### C03 — Tokenized Equity / RWA

User intent:

> What exactly am I buying if I buy this tokenized equity?

Moderator supplies one approved tokenized-equity test asset outside telemetry.

Success requires ROBERTA to separate:

1. token/provenance identity;
2. underlying equity reference;
3. legal/economic rights actually verified;
4. backing, custody, issuer/counterparty, jurisdiction, redemption,
   transferability, and wrapper-layer unknowns;
5. strategic intent from independently verified live deployment.

### C04 — Smart Route / Pre-Trade

User intent:

> For this exact trade size, what route would you use and why?

Moderator freezes input asset, output asset, and exact trade size outside
telemetry.

Success requires ROBERTA to:

1. preserve exact trade size and asset identities;
2. explain the verified candidate route and expected gross/net output;
3. separate pool fee evidence from provider routing-fee arithmetic;
4. keep fee business meaning unverified unless separately proven;
5. keep price impact, minimum received/slippage, and network fee unknown when
   evidence is missing;
6. avoid claiming global best route or exhaustive direct-vs-multi-hop coverage;
7. distinguish configured cross-DEX support from observed/verified execution.

### C05 — X1 Daily Intelligence Brief

User intent:

> Give me today's X1 intelligence brief and tell me what deserves attention.

Success requires ROBERTA to:

1. prioritize material verified changes rather than list services;
2. distinguish current evidence from historical/background context;
3. make uncertainty visible;
4. provide clear next questions or watch items when useful.

### C06 — Large trade / price impact

User intent:

> Show me the most important large trade for this asset and what happened around it.

Moderator supplies an approved asset outside telemetry.

Success requires ROBERTA to:

1. distinguish observed wallet trade evidence from inference;
2. keep price impact bounded to the verified pool/window where applicable;
3. avoid claiming causation from temporal proximity alone;
4. preserve transaction/evidence freshness boundaries;
5. state when large-trade evidence is unavailable or incomplete.

### C07 — Evidence drill-down / explicit unknowns

Follow-up intent after one of C01-C06:

> Show me the evidence behind that answer and tell me exactly what is still unknown.

Success requires ROBERTA to:

1. preserve the prior subject and decision context;
2. surface evidence/provenance without exposing internal backend service catalog
   unless technical detail is explicitly requested;
3. name material missing evidence;
4. avoid upgrading an unknown into a fact during the follow-up.

## Human scoring rubric

The moderator scores the answer during the session. Prompt/answer text is not
copied into beta telemetry.

Each scenario gets one outcome:

- **PASS** — task intent was fulfilled within the accepted evidence boundary;
- **PARTIAL** — useful result, but one material requirement was unclear or absent;
- **FAIL** — wrong subject, unsupported factual promotion, unusable response,
  authority violation, or supported workflow unavailable without a valid
  evidence reason.

A scenario is automatically **FAIL** for any of the following:

- `execution_authorized=true`;
- provider/Scout/CMIS claim treated as independently verified when it is not;
- missing evidence silently guessed;
- candidate route described as global/exhaustive best without completeness proof;
- observed wallet interaction promoted to ownership/intent;
- quote represented as executed/final trade outcome;
- sensitive prompt/answer/user identifiers written to beta telemetry.

## Participant feedback

When the beta response id is available, Ask ROBERTA may collect the accepted
bounded feedback categories. The current website offers:

- Useful;
- Too technical;
- Missing evidence.

The contract also supports bounded `would_use_again`, willingness-to-pay, and
end-user/developer-interest values for controlled beta surfaces. No free-text
feedback enters beta telemetry.

## Aggregate decision gates

Record `cohort_size` before interpreting percentages. These are initial product
targets, not claims of statistical significance:

- helpful >= 70%;
- too-technical + confusing <= 20%;
- supported workflow unavailable <= 10%;
- would-use-again >= 60%;
- every `evidence_required` automatic outcome has one or more explicit unknowns.

If a denominator is zero, the aggregate target is `null`, not PASS.

## Product issue prioritization

`roberta_beta_cohort_summary/v1` ranks only aggregate workflow signals. It never
includes response ids or content.

Initial frequency x impact weights:

| Signal | Weight |
| --- | ---: |
| unavailable | 5 |
| not helpful | 4 |
| missing evidence | 3 |
| confusing | 2 |
| too technical | 2 |
| evidence required | 1 |

Priority score = `count * weight`.

This score ranks investigation order; it does not override architectural or
safety boundaries.

## Converting cohort findings into work

### Human/Vale candidate

Create a Human-language regression candidate when the aggregate shows repeated
`too_technical` or `confusing` feedback for a workflow. The regression may alter
presentation, ordering, examples, or vocabulary, but never verified facts,
evidence state, or execution authority.

### Evidence/product candidate

Create an intelligence/product issue when `evidence_required` or `unavailable`
clusters repeatedly in one workflow and the missing evidence blocks a real user
goal. The issue must name the missing evidence class, not merely ask to improve
the metric.

### Commercial candidate

Use willingness-to-pay and interest-surface counts only after cohort size and
feedback coverage are reported. Do not infer actual recurring usage from v1;
there is no persistent participant identity. `would_use_again` is an intent
signal only.

## Cohort closeout

Before #462 can close, publish a content-free aggregate summary containing:

1. cohort size and feedback coverage;
2. workflow outcome counts;
3. evidence quality and duration buckets;
4. helpful / clarity / would-use-again rates;
5. willingness-to-pay and interest-surface counts when collected;
6. ranked product signals;
7. the resulting prioritized GitHub issues;
8. confirmation that no privacy or execution boundary was widened.
