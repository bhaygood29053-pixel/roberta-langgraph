# X1 Smart Route Scout Projection v1

Issue: ROBERTA #447, parent #444.

## Purpose

Project the accepted CMIS `xdex_multi_hop_route_snapshot/v1` contract into a typed X1 Scout product without widening CMIS authority.

Authority path remains:

`User -> ROBERTA -> X1 Scout -> CMIS -> X1 Provider / verified source`

X1 Scout does not call XDEX directly for this capability and does not parse raw provider JSON. It consumes only the normalized CMIS snapshot.

## Accepted upstream

CMIS Smart Route Phase 1:
- `xdex_multi_hop_route_intelligence/v1`
- CMIS PR #682
- merge `1fe0aad81716d7a80ee9b7cbe2f9049e1ad0c2f8`

CMIS Smart Route Phase 2:
- `xdex_multi_hop_route_snapshot/v1`
- CMIS Issue #684 / PR #685
- merge `503a9e29e51e83bd85c4502c620d6fc38370f943`

## X1 Scout contract

`x1_smart_route_intelligence/v1`

The projection preserves:
- exact input/output mints;
- exact input amount;
- ordered route path and hop count;
- exact venue/pool/config lineage;
- pool/config context slots;
- route observation slot window;
- independently verified active reserves;
- decoded per-hop fee configuration;
- reconstructed per-hop outputs;
- aggregate gross route output;
- net output from the accepted provider arithmetic transform;
- per-hop pool fee evidence in each hop's input-token units;
- cross-DEX configured / route-available / execution-observed / execution-verified states separately.

## Explicit evidence gaps

The current accepted CMIS snapshot deliberately leaves these unresolved, and Scout must preserve them exactly:
- price impact: `EVIDENCE_REQUIRED`;
- minimum received / slippage: `EVIDENCE_REQUIRED`;
- network fee: `EVIDENCE_REQUIRED`;
- provider fact time: unverified;
- provider 50-bps business meaning: unverified;
- route optimality: not verified;
- cross-DEX execution observed: false;
- cross-DEX execution verified: false.

Scout is not allowed to translate an evidence gap into zero, false certainty, or a recommendation-strengthening assumption.

## Fee-unit boundary

Per-hop pool fees are denominated in each hop's input token. Scout preserves them as separate hop-scoped facts and does not sum raw fee amounts across incompatible token units.

The provider gross-to-net routing-fee transform is shown separately. Arithmetic verification does not prove the business meaning of the provider's fee label.

## Claims Scout must not make

The projection explicitly prevents:
- candidate route -> global optimality;
- current quote -> executed/final output;
- minimum received -> guaranteed fill;
- configured cross-DEX support -> observed cross-DEX execution;
- provider fee arithmetic -> verified fee business semantics;
- quote availability -> verified provider fact time;
- one route snapshot -> exhaustive direct-vs-multi-hop comparison.

`execution_authorized=false` remains invariant.

## Acceptance target

- ROBERTA-side CMIS snapshot validator fails closed on schema, identity, reserve, fee, slot-window, evidence-state, cross-DEX, optimality, raw-provider, and execution drift;
- X1 Scout consumes only the normalized snapshot;
- projection deep-copies CMIS evidence;
- Python 3.11 / 3.12 dedicated CI passes;
- repository-wide tests pass;
- no transaction construction, signing, broadcasting, custody, autonomous trading, bridge transfer, or value movement is introduced.

## Next dependency

After this projection is accepted:

`X1 Scout Smart Route projection -> ROBERTA #444 Pre-Trade adoption -> public beta / product proof`

ROBERTA may later recommend among accepted candidates, but global-best or exhaustive-comparison language remains prohibited until CMIS accepts a bounded `x1_route_comparison/v1` candidate set.
