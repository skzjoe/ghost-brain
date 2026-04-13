#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from ghost_research_lib import list_cases, list_suites, run_suite, show_run


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost-eval", description="Ghost eval runner")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run a suite or one case")
    run_p.add_argument("suite", choices=["ghostlite", "continuity", "all"])
    run_p.add_argument("--case")
    run_p.add_argument("--json", action="store_true")

    list_p = sub.add_parser("list", help="List suites or suite cases")
    list_p.add_argument("suite", nargs="?")
    list_p.add_argument("--json", action="store_true")

    show_p = sub.add_parser("show-run", help="Show a run artifact")
    show_p.add_argument("run_id")
    show_p.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict, as_json: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if as_json else None))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    if args.command == "run":
        _emit(run_suite(args.suite, case=args.case), args.json)
        return
    if args.command == "list":
        payload = {"schema_version": "ghost-eval/v1", "suites": list_suites()} if not args.suite else {"schema_version": "ghost-eval/v1", "suite": args.suite, "cases": list_cases(args.suite)}
        _emit(payload, args.json)
        return
    if args.command == "show-run":
        _emit(show_run(args.run_id), args.json)
        return
    parser.print_help()


if __name__ == "__main__":
    main()
