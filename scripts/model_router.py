#!/usr/bin/env python3
"""
model_router.py — Ghost Smart Model Router
Evaluates a message and recommends cheap vs strong model based on routing rules.

Usage (interactive):
    python3 scripts/model_router.py "quick question about X"
    python3 scripts/model_router.py --interactive
    python3 scripts/model_router.py --show-rules

Ghost uses this as a lightweight heuristic to decide whether to suggest a model switch.
Output: prints recommendation to stdout. Exit 0 = cheap, Exit 1 = strong.

Integration note:
    Ghost can call this at the start of complex tasks to check model fitness.
    The result is advisory — the user always has override authority.
"""

import json
import re
import sys
import argparse
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
SELECTOR_FILE = WORKSPACE / ".local/capability_selector.json"

# Default routing rules (fallback if capability_selector.json missing/malformed)
DEFAULT_CHEAP_SIGNALS = [
    "hi", "ok", "ครับ", "ขอบคุณ", "noted", "ได้ครับ", "โอเค", "yes", "no",
    "สวัสดี", "thanks", "got it", "sounds good", "sure", "cool", "alright",
    "done", "เสร็จ", "เข้าใจ", "ไม่เป็นไร"
]

DEFAULT_STRONG_SIGNALS = [
    # Deep work
    "audit", "review", "compare", "design", "architect", "refactor",
    "production", "deep", "opus", "analyze", "วิเคราะห์",
    # Code
    "implement", "build", "create", "write code", "script", "deploy",
    "bug", "error", "debug", "fix", "migrate", "test",
    # Long-form
    "proposal", "document", "spec", "strategy", "plan", "draft",
    "explain in detail", "อธิบาย", "เปรียบเทียบ", "วางแผน",
    # Research
    "research", "ค้นหา", "สรุป", "summarize", "compare", "evaluate",
    # ERPNext ops
    "erpnext", "frappe", "doctype", "reconcile", "migration",
]

# Routing boundaries
CHEAP_MAX_WORDS = 8
CHEAP_MAX_CHARS = 100
STRONG_MIN_WORDS = 25

# Model recommendations
CHEAP_MODEL = "gpt-5.4"           # fast/cheap default
STRONG_MODEL = "claude-sonnet"    # standard reasoning
HEAVY_MODEL = "claude-opus"       # deep design/audit

def load_routing_config() -> dict:
    try:
        data = json.loads(SELECTOR_FILE.read_text())
        return data.get("model_routing", {})
    except Exception:
        return {}

def score_message(text: str, config: dict) -> dict:
    """
    Score a message and return routing decision.
    Returns dict with: model, tier, reason, confidence, signals_matched
    """
    text_lower = text.lower().strip()
    word_count = len(text_lower.split())
    char_count = len(text_lower)

    cheap_signals = config.get("cheap_signals", DEFAULT_CHEAP_SIGNALS)
    strong_signals = config.get("strong_signals", DEFAULT_STRONG_SIGNALS)
    cheap_max_words = config.get("cheap_max_words", CHEAP_MAX_WORDS)

    # Collect matched signals
    cheap_matched = [s for s in cheap_signals if s.lower() in text_lower]
    strong_matched = [s for s in strong_signals if s.lower() in text_lower]

    # Special patterns
    has_code_block = "```" in text or re.search(r"\b(def |class |import |function |SELECT |FROM )\b", text)
    has_url = bool(re.search(r"https?://", text))
    has_thai_complex = bool(re.search(r"[ก-๙]{10,}", text))  # long Thai text = complex
    is_question = text.strip().endswith("?") or re.search(r"\b(what|how|why|when|where|which|ทำไม|อธิบาย|อย่างไร)\b", text_lower)

    # Scoring
    cheap_score = 0
    strong_score = 0

    if word_count <= cheap_max_words and not strong_matched and not has_code_block:
        cheap_score += 3
    if cheap_matched and not strong_matched:
        cheap_score += len(cheap_matched) * 2
    if char_count <= CHEAP_MAX_CHARS and not strong_matched:
        cheap_score += 2

    if strong_matched:
        strong_score += len(strong_matched) * 3
    if has_code_block:
        strong_score += 4
    if word_count >= STRONG_MIN_WORDS:
        strong_score += 2
    if has_url and is_question:
        strong_score += 2
    if has_thai_complex and word_count > 10:
        strong_score += 1

    # Heavy model triggers
    heavy_triggers = ["opus", "audit", "architect", "production grade", "deep review", "ออกแบบระบบ"]
    heavy_matched = [t for t in heavy_triggers if t.lower() in text_lower]

    # Decision
    if heavy_matched:
        model = HEAVY_MODEL
        tier = "heavy"
        reason = f"Heavy trigger: {heavy_matched}"
        confidence = "high"
    elif strong_score > cheap_score:
        model = STRONG_MODEL
        tier = "strong"
        reason = f"Strong signals ({strong_score} vs {cheap_score})"
        confidence = "high" if strong_score >= cheap_score + 3 else "medium"
    elif cheap_score > strong_score:
        model = CHEAP_MODEL
        tier = "cheap"
        reason = f"Short/simple ({word_count} words, {char_count} chars)"
        confidence = "high" if cheap_score >= 5 else "medium"
    else:
        # Tie → default to strong
        model = STRONG_MODEL
        tier = "strong"
        reason = "Tie — defaulting to strong"
        confidence = "low"

    return {
        "model": model,
        "tier": tier,
        "reason": reason,
        "confidence": confidence,
        "cheap_score": cheap_score,
        "strong_score": strong_score,
        "word_count": word_count,
        "signals": {
            "cheap": cheap_matched,
            "strong": strong_matched,
            "heavy": heavy_matched,
        }
    }


