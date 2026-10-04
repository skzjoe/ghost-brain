#!/usr/bin/env bash
set -euo pipefail

# 👻 Ghost Brain Installer
# Installs productivity framework into your OpenClaw workspace.
# Safe: won't overwrite existing files unless you use --force.

FORCE=false
LEGACY=false
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=true ;;
    --legacy) LEGACY=true ;;
    --help|-h)
      echo "Usage: bash install.sh [--force] [--legacy]"
      echo "Default: native-first skills and guidance only; no dependencies or runtime changes."
      echo "--force updates packaged files, never user data or workspace instructions."
      echo "--legacy also installs the older local-memory scripts, dependencies and templates."
      exit 0 ;;
    *) echo "Unknown option: $arg. Use --help." >&2; exit 2 ;;
  esac
done

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "👻 Ghost Brain Installer"
echo "   Target: $WORKSPACE"
echo ""

# Keep lexical ancestors visible: resolving links here would hide unsafe targets.
[[ "$WORKSPACE" = /* ]] || WORKSPACE="$PWD/$WORKSPACE"

reject_path() {
  echo "Unsafe install destination: $1 ($2). No files installed." >&2
  echo "Use a real workspace directory; move conflicting links/files aside manually, then retry." >&2
  exit 1
}

check_directory() {
  local path="$1" parent
  while [[ "$path" != / && "$path" == */ ]]; do path="${path%/}"; done
  [[ "$path" == / ]] && return
  parent=$(dirname "$path")
  check_directory "$parent"
  [[ ! -L "$path" ]] || reject_path "$path" "symbolic link"
  [[ ! -e "$path" || -d "$path" ]] || reject_path "$path" "not a directory"
}

