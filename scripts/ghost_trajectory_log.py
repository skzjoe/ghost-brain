#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from ghost_research_lib import append_trajectory_event, trajectory_summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost-trajectory-log", description="Ghost trajectory event log")
    sub = parser.add_subparsers(dest="command")

    append_p = sub.add_parser("append", help="Append a structured event")
    append_p.add_argument("run_id")
    append_p.add_argument("--event", required=True)
    append_p.add_argument("--suite", default="")
    append_p.add_argument("--task", default="")
    append_p.add_argument("--status", default="")
    append_p.add_argument("--score", type=float)
    append_p.add_argument("--notes", default="")
    append_p.add_argument("--data", default="{}")
    append_p.add_argument("--json", action="store_true")

    sum_p = sub.add_parser("summary", help="Summarize one run's events")
    sum_p.add_argument("run_id")
    sum_p.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict, as_json: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if as_json else None))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        if args.command == "append":
            try:
                metadata = json.loads(args.data)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid --data JSON: {exc}") from exc
            _emit(append_trajectory_event(run_id=args.run_id, event_type=args.event, suite=args.suite, task_id=args.task, status=args.status, score=args.score, notes=args.notes, metadata=metadata), args.json)
            return
        if args.command == "summary":
            _emit(trajectory_summary(args.run_id), args.json)
            return
        parser.print_help()
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
