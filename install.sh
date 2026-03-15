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

# Check workspace exists
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

# ── 1. Skills ──
echo "📦 Installing skills..."
for skill_dir in "$SCRIPT_DIR"/skills/*/; do
  skill_name=$(basename "$skill_dir")
  safe_copy "$skill_dir" "$WORKSPACE/skills/$skill_name"
done

# ── 2. Knowledge docs (into memory/reference/) ──
echo ""
echo "📚 Installing knowledge docs..."
mkdir -p "$WORKSPACE/memory/reference"
for doc in TOKEN-EFFICIENCY.md SELF-LEARNING.md PLAYBOOK.md SECOND-BRAIN.md CRON-PATTERNS.md; do
  safe_copy "$SCRIPT_DIR/$doc" "$WORKSPACE/memory/reference/$doc"
done

# ── 3. Memory structure ──
echo ""
echo "🧠 Setting up memory structure..."
for dir in weekly projects reference; do
  mkdir -p "$WORKSPACE/memory/$dir"
done

for f in decisions.md people.md ideas.md commitments.md follow-ups.md heartbeat-state.json; do
  safe_copy "$SCRIPT_DIR/structure/memory/$f" "$WORKSPACE/memory/$f"
done

# ── 4. Learnings structure ──
echo ""
echo "📝 Setting up .learnings/..."
for dir in domains projects archive; do
  mkdir -p "$WORKSPACE/.learnings/$dir"
done

for f in LEARNINGS.md ERRORS.md FEATURE_REQUESTS.md; do
  safe_copy "$SCRIPT_DIR/structure/.learnings/$f" "$WORKSPACE/.learnings/$f"
done

# ── 5. Cron prompts ──
echo ""
echo "⏰ Installing cron prompts..."
mkdir -p "$WORKSPACE/scripts"
for f in "$SCRIPT_DIR"/scripts/cron_*.md; do
  safe_copy "$f" "$WORKSPACE/scripts/$(basename "$f")"
done

# ── 6. Summary ──
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Ghost Brain installed!"
echo ""
echo "What was installed:"
echo "  • $(ls -d "$WORKSPACE"/skills/ghost-* "$WORKSPACE"/skills/self-improving-agent 2>/dev/null | wc -l) skills (ghost-ops + self-improving-agent)"
echo "  • 5 knowledge docs → memory/reference/"
echo "  • Second brain templates → memory/"
echo "  • .learnings/ structure"
echo "  • $(ls "$WORKSPACE"/scripts/cron_*.md 2>/dev/null | wc -l) cron prompt templates → scripts/"
echo ""
echo "Next steps:"
echo "  1. Read memory/reference/PLAYBOOK.md and copy patterns you like into AGENTS.md"
echo "  2. Customize memory templates (decisions.md, people.md, etc.)"
echo "  3. Set up cron jobs: bash $(basename "$SCRIPT_DIR")/setup-crons.sh"
echo "     (edit timezone + model in the script first)"
echo "  4. Add to your AGENTS.md:"
echo '     Rate limits: 5s between API calls, 10s between searches, max 5/batch then 2min break.'
echo "  5. Try /audit to verify everything works"
echo ""
echo "Docs: read the .md files in memory/reference/ for full details."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
