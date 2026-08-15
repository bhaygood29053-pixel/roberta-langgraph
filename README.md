# Roberta LangGraph

Roberta is the top-level Oracle and multi-agent coordinator. X1-specific market
investigations are delegated to X1 Scout, which obtains deterministic facts
from the external Cross-Chain Market Intelligence Service (CMIS).

```text
User
  -> Roberta
    -> X1 Scout
      -> CMIS HTTP gateway
        -> X1 Provider
```

Roberta does not call CMIS or X1 provider internals directly.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev,deepseek]'
```

## Deterministic tests

```bash
python -m pytest -v -m 'not live and not cmis_live'
```

The suite covers Roberta delegation, the X1 Scout boundary, CMIS envelope
semantics, HTTP transport behavior, explicit X1 chain scoping, unavailable
states, warnings, and service errors.

## Provider-backed CMIS

The current X1 provider implementation remains in the separate
`liquidity-scout` repository. Start its CMIS gateway there:

```bash
python -m liquidity_scout.cmis.http
```

Roberta defaults to:

```text
CMIS_BASE_URL=http://127.0.0.1:8765
```

Optional settings:

```text
CMIS_TIMEOUT_SECONDS=30
CMIS_API_KEY=...
```

A non-loopback CMIS deployment should require Bearer authentication.

Run the explicit CMIS integration test while that service is running:

```bash
RUN_LIVE_CMIS_TESTS=1 python -m pytest -v -m cmis_live
```

The test verifies the service envelope and chain identity; it does not assert
specific current market values.

## Live DeepSeek routing

Set `DEEPSEEK_API_KEY`, then run the paid opt-in routing test:

```bash
RUN_LIVE_MODEL_TESTS=1 python -m pytest -v -m live
```

This test injects the deterministic CMIS mock so it proves DeepSeek's specialist
routing independently of provider availability.

For an actual end-to-end live run, start CMIS first and then execute:

```bash
roberta-live "On X1, check AGI market risk"
```

See `docs/X1_PROVIDER_CMIS_HTTP.md` for the current runtime boundary.
