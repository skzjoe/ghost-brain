# Release Checklist

Target release: `v1.3.0`
Date: 2026-04-13

## Release hygiene
- [x] Changelog updated
- [x] Starter installer version bumped
- [x] Release notes written
- [x] Starter docs refreshed or confirmed current
- [x] Public repo examples genericized
- [x] PII sweep completed

## Validation
- [x] `pytest -q tests` passes (`177 passed`)
- [x] `bash -n install.sh` passes
- [x] `bash -n starter/install.sh` passes
- [x] `bash -n test.sh` passes
- [x] Repo clean before tagging
- [x] Public ownership references reviewed and intentional

## Tagging
- [x] Create `v1.3.0` tag for current release
- [x] Push tag to origin

## Post-release
- [x] Confirm remote tag exists
- [x] Publish a GitHub release body from `RELEASE_NOTES_v1.3.0.md`
- [x] Main now reflects the tagged public state
