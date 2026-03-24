# Ref Patterns

## 1) Inspect a page
- Open page
- Snapshot with `interactive:true`, `refs:"aria"`
- Read refs and roles
- Summarize important controls before acting

## 2) Click a control
- Find the element ref in the snapshot
- Use `act` with `kind:"click"` and that ref
- Snapshot again

## 3) Fill a field
- Snapshot until the textbox/combobox ref is visible
- Use `fill` or `type` on that ref
- Snapshot again if the UI reacts dynamically

## 4) Multi-step flows
For wizards and web apps:
1. snapshot
2. act on one control
3. snapshot
4. verify the state changed as expected
5. continue

## 5) Fallback when refs are not enough
Use `evaluate` for:
- nested scrolling containers
- hidden DOM state
- hard-to-reach inputs with visible placeholders but missing snapshot refs

Then return to normal `snapshot` + `ref` control.

## 6) What to tell the user
Use a compact status update:
- where you are
- what is visible
- what you changed
- what is blocked
- what the next step is
