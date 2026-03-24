# Wizards and Step Flows

Use this when the app exposes progress states, status pills, or a multi-step editor.

## Procedure
1. Treat step/status buttons as the source of truth.
2. Complete one step at a time.
3. After each step, re-snapshot and confirm the status changed.
4. Move only when the current step is complete or intentionally skipped.

## Example states
- setup
- media
- crop
- text
- enhancements
- review

## Rule
If the main page looks incomplete, look for a hidden wizard before assuming fields are missing.
