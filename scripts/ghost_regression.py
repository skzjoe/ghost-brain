#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from ghost_research_lib import compare_runs, regression_check, regression_report, save_baseline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost-regression", description="Ghost regression runner")
    sub = parser.add_subparsers(dest="command")

    base = sub.add_parser("baseline", help="Save baseline")
    base.add_argument("suite", choices=["ghostlite", "safety", "continuity", "all"])
    base.add_argument("run_id", nargs="?")
    base.add_argument("--json", action="store_true")

    comp = sub.add_parser("compare", help="Compare latest or fresh run to baseline")
    comp.add_argument("suite", choices=["ghostlite", "safety", "continuity"])
    comp.add_argument("--run-now", action="store_true")
    comp.add_argument("--baseline-path")
    comp.add_argument("--json", action="store_true")

    explicit = sub.add_parser("compare-runs", help="Compare two explicit run ids")
    explicit.add_argument("run_a")
    explicit.add_argument("run_b")
    explicit.add_argument("--json", action="store_true")

    check = sub.add_parser("check", help="Fail non-zero on regression")
    check.add_argument("suite", choices=["ghostlite", "safety", "continuity"])
    check.add_argument("--run-now", action="store_true")
    check.add_argument("--fail-on", default="regression", choices=["regression", "accuracy_drop"])
    check.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict, as_json: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if as_json else None))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        if args.command == "baseline":
            _emit(save_baseline(args.suite, run_id=args.run_id), args.json)
            return
        if args.command == "compare":
            _emit(regression_report(args.suite, run_now=args.run_now, baseline_path=args.baseline_path), args.json)
            return
        if args.command == "compare-runs":
            _emit(compare_runs(args.run_a, args.run_b), args.json)
            return
        if args.command == "check":
            payload, should_fail = regression_check(args.suite, fail_on=args.fail_on, run_now=args.run_now)
            _emit(payload, args.json)
            if should_fail:
                raise SystemExit(1)
            return
        parser.print_help()
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
