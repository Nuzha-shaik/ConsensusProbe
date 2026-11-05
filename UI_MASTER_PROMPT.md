# UI_MASTER_PROMPT: Impeccable UI upgrade + Google login (autonomous, resumable)

MISSION
Upgrade the UI of my existing, finished project and add a Google login page. Core logic is FROZEN. Today the app opens straight on the main page; after this work a signed-out user must always land on /login, and signing out must return to /login.
Stack (auto-detect, adapt if different): React + Vite + TS/JS, Tailwind, shadcn/ui, FastAPI backend, Makefile, git.

══════════════════════════════════════
1. OPERATING MODEL (Ralph loop)
══════════════════════════════════════
You are re-fed this same prompt every iteration with NO memory of previous iterations. Your memory is: git history + tags, UI_PROGRESS.md, docs/plans/P*.md. Never rely on conversation recall.
- One iteration = one GSD checklist item batch (max 3 items) OR one phase close. Then end the iteration with a one-line status.
- Never output the completion promise unless Section 11 is TRUE. Do not lie to escape the loop.
- Never `git push`, force-push, rewrite history, or delete tags/branches. Never run interactive commands. Never print or commit secrets.

══════════════════════════════════════
2. ITERATION PROTOCOL (run in this order, every iteration)
══════════════════════════════════════
a) REHYDRATE (cheap): `git status --short`, `git log --oneline -15`, `git tag -l "ui-*"`, then read ONLY UI_PROGRESS.md and the current phase's docs/plans/PN.md. Do not re-read the whole codebase.
b) RECOVER: if the working tree is dirty from a cut-off iteration: run `make ui_gate`. Passes → commit as `ui(PN): wip recovered`. Fails → `git restore .` (and remove untracked partial files from that item) back to last commit, then redo the item.
c) PICK the first unchecked item in UI_PROGRESS.md.
d) PLAN (GSD): if docs/plans/PN.md does not exist, run `/gsd-plan-phase` for that phase. The plan must be a checklist of ≤8 small items, each with: files touched, acceptance check. Execute items one by one, ticking each in PN.md immediately after it passes.
e) COMMIT after each item or small batch: `ui(PN): <what>`. Small commits are the checkpoints.
f) GATE after every batch: `make ui_gate` (and `make verify_all` if that target exists). Fix failures before anything else. Do not advance while red.
g) PHASE CLOSE (only when all items in PN.md are ticked): run `/coderabbit:review` (or `cr review`). Fix every critical/high finding (security, logic, auth bypass, determinism, a11y). Max 2 review-fix cycles; if CodeRabbit is unavailable or rate-limited, do a self-review against the same categories and log "coderabbit-unavailable" in UI_PROGRESS.md. Then gate again, commit, `git tag ui-PN-done`, tick the phase in UI_PROGRESS.md.
h) TOKEN DISCIPLINE: use grep/head/sed -n instead of dumping large files; never paste whole files back in chat; write progress BEFORE long operations; keep each file under ~300 lines by splitting components.
i) STUCK RULE: same item failing in 3 iterations → mark it BLOCKED in UI_PROGRESS.md with the reason, skip it, continue. Blocked and Deferred items are listed in the final report.

══════════════════════════════════════
3. HARD CONSTRAINTS (frozen core)
══════════════════════════════════════
Allowed: styling, layout, markup structure, UI components, design tokens, animation, and NEW auth/login files.
Forbidden: business logic, data processing, algorithms, API routes, request/response shapes, DB models, existing tests' expectations, existing handlers/props/state semantics.
Only these existing files may receive ADDITIVE edits for auth: app entry (providers), router (wrap routes), API client (attach Bearer header when logged in; on 401 → signOut). Record them in `.ui-allowlist`.
If a UI idea needs core-logic changes: skip it and list it under "Deferred".

MECHANICAL ENFORCEMENT: in P0, detect frozen paths (backend business logic, models, routes, migrations, tests, frontend hooks/stores/utils/api) and write them to `.ui-frozen-paths`. `make ui_gate` fails if `git diff --name-only pre-ui-upgrade` touches any frozen path not in `.ui-allowlist`.

══════════════════════════════════════
4. PLUGIN RULES
══════════════════════════════════════
- Ponytail (minimal code, YAGNI): smallest change that works. No new dependencies unless allowed below. Prefer platform features (CSS variables, native <dialog>, fetch, atob for JWT payload decode) over libraries. No abstractions for one use. Backend: standard library first.
  Allowed new deps ONLY: `@react-oauth/google`; one font package (fontsource) if fonts aren't self-hosted; `google-auth` (backend, lazily imported, only for optional token verification). Anything else needs a one-line justification in UI_PROGRESS.md and is otherwise rejected by the gate.
