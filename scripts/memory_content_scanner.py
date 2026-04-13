#!/usr/bin/env python3
"""
Ghost Brain — Memory Content Scanner

Validates content before it gets written to memory/ or .learnings/ files.
Prevents prompt injection, exfiltration attempts, and invisible unicode
from entering the system prompt via captured memory.

Inspired by Hermes Agent's memory_tool.py content scanning, adapted for
Ghost Brain's markdown-first memory system.

Usage:
    from memory_content_scanner import scan_content, is_safe

    result = scan_content("some text to validate")
    if not result.safe:
        print(f"Blocked: {result.reason}")

    # Quick check
    if is_safe(text):
        write_to_memory(text)

CLI:
    python3 scripts/memory_content_scanner.py "text to check"
    python3 scripts/memory_content_scanner.py --file memory/decisions.md
    python3 scripts/memory_content_scanner.py --scan-all
"""

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE",
    os.path.expanduser("~/.openclaw/workspace")))

# Prompt injection patterns
_INJECTION_PATTERNS = [
    (r'ignore\s+(previous|all|above|prior)\s+\w*\s*(instructions|rules)', "prompt_injection"),
    (r'you\s+are\s+now\s+', "role_hijack"),
    (r'do\s+not\s+tell\s+the\s+user', "deception_hide"),
    (r'system\s+prompt\s+override', "sys_prompt_override"),
    (r'disregard\s+(your|all|any)\s+(instructions|rules|guidelines)', "disregard_rules"),
    (r'act\s+as\s+(if|though)\s+you\s+(have\s+no|don\'t\s+have)\s+(restrictions|limits|rules)', "bypass_restrictions"),
    (r'pretend\s+(you\s+are|to\s+be)\s+a\s+different', "identity_swap"),
    (r'forget\s+(everything|all|your)\s+(you|instructions|rules)', "memory_wipe"),
    (r'new\s+instructions?\s*:', "instruction_override"),
    (r'<\s*system\s*>', "xml_system_inject"),
]

# Exfiltration patterns
_EXFIL_PATTERNS = [
    (r'curl\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)', "exfil_curl"),
    (r'wget\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)', "exfil_wget"),
    (r'cat\s+[^\n]*(\.env|credentials|\.netrc|\.pgpass|\.npmrc|\.pypirc)', "read_secrets"),
    (r'curl\s+[^\n]*secrets/', "exfil_secrets_dir"),
    (r'authorized_keys', "ssh_backdoor"),
    (r'\$HOME/\.ssh|\~/\.ssh', "ssh_access"),
    (r'eval\s*\(\s*base64', "eval_base64"),
    (r'python[3]?\s+-c\s+.*import\s+(os|subprocess|socket)', "python_exec_inject"),
]

# Invisible unicode characters that could be used for injection
_INVISIBLE_CHARS = {
    '\u200b': 'ZERO WIDTH SPACE',
    '\u200c': 'ZERO WIDTH NON-JOINER',
    # U+200D (ZWJ) intentionally excluded — used in emoji sequences like 👨‍👩‍👦
    '\u2060': 'WORD JOINER',
    '\ufeff': 'ZERO WIDTH NO-BREAK SPACE',
    '\u202a': 'LEFT-TO-RIGHT EMBEDDING',
    '\u202b': 'RIGHT-TO-LEFT EMBEDDING',
    '\u202c': 'POP DIRECTIONAL FORMATTING',
    '\u202d': 'LEFT-TO-RIGHT OVERRIDE',
    '\u202e': 'RIGHT-TO-LEFT OVERRIDE',
    '\u2066': 'LEFT-TO-RIGHT ISOLATE',
    '\u2067': 'RIGHT-TO-LEFT ISOLATE',
    '\u2068': 'FIRST STRONG ISOLATE',
    '\u2069': 'POP DIRECTIONAL ISOLATE',
}

