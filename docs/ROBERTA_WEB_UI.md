# ROBERTA Local Web UI

The ROBERTA bridge now serves a local browser interface from the same process that owns `/v1/roberta`.

## Start

Use the existing ROBERTA bridge command or systemd unit. With the default local configuration:

```text
http://127.0.0.1:8766/
```

Health remains available at:

```text
http://127.0.0.1:8766/healthz
```

The website sends user requests only to:

```text
POST /v1/roberta
{"message":"..."}
```

It does not expose CMIS/provider tool controls and does not add a direct browser -> CMIS path.

## Service surface

The interface presents the accepted user-facing ROBERTA services, including:

- Instant X1 Scan v3;
- Asset Overview;
- Compare Two Assets;
- Risk Assessment;
- Tokenomics & Authorities;
- Liquidity Analysis;
- Historical Analysis;
- Market Activity;
- Concentration Change Intelligence;
- CMIS 1.18 pull-only Concentration Warning Intelligence;
- Rank X1 Assets;
- Pre-Trade Analysis;
- Evidence Quality Report;
- Burn Intelligence;
- Discovery Intelligence;
- What Changed?;
- Full Assessment;
- Alert & Status Key;
- natural-language ROBERTA questions;
- configured Solana read-only Market Report, Tokenomics, and Risk for exact mints.

Warp / bridge-flow intelligence is intentionally not exposed as a completed runnable service while its CMIS coverage and supply gates remain open. The website does reflect the newer accepted evidence checkpoint: exact Warp config semantics, canonical settled-event pairing, wallet-history response semantics as corroboration only, and current message-universe counter/account closure are accepted foundations. Route-wide 24h/7d/30d totals and verified bridged supply remain unavailable pending CMIS #441/#409, followed by #410 and ROBERTA #314 adoption.

## Trust and safety invariants

The interface preserves the repository architecture:

```text
User
  -> ROBERTA
    -> Chain Scout
      -> CMIS
        -> verified provider/source
```

The browser never selects or calls CMIS/provider tools directly. Missing evidence remains unknown/unavailable. Proof remains separate from deterministic risk. A PASS is not permission to trade.

`execution_authorized=false` remains invariant.

## Authentication

Default loopback use requires no bearer token. If `ROBERTA_API_KEY` is configured, the UI includes a Connection panel where the operator may enter the token. The token is stored only in browser session storage and is sent as a Bearer token to `/v1/roberta`.

Do not expose the loopback bridge to an untrusted network merely to make the UI externally reachable. Non-loopback deployment remains subject to the existing bridge security boundary.


## Solana scope

The website reflects the accepted Solana Scout surface without claiming X1/Solana parity. Solana cards are marked **Configured** because the provider path is disabled by default and must be explicitly enabled against an accepted CMIS deployment.

The only promoted Solana web options are:

- market report;
- tokenomics / authorities;
- deterministic risk;
- exact-mint identity handling required by those services.

Solana history, rank, pre-trade, concentration, burn, discovery, warning, and other X1-specific intelligence services are not presented as Solana capabilities.

## Learning Plane

ROBERTA's Learning Command Center remains a separate loopback, read-only operator surface. The market/intelligence website does not start training, mutate the Pyramid ledger, approve lessons, or create a new learning-control authority path.

## Animated intelligence field

The public ROBERTA hero uses an original procedural rendering layer rather than a GIF, video, or copied visual asset. A responsive canvas draws the particle profile, flowing evidence strands, animated route nodes, and orbital intelligence field in real time.

The renderer is deliberately bounded for the local UI: device-pixel ratio is capped, particle density scales with viewport area, animation pauses when the page is hidden, ResizeObserver rebuilds the field only when needed, pointer interaction is lightweight, and prefers-reduced-motion renders a static frame instead of continuous motion.

The animation is presentation only. It does not create a browser-to-provider path, does not alter evidence state, and does not change the invariant execution_authorized=false.

## ROBERTA Opinion v1 on the website

The existing website adopts the accepted protected `roberta_opinion/v1` behavior without creating a browser-side judgment engine. Opinion-bearing decision questions remain normal `/v1/roberta` requests and are enforced by ROBERTA's protected decision-synthesis layer.

For those intents, Human ROBERTA is expected to lead with `My recommendation`, then disclose `Conviction`, `Evidence quality`, `My view`, the best material evidence against the view, and `What would change my mind`. The website exposes a dedicated **ROBERTA Opinion** capability card and formats those explicit opinion-header fields for readability.

The website does not calculate a recommendation, alter CMIS facts, derive risk, or create a separate opinion authority. Facts and deterministic risk remain `Chain Scout -> CMIS`; judgment remains ROBERTA-owned. `execution_authorized=false` remains invariant.
