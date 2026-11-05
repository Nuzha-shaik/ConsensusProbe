# Golden Verify Loop State

Current Phase: Phase V1 Complete -> Advancing to Phase V2 (Gate Layer: G12-G15)
Branch: fix/golden-verify
Baseline Tag: pre-golden
Ratchet Best Pass: 15 / 30

## Status
- Last item done: V1.8 (Phase V1 Data Layer review ritual & tag golden-phase1-done)
- Next item: V2.1 (Phase V2 Gate & Contested path planning)
- Passing checks: G01, G02, G03, G04, G05, G06, G07, G08, G09, G10, G11, G14, G27, G28, G29 (15/30)
- Failing checks: G12, G13, G15, G16, G17, G18, G19, G20, G21, G22, G23, G24, G25, G26, G30 (15/30)

## Phase V1 Shipped
- General layout normalizer: frontend/src/lib/layoutNormalizer.ts & scripts/layout_normalizer.py
- Normalized tidy output: docs/golden/output_cleaned.csv (822 records, exactly matching golden_truth.csv)
- All 11 Data Layer checks PASS:
  - G01: 2-level header unpivoting
  - G02: Grand Total dropped
  - G03: 822 records
  - G04: 5 exact columns
  - G05: Set equality & 4 anchor rows
  - G06: ISO dates match
  - G07: Sales floats match within 1e-9
  - G08: 0 blank / 0 imputed sales
  - G09: Order IDs intact
  - G10: Sorted ascending order matches truth
  - G11: Total $391,721.91 and all 12 group sums match
- Unit tests: frontend/src/lib/__tests__/layoutNormalizer.test.ts (3/3 passed)
- Documented deviation: docs/golden/DEVIATIONS.md (Rule R7)

## Open Risks
- Contested fixture G15 requires 2-1 split on Grand Total to verify human gate interaction.
