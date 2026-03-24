# Browser Debug Pack

Use this when the page is loaded but the UI does not behave as expected.

## Common failure modes
- click appears to do nothing
- refs vanish after each action
- expected fields do not render
- selector works once then fails
- hidden/nested scroll containers block progress
- a dialog opened but snapshot still looks similar
- the page rerendered and old refs became stale

## Debug sequence
1. Re-snapshot immediately.
2. Confirm you are still on the same `targetId` and tab.
3. Compare expected state vs visible state.
4. Increase snapshot depth if controls may be nested.
5. Look for hidden wizard steps, drawers, menus, or overlays.
6. Test one minimal interaction only.
7. Use `evaluate` only for DOM inspection, nested scroll, or last-mile field discovery.
8. If state remains inconsistent, reload/re-open and report the blocker.

## What to inspect
- disabled buttons
- status pills / progress steps
- hidden tabs or collapsed sections
- placeholder-only fields
- nested panels with their own scrollbars
- auth / permission banners
- confirmation dialogs behind the main page

## Good debug output
- **Expected**: what should have been visible or happened
- **Observed**: what the UI actually did
- **Likely cause**: stale refs, hidden panel, rerender, auth gate, layout change
- **Next test**: the smallest useful check
