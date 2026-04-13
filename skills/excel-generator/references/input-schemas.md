# Input Schemas

Use these schemas when preparing JSON inputs for the bundled scripts.

## 1) Generic table export

Accepted inputs:
- Array of arrays
- Array of objects
- Object with `rows`

Examples:

```json
[
  {"Name": "Alice", "Role": "CTO", "Company": "Acme"},
  {"Name": "Taylor", "Role": "Ops", "Company": "ExampleCo"}
]
```

```json
{
  "rows": [
    ["Name", "Role", "Company"],
    ["Alice", "CTO", "Acme"],
    ["Taylor", "Ops", "ExampleCo"]
  ]
}
```

## 2) Timeline rows

Each row must follow this order:

```text
[
  phase_no,
  phase_name,
  task,
  detail,
  owner,
  deliverable,
  start_week,
  end_week,
  duration_weeks,
  dependency,
  status,
  notes
]
```

The first row should be the header row if you override the defaults.

## 3) WBS rows

```text
[
  wbs_code,
  work_package,
  task,
  owner,
  start_week,
  end_week,
  duration,
  status,
  deliverable,
  notes
]
```

The first row should be the header row.

## 4) Tracker rows

```text
[
  task_id,
  task,
  owner,
  priority,
  status,
  start_date,
  due_date,
  progress_percent,
  dependency,
  notes
]
```

The first row should be the header row.

## 5) Business project pack sheets

These optional JSON files are supported by `generate_business_project_pack_xlsx.py`.

Branding-related flags:
- `--brand-name`
- `--theme-color`
- `--include-logo`
- `--no-logo`
- `--logo-note`

Use `--no-logo` whenever the user asks to remove or hide the logo.

These optional JSON files are supported by `generate_business_project_pack_xlsx.py`: 

### milestones-json

```text
[
  ['Milestone', 'Owner', 'Target Week', 'Status', 'Notes'],
  ['Kickoff Complete', 'PM', 1, 'Planned', '']
]
```

### risks-json

```text
[
  ['Risk', 'Impact', 'Mitigation', 'Owner', 'Status'],
  ['Scope creep', 'High', 'Freeze must-have scope', 'PM', 'Open']
]
```

### actions-json

```text
[
  ['Action ID', 'Action', 'Owner', 'Due Week', 'Status', 'Notes'],
  ['A-001', 'Confirm scope', 'PM', 1, 'Open', '']
]
```
