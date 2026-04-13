#!/usr/bin/env python3
"""Compatibility umbrella CLI for Ghost research surfaces."""

from __future__ import annotations

import argparse
import json
import sys

from ghost_research_lib import (
    add_experiment,
    build_dashboard,
    build_focus_report,
    compare_experiment,
    compare_runs,
    continuity_report,
    list_cases,
    list_experiments,
    log_manual_outcome,
    regression_report,
    run_experiment,
    run_suite,
    safety_report,
    save_baseline,
    show_run,
    list_suites,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost-research", description="Ghost research/eval toolkit")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="Run a research suite")
    run_p.add_argument("suite", choices=["ghostlite", "safety", "continuity", "all"])
    run_p.add_argument("--case")
    run_p.add_argument("--json", action="store_true")

    list_p = sub.add_parser("list", help="List available suites and cases")
    list_p.add_argument("suite", nargs="?")
    list_p.add_argument("--json", action="store_true")

    show_p = sub.add_parser("show-run", help="Show a saved run")
    show_p.add_argument("run_id")
    show_p.add_argument("--json", action="store_true")

    base_p = sub.add_parser("baseline", help="Save latest run as baseline")
    base_sub = base_p.add_subparsers(dest="baseline_command")
    save_p = base_sub.add_parser("save", help="Save latest run as baseline")
    save_p.add_argument("suite", choices=["ghostlite", "safety", "continuity", "all"])
    save_p.add_argument("--run-id")
    save_p.add_argument("--json", action="store_true")

    reg_p = sub.add_parser("regression", help="Compare current run to baseline")
    reg_p.add_argument("suite", choices=["ghostlite", "safety", "continuity"])
    reg_p.add_argument("--run-now", action="store_true")
    reg_p.add_argument("--baseline-path")
    reg_p.add_argument("--json", action="store_true")

    compare_p = sub.add_parser("compare-runs", help="Compare two explicit runs")
    compare_p.add_argument("run_a")
    compare_p.add_argument("run_b")
    compare_p.add_argument("--json", action="store_true")

    dash_p = sub.add_parser("dashboard", help="Show research dashboard")
    dash_p.add_argument("--days", type=int, default=30)
    dash_p.add_argument("--json", action="store_true")

    focus_p = sub.add_parser("focus", help="Show actionable second-brain recommendations")
    focus_p.add_argument("--days", type=int, default=30)
    focus_p.add_argument("--json", action="store_true")

    cont_p = sub.add_parser("continuity-report", help="Show continuity benchmark summary")
    cont_p.add_argument("--days", type=int, default=30)
    cont_p.add_argument("--json", action="store_true")

    safety_p = sub.add_parser("safety-report", help="Show safety benchmark summary")
    safety_p.add_argument("--days", type=int, default=30)
    safety_p.add_argument("--json", action="store_true")

    track_p = sub.add_parser("track", help="Log a manual outcome")
    track_sub = track_p.add_subparsers(dest="track_command")
    outcome_p = track_sub.add_parser("outcome", help="Log a manual experiment outcome")
    outcome_p.add_argument("suite")
    outcome_p.add_argument("task")
    outcome_p.add_argument("status", choices=["success", "partial", "failure"])
    outcome_p.add_argument("--score", type=float, default=1.0)
    outcome_p.add_argument("--notes", default="")
    outcome_p.add_argument("--model", default="")
    outcome_p.add_argument("--metadata-json", default="{}")
    outcome_p.add_argument("--json", action="store_true")

    exp_p = sub.add_parser("experiments", help="Experiment registry helpers")
    exp_sub = exp_p.add_subparsers(dest="experiments_command")
    exp_add = exp_sub.add_parser("add", help="Create an experiment")
    exp_add.add_argument("name")
    exp_add.add_argument("--hypothesis", required=True)
    exp_add.add_argument("--tag", dest="tags", action="append", default=[])
    exp_add.add_argument("--json", action="store_true")

    exp_run = exp_sub.add_parser("run", help="Record an experiment run")
    exp_run.add_argument("name")
    exp_run.add_argument("--metric", dest="metrics", action="append", default=[])
    exp_run.add_argument("--notes", default="")
    exp_run.add_argument("--status", default="success")
    exp_run.add_argument("--json", action="store_true")

    exp_show = exp_sub.add_parser("show", help="Show experiments")
    exp_show.add_argument("--json", action="store_true")
    exp_compare = exp_sub.add_parser("compare", help="Compare an experiment to baseline or another experiment")
    exp_compare.add_argument("name")
    exp_compare.add_argument("against", nargs="?", default="baseline")
    exp_compare.add_argument("--json", action="store_true")

    return parser


def _parse_metrics(values: list[str]) -> dict[str, object]:
    metrics: dict[str, object] = {}
    for value in values:
        if "=" not in value:
            raise ValueError(f"Invalid metric '{value}', expected key=value")
        key, raw = value.split("=", 1)
        try:
            metrics[key] = int(raw)
        except ValueError:
            try:
                metrics[key] = float(raw)
            except ValueError:
                metrics[key] = raw
    return metrics


def _emit(payload: dict, as_json: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2 if as_json else None))


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    try:
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
        if args.command == "baseline" and args.baseline_command == "save":
            _emit(save_baseline(args.suite, run_id=args.run_id), args.json)
            return
        if args.command == "regression":
            _emit(regression_report(args.suite, run_now=args.run_now, baseline_path=args.baseline_path), args.json)
            return
        if args.command == "compare-runs":
            _emit(compare_runs(args.run_a, args.run_b), args.json)
            return
        if args.command == "dashboard":
            _emit(build_dashboard(days=args.days), args.json)
            return
        if args.command == "focus":
            _emit(build_focus_report(days=args.days), args.json)
            return
        if args.command == "continuity-report":
            _emit(continuity_report(days=args.days), args.json)
            return
        if args.command == "safety-report":
            _emit(safety_report(days=args.days), args.json)
            return
        if args.command == "track" and args.track_command == "outcome":
            payload = log_manual_outcome(
                suite=args.suite,
                task=args.task,
                status=args.status,
                score=args.score,
                notes=args.notes,
                model=args.model,
                metadata=json.loads(args.metadata_json),
            )
            _emit(payload, args.json)
            return
        if args.command == "experiments" and args.experiments_command == "add":
            _emit(add_experiment(args.name, args.hypothesis, tags=args.tags), args.json)
            return
        if args.command == "experiments" and args.experiments_command == "run":
            _emit(run_experiment(args.name, _parse_metrics(args.metrics), notes=args.notes, status=args.status), args.json)
            return
        if args.command == "experiments" and args.experiments_command == "show":
            _emit(list_experiments(), args.json)
            return
        if args.command == "experiments" and args.experiments_command == "compare":
            _emit(compare_experiment(args.name, args.against), args.json)
            return

        parser.print_help()
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
