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

## Exact-mint normalized identity boundary

For an address-shaped X1 asset request, X1 Scout first checks whether the live CMIS capability manifest accepts `x1_asset_identity/v1` under CMIS 1.11 or newer. Only then may it call CMIS `asset_lookup` as an identity preflight.

```text
exact requested mint
  -> X1 Scout capability gate
    -> CMIS asset_lookup
      -> CMIS Token Metadata + exact-mint XDEX reconciliation
        -> normalized mint-rooted identity
          -> X1 Scout preserves result
```

X1 Scout does not decode Metaplex accounts, compare Metaplex/XDEX labels, select a different mint, verify URI contents, or infer safety/legitimacy from descriptor agreement. It preserves CMIS states including `descriptor_conflict`, `xdex_unavailable`, and `metadata_unavailable`.

Symbol-based requests do not trigger this exact-mint preflight and retain existing CMIS behavior.


## Full asset assessment boundary

A full/complete/comprehensive X1 asset assessment or due-diligence request is a
deterministic multi-service objective rather than a model-selected ranking query.

The accepted read-only plan is:

```text
market_report
rank
tokenomics
historical_compare(mode="all_available")
risk_check
```

All five CMIS results are preserved as separate Scout investigations. The
`risk_check` result remains the primary/top-level result so ranking or market
status cannot be mistaken for deterministic risk. The historical request uses
all verified observations currently available to CMIS and preserves the same
non-lifetime/non-continuity limitations described below.

A ranking phrase inside a full assessment does not convert the objective into a
rank-only plan. Conversely, a genuinely ranking-only request remains rank-only.

For symbol-only `XNT` requests, X1 Scout does not infer that native XNT and a
wrapped/token representation are identical. Per-investigation CMIS asset
descriptors are preserved. If a CMIS result identifies a wrapped descriptor,
the Scout emits an explicit native-versus-wrapped scope warning and requires
stronger identity evidence before Roberta may treat those representations as
the same analytical subject.

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
