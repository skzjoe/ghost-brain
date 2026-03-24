#!/usr/bin/env python3
import argparse
import json
from excel_core import write_xlsx, infer_widths

DEFAULT_ROWS = [
    ['Task ID', 'Task', 'Owner', 'Priority', 'Status', 'Start Date', 'Due Date', 'Progress %', 'Dependency', 'Notes'],
    ['T-001', 'Finalize scope', 'PM', 'High', 'In Progress', '', '', 60, '', ''],
    ['T-002', 'Prepare master data', 'Business Owner', 'High', 'Not Started', '', '', 0, 'T-001', ''],
    ['T-003', 'Configure workflows', 'Consultant', 'Medium', 'Not Started', '', '', 0, 'T-001', ''],
]


def main():
    p = argparse.ArgumentParser(description='Generate a generic task tracker workbook')
    p.add_argument('--output', required=True)
    p.add_argument('--title', default='Task Tracker')
    p.add_argument('--rows-json')
    args = p.parse_args()

    rows = DEFAULT_ROWS
    if args.rows_json:
        with open(args.rows_json, 'r', encoding='utf-8') as f:
            rows = json.load(f)
    sheets = [
        {'name': 'Tracker', 'rows': rows, 'widths': infer_widths(rows)},
        {'name': 'Summary', 'rows': [['Metric', 'Value'], ['Open Tasks', ''], ['In Progress', ''], ['Done', ''], ['Blocked', '']], 'widths': {1: 20, 2: 20}}
    ]
    write_xlsx(args.output, sheets, title=args.title)
    print(args.output)


if __name__ == '__main__':
    main()
