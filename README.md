# ConsensusProbe

Disagreement-driven interactive gates for reliable LLM-based data cleaning.

## Quick Start

```bash
# Backend
pip install -r requirements.txt   # or: pip install fastapi uvicorn sqlalchemy pandas pydantic openpyxl reportlab matplotlib numpy scipy
cp .env.example .env
cd backend && uvicorn app.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Run experiments (mock LLM, zero cost)
python -m research.run_experiments

# Verify everything
make verify_all
```

## Project Structure

```
backend/          FastAPI application (upload, profile, clean, export)
frontend/         React + Vite + TypeScript + Tailwind UI
research/         ConsensusGate engine, policies, experiments
paper/            LaTeX manuscript and figures
results/          Experiment outputs (metrics.json, hypotheses.json)
scripts/          Build, check, and generation scripts
configs/          Frozen experiment parameters
prereg/           Pre-registration and integrity lock
docs/             Charter, state, dependency manifest
refs/             Related work bibliography source
```

## Key Results

Evaluated on 100 synthetic tasks, 7,200 total runs (8 systems × 3 modes × 3 trials):

| System | Success | Silent Error | Questions/Task |
|--------|---------|--------------|----------------|
| A (single plan) | 67.0% | 5.0% | 0.00 |
| E (ConsensusGate) | 72.8% | 0.0% | 0.38 |
| C (always ask) | 73.3% | 0.0% | 1.00 |

**Mock-honesty notice:** All results use `LLM_PROVIDER=mock`. See paper for details.

## Reproduction

```bash
make verify_all    # runs tests, security, numbers check, determinism
make gate PHASE=N  # check a single phase
```

Expected runtime: ~60s for full experiment + verification.

## License

MIT
