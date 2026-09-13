# Cohort 001 — Participant 1 interim manual score

Status: **manual baseline frozen pending privacy-safe telemetry comparison**

Do not remediate or rerun yet. First generate `roberta_beta_cohort_summary/v1`, compare automatic telemetry with this seven-scenario manual baseline, then set the remediation/rerun order.

## Manual first-pass scores

| Scenario | Manual score | Key finding |
| --- | --- | --- |
| C01 — Exact-token investigation | PASS | Exact asset bound correctly; verified vs unknown separated; explicit evidence gaps; no execution. |
| C02 — Wallet relationship | FAIL | Supported workflow unavailable: accepted exact-transfer verifier cannot perform bounded wallet-pair discovery. Tracked by CMIS #686 -> ROBERTA #472. |
| C03 — Tokenized Equity / RWA | PARTIAL | Safely refused unsupported equity premise, but full accepted Tokenized Equity Human structure was not surfaced. |
| C04 — Smart Route / Pre-Trade | PARTIAL | Valid evidence-required stop, but Human wording incorrectly denied route-recommendation authority. Tracked by ROBERTA #473. |
| C05 — X1 Daily Intelligence Brief | FAIL | Canonical network-brief prompt misrouted to an XDEX asset lookup. Tracked by ROBERTA #474. |
| C06 — Large trade / price impact | PASS | Valid EVIDENCE_REQUIRED result: provider timeout named; no trade/impact/causality invented. |
| C07 — Evidence drill-down / explicit unknowns | PARTIAL | Correct subject/context and unknowns preserved, but normal Human response exposed internal backend terminology. |

Manual first-pass total: **2 PASS / 3 PARTIAL / 2 FAIL**.

## Hold rule

No code remediation, prompt rewriting, or scenario rerun should start until the privacy-safe automatic telemetry summary is generated and reconciled against this manual baseline.

The comparison must check:
- automatic cohort size vs seven valid manual scenarios;
- workflow classifications;
- `success` / `evidence_required` / `unavailable` outcomes;
- explicit unknown counts for evidence-required responses;
- evidence-quality distribution;
- feedback coverage if any;
- privacy invariants;
- `execution_authorized=false`;
- whether excluded/setup attempts are inflating automatic cohort size.

After reconciliation, publish the final remediation/rerun order in #466 and update parent #462.
