---
name: excel-generator
description: Create general Excel workbooks (.xlsx) from structured data. Use when generating real Excel files for tables, CSV/JSON exports, project timelines, WBS sheets, task trackers, customer-facing business workbooks, or detailed ERP/PM implementation packs. Prefer the openpyxl-backed scripts for delivery-grade Excel files that must open reliably in Excel clients.
---

# Excel Generator

Create delivery-ready `.xlsx` files with deterministic local scripts.

## Use this skill for

- Convert CSV or JSON into Excel
- Generate a simple table workbook
- Create project timeline workbooks
- Create WBS sheets
- Create task tracker workbooks
- Generate customer-facing business project packs
- Produce simple multi-sheet planning artifacts without external spreadsheet libraries

## Quick workflow

1. Pick the closest bundled script.
2. Prepare input data as CSV or JSON if the default template is not enough.
3. Write output to `media/` unless the user requests another workspace path.
4. Send the `.xlsx` file back when needed.

## Bundled scripts

### 1) Generic table export

Use for plain tabular data from CSV or JSON.

```bash
skills/excel-generator/scripts/create_table_xlsx.py \
  --input data.csv \
  --output media/table.xlsx \
  --sheet-name "Data" \
  --title "Table Export"
```

### 2) Project timeline workbook

Use for implementation plans, phased rollouts, and schedule overviews.

```bash
skills/excel-generator/scripts/generate_project_timeline_xlsx.py \
  --output media/project_timeline.xlsx \
  --project-name "ERPNext" \
  --weeks 16
```

### 3) WBS workbook

Use for work breakdown structures.

```bash
skills/excel-generator/scripts/generate_wbs_xlsx.py \
  --output media/wbs.xlsx \
  --title "ERPNext WBS"
```

### 4) Task tracker workbook

Use for action lists, PM tracking, and follow-up sheets.

```bash
skills/excel-generator/scripts/generate_tracker_xlsx.py \
  --output media/tracker.xlsx \
  --title "Implementation Tracker"
```

### 5) Customer-facing business project pack

Use for cleaner stakeholder-ready workbooks with summary, branding, milestones, timeline, risks, and action tracker sheets. Branding can be toggled on/off, so this is safe for requests like “remove the logo”.

### 6) Real ERPNext PM implementation pack

Use for delivery-grade ERPNext planning files with a true PM structure: executive summary, scope, phase plan, milestones, timeline, critical path, RAID, decision log, detailed WBS, dependencies, deliverables, UAT, cutover, and hypercare.

Run this with the local `openpyxl` Python environment:

```bash
.venv_excel/bin/python skills/excel-generator/scripts/generate_erpnext_pm_real_pack.py \
  --pack-output media/erpnext_pm_pack.xlsx \
  --wbs-output media/erpnext_pm_wbs.xlsx \
  --project-name "ERPNext Implementation Plan" \
  --customer-name "Customer Name"
```

```bash
skills/excel-generator/scripts/generate_business_project_pack_xlsx.py \
  --output media/project_pack.xlsx \
  --project-name "ERPNext Implementation" \
  --customer-name "Customer Name" \
  --brand-name "ExampleCo" \
  --theme-color 385723 \
  --include-logo \
  --weeks 16
```

For a clean no-logo version:

```bash
skills/excel-generator/scripts/generate_business_project_pack_xlsx.py \
  --output media/project_pack_no_logo.xlsx \
  --project-name "ERPNext Implementation" \
  --customer-name "Customer Name" \
  --brand-name "ExampleCo" \
  --no-logo \
  --weeks 16
```

## Input schemas

If custom data is needed, read `references/input-schemas.md` and provide JSON in the expected row format.

## Guardrails

- Prefer simple, reliable workbook structure over fancy formatting.
- Use these scripts for deterministic exports, not for macros or complex formulas.
- If a new workbook pattern keeps recurring, add a new script rather than hacking one-off output every time.
- Keep sheet names under Excel's usual 31-character limit.
