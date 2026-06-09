#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
RUN_GUI_SMOKE="${RUN_GUI_SMOKE:-0}"

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Required command not found: $cmd" >&2
    exit 1
  fi
}

run_step() {
  local description="$1"
  shift
  printf '\n==> %s\n' "$description"
  "$@"
}

resolve_python() {
  if [[ -x "${REPO_DIR}/.venv/bin/python" ]]; then
    printf '%s\n' "${REPO_DIR}/.venv/bin/python"
    return
  fi
  printf '%s\n' "$PYTHON_BIN"
}

require_command "$PYTHON_BIN"
require_command find
require_command xargs
require_command awk

PYTHON_CMD="$(resolve_python)"

printf '==> repo: %s\n' "$REPO_DIR"
printf '==> python: %s\n' "$PYTHON_CMD"

cd "$REPO_DIR"

run_step "./scripts/check_file_sizes.sh ." ./scripts/check_file_sizes.sh .
run_step "unit tests" "$PYTHON_CMD" -m unittest discover -s tests -p 'test_*.py' -v
run_step "syntax check" "$PYTHON_CMD" -m compileall -q .

if [[ "$RUN_GUI_SMOKE" == "1" ]]; then
  run_step "GUI smoke start (2s timeout)" "$PYTHON_CMD" - <<'PY'
import subprocess
import sys
import time

proc = subprocess.Popen([sys.executable, "main.py"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.0)
proc.terminate()
try:
    proc.wait(timeout=3.0)
except subprocess.TimeoutExpired:
    proc.kill()
    proc.wait(timeout=3.0)
print("GUI smoke run completed.")
PY
fi
