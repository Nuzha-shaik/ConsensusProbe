# Data Availability Audit (ConsensusProbe 2.0 Recon)

**Date**: 2026-11-06  
**Audited Against**: 
- Backend: `backend/app/main.py`, `backend/app/models.py`, `research/consensus.py`, `research/patch.py`
- Frontend: `frontend/src/api/client.ts`, `frontend/src/App.tsx`
- Freeze Rule R1: Backend is frozen; any missing telemetry must be typed as unavailable or computed client-side.

---

## 13-Point API Field Audit Matrix

| # | Telemetry / Data Field | API Status | Source / Field Name | Handling in RunViewModel & UI |
|---|------------------------|------------|---------------------|-------------------------------|
| 1 | **Original rows** | **AVAILABLE** | `POST /upload` -> `rows`, `GET /profile/{id}` -> `rows`, `preview` (20 rows), or in-browser parsed CSV | Available. Ingested file parsed via Web Worker for instant local table rendering. |
| 2 | **Cleaned rows** | **AVAILABLE** | `GET /profile/{id}` (active patch preview), `GET /export/{id}?format=csv` (full file) | Available. Export CSV can be loaded or client-side patch applied to original rows. |
| 3 | **3 candidate plans & per-cell edits** | **MISSING** | Internal only: generated in `backend/app/main.py:209-240` and stored in SQLite `CandidatePlan` table, but NOT serialized in `CleanResponse` | Marked `{ available: false, reason: "Candidate plan proposals and per-cell operations are not exposed by the /clean API endpoint" }`. UI shows honest unavailable state per R6. |
| 4 | **Pairwise d values** | **MISSING** | Internal only: calculated inside `research/consensus.py` during `calculate_consensus(patches)` | Marked `{ available: false, reason: "Pairwise disagreement matrix is internal to the consensus engine and omitted from API response" }`. |
| 5 | **Mean d** | **AVAILABLE** | `CleanResponse.consensus_score` (float) | Available as `meanDisagreement: number`. Computed directly from engine. |
| 6 | **tau_d** | **MISSING** | Hardcoded to `0.0` in `backend/app/main.py:257` (`consensus.should_ask(tau_d=0.0)`); not returned in API | Default set to `0.0` with configurable slider in UI for simulation. Marked `{ available: false, reason: "Default tau_d is fixed to 0.0 in server logic and not returned by API" }`. |
| 7 | **Gate decision** | **AVAILABLE** | `CleanResponse.status`: `"needs_clarification"` vs `"applied"` / `"no_changes"` | Available: maps to `"needs_human_clarification"` vs `"auto_approved"`. Evaluated strictly against `mean d > tau_d`. |
| 8 | **Canary results** (planted, expected, observed) | **MISSING** | No canary planting or audit endpoints exist in the backend API | Marked `{ available: false, reason: "Backend API does not support runtime canary injection or telemetry" }`. UI renders honest canary audit panel indicating unavailable for live runs, or ground-truth evaluation for bundled sample datasets. |
| 9 | **Model identifiers** (proposer / auditor) | **MISSING** | Backend uses rule-based plan heuristics and MockProvider; no model IDs returned | Marked `{ available: false, reason: "Model identifiers not reported by the backend API" }`. UI styles as "Deterministic research mock" per R4. |
| 10 | **Mock vs live indicator** | **MISSING** | API does not report execution environment | Handled via config / run metadata: labelled "Deterministic research mock" per R4. |
| 11 | **Timings (agent latencies)** | **MISSING** | No timestamps or elapsed milliseconds in `CleanResponse` | Marked `{ available: false, reason: "Agent execution timings not reported by API" }`. Timeline labelled "Reconstructed from run summary" when synthetic reconstruction is enabled. |
| 12 | **Token usage** | **MISSING** | No token counters in `CleanResponse` | Marked `{ available: false, reason: "Token usage not reported by API" }`. UI renders em dash `—` with explanatory tooltip per R6. |
| 13 | **Human-clarification endpoint** | **AVAILABLE** | `POST /clarify/{id}` with `ClarifyRequest` `{ selected_option, notes }` -> `CleanResponse` | Available. When `status == "needs_clarification"`, `CleanResponse.question` provides `question_text`, `options`, `affected_rows_count`, and `example_rids`. |

---

## Architecture Plan for RunViewModel

Per Rule R1 (Core Freeze), we will NOT alter backend code to add fields. Instead:
1. `RunViewModel` in `frontend/src/adapters/runViewModel.ts` will strictly type all 13 fields.
2. Available fields (`originalRows`, `cleanedRows`, `meanDisagreement`, `gateDecision`, `clarificationQuestion`, `patchSummary`) will be mapped directly.
3. Missing fields (`candidatePlans`, `pairwiseD`, `canaries`, `modelIds`, `tokens`, `timings`) will be wrapped in `{ available: false, reason: string }`.
4. Sample datasets (`retail_clean.csv`, `customers_contested.csv`) will be accompanied by companion ground-truth and run metadata fixtures so the showcase can demonstrably exercise all visual elements without violating truthfulness rules.
