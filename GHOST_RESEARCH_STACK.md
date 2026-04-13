# Ghost Research Stack

Status: active
Owner: user
Date: 2026-04-13

## Purpose

Lightweight, Ghost-native research infrastructure for measuring quality, safety, continuity, and regression without building a full RL training stack.

## Implemented Phases

### Phase 1
- **GhostLite eval suite**
  - Fast regression checks for capture routing, memory safety, model routing, error classification, and session-context extraction.
- **Safety benchmark**
  - Focused tests for prompt injection, exfiltration, invisible unicode, duplicate prevention, and file-size budgets.
- **Trajectory / outcome logging**
  - Task-level events and manual outcomes stored under `.local/research/events.jsonl`.
- **Regression runner**
  - Save baselines and compare latest or fresh runs against those baselines.

### Phase 2
- **Long-horizon continuity benchmark**
  - Multi-step scenarios that simulate Ghost continuity across capture, recall, duplicate protection, and context synthesis.
- **Usage / experiment dashboard**
  - Summaries of suite runs, pass rates, top failing tasks, manual outcomes, and observed model usage.
- **Second-brain focus report**
  - Actionable recommendations that convert eval drift into concrete memory and continuity improvements.
- **Production hardening**
  - Atomic writes, locked JSONL appends, baseline validation, manifest drift warnings, and graceful telemetry degradation.

## Files

### Shared runtime
- `scripts/ghost_research_lib.py`
- `scripts/ghost_research.py` (compatibility umbrella)

### Split production surfaces
- `scripts/ghost_eval.py`
- `scripts/ghost_regression.py`
- `scripts/ghost_safety_benchmark.py`
- `scripts/ghost_trajectory_log.py`
- `scripts/ghost_continuity_benchmark.py`
- `scripts/ghost_dashboard.py`
- `scripts/ghost_experiments.py`
- `scripts/ghost_usage_insights.py`

### Core contracts/adapters
- `scripts/ghost_core/contracts.py`
- `scripts/ghost_core/adapters/eval.py`
- `scripts/ghost_core/adapters/regression.py`
- `scripts/ghost_core/adapters/safety.py`
- `scripts/ghost_core/adapters/trajectory.py`
- `scripts/ghost_core/adapters/continuity_benchmark.py`
- `scripts/ghost_core/adapters/usage_dashboard.py`
- `scripts/ghost_core/adapters/experiments.py`

### Integrated CLI surface
- `scripts/ghost_cli.py`
  - `ghost research run ...`
  - `ghost research list`
  - `ghost research show-run ...`
  - `ghost research baseline-save ...`
  - `ghost research regression ...`
  - `ghost research compare-runs ...`
  - `ghost research dashboard ...`
  - `ghost research focus ...`
  - `ghost research continuity-report ...`
  - `ghost research safety-report ...`
  - `ghost research experiments ...`
  - `ghost research track-outcome ...`

### Tests
- `tests/test_ghost_research.py`
- `tests/test_ghost_research_surfaces.py`
- `tests/test_ghost_cli.py`
- `tests/test_ghost_core_contracts.py`
- `tests/test_ghost_core_adapters.py`

## Runtime state
- `.local/research/runs.jsonl`
- `.local/research/events.jsonl`
- `.local/research/runs/*.json`
- `.local/research/trajectories/*/*.jsonl`
- `.local/research/baselines/*.json`
- `.local/research/experiments.json`

## Commands

### Run suites
```bash
python3 scripts/ghost_research.py run ghostlite --json
python3 scripts/ghost_eval.py run ghostlite --json
python3 scripts/ghost_safety_benchmark.py run --json
python3 scripts/ghost_continuity_benchmark.py run --json
python3 scripts/ghost_research.py run all --json
```

### Use the unified Ghost CLI
```bash
python3 scripts/ghost_cli.py research list --json
python3 scripts/ghost_cli.py research run ghostlite --case capture_decision --json
python3 scripts/ghost_cli.py research dashboard --days 14 --json
python3 scripts/ghost_cli.py research focus --days 14 --json
python3 scripts/ghost_cli.py research regression ghostlite --run-now --json
python3 scripts/ghost_cli.py research continuity-report --json
```

### Save baselines
```bash
python3 scripts/ghost_research.py baseline save ghostlite --json
python3 scripts/ghost_regression.py baseline safety --json
python3 scripts/ghost_cli.py research baseline-save safety --json
```

### Compare against baseline
```bash
python3 scripts/ghost_research.py regression ghostlite --run-now --json
python3 scripts/ghost_regression.py compare ghostlite --run-now --json
python3 scripts/ghost_regression.py check continuity --run-now --json
python3 scripts/ghost_cli.py research regression continuity --json
```

### Log trajectories and experiment outcomes
```bash
python3 scripts/ghost_research.py track outcome manual proposal-review success --score 1.0 --model gpt-5.4 --notes "client-ready" --json
python3 scripts/ghost_trajectory_log.py append run-123 --event manual_outcome --suite manual --task proposal-review --status success --score 1.0 --json
python3 scripts/ghost_experiments.py add phase2-context-bridge --hypothesis "Context bridge reduces continuity misses" --json
python3 scripts/ghost_experiments.py run phase2-context-bridge --metric score_pct=94.2 --metric misses=1 --json
python3 scripts/ghost_dashboard.py summary --days 14 --json
python3 scripts/ghost_dashboard.py focus --days 14 --json
```

## Suite coverage

### GhostLite
- decision capture routing
- follow-up capture routing
- prompt-injection blocking
- duplicate detection
- file-size budget protection
- rate-limit error classification
- cheap/heavy model routing
- context deadline/blocker extraction

### Safety
- injection blocking
- exfiltration blocking
- invisible unicode blocking
- audit/reference-doc false-positive avoidance
- normal-note allow path
- duplicate detection
- size-budget alerts

### Continuity
- commitment + follow-up survive into recall
- blocker + deadline survive into context snapshot
- duplicate guard keeps continuity clean
- people and decision storage remain canonical across steps

## Success criteria
- Full test suite stays green
- Baselines can be saved and compared
- Dashboard shows suite health over time
- Focus report turns raw eval signals into concrete next actions
- Manual outcomes augment automated benchmarks
- Telemetry and storage failures degrade gracefully instead of killing the whole eval run

## Validation
- `pytest tests/ -q` → passing
