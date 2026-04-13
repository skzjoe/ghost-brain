#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from ghost_research_lib import list_cases, run_suite, safety_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost-safety-benchmark", description="Ghost safety benchmark")
    sub = parser.add_subparsers(dest="command")
    run_p = sub.add_parser("run", help="Run the safety suite")
    run_p.add_argument("--suite", default="core")
    run_p.add_argument("--json", action="store_true")
    list_p = sub.add_parser("list", help="List safety cases")
    list_p.add_argument("--json", action="store_true")
    rep_p = sub.add_parser("report", help="Summarize recent safety runs")
    rep_p.add_argument("--days", type=int, default=30)
    rep_p.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict, as_json: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if as_json else None))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "run":
        if args.suite != "core":
            raise SystemExit("Only --suite core is currently supported")
        _emit(run_suite("safety"), args.json)
        return
    if args.command == "list":
        _emit({"schema_version": "ghost-safety-benchmark/v1", "suite": "safety", "cases": list_cases("safety")}, args.json)
        return
    if args.command == "report":
        _emit(safety_report(days=args.days), args.json)
        return
    parser.print_help()


if __name__ == "__main__":
    main()
