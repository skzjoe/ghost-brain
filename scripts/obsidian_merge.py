#!/usr/bin/env python3
"""
obsidian_merge.py — Shared section-aware merge for Obsidian vault files.

Part of Ghost Brain. Used by obsidian_push_daily.sh and obsidian_push_syntheses.sh.

Policy: MERGE, never overwrite. Protects against multi-agent data loss in shared vaults.

Safety layers:
  1. Size sanity check — abort if merged result < 85% of original (data-loss guard)
  2. Atomic write — temp file + os.replace() (no partial writes)
  3. Source attribution — marks appended content with agent marker

Usage (called by shell scripts):
    python3 scripts/obsidian_merge.py <src> <dest> [--min-ratio 0.85] [--source "*(Ghost)*"]

Exit codes:
    0  — merged successfully (or created new file)
    10 — aborted: merged result too small (data-loss guard)
    1  — unexpected error
"""
import sys, re, os, argparse


def split_sections(text):
    sections = []
    current_heading = None
    current_body = []
    for line in text.splitlines(keepends=True):
        if re.match(r'^#{1,3} ', line):
            if current_heading is not None or current_body:
                sections.append((current_heading, current_body))
            current_heading = line.rstrip('\n')
            current_body = []
        else:
            current_body.append(line)
    sections.append((current_heading, current_body))
    return sections


def heading_key(h):
    if h is None:
        return ""
    return re.sub(r'^#+\s*', '', h).lower().strip()


SOURCE_MARKER = "*(Ghost)*"


def merge_texts(src_text, dest_text, source: str = SOURCE_MARKER):
    """Merge src into dest: update matching sections, append new ones. Returns merged string."""
    src_sections = split_sections(src_text)
    dest_sections = split_sections(dest_text)

    dest_index = {heading_key(h): i for i, (h, _) in enumerate(dest_sections)}
    result = list(dest_sections)

    for (src_h, src_body) in src_sections:
        key = heading_key(src_h)
        src_body_text = ''.join(src_body).strip()
        if not src_body_text:
            continue

        if key in dest_index:
            idx = dest_index[key]
            dest_lines_set = set(l.strip() for l in result[idx][1] if l.strip())
            new_lines = [l for l in src_body if l.strip() and l.strip() not in dest_lines_set]
            if new_lines:
                existing = result[idx][1]
                if existing and existing[-1].strip():
                    existing.append('\n')
                if source:
                    existing.append(f'<!-- appended by {source} -->\n')
                existing.extend(new_lines)
                result[idx] = (result[idx][0], existing)
        else:
            if source and src_h is not None:
                marked_h = f"{src_h}  <!-- {source} -->"
                result.append((marked_h, src_body))
            else:
                result.append((src_h, src_body))
            dest_index[key] = len(result) - 1

    out = []
    for (h, body) in result:
        if h is not None:
            out.append(h + '\n')
        out.extend(body)
        joined = ''.join(body)
        if joined and not joined.endswith('\n\n'):
            out.append('\n' if joined.endswith('\n') else '\n\n')

    return ''.join(out)


def main():
    parser = argparse.ArgumentParser(description="Section-aware merge for Obsidian vault files")
    parser.add_argument('src', help="Source file to merge from")
    parser.add_argument('dest', help="Destination file to merge into")
    parser.add_argument('--min-ratio', type=float, default=0.85, help="Minimum size ratio (abort if below)")
    parser.add_argument('--source', default=SOURCE_MARKER, help="Source attribution marker")
    args = parser.parse_args()

    src_text = open(args.src).read()

    if not os.path.exists(args.dest):
        import shutil
        shutil.copy(args.src, args.dest)
        print(f"  Created: {args.dest}")
        return

    dest_text = open(args.dest).read()
    orig_bytes = len(dest_text.encode('utf-8'))

    merged = merge_texts(src_text, dest_text, source=args.source)
    merged_bytes = len(merged.encode('utf-8'))

    if orig_bytes > 0:
        ratio = merged_bytes / orig_bytes
        if ratio < args.min_ratio:
            print(f"  ❌ ABORT: {merged_bytes}B is {ratio:.0%} of original {orig_bytes}B (min {args.min_ratio:.0%})", file=sys.stderr)
            sys.exit(10)

    tmp = args.dest + '.tmp'
    with open(tmp, 'w') as f:
        f.write(merged)
    os.replace(tmp, args.dest)
    print(f"  Merged: {args.dest} ({orig_bytes}B → {merged_bytes}B)")


if __name__ == '__main__':
    main()
