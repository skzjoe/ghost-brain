#!/usr/bin/env python3
import argparse
import json
from excel_core import write_xlsx, infer_widths

DEFAULT_ROWS = [
    ['Phase No.', 'Phase / Workstream', 'Task', 'Detail', 'Owner', 'Deliverable', 'Start Week', 'End Week', 'Duration (Weeks)', 'Dependency', 'Status', 'Notes'],
    [0, 'Pre-Sales / Discovery', 'Initial discovery meeting', 'Collect business goals, pain points, high-level scope, expected modules, timeline expectations', 'Implementer + Customer Sponsor', 'Discovery note / requirement summary', 1, 1, 1, '-', 'Planned', 'Use to align scope before kickoff'],
    [1, 'Project Kickoff & Planning', 'Kickoff meeting', 'Confirm stakeholders, governance, communication plan, target go-live window', 'Implementer PM + Customer PM', 'Kickoff minutes / project charter', 1, 1, 1, 'Discovery', 'Planned', 'Assign project owners from both sides'],
    [1, 'Project Kickoff & Planning', 'Project plan setup', 'Define milestones, decision owners, meeting cadence, RAID log', 'Implementer PM', 'Project plan / timeline', 1, 2, 2, 'Kickoff', 'Planned', 'Lock must-have vs nice-to-have early'],
    [2, 'Business Process Mapping / Fit-Gap', 'Department workshops', 'Run workshops for Sales, Purchase, Inventory, Accounting, Manufacturing, HR or other modules in scope', 'Functional Consultant + Key Users', 'Workshop notes', 2, 3, 2, 'Kickoff', 'Planned', 'Map current-state and future-state'],
    [2, 'Business Process Mapping / Fit-Gap', 'Fit-gap analysis', 'Map ERPNext standard capabilities vs gaps requiring custom process or development', 'Functional Consultant', 'Fit-gap matrix', 3, 4, 2, 'Department workshops', 'Planned', 'Critical scope control step'],
    [2, 'Business Process Mapping / Fit-Gap', 'Master data design', 'Define item code rules, COA, warehouses, UOM, customer/supplier groups, naming rules', 'Functional Consultant + Customer Data Owner', 'Master data design', 3, 4, 2, 'Department workshops', 'Planned', 'Heavily affects migration speed'],
    [3, 'Solution Design', 'Solution blueprint', 'Design target business flow, approvals, roles, reports, print formats, tax/accounting flow', 'Solution Architect', 'Solution blueprint', 4, 5, 2, 'Fit-gap analysis', 'Planned', 'Needs customer sign-off'],
    [3, 'Solution Design', 'Customization specification', 'Document custom fields, scripts, reports, integrations, workflows, automation', 'Solution Architect + Technical Lead', 'Customization spec', 4, 5, 2, 'Fit-gap analysis', 'Planned', 'Freeze change requests where possible'],
    [4, 'Environment Setup', 'Environment provisioning', 'Prepare DEV/UAT/PROD, domain, SSL, backups, email settings, access policy', 'Technical Lead / DevOps', 'Ready environments', 5, 6, 2, 'Solution blueprint', 'Planned', 'Separate UAT and PROD if possible'],
    [5, 'Configuration', 'Core ERPNext setup', 'Configure company, fiscal year, taxes, warehouses, permissions, workflows, numbering series', 'Functional Consultant', 'Configured base system', 6, 8, 3, 'Environment provisioning', 'Planned', 'Document all key settings'],
    [5, 'Configuration', 'Print format / notifications', 'Set print formats, alerts, approval notifications, dashboards', 'Functional Consultant', 'Configured operational templates', 7, 8, 2, 'Core ERPNext setup', 'Planned', 'Keep outputs simple'],
    [6, 'Customization / Development', 'Custom development build', 'Implement approved custom fields, scripts, reports, integrations, validations', 'Technical Lead + Developers', 'Custom features in UAT', 6, 10, 5, 'Customization specification', 'Planned', 'Avoid unnecessary custom logic'],
    [6, 'Customization / Development', 'Internal testing', 'Developer and consultant testing of custom logic and critical flows', 'Technical Team', 'Internal test log', 9, 10, 2, 'Custom development build', 'Planned', 'Catch major bugs before UAT'],
    [7, 'Data Preparation & Migration', 'Data template preparation', 'Prepare import templates for customers, suppliers, items, BOMs, stock, AR/AP, COA', 'Data Consultant', 'Import templates', 5, 6, 2, 'Master data design', 'Planned', 'Start early'],
    [7, 'Data Preparation & Migration', 'Data cleansing and mapping', 'Clean duplicates, standardize codes, map old fields to ERPNext', 'Customer Data Owner + Data Consultant', 'Clean data files', 6, 9, 4, 'Data template preparation', 'Planned', 'Usually the biggest hidden delay'],
    [7, 'Data Preparation & Migration', 'Migration dry run', 'Trial import to UAT and validate balances, stock, masters, open docs', 'Data Consultant + Key Users', 'Migration validation report', 9, 10, 2, 'Data cleansing and mapping', 'Planned', 'Do at least one full dry run'],
    [8, 'Testing (SIT / UAT)', 'SIT', 'End-to-end functional/system integration test by implementation team', 'Implementer Team', 'SIT log / issue list', 10, 11, 2, 'Core ERPNext setup; Custom development build; Migration dry run', 'Planned', 'Use realistic scenarios'],
    [8, 'Testing (SIT / UAT)', 'UAT', 'Business users validate real scenarios, permissions, outputs, and exceptions', 'Key Users + Customer PM', 'UAT sign-off', 11, 12, 2, 'SIT', 'Planned', 'UAT must not be only demo/training'],
    [9, 'Training & Change Management', 'Key user training', 'Train process owners and super users by module', 'Functional Consultant', 'Training attendance / materials', 11, 12, 2, 'Configured base system', 'Planned', 'Train key users before end users'],
    [9, 'Training & Change Management', 'End user training', 'Role-based training with SOP or quick reference guide', 'Functional Consultant + Key Users', 'End-user readiness', 12, 12, 1, 'Key user training', 'Planned', 'Tie training to real transactions'],
    [10, 'Cutover Planning', 'Cutover checklist', 'Finalize migration steps, freeze timing, owners, validation points, rollback plan', 'Implementer PM + Customer PM', 'Cutover plan', 12, 13, 2, 'UAT', 'Planned', 'No go-live without checklist'],
    [10, 'Cutover Planning', 'Final migration rehearsal', 'Rehearse final load and validation steps with actual sequence', 'Data Consultant + PM', 'Rehearsal result', 12, 13, 2, 'Migration dry run', 'Planned', 'Reduce cutover surprises'],
    [11, 'Go-Live', 'Production cutover and launch', 'Final data load, access confirmation, opening balances, first live transactions', 'Full Project Team', 'Go-live confirmation', 13, 13, 1, 'Cutover checklist; Final migration rehearsal', 'Planned', 'Support team should be on standby'],
    [11, 'Go-Live', 'Hypercare support', 'Rapid issue triage, fix urgent errors, support users during first live operations', 'Implementer + Key Users', 'Hypercare issue log', 13, 14, 2, 'Production cutover and launch', 'Planned', 'Track top recurring issues'],
    [12, 'Post-Go-Live Stabilization', 'Stabilization and optimization', 'Fine-tune permissions, reports, workflows, dashboards, and backlog items', 'Support Lead + Customer Owner', 'Stabilization report / phase 2 backlog', 14, 16, 3, 'Go-Live', 'Planned', 'Good point to prioritize phase 2']
]


