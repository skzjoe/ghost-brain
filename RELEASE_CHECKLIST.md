# Release Checklist

Target release: `v1.2.0`
Date: 2026-04-13

## Release hygiene
- [x] Changelog updated
- [x] Starter installer version bumped
- [x] Release notes written
- [x] Starter docs refreshed
- [x] Public repo examples genericized
- [x] PII sweep completed

## Validation
- [x] `pytest -q tests` passes (`129 passed`)
- [x] Repo clean before tagging
- [x] Public ownership references reviewed and intentional

## Tagging
- [ ] Create/verify retroactive `v1.1.0` tag for the starter distribution milestone
- [ ] Create `v1.2.0` tag for current release
- [ ] Push tags to origin

## Post-release
- [ ] Confirm remote tags exist
- [ ] Optionally publish a GitHub release body from `RELEASE_NOTES_v1.2.0.md`
- [ ] Start P0 next-milestone work: guardrails, drift checks, targeted test coverage