check_copy() {
  local src="${1%/}" dst="$2" child
  check_directory "$(dirname "$dst")"
  [[ ! -L "$dst" ]] || reject_path "$dst" "symbolic link"
  if [[ -L "$src" ]]; then
    echo "Unsupported source symbolic link: $src. Review the package before installing." >&2
    exit 1
  fi
  if [[ -d "$src" ]]; then
    [[ ! -e "$dst" || -d "$dst" ]] || reject_path "$dst" "directory/file collision"
    # Include dotfiles; unmatched patterns are explicitly ignored.
    for child in "$src"/* "$src"/.[!.]* "$src"/..?*; do
      [[ -e "$child" || -L "$child" ]] || continue
      check_copy "$child" "$dst/$(basename "$child")"
    done
  else
    [[ ! -e "$dst" || -f "$dst" ]] || reject_path "$dst" "file/directory collision"
  fi
}

safe_mkdir() {
  check_directory "$1"
  [[ "$PREFLIGHT" == true ]] || mkdir -p "$1"
}

safe_chmod() {
  [[ "$PREFLIGHT" == true ]] || chmod +x "$1" 2>/dev/null || true
}

check_directory "$WORKSPACE"
if [[ ! -d "$WORKSPACE" ]]; then
  echo "❌ Workspace not found: $WORKSPACE"
  echo "   Set OPENCLAW_WORKSPACE or run 'openclaw setup' first."
  exit 1
fi

safe_copy() {
  local src="$1" dst="$2"
  if [[ "$PREFLIGHT" == true ]]; then
    check_copy "$src" "$dst"
    return
  fi
  if [[ -e "$dst" || -L "$dst" ]] && [[ "$FORCE" != true ]]; then
    echo "   ⏭️  Skip (exists): $(basename "$dst")"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  if [[ -d "$src" ]]; then
    mkdir -p "$dst"
    cp -R "$src/." "$dst/"
  else
    cp "$src" "$dst"
  fi
  echo "   ✅ $(basename "$dst")"
}

safe_copy_data() {
  local src="$1" dst="$2"
  check_directory "$(dirname "$dst")"
  if [[ -e "$dst" || -L "$dst" ]]; then
    echo "   ⏭️  Skip (user data): $(basename "$dst")"
    return
  fi
  if [[ "$PREFLIGHT" == true ]]; then
    check_copy "$src" "$dst"
    return
  fi
  mkdir -p "$(dirname "$dst")"
  cp -r "$src" "$dst"
  echo "   ✅ $(basename "$dst")"
}

# The same selected file operations run read-only first, then write.
# No package/runtime initialization occurs until the whole preflight passes.
install_files() {
if [[ "$LEGACY" != true ]]; then
  echo "📦 Installing native-first Ghost skills..."
  for skill in ghost-audit ghost-capture ghost-recall ghost-remember; do
    safe_copy "$SCRIPT_DIR/skills/$skill" "$WORKSPACE/skills/$skill"
  done
  safe_copy "$SCRIPT_DIR/PLAYBOOK.md" "$WORKSPACE/memory/reference/PLAYBOOK.md"
  safe_copy "$SCRIPT_DIR/SECOND-BRAIN.md" "$WORKSPACE/memory/reference/SECOND-BRAIN.md"
  safe_copy_data "$SCRIPT_DIR/starter/templates/AGENTS.md" "$WORKSPACE/AGENTS.md"
  safe_copy_data "$SCRIPT_DIR/starter/BOOTSTRAP.md" "$WORKSPACE/BOOTSTRAP.md"
  echo ""
  echo "Ghost Brain installed. Existing workspace instructions were preserved."
  echo "Review BOOTSTRAP.md; merge the packaged AGENTS.md guidance if yours already exists."
  echo "Run bash test.sh for file checks; use /audit for behavioral evidence."
  echo "No dependencies, indexes, cron jobs, credentials or OpenClaw settings changed."
  return
fi

echo "Legacy compatibility install selected: local memory and learning pipelines."
echo "Review legacy instructions before use; they do not configure Skill Workshop or a canonical vault."
echo "📦 Installing skills..."
shopt -s nullglob
for skill_dir in "$SCRIPT_DIR"/skills/ghost-*/ "$SCRIPT_DIR"/skills/self-improving-agent/; do
  [[ -d "$skill_dir" ]] || continue
  skill_name=$(basename "$skill_dir")
  safe_copy "$skill_dir" "$WORKSPACE/skills/$skill_name"
done
shopt -u nullglob

echo ""
echo "📚 Installing knowledge docs..."
safe_mkdir "$WORKSPACE/memory/reference"
for doc in TOKEN-EFFICIENCY.md SELF-LEARNING.md PLAYBOOK.md SECOND-BRAIN.md CRON-PATTERNS.md MEMORY-DB.md LEARNING-REVIEW.md CODING-WORKFLOW.md CODING-QUICKSTART.md; do
  [[ -f "$SCRIPT_DIR/$doc" ]] && safe_copy "$SCRIPT_DIR/$doc" "$WORKSPACE/memory/reference/$doc"
done

echo ""
echo "🧠 Setting up memory structure..."
for dir in weekly projects reference; do
  safe_mkdir "$WORKSPACE/memory/$dir"
done

for f in decisions.md people.md ideas.md commitments.md follow-ups.md now.md heartbeat-state.json; do
  safe_copy_data "$SCRIPT_DIR/structure/memory/$f" "$WORKSPACE/memory/$f"
done

echo ""
echo "📝 Setting up .learnings/..."
for dir in domains projects archive; do
  safe_mkdir "$WORKSPACE/.learnings/$dir"
done

for f in LEARNINGS.md ERRORS.md FEATURE_REQUESTS.md; do
  safe_copy_data "$SCRIPT_DIR/structure/.learnings/$f" "$WORKSPACE/.learnings/$f"
done

[[ -f "$SCRIPT_DIR/starter/BOOTSTRAP.md" ]] && safe_copy_data "$SCRIPT_DIR/starter/BOOTSTRAP.md" "$WORKSPACE/BOOTSTRAP.md"

echo ""
echo "🛠️ Installing scripts..."
safe_mkdir "$WORKSPACE/scripts"

safe_copy "$SCRIPT_DIR/scripts/gateway_watchdog.sh" "$WORKSPACE/scripts/gateway_watchdog.sh"
safe_chmod "$WORKSPACE/scripts/gateway_watchdog.sh"

[[ -f "$SCRIPT_DIR/scripts/heartbeat_pulse.sh" ]] && {
  safe_copy "$SCRIPT_DIR/scripts/heartbeat_pulse.sh" "$WORKSPACE/scripts/heartbeat_pulse.sh"
  safe_chmod "$WORKSPACE/scripts/heartbeat_pulse.sh"
}

for f in obsidian_push_daily.sh obsidian_push_today.sh obsidian_push_weekly.sh run_memory_pipeline.sh; do
  [[ -f "$SCRIPT_DIR/scripts/$f" ]] && {
    safe_copy "$SCRIPT_DIR/scripts/$f" "$WORKSPACE/scripts/$f"
    safe_chmod "$WORKSPACE/scripts/$f"
  }
done

# Memory, CLI, and research surfaces
for f in learning_review.py ghost_memory_db.py detect_active_lanes.py ghost_auto_skill.py          ghost_unified_recall.py ghost_learning_loop.py ghost_error_classifier.py          ghost_todos.py model_router.py memory_content_scanner.py ghost_usage_insights.py          ghost_cli.py ghost_session_context.py ghost_working_memory.py          ghost_conversation_memory.py ghost_guardrails.py ghost_memory_sync.py          ghost_research.py ghost_research_lib.py ghost_eval.py ghost_regression.py          ghost_safety_benchmark.py ghost_trajectory_log.py ghost_continuity_benchmark.py          ghost_dashboard.py ghost_experiments.py ghost_core_contracts.py; do
  [[ -f "$SCRIPT_DIR/scripts/$f" ]] && {
    safe_copy "$SCRIPT_DIR/scripts/$f" "$WORKSPACE/scripts/$f"
    safe_chmod "$WORKSPACE/scripts/$f"
  }
done

[[ -d "$SCRIPT_DIR/scripts/ghost_core" ]] && safe_copy "$SCRIPT_DIR/scripts/ghost_core" "$WORKSPACE/scripts/ghost_core"

[[ -f "$SCRIPT_DIR/scripts/generate_context_bridge.sh" ]] && {
  safe_copy "$SCRIPT_DIR/scripts/generate_context_bridge.sh" "$WORKSPACE/scripts/generate_context_bridge.sh"
  safe_chmod "$WORKSPACE/scripts/generate_context_bridge.sh"
}

for f in "$SCRIPT_DIR"/scripts/cron_*.md; do
  [[ -f "$f" ]] && safe_copy "$f" "$WORKSPACE/scripts/$(basename "$f")"
done
safe_mkdir "$WORKSPACE/.local"

}

PREFLIGHT=true
install_files >/dev/null
PREFLIGHT=false
install_files
[[ "$LEGACY" == true ]] || exit 0

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
echo "  Legacy gateway watchdog (optional; not part of recommended setup):"
echo "     1. Create secrets/telegram_bot_token.txt and secrets/telegram_chat_id.txt"
echo "     2. Add to OS crontab: */2 * * * * bash $WORKSPACE/scripts/gateway_watchdog.sh"
echo ""
echo "Next steps:"
echo "  1. Verify legacy install: bash test.sh --legacy"
echo "  2. Review legacy cron prompts before opting in: bash setup-crons.sh --legacy"
echo "  3. Use /audit to inspect evidence, not to assume everything works"
echo "  4. Prefer native OpenClaw controls and Skill Workshop over legacy automation"
echo ""
echo "Docs: read the .md files in memory/reference/ for full details."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
