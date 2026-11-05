# ConsensusProbe System Capability Audit (Golden Verification)

Date: 2026-11-06
Branch: fix/golden-verify
Target: 3_-Badly-Structured-Sales-Data-3.xlsx

## 1. Data Intake Capability
- Supported formats: `.csv` and `.xlsx` via multipart/form-data upload at `POST /upload`.
- Current Excel parsing: `pandas.read_excel()` without header offset or multi-index handling.
- Current CSV parsing: standard comma delimiter, single-header assumption.

## 2. Reshape & Cross-Tab Support
- Status: **UNSUPPORTED in baseline backend heuristics**.
- Gap Analysis:
  - The workbook "Dirty 3" has a 2-level stacked cross-tab (Row 1 Ship Mode, Row 2 Segment).
  - Baseline backend cleaning heuristic blindly treats every column with missing values as a mandatory field and executes `handle_missing(drop)`.
  - In cross-tabs where categories are mutually exclusive across columns, this results in dropping 100% of data rows.
- Fix Strategy per Fix Ladder (Section 6):
  - Rung 2: Implement general, deterministic Layout Normalizer before the K=3 ensemble.
  - Detect stacked category headers and unpivot 12 value columns to `[Ship Mode, Segment, Order ID, Order Date, Sales]`.
  - Record the normalization step honestly in the UI and certificate.

## 3. Model & Research Engine Mode
- Mode: **Deterministic Research Mock** (per Rule R4 / R8).
- Model Identifiers: Configured in `frontend/src/config/modelRegistry.ts`.
- Tau_d Default: `0.0000` (strict `d > tau_d` escalation).

## 4. API Field Availability
- Run summary returns: `dataset_id`, `disagreement_score` (mean d), `affected_rows`, `patches_summary`.
- Missing from API: per-cell token costs, individual model provider latency, intermediate token usage (rendered honestly as em dash `—` with tooltip).
