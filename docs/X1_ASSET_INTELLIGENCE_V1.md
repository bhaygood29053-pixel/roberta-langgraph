# X1 Asset Intelligence Packet v1

Status: implementation slice for issue #336.

## Purpose

For normal single-asset decision questions, X1 Scout should give ROBERTA a broad
verified evidence dossier instead of forcing ROBERTA to predict every narrow CMIS
service she may need before reasoning.

The authority path remains:

```text
User
  -> ROBERTA
    -> X1 Scout
      -> CMIS
        -> accepted X1/XDEX providers
```

CMIS remains authoritative for facts, deterministic risk, proof/evidence state,
freshness, conflicts, and unavailable states. X1 Scout assembles those accepted
products. ROBERTA decides which evidence matters to the user's question and owns
only the judgment.

## Contract

Scout packet:

```text
x1_asset_intelligence/v1
```

Workflow envelope:

```text
x1_asset_intelligence_workflow/v1
```

## Baseline dossier

Every Asset Intelligence request attempts these accepted Scout products:

1. Instant X1 Scan v3 product view
   - exact/canonical identity state
   - current market
   - field-scoped freshness
   - tokenomics/authorities
   - holder/concentration evidence
   - all-available verified history
   - deterministic risk
   - evidence/proof state
2. Burn Intelligence v1
3. Discovery Intelligence v1

A source may be partial or unavailable. The packet records the terminal source
status instead of manufacturing a substitute value.

## Conditional enrichments

Pre-trade evidence is attached only when the current user request supplies both:

- exact BUY or SELL side; and
- positive USD notional.

The enrichment remains read-only and analysis-only. No side or amount may be
invented by the model.

Future enrichments may add route/bridge/transaction-specific evidence, but each
must retain its own explicit input and evidence contract.

## Identity binding

The packet never joins products by symbol/name alone.

The Instant X1 Scan defines the packet subject. Other source products are
classified as:

- `verified_match` — exact canonical-id / identity-key / mint evidence matches;
- `unverified` — there is not enough exact identity evidence to join the source;
- `mismatch` — exact source and Scan subject identities disagree.

Only canonically bound sources appear in `available_sections`.
Unbound/mismatched products remain visible in `source_products` and
`unbound_sections` so ROBERTA can disclose the ambiguity without silently
collapsing native XNT and wrapped/token representations.

## Evidence completion

The packet records:

- baseline required;
- baseline attempted;
- validated products returned;
- whether every baseline attempt reached a terminal state;
- request-specific enrichments requested/returned;
- whether a decision input is ready for ROBERTA.

"Ready" means the requested evidence paths were attempted and their states are
known. It does not mean every fact is verified.

## ROBERTA behavior

ROBERTA receives more internal information than she needs to display. She should:

1. inspect the full packet;
2. select only decision-relevant facts;
3. preserve risk and evidence quality separately;
4. disclose material unknown/stale/conflicting/unbound evidence;
5. make her own `roberta_opinion/v1` judgment.

The packet itself does not recommend BUY/WAIT/SELL.

## Execution boundary

```text
facts_authority = chain_scout_cmis
judgment_authority = roberta
read_only = true
execution_authorized = false
```

No packet, pre-trade enrichment, deterministic PASS/WARN/BLOCK, or ROBERTA
opinion creates transaction construction/signing/broadcast/custody authority.
