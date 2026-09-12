# ROBERTA Public Beta Product Proof v1

Contract: `roberta_beta_product_proof/v1`

Roadmap parent: `#246`  
Implementation tracker: `#456`

## Purpose

Measure whether people understand, repeat, and value ROBERTA during public beta without turning product analytics into another source of sensitive chain/user data.

The beta layer observes accepted ROBERTA outputs. It never changes facts, evidence state, recommendations, routing, or execution authority.

## Two record types

### `automatic_response_outcome`

Derived only from accepted final/evaluation structures. Stores coarse fields:

- anonymous random response id;
- timestamp;
- workflow label;
- success / evidence-required / unavailable outcome;
- Quick / Normal / Deep Dive response depth;
- coarse evidence quality;
- count of explicit unknowns;
- count of accepted claims/source contracts;
- duration bucket rather than exact duration;
- `execution_authorized=false`;
- `content_persisted=false`.

### `explicit_user_feedback`

User-supplied bounded choices only:

- helpful yes/no;
- clarity: `clear`, `too_technical`, `confusing`, or `missing_evidence`;
- whether evidence drill-down was used;
- optional would-use-again yes/no;
- optional willingness-to-pay: `no`, `maybe`, `yes`;
- optional surface interest: `end_user`, `developer_api`, `both`, `unknown`.

No freeform feedback text is accepted by this contract.

## Privacy boundary

Beta records MUST NOT persist:

- prompt/message text;
- final response text;
- wallet addresses;
- token/contract addresses;
- transaction hashes;
- raw Scout/CMIS/provider evidence;
- raw tool arguments;
- user-entered identifiers.

The record validator is exact-schema and fail-closed.

## Collection boundary

Storage is disabled by default.

Set `ROBERTA_BETA_PRODUCT_PROOF_PATH=/path/to/events.jsonl` to enable the append-only JSONL collector. If the variable is unset, `append_beta_record(...)` returns `False` and writes nothing.

The collector has no advertising SDK, third-party tracking SDK, or execution capability.

## Product questions this supports

- Which workflows are actually used?
- Which workflows frequently end with explicit missing evidence?
- Which answers are marked too technical or confusing?
- Do users drill into evidence?
- Would they use ROBERTA again?
- Is willingness to pay stronger for end-user workflows or a developer/API surface?

## Authority boundary

`execution_authorized=false` is mandatory on every beta record.

A beta event cannot authorize or cause transaction construction, signing, broadcasting, custody, bridge movement, autonomous trading, or value movement.
