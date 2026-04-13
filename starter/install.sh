#!/usr/bin/env bash
set -euo pipefail

# Ghost Brain Installer
# Installs Ghost Brain product layer into an existing OpenClaw workspace.

GHOST_VERSION="1.2.0"
REPO_URL="https://github.com/skzjoe/ghost-brain"

echo "👻 Ghost Brain Installer v${GHOST_VERSION}"
echo "=================================="
echo ""

# ─── Check prerequisites ───
echo "Checking prerequisites..."

# 1. OpenClaw must be installed
if ! command -v openclaw >/dev/null 2>&1; then
  echo "❌ OpenClaw is not installed."
  echo "   Install it first: https://github.com/openclaw/openclaw"
  exit 1
fi
echo "  ✅ OpenClaw $(openclaw --version 2>/dev/null || echo 'installed')"

# 2. Python3 must be available
PYTHON_BIN=""
for p in /home/linuxbrew/.linuxbrew/bin/python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do
  if [[ -x "$p" ]]; then
    PYTHON_BIN="$p"
    break
  fi
done
if [[ -z "$PYTHON_BIN" ]]; then
  command -v python3 >/dev/null 2>&1 && PYTHON_BIN=$(command -v python3)
fi
if [[ -z "$PYTHON_BIN" ]]; then
  echo "❌ Python3 not found."
  exit 1
fi
echo "  ✅ Python3: $PYTHON_BIN"

# 3. Determine workspace
WORKSPACE="${OPENCLAW_WORKSPACE:-$HOME/.openclaw/workspace}"
if [[ ! -d "$WORKSPACE" ]]; then
  echo "  Creating workspace: $WORKSPACE"
  mkdir -p "$WORKSPACE"
fi
echo "  ✅ Workspace: $WORKSPACE"
echo ""

# ─── Create directory structure ───
echo "Setting up Ghost Brain directories..."

mkdir -p "$WORKSPACE/memory"
mkdir -p "$WORKSPACE/memory/reference"
mkdir -p "$WORKSPACE/memory/projects"
mkdir -p "$WORKSPACE/memory/topics"
mkdir -p "$WORKSPACE/memory/syntheses"
mkdir -p "$WORKSPACE/.learnings/domains"
mkdir -p "$WORKSPACE/.learnings/projects"
mkdir -p "$WORKSPACE/.learnings/archive"
mkdir -p "$WORKSPACE/.local"
mkdir -p "$WORKSPACE/scripts"
mkdir -p "$WORKSPACE/skills"
mkdir -p "$WORKSPACE/tests"
mkdir -p "$WORKSPACE/media"
mkdir -p "$WORKSPACE/backups"

echo "  ✅ Directories created"

# ─── Copy template files (don't overwrite existing) ───
echo "Installing template files..."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_ROOT="$SCRIPT_DIR"
if [[ ! -d "$PACKAGE_ROOT/scripts" ]] && [[ -d "$SCRIPT_DIR/../scripts" ]]; then
  PACKAGE_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

copy_if_missing() {
  local src="$1"
  local dst="$2"
  if [[ ! -f "$dst" ]]; then
    if [[ -f "$src" ]]; then
      cp "$src" "$dst"
      echo "  📄 Created: $(basename "$dst")"
    fi
  else
    echo "  ⏭️  Exists: $(basename "$dst")"
  fi
}

# Core files
for f in SOUL.md IDENTITY.md USER.md MEMORY.md AGENTS.md ACTIVE_WORK.md GHOST_PLAYBOOK.md GHOST_PRODUCT_PLAN.md HEARTBEAT.md; do
  template="${SCRIPT_DIR}/templates/${f}"
  if [[ -f "$template" ]]; then
    copy_if_missing "$template" "$WORKSPACE/$f"
  fi
done

# Second-brain files
for f in decisions.md people.md ideas.md commitments.md follow-ups.md template.md; do
  template="${SCRIPT_DIR}/templates/memory/${f}"
  if [[ -f "$template" ]]; then
    copy_if_missing "$template" "$WORKSPACE/memory/$f"
  fi
done

# Learnings files
for f in LEARNINGS.md ERRORS.md FEATURE_REQUESTS.md REVIEW.md; do
  template="${SCRIPT_DIR}/templates/.learnings/${f}"
  if [[ -f "$template" ]]; then
    copy_if_missing "$template" "$WORKSPACE/.learnings/$f"
  fi
done

[[ -f "$SCRIPT_DIR/BOOTSTRAP.md" ]] && copy_if_missing "$SCRIPT_DIR/BOOTSTRAP.md" "$WORKSPACE/BOOTSTRAP.md"

echo ""

# ─── Copy scripts ───
echo "Installing Ghost scripts..."

if [[ -d "${PACKAGE_ROOT}/scripts" ]]; then
  for script in "${PACKAGE_ROOT}/scripts/"*; do
    base="$(basename "$script")"
    cp "$script" "$WORKSPACE/scripts/$base"
  done
  chmod +x "$WORKSPACE/scripts/"*.sh 2>/dev/null || true
  echo "  ✅ Scripts installed"
else
  echo "  ⚠️  No scripts directory found in package"
fi

# ─── Copy skills ───
echo "Installing Ghost skills..."

if [[ -d "${PACKAGE_ROOT}/skills" ]]; then
  shopt -s nullglob
  for skill_dir in "${PACKAGE_ROOT}/skills/"ghost-*/ "${PACKAGE_ROOT}/skills/self-improving-agent/"; do
    [[ -d "$skill_dir" ]] || continue
    base="$(basename "$skill_dir")"
    if [[ ! -d "$WORKSPACE/skills/$base" ]]; then
      cp -r "$skill_dir" "$WORKSPACE/skills/$base"
      echo "  📦 Installed: $base"
    else
      echo "  ⏭️  Exists: $base"
    fi
  done
  shopt -u nullglob
else
  echo "  ⚠️  No skills directory found in package"
fi

# ─── Copy tests ───
if [[ -d "${PACKAGE_ROOT}/tests" ]]; then
  echo "Installing tests..."
  cp -r "${PACKAGE_ROOT}/tests/"* "$WORKSPACE/tests/" 2>/dev/null || true
  echo "  ✅ Tests installed"
fi

echo ""

# ─── Reindex memory ───
echo "Reindexing memory..."
if openclaw memory reindex 2>/dev/null; then
  echo "  ✅ Memory indexed"
else
  echo "  ⚠️  Memory reindex skipped (run 'openclaw memory reindex' manually)"
fi

echo ""

# ─── Summary ───
echo "=================================="
echo "👻 Ghost Brain v${GHOST_VERSION} installed!"
echo ""
echo "Next steps:"
echo "  1. Edit SOUL.md, IDENTITY.md, USER.md in $WORKSPACE"
echo "  2. Seed MEMORY.md with your initial context"
echo "  3. Run /health to verify Ghost layer"
echo "  4. Run /onboard for interactive guided setup"
echo "  5. See BOOTSTRAP.md in your workspace for the full checklist"
echo ""
echo "Happy haunting! 👻"
