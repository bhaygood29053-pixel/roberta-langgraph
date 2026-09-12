# Human ROBERTA v2 — Plain Language Quality Gate

Tracking: ROBERTA #449 and #452

Status: Vale CI gate accepted; runtime Quick/Normal enforcement active in #452 implementation.

## Purpose

Human ROBERTA v1 established the correct response hierarchy, evidence-safe judgment, conversational continuity, and progressive disclosure. Real user testing still shows a narrower product defect: a response can avoid raw internal identifiers and still sound like an engineering or audit report.

Human ROBERTA v2 adds two presentation-only controls:

1. Vale checks candidate human-facing prose for language that should be translated before Quick/Normal responses are accepted.
2. The runtime Human renderer deterministically simplifies known engineering phrases in Quick/Normal output after the evidence-safe response contract is built.

Neither layer becomes an evidence, recommendation, or policy authority.

## Authority boundary

The accepted authority path remains:

```text
User
  -> ROBERTA
    -> Chain Scout
      -> CMIS
        -> verified provider / RPC evidence
```

The runtime simplifier sits after the validated public Human Response contract is built:

```text
accepted ROBERTA Human Response Decision
  -> validated public Human Response contract
  -> deterministic Human renderer
  -> Quick/Normal plain-language presentation
```

Vale remains QA around the Human presentation surface:

```text
accepted ROBERTA Human Response
  -> export evaluation candidate prose
  -> Vale RobertaHuman style
  -> PASS / warning / error
```

Neither Vale nor the runtime simplifier may:

- change a fact, number, timestamp, freshness meaning, risk result, recommendation, conviction, or evidence quality;
- suppress a material unknown because the technical wording is inconvenient;
- manufacture a simpler replacement fact;
- become current blockchain truth;
- grant transaction or execution authority.

`execution_authorized=false`

## Plain-language rule

Human ROBERTA should explain **meaning before machinery**.

Examples:

| Engineering phrasing | Human ROBERTA phrasing |
| --- | --- |
| deterministic risk engine | risk checks |
| deterministic risk result | risk assessment |
| freshness state is unverified | I can't confirm these numbers are current |
| verification state is incomplete | there are still important things I couldn't confirm |
| source contract | source details |
| provider fact time | when the source data was observed |
| canonical/decision object | internal analysis |
| independent/provider corroboration | confirmation from another source |
| Proof Score | evidence score, unless technical detail was requested |
| Evidence Receipt | evidence record, unless technical detail was requested |
| Chain Scout | chain analysis in Quick/Normal |
| CMIS | evidence service in Quick/Normal |

Domain terms that materially help the user, such as liquidity, slippage, mint authority, bridge, validator, or pool, are not automatically banned. Human ROBERTA should explain their practical consequence when the meaning is not obvious.

## Runtime depth policy

### Quick and Normal

The renderer applies deterministic phrase normalization only to the final prose after the validated evidence contract has been constructed. This keeps the transformation downstream of fact authority and prevents presentation cleanup from altering source data.

The simplifier may change wording, but it does not modify the structured Human Response contract or its underlying evidence values.

### Deep Dive

Deep Dive bypasses the runtime simplifier. Precise technical terminology, evidence references, source-contract names, and Chain Scout / CMIS authority language remain available when the user asks for technical depth.

This preserves progressive disclosure rather than deleting technical capability.

## Severity policy

### Error — blocks CI

Hard engineer-speak that should not appear in ordinary Human ROBERTA prose is implemented in:

`/.github/styles/RobertaHuman/EngineeringLeak.yml`

These phrases have straightforward human equivalents and should be translated before acceptance.

### Warning — review signal

Technical terms that may be legitimate in Deep Dive but usually need explanation in Quick/Normal mode are implemented in:

`/.github/styles/RobertaHuman/TechnicalVocabulary.yml`

Warnings do not fail the gate. They make technical-language drift visible without removing Deep Dive's ability to expose precise evidence terminology.

## Corpus integration

The existing 100-scenario Human Response corpus remains the canonical deterministic presentation fixture:

`evals/human_response_learning_v1.json`

`scripts/export_human_responses_for_vale.py` extracts only each scenario's `reference_candidate.response` into a generated Markdown document. The generated document is evaluation-only and is not committed as blockchain evidence.

Local export:

```bash
python scripts/export_human_responses_for_vale.py \
  --source evals/human_response_learning_v1.json \
  --output .vale-generated/human-response-corpus.md
```

With Vale installed locally:

```bash
vale --config=.vale.ini .vale-generated/human-response-corpus.md
```

CI uses the official `vale-cli/vale-action@v3` with Vale `3.21.0`, reports warnings, and fails on error-level RobertaHuman rules. Renderer changes also trigger this workflow and the dedicated runtime plain-language regression suite.

## Relationship to the existing evaluator

Vale and runtime presentation enforcement supplement rather than replace `roberta_human_response_quality/v1`.

The deterministic ROBERTA evaluator continues to own response invariants such as:

- answer first;
- opinion-family fidelity;
- primary driver;
- fact fidelity;
- uncertainty fidelity;
- counterevidence;
- what-would-change-my-mind;
- unsupported-causality prevention;
- continuity/freshness behavior;
- no execution authority.

Vale specializes in prose/style leakage that is difficult to cover with a short internal-jargon tuple. The runtime renderer prevents a known set of those terms from reaching Quick/Normal output in the first place.

## Product target

Quick and Normal should feel like a knowledgeable analyst talking to a person. Deep Dive can expose technical evidence when requested.

The intended transformation is:

```text
technical truth
  -> preserve exact meaning
  -> explain practical consequence
  -> use ordinary language
  -> expose technical detail only when useful/requested
```

Human ROBERTA must become easier to understand without becoming less accurate.