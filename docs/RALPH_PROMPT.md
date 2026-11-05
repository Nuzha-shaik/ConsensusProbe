<USER_REQUEST>
/ralph-loop "Read docs/RALPH_PROMPT.md fully and follow it exactly. Resume from repo state." --max-iterations 90 --completion-promise "CONSENSUSPROBE_2_COMPLETE"
MISSION: ConsensusProbe 2.0 Showcase Add-On (Visual Multi-Agent Command Center)

CONTEXT
ConsensusProbe is ALREADY BUILT and deployed (React + Vite + TypeScript frontend in frontend/, a frozen backend, Firebase hosting at ai-powered-multi-agents.web.app, scripts/ui_gate.py, tokens in frontend/src/styles/tokens.css). This is an ADD-ON. Never rewrite working features; extend them. Existing tabs, routes and behavior must keep working.

The research engine: a K=3 candidate plan ensemble, pairwise semantic disagreement d, canary integrity checks, and a human gate that fires only when mean d > tau_d. Today it is invisible: the UI shows a generic upload form and a number like d = 0.0000. Goal: make the engine the visible product. A stranger must understand it in 10 seconds and trust it in 60.

====================================================================
SECTION 1. THE LOOP CONTRACT (you are inside /ralph-loop)
====================================================================
You are re-invoked with this same prompt every iteration. You have no memory except the repo. So every iteration:

1. ORIENT (always first, never skip):
   - Read docs/plans/STATE.md (create it in iteration 1 if missing).
   - Run: git status; git log --oneline -15; git tag --list "cp2-*"
   - Find the current phase = first phase without a tag cp2-phaseN-done.
   - Open docs/plans/P{N}.md and find the first unticked checklist item.
   - Run `make gate` (after Phase 0 creates it) to learn the real current state. Trust test output over your notes.
2. DO ONE UNIT of work: exactly one checklist item (or a tightly coupled pair). Small diffs. No giant code blocks.
3. VERIFY: run `make gate`. If red, fix it this iteration. Never leave the repo red at the end of an iteration.
4. COMMIT: `git add -A && git commit -m "cp2(P{N}.{k}): <what>"`. Tick the checklist box in the same commit.
5. UPDATE docs/plans/STATE.md: current phase, last item done, next item, open risks. Keep it under 40 lines.
6. END YOUR TURN. The loop restarts you. Do not try to do the whole project in one iteration.

STUCK RULE: if the same item fails 3 iterations in a row, write docs/plans/BLOCKED.md (what you tried, exact error, hypotheses), mark the item "[!]" in the checklist, and move to the next independent item. If everything remaining is blocked, finish the iteration with a clear BLOCKED summary and do NOT output the completion promise.

HONESTY RULE FOR THE PROMISE: output <promise>CONSENSUSPROBE_2_COMPLETE</promise> ONLY when every item in Section 9 is verifiably true right now. Never output it to escape the loop, to save iterations, or because you are tired. A false promise is the worst possible failure.

HUMAN-ONLY TASKS: anything you cannot do autonomously (missing API keys, missing ffmpeg/latexmk, Firebase login, CodeRabbit not installed) goes into docs/plans/HUMAN_TODO.md with exact commands. Never fake the result. Never block the loop waiting on a human.

====================================================================
SECTION 2. HOW TO USE EACH TOOL (mandatory)
====================================================================
GSD (/gsd-plan-phase)
- At the START of each phase, run /gsd-plan-phase and write docs/plans/P{N}.md.
- Format per item: `- [ ] P{N}.{k} <title> | files: <paths> | acceptance: <observable check> | verify: <command>`
- Max 12 items per phase; each item <= ~200 changed lines. Execute strictly in order. Tick boxes only when the verify command passes.
- Never start phase N+1 planning before phase N is tagged done.