# Memory file size budgets (chars)
_SIZE_BUDGETS = {
    "memory/decisions.md": 50_000,
    "memory/people.md": 30_000,
    "memory/ideas.md": 20_000,
    "memory/commitments.md": 15_000,
    "memory/follow-ups.md": 15_000,
    "memory/wiki-index.md": 30_000,
    "memory/wiki-log.md": 50_000,
    ".learnings/LEARNINGS.md": 40_000,
    ".learnings/ERRORS.md": 30_000,
    ".learnings/FEATURE_REQUESTS.md": 20_000,
}

# Default budget for files not in the map
_DEFAULT_SIZE_BUDGET = 60_000


@dataclass
class ScanResult:
    safe: bool
    reason: Optional[str] = None
    pattern_id: Optional[str] = None
    details: Optional[str] = None


def scan_content(text: str) -> ScanResult:
    """Scan text for injection/exfiltration patterns and invisible chars."""
    if not text or not text.strip():
        return ScanResult(safe=True)

    # Check invisible unicode
    for char, name in _INVISIBLE_CHARS.items():
        if char in text:
            return ScanResult(
                safe=False,
                reason=f"Contains invisible unicode: {name} (U+{ord(char):04X})",
                pattern_id="invisible_unicode",
                details=f"Character U+{ord(char):04X} found at position {text.index(char)}"
            )

    # Check injection patterns (skip if content looks like an audit/reference doc)
    is_reference = any(marker in text[:200] for marker in [
        'Production-Grade Audit', 'pattern detected:', 'Prompt injection',
        'threat pattern', 'example:', 'Example:',
    ])
    for pattern, pid in _INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            if is_reference:
                continue
            match = re.search(pattern, text, re.IGNORECASE)
            return ScanResult(
                safe=False,
                reason=f"Prompt injection pattern detected: {pid}",
                pattern_id=pid,
                details=f"Matched: '{match.group()[:80]}'"
            )

    # Check exfiltration patterns
    for pattern, pid in _EXFIL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            if is_reference:
                continue
            match = re.search(pattern, text, re.IGNORECASE)
            return ScanResult(
                safe=False,
                reason=f"Exfiltration pattern detected: {pid}",
                pattern_id=pid,
                details=f"Matched: '{match.group()[:80]}'"
            )

    return ScanResult(safe=True)


def is_safe(text: str) -> bool:
    """Quick boolean check."""
    return scan_content(text).safe


def check_file_size(filepath: str, content_to_add: str = "") -> ScanResult:
    """Check if a file is within its size budget."""
    path = Path(filepath)
    if not path.is_absolute():
        path = WORKSPACE / path

    rel_path = str(path.relative_to(WORKSPACE)) if str(path).startswith(str(WORKSPACE)) else str(path)

    budget = _SIZE_BUDGETS.get(rel_path, _DEFAULT_SIZE_BUDGET)

    current_size = 0
    if path.exists():
        try:
            current_size = len(path.read_text(encoding="utf-8"))
        except (OSError, IOError):
            pass

    projected = current_size + len(content_to_add)

    if projected > budget:
        pct = int((projected / budget) * 100)
        return ScanResult(
            safe=False,
            reason=f"File would exceed size budget: {projected:,}/{budget:,} chars ({pct}%)",
            pattern_id="size_budget_exceeded",
            details=f"File: {rel_path}, current: {current_size:,}, adding: {len(content_to_add):,}"
        )

    return ScanResult(safe=True)


