#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

STACK_ROOT="${ROBERTA_STACK_ROOT:-$HOME/roberta-dev}"
CMIS="$STACK_ROOT/cmis"
CMIS_CORE="$STACK_ROOT/cmis-core"
ROBERTA="$STACK_ROOT/roberta-langgraph"
ROBERTA_CORE="$STACK_ROOT/roberta-core"

for repo in "$CMIS" "$CMIS_CORE" "$ROBERTA" "$ROBERTA_CORE"; do
  [[ -d "$repo/.git" ]] || fail "Git repository not found: $repo"
done

sync_repo() {
  local repo="$1"
  local name
  name="$(basename "$repo")"

  printf '\n========== SYNC %s ==========\n' "$name"
  cd "$repo"

  git fetch --prune origin

  if [[ -n "$(git status --porcelain)" ]]; then
    printf 'Local changes detected in %s:\n' "$name" >&2
    git status --short >&2
    fail "Refusing to overwrite uncommitted work in $name."
  fi

  git switch main
  git pull --ff-only origin main

  local head remote
  head="$(git rev-parse HEAD)"
  remote="$(git rev-parse origin/main)"
  [[ "$head" == "$remote" ]] || fail "$name did not reach origin/main."

  printf 'HEAD %s\n' "$head"
  git status -sb
}

sync_repo "$CMIS"
sync_repo "$CMIS_CORE"
sync_repo "$ROBERTA"
sync_repo "$ROBERTA_CORE"

printf '\n========== REFRESH CMIS PRIVATE RUNTIME ==========\n'
CMIS_PYTHON="$CMIS/.venv/bin/python"
[[ -x "$CMIS_PYTHON" ]] || fail "CMIS virtualenv missing at $CMIS/.venv. Recreate the existing CMIS environment first."

"$CMIS_PYTHON" -m pip install --upgrade --force-reinstall --no-deps "$CMIS_CORE"
(
  cd /
  env -u PYTHONPATH "$CMIS_PYTHON" - <<'PY'
import cmis_core
from cmis_core.api import CUTOVER_CONTRACT

assert CUTOVER_CONTRACT == "cmis-private-core/v1"
print("cmis_private_core_version=", cmis_core.__version__)
print("cmis_private_contract=", CUTOVER_CONTRACT)
print("cmis_private_runtime=PASS")
PY
)

if systemctl cat cmis-gateway.service >/dev/null 2>&1; then
  sudo systemctl restart cmis-gateway.service
else
  printf 'cmis-gateway.service is not installed; installing managed service.\n'
  cd "$CMIS"
  bash scripts/install_cmis_systemd.sh
fi

printf '\n========== BUILD ROBERTA ASSEMBLED RUNTIME ==========\n'
cd "$ROBERTA"
ROBERTA_PRIVATE_CORE_PATH="$ROBERTA_CORE" bash scripts/build_roberta_runtime.sh

if systemctl cat roberta-bridge.service >/dev/null 2>&1; then
  sudo systemctl restart roberta-bridge.service
else
  printf 'roberta-bridge.service is not installed; installing managed service.\n'
  bash scripts/install_roberta_bridge_systemd.sh
fi

printf '\n========== HEALTH CHECKS ==========\n'
for _ in $(seq 1 30); do
  if curl -fsS --max-time 2 http://127.0.0.1:8765/healthz >/dev/null 2>&1 \
     && curl -fsS --max-time 2 http://127.0.0.1:8766/healthz >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

printf 'CMIS:    '
curl -fsS --max-time 5 http://127.0.0.1:8765/healthz
printf '\nROBERTA: '
curl -fsS --max-time 5 http://127.0.0.1:8766/healthz
printf '\n'

printf '\n========== WEBSITE RUNTIME CHECK ==========\n'
website="$(curl -fsS --max-time 5 http://127.0.0.1:8766/)"
grep -q 'ROBERTA — Verified On-Chain Intelligence' <<<"$website" \
  || fail "ROBERTA website title was not found on the live 8766 runtime."
grep -q 'View evidence &amp; details' <<<"$website" \
  || fail "The live website does not contain the accepted #381 progressive-evidence UI."
grep -q 'ROBERTA judgment' <<<"$website" \
  || fail "The live website does not contain the accepted Human Intelligence judgment UI."
printf 'website_runtime=PASS\n'

printf '\n========== FINAL REPOSITORY HEADS ==========\n'
for repo in "$CMIS" "$CMIS_CORE" "$ROBERTA" "$ROBERTA_CORE"; do
  cd "$repo"
  printf '%-20s %s\n' "$(basename "$repo")" "$(git rev-parse HEAD)"
done

printf '\n========== SERVICE STATUS ==========\n'
systemctl --no-pager --full status cmis-gateway.service | sed -n '1,10p'
systemctl --no-pager --full status roberta-bridge.service | sed -n '1,10p'

printf '\nLOCAL_STACK_SYNC=PASS\n'
printf 'All four local repositories match origin/main, CMIS/ROBERTA runtimes were refreshed, and the live website passed the #381 UI check.\n'