PONYTAIL (coding constraints, YAGNI)
- Write the minimum code that satisfies the acceptance check. No speculative features, options, layers or abstractions. No abstraction until it has 2 real call sites.
- ZERO new runtime npm dependencies. Prefer platform APIs: Web Crypto (SHA-256), Web Worker, TextDecoder (encoding detection), native <dialog> (focus trap), <details>, CSS custom properties, hand-rolled SVG for gauge / histograms / Sankey (4 flows), simple fixed-row-height windowing for virtualization. First check package.json: REUSE libraries the app already has before writing anything new.
- Allowed new devDependencies only: vitest, @playwright/test, @axe-core/playwright. Lighthouse runs via `npx` on demand, not installed. Justify any other addition in docs/plans/DEPS.md or do not add it.
- Python scripts (scripts/): standard library only (argparse, csv, json, hashlib, random with fixed seed, subprocess, pathlib).
- Component files under ~150 lines, one responsibility. Pure logic (diff, health score, histograms, gate re-evaluation, hashing, change-log) lives in frontend/src/lib/ or frontend/src/adapters/ as pure functions with unit tests.
- Delete dead code you create. No commented-out code. No TODO without an entry in HUMAN_TODO.md.

CODERABBIT (/coderabbit:review or `cr review`)
- Run at the END of every phase, after `make gate` is green and before tagging.
- Fix every critical/high finding (security, determinism, logic, a11y, backend-freeze violations). For medium/low: fix if cheap, otherwise list in docs/plans/P{N}-review.md with a one-line reason.
- Max 2 review-fix cycles per phase. Save the summary to docs/plans/P{N}-review.md.
- If CodeRabbit is unavailable, perform a written self-review against the same categories, record "CodeRabbit unavailable" in the review file and in HUMAN_TODO.md, then continue.

MAKE (the hard gatekeeper, no exceptions)
Create or extend the Makefile in Phase 0 with these targets:
- make freeze      -> python scripts/core_freeze_check.py
- make guards      -> python scripts/token_check.py && python scripts/no_literals_check.py
- make typecheck   -> cd frontend && npx tsc --noEmit
- make test        -> cd frontend && npx vitest run
- make build       -> cd frontend && npm run build
- make ui_gate     -> python scripts/ui_gate.py
- make gate        -> freeze + guards + typecheck + test + build + ui_gate (fast; run every iteration)
- make e2e         -> Playwright full demo flow on both samples + axe-core
- make perf        -> Lighthouse on the built app (performance >= 90, accessibility >= 90)
- make verify_all  -> gate + e2e + perf + docs check
You may NOT advance past a phase until `make gate` exits 0. You may NOT finish the project until `make verify_all` exits 0.

GIT (checkpointing and resume)
- First iteration: `git tag pre-cp2` on the current HEAD if it does not exist (this is the freeze baseline). Create and work on branch feat/cp2-showcase.
- One commit per checklist item. When a phase passes gate + review: `git tag cp2-phase{N}-done`.
- Resume logic is ALWAYS derived from tags + STATE.md + checklist, never from memory. If the working tree is dirty at the start of an iteration, inspect `git diff` and either finish or `git stash`/revert the half-done item cleanly.
- Never force-push. Never rewrite published history. Never touch main directly.

VITE / TSC
- `tsc --noEmit` must show 0 errors and `npm run build` must succeed at the end of every iteration. No `any` escape hatches, no @ts-ignore without a justification comment and a HUMAN_TODO entry.

LATEXMK (optional evidence PDF, Phase 7)
- Used only to compile a short results brief from real, computed metrics (see Phase 7). If latexmk is missing, skip and log in HUMAN_TODO.md.

