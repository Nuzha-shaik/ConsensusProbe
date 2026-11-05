# Golden Verify Loop State

Current Phase: Phase V0 Complete -> Advancing to Phase V1 (Data Layer: G01-G11)
Branch: fix/golden-verify
Baseline Tag: pre-golden
Ratchet Best Pass: 4 / 30

## Status
- Last item done: V0.8 (Phase V0 review ritual & tag golden-phase0-done)
- Next item: V1.1 (Phase V1 Data Layer planning & layout normalizer)
- Passing checks: G14, G27, G28, G29 (4/30)
- Failing checks: G01-G13, G15-G26, G30 (26/30 baseline)

## Phase V0 Shipped
- Locked golden answer key: docs/golden/golden_truth.csv, golden_metrics.json, dirty3.csv
- Checksum integrity lock: docs/golden/GOLDEN.sha256 (verified via make golden_integrity)
- Anti-leakage guard: scripts/no_leak_check.py (Rule R2, verified via make no_leak)
- Golden scoreboard: scripts/golden_check.py covering G01-G30
- Capability audit: docs/golden/CAPABILITY.md
- Baseline ratchet recorded: docs/golden/RATCHET.json (4 passing, 26 failing)

## Open Risks
- Reshape logic must be general and structural (Rule R3), supporting arbitrary multi-level cross-tabs without dataset-specific constants.
