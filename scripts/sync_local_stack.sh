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
ROBERTA_EVAL="$STACK_ROOT/roberta-eval"

for repo in "$CMIS" "$CMIS_CORE" "$ROBERTA" "$ROBERTA_CORE" "$ROBERTA_EVAL"; do
  [[ -d "$repo/.git" ]] || fail "Git repository not found: $repo"
done

cleanup_generated_artifacts() {
  local repo="$1"
  local name line path
  name="$(basename "$repo")"

  cd "$repo"

  # Remove only known untracked Python packaging output. Real source edits and
  # arbitrary untracked files still stop the sync.
  while IFS= read -r line; do
    [[ "$line" == "?? "* ]] || continue
    path="${line#?? }"
    case "$path" in
      build/|build/*|dist/|dist/*|*.egg-info/|*.egg-info/*)
        printf 'Removing generated packaging artifact from %s: %s\n' "$name" "$path"
        rm -rf -- "$path"
        ;;
    esac
  done < <(git status --porcelain --untracked-files=all)
}

sync_repo() {
  local repo="$1"
  local name
  name="$(basename "$repo")"

  printf '\n========== SYNC %s ==========\n' "$name"
  cd "$repo"

  git fetch --prune origin
  cleanup_generated_artifacts "$repo"

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
sync_repo "$ROBERTA_EVAL"

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

printf '\n========== REFRESH CMIS SYSTEMD ASSEMBLY ==========\n'
# Always reinstall the unit instead of merely restarting an existing one. Older
# units may predate the repository-owned PYTHONPATH/WorkingDirectory contract and
# can otherwise combine current cmis-core with stale public CMIS site-packages.
cd "$CMIS"
bash scripts/install_cmis_systemd.sh

printf '\n========== VALIDATE CMIS ASSEMBLED RUNTIME ==========\n'
(
  cd "$CMIS"
  env PYTHONPATH="$CMIS" "$CMIS_PYTHON" - <<'PY'
import inspect

from cmis_core.api import CUTOVER_CONTRACT, runtime_gateway_class
from cmis_core.instant_scan_evidence_completion import InstantScanEvidenceCompletionMixin
import liquidity_scout.cmis.instant_x1_scan_gateway as scan_gateway

Gateway = runtime_gateway_class()
assert CUTOVER_CONTRACT == "cmis-private-core/v1"
assert InstantScanEvidenceCompletionMixin in Gateway.__mro__
assert hasattr(scan_gateway.InstantX1ScanMixin, "_runtime_current_market_freshness_evidence")

gateway = Gateway()
resolver = getattr(gateway, "x1_current_market_freshness_evidence_resolver", None)
manager = getattr(gateway, "x1_current_market_freshness_evidence_manager", None)
assert callable(resolver), "freshness evidence resolver is not registered"
assert manager is not None, "freshness evidence manager is not registered"

print("cmis_gateway_class=", f"{Gateway.__module__}.{Gateway.__name__}")
print("instant_scan_module=", inspect.getsourcefile(scan_gateway.InstantX1ScanMixin))
print("freshness_resolver_registered=", callable(resolver))
print("freshness_manager_registered=", manager is not None)
print("cmis_assembled_runtime=PASS")
PY
)

unit_text="$(systemctl cat cmis-gateway.service)"
grep -Fq "WorkingDirectory=$CMIS" <<<"$unit_text" \
  || fail "CMIS systemd unit is not bound to the current repository WorkingDirectory."
grep -Fq "Environment=PYTHONPATH=$CMIS" <<<"$unit_text" \
  || fail "CMIS systemd unit is missing the current repository PYTHONPATH."

printf '\n========== BUILD ROBERTA ASSEMBLED RUNTIME ==========\n'
cd "$ROBERTA"
ROBERTA_PRIVATE_CORE_PATH="$ROBERTA_CORE" bash scripts/build_roberta_runtime.sh

printf '\n========== REFRESH ROBERTA SYSTEMD ASSEMBLY ==========\n'
# Reinstall the managed bridge unit on every sync so transport-budget changes and
# other accepted runtime settings cannot be left behind in a stale unit file.
bash scripts/install_roberta_bridge_systemd.sh

bridge_environment="$(systemctl show roberta-bridge.service -p Environment --value)"
grep -Fq "CMIS_TIMEOUT_SECONDS=90" <<<"$bridge_environment" \
  || fail "ROBERTA bridge is missing the 90-second CMIS evidence-completion timeout budget."
printf 'roberta_cmis_timeout_seconds=90\n'
printf 'roberta_bridge_assembled_runtime=PASS\n'

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
grep -q 'data-capability-surface="roberta-website-capabilities/2026-09-11"' <<<"$website" \
  || fail "The live website is not serving the current 2026-09-11 capability surface."
grep -q 'Wallet relationships' <<<"$website" \
  || fail "The live website is missing accepted Wallet Relationship capability discovery."
grep -q 'Tokenized equities &amp; RWAs' <<<"$website" \
  || fail "The live website is missing accepted Tokenized Equity / RWA capability discovery."
grep -q 'X1 Daily Intelligence Brief' <<<"$website" \
  || fail "The live website is missing accepted X1 Daily Intelligence Brief discovery."
grep -q 'Evidence-complete answers' <<<"$website" \
  || fail "The live website is missing the system-wide Evidence Completion capability surface."
grep -q 'id="chat-focus-workspace-v1"' <<<"$website" \
  || fail "The live website is missing the chat-focused workspace layout."
grep -q 'id="roberta-answer-consistency-v1"' <<<"$website" \
  || fail "The live website is missing the deterministic answer-consistency surface."
grep -q '.inspector{display:none!important}' <<<"$website" \
  || fail "The live website has not removed the right-side inspector from the visible chat layout."
grep -q "Working':'Send" <<<"$website" \
  || fail "The live website is missing the accepted Working/Send chat-button state contract."
grep -q '#send:disabled{background:#b91c1c!important' <<<"$website" \
  || fail "The live website is missing the red Working-state button treatment."
grep -q '#send{background:#15803d!important' <<<"$website" \
  || fail "The live website is missing the green Send-state button treatment."
printf 'website_runtime=PASS\n'

printf '\n========== FINAL REPOSITORY HEADS ==========\n'
for repo in "$CMIS" "$CMIS_CORE" "$ROBERTA" "$ROBERTA_CORE" "$ROBERTA_EVAL"; do
  cd "$repo"
  printf '%-20s %s\n' "$(basename "$repo")" "$(git rev-parse HEAD)"
done

printf '\n========== SERVICE STATUS ==========\n'
systemctl --no-pager --full status cmis-gateway.service | sed -n '1,10p'
systemctl --no-pager --full status roberta-bridge.service | sed -n '1,10p'

printf '\nLOCAL_STACK_SYNC=PASS\n'
printf 'All five operational repositories match origin/main, CMIS/ROBERTA runtimes were refreshed, CMIS assembly was validated, and the live website passed current capability and chat-workspace checks.\n'
