# Scroll and Hidden Panels

Use this when snapshot output does not expose controls that should exist.

## Procedure
1. Re-snapshot with more depth first.
2. Identify whether the page uses a nested scroll container.
3. Use `evaluate` only to move that container.
4. Snapshot again immediately after scrolling.
5. Return to ref-first control once the hidden controls appear.

## Warning
Do not keep operating blind after an evaluate scroll. Always re-snapshot.