====================================================================
SECTION 3. NON-NEGOTIABLE RULES
====================================================================
R1 CORE FREEZE. Do not modify backend models, routes, algorithms or API contracts. Writable paths ONLY: frontend/, scripts/, docs/, Makefile, README.md, .github/, report/, and firebase config only if needed for the preview channel. If a feature needs data the API does not expose, derive it on the client or show it as unavailable. Never edit the backend to get it.
R2 TRUTHFUL UI. No hard-coded metrics anywhere. Every number, score, badge and status is computed from the actual run result. If it cannot be computed, show an em dash "—" with a tooltip explaining why. Headline numbers from old mockups (58% to 98.4%, 94.2%, 100% canaries) are FORBIDDEN as literals. Add a unit test that mutates the fixture run and asserts the displayed numbers change.
R3 REAL AGENT STATE. Agent statuses, traces, timings, token counts and model names come from real run data. If the API provides no trace, build the timeline from the run summary and label it "Reconstructed from run summary". NEVER invent reasoning text. Pulse animation only while an agent is actually running.
R4 NO HARD-CODED MODELS. Display exactly the model identifiers the run reports. Use a config-driven registry (frontend/src/config/modelRegistry.ts) keyed by provider-family pattern for icon and color only; the label is always the raw reported identifier. Unknown id -> raw string + generic icon. A deterministic mock is labelled "Deterministic research mock" and is never styled as an LLM. Show an "Independent auditor" indicator only when proposer and auditor model ids differ.
R5 DESIGN SYSTEM. Colors only from tokens.css via CSS variables, dark and light themes both. No hex/rgb/hsl literals outside tokens.css (enforced by scripts/token_check.py). If a needed token is missing (e.g. agent cyan/indigo/emerald/amber/rose), ADD it to tokens.css for both themes with AA contrast. Diff states always use icons or patterns in addition to color (edited = pencil icon, dropped = strike-through + minus icon, imputed = fill icon + dotted pattern).
R6 ACCESSIBILITY. WCAG AA contrast; full keyboard operation (a visible Browse button alongside drag-and-drop); aria-live="polite" for agent status; focus trap + Escape + focus return in the clarification modal; prefers-reduced-motion respected for every animation and count-up.
R7 ADDITIVE ONLY. Put new code in new files/folders (frontend/src/adapters, components/showcase, lib, workers). Edit existing files minimally and only to mount new components. Run `make gate` before and after touching any existing file. No regressions in ui_gate.py versus the baseline recorded in Phase 0.
R8 NO FAKE SUCCESS. Never weaken a test, raise a threshold, or edit the freeze/token/literal guards to make a gate pass. Fix the cause.
R9 TUNE DATA, NOT THRESHOLDS. For samples, adjust the sample data (never tau_d) until the clean file stays <= tau_d and the contested file crosses > tau_d on the REAL pipeline (or the deterministic mock if that is the only runnable mode; record which in the README and HUMAN_TODO.md).

====================================================================
SECTION 4. PHASES
====================================================================

PHASE 0: RECON AND GUARDRAILS (no user-facing features yet)
Goal: know exactly what data exists, lock the freeze, create the gates.
- Read: frontend structure, API client, response types, tokens.css, scripts/ui_gate.py, package.json, firebase.json, existing Makefile (if any).
- Create docs/DATA_AVAILABILITY.md. For each, name the existing API field or mark MISSING: original rows, cleaned rows, 3 candidate plans and their per-cell edits, pairwise d values, mean d, tau_d, gate decision, canary results (planted/expected/observed), model identifiers (proposer/auditor), mock-vs-live indicator, timings, token usage, any existing human-clarification endpoint.
- Create scripts/backend_paths.txt (list of backend paths found), scripts/core_freeze_check.py (fails if `git diff --name-only pre-cp2` touches any of them or anything outside the writable paths in R1), scripts/token_check.py, scripts/no_literals_check.py (flags forbidden literals like 98.4, 94.2, 58% in frontend/src).
- Create the Makefile targets from Section 2. Record baseline output of ui_gate.py in docs/plans/BASELINE.md.
- Add vitest + Playwright config (devDependencies only). Add fixtures: frontend/src/adapters/__fixtures__/ with one real captured run response (sanitized).
- Create frontend/src/adapters/runViewModel.ts: one RunViewModel type + adapter(apiResponse) -> RunViewModel, with unavailable fields typed as { available: false, reason: string }. All new components read ONLY from RunViewModel.
- Pure functions + unit tests: diffRuns, healthScore (weights in one exported constant), histograms, gateDecision(d, tau) with strict ">" boundary.
Acceptance: make gate green, baseline recorded, DATA_AVAILABILITY.md complete.