def check_duplicate(filepath: str, new_entry: str, threshold: float = 0.70) -> ScanResult:
    """Check if a similar entry already exists in the file."""
    path = Path(filepath)
    if not path.is_absolute():
        path = WORKSPACE / path

    if not path.exists():
        return ScanResult(safe=True)

    try:
        existing = path.read_text(encoding="utf-8")
    except (OSError, IOError):
        return ScanResult(safe=True)

    new_normalized = _normalize_for_dedup(new_entry)
    if len(new_normalized) < 20:
        return ScanResult(safe=True)

    # Split existing content into blocks (by heading or horizontal rule)
    blocks = re.split(r'\n(?=## |---)', existing)

    for block in blocks:
        block_normalized = _normalize_for_dedup(block)
        if len(block_normalized) < 20:
            continue

        similarity = _jaccard_similarity(new_normalized, block_normalized)
        if similarity >= threshold:
            preview = block.strip()[:120].replace('\n', ' ')
            return ScanResult(
                safe=False,
                reason=f"Duplicate detected ({similarity:.0%} similar)",
                pattern_id="duplicate_entry",
                details=f"Similar to existing: '{preview}...'"
            )

    return ScanResult(safe=True)


def _normalize_for_dedup(text: str) -> str:
    """Normalize text for duplicate comparison."""
    text = text.lower().strip()
    text = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[*_`#\->\[\]()]', '', text)
    return text


def _jaccard_similarity(a: str, b: str) -> float:
    """Word-level Jaccard similarity."""
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def scan_all_memory_files() -> List[dict]:
    """Scan all memory and learnings files for issues."""
    issues = []

    scan_dirs = [
        WORKSPACE / "memory",
        WORKSPACE / ".learnings",
    ]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for md_file in scan_dir.rglob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
            except (OSError, IOError):
                continue

            rel_path = str(md_file.relative_to(WORKSPACE))

            # Content scan
            result = scan_content(content)
            if not result.safe:
                issues.append({
                    "file": rel_path,
                    "type": "content",
                    "severity": "high",
                    "reason": result.reason,
                    "pattern": result.pattern_id,
                    "details": result.details,
                })

            # Size check
            budget = _SIZE_BUDGETS.get(rel_path, _DEFAULT_SIZE_BUDGET)
            file_size = len(content)
            if file_size > budget:
                pct = int((file_size / budget) * 100)
                issues.append({
                    "file": rel_path,
                    "type": "size",
                    "severity": "medium",
                    "reason": f"Exceeds budget: {file_size:,}/{budget:,} chars ({pct}%)",
                })
            elif file_size > budget * 0.8:
                pct = int((file_size / budget) * 100)
                issues.append({
                    "file": rel_path,
                    "type": "size",
                    "severity": "low",
                    "reason": f"Approaching budget: {file_size:,}/{budget:,} chars ({pct}%)",
                })

    return issues


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    if sys.argv[1] == "--scan-all":
        issues = scan_all_memory_files()
        if not issues:
            print("✅ All memory files clean — no injection, exfil, or size issues found.")
            return
        print(f"⚠️  Found {len(issues)} issue(s):\n")
        for issue in issues:
            severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue["severity"], "⚪")
            print(f"  {severity_emoji} [{issue['type']}] {issue['file']}")
            print(f"     {issue['reason']}")
            if issue.get("details"):
                print(f"     {issue['details']}")
            print()
        return

    if sys.argv[1] == "--file":
        if len(sys.argv) < 3:
            print("Usage: memory_content_scanner.py --file <path>")
            return
        filepath = sys.argv[2]
        path = Path(filepath)
        if not path.exists():
            print(f"❌ File not found: {filepath}")
            return
        content = path.read_text(encoding="utf-8")
        result = scan_content(content)
        size_result = check_file_size(filepath)
        if result.safe and size_result.safe:
            print(f"✅ {filepath} — clean")
        else:
            if not result.safe:
                print(f"🔴 Content issue: {result.reason}")
                if result.details:
                    print(f"   {result.details}")
            if not size_result.safe:
                print(f"🟡 Size issue: {size_result.reason}")
        return

    # Direct text check
    text = " ".join(sys.argv[1:])
    result = scan_content(text)
    if result.safe:
        print("✅ Content is safe")
    else:
        print(f"🔴 Blocked: {result.reason}")
        if result.details:
            print(f"   {result.details}")
        sys.exit(1)


if __name__ == "__main__":
    main()
