# ConsensusProbe 2.0 Loop State

Current Phase: Phase 0 Complete -> Advancing to Phase 1 (Ingestion & Hero)
Branch: feat/cp2-showcase
Baseline Tag: pre-cp2
Phase Tag: cp2-phase0-done

## Status
- Last item done: P0.12 Phase 0 verification, review ritual, and tag
- Next item: P1.1 (Phase 1 planning: Hero component & pipeline strip)
- Blocked items: None

## Phase 0 Shipped
- Data Availability Audit (docs/DATA_AVAILABILITY.md)
- Guard scripts: core_freeze_check.py, token_check.py, no_literals_check.py
- Test harness: vitest 2.1.9, playwright 1.64.1, axe-core
- RunViewModel adapter with strictly typed unavailable telemetry states
- Pure functions & unit tests: metrics.ts, gateDecision.ts, 12 passing unit tests
- Makefile with freeze, guards, typecheck, test, build, ui_gate, gate targets

## Unavailable & Why
- Canaries, pairwise d matrix, per-plan cell diffs, model IDs, token counts, execution timings not exposed by backend API. Typed as `{ available: false, reason: string }` per R2/R6.
