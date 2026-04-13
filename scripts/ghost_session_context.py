#!/usr/bin/env python3
"""Ghost Brain — Session Context Surface

Summarize Ghost-owned execution state from ACTIVE_WORK.md and memory sources.

Usage:
  python3 scripts/ghost_session_context.py show
  python3 scripts/ghost_session_context.py show --json
"""

import argparse
import json
import os

from ghost_core.defaults import build_default_runtime
from ghost_core.workspace import get_workspace_paths

_paths = get_workspace_paths(os.environ.get("OPENCLAW_WORKSPACE"))
WORKSPACE = _paths.workspace


def _runtime():
    return build_default_runtime(str(WORKSPACE))


def _print_snapshot(snapshot: dict) -> None:
    print("🧭 Ghost Session Context")
    print(f"   Focus: {snapshot.get('focus') or '-'}")
    second_brain = snapshot.get("second_brain_focus") or {}
    if second_brain:
        print(f"   Second-brain risk: {second_brain.get('repetition_risk', '-')}")
        if second_brain.get("next_best_action"):
            print(f"   Next best action: {second_brain['next_best_action']}")
    guardrails = snapshot.get("guardrails") or {}
    if guardrails:
        print(f"   Capture risk: {guardrails.get('capture_risk', '-')}")
        if guardrails.get("next_action"):
            print(f"   Guardrail action: {guardrails['next_action']}")
    memory_sync = snapshot.get("memory_sync") or {}
    if memory_sync:
        print(f"   Memory sync: {memory_sync.get('status', '-')}")
        if memory_sync.get("recommendation"):
            print(f"   Sync action: {memory_sync['recommendation']}")
    if snapshot.get("blockers"):
        print("   Blockers:")
        for item in snapshot["blockers"][:5]:
            print(f"     - {item}")
    if snapshot.get("next_actions"):
        print("   Next actions:")
        for item in snapshot["next_actions"][:5]:
            print(f"     - {item}")
    if snapshot.get("commitments_due"):
        print("   Commitments due:")
        for item in snapshot["commitments_due"][:5]:
            print(f"     - {item}")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ghost_session_context",
        description="Ghost Brain session-context surface",
    )
    sub = parser.add_subparsers(dest="command")
    show_p = sub.add_parser("show", help="Show current Ghost session context")
    show_p.add_argument("--json", action="store_true", help="Return machine-readable JSON")
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    if args.command == "show":
        snapshot = _runtime().session_context.snapshot().to_dict()
        if args.json:
            print(json.dumps(snapshot, indent=2, ensure_ascii=False))
        else:
            _print_snapshot(snapshot)


if __name__ == "__main__":
    main()
