#!/usr/bin/env bash
set -euo pipefail

# 👻 Ghost Brain — Smoke Test
# Run after install to verify everything works.

WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
PASS=0
FAIL=0

check() {
  local desc="$1" cmd="$2"
  if eval "$cmd" &>/dev/null; then
    echo "  ✅ $desc"
    PASS=$((PASS + 1))
  else
    echo "  ❌ $desc"
    FAIL=$((FAIL + 1))
  fi
}

echo "👻 Ghost Brain — Smoke Test"
echo ""

echo "📦 Skills:"
for skill in ghost-audit ghost-capture ghost-commitments ghost-conflicts ghost-decisions \
             ghost-export ghost-fastlanes ghost-followups ghost-health ghost-ideas \
             ghost-logs ghost-onboard ghost-people ghost-project ghost-projects ghost-weekly; do
  check "$skill" "[[ -f '$WORKSPACE/skills/$skill/SKILL.md' ]]"
done
check "self-improving-agent" "[[ -f '$WORKSPACE/skills/self-improving-agent/SKILL.md' ]]"

echo ""
echo "🧠 Memory:"
for f in decisions.md people.md ideas.md commitments.md follow-ups.md; do
  check "memory/$f" "[[ -f '$WORKSPACE/memory/$f' ]]"
done

echo ""
echo "📝 Learnings:"
for f in LEARNINGS.md ERRORS.md FEATURE_REQUESTS.md; do
  check ".learnings/$f" "[[ -f '$WORKSPACE/.learnings/$f' ]]"
done

echo ""
echo "🛠️ Scripts:"
check "ghost_memory_db.py" "[[ -f '$WORKSPACE/scripts/ghost_memory_db.py' ]]"
check "ghost_unified_recall.py" "[[ -f '$WORKSPACE/scripts/ghost_unified_recall.py' ]]"
check "ghost_cli.py" "[[ -f '$WORKSPACE/scripts/ghost_cli.py' ]]"
check "ghost_session_context.py" "[[ -f '$WORKSPACE/scripts/ghost_session_context.py' ]]"
check "ghost_working_memory.py" "[[ -f '$WORKSPACE/scripts/ghost_working_memory.py' ]]"
check "ghost_research.py" "[[ -f '$WORKSPACE/scripts/ghost_research.py' ]]"
check "ghost_core/contracts.py" "[[ -f '$WORKSPACE/scripts/ghost_core/contracts.py' ]]"
check "memory_content_scanner.py" "[[ -f '$WORKSPACE/scripts/memory_content_scanner.py' ]]"
check "learning_review.py" "[[ -f '$WORKSPACE/scripts/learning_review.py' ]]"
check "heartbeat_pulse.sh" "[[ -f '$WORKSPACE/scripts/heartbeat_pulse.sh' ]]"

echo ""
echo "📦 Dependencies:"
check "sqlite-vec" "python3 -c 'import sqlite_vec'"
check "google-genai (optional)" "python3 -c 'from google import genai'" || true

echo ""
echo "🗄️ Memory DB:"
check "DB exists" "[[ -f '$WORKSPACE/.local/ghost_memory.db' ]]"
check "DB queryable" "python3 '$WORKSPACE/scripts/ghost_memory_db.py' stats"

echo ""
echo "📚 Knowledge docs:"
for doc in TOKEN-EFFICIENCY.md SELF-LEARNING.md PLAYBOOK.md SECOND-BRAIN.md CRON-PATTERNS.md LEARNING-REVIEW.md; do
  check "memory/reference/$doc" "[[ -f '$WORKSPACE/memory/reference/$doc' ]]"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Passed: $PASS"
echo "  ❌ Failed: $FAIL"
if [[ $FAIL -eq 0 ]]; then
  echo "  🎉 All tests passed!"
else
  echo "  ⚠️  Some checks failed — review above."
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
exit $FAIL
