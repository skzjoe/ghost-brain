#!/usr/bin/env python3
"""Ghost Brain unified CLI.

Stable product-facing CLI over Ghost core surfaces.

Usage examples:
  python3 scripts/ghost_cli.py recall search "erpnext"
  python3 scripts/ghost_cli.py recall summary "erpnext"
  python3 scripts/ghost_cli.py recall report "erpnext" --json
  python3 scripts/ghost_cli.py capture "We decided to use X" --context meeting
  python3 scripts/ghost_cli.py user-model --show
  python3 scripts/ghost_cli.py learning status
  python3 scripts/ghost_cli.py learning digest --json
  python3 scripts/ghost_cli.py context show --json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from ghost_core.contracts import CaptureRequest, LearningReflectionRequest, RecallQuery, UserModelSignal
from ghost_core.defaults import build_default_runtime
from ghost_core.workspace import get_workspace_paths
from ghost_learning_loop import _emit_result as emit_learning_result
from ghost_learning_loop import _print_digest, _print_status
from ghost_conversation_memory import print_recent_report, print_search_report, recent_conversations, search_conversations
from ghost_guardrails import build_guardrail_report, print_guardrail_report
from ghost_memory_sync import build_memory_sync_report, print_memory_sync_report
from ghost_research import (
    build_dashboard,
    build_focus_report,
    compare_experiment,
    compare_runs,
    continuity_report,
    list_experiments,
    list_suites,
    log_manual_outcome,
    regression_report,
    run_suite,
    safety_report,
    save_baseline,
    show_run,
)
from ghost_unified_recall import build_recall_report, build_related_recall, recall_summary, related_recall_summary
from ghost_working_memory import build_brief, followups_due, print_brief, print_followups

_paths = get_workspace_paths(os.environ.get("OPENCLAW_WORKSPACE"))
WORKSPACE = _paths.workspace


def _runtime():
    return build_default_runtime(str(WORKSPACE))


def _split_sources(raw: str) -> list[str]:
    return [s.strip() for s in raw.split(",") if s.strip()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ghost", description="Ghost Brain unified CLI")
    sub = parser.add_subparsers(dest="command")

    recall_p = sub.add_parser("recall", help="Recall and capture surfaces")
    recall_sub = recall_p.add_subparsers(dest="recall_command")

    rs = recall_sub.add_parser("search", help="Search all memory layers")
    rs.add_argument("query")
    rs.add_argument("--limit", type=int, default=10)
    rs.add_argument("--sources", default="all")
    rs.add_argument("--json", action="store_true")

    rsum = recall_sub.add_parser("summary", help="Formatted recall summary")
    rsum.add_argument("query")
    rsum.add_argument("--limit", type=int, default=5)

    rr = recall_sub.add_parser("report", help="Structured recall report")
    rr.add_argument("query")
    rr.add_argument("--limit", type=int, default=10)
    rr.add_argument("--sources", default="all")
    rr.add_argument("--json", action="store_true")

    rrel = recall_sub.add_parser("related", help="Expand recall into linked memory types")
    rrel.add_argument("query")
    rrel.add_argument("--limit", type=int, default=8)
    rrel.add_argument("--sources", default="all")
    rrel.add_argument("--json", action="store_true")

    capture_p = sub.add_parser("capture", help="Smart capture content")
    capture_p.add_argument("content")
    capture_p.add_argument("--context", default="")
    capture_p.add_argument("--json", action="store_true")

    um_p = sub.add_parser("user-model", help="View or update user model")
    um_p.add_argument("--show", action="store_true")
    um_p.add_argument("--json", action="store_true")
    um_p.add_argument("--update", nargs=2, metavar=("TYPE", "DATA"))

    learning_p = sub.add_parser("learning", help="Learning loop surfaces")
    learning_sub = learning_p.add_subparsers(dest="learning_command")

    l_reflect = learning_sub.add_parser("reflect", help="Post-task reflection")
    l_reflect.add_argument("task_summary")
    l_reflect.add_argument("outcome")
    l_reflect.add_argument("--errors", default="")
    l_reflect.add_argument("--json", action="store_true")

    l_detect = learning_sub.add_parser("detect-skill", help="Detect skill candidate")
    l_detect.add_argument("task_log")
    l_detect.add_argument("--json", action="store_true")

    l_check = learning_sub.add_parser("check-skill", help="Check skill for improvement needs")
    l_check.add_argument("skill_name")
    l_check.add_argument("execution_log")
    l_check.add_argument("--success", dest="success", action="store_true", default=True)
    l_check.add_argument("--failure", dest="success", action="store_false")
    l_check.add_argument("--json", action="store_true")

    l_promote = learning_sub.add_parser("promote", help="Auto-promote qualified learnings")
    l_promote.add_argument("--json", action="store_true")

    l_status = learning_sub.add_parser("status", help="Show learning loop status")
    l_status.add_argument("--json", action="store_true")

    l_digest = learning_sub.add_parser("digest", help="Show learning impact digest")
    l_digest.add_argument("--days", type=int, default=30)
    l_digest.add_argument("--json", action="store_true")

    context_p = sub.add_parser("context", help="Session context surfaces")
    context_sub = context_p.add_subparsers(dest="context_command")
    c_show = context_sub.add_parser("show", help="Show current Ghost session context")
    c_show.add_argument("--json", action="store_true")

    brief_p = sub.add_parser("brief", help="Working-memory briefing")
    brief_p.add_argument("--json", action="store_true")
    brief_p.add_argument("--decisions", type=int, default=3)
    brief_p.add_argument("--followups", type=int, default=5)

    followups_p = sub.add_parser("followups", help="Follow-up attention surfaces")
    followups_sub = followups_p.add_subparsers(dest="followups_command")
    f_due = followups_sub.add_parser("due", help="Show due or stale follow-ups")
    f_due.add_argument("--json", action="store_true")
    f_due.add_argument("--limit", type=int, default=10)
    f_due.add_argument("--stale-after-days", type=int, default=7)

    conversation_p = sub.add_parser("conversation", help="Conversation and transcript recall")
    conversation_sub = conversation_p.add_subparsers(dest="conversation_command")
    conv_search = conversation_sub.add_parser("search", help="Search raw session transcripts")
    conv_search.add_argument("query")
    conv_search.add_argument("--days", type=int, default=30)
    conv_search.add_argument("--limit", type=int, default=10)
    conv_search.add_argument("--json", action="store_true")
    conv_recent = conversation_sub.add_parser("recent", help="Summarize recent non-automated sessions")
    conv_recent.add_argument("--days", type=int, default=7)
    conv_recent.add_argument("--limit", type=int, default=8)
    conv_recent.add_argument("--json", action="store_true")

    guardrails_p = sub.add_parser("guardrails", help="Self-discipline guardrails")
    guardrails_sub = guardrails_p.add_subparsers(dest="guardrails_command")
    guardrails_check = guardrails_sub.add_parser("check", help="Inspect uncaptured-session risk")
    guardrails_check.add_argument("--days", type=int, default=3)
    guardrails_check.add_argument("--json", action="store_true")
    guardrails_pre_new = guardrails_sub.add_parser("pre-new", help="Block /new when uncaptured work risk exists")
    guardrails_pre_new.add_argument("--days", type=int, default=3)
    guardrails_pre_new.add_argument("--json", action="store_true")

    memory_sync_p = sub.add_parser("memory-sync", help="Markdown to Memory DB freshness checks")
    memory_sync_sub = memory_sync_p.add_subparsers(dest="memory_sync_command")
    memory_sync_check = memory_sync_sub.add_parser("check", help="Check markdown↔DB freshness and drift")
    memory_sync_check.add_argument("--json", action="store_true")

    research_p = sub.add_parser("research", help="Research and eval surfaces")
    research_sub = research_p.add_subparsers(dest="research_command")

    r_run = research_sub.add_parser("run", help="Run a Ghost research suite")
    r_run.add_argument("suite", choices=["ghostlite", "safety", "continuity", "all"])
    r_run.add_argument("--case")
    r_run.add_argument("--json", action="store_true")

    r_list = research_sub.add_parser("list", help="List research suites and cases")
    r_list.add_argument("--json", action="store_true")

    r_show = research_sub.add_parser("show-run", help="Show a saved run")
    r_show.add_argument("run_id")
    r_show.add_argument("--json", action="store_true")

    r_base = research_sub.add_parser("baseline-save", help="Save latest suite run as baseline")
    r_base.add_argument("suite", choices=["ghostlite", "safety", "continuity", "all"])
    r_base.add_argument("--run-id")
    r_base.add_argument("--json", action="store_true")

    r_reg = research_sub.add_parser("regression", help="Compare latest or fresh run to suite baseline")
    r_reg.add_argument("suite", choices=["ghostlite", "safety", "continuity"])
    r_reg.add_argument("--run-now", action="store_true")
    r_reg.add_argument("--baseline-path")
    r_reg.add_argument("--json", action="store_true")

    r_compare = research_sub.add_parser("compare-runs", help="Compare two explicit runs")
    r_compare.add_argument("run_a")
    r_compare.add_argument("run_b")
    r_compare.add_argument("--json", action="store_true")

    r_dash = research_sub.add_parser("dashboard", help="Show research dashboard")
    r_dash.add_argument("--days", type=int, default=30)
    r_dash.add_argument("--json", action="store_true")

    r_focus = research_sub.add_parser("focus", help="Show actionable second-brain recommendations")
    r_focus.add_argument("--days", type=int, default=30)
    r_focus.add_argument("--json", action="store_true")

    r_cont = research_sub.add_parser("continuity-report", help="Show continuity summary")
    r_cont.add_argument("--days", type=int, default=30)
    r_cont.add_argument("--json", action="store_true")

    r_safety = research_sub.add_parser("safety-report", help="Show safety summary")
    r_safety.add_argument("--days", type=int, default=30)
    r_safety.add_argument("--json", action="store_true")

    r_exp = research_sub.add_parser("experiments", help="Show or compare experiments")
    r_exp.add_argument("name", nargs="?")
    r_exp.add_argument("against", nargs="?", default="baseline")
    r_exp.add_argument("--json", action="store_true")

    r_track = research_sub.add_parser("track-outcome", help="Log a manual experiment outcome")
    r_track.add_argument("suite")
    r_track.add_argument("task")
    r_track.add_argument("status", choices=["success", "partial", "failure"])
    r_track.add_argument("--score", type=float, default=1.0)
    r_track.add_argument("--notes", default="")
    r_track.add_argument("--model", default="")
    r_track.add_argument("--metadata-json", default="{}")
    r_track.add_argument("--json", action="store_true")

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    runtime = _runtime()

    if not args.command:
        parser.print_help()
        return

    if args.command == "recall":
        if not args.recall_command:
            recall_parser = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
            parser.print_help()
            return
        if args.recall_command == "search":
            sources = _split_sources(args.sources)
            if args.json:
                report = runtime.recall.recall(RecallQuery(query=args.query, limit=args.limit, sources=sources))
                print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
            else:
                results = build_recall_report(args.query, limit=args.limit, sources=sources).get("results", [])
                if not results:
                    print("No results found.")
                    return
                for r in results:
                    score = r.get("score", 0)
                    print(
                        f"[{score:.2f} | {r.get('confidence', 'low'):6s}] "
                        f"{r.get('item_type', '?'):12s} {r.get('citation', r.get('file', '?')):50s} "
                        f"{r.get('snippet', '')[:80]}"
                    )
        elif args.recall_command == "summary":
            print(recall_summary(args.query, limit=args.limit))
        elif args.recall_command == "report":
            report = runtime.recall.recall(
                RecallQuery(query=args.query, limit=args.limit, sources=_split_sources(args.sources))
            ).to_dict()
            if args.json:
                print(json.dumps(report, indent=2, ensure_ascii=False))
            else:
                print(recall_summary(args.query, limit=args.limit))
        elif args.recall_command == "related":
            related = build_related_recall(args.query, limit=args.limit, sources=_split_sources(args.sources))
            if args.json:
                print(json.dumps(related, indent=2, ensure_ascii=False))
            else:
                print(related_recall_summary(args.query, limit=args.limit))
        return

    if args.command == "capture":
        capture = runtime.recall.capture(CaptureRequest(content=args.content, context=args.context)).to_dict()
        capture["file"] = capture["path"]
        capture["duplicate_warning"] = capture["message"] if capture["duplicate"] or not capture["added"] else ""
        if args.json:
            print(json.dumps(capture, indent=2, ensure_ascii=False))
        else:
            print(f"Type:    {capture['type']}")
            print(f"File:    {capture['file']}")
            if capture.get("tags"):
                print(f"Tags:    {', '.join(capture['tags'])}")
            if capture.get("duplicate_warning"):
                print(f"Warning: {capture['duplicate_warning']}")
            else:
                print("Status:  captured")
        return

    if args.command == "user-model":
        if args.update:
            signal_type, signal_data = args.update
            runtime.recall.update_user_model(UserModelSignal(signal_type=signal_type, data=signal_data))
            print(f"Updated user model ({signal_type}): {signal_data}")
        else:
            model = runtime.recall.get_user_model()
            print(json.dumps(model, indent=2, ensure_ascii=False))
        return

    if args.command == "learning":
        if args.learning_command == "reflect":
            errors = [e.strip() for e in args.errors.split(",") if e.strip()] or []
            result = runtime.learning.reflect(
                LearningReflectionRequest(task_summary=args.task_summary, outcome=args.outcome, errors=errors)
            ).to_dict()
            if args.json:
                emit_learning_result("reflect", result, True)
            else:
                if result["captured"]:
                    for entry in result["entries"]:
                        print(f"✅ Captured [{entry['id']}] ({entry['category']}) → {entry['scope']}")
                    if result.get("proposed_skill"):
                        print(f"💡 Skill candidate detected: {result['proposed_skill']}")
                else:
                    print("ℹ️  No learning signal detected — nothing captured.")
        elif args.learning_command == "detect-skill":
            candidate = runtime.learning.detect_skill_candidate(args.task_log)
            if args.json:
                emit_learning_result("detect-skill", candidate or {}, True)
            else:
                if candidate:
                    print(f"💡 Skill candidate: {candidate['name']}")
                    print(f"   Steps: {len(candidate['steps'])}")
                    print(f"   Description: {candidate['description'][:100]}")
                    print(json.dumps(candidate, indent=2, ensure_ascii=False))
                else:
                    print("ℹ️  No skill candidate detected.")
        elif args.learning_command == "check-skill":
            result = runtime.learning.check_skill(args.skill_name, args.execution_log, args.success)
            if args.json:
                emit_learning_result("check-skill", result or {"skill_name": args.skill_name, "clean": True}, True)
            else:
                if result:
                    print(f"⚠️  Improvement needed for {result['skill_name']}")
                    print(f"   Issue: {result['issue']}")
                    print(f"   Fix: {result['proposed_fix']}")
                else:
                    print(f"✅ {args.skill_name} executed cleanly.")
        elif args.learning_command == "promote":
            promoted = runtime.learning.promote()
            if args.json:
                emit_learning_result("promote", {"actions": promoted}, True)
            else:
                if promoted:
                    for item in promoted:
                        print(f"⬆️  [{item['id']}] → {item['action']} ({item['reason']})")
                else:
                    print("ℹ️  No learnings qualify for promotion right now.")
        elif args.learning_command == "status":
            stats = runtime.learning.status().to_dict()
            if args.json:
                emit_learning_result("status", stats, True)
            else:
                _print_status(stats)
        elif args.learning_command == "digest":
            digest = runtime.learning.digest(days=args.days).to_dict()
            if args.json:
                emit_learning_result("digest", digest, True)
            else:
                _print_digest(digest)
        else:
            parser.print_help()
        return

    if args.command == "context":
        snapshot = runtime.session_context.snapshot().to_dict()
        if args.context_command == "show":
            if args.json:
                print(json.dumps(snapshot, indent=2, ensure_ascii=False))
            else:
                print("🧭 Ghost Session Context")
                print(f"   Focus: {snapshot.get('focus') or '-'}")
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
                guardrails = snapshot.get("guardrails") or {}
                if guardrails:
                    print(f"   Capture risk: {guardrails.get('capture_risk', '-')}")
                memory_sync = snapshot.get("memory_sync") or {}
                if memory_sync:
                    print(f"   Memory sync: {memory_sync.get('status', '-')}")
        else:
            parser.print_help()
        return

    if args.command == "brief":
        payload = build_brief(decision_limit=args.decisions, followup_limit=args.followups)
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print_brief(payload)
        return

    if args.command == "followups":
        if args.followups_command == "due":
            payload = followups_due(limit=args.limit, stale_after_days=args.stale_after_days)
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print_followups(payload)
        else:
            parser.print_help()
        return

    if args.command == "conversation":
        if args.conversation_command == "search":
            payload = search_conversations(args.query, limit=args.limit, days=args.days)
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print_search_report(payload)
        elif args.conversation_command == "recent":
            payload = recent_conversations(days=args.days, limit=args.limit)
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print_recent_report(payload)
        else:
            parser.print_help()
        return

    if args.command == "guardrails":
        if args.guardrails_command in {"check", "pre-new"}:
            payload = build_guardrail_report(days=args.days)
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print_guardrail_report(payload)
            if args.guardrails_command == "pre-new" and payload.get("status") != "clear":
                raise SystemExit(2)
        else:
            parser.print_help()
        return

    if args.command == "memory-sync":
        if args.memory_sync_command == "check":
            payload = build_memory_sync_report()
            if args.json:
                print(json.dumps(payload, indent=2, ensure_ascii=False))
            else:
                print_memory_sync_report(payload)
        else:
            parser.print_help()
        return

    if args.command == "research":
        try:
            if args.research_command == "run":
                payload = run_suite(args.suite, case=args.case)
            elif args.research_command == "list":
                payload = {"schema_version": "ghost-eval/v1", "suites": list_suites()}
            elif args.research_command == "show-run":
                payload = show_run(args.run_id)
            elif args.research_command == "baseline-save":
                payload = save_baseline(args.suite, run_id=args.run_id)
            elif args.research_command == "regression":
                payload = regression_report(args.suite, run_now=args.run_now, baseline_path=args.baseline_path)
            elif args.research_command == "compare-runs":
                payload = compare_runs(args.run_a, args.run_b)
            elif args.research_command == "dashboard":
                payload = build_dashboard(days=args.days)
            elif args.research_command == "focus":
                payload = build_focus_report(days=args.days)
            elif args.research_command == "continuity-report":
                payload = continuity_report(days=args.days)
            elif args.research_command == "safety-report":
                payload = safety_report(days=args.days)
            elif args.research_command == "experiments":
                payload = list_experiments() if not args.name else compare_experiment(args.name, args.against)
            elif args.research_command == "track-outcome":
                payload = log_manual_outcome(
                    suite=args.suite,
                    task=args.task,
                    status=args.status,
                    score=args.score,
                    notes=args.notes,
                    model=args.model,
                    metadata=json.loads(args.metadata_json),
                )
            else:
                parser.print_help()
                return
        except (ValueError, json.JSONDecodeError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            raise SystemExit(2)

        print(json.dumps(payload, indent=2, ensure_ascii=False) if getattr(args, "json", False) else json.dumps(payload, ensure_ascii=False))
        return


if __name__ == "__main__":
    main()
