# Baseline UI Gate Output

Recorded at: 2026-11-06T00:52:00+05:30
Git Baseline Tag: pre-cp2
Branch: feat/cp2-showcase

## ui_gate.py Execution Record

```text
============================================================
ConsensusProbe: make ui_gate
============================================================
[PASS] Step 1: Frontend TypeScript typecheck 
[PASS] Step 1: Frontend production build 
[PASS] Step 2: Backend unit tests 
[PASS] Step 3: Baseline test comparison (0 regressions)
[PASS] Step 4: Core-freeze check (39 changed files verified)
[PASS] Step 5: Secret scan (no GOCSPX- or client secrets)
[PASS] Step 6: Production bundle dev-mock check (clean of AUTH_DEV_MOCK)
[PASS] Step 7: Dependency budget check (within allowed scope)
============================================================
UI GATE: ALL CHECKS PASSED
```

## Baseline Status
- TypeScript Errors: 0
- Frontend Build: Successful
- Backend Unit Tests: All passing
- Regressions: 0
- Dev Mock Leaks: 0
- Secret Violations: 0
