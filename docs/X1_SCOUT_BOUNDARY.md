# X1 Scout Integration Boundary

Last reconciled: 2026-08-26

## Authority flow

```text
Roberta
  -> X1 Scout
    -> CMIS
      -> X1 Provider / verified source
```

Roberta sees only the `x1_scout_investigate` capability. CMIS and provider operations are not registered as direct Roberta tools.

## Current verified-data flow

```text
X1 Provider / verified source
  -> CMIS deterministic envelope
    -> X1 Scout structured report
      -> Roberta ToolMessage
        -> Roberta final synthesis
```

X1 Scout preserves CMIS status, facts, risk, confidence, provenance, warnings/errors, Evidence Receipt, Proof Score, and uncertainty. It does not manufacture missing market facts or strengthen coverage claims.

## Historical comparison boundary

CMIS 1.10 extends the existing `historical_compare` service with `window`, `all_available`, and `all_available_pair` modes.

For a request such as “Compare XNT and ANL over their entire history”:

```text
Roberta
  -> x1_scout_investigate(asset="XNT", compare_asset="ANL", objective=<exact request>)
    -> X1 Scout
      -> one CMIS historical_compare request
         mode="all_available_pair"
         asset="XNT"
         compare_asset="ANL"
```

The second asset is explicit user/trusted-context input. X1 Scout does not invent it. Roberta does not independently retrieve two historical series and recompute the comparison.

The all-available modes require the CMIS 1.10 service-specific capability guard. “All available” means all verified observations currently available to CMIS; it is not automatically complete asset lifetime. Returned `full_asset_lifetime_verified`, `continuous_coverage_verified`, coverage windows, gaps, and limitations remain authoritative.

## Execution boundary

X1 Scout remains read-only. Pre-trade analysis is explicit-only and analysis-only. No X1 Scout or CMIS historical result authorizes transaction construction, signing, broadcasting, custody, swaps, bridge transfer, autonomous trading, or value movement.
