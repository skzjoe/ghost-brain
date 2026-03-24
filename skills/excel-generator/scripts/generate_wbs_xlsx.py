#!/usr/bin/env python3
import argparse
import json
from excel_core import write_xlsx, infer_widths

DEFAULT_ROWS = [
    ['WBS Code', 'Work Package', 'Task', 'Owner', 'Start Week', 'End Week', 'Duration', 'Status', 'Deliverable', 'Notes'],
    ['1.0', 'Project Initiation', 'Kickoff', 'PM', 1, 1, 1, 'Planned', 'Kickoff minutes', ''],
    ['1.1', 'Project Initiation', 'Stakeholder alignment', 'PM', 1, 2, 2, 'Planned', 'Stakeholder list', ''],
    ['2.0', 'Analysis', 'Process workshops', 'Consultant', 2, 4, 3, 'Planned', 'Workshop notes', ''],
    ['3.0', 'Build', 'Configuration and customizations', 'Tech Lead', 5, 10, 6, 'Planned', 'Configured system', ''],
]


def main():
    p = argparse.ArgumentParser(description='Generate a WBS workbook')
    p.add_argument('--output', required=True)
    p.add_argument('--title', default='Work Breakdown Structure')
    p.add_argument('--rows-json')
    args = p.parse_args()

    rows = DEFAULT_ROWS
    if args.rows_json:
        with open(args.rows_json, 'r', encoding='utf-8') as f:
            rows = json.load(f)
    sheets = [
        {'name': 'WBS', 'rows': rows, 'widths': infer_widths(rows)},
        {'name': 'Summary', 'rows': [['Section', 'Owner', 'Status'], ['Project Initiation', '', ''], ['Analysis', '', ''], ['Build', '', ''], ['Go-Live', '', '']], 'widths': {1: 24, 2: 18, 3: 14}}
    ]
    write_xlsx(args.output, sheets, title=args.title)
    print(args.output)


if __name__ == '__main__':
    main()