PHASE 1: INGESTION AND HERO
- Hero: one-line pitch "Three AI cleaners propose. A supervisor measures disagreement. A human decides only when it matters." Under it a pipeline strip (Ingest, Propose, Audit, Gate, Result) that is real progress navigation, driven by run state, keyboard focusable.
- Dropzone: animated sky-blue border and "Drop to Ingest" on drag-over, visible Browse button, keyboard operable. Before upload show file name, size, MIME type, estimated rows and columns, delimiter, detected encoding, and first-rows preview. Reject unsupported/oversized files with a clear message (limits in one config constant).
- Parse in a Web Worker (frontend/src/workers/parseWorker.ts): encoding detection (BOM + TextDecoder fallback), delimiter detection, large-file sample preview.
- scripts/make_samples.py (stdlib, fixed seed): writes frontend/public/samples/retail_clean.csv, customers_contested.csv and a ground-truth JSON for each (true value per injected-error cell). Inject: typos, mixed date formats including ambiguous 03/04/2026, negative stock, nulls, duplicates, casing variants, ambiguous abbreviations. Clean file = mostly clean, few unambiguous errors. Contested file = many genuinely ambiguous cells.
- Buttons "Try a clean file" and "Try a contested file" (one click -> ingest -> run).
- Run both through the real pipeline and tune data per R9. Record resulting d and tau_d in the README at the end (from real runs, not typed from memory).
Acceptance: both samples load in <= 2 s locally; drag-drop, Browse and keyboard all work; e2e smoke test for ingestion passes.

PHASE 2: SWARM PIPELINE AND GATEKEEPER
- Section above the workspace with three agent cards: Cleaner (cyan, "Generated 3 candidate plans"), Supervisor (indigo, "Mean disagreement d = X.XXXX" + canary audit result), Gatekeeper (emerald "Auto-approved" or amber "Human clarification engaged"). Statuses from run data only (R3).
- Model badge on each card (R4) + "Independent auditor" indicator + clear mode label (live LLM vs "Deterministic research mock").
- Expandable Agent Trace timeline: per-agent latency, tokens, estimated cost where available (em dash otherwise), collapse control, Replay button that replays recorded timestamps only. Label "Reconstructed from run summary" when applicable.
- Threshold simulator: slider for tau_d re-evaluating gateDecision from the stored d; shows the exact flip value; display only; never mutates the stored run. Unit-test the boundary.
- Canary audit panel: each planted canary with expected, observed, pass/fail (or "unavailable" with reason).
- Human clarification card/modal, only when d > tau_d: one plain-language question per contested group (group = same column + same disagreement type; question text built from the actual plan proposals), options with live impact preview ("Choosing A changes N rows", N computed), "apply to similar cells" toggle (similar = same column + same value pattern), number-key shortcuts, focus trap. Record every decision (timestamp, group, option, scope) in a decisions store for the certificate. If no backend clarification endpoint exists (see DATA_AVAILABILITY.md), apply decisions client-side to the review/export layer and say so in the UI: "Applied to export; backend run unchanged."
Acceptance: clean sample shows Auto-approved; contested shows the clarification card; slider flips at the right d; keyboard-only path works.

PHASE 3: RESULTS
- View toggle: Unified Diff | Side-by-Side | Disagreement Heatmap (state kept in URL hash).
- Unified: edited cells with original value in tooltip; dropped rows struck through with "Dropped" badge; imputed nulls with "Imputed" badge (R5 icons/patterns).
- Side-by-side: original left, cleaned right, sticky headers, synchronized scrolling.
- Heatmap: tint by agreement (unanimous 3/3, majority 2/3, fully split 1/1/1). Clicking a contested cell opens a popover with Plan A, B, C proposals and which won. If per-plan edits are MISSING, show the unavailable state, do not fake.
- Review queue: accept / reject / undo per change, filters (changed-only, contested-only), next/previous change shortcuts, exports reflect decisions.
- Virtualized table (fixed row height windowing) smooth at 50,000 rows (add a unit/perf test with a generated 50k-row fixture). Legend, per-column change counts, empty / loading / error states.
Acceptance: all three views render both samples; contested-cell popover works; 50k fixture scrolls without long tasks over budget.