- Impeccable: run its teach/setup command ONCE in P1 (e.g. /teach-impeccable; use the closest equivalent in the installed version). Then use /audit, /critique, /normalize, /clarify, /polish, /harden, /adapt, /animate, /optimize at the points named in the phases. Respect its anti-pattern rules (no generic AI look: purple gradients, glassmorphism everywhere, nested cards, emoji icons, default-font-everything, centered-everything).
- GSD: every phase gets a docs/plans/PN.md checklist before code is written. No large unplanned code blocks.
- CodeRabbit: end of every phase (step 2g).
- Make: `make ui_gate` is the hard gatekeeper (Section 5). Add it additively; do not change existing targets.
- Git: branch `ui/impeccable-login`; commits `ui(PN): ...`; tags `ui-PN-done`; baseline tag `pre-ui-upgrade`.

══════════════════════════════════════
5. GATE: `make ui_gate` (create in P0, additive; implement in scripts/ui_gate.sh)
══════════════════════════════════════
Must run, fail-fast, and print PASS/FAIL per step:
1. Frontend: `npx tsc --noEmit` · lint (if script exists) · `npm run build` · `npm test` (if exists)
2. Backend: the existing test command (if any)
3. Baseline compare: failing tests must be a subset of those recorded in docs/ui/baseline.md
4. Core-freeze check (Section 3)
5. Secret scan: no `GOCSPX-`, no client secrets, `.env` not tracked
6. Production bundle must not contain the dev-mock marker `AUTH_DEV_MOCK`
7. Dependency budget: package.json / requirements diffs vs `pre-ui-upgrade` add only allowed packages
From P2 onward also run the auth route-guard tests (Section 7).

══════════════════════════════════════
6. PHASES (tick in UI_PROGRESS.md; each gets its own docs/plans/PN.md)
══════════════════════════════════════
P0 RECON + SAFETY: create branch, tag `pre-ui-upgrade`; run build/lint/tests and record the baseline in docs/ui/baseline.md; map entry, router, pages, shared components, API client, state, Tailwind/shadcn config, global CSS; list pages for P5 (one sub-phase per page: P5.1, P5.2...); create `.ui-frozen-paths`, `.ui-allowlist`, scripts/ui_gate.sh, Makefile target, UI_PROGRESS.md.
P1 DESIGN SYSTEM: Impeccable teach with context below; tokens as CSS variables wired into Tailwind + shadcn theme (color roles, type scale, spacing, radii, shadows, motion); font pairing (display + body + mono) with fallbacks and no layout shift; light + dark (system default + manual toggle persisted); /normalize base components (button, input, select, table, tabs, dialog, toast, badge, progress, empty state). Replace hard-coded colors/sizes with tokens, no logic edits.
P2 AUTH PLUMBING: Section 7.
P3 LOGIN PAGE: Section 8; run /critique and iterate once.
P4 APP SHELL: top bar or sidebar with wordmark, nav with clear active state, theme toggle, user menu (Google avatar with initials fallback, name, email, Sign out).
P5.x PER-PAGE RESTYLE (one page per iteration): /audit → /critique → /normalize → /clarify (labels, microcopy, errors) → /polish → /harden (skeleton loading, empty state with next action, error with retry, overflow/long content). Improve hierarchy, spacing rhythm, table density (sticky headers, subtle row separators, tabular numerals, mono IDs), charts, upload dropzone, progress/status, dialogs, toasts.
P6 CROSS-CUTTING: /adapt (360–1920px, touch targets ≥44px, tables scroll with affordance); /animate sparingly (150–250ms ease-out, no bounce, honor prefers-reduced-motion); WCAG AA contrast in both themes, focus order, aria, keyboard; /optimize (lazy-load heavy routes/charts, font loading, no layout shift); consistency sweep for leftover hard-coded values; remove dead CSS only if provably unused.
P7 OPTIONAL BACKEND VERIFICATION (flag OFF by default): FastAPI dependency in a NEW module that verifies the Google ID token (`google-auth`, audience = client ID), attached to existing routes ONLY when `AUTH_ENFORCE=true`. With the flag off, behavior is byte-for-byte unchanged. Add one test for each flag state.
P8 FINAL VERIFY: Section 9 checklist, README "Google OAuth setup", UI_FINAL_REPORT.md.

