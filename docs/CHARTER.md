# ConsensusProbe Charter
Source of truth. Never read it whole after iteration 1: `grep -n '^## ' docs/CHARTER.md`, then `sed -n 'A,Bp'` only the section you need.

## 0. Role and mission
Senior AI researcher + full-stack architect. Build, autonomously, a monorepo: (a) ConsensusProbe, a web app for CSV/Excel upload, profiling, AI cleaning, transformation, validation, PDF/CSV/Excel export; (b) a reproducible LaTeX paper evaluating ConsensusGate against baseline policies. Original datasets are immutable (stored read-only, sha256 recorded, verified before and after every run).

## 1. Rules of engagement
**R1 Token discipline (highest priority; a prior run died on token limits).**
- Never `cat` results/*.json, lockfiles, node_modules, build or test logs. Use `head -n 40`, `tail -n 25`, `grep`, `sed -n`.
- Redirect every long command: `cmd > .logs/<name>.log 2>&1; tail -n 25 .logs/<name>.log`. Read the log only on failure, and only the failing part.
- Write each file once, complete. No rewrites for style. No prose in chat beyond one status line per task.
- During a phase run only touched-module tests (`pytest -x -q <path>`). Full `make verify_all` only in P10 and when the Completion Contract is believed met. `make gate PHASE=N` is the cheap per-phase check.
- GSD plan per phase: at most 15 lines in `docs/plans/PN.md`. Do not re-plan finished phases.
- CodeRabbit: once per phase, on the phase diff only, at most one fix round. Fix correctness, determinism, security. Ignore style.
- Quiet installs: `pip install -q`, `npm install --no-fund --no-audit --silent`.
- **Context guard:** at about 70% context, or on any usage-limit warning: finish the current task, commit, write the handoff in STATE.md, end the iteration normally. Do NOT emit the completion promise.

**R2 Checkpointing.** One task = one commit (`P4.3: disagreement scorer`). Update `docs/STATE.md` after every task, before starting the next. A task that cannot finish in one iteration must be split.

**R3 Ponytail / YAGNI.** Standard library first. Any new dependency requires a line in `docs/DEPS.md` (name, version pin, reason) in the same commit. No abstractions without two call sites.

**R4 Determinism.** All randomness via `random.Random(seed)` / `numpy.random.default_rng(seed)`; derive seeds with `hashlib.sha256`, never builtin `hash()`. Sort every set/dict before iterating into outputs. Fixed timestamps in logs (`SOURCE_DATE_EPOCH`). Same seed twice must give byte-identical `results/metrics.json`; `make verify_all` checks this.

**R5 Security.** No secrets in repo; `.env.example` only; `.gitignore` covers `.env`, `*.db`, `node_modules`, `.logs`. `scripts/check_security.py` AST-scans for `eval`, `exec`, `pickle.load`, `os.system`, `subprocess(..., shell=True)` and greps for key patterns (`sk-`, `AKIA`, `BEGIN PRIVATE KEY`). Upload: allow only `.csv/.xlsx`, 50 MB cap, uuid filenames, no user-controlled paths. Excel/CSV export must neutralize formula injection (prefix cells starting with `= + - @` with `'`). CORS restricted to the Vite dev origin.

**R6 Academic integrity.** Every number in the paper comes from `results/*.json` via `results/numbers.tex` macros; `scripts/check_numbers.py` recomputes each macro and fails on mismatch. No hand-typed results. Formal tone. No fabricated DOIs, authors or page numbers: `refs/related_work.csv` has columns `key,title,authors,venue,year,doi_or_url,verified,note`; unknown fields stay blank, `verified=no`, and the item goes into `docs/TODO_HUMAN.md`. Report all hypotheses, including nulls and failures.

**R7 Mock honesty.** With `LLM_PROVIDER=mock` and `BUDGET_USD=0`, results measure policy logic under a simulated-LLM noise model, not real LLM behavior. The abstract, evaluation and threats-to-validity sections must say so explicitly. Never claim generalization to real models.

**R8 Offline tolerance.** If a network install or tool is unavailable, do not loop on it: record the blocker in STATE.md and `docs/TODO_HUMAN.md`, use the smallest offline substitute (e.g. hand-written minimal UI components instead of shadcn CLI), mark `mode: DEGRADED`, continue. Never fake an artifact (no placeholder PDFs, no fake test passes).

## 2. State file schema (`docs/STATE.md`, keep under 60 lines)
```
phase: P4            # P1..P10
task: P4.3
status: in_progress  # in_progress | done | blocked
last_green_commit: <sha>
next_action: <one sentence, concrete>
mode: COMPLETE       # or DEGRADED
iteration: <n>
blockers: []
decisions:           # dated one-liners, max 15, prune old ones
handoff: <only when ending an iteration early: what is half-done and where>
```

## 3. Resume protocol (run at the start of every iteration)
1. Read STATE.md. If absent (e.g. a previous run died before writing it): inspect `ls`, `git log --oneline | head -10`, `git status --short | head -20`, reconstruct the phase from existing artifacts, write STATE.md, then continue. Never restart a phase whose artifacts already exist and pass their gate.
2. If the tree is dirty: run tests for the touched files. Green: commit. Red: finish the half-done task if small, else `git checkout -- <file>` the partial file and redo that task.
3. Run `make gate PHASE=<current>` (after P1). If it passes, mark the phase done and advance. Otherwise do `next_action`.
4. Execute exactly one task, then commit and update STATE.md. Repeat until the context guard fires.

## 4. Phases and gates
Each phase = `/gsd-plan-phase N` -> tasks -> tests -> commit -> `/coderabbit:review` -> fix -> `make gate PHASE=N` -> advance. `scripts/gate.py` is created in P1 and each phase adds its own checks (artifact exists, tests pass, config keys present).

### P1 Scaffold, literature, requirements
- Dirs: `frontend/ backend/app/ research/ scripts/ docs/ prereg/ results/ refs/ configs/ paper/ .logs/`.
- `Makefile` targets: `verify_all tests build gate lock_check paper clean`. `scripts/check_security.py`, `scripts/check_lock.py`, `scripts/gate.py`, `scripts/check_numbers.py` (stub allowed until P9).
- `docs/STATE.md`, `docs/DEPS.md` (pre-approved: fastapi, uvicorn, sqlalchemy, pandas, pydantic, openpyxl, reportlab, matplotlib, pytest, numpy, scipy), `docs/TODO_HUMAN.md`, `docs/ARTIFACTS.md` (the F1-F13 / T1-T10 manifest from section 6).
- `refs/related_work.csv` seeded with LAMBDA (JASA 2025), PrepBench, AutoDCWorkflow, all `verified=no` unless verifiable offline.
- Gate: `make gate PHASE=1` passes; `git log` has a baseline commit.

### P2 Ground truth, operations, baselines
- `_rid`: stable integer row id injected at load, never reused, survives filtering, dropped on export.
- Operations (pure, copy-on-write, return new DataFrame + Patch): `deduplicate(by=[cols], keep)`, `normalize_category(col, mapping|rule)`, `recalculate(target, formula)`, `handle_missing(col, strategy)`, `convert_type(col, dtype)`. Registry maps name -> function + JSON schema for params. Unknown op or bad params raises a typed error, never silently skips.
- `Patch`: `deleted_rids` (sorted tuple), `cell_edits` (`{(rid, col): new_value}`), `flagged` (`{rid: reason}`); `Patch.atoms()` returns the edit set E as sorted hashable atoms `("del", rid)` and `("edit", rid, col, repr(value))`. Flags are excluded from E.
- `MockProvider`: input (prompt, seed, k) -> deterministic JSON plan. Noise model (parameters live in `configs/frozen.toml`): for operations with a gold-ambiguous parameter, each plan picks among candidate parameterizations with probabilities `p_amb`; for unambiguous operations it follows gold with probability `1 - eps`. Token count = whitespace-token count of prompt + output (deterministic).
- Tests: op purity (input DataFrame unchanged), patch round-trip, mock determinism (same seed => same JSON), different k => different plans.

### P3 Pilot (DEV)
- Track S generator: retail/inventory CSVs with gold labels (`gold.json`: required_edits, forbidden_edits, ambiguous: bool, ambiguity_type). Ambiguity taxonomy (minimum 5 types): duplicate-by-name vs by-ID, category merge granularity, missing value strategy, unit/currency recalculation basis, type coercion of mixed columns. Balance about 50% ambiguous tasks.
- 20 DEV tasks, seeds 1000-1019. TEST seeds live in a disjoint range (5000+); the generator refuses to emit a TEST seed in DEV mode.
- Pilot: K=5 plans per task. Calibrate `tau_d` on K=3 subsets sampled from the 5 (production uses K=3): choose the value maximizing F1 of "ask" vs `ambiguous`, ties to the smaller value. Write `tau_d`, `p_amb`, `eps`, K, seeds, and the DEV data hash to `configs/frozen.toml`. Save the calibration curve data to `results/dev_calibration.json`.

### P4 Consensus engine and policies
- Disagreement: `d(i,j) = 1 - |E_i ∩ E_j| / |E_i ∪ E_j|`, with `d = 0` when both sets are empty. Task score = mean pairwise d over the K plans. Contested atoms = atoms not in all K patches. Ask iff score > `tau_d` AND contested atoms contain a destructive or transformative atom.
- Question generator: group contested rids by the parameter that differs between plans (e.g. `dedup.by`); output one question with 2-4 options, each listing affected row count and up to 3 example rows. At most one question per task per round; max 2 rounds.
- Simulators (read Track S gold, seeded): oracle (always correct), noisy (correct w.p. 0.8), unsure (answers "unsure" w.p. 0.3; the policy then falls back to the majority plan and sets `flagged`).
- Systems: A single plan; A2 majority-vote of K=3 plans, never asks (token-matched control isolating ensembling from asking); B A + validators (row-count drop > 20%, key-uniqueness, dtype, null-rate); C always ask; D ask when the plan's self-reported confidence < threshold in `frozen.toml`; E ConsensusGate; R random-ask baseline that asks with probability equal to E's DEV ask rate.
- Tests for each system on a hand-built mini task with known expected behavior.

### P5 Canaries and pre-registration lock
- ProbeGate: canary generators (known fake duplicates, misspelt cities); append to a temp copy with `_canary=True`; a policy is flagged unsafe on a task if a plan edits or deletes canaries incorrectly. Canaries never reach the output dataset. System F = E + canary check (unsafe plan => ask or fall back).
- `prereg/PREREG.md`: hypotheses, metrics, tests, exclusion rules, written before any TEST run (section 5).
- `scripts/lock.py`: sha256 of tests, gold-label generator, `configs/frozen.toml`, PREREG.md into `prereg/lock.json`. `scripts/check_lock.py` fails if any hashed file changed after the lock commit. After this phase `frozen.toml` is read-only; changing it requires a new lock and a `decisions` entry explaining why.

### P6 Full experiments
- 100 TEST tasks (seeds 5000-5099). Systems A, A2, B, C, D, E, F, R x modes oracle/noisy/unsure x `TRIALS=3` (trial seed = sha256(task_seed, system, mode, trial)).
- Extra cheap runs: K ablation for E at K in {2,3,4,5}; `p_amb` sensitivity at three values; canary detection rates.
- Outputs: `results/metrics.json` (per task/system/mode/trial: task_success, silent_error, questions_asked, question_precision, tokens, simulated_latency), `results/hypotheses.json`, `results/ablations.json`. Wall-clock time is logged separately and never used in claims.
- Resumable: write each (system, mode) block to `results/parts/*.json`; a rerun skips blocks that exist with matching config hash. Merge at the end.
- Metric definitions: task_success = all gold required edits applied AND zero forbidden edits. silent_error = a forbidden destructive edit applied without a question or flag. question_precision = asked-on-ambiguous / asked.

### P7 Backend application
- SQLAlchemy models: Dataset (id, sha256, path, rows, cols), CandidatePlan, OperationRun, Clarification (question JSON, answer, status). SQLite file via env `DATABASE_URL`.
- Endpoints: `POST /upload`, `GET /profile/{id}`, `POST /clean/{id}` (returns `{status:"needs_clarification", question}` or `{status:"applied", patch_summary}`), `POST /clarify/{id}`, `POST /analyze/{id}`, `GET /export/{id}?format=pdf|csv|xlsx`. Pydantic schemas on every route. The engine is imported from `research/` or a shared package, not duplicated.
- reportlab PDF (cleaning summary + audit log), openpyxl audit workbook. Test with FastAPI TestClient: upload -> clean -> clarify -> export; original file hash unchanged.

### P8 Frontend application
- Vite + React + TypeScript + Tailwind; shadcn/ui via CLI if online, else minimal local components (R8). Pages: Dashboard, Upload (preview first 20 rows), Profile, ConsensusGate workspace (three candidate-plan columns, affected-rows table with diff highlighting, clarification dialog that posts to `/clarify`). API base from `VITE_API_URL`.
- Gate: `npm run build` and `tsc --noEmit` exit 0. No extra test framework (YAGNI).

### P9 Statistics and manuscript
- `scripts/make_figures.py` (matplotlib, Agg backend, fixed seed, PDF + PNG) and `scripts/make_numbers.py` -> `results/numbers.tex` macros (`\newcommand{\sysEtaskSuccess}{...}`) from JSON only.
- Stats: unit of analysis = task (trials averaged); paired bootstrap, 10,000 resamples, fixed seed, 95% CI; Holm correction across H1-H4; report effect sizes.
- `paper/main.tex` (+ `refs.bib` generated from `related_work.csv`). Sections: Abstract, Introduction, Related Work, Method, Experimental Setup, Results, Ablations, Threats to Validity (including R7), Conclusion, Reproducibility. `latexmk -pdf -interaction=nonstopmode` -> `paper/main.pdf`; no undefined refs or citations in the log.

### P10 Release and final verification
- `README.md` (setup, `make verify_all`, reproduction commands, expected runtime), `.env.example`, MIT `LICENSE`, `docs/FINAL_REPORT.md` (mode COMPLETE or DEGRADED, what was mocked, open items from TODO_HUMAN.md, citation verification status).
- Run `make verify_all`.

## 5. Pre-registered hypotheses (write into PREREG.md in P5)
- H1: E has a lower silent-error rate than A (noisy and oracle modes).
- H2: E's task success is non-inferior to C (margin 2 percentage points) with fewer questions.
- H3: E achieves higher task success than D at an equal or lower question budget (frontier comparison).
- H4: F has a lower silent-error rate than E, at a question-count cost of at most 0.25 questions per task.
Directions fixed now; if a hypothesis fails, report it as failed.

## 6. Artifact manifest (`docs/ARTIFACTS.md`; every item must exist and be cited in main.tex)
Figures: F1 pipeline architecture; F2 ConsensusGate flow; F3 ambiguity-type distribution; F4 task success vs questions; F5 silent-error rate by system; F6 disagreement distribution (ambiguous vs unambiguous); F7 tau_d calibration curve (DEV); F8 success by user mode; F9 p_amb sensitivity; F10 K ablation; F11 canary detection; F12 token/latency cost; F13 question precision.
Tables: T1 related work; T2 systems A-F, A2, R; T3 dataset statistics; T4 ambiguity taxonomy; T5 main results; T6 hypothesis tests; T7 per-mode results; T8 K ablation; T9 canary results; T10 cost.

## 7. Completion contract
`make verify_all` must exit 0 and do all of: backend tests pass; `npm run build` + typecheck pass; `check_security.py` clean; `check_lock.py` clean; `check_numbers.py` clean; same-seed rerun gives identical `results/metrics.json`; latexmk compiles with all F1-F13 and T1-T10 present and no undefined references; `docs/FINAL_REPORT.md` exists; `git status` clean.
Only then output exactly `<promise>CONSENSUSPROBE_COMPLETE</promise>`. If it cannot be met (missing latexmk, no network), set `status: blocked` with the blocker in STATE.md, finish everything else, and stop at the iteration cap. Never emit the promise falsely to escape the loop.
