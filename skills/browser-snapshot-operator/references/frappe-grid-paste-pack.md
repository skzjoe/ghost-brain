# Frappe Grid Paste / Child-Table Tactics Pack

Use this when ERPNext/Frappe work involves child tables, inline grid cells, row dialogs, or paste-heavy entry.

## Core rule
Treat inline child-table editing as the least reliable path.
If a safer app-supported popup, bulk tool, or row dialog exists, prefer that first.

## Decision order
1. **Best:** use an app-supported paste/import dialog.
2. **Next best:** open the child-row dialog and fill stable fields there.
3. **Last resort:** edit inline grid cells one at a time.

## Why this matters
- Grid rows rerender frequently.
- Cell refs die as soon as focus changes.
- Link fields inside grids are especially brittle.
- Scroll position and row focus often break automation state.

## Recommended pattern for grids
1. Snapshot the form.
2. Identify the child table section.
3. Click the intended row.
4. Re-snapshot.
5. Decide whether a row dialog is available.
6. If yes, open the row dialog and work there.
7. If no, edit the minimum number of inline cells possible.
8. Re-snapshot after each row-level commit.

## Inline editing rules
- Do not try to fill many grid cells blindly in one batch.
- Re-snapshot after each meaningful cell/row change.
- Expect refs to die after Tab, Enter, or row changes.
- If a Link field behaves badly inline, stop and switch to dialog mode if possible.

## Paste-heavy workflows
When the user wants to paste many rows:
- Prefer a dedicated paste popup, import tool, or custom dialog if the app has one.
- If the app does not support this safely, say so explicitly instead of pretending the grid is robust.
- Browser automation should not brute-force dozens of fragile inline grid actions unless there is no safer path.

## Signals to stop and change strategy
- refs disappear after every keystroke
- grid rows virtualize or rerender unpredictably
- link/autocomplete fields do not expose stable refs
- save triggers full rerender and loses row context
- the task will require many repeated inline actions

## Safe reporting style
- **Grid state**: which child table / row you are in
- **Method chosen**: popup, row dialog, or inline edit
- **Why**: why that method is safest
- **Observed fragility**: stale refs, link field issues, rerender, scroll loss
- **Next move**: continue, switch strategy, or ask for a better tool path
