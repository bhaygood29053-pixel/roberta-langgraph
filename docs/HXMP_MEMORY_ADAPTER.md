# HXMP Durable Memory Adapter

Roberta binds durable long-term memory to the public `SyntharaLabs/HXMP` protocol through an approval-gated adapter.

## Verified HXMP backend

The backend contract is taken from the upstream HXMP repository, especially:

- `README.md`
- `API.md`
- `TOOL_MANIFEST.json`
- `scripts/hxmp_tools.mjs`

HXMP is a Node.js tool/protocol layer on X1. It is not a conventional key/value database.

Its memory primitive is a versioned encrypted snapshot in an HXMP lane:

```text
encrypted soul.chunk records
  -> soul.latest pointer
       lane
       seq
       prev
       sid
       n
       plaintext SHA-256
```

`read-soul` decrypts locally and verifies the recovered plaintext against the on-chain hash.

## Roberta mapping

Roberta stores one deterministic JSON document in the dedicated lane:

```text
roberta-memory
```

The document contains the complete current collection of typed `MemoryRecord` values.

This gives Roberta key/value-like behavior without inventing backend semantics:

```text
HXMP read-soul
  -> verified plaintext snapshot
  -> parse MemoryRecord collection
  -> exact get(key)
  -> deterministic local search(query)
```

Stable keys remain Roberta application semantics. HXMP supplies encrypted snapshot durability, chain history, and integrity verification.

## Approval-gated writes

HXMP memory writes are state-changing X1 transactions. They spend XNT gas and require explicit user approval.

Therefore `HXMPMemoryStore.upsert()` always refuses.

The only supported write path is:

```text
MemoryCandidate
  -> Roberta deterministic write policy
  -> MemoryRecord(authority="durable")
  -> rebuild deterministic roberta-memory snapshot
  -> write 0600 temporary plaintext file
  -> HXMP dry-run-soul
  -> verify exact plaintext SHA-256 / wallet / lane / Agent ID / safety
  -> return HXMPPreparedWrite
  -> HUMAN APPROVES EXACT SHA-256 + WALLET + LANE
  -> verify configured keypair resolves to that approved wallet
  -> execute_prepared_write(..., user_approved=True)
  -> HXMP write-soul
  -> encrypted chunks + soul.latest
  -> HXMP readback verification
  -> HXMPWriteCommit
```

No Python code reads wallet secret bytes or HXMP encryption-key bytes. The adapter passes configured file paths to the upstream HXMP process. Before execution it uses the upstream-documented `solana address -k <KEYPAIR_PATH>` command to resolve only the public address and bind the signer to the approved wallet.

A write cannot execute unless all of these are true:

- Roberta's deterministic category policy allows the record.
- The record authority is `durable` and its category is one of Roberta's durable categories.
- HXMP dry-run returns the exact deterministic snapshot hash.
- HXMP dry-run reports the configured wallet and lane.
- Agent ID verification is true.
- HXMP safety classification is `safe`.
- The caller supplies `user_approved=True`.
- The caller supplies the exact approved dry-run SHA-256, wallet, and lane.
- The prepared preview still matches that approved hash, wallet, and lane.
- The staged source still hashes to the same SHA-256 and contains the exact prepared `MemoryRecord`.
- A keypair path is explicitly configured/provided for execution.
- `solana address -k <KEYPAIR_PATH>` resolves to the exact approved wallet before `write-soul` is invoked.
- HXMP `write-soul` reports `readback_verified: true`.
- The committed wallet, lane, and hash match the approved preview.

## Read behavior

Reads are automatic/read-only.

`HXMPMemoryStore` invokes:

```bash
node <HXMP>/scripts/hxmp_tools.mjs read-soul \
  --wallet <PUBLIC_WALLET> \
  --encryption-key <LOCAL_MEMORY_KEY_PATH> \
  --lane roberta-memory \
  --show-content
```

The adapter accepts plaintext only when HXMP reports both `ok: true` and `verified: true`, and the returned wallet/lane match configuration.

A missing `soul.latest` for the lane is treated as an empty durable-memory store. Other verification failures fail closed.

## Dry-run behavior

Preparation invokes:

```bash
node <HXMP>/scripts/hxmp_tools.mjs dry-run-soul \
  --wallet <PUBLIC_WALLET> \
  --source <TEMP_0600_SNAPSHOT> \
  --profile default \
  --lane roberta-memory
```

Dry-run never receives a keypair path and never uses `--execute`.

The staged plaintext remains local and should be discarded if the proposal is rejected or abandoned.

## Execution behavior

After explicit approval of the exact hash, wallet, and lane, the adapter first verifies signer identity without printing secret bytes:

```bash
solana address -k <LOCAL_KEYPAIR_PATH>
```

If that public address differs from the approved wallet, execution stops **before** `write-soul`.

Only after that binding check does the adapter invoke:

```bash
node <HXMP>/scripts/hxmp_tools.mjs write-soul \
  --keypair <LOCAL_KEYPAIR_PATH> \
  --encryption-key <LOCAL_MEMORY_KEY_PATH> \
  --source <EXACT_PREVIEWED_SNAPSHOT> \
  --profile default \
  --lane roberta-memory \
  --expected-sha256 sha256:<APPROVED_HASH> \
  --execute \
  --confirm-write
```

The adapter reports success only after upstream readback verification.

## Configuration

`HXMPMemoryConfig` requires explicit local paths and identity:

```python
HXMPMemoryConfig(
    script_path="/path/to/HXMP/scripts/hxmp_tools.mjs",
    wallet="<X1_PUBLIC_WALLET>",
    encryption_key_path="~/.hermes/x1/default/hxmp-encryption.key",
    keypair_path="~/.hermes/x1/default/id.json",  # execution only
    lane="roberta-memory",
)
```

The keypair path may be omitted for read/dry-run-only operation.

## Local HXMP prerequisites

From the upstream HXMP contract:

```bash
cd /path/to/HXMP/scripts
npm install --ignore-scripts
```

The current upstream tool dependency is `@solana/web3.js`.

Normal HXMP writes additionally require:

- X1 wallet funded with XNT for gas
- Agent ID Protocol verification
- local HXMP encryption key
- Solana CLI available for the pre-execution public-wallet binding check
- explicit approval of the exact dry-run SHA-256, wallet, and lane

## Deliberate limitations

This adapter does not:

- silently broadcast memory writes
- bypass HXMP Agent ID verification
- use `force-sensitive`
- print or inspect secret key bytes
- rely on a post-broadcast wallet mismatch check as its signer-identity control
- treat memory as current market truth
- bypass Roberta's stable-vs-freshness-sensitive category policy through direct `prepare_upsert()` calls
- invent an HXMP key/value API
- execute live writes in deterministic CI

The upstream HXMP v0 tool currently enforces a finite plaintext/chunk budget. As the durable memory book grows, Roberta must respect upstream capacity limits rather than bypassing them.

Fresh market/tokenomics/risk facts continue to come from X1 Scout -> CMIS -> provider evidence, never from durable memory.
