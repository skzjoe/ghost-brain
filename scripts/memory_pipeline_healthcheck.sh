#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
WRAPPER="$WORKSPACE/scripts/run_memory_pipeline.sh"
DB_PATH="$WORKSPACE/.local/ghost_memory.db"

if [[ ! -x "$WRAPPER" ]]; then
  echo "⚠️ Memory pipeline wrapper missing: $WRAPPER"
  exit 1
fi

CHECK_OUTPUT="$(bash "$WRAPPER" check 2>&1 || true)"
if ! grep -q 'sqlite_vec=True' <<<"$CHECK_OUTPUT"; then
  echo "⚠️ Memory pipeline runtime unhealthy, sqlite_vec missing or runtime resolution failed"
  echo "$CHECK_OUTPUT"
  exit 1
fi

SMOKE_OUTPUT="$(bash "$WRAPPER" smoke 2>&1 || true)"
if ! grep -q 'memory-pipeline-smoke: ok' <<<"$SMOKE_OUTPUT"; then
  echo "⚠️ Memory pipeline smoke test failed"
  echo "$SMOKE_OUTPUT"
  exit 1
fi

if [[ ! -f "$DB_PATH" ]]; then
  echo "⚠️ Memory DB file missing: $DB_PATH"
  exit 1
fi

echo "HEARTBEAT_OK"
