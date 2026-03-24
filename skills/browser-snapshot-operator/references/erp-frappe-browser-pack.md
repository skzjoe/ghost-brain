# ERP/Frappe Browser Pack

Use this when browsing ERPNext/Frappe desk pages, forms, reports, list views, or child tables.

## What is special about Frappe UI
- Many actions live in menus, drawers, or small icon buttons.
- Child tables/grid rows are often dynamic and refs go stale quickly.
- Dialogs and quick-entry forms may open on top of the desk without obvious route changes.
- Some controls only appear after focusing a row, opening a menu, or switching a tab/section.

## Recommended operating pattern
1. Snapshot the page before touching anything.
2. Identify whether you are in:
   - list view
   - form view
   - report view
   - dialog / quick entry
   - child table/grid editor
3. Use one small action at a time.
4. Re-snapshot after row focus changes, menu opens, quick-entry dialogs, save actions, and tab switches.

## Lists and reports
- Prefer clicking row refs directly instead of guessing record links.
- If filters/search exist, snapshot again after each change because result rows often rerender.
- In report-style pages, verify whether the visible table is static or virtualized before trying to read deep rows.

## Form view
- Expect sections to be collapsible.
- Fields may be hidden until a section is expanded.
- Save/Submit/Amend actions may move between primary buttons and menus depending on docstatus.
- Re-snapshot after Save or Submit; the page often rerenders and old refs die.

## Child tables / grid editors
- Treat grid interactions as fragile.
- Click the row first, then re-snapshot before editing cells.
- If inline grid editing does not expose stable refs, open the row dialog if possible.
- For paste-heavy workflows, prefer app-supported dialogs/popups over trying to fill many inline grid refs blindly.

## Menus and action dots
- Frappe frequently hides important actions inside dropdowns or kebab menus.
- Click the menu, then re-snapshot immediately.
- Do not assume the menu opened correctly without a new snapshot.

## Quick entry / dialogs
- Quick entry forms often look like the page did not change, but a modal opened.
- Re-snapshot after create/new actions.
- Work only inside the dialog layer until it is saved or closed.

## Recovery rules
- If the desk looks unchanged after a click, re-snapshot before retrying.
- If a child-table ref disappears, assume rerender and snapshot again.
- If a field is visibly on screen but no ref appears, try expanding the section or focusing the row first.
- Use `evaluate` only for last-mile scrolling inside long forms or hidden desk panels.

## Safe output style for ERP/Frappe browsing
- **State**: list / form / report / dialog / grid
- **Doc / view**: what doctype or record you are on
- **Action taken**: what was clicked/edited
- **Observed result**: what changed
- **Risk / blocker**: hidden field, stale grid refs, permission issue, unsaved changes
- **Next move**: the safest next step
