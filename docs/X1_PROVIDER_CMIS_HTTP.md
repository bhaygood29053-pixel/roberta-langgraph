# X1 Provider Integration Through CMIS HTTP

The X1 Provider already exists in the separate `liquidity-scout` repository.
Roberta must not import or duplicate those provider internals.

## Runtime path

```text
Roberta
  -> X1 Scout
    -> CMISHTTPClient
      -> POST /v1/cmis
        -> CMISGateway
          -> X1 Provider
```

Verified results return through the same path in reverse.

## Process boundary

Start the provider-backed CMIS gateway from the Liquidity Scout repository:

```bash
python -m liquidity_scout.cmis.http
```

Its default endpoint is `http://127.0.0.1:8765/v1/cmis`. Roberta uses
`CMIS_BASE_URL` when a different address is required. A gateway configured with
Bearer authentication uses the `CMIS_API_KEY` environment variable on the
Roberta side.

## Contract

Roberta consumes the CMIS service envelope directly:

- `service`
- `chain`
- `status`
- `asset`
- `data`
- `risk`
- `confidence`
- `sources`
- `observed_at`
- `warnings`
- `errors`

X1 Scout always supplies `chain="x1"`. It preserves `partial`, `unavailable`,
`ambiguous`, and `error` rather than replacing missing values.

## Failure behavior

Network/HTTP/malformed-response failures are converted into explicit CMIS-like
failure envelopes with empty data and no fabricated facts. Provider failures
that reach CMIS are already represented by CMIS itself and are preserved.

## Tests

Deterministic tests use `MockCMISClient` or a local stub HTTP server. The paid
DeepSeek routing test also injects the mock so model behavior is isolated from
CMIS availability.

To exercise a running provider-backed gateway explicitly:

```bash
RUN_LIVE_CMIS_TESTS=1 python -m pytest -v -m cmis_live
```