Impeccable design context (give to teach step):
- Product: research-grade data-cleaning / consensus-analysis tool for analysts and researchers.
- Personality: precise, calm, trustworthy, modern; dense information that is easy to scan.
- Audience: technical users, long sessions, mostly laptops, some tablets.
- Direction: distinctive but restrained identity; confident type pairing; tinted (not pure grey) neutrals in OKLCH; one strong accent; purposeful whitespace; clear hierarchy.

══════════════════════════════════════
7. AUTH SPEC (P2)
══════════════════════════════════════
- Google Identity Services via `@react-oauth/google`. Client ID from `VITE_GOOGLE_CLIENT_ID`. Any Google account may sign in; optional `VITE_ALLOWED_EMAIL_DOMAIN` (empty by default = no restriction).
- `AuthProvider` exposes: user {name, email, picture}, status (loading | authenticated | unauthenticated), signIn, signOut. Decode the ID token payload with atob (no JWT library). Store the minimum needed; check `exp` on load and on a timer; auto sign-out when expired.
- `ProtectedRoute` wraps every existing route. `/login` is public.
  * Signed out + any existing route → `/login`, remembering the intended path.
  * After login → intended path, else main page.
  * Signed in + `/login` → main page.
- SIGN OUT: clear auth state and stored tokens, call `google.accounts.id.disableAutoSelect()`, clear user-specific cached state, `navigate('/login', { replace: true })` so Back cannot reveal protected pages.
- API client: send `Authorization: Bearer <id_token>` only when logged in; 401 → signOut → /login. No other API changes.
- Missing `VITE_GOOGLE_CLIENT_ID`: no crash; the login page shows a clear setup message.
- Add `.env.example` (never real values).
- Testing without real Google: a dev-only mock provider guarded by `import.meta.env.DEV` and marked `AUTH_DEV_MOCK`, used only by route-guard tests (signed-out redirect, intended-path return, signed-in redirect from /login, sign-out → /login with replace, expired token → /login). Use the existing test runner; if there is no frontend runner, write the checks as a documented manual script instead of adding a framework.

══════════════════════════════════════
8. LOGIN PAGE SPEC (P3)
══════════════════════════════════════
- Desktop: split layout. Left = brand panel (wordmark, one-line value proposition, subtle abstract data motif relevant to the product; no stock-illustration clichés). Right = sign-in panel. Mobile: single column, compact brand on top.
- Sign-in panel: product name, short welcome line, ONE primary "Continue with Google" button (official Google "G" mark, correct proportions), small privacy/terms line. No email/password.
- States: idle, hover, focus-visible, loading (spinner, disabled), error with human message + retry, popup blocked/cancelled, offline, missing client ID.
- Gentle entrance animation and press feedback; honor prefers-reduced-motion.
- Accessibility: landmarks, labelled button, visible focus, AA contrast, full keyboard use, errors announced via aria-live.

══════════════════════════════════════
9. FINAL VERIFICATION (P8). Report each as PASS/FAIL
══════════════════════════════════════
1 Fresh visit signed out → /login
2 Deep link signed out → /login → after login returns to that page
3 Google sign-in with a regular Gmail account → main page (manual step if no credentials are available; mark "needs human" honestly)
4 Refresh while signed in → stays signed in
5 Sign out → /login; Back does not reveal protected pages
6 Expired/invalid token → /login
7 All original features behave identically (tests equal or better than baseline)
8 Light/dark × mobile/tablet/desktop look right (before/after screenshots if Playwright or a browser tool is available)

══════════════════════════════════════
10. BLOCKERS
══════════════════════════════════════
- A missing Google client ID is NOT a blocker: build everything against the placeholder and document the setup (Cloud Console → OAuth Client ID, type Web application → Authorized JavaScript origins: http://localhost:5173 + production URL → consent screen "External" so any Google account works → paste ID into .env).
- Real Google sign-in cannot be automated; mark check 3 as "needs human" rather than faking it.

══════════════════════════════════════
11. COMPLETION CONDITIONS (ALL must be true)
══════════════════════════════════════
- Every phase in UI_PROGRESS.md is ticked or explicitly BLOCKED/Deferred with a reason.
- `make ui_gate` (and `make verify_all` if present) passes on the final commit.
- Tags ui-P0-done … ui-P8-done exist (for phases not blocked).
- UI_FINAL_REPORT.md exists: design decisions (fonts, palette, tokens), files added/changed, new env vars, Google setup steps, results vs baseline, Deferred/Blocked list, the exact run command.
Only then output exactly: <promise>UI_LOGIN_COMPLETE</promise>