PHASE 4: ANALYSIS TAB
New top-level Analysis tab containing:
a) Data Health Score radial gauge (hand-rolled SVG), before and after. Tooltip shows the formula: 100 x (0.35 completeness + 0.25 validity + 0.20 uniqueness + 0.20 consistency). Completeness = non-null cells / all cells. Validity = values matching inferred column type. Uniqueness = 1 - duplicate row share. Consistency = values matching the column's dominant format and casing. Weights in one exported constant (configurable).
b) Metric cards: Missing Values Recovered (imputed / originally null), Contested Cells Resolved (auto + human), Canaries Intercepted (caught / planted), Silent Error Reduction (only when ground truth exists, otherwise "Needs ground truth").
c) Before/after histograms for numeric columns, frequency bars for categorical, with a column selector.
d) Row-flow Sankey: kept, edited, imputed, dropped (hand-rolled SVG).
e) Ablation panel (ground-truth samples only): single plan (each of A, B, C) vs K=3 consensus: error rate, precision, recall of changes, computed against the ground-truth JSON. Unavailable state for user files.
Acceptance: unit tests for every formula with hand-computed expected values; numbers change when the file changes.

PHASE 5: PROVENANCE AND EXPORT
- Certificate (JSON + printable view): SHA-256 (Web Crypto) of input and output files, plan hashes, d, tau_d, gate decision, canary results, model identifiers, run timestamps, every human decision, app version, and the mode label.
- Exports: cleaned CSV, change-log CSV (cell, before, after, source plan, auto/human, accepted/rejected), and a reproducible cleaning recipe only if the run data supports it (else unavailable with reason).
- One-click self-contained HTML report (single file, inlined CSS/data, no network calls).
- Test: hash of the exported CSV recomputed in a unit test equals the certificate hash.
Acceptance: certificate hashes match exported files byte for byte.

PHASE 6: POLISH
- Five-step guided tour on first visit (dismissible, skippable, stored in localStorage, replayable from the palette).
- Ctrl/Cmd+K command palette (jump to views, tabs, samples, exports, theme toggle).
- Skeleton loaders, count-up numbers (disabled under reduced motion), responsive layout down to 360 px (no horizontal page scroll), Open Graph preview image (static, generated by a stdlib script or a committed asset) and meta tags.
- Privacy note stating EXACTLY what happens to uploaded files. Read the code to find where files go (browser only vs sent to backend/LLM provider). Claim "stays in your browser" ONLY if the code truly does that.
Acceptance: tour, palette, theme toggle and 360 px layout all verified by Playwright.

PHASE 7: VERIFY
- Playwright full demo flow on both samples (landing -> ingest -> swarm -> gate -> results views -> contested popover -> analysis -> certificate download). Dark and light run, keyboard-only run, 360 px run.
- axe-core: 0 serious/critical violations. Lighthouse (make perf): performance >= 90, accessibility >= 90.
- README update: pitch, demo GIF of the 60-second flow (Playwright video/screenshots -> GIF; if ffmpeg is missing, commit screenshots and log HUMAN_TODO), screenshots, architecture diagram (Mermaid), how each metric is computed, how to run the samples, honest "what is unavailable and why".
- OPTIONAL (only if latexmk exists): scripts/make_report_tex.py (stdlib) reads report/metrics.json (exported from the real sample runs: d, tau_d, gate decisions, ablation numbers) and fills report/results_brief.tex; run `latexmk -pdf -interaction=nonstopmode report/results_brief.tex`. Every number in the PDF comes from metrics.json.
- Run `make verify_all`. Must exit 0.

PHASE 8: SHIP
- Push branch feat/cp2-showcase to origin.
- Deploy to a Firebase preview channel: `firebase hosting:channel:deploy cp2-preview --expires 7d`. Capture the URL in docs/plans/DEPLOY.md. Run Playwright against it (BASE_URL=<preview url>); must pass.
- PRODUCTION: only if the file docs/plans/APPROVE_PROD exists. Then run `firebase deploy --only hosting`, confirm https://ai-powered-multi-agents.web.app serves the same build as the preview (compare asset hashes or version string), run Playwright against production. If APPROVE_PROD does not exist, write the exact commands to HUMAN_TODO.md and treat production as "pending human approval".
- Open a PR (do not merge unless told to). Final report in docs/plans/FINAL_REPORT.md: what shipped per phase, everything marked unavailable and why, test results, links, HUMAN_TODO summary.

