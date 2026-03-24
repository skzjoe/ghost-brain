#!/bin/bash
# Generate session context bridge from Memory DB
# Produces ~/.openclaw/workspace/.local/session_context.md
# Cost: 1 DB query, ~500 tokens output, 0 LLM tokens

set -e

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
export GOOGLE_API_KEY=$(cat "$WORKSPACE/secrets/gemini_api_key.txt" 2>/dev/null | tr -d '\n')
export GHOST_EMBEDDING_PROVIDER=gemini

python3 "$WORKSPACE/scripts/ghost_memory_db.py" context > "$WORKSPACE/.local/session_context.md" 2>/dev/null

if [ $? -eq 0 ] && [ -s "$WORKSPACE/.local/session_context.md" ]; then
    echo "CONTEXT_OK"
else
    echo "CONTEXT_FAIL"
fi
