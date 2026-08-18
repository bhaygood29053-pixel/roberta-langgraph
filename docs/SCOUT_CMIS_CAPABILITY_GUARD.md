# Chain Scout ↔ CMIS Capability Guard

Roberta remains above the specialist layer:

```text
User
  ↓
Roberta
  ↓
Chain Scout
  ↓
CMIS
  ↓
Chain Provider
```

Roberta does **not** call the CMIS capability endpoint directly. The shared CMIS client is a dependency used beneath Chain Scouts, and the capability handshake occurs lazily only when a Scout attempts a CMIS operation.

## Runtime behavior

Before the first CMIS service POST, the Scout-side client requests:

```text
GET /v1/cmis/capabilities
```

The response must satisfy:

- capability schema `1`;
- CMIS contract version `>= 1.6.0`;
- request path `/v1/cmis`;
- explicit classification of every advertised service for every known chain;
- consistent `state` / `callable` values;
- exact `callable_services` projection.

A successfully validated manifest is cached for that client instance. A Scout performing several CMIS operations therefore does not perform a capability GET before every POST.

## Fail-closed rules

The client does not guess capability support.

If the capability contract is unavailable, malformed, stale, or incompatible, the attempted service returns a standard `unavailable` CMIS envelope with `cmis_capability_contract_unavailable`, and no service POST is sent.

If CMIS explicitly classifies a chain/service as non-callable, the attempted service returns `unavailable` with `cmis_capability_unavailable`, and no service POST is sent.

`partial` and `bounded` capabilities are callable. Their limitations are still preserved by the normal CMIS response contract and must not be upgraded by a Scout or by Roberta.

## Architectural effect

This protects the two-repository boundary without coupling Roberta to provider details:

- Roberta decides which specialist should investigate.
- The Chain Scout plans chain-specific work.
- The CMIS client enforces the live CMIS service contract before dispatch.
- CMIS remains authoritative for deterministic data, evidence, provenance, risk, and pre-trade analysis.
- Provider-specific details remain below CMIS.

The open Solana Scout Phase 10 work can reuse this shared client after it is refreshed onto the accepted guarded baseline. No separate Roberta-to-CMIS path is needed.

## Deployment order

1. Merge and deploy the CMIS `1.6.0` capability contract.
2. Merge/deploy this Scout-side capability guard.
3. Refresh Phase 10 Solana Scout work onto that baseline so it inherits the same guard.

No signing, transaction construction, broadcasting, custody, autonomous execution, or value movement is added.
