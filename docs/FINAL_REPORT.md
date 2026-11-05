# Final Report: ConsensusProbe

## Mode: DEGRADED

The project was completed in degraded mode due to missing external tools.

## What Was Built

1. **Research engine** (`research/`): ConsensusGate consensus policy, 5 cleaning operations, Patch system, MockProvider with seeded determinism, 8 evaluation systems (A, A2, B, C, D, E, F, R), 3 user simulation modes, canary safety probes.
2. **Benchmark**: 100 TEST tasks (seeds 5000–5099) with 5 ambiguity types, 7,200 total evaluations.
3. **Backend** (`backend/`): FastAPI app with upload, profiling, cleaning, export (PDF/CSV/XLSX with formula injection protection).
4. **Frontend** (`frontend/`): React + Vite + TypeScript + Tailwind single-page app with Dashboard, Upload, Profile, and ConsensusGate Workspace views.
5. **Paper** (`paper/main.tex`): Full LaTeX manuscript with 13 figures, 10 tables, all data from macros (160 macros in `results/numbers.tex`), pre-registered hypotheses reported including H2 failure.
6. **Reproducibility**: Seeded RNG (R4), security scanner (R5), academic integrity checks (R6), mock honesty disclosures (R7), pre-registration lock (`prereg/lock.json`).

## Key Results

- **H1 Supported**: ConsensusGate reduces silent errors vs. single-plan baseline.
- **H2 Not Supported**: ConsensusGate is NOT non-inferior to always-ask policy.
- **H3 Supported**: ConsensusGate outperforms confidence-threshold policy.
- **H4 Supported**: ProbeGate adds canary safety with no measurable overhead.

## Degraded Components

| Component | Status | Reason |
|-----------|--------|--------|
| Paper PDF compilation | DEGRADED | `latexmk` not installed |
| Code review | DEGRADED | `cr` (CodeRabbit CLI) not installed |

## Open Items (from TODO_HUMAN.md)

- Install a TeX distribution (MiKTeX or TeX Live) for `latexmk`
- Install CodeRabbit CLI for per-phase review
- Verify citations in `refs/related_work.csv` (DOIs, authors, page numbers)

## Verification

Run `make verify_all` to execute the full check suite. Expected passes:
- Backend tests (pytest)
- Frontend build (Vite + TypeScript tsc)
- Security scan (no eval/exec/pickle/shell=True, no secrets)
- Lock-file integrity
- Numbers-macro consistency (160 macros)
- Same-seed determinism

Expected skips (DEGRADED):
- `latexmk` paper compilation
