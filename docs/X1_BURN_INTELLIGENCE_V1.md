# X1 Burn Intelligence v1

Status: accepted X1 Scout consumption contract over first-class CMIS Burn Intelligence.

## Purpose

`x1_burn_intelligence/v1` is the X1 Scout projection of the accepted CMIS 1.15.0 `burn_intelligence/v1` service. CMIS remains the deterministic source of burn facts; X1 Scout validates and projects those facts without recalculating burn, emission, circulating-supply, historical-price, valuation, or Proof Score state.

Canonical authority:

```text
User / transport
  -> ROBERTA
    -> X1 Scout
      -> CMIS burn_intelligence/v1
        -> accepted CMIS tokenomics / burn-scanner evidence
          -> X1 provider / verified source
```

The first-class CMIS service deliberately reuses the accepted CMIS tokenomics/burn-scanner foundation. It is not a second burn parser or arithmetic path.

## Accepted CMIS source

The source envelope must be:

```text
service = burn_intelligence
chain = x1
status in {ok, partial, unavailable}
data.contract_version = burn_intelligence/v1
execution_authorized = false
```

For an available burn result, the exact resolved X1 mint in the envelope asset must match the data mint. `data.burn_metrics` remains CMIS-owned and includes the accepted burn contract:

- explicit availability/status and `lifetime_total_burn_verified`;
- 1h / 24h / 7d / 30d windows;
- per-window coverage verification;
- burn and mint amounts/event counts only where the window is verified;
- burn-to-emission ratio, net issuance, and issuance state;
- 24h / 7d / 30d equal-period comparisons;
- comparison states `AVAILABLE`, `NO_CHANGE_ZERO_BASE`, `NEW_BURN_ACTIVITY`, or `INSUFFICIENT_COVERAGE`;
- null percent for non-numeric comparison states;
- burn-time valuation and its completeness state;
- independently gated circulating-supply context;
- coverage and observation metadata.

If CMIS marks burn metrics unavailable, X1 Scout preserves that state. It must not manufacture zero burn, zero events, lifetime burn, a comparison, or a valuation from absence.

## X1 Scout projection

The Scout product contract is:

```text
contract_version = x1_burn_intelligence/v1
product = x1_burn_intelligence
chain = x1
execution_authorized = false
```

It preserves the requested asset, exact CMIS-resolved asset identity, complete validated `burn_metrics`, observation time, confidence, sources, warnings/errors, Evidence Receipt, Proof Score, and explicit Proof Score/risk separation. The projection deep-copies accepted CMIS state and performs no burn arithmetic.

## Human and Machine ROBERTA

Protected `roberta_decision/v1` accepts this Scout product as workflow `x1_burn_intelligence`. Human ROBERTA and Machine ROBERTA render from the same canonical burn facts.

Human presentation may organize or label the data but may not:

- relabel verified-observed cumulative burn as lifetime total without `lifetime_total_burn_verified=true`;
- calculate a new percentage from current/prior amounts;
- replace null comparison states with infinity or zero;
- substitute current/nearest/interpolated prices for burn-time valuation;
- infer circulating supply;
- create a burn-derived risk score or trade recommendation.

## Fail-closed behavior

Reject or convert to an unavailable/error boundary when the dedicated CMIS service contract is absent, stale, weakened, malformed, on the wrong chain, has mismatched mint identity, weakens required coverage/comparison semantics, collapses Proof Score into risk, or grants execution authority.

The Scout requires the accepted CMIS 1.15.0 capability promotion before dispatch. Solana Burn Intelligence remains unavailable in v1.

## Non-goals

No second burn scanner, second burn parser, ROBERTA-side burn arithmetic, ROBERTA-side valuation engine, burn-derived risk score, wallet authority, token burning, transaction construction/signing/broadcasting, trading, custody, or Controlled Execution.

`execution_authorized=false`
