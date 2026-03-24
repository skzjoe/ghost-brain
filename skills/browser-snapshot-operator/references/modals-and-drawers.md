# Modals and Drawers

Use this pattern when clicks open overlays, slide-outs, or layered dialogs.

## Procedure
1. Click the triggering ref.
2. Snapshot again immediately.
3. Confirm the modal/drawer exists before typing.
4. Act only inside the new visible layer.
5. If the background page still appears unchanged, do not assume failure until after a re-snapshot.

## Pitfalls
- Typing into the background page instead of the modal
- Reusing refs from before the overlay opened
- Missing a second-step dialog after the first confirmation
