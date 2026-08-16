# HXMP Live Contract Probe

The HXMP backend adapter includes an opt-in **read-only** live probe against a local checkout of `SyntharaLabs/HXMP`.

The probe never loads a wallet keypair and never calls `write-soul`.

## Local setup

Clone or update the upstream HXMP repository outside the Roberta repository, then install its Node dependency:

```bash
cd /path/to/HXMP/scripts
npm install --ignore-scripts
```

Set only non-signing probe configuration:

```bash
export HXMP_TOOL_SCRIPT=/path/to/HXMP/scripts/hxmp_tools.mjs
export HXMP_WALLET=<X1_PUBLIC_WALLET>
export RUN_HXMP_LIVE_TESTS=1
```

The RPC + `dry-run-soul` probe needs no keypair and performs no transaction.

To additionally test `read-soul`, point to the existing local HXMP encryption-key file without printing or copying its contents:

```bash
export HXMP_ENCRYPTION_KEY_PATH=~/.hermes/x1/default/hxmp-encryption.key
```

Then run:

```bash
python -m pytest -v tests/test_hxmp_live_contract.py
```

## What the probe verifies

The first live test checks:

- upstream `rpc-health`
- current X1 RPC reachability through the HXMP tool
- `dry-run-soul` accepts Roberta's deterministic snapshot document
- returned wallet and `roberta-memory` lane match the request
- upstream plaintext SHA-256 exactly matches Roberta's local deterministic hash
- the preview remains confirmation-required
- Agent ID and safety fields are present

The optional read test checks:

- `read-soul` for the configured public wallet and `roberta-memory` lane
- a missing lane is reported explicitly rather than fabricated
- an existing lane returns `ok=true` and `verified=true`
- plaintext hash and content are returned only through the local encryption-key path

## Safety

Do **not** set or pass a keypair path for this probe.

Do not commit:

- `id.json`
- `hxmp-encryption.key`
- `.env`
- any secret bytes

A future live write test, if ever added, must remain a separate explicitly approved workflow because HXMP memory writes are X1 transactions and spend XNT gas.
