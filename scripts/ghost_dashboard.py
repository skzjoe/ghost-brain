#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from ghost_research_lib import build_dashboard, build_focus_report, continuity_report, list_experiments, safety_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost-dashboard", description="Ghost research dashboard")
    sub = parser.add_subparsers(dest="command")

    summary = sub.add_parser("summary", help="Unified dashboard summary")
    summary.add_argument("--days", type=int, default=30)
    summary.add_argument("--json", action="store_true")

    usage = sub.add_parser("usage", help="Usage section")
    usage.add_argument("--days", type=int, default=30)
    usage.add_argument("--json", action="store_true")

    continuity = sub.add_parser("continuity", help="Continuity section")
    continuity.add_argument("--days", type=int, default=30)
    continuity.add_argument("--json", action="store_true")

    experiments = sub.add_parser("experiments", help="Experiment section")
    experiments.add_argument("--json", action="store_true")

    focus = sub.add_parser("focus", help="Actionable second-brain recommendations")
    focus.add_argument("--days", type=int, default=30)
    focus.add_argument("--json", action="store_true")

    safety = sub.add_parser("safety", help="Safety section")
    safety.add_argument("--days", type=int, default=30)
    safety.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict, as_json: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if as_json else None))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        if args.command == "summary":
            _emit(build_dashboard(days=args.days), args.json)
            return
        if args.command == "usage":
            payload = build_dashboard(days=args.days)
            _emit({"schema_version": payload["schema_version"], "generated_at": payload["generated_at"], "usage": payload.get("usage", {})}, args.json)
            return
        if args.command == "continuity":
            _emit(continuity_report(days=args.days), args.json)
            return
        if args.command == "experiments":
            _emit(list_experiments(), args.json)
            return
        if args.command == "focus":
            _emit(build_focus_report(days=args.days), args.json)
            return
        if args.command == "safety":
            _emit(safety_report(days=args.days), args.json)
            return
        parser.print_help()
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
