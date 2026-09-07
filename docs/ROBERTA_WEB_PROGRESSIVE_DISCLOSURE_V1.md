# ROBERTA Website Progressive Evidence Disclosure v1

Status: implementation for ROBERTA #381.

## Goal

Make the Human ROBERTA website reflect the accepted Human Intelligence
Experience v1 hierarchy:

1. ROBERTA's judgment;
2. concise human explanation;
3. primary decision driver;
4. risk and evidence quality as separate concepts;
5. important unknowns;
6. what would change ROBERTA's mind;
7. optional evidence / technical detail.

The conversation remains the product. Evidence inspection is optional.

## Authority boundary

The browser remains a presentation and transport layer.

It may:

- display ROBERTA's returned text;
- recognize already-accepted Human Response wording for presentation;
- copy an explicit returned Risk, Evidence quality, Freshness, or Conviction label;
- organize returned text into human-readable UI regions;
- ask ROBERTA for additional evidence, technical detail, charts, or a fresh recheck.

It may not:

- call CMIS directly;
- call chain providers directly;
- calculate risk;
- calculate compliance;
- calculate freshness;
- infer a new market fact;
- convert a machine PASS/WARN/BLOCK into an economic conclusion;
- authorize or execute a transaction.

All evidence actions continue through:

User -> website -> ROBERTA -> Chain Scout -> CMIS

## Human decision labels

The website can project a compact ROBERTA judgment badge from the accepted
direct-answer vocabulary already returned by ROBERTA.

Examples include:

- AVOID;
- WAIT;
- CAUTION;
- BUY CANDIDATE;
- HOLD;
- REDUCE;
- EXIT;
- INSUFFICIENT EVIDENCE.

This is presentation-only normalization.

For example:

"I wouldn't trade X1X right now."

may display an AVOID badge because the underlying ROBERTA answer already made
that judgment. The browser does not independently decide that X1X should be
avoided.

If a recognized judgment is not present, the browser shows no invented judgment
badge.

## Risk is not evidence quality

The previous website used one generic status-color helper. That could make
HIGH appear green regardless of meaning.

v1 separates field-specific presentation.

### Risk

- high / very high / severe / critical -> adverse styling;
- medium / moderate -> caution styling;
- low / very low -> favorable styling.

The browser is styling an explicit returned risk label only. It does not derive a
risk level.

### Evidence quality

- strong / very strong / high / verified -> strong-evidence styling;
- moderate / partial -> caution styling;
- weak / low / unverified / insufficient -> weak-evidence styling.

### Freshness

- verified / fresh / current -> fresh styling;
- partial / unknown -> caution styling;
- stale / unverified / unavailable -> degraded styling.

### Raw machine statuses

Raw tokens such as PASS, WARN, BLOCK, PARTIAL, or VERIFIED use neutral
machine-status styling in normal answer text.

They are not colored as though they were automatically ROBERTA's economic
judgment.

## Progressive disclosure

Every assistant answer exposes a native HTML details/summary control labeled:

View evidence & details

Inside that disclosure the user can:

- ask ROBERTA for evidence;
- request technical detail;
- recheck current data.

The side inspector also contains a native:

View evidence & technical detail

disclosure.

The browser does not fetch evidence separately. These controls send a follow-up
to ROBERTA using the accepted #379 thread continuity path.

## Human-first inspector

The optional inspector now separates:

- ROBERTA judgment;
- Decision labels;
- Primary driver;
- Important unknowns;
- What would change her mind;
- Selected on-chain identifier;
- Evidence & technical detail.

The primary-driver, unknowns, and change-my-mind displays copy text already
present in ROBERTA's answer. Missing sections are shown as missing rather than
invented.

## Accessibility

Evidence disclosure uses native HTML details and summary controls, which are
keyboard operable without a custom keyboard interaction model.

Visible focus styles are provided.

The existing side-inspector collapse button now updates:

- aria-expanded;
- aria-label.

## Mobile behavior

The right-side inspector remains hidden on smaller screens to protect the
conversation area.

Inline View evidence & details remains available with every ROBERTA answer, so
progressive disclosure is still available on mobile.

## Existing product behavior preserved

v1 preserves:

- one universal ROBERTA conversation surface;
- browser-local Chat History;
- Saved investigations;
- recheck controls;
- Clear Chat / Clear History;
- service examples;
- entity investigation;
- chart/evidence/technical follow-ups;
- explicit thread_id continuity;
- /v1/roberta as the only intelligence request path;
- analysis-only / no-execution boundary.

## Execution

The website remains read-only.

execution_authorized=false