def timeline_rows(rows, total_weeks):
    headers = ['Phase / Task', 'Owner', 'Start Week', 'End Week'] + [f'W{w}' for w in range(1, total_weeks + 1)]
    out = [headers]
    for row in rows[1:]:
        start = int(row[6])
        end = int(row[7])
        marks = ['■' if start <= w <= end else '' for w in range(1, total_weeks + 1)]
        out.append([f'{row[1]} - {row[2]}', row[4], start, end] + marks)
    return out


def summary_rows(project_name, total_weeks):
    return [
        ['Metric', 'Value'],
        ['Project', project_name],
        ['Recommended duration', f'{total_weeks} weeks'],
        ['Typical scope', 'Sales, Purchase, Inventory, Accounting, Manufacturing'],
        ['Key success factors', 'Clear scope, clean data, controlled customization, real UAT, disciplined cutover'],
        ['Major risks', 'Scope creep, dirty data, slow decisions, weak UAT, over-customization']
    ]


def main():
    p = argparse.ArgumentParser(description='Generate a project timeline workbook')
    p.add_argument('--output', required=True)
    p.add_argument('--project-name', default='ERPNext')
    p.add_argument('--weeks', type=int, default=16)
    p.add_argument('--rows-json')
    args = p.parse_args()

    rows = DEFAULT_ROWS
    if args.rows_json:
        with open(args.rows_json, 'r', encoding='utf-8') as f:
            rows = json.load(f)
    sheets = [
        {'name': f'{args.project_name} Timeline'[:31], 'rows': rows, 'widths': infer_widths(rows)},
        {'name': 'Timeline View', 'rows': timeline_rows(rows, args.weeks), 'widths': infer_widths(timeline_rows(rows, args.weeks), max_width=48)},
        {'name': 'Summary', 'rows': summary_rows(args.project_name, args.weeks), 'widths': {1: 24, 2: 100}}
    ]
    write_xlsx(args.output, sheets, title=f'{args.project_name} Implementation Timeline')
    print(args.output)


if __name__ == '__main__':
    main()
