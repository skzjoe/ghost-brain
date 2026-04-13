#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys

from ghost_research_lib import add_experiment, compare_experiment, list_experiments, run_experiment


def _parse_metrics(values: list[str]) -> dict[str, object]:
    metrics: dict[str, object] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(f"Invalid metric '{value}', expected key=value")
        key, raw = value.split("=", 1)
        try:
            metrics[key] = int(raw)
        except ValueError:
            try:
                metrics[key] = float(raw)
            except ValueError:
                metrics[key] = raw
    return metrics


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost-experiments", description="Ghost experiment registry")
    sub = parser.add_subparsers(dest="command")

    add = sub.add_parser("add", help="Add a new experiment")
    add.add_argument("name")
    add.add_argument("--hypothesis", required=True)
    add.add_argument("--tag", dest="tags", action="append", default=[])
    add.add_argument("--json", action="store_true")

    run = sub.add_parser("run", help="Record an experiment run")
    run.add_argument("name")
    run.add_argument("--metric", dest="metrics", action="append", default=[])
    run.add_argument("--notes", default="")
    run.add_argument("--status", default="success")
    run.add_argument("--json", action="store_true")

    show = sub.add_parser("show", help="Show all experiments")
    show.add_argument("--json", action="store_true")

    compare = sub.add_parser("compare", help="Compare latest run against baseline or another experiment")
    compare.add_argument("name")
    compare.add_argument("against", nargs="?", default="baseline")
    compare.add_argument("--json", action="store_true")
    return parser


def _emit(payload: dict, as_json: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if as_json else None))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        if args.command == "add":
            _emit(add_experiment(args.name, args.hypothesis, tags=args.tags), args.json)
            return
        if args.command == "run":
            _emit(run_experiment(args.name, _parse_metrics(args.metrics), notes=args.notes, status=args.status), args.json)
            return
        if args.command == "show":
            _emit(list_experiments(), args.json)
            return
        if args.command == "compare":
            _emit(compare_experiment(args.name, args.against), args.json)
            return
        parser.print_help()
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
