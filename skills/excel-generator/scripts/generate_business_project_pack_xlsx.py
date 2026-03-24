#!/usr/bin/env python3
import argparse
import json
from excel_core import write_xlsx, infer_widths

DEFAULT_MILESTONES = [
    ['Milestone', 'Owner', 'Target Week', 'Status', 'Notes'],
    ['Kickoff Complete', 'PM', 1, 'Planned', ''],
    ['Requirements Signed Off', 'Consultant + Customer', 4, 'Planned', ''],
    ['Build Complete', 'Tech Lead', 10, 'Planned', ''],
    ['UAT Complete', 'Key Users', 12, 'Planned', ''],
    ['Go-Live', 'Project Team', 13, 'Planned', ''],
]

DEFAULT_RISKS = [
    ['Risk', 'Impact', 'Mitigation', 'Owner', 'Status'],
    ['Scope creep', 'High', 'Freeze must-have scope and defer extras to phase 2', 'PM', 'Open'],
    ['Dirty master data', 'High', 'Run cleansing and migration dry runs early', 'Business Owner', 'Open'],
    ['Slow decisions', 'Medium', 'Assign decision owners and escalation path', 'Sponsor', 'Open'],
    ['Weak UAT participation', 'High', 'Use named key users and scenario-based UAT', 'Customer PM', 'Open'],
]

DEFAULT_ACTIONS = [
    ['Action ID', 'Action', 'Owner', 'Due Week', 'Status', 'Notes'],
    ['A-001', 'Confirm scope and module list', 'PM', 1, 'Open', ''],
    ['A-002', 'Finalize workshop schedule', 'Customer PM', 2, 'Open', ''],
    ['A-003', 'Prepare master data owners', 'Business Owner', 3, 'Open', ''],
]


def branding_rows(project_name, customer_name, brand_name, include_logo, logo_note, theme_color):
    logo_status = 'Included' if include_logo else 'Removed / hidden'
    rows = [
        ['Branding Field', 'Value'],
        ['Brand Name', brand_name],
        ['Project Name', project_name],
        ['Customer Name', customer_name],
        ['Theme Color', theme_color],
        ['Logo Status', logo_status],
    ]
    if logo_note:
        rows.append(['Logo Note', logo_note])
    return rows


def summary_rows(project_name, customer_name, duration_weeks, brand_name, include_logo):
    return [
        ['Field', 'Value'],
        ['Brand', brand_name],
        ['Project', project_name],
        ['Customer', customer_name],
        ['Recommended Duration', f'{duration_weeks} weeks'],
        ['Delivery Mode', 'Phased implementation'],
        ['Primary Goal', 'Structured ERPNext rollout with clear milestones and controlled scope'],
        ['Suggested Modules', 'Sales, Purchase, Inventory, Accounting, Manufacturing'],
        ['Success Factors', 'Scope clarity, clean data, active key users, real UAT, disciplined cutover'],
        ['Branding Mode', 'With logo' if include_logo else 'No logo'],
    ]


def timeline_rows(duration_weeks):
    headers = ['Workstream'] + [f'W{i}' for i in range(1, duration_weeks + 1)]
    data = [headers]
    phases = [
        ('Discovery & Kickoff', 1, 2),
        ('Fit-Gap & Design', 2, 5),
        ('Configuration', 5, 8),
        ('Customization', 6, 10),
        ('Migration', 6, 10),
        ('Testing & Training', 10, 12),
        ('Cutover & Go-Live', 12, 13),
        ('Stabilization', 13, duration_weeks),
    ]
    for name, start, end in phases:
        marks = ['■' if start <= w <= end else '' for w in range(1, duration_weeks + 1)]
        data.append([name] + marks)
    return data


def load_json_or_default(path, default_rows):
    if not path:
        return default_rows
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_color(color: str) -> str:
    value = color.strip().lstrip('#').upper()
    if len(value) == 6:
        return 'FF' + value
    if len(value) == 8:
        return value
    raise SystemExit('theme-color must be RRGGBB or AARRGGBB')


def main():
    p = argparse.ArgumentParser(description='Generate a customer-facing business project workbook')
    p.add_argument('--output', required=True)
    p.add_argument('--project-name', default='ERPNext Implementation')
    p.add_argument('--customer-name', default='Customer')
    p.add_argument('--brand-name', default='1stCraft')
    p.add_argument('--weeks', type=int, default=16)
    p.add_argument('--theme-color', default='385723', help='Hex color, e.g. 385723 or FF385723')
    p.add_argument('--include-logo', action='store_true', default=False)
    p.add_argument('--no-logo', action='store_true', default=False)
    p.add_argument('--logo-note', default='')
    p.add_argument('--milestones-json')
    p.add_argument('--risks-json')
    p.add_argument('--actions-json')
    args = p.parse_args()

    include_logo = args.include_logo and not args.no_logo
    theme_color = normalize_color(args.theme_color)

    summary = summary_rows(args.project_name, args.customer_name, args.weeks, args.brand_name, include_logo)
    branding = branding_rows(args.project_name, args.customer_name, args.brand_name, include_logo, args.logo_note, theme_color)
    milestones = load_json_or_default(args.milestones_json, DEFAULT_MILESTONES)
    risks = load_json_or_default(args.risks_json, DEFAULT_RISKS)
    actions = load_json_or_default(args.actions_json, DEFAULT_ACTIONS)
    timeline = timeline_rows(args.weeks)

    sheets = [
        {'name': 'Executive Summary', 'rows': summary, 'widths': {1: 24, 2: 100}},
        {'name': 'Branding', 'rows': branding, 'widths': {1: 22, 2: 90}},
        {'name': 'Milestones', 'rows': milestones, 'widths': infer_widths(milestones)},
        {'name': 'Timeline', 'rows': timeline, 'widths': infer_widths(timeline, max_width=20)},
        {'name': 'Risks', 'rows': risks, 'widths': infer_widths(risks)},
        {'name': 'Action Tracker', 'rows': actions, 'widths': infer_widths(actions)},
    ]
    write_xlsx(args.output, sheets, title=args.project_name, header_fill=theme_color)
    print(args.output)


if __name__ == '__main__':
    main()
