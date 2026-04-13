#!/usr/bin/env bash
set -euo pipefail

# 👻 Ghost Brain Installer
# Installs productivity framework into your OpenClaw workspace.
# Safe: won't overwrite existing files unless you use --force.

FORCE=false
[[ "${1:-}" == "--force" ]] && FORCE=true

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "👻 Ghost Brain Installer"
echo "   Target: $WORKSPACE"
echo ""

if [[ ! -d "$WORKSPACE" ]]; then
  echo "❌ Workspace not found: $WORKSPACE"
  echo "   Set OPENCLAW_WORKSPACE or run 'openclaw setup' first."
  exit 1
fi

safe_copy() {
  local src="$1" dst="$2"
  if [[ -e "$dst" ]] && [[ "$FORCE" != true ]]; then
    echo "   ⏭️  Skip (exists): $(basename "$dst")"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  cp -r "$src" "$dst"
  echo "   ✅ $(basename "$dst")"
}

safe_copy_data() {
  local src="$1" dst="$2"
  if [[ -e "$dst" ]]; then
    echo "   ⏭️  Skip (user data): $(basename "$dst")"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  cp -r "$src" "$dst"
  echo "   ✅ $(basename "$dst")"
}

echo "📦 Installing skills..."
for skill_dir in "$SCRIPT_DIR"/skills/*/; do
  skill_name=$(basename "$skill_dir")
  safe_copy "$skill_dir" "$WORKSPACE/skills/$skill_name"
done

echo ""
echo "📚 Installing knowledge docs..."
mkdir -p "$WORKSPACE/memory/reference"
for doc in TOKEN-EFFICIENCY.md SELF-LEARNING.md PLAYBOOK.md SECOND-BRAIN.md CRON-PATTERNS.md MEMORY-DB.md LEARNING-REVIEW.md CODING-WORKFLOW.md CODING-QUICKSTART.md; do
  [[ -f "$SCRIPT_DIR/$doc" ]] && safe_copy "$SCRIPT_DIR/$doc" "$WORKSPACE/memory/reference/$doc"
done

echo ""
echo "🧠 Setting up memory structure..."
for dir in weekly projects reference; do
  mkdir -p "$WORKSPACE/memory/$dir"
done

for f in decisions.md people.md ideas.md commitments.md follow-ups.md now.md heartbeat-state.json; do
  safe_copy_data "$SCRIPT_DIR/structure/memory/$f" "$WORKSPACE/memory/$f"
done

echo ""
echo "📝 Setting up .learnings/..."
for dir in domains projects archive; do
  mkdir -p "$WORKSPACE/.learnings/$dir"
done

for f in LEARNINGS.md ERRORS.md FEATURE_REQUESTS.md; do
  safe_copy_data "$SCRIPT_DIR/structure/.learnings/$f" "$WORKSPACE/.learnings/$f"
done

echo ""
echo "🛠️ Installing scripts..."
mkdir -p "$WORKSPACE/scripts"

safe_copy "$SCRIPT_DIR/scripts/gateway_watchdog.sh" "$WORKSPACE/scripts/gateway_watchdog.sh"
chmod +x "$WORKSPACE/scripts/gateway_watchdog.sh" 2>/dev/null || true

[[ -f "$SCRIPT_DIR/scripts/heartbeat_pulse.sh" ]] && {
  safe_copy "$SCRIPT_DIR/scripts/heartbeat_pulse.sh" "$WORKSPACE/scripts/heartbeat_pulse.sh"
  chmod +x "$WORKSPACE/scripts/heartbeat_pulse.sh" 2>/dev/null || true
}

for f in obsidian_push_daily.sh obsidian_push_today.sh obsidian_push_weekly.sh run_memory_pipeline.sh; do
  [[ -f "$SCRIPT_DIR/scripts/$f" ]] && {
    safe_copy "$SCRIPT_DIR/scripts/$f" "$WORKSPACE/scripts/$f"
    chmod +x "$WORKSPACE/scripts/$f" 2>/dev/null || true
  }
done

# Memory, CLI, and research surfaces
for f in learning_review.py ghost_memory_db.py detect_active_lanes.py ghost_auto_skill.py          ghost_unified_recall.py ghost_learning_loop.py ghost_error_classifier.py          ghost_todos.py model_router.py memory_content_scanner.py ghost_usage_insights.py          ghost_cli.py ghost_session_context.py ghost_working_memory.py          ghost_research.py ghost_research_lib.py ghost_eval.py ghost_regression.py          ghost_safety_benchmark.py ghost_trajectory_log.py ghost_continuity_benchmark.py          ghost_dashboard.py ghost_experiments.py ghost_core_contracts.py; do
  [[ -f "$SCRIPT_DIR/scripts/$f" ]] && {
    safe_copy "$SCRIPT_DIR/scripts/$f" "$WORKSPACE/scripts/$f"
    chmod +x "$WORKSPACE/scripts/$f" 2>/dev/null || true
  }
done

[[ -d "$SCRIPT_DIR/scripts/ghost_core" ]] && safe_copy "$SCRIPT_DIR/scripts/ghost_core" "$WORKSPACE/scripts/ghost_core"

[[ -f "$SCRIPT_DIR/scripts/generate_context_bridge.sh" ]] && {
  safe_copy "$SCRIPT_DIR/scripts/generate_context_bridge.sh" "$WORKSPACE/scripts/generate_context_bridge.sh"
  chmod +x "$WORKSPACE/scripts/generate_context_bridge.sh" 2>/dev/null || true
}

for f in "$SCRIPT_DIR"/scripts/cron_*.md; do
  [[ -f "$f" ]] && safe_copy "$f" "$WORKSPACE/scripts/$(basename "$f")"
done

echo ""
echo "📦 Installing Python dependencies..."

if python3 -c "import sqlite_vec" 2>/dev/null; then
  echo "   ✅ sqlite-vec (already installed)"
else
  echo "   📥 Installing sqlite-vec..."
  pip3 install sqlite-vec --quiet --break-system-packages 2>/dev/null \
    || pip3 install sqlite-vec --quiet 2>/dev/null \
    || pip install sqlite-vec --quiet 2>/dev/null \
    || echo "   ⚠️  Could not install sqlite-vec automatically. Run: pip install sqlite-vec"
fi

if python3 -c "from google import genai" 2>/dev/null; then
  echo "   ✅ google-genai (already installed)"
else
  echo "   📥 Installing google-genai (optional — for semantic search)..."
  pip3 install google-genai --quiet --break-system-packages 2>/dev/null \
    || pip3 install google-genai --quiet 2>/dev/null \
    || pip install google-genai --quiet 2>/dev/null \
    || echo "   ⚠️  Could not install google-genai. Semantic search will use local fallback (still works)."
fi

echo ""
echo "🗄️ Initializing Memory DB..."
mkdir -p "$WORKSPACE/.local"
if bash "$WORKSPACE/scripts/run_memory_pipeline.sh" pipeline 2>/dev/null; then
  echo "   ✅ Memory DB indexed"
else
  echo "   ⚠️  Memory DB index failed (will work after you add some notes)"
fi

echo ""
echo "🔄 Initializing Learning Review..."
if python3 "$WORKSPACE/scripts/learning_review.py" init 2>/dev/null; then
  echo "   ✅ Learning Review initialized"
else
  echo "   ⚠️  Learning Review init skipped (will work after you add learnings)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Ghost Brain installed!"
echo ""
echo "What was installed:"
echo "  • $(ls -d "$WORKSPACE"/skills/ghost-* "$WORKSPACE"/skills/self-improving-agent 2>/dev/null | wc -l) skills"
echo "  • Knowledge docs → memory/reference/"
echo "  • Second brain templates → memory/"
echo "  • .learnings/ structure"
echo "  • Core + research scripts → scripts/ (recall, learning, context, working-memory, eval)"
echo "  • $(ls "$WORKSPACE"/scripts/cron_*.md 2>/dev/null | wc -l) cron prompt templates → scripts/"
echo ""

if [[ -n "${GEMINI_API_KEY:-}" ]]; then
  echo "  🔑 GEMINI_API_KEY detected — semantic search enabled (free tier)"
else
  echo "  💡 Tip: Set GEMINI_API_KEY for semantic search (free at ai.google.dev)"
  echo "     Without it, search still works using local embeddings."
fi

echo ""
echo "  🛡️ Gateway watchdog (recommended):"
echo "     1. Create secrets/telegram_bot_token.txt and secrets/telegram_chat_id.txt"
echo "     2. Add to OS crontab: */2 * * * * bash $WORKSPACE/scripts/gateway_watchdog.sh"
echo ""
echo "Next steps:"
echo "  1. Verify install: bash test.sh"
echo "  2. Set up cron jobs: bash setup-crons.sh"
echo "  3. Try /audit to verify everything works"
echo "  4. Start chatting — Ghost captures decisions, ideas, and learnings automatically"
echo ""
echo "Docs: read the .md files in memory/reference/ for full details."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
