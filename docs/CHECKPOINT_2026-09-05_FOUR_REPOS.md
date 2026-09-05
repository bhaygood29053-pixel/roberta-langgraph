# Four-Repository GitHub Checkpoint — 2026-09-05

## Accepted implementation heads at checkpoint start

| Repository | Visibility | Accepted implementation head |
| --- | --- | --- |
| `cmis` | public | `e3fcaa28c32143de03a88bebe1f3626e22a46573` |
| `cmis-core` | private | `e84a352f12fa2b5291a98de61603f8dece577d44` |
| `roberta-langgraph` | public | `548bf70360ecb928002b8d9fce6cc8a673b1919e` |
| `roberta-core` | private | `6627e756427f6270a7f32a243e40ad4db4df3c71` |

## ROBERTA checkpoint

Opinion v1, Asset Intelligence, Claim Integrity v1, and Compare Claim Integrity are accepted. Standalone History is the next Truth Gate.

## CMIS dependency checkpoint

CMIS PR #465 is merged with five same-fact revaluation events across five pools and `liquidity_fact_time_verified=true`.

The remaining USD-equivalence and liquidity-freshness claims are not accepted. CMIS PR #466 is the active bridge-parity follow-up, so ROBERTA must preserve the unverified boundary rather than recompute or upgrade the claim.

## Safety boundary

```text
execution_authorized=false
```
