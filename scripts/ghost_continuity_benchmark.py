#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from ghost_research_lib import compare_runs, continuity_report, list_cases, run_suite


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost-continuity-benchmark", description="Ghost continuity benchmark")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run continuity suite")
    run_p.add_argument("--suite", default="core")
    run_p.add_argument("--case")
    run_p.add_argument("--json", action="store_true")

    list_p = sub.add_parser("list", help="List continuity cases")
    list_p.add_argument("--json", action="store_true")

    rep_p = sub.add_parser("report", help="Show continuity summary")
    rep_p.add_argument("--days", type=int, default=30)
    rep_p.add_argument("--json", action="store_true")

    cmp_p = sub.add_parser("compare", help="Compare two continuity runs")
    cmp_p.add_argument("run_a")
    cmp_p.add_argument("run_b")
    cmp_p.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict, as_json: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if as_json else None))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "run":
        if args.suite != "core":
            raise SystemExit("Only --suite core is currently supported")
        _emit(run_suite("continuity", case=args.case), args.json)
        return
    if args.command == "list":
        _emit({"schema_version": "ghost-eval/v1", "suite": "continuity", "cases": list_cases("continuity")}, args.json)
        return
    if args.command == "report":
        _emit(continuity_report(days=args.days), args.json)
        return
    if args.command == "compare":
        _emit(compare_runs(args.run_a, args.run_b), args.json)
        return
    parser.print_help()


if __name__ == "__main__":
    main()
