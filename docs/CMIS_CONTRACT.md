# CMIS Contract Boundary

CMIS is Roberta's deterministic cross-chain market-intelligence service layer.
Roberta does not call CMIS directly; chain specialists such as X1 Scout own
CMIS operation selection and interpretation.

## Authority path

```text
Roberta -> X1 Scout -> CMIS -> X1 Provider
```

Verified information flows in the reverse direction.

## Initial operations

The Roberta-side typed client currently defines:

- `market_report(chain, asset)`
- `tokenomics(chain, asset)`
- `risk_check(chain, asset)`
- `pre_trade_check(chain, asset, action, amount_usd)`

Every operation names its target chain explicitly. `asset_lookup`, `rank`, and
`historical_compare` stay deferred until a concrete specialist workflow needs
them.

## Result envelope

Every result carries:

- service and operation identity
- explicit chain and normalized asset
- timestamp
- data confidence
- source identifiers
- warnings
- structured errors
- operation-specific deterministic facts

Unavailable facts remain `null`/`None`. A service/provider failure is returned
as `data_confidence="UNAVAILABLE"` plus structured errors and does not authorize
an LLM to invent missing values.

## X1 Scout integration

X1 Scout's internal state can dispatch all four initial operations while always
calling CMIS with `chain="x1"`. The current Roberta-facing X1 Scout tool still
defaults to `market_report`; agentic Scout planning is a later milestone and
will populate the internal operation without exposing CMIS directly to Roberta.

## Current implementation

`MockCMISClient` is a deterministic contract test adapter only. It supports
normal, warning, unavailable, and service-error scenarios. Connecting the
existing Liquidity Scout/X1 implementation beneath this contract is the next
provider-integration step and does not require a mass package rename.
