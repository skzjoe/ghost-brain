#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SCRIPT="$WORKSPACE/scripts/ghost_memory_db.py"
MODE="${1:-pipeline}"
CUSTOM_PYTHON_CANDIDATES="${GHOST_MEMORY_PYTHON_CANDIDATES:-}"

choose_python() {
  local -a candidates=(
    "$WORKSPACE/.local/envs/.venv/bin/python"
    "$WORKSPACE/.local/envs/venv/bin/python"
    "${HOMEBREW_PREFIX:-/home/linuxbrew/.linuxbrew}/bin/python3"
    "${HOMEBREW_PREFIX:-/home/linuxbrew/.linuxbrew}/opt/python@3.14/bin/python3.14"
    "python3"
    "python"
  )

  if [[ -n "$CUSTOM_PYTHON_CANDIDATES" ]]; then
    local -a extra_candidates=()
    IFS=':' read -r -a extra_candidates <<< "$CUSTOM_PYTHON_CANDIDATES"
    candidates=("${extra_candidates[@]}" "${candidates[@]}")
  fi

  for py in "${candidates[@]}"; do
    if ! command -v "$py" >/dev/null 2>&1 && [[ ! -x "$py" ]]; then
      continue
    fi
    if "$py" -c "import sqlite_vec" >/dev/null 2>&1; then
      echo "$py"
      return 0
    fi
  done
  return 1
}

PYTHON_BIN="$(choose_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "sqlite-vec runtime not found in known Python interpreters" >&2
  exit 1
fi

for key_file in \
  "$WORKSPACE/secrets/gemini_api_key.txt" \
  "$WORKSPACE/secrets/google_api_key.txt"
do
  if [[ -f "$key_file" ]]; then
    export GOOGLE_API_KEY="$(tr -d '\n' < "$key_file")"
    break
  fi
done

export GHOST_EMBEDDING_PROVIDER="${GHOST_EMBEDDING_PROVIDER:-gemini}"

case "$MODE" in
  --python|python)
    echo "$PYTHON_BIN"
    ;;
  --check|check)
    "$PYTHON_BIN" - <<'PY'
import importlib.util
import os
import sys
print(f"python={sys.executable}")
print(f"sqlite_vec={bool(importlib.util.find_spec('sqlite_vec'))}")
print(f"google_api_key={bool(os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY'))}")
PY
    ;;
  --smoke|smoke)
    "$PYTHON_BIN" "$SCRIPT" stats >/dev/null
    echo "memory-pipeline-smoke: ok | python=$PYTHON_BIN"
    ;;
  pipeline|--pipeline|"")
    exec "$PYTHON_BIN" "$SCRIPT" pipeline
    ;;
  *)
    exec "$PYTHON_BIN" "$SCRIPT" "$@"
    ;;
esac
