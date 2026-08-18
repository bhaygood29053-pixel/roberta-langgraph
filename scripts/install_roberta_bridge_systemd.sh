#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

if [[ ${EUID} -eq 0 ]]; then
  fail "Run this installer as the normal Roberta user, not as root. It will use sudo only for systemd files."
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_USER="$(id -un)"
PYTHON="$REPO_ROOT/.venv/bin/python"
ENV_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/roberta"
ENV_FILE="$ENV_DIR/roberta.env"
UNIT_FILE="/etc/systemd/system/roberta-bridge.service"
HEALTH_URL="http://127.0.0.1:8766/healthz"

[[ -x "$PYTHON" ]] || fail "Roberta virtualenv Python was not found at $PYTHON"

case "$REPO_ROOT$ENV_FILE" in
  *[[:space:]]*) fail "This installer currently requires repository and environment-file paths without whitespace." ;;
esac

mkdir -p "$ENV_DIR"
chmod 700 "$ENV_DIR"

if [[ ! -f "$ENV_FILE" ]] || ! grep -q '^DEEPSEEK_API_KEY=' "$ENV_FILE"; then
  model_key="${DEEPSEEK_API_KEY:-}"
  if [[ -z "$model_key" ]]; then
    read -r -s -p "Enter your DeepSeek API key: " model_key
    printf '\n'
  fi
  [[ -n "$model_key" ]] || fail "DEEPSEEK_API_KEY is required."
  [[ "$model_key" != *$'\n'* ]] || fail "DEEPSEEK_API_KEY must be a single line."

  umask 077
  {
    printf 'DEEPSEEK_API_KEY=%s\n' "$model_key"
    if [[ -n "${ROBERTA_MODEL_PROVIDER:-}" ]]; then
      printf 'ROBERTA_MODEL_PROVIDER=%s\n' "$ROBERTA_MODEL_PROVIDER"
    fi
    if [[ -n "${ROBERTA_MODEL:-}" ]]; then
      printf 'ROBERTA_MODEL=%s\n' "$ROBERTA_MODEL"
    fi
    if [[ -n "${ROBERTA_API_KEY:-}" ]]; then
      printf 'ROBERTA_API_KEY=%s\n' "$ROBERTA_API_KEY"
    fi
  } > "$ENV_FILE"
  chmod 600 "$ENV_FILE"
  printf 'Saved Roberta runtime secrets/config to %s (mode 600).\n' "$ENV_FILE"
else
  chmod 600 "$ENV_FILE"
  printf 'Using existing Roberta environment file: %s\n' "$ENV_FILE"
fi

if ! sudo systemctl is-active --quiet roberta-bridge.service 2>/dev/null; then
  if ss -ltn 2>/dev/null | grep -Eq '127\.0\.0\.1:8766|\[::1\]:8766|:8766[[:space:]]'; then
    fail "Port 8766 is already in use by a non-managed process. Stop the manually started Roberta bridge, then run this installer again."
  fi
fi

unit_tmp="$(mktemp)"
trap 'rm -f "$unit_tmp"' EXIT
cat > "$unit_tmp" <<EOF
[Unit]
Description=Roberta Local Bridge
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$REPO_ROOT
Environment=PYTHONPATH=$REPO_ROOT/src
EnvironmentFile=$ENV_FILE
ExecStart=$PYTHON -m roberta.bridge_http --host 127.0.0.1 --port 8766
Restart=always
RestartSec=3
TimeoutStopSec=10
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
EOF

sudo install -m 0644 "$unit_tmp" "$UNIT_FILE"
sudo systemctl daemon-reload
sudo systemctl enable roberta-bridge.service >/dev/null
sudo systemctl restart roberta-bridge.service

health_ready=0
if command -v curl >/dev/null 2>&1; then
  printf '\n=== WAITING FOR ROBERTA HEALTH ===\n'
  for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do
    if curl -fsS --max-time 2 "$HEALTH_URL" >/dev/null 2>&1; then
      health_ready=1
      break
    fi
    sleep 1
  done
fi

printf '\n=== ROBERTA BRIDGE SERVICE ===\n'
sudo systemctl --no-pager --full status roberta-bridge.service | sed -n '1,18p'

printf '\n=== ROBERTA HEALTH ===\n'
if command -v curl >/dev/null 2>&1; then
  if [[ "$health_ready" -ne 1 ]]; then
    printf 'Roberta did not become healthy within 30 seconds.\n' >&2
    printf '\n=== ROBERTA RECENT LOG ===\n' >&2
    sudo journalctl -u roberta-bridge.service -n 50 --no-pager >&2 || true
    exit 1
  fi
  curl -fsS --max-time 5 "$HEALTH_URL"
  printf '\n'
else
  printf 'curl is not installed; check %s manually.\n' "$HEALTH_URL"
fi

printf '\nRoberta bridge is enabled to start automatically and restart after failures.\n'
