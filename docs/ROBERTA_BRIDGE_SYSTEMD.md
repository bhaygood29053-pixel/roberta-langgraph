# Roberta bridge as a managed systemd service

Roberta's local HTTP bridge normally listens on `127.0.0.1:8766`. For a
long-running MoltGrid integration, run the bridge under systemd instead of
keeping `roberta-serve` open in a terminal.

The managed service provides:

- automatic start at system boot;
- automatic restart after an unexpected bridge failure;
- a stable `127.0.0.1:8766` endpoint for local transports;
- model secrets stored outside the repository;
- logs through `journalctl`.

## Install

The managed bridge must run from an **assembled runtime** where the public shell
and private core are installed into the same site-packages tree. Do not run the
bridge with `PYTHONPATH=<repo>/src` after the private-core split; the public
`roberta` package can otherwise shadow protected modules such as
`roberta.recommendation_policy`.

From the public Roberta repository:

```bash
git pull --ff-only origin main
cd ../roberta-core
git pull --ff-only origin main
cd ../roberta-langgraph

bash scripts/build_roberta_runtime.sh
bash scripts/install_roberta_bridge_systemd.sh
```

The builder defaults to `../roberta-core`. If the private repository lives
elsewhere, set `ROBERTA_PRIVATE_CORE_PATH=/absolute/path/to/roberta-core`.
The assembled interpreter defaults to `.venv-runtime/bin/python`.

Do not run the installer as root. It uses `sudo` only when writing and managing
the systemd unit.

If `DEEPSEEK_API_KEY` is already exported in the current shell, the installer
persists it without printing it. Otherwise, it asks for the key with terminal
echo disabled.

The runtime environment file is stored at:

```text
~/.config/roberta/roberta.env
```

The installer creates that file with mode `600` and the parent directory with
mode `700`. Never add that environment file or its secret values to Git.

If the environment file already contains `DEEPSEEK_API_KEY`, the installer
preserves it rather than asking again.

## Important: stop a manually launched bridge first

Only one process can own port `8766`. If `roberta-serve` or
`python -m roberta.bridge_http` is already running manually, stop that process
before installation. The installer deliberately refuses to kill an unknown
process using the port.

## Service behavior

The generated unit uses the dedicated assembled runtime and runs:

```text
.venv-runtime/bin/python -m roberta.bridge_http --host 127.0.0.1 --port 8766
```

The unit deliberately does **not** set a public-source `PYTHONPATH`. Before
writing the unit, the installer validates that the selected interpreter can
import the public bridge plus protected `roberta.graph`,
`roberta.recommendation_policy`, and `roberta.opinion_contract`.

It is configured with:

```text
Restart=always
RestartSec=3
```

so a failed bridge is restarted automatically.

The installer does not assume the bridge will be ready after a fixed sleep. It
polls `http://127.0.0.1:8766/healthz` for up to 30 seconds and only reports
success after the health endpoint responds. This avoids false installation
failures on slower Roberta graph/model initialization. If Roberta does not
become healthy in that window, the installer prints recent service logs and
exits with an error.

## Verification

Check service state:

```bash
sudo systemctl status roberta-bridge.service --no-pager -l
```

Check the bridge health endpoint:

```bash
curl -fsS http://127.0.0.1:8766/healthz
```

Expected service envelope:

```json
{"service":"roberta_bridge","status":"ok","version":1}
```

Inspect recent logs:

```bash
sudo journalctl -u roberta-bridge.service -n 100 --no-pager
```

Follow logs live:

```bash
sudo journalctl -u roberta-bridge.service -f
```

## Restart after a Roberta code update

After updating either repository, rebuild the assembled runtime before restarting
the service:

```bash
cd ~/roberta-dev/roberta-langgraph
git pull --ff-only origin main

cd ~/roberta-dev/roberta-core
git pull --ff-only origin main

cd ~/roberta-dev/roberta-langgraph
bash scripts/build_roberta_runtime.sh
sudo systemctl restart roberta-bridge.service
```

This prevents a successful Git pull from leaving port 8766 on an older protected
core or on a source-shadowed side-by-side layout.

## Change the model key

Edit or recreate `~/.config/roberta/roberta.env` locally, keep it mode `600`,
and restart the service. Do not put the key in the systemd unit or repository.

## MoltGrid dependency

Liquidity Scout can continue pointing to:

```text
ROBERTA_BASE_URL=http://127.0.0.1:8766
```

A Liquidity Scout systemd drop-in may additionally declare:

```ini
[Unit]
Wants=roberta-bridge.service
After=roberta-bridge.service
```

This starts Roberta before the MoltGrid listener without tightly coupling their
lifecycles. The current Liquidity Scout deployment helper additionally waits
for the Roberta and CMIS health endpoints before allowing the listener to start.
If Roberta is temporarily unavailable after startup, the MoltGrid integration
can return its concise availability response while systemd restarts the bridge.
