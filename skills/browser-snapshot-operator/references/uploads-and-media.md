# Uploads and Media

Use this when the UI requires file selection, media libraries, or asset pickers.

## Procedure
1. Reach the upload surface in the UI first.
2. If browser uploads are required, ensure the file exists in `/tmp/openclaw/uploads`.
3. Use the browser upload flow only after the page is clearly ready for a file chooser.
4. Re-snapshot and verify the uploaded asset appears in the library/grid/list.
5. Select the uploaded asset explicitly before moving to the next step.

## Notes
- Some apps hide the real media editor behind a wizard.
- An upload may succeed technically but still not be selected for the current item.
