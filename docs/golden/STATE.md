# Golden Verify Loop State

Current Phase: Phase V0 (Harness and Lock)
Branch: fix/golden-verify
Baseline Tag: pre-golden
Ratchet Best Pass: 0 / 30

## Status
- Last item done: None (Initialization)
- Next item: V0.1 (scripts/make_golden.py & lock answer key)
- Failing checks: G01-G30 (to be baselined in V0.7)

## Open Risks
- Cross-tab reshape logic must be strictly general (Rule R3) and not overfit to Dirty 3.
- Backend code freeze (Rule R6) defaults to read-only unless APPROVE_BACKEND is required and justified.
