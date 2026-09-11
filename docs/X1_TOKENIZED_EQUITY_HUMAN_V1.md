# X1 Tokenized Equity Human — “What exactly am I buying?” v1

Parent: ROBERTA #427  
Public renderer child: #429

## Purpose

This public layer renders a protected `roberta_tokenized_equity_human_plan/v1` into a human-facing Tokenized Equity / RWA explanation without importing protected source or changing the accepted Machine/Claim Integrity authority boundary.

Public response contract:

`roberta_tokenized_equity_human_response/v1`

## Authority path

`User -> ROBERTA -> X1 Scout -> CMIS -> verified provider/source`

The renderer does not call X1 Scout, CMIS, providers, or models. It consumes a protected Human plan as data and changes presentation depth only.

## Answer order

1. What it is
2. What you actually own or are exposed to
3. What rights exist
4. Who or what you depend on
5. Where it came from
6. What the market evidence says
7. How strong or fresh the evidence is
8. Observed wallet activity
9. What remains unknown

## Response depths

### Quick
Shows the five decision-critical sections:

- what it is;
- ownership/exposure;
- rights;
- evidence;
- unknowns.

### Normal
Shows all nine sections in the accepted order without technical evidence references or limitation identifiers.

### Deep Dive
Shows all nine sections plus:

- technical evidence references;
- limitation identifiers;
- the accepted evidence class that would strengthen unresolved claims.

Response depth is presentation only. It cannot change facts, claim states, recommendation authority, or execution authority.

## Required semantic boundaries

The protected plan and public renderer preserve:

- economic exposure != shareholder or beneficial ownership;
- representation/wrapper != legal/economic equivalence;
- VERIFIED / DENIED / CONDITIONAL / EVIDENCE_REQUIRED rights remain explicit;
- backing description != backing sufficiency;
- custody description != custody safety;
- route configuration != observed asset movement or adoption;
- liquidity != volume;
- transfer != trade;
- reference/quoted/derived price != executed price;
- Proof Score/confidence != risk;
- observed transfer != ownership/identity/intent/insider/bot/manipulation/causality/risk;
- UNKNOWN remains EVIDENCE_REQUIRED, never false or zero.

## No invented recommendation

Tokenized Equity Machine v1 intentionally carries:

- `recommendation=null`
- `risk_conclusion=null`
- `legal_conclusion=null`
- `investment_conclusion=null`

The Human renderer requires those fields to remain null. This flow is an evidence explanation, not a synthetic trade or legal decision.

## Invariants

- `facts_authority=chain_scout_cmis`
- `synthesis_authority=roberta`
- `explanation_authority=roberta`
- `fact_values_recomputed=false`
- `claim_authority_widened=false`
- `new_chain_fact_added=false`
- `read_only=true`
- `execution_authorized=false`

## Acceptance path

Public #429 is accepted only when:

- dedicated Python 3.11 and 3.12 renderer gates pass;
- Quick / Normal / Deep Dive regressions pass;
- authority-widening regressions fail closed;
- existing Human Intelligence renderer coexistence passes;
- full public-shell tests pass.

After public acceptance, protected ROBERTA core will implement the `roberta_tokenized_equity_human_plan/v1` producer directly over accepted `roberta_tokenized_equity_machine/v1`.
