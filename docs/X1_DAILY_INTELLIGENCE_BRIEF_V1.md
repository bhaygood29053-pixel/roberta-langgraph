# X1 Daily Intelligence Brief v1 — ROBERTA Foundation

Status: contract-only / runtime reliance not authorized  
Issue: ROBERTA #412  
Accepted upstream foundation: CMIS #635 / PR #636  
Current live dependency: CMIS #637

## Purpose

ROBERTA needs a concise X1 intelligence brief that is more useful than a raw
feed while remaining faithful to CMIS evidence.

The public ROBERTA foundation has three layers:

```text
CMIS x1_intelligence_brief_inputs/v1
  -> X1 Scout x1_daily_intelligence_brief/v1
    -> roberta_daily_intelligence_brief_decision_input/v1
      -> protected roberta_decision/v1 (future, after CMIS #637)
```

The public repository does **not** recreate the protected canonical Decision
Object builder. It prepares a typed, fail-closed input for that protected layer.

## Human product structure

The typed Scout brief exposes:

1. **What changed** — exact accepted CMIS brief items.
2. **Why it matters** — ROBERTA presentation basis only; never a new chain fact.
3. **Evidence** — exact source service/contract/fact-time/status/evidence metadata.
4. **What is unknown / incomplete** — explicit coverage limitations and unavailable/error classes.
5. **What to watch next** — bounded follow-up candidates, not predictions.

## Claim Integrity

`roberta_daily_intelligence_brief_claim_integrity/v1` rejects upgrades from:

- warning level -> risk severity;
- large trade -> whale/insider/manipulator;
- wallet address -> real-world owner;
- sequence/activity -> causality;
- first Discovery observation -> launch time;
- bounded empty result -> “nothing happened on X1”;
- presentation basis -> new blockchain fact;
- pre-#637 foundation -> live runtime authority.

The brief also preserves:

```text
facts_authority = chain_scout_cmis
judgment_authority = roberta
provider_truth_certified = false
complete_x1_ecosystem_coverage_verified = false
execution_authorized = false
```

## Runtime boundary

CMIS #635 is accepted as a **non-promoted foundation**. Therefore this public
ROBERTA tracer bullet accepts only the non-promoted foundation shape:

```text
public_service_promoted = false
scout_reliance_promoted = false
```

That is deliberate. It allows type/UX/Claim Integrity work to be accepted
without pretending X1 Scout can call the service live.

CMIS #637 must separately promote the service through protected runtime and
explicit Scout reliance. A later ROBERTA adoption PR may then replace the
foundation-only source adapter with the accepted runtime handshake.

No transaction construction, signing, broadcasting, custody, trading, bridge
transfer, or autonomous value movement is authorized.
