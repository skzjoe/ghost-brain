---
name: browser-snapshot-operator
description: Navigate websites and web apps using browser snapshots with element refs (for example `e123`) instead of brittle selectors. Use when controlling the OpenClaw browser for page inspection, step-by-step UI automation, debugging web flows, or explaining how to browse a site safely and repeatably by snapshotting the page, reading refs, and acting on those refs.
---

# Browser Snapshot Operator

Use browser snapshots as the default way to inspect and drive a web UI.

## Core workflow

1. **Open or focus the target page** with the `browser` tool.
2. **Take a snapshot** with `interactive:true` and `refs:"aria"` when stable refs matter.
3. **Read the page state** from the snapshot output.
   - Refs look like `e123`.
   - These refs identify buttons, links, tabs, inputs, and other interactive elements.
4. **Act using refs first** (`click`, `fill`, `press`, `select`) instead of ad-hoc selectors.
5. **Re-snapshot after major transitions** so refs stay current.
6. **Stop and report blockers** when login prompts, permission gates, modals, missing fields, or unexpected routes appear.

## Why use snapshot refs

Prefer snapshot refs because they are usually more reliable than text selectors in modern SPAs.

Use refs when:
- the page is dynamic
- labels repeat
- the UI changes after each action
- the flow is multi-step and stateful
- you need to explain the page structure back to the user

Avoid relying on raw screenshots alone. Screenshots help visually, but snapshots expose the actual interactive structure.

## Default browser pattern

### Inspect a page
- Open page
- Snapshot with refs
- Summarize key interactive elements
- Identify the next safest action

### Drive a page
- Click by ref
- Re-snapshot
- Fill/type/select by ref
- Re-snapshot after page transitions
- Continue until the task reaches a stable checkpoint

### Debug a page
- Snapshot the visible state
- Compare expected vs actual elements
- Identify missing controls, disabled buttons, auth walls, or hidden steps
- Use evaluate only when normal refs are insufficient

## Ref-first operating rules

- Prefer `snapshot` + `act` over guessing selectors.
- Prefer `refs:"aria"` for stability across calls.
- Use the same `targetId` while staying on the same tab.
- Re-snapshot after clicks that open dialogs, tabs, menus, editors, or route changes.
- If a ref disappears, do not reuse it blindly; snapshot again.
- Use selectors only when refs are unavailable or the UI is not exposed properly.
- Use `evaluate` sparingly for scrolls, hidden panels, or last-mile DOM inspection.

## Recovery ladder

When the UI does not behave as expected, escalate in this order:
1. Re-snapshot the current tab.
2. Increase snapshot depth or switch to `refs:"aria"`.
3. Confirm the same `targetId` is still in use.
4. Re-focus the tab and retry one action.
5. Use a narrow selector fallback only if refs are missing.
6. Use `evaluate` for nested scrolls, hidden panels, or DOM-only fields.
7. Reload or re-open the page only when state is clearly broken.
8. Stop and report the blocker if the state is still unclear.

## Recipes

Read the matching reference file when the page pattern is obvious:
- `references/modals-and-drawers.md` for popups, side panels, and layered dialogs
- `references/dropdowns-and-comboboxes.md` for searchable dropdowns and complex pickers
- `references/uploads-and-media.md` for file uploads and media-library flows
- `references/scroll-and-hidden-panels.md` for nested scrolling and non-visible editors
- `references/wizards-and-step-flows.md` for step-based flows with progress/status pills
- `references/erp-frappe-browser-pack.md` for ERPNext/Frappe desk, forms, reports, and child-table/grid behavior
- `references/frappe-grid-paste-pack.md` for paste-heavy child-table work, row dialogs, and fragile inline grid editing
- `references/final-review-publish-checklist.md` for high-impact actions, review gates, and publish/submit safety checks
- `references/browser-debug-pack.md` for debugging stale refs, hidden steps, rerenders, and UI mismatches

## Practical interpretation guide

When a snapshot shows lines like:
- `button "Create" [ref=e975]`
- `tab "Campaigns" [ref=e95]`
- `textbox "URL parameters" [ref=e8471]`

Treat this as a machine-readable UI map:
- the role tells you what kind of element it is
- the accessible name tells you what the user sees
- the ref is the handle to act on

## Good output style

When reporting back to the user during browsing work, keep it concise:
- **State**: where you are now
- **Found**: the important buttons/fields/tabs
- **Blocker**: what prevents the next step, if any
- **Next action**: the best move

## Common pitfalls

- Snapshot too shallow and miss important controls
- Reuse stale refs after the page changes
- Depend on text selectors when multiple similar controls exist
- Forget to keep the same `targetId`
- Assume a modal or side panel opened correctly without re-snapshotting

## When to use evaluate

Use `evaluate` only when needed for:
- scrolling inside nested panels
- reading placeholder-heavy DOM that snapshot does not expose well
- setting values in hard-to-reach inputs as a fallback
- diagnosing why expected fields are not rendering

After `evaluate`, snapshot again if you will continue normal UI operations.

## Resource

Read `references/ref-patterns.md` when you want compact examples of the main patterns: inspect, click, fill, re-snapshot, and fallback-to-evaluate.

For harder UI patterns, read the matching recipe file:
- `references/modals-and-drawers.md`
- `references/dropdowns-and-comboboxes.md`
- `references/uploads-and-media.md`
- `references/scroll-and-hidden-panels.md`
- `references/wizards-and-step-flows.md`
- `references/erp-frappe-browser-pack.md`
- `references/frappe-grid-paste-pack.md`
- `references/output-contract.md`
