# UI Baseline (pre-ui-upgrade)

Baseline recorded at commit `9ef37b2` (`pre-ui-upgrade` tag):

## Frontend
- `npx tsc --noEmit`: PASS (0 errors)
- `npm run build`: PASS (built in 7.54s, bundle size: 867.93 kB JS, 20.45 kB CSS)
- Lint script: None configured

## Backend
- `python -m pytest -x -q research/ backend/`: PASS (36 passed, 0 failed in 3.30s)

## Baseline Failing Tests
- None (0 failures)
