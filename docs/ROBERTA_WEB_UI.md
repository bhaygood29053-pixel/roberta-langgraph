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
- natural-language ROBERTA questions.

Warp / bridge-flow intelligence is intentionally not exposed as a completed runnable service while its CMIS evidence and coverage gates remain open.

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
