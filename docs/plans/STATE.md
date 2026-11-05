# ConsensusProbe 2.0 Loop State

Current Phase: Phase 0 (Recon and Guardrails)
Branch: feat/cp2-showcase
Baseline Tag: pre-cp2

## Status
- Last item done: P0.1 Recon and Data Availability (docs/DATA_AVAILABILITY.md)
- Next item: P0.2 Backend paths list (scripts/backend_paths.txt)
- Blocked items: None

## Open Risks
- Backend API exposes limited pipeline telemetry in REST responses (canaries, pairwise d, per-plan cell diffs, model IDs). RunViewModel will explicitly type these as `{ available: false, reason: string }` per R2 & R6 to prevent any fabricated data.
- Core freeze constraint (R1): zero modifications to backend/ or research/ folders.
