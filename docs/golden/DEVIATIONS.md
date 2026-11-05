# ConsensusProbe Deviations Log (Rule R7)

## Deviation DEV-01: Layout Normalization Outside K=3 Ensemble
- **Component**: `frontend/src/lib/layoutNormalizer.ts` & `scripts/layout_normalizer.py`
- **Fix Ladder Level**: Rung 2 (Deterministic Layout Normalizer)
- **Description**: Cross-tab matrix reshaping (unpivoting 12 structural value columns and dropping the Grand Total summary row) is executed as a deterministic pre-processing stage prior to the K=3 plan ensemble.
- **Honest Label Requirement**:
  - UI labels and provenance certificates must explicitly state:
    *"Layout normalization (deterministic, outside the K=3 ensemble)"*
  - The K=3 cleaner ensemble operates on the normalized tidy dataset, auditing completeness, formatting consistency, and detecting anomalies.
- **Justification**:
  - Unpivoting a cross-tab with fixed structural headers is an algebraic matrix reshape, not an LLM hallucination risk.
  - Feeding the raw cross-tab to naive row-drop heuristics results in dropping 100% of data rows because sparse options are mutually exclusive across columns.
