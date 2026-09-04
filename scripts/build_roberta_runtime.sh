#!/usr/bin/env bash
set -euo pipefail

fail() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PRIVATE_CORE_PATH="${ROBERTA_PRIVATE_CORE_PATH:-$REPO_ROOT/../roberta-core}"
RUNTIME_VENV="${ROBERTA_RUNTIME_VENV:-$REPO_ROOT/.venv-runtime}"
PYTHON_BIN="${ROBERTA_BOOTSTRAP_PYTHON:-python3}"

[[ -d "$PRIVATE_CORE_PATH" ]] || fail "Private core repository not found at $PRIVATE_CORE_PATH. Set ROBERTA_PRIVATE_CORE_PATH."
command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "Python bootstrap executable not found: $PYTHON_BIN"

if [[ ! -x "$RUNTIME_VENV/bin/python" ]]; then
  "$PYTHON_BIN" -m venv "$RUNTIME_VENV"
fi

PYTHON="$RUNTIME_VENV/bin/python"

printf 'Building assembled ROBERTA runtime in %s\n' "$RUNTIME_VENV"
"$PYTHON" -m pip install --upgrade pip
"$PYTHON" -m pip install --upgrade --force-reinstall   "${REPO_ROOT}[deepseek]"   "$PRIVATE_CORE_PATH"

printf '\n=== ASSEMBLED RUNTIME IMPORT VALIDATION ===\n'
(
  cd /
  env -u PYTHONPATH "$PYTHON" - <<'PY'
import inspect

import roberta
import roberta.bridge_http
import roberta.graph
import roberta.opinion_contract
import roberta.recommendation_policy
import roberta_core.api

print("public package:", roberta.__file__)
print("bridge:", inspect.getsourcefile(roberta.bridge_http))
print("protected graph:", inspect.getsourcefile(roberta.graph))
print("recommendation policy:", inspect.getsourcefile(roberta.recommendation_policy))
print("opinion contract:", inspect.getsourcefile(roberta.opinion_contract))
print("private facade:", inspect.getsourcefile(roberta_core.api))
print("private contract:", roberta_core.api.CUTOVER_CONTRACT)
print("status=PASS")
PY
)

printf '\nAssembled ROBERTA runtime is ready: %s\n' "$PYTHON"
printf 'Restart/reinstall the managed bridge so it uses this interpreter.\n'
