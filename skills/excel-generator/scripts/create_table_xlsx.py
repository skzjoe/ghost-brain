#!/usr/bin/env python3
import argparse
import csv
import json
import os
import sys
from excel_core import write_xlsx, infer_widths


def load_rows(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and 'rows' in data:
            return data['rows']
        return data
    if ext == '.csv':
        with open(path, 'r', encoding='utf-8-sig', newline='') as f:
            return list(csv.reader(f))
    raise SystemExit('Unsupported input. Use .json or .csv')


def normalize(rows):
    if not rows:
        return [['No data']]
    if isinstance(rows[0], dict):
        headers = list(rows[0].keys())
        body = [[r.get(h, '') for h in headers] for r in rows]
        return [headers] + body
    return rows


def main():
    p = argparse.ArgumentParser(description='Create a simple Excel workbook from CSV or JSON data')
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--sheet-name', default='Sheet1')
    p.add_argument('--title', default='Table Export')
    args = p.parse_args()

    rows = normalize(load_rows(args.input))
    write_xlsx(args.output, [{'name': args.sheet_name, 'rows': rows, 'widths': infer_widths(rows)}], title=args.title)
    print(args.output)


if __name__ == '__main__':
    main()