def print_recommendation(result: dict, verbose: bool = False):
    tier_emoji = {"cheap": "💚", "strong": "🔵", "heavy": "🟣"}.get(result["tier"], "⚪")
    conf_badge = {"high": "✅", "medium": "⚠️", "low": "❓"}.get(result["confidence"], "")
    print(f"\n{tier_emoji} Recommended: {result['model']}  {conf_badge}")
    print(f"   Tier:   {result['tier']}")
    print(f"   Reason: {result['reason']}")
    if verbose:
        print(f"   Scores: cheap={result['cheap_score']}, strong={result['strong_score']}")
        if result["signals"]["cheap"]:
            print(f"   Cheap signals: {result['signals']['cheap']}")
        if result["signals"]["strong"]:
            print(f"   Strong signals: {result['signals']['strong']}")
        if result["signals"]["heavy"]:
            print(f"   Heavy signals: {result['signals']['heavy']}")
    print()


def show_rules(config: dict):
    print("\n🔀 Model Routing Rules\n")
    print(f"  Cheap model:  {CHEAP_MODEL}")
    print(f"  Strong model: {STRONG_MODEL}")
    print(f"  Heavy model:  {HEAVY_MODEL}")
    print(f"\n  Cheap triggers (≤{config.get('cheap_max_words', CHEAP_MAX_WORDS)} words + signals):")
    for s in config.get("cheap_signals", DEFAULT_CHEAP_SIGNALS)[:10]:
        print(f"    - {s}")
    print(f"\n  Strong triggers:")
    for s in DEFAULT_STRONG_SIGNALS[:10]:
        print(f"    - {s}")
    print(f"\n  Heavy triggers: opus, audit, architect, production grade, deep review")
    print()


def interactive_mode(config: dict):
    print("\n👻 Ghost Model Router — Interactive Mode")
    print("  Enter messages to get routing recommendations. Ctrl+C to exit.\n")
    try:
        while True:
            text = input("Message: ").strip()
            if not text:
                continue
            result = score_message(text, config)
            print_recommendation(result, verbose=True)
    except (KeyboardInterrupt, EOFError):
        print("\nBye!")


def main():
    parser = argparse.ArgumentParser(description="Ghost smart model router")
    parser.add_argument("message", nargs="?", help="Message to evaluate")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--show-rules", action="store_true", help="Show routing rules")
    args = parser.parse_args()

    config = load_routing_config()

    if args.show_rules:
        show_rules(config)
        return

    if args.interactive:
        interactive_mode(config)
        return

    if not args.message:
        # Read from stdin if piped
        if not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            parser.print_help()
            sys.exit(1)
    else:
        text = args.message

    result = score_message(text, config)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_recommendation(result, verbose=args.verbose)

    # Exit code: 0 = cheap, 1 = strong/heavy
    sys.exit(0 if result["tier"] == "cheap" else 1)


if __name__ == "__main__":
    main()
