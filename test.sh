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
    ((PASS++))
  else
    echo "  ❌ $desc"
    ((FAIL++))
  fi
}

echo "👻 Ghost Brain — Smoke Test"
echo ""

# Skills
echo "📦 Skills:"
for skill in ghost-audit ghost-capture ghost-commitments ghost-conflicts ghost-decisions \
             ghost-export ghost-fastlanes ghost-followups ghost-health ghost-ideas \
             ghost-logs ghost-onboard ghost-people ghost-project ghost-projects ghost-weekly; do
  check "$skill" "[[ -f '$WORKSPACE/skills/$skill/SKILL.md' ]]"
done
check "self-improving-agent" "[[ -f '$WORKSPACE/skills/self-improving-agent/SKILL.md' ]]"

# Memory structure
echo ""
echo "🧠 Memory:"
for f in decisions.md people.md ideas.md commitments.md follow-ups.md; do
  check "memory/$f" "[[ -f '$WORKSPACE/memory/$f' ]]"
done

# Learnings
echo ""
echo "📝 Learnings:"
for f in LEARNINGS.md ERRORS.md FEATURE_REQUESTS.md; do
  check ".learnings/$f" "[[ -f '$WORKSPACE/.learnings/$f' ]]"
done

# Scripts
echo ""
echo "🛠️ Scripts:"
check "ghost_memory_db.py" "[[ -f '$WORKSPACE/scripts/ghost_memory_db.py' ]]"
check "sr_review.py" "[[ -f '$WORKSPACE/scripts/sr_review.py' ]]"
check "heartbeat_pulse.sh" "[[ -f '$WORKSPACE/scripts/heartbeat_pulse.sh' ]]"

# Dependencies
echo ""
echo "📦 Dependencies:"
check "sqlite-vec" "python3 -c 'import sqlite_vec'"
check "google-genai (optional)" "python3 -c 'from google import genai'" || true

# Memory DB
echo ""
echo "🗄️ Memory DB:"
check "DB exists" "[[ -f '$WORKSPACE/.local/ghost_memory.db' ]]"
check "DB queryable" "python3 '$WORKSPACE/scripts/ghost_memory_db.py' stats"

# Knowledge docs
echo ""
echo "📚 Knowledge docs:"
for doc in TOKEN-EFFICIENCY.md SELF-LEARNING.md PLAYBOOK.md SECOND-BRAIN.md CRON-PATTERNS.md; do
  check "memory/reference/$doc" "[[ -f '$WORKSPACE/memory/reference/$doc' ]]"
done

# Summary
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
