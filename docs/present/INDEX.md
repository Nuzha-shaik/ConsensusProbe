# ConsensusProbe Presentation Mode — Master Plan Index

## 1. Task Order & Dependency Graph

```
[T01: Backend Metrics & Scenario Runner]
       │
       ▼
[T02: Presentation Mode Header & Scenarios 1-2]
       │
       ├───► [T03: Micro-Dispute Inspector]
       │
       ├───► [T04: System Comparison Analytics Bar]
       │
       ├───► [T05: Canary Sentinel Widget & Scenario 3]
       │
       ├───► [T06: Pareto Chart (Inline SVG)]
       │
       ├───► [T07: Benchmark Seed Selector]
       │
       └───► [T08: Integrity Hash (SHA-256) Drawer]
               │
               ▼
[T09: Audit PDF Change Highlights]
       │
       ▼
[T10: QA Smoke Tests, PDF Text Verification & Demo Script]
```

- **T01** is prerequisite for all downstream features (provides backend endpoints + scenario contract).
- **T02** adds the visual container & presentation toggle in `App.tsx`.
- **T03–T08** can be implemented sequentially; they enrich the Presentation Mode dashboard.
- **T08** and **T09** share the exact same patch and change summary data structures.
- **T10** validates full integration, verifies PDF text invariants, and generates `DEMO_SCRIPT.md`.

---

## 2. Repo Conventions & Architectural Findings

- **Backend Architecture**:
  - FastAPI application located at `backend/app/main.py`.
  - Pydantic models in `backend/app/models.py`.
  - Server endpoints use CORS and error handling; all data derived from `research/` or `results/`.
- **Frontend Architecture**:
  - React 18 SPA built with Vite and TypeScript (`frontend/src/App.tsx`).
  - Styling: Tailwind CSS with dark mode classes (`dark:bg-slate-900`, `dark:border-slate-800`, `text-slate-900`, `dark:text-white`).
  - Icons: `lucide-react` (already installed).
  - API Client: `frontend/src/api/client.ts` pointing to `VITE_API_URL` (default `http://localhost:8000`).
  - Client-Side Engine: `frontend/src/lib/clientEngine.ts` provides zero-install, in-browser dataset execution and jsPDF export when backend is offline or static-hosted on Firebase.
- **Results & Data Sources**:
  - Ground truth benchmark evaluations: `results/metrics.json` (300 evaluations per system across A, A2, B, C, D, E, F, R).
  - Dev calibration: `results/dev_calibration.json` (`best_tau_d = 0.0`).
  - Real track generator: `research/track_s.py`, `research/consensus.py`, `research/canary.py`.
- **Chart Libraries**:
  - `package.json` contains **NO** external charting library.
  - Per Design Rule 6: ALL charts (e.g. Pareto frontier) must be implemented with pure inline React SVG elements.

---

## 3. How to Run Dev Server and Tests

- **Run Backend**:
  ```powershell
  uvicorn backend.app.main:app --port 8000 --reload
  ```
- **Run Frontend**:
  ```powershell
  cd frontend
  npm run dev
  ```
- **Run Tests**:
  ```powershell
  pytest tests/ -v
  cd frontend
  npm test
  ```

---

## 4. Definition of Done

1. Every task touches **ONLY** its whitelisted files.
2. Presentation Mode can be launched with 1 click from the dashboard header.
3. All metrics match `results/metrics.json` and `results/numbers.tex` exactly (no hardcoding).
4. All 3 demo scenarios run deterministic real logic with real latency measurements.
5. Audit PDF feature (T09) passes the additive invariant test: with `include_change_highlights=false`, text is bitwise/string identical to baseline.
6. TypeScript check (`npm run build` or `npx tsc`) passes with 0 errors.

---

## 5. Five Most Likely Flash Failure Points & Exact Guards

1. **Failure 1: Audit PDF Regression (Breaking existing PDF output)**
   - *Symptom*: Flash alters existing headers, layout, or font styles in `clientExportPdf`.
   - *Guard*: Step 0 of T09 creates `tests/golden/audit_baseline.txt`. `test_audit_pdf_preserves_baseline` compares plain text output and asserts 100% preservation of all baseline text.
2. **Failure 2: Hardcoding Metrics & Placeholders**
   - *Symptom*: Flash types `67.0%`, `71.3%`, `d=0.67` directly into TSX components.
   - *Guard*: T01 provides typed `/api/metrics/summary` and `clientEngine.ts` exports `getBenchmarkMetricsSummary()` reading directly from imported `results/metrics.json`.
3. **Failure 3: Adding npm dependencies (e.g. recharts, chart.js)**
   - *Symptom*: Flash runs `npm install recharts` or `chart.js`.
   - *Guard*: Explicitly disallowed in prompt and T06; T06 contains a ready-to-use pure SVG component skeleton.
4. **Failure 4: Out-of-Scope File Modifications**
   - *Symptom*: Flash modifies `research/patch.py`, `scripts/make_numbers.py`, or root configs.
   - *Guard*: Strict whitelist in each task file; any edit outside the whitelist causes task failure.
5. **Failure 5: Failing Offline / Fallback Operation**
   - *Symptom*: Presentation mode fails if backend server isn't running on port 8000.
   - *Guard*: Every scenario and metric fetch in the frontend has an automatic client-side fallback using `clientEngine.ts` and local JSON imports.