====================================================================
SECTION 5. PHASE-END RITUAL (every phase, in order)
====================================================================
1. All checklist items ticked (or "[!]" with BLOCKED.md entry).
2. `make gate` exit 0 (and `make e2e` for phases 1 through 6 where e2e tests exist).
3. CodeRabbit review -> fix critical/high -> save docs/plans/P{N}-review.md.
4. `make freeze` re-run explicitly. Backend diff must be empty.
5. Append a phase report to docs/plans/STATE.md: shipped, unavailable-and-why, test results.
6. `git tag cp2-phase{N}-done`, then end the iteration. Next iteration begins the next phase with /gsd-plan-phase.

====================================================================
SECTION 6. WHAT "UNAVAILABLE" LOOKS LIKE
====================================================================
Em dash "—" + accessible tooltip/aria-label stating the missing field and why (e.g. "Token usage not reported by the API"). Never a zero, never a plausible-looking default, never a placeholder number.

====================================================================
SECTION 7. WHAT YOU MUST NEVER DO
====================================================================
- Edit backend files, routes, models, or API contracts.
- Add runtime dependencies, UI kits, chart libraries or state libraries unless already present in the app.
- Hard-code metrics, model names, agent reasoning or colors.
- Skip, loosen or delete a gate, test or guard.
- Run more than one checklist item per iteration, or leave the repo red.
- Merge to main, force-push, or deploy to production without APPROVE_PROD.
- Output the completion promise unless Section 9 is fully true.

====================================================================
SECTION 8. FIRST ITERATION CHECKLIST
====================================================================
If docs/plans/STATE.md does not exist: create it, tag pre-cp2, create branch feat/cp2-showcase, run /gsd-plan-phase for Phase 0, write docs/plans/P0.md, and end the iteration after completing its first item.

====================================================================
SECTION 9. DEFINITION OF DONE (all must be verifiably true)
====================================================================
[ ] A new visitor can state what the project does within 10 seconds of the landing page (pitch + pipeline strip + two sample buttons visible above the fold at 1280x720 and 360x640).
[ ] Both samples run end to end; the clean file auto-approves, the contested file triggers the human gate.
[ ] Every number on screen changes when a different file is uploaded; no_literals_check and the mutation test pass.
[ ] Clicking any contested cell shows what all three plans proposed (or an honest unavailable state if the API lacks per-plan edits).
[ ] The threshold slider flips the gate at exactly d = tau_d (strict >), unit-tested.
[ ] Certificate hashes match the exported files, unit-tested.
[ ] `git diff pre-cp2 --name-only` shows no backend path; `make freeze` passes.
[ ] `make verify_all` exits 0: tsc 0 errors, build OK, ui_gate 0 type errors and 0 regressions vs BASELINE.md, Playwright (both samples, dark/light, keyboard, 360 px) passes, axe 0 serious/critical, Lighthouse performance and accessibility >= 90.
[ ] CodeRabbit (or documented fallback) completed for every phase with no unresolved critical/high findings.
[ ] Preview channel deployed and Playwright passes against it; production deployed and matching only if APPROVE_PROD existed, otherwise commands are in HUMAN_TODO.md.
[ ] README has the pitch, demo GIF (or screenshots + HUMAN_TODO note), architecture diagram, metric formulas and sample instructions.
[ ] docs/plans/FINAL_REPORT.md written.

When, and only when, every box above is true, output exactly:
<promise>CONSENSUSPROBE_2_COMPLETE</promise>
</USER_REQUEST>
<ADDITIONAL_METADATA>
The current local time is: 2026-11-06T00:37:08+05:30.
</ADDITIONAL_METADATA>
<USER_SETTINGS_CHANGE>
The user changed setting `Model Selection` from Gemini 3.8 Flash (High) to Claude Opus 4.6 (Thinking). No need to comment on this change if the user doesn't ask about it. If reporting what model you are, please use a human readable name instead of the exact string.
</USER_SETTINGS_CHANGE>