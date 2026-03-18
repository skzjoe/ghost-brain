# Examples

Concrete examples of how to use Ghost Brain artifacts and templates.

## Coding workflow example

See:
- `examples/coding-workflow-example.md`

This example shows how to apply the brownfield coding workflow to a non-trivial bug fix using:
- research,
- plan,
- implementation,
- compaction handoff.

## Learning entry example

```markdown
## [LRN-20250115-001] correction

**Logged**: 2025-01-15T10:30:00Z
**Priority**: high
**Status**: pending
**Area**: tests

### Summary
Incorrectly assumed pytest fixtures are scoped to function by default

### Details
When writing test fixtures, I assumed all fixtures were function-scoped. 
User corrected that while function scope is the default, the codebase 
convention uses module-scoped fixtures for database connections to 
improve test performance.

### Suggested Action
When creating fixtures that involve expensive setup (DB, network), 
check existing fixtures for scope patterns before defaulting to function scope.

### Metadata
- Source: user_feedback
- Related Files: tests/conftest.py
- Tags: pytest, testing, fixtures

---
```

## Error entry example

```markdown
## [ERR-20250115-A3F] docker_build

**Logged**: 2025-01-15T09:15:00Z
**Priority**: high
**Status**: pending
**Area**: infra

### Summary
Docker build fails on M1 Mac due to platform mismatch

### Error
```
error: failed to solve: python:3.11-slim: no match for platform linux/arm64
```

### Context
- Command: `docker build -t myapp .`
- Dockerfile uses `FROM python:3.11-slim`
- Running on Apple Silicon (M1/M2)

### Suggested Fix
Add platform flag: `docker build --platform linux/amd64 -t myapp .`
Or update Dockerfile: `FROM --platform=linux/amd64 python:3.11-slim`

### Metadata
- Reproducible: yes
- Related Files: Dockerfile

---
```

## Feature request example

```markdown
## [FEAT-20250115-001] export_to_csv

**Logged**: 2025-01-15T16:45:00Z
**Priority**: medium
**Status**: pending
**Area**: backend

### Requested Capability
Export analysis results to CSV format

### User Context
User runs weekly reports and needs to share results with non-technical 
stakeholders in Excel. Currently copies output manually.

### Complexity Estimate
simple

### Suggested Implementation
Add `--output csv` flag to the analyze command. Use standard csv module.
Could extend existing `--output json` pattern.

### Metadata
- Frequency: recurring
- Related Features: analyze command, json output

---
```
