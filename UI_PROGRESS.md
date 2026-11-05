# UI Upgrade & Google Login Progress Tracker

## Phase Overview

- [x] **P0: Recon & Safety Harness** (baseline recorded, frozen paths locked, ui_gate operational)
- [x] **P1: Design System & Tokens** (Impeccable teach context, design tokens in Tailwind, base components normalized)
- [x] **P2: Auth Plumbing** (`@react-oauth/google`, `AuthProvider`, `ProtectedRoute`, router guards, bearer headers)
- [x] **P3: Login Page** (desktop split layout, Google button, loading/error states, AA contrast)
- [x] **P4: App Shell** (header wordmark, clear active nav states, theme toggle, user menu)
- [x] **P5: Per-Page Restyle**
  - [x] P5.1 Dashboard Overview
  - [x] P5.2 Dataset Upload
  - [x] P5.3 Data Profiler
  - [x] P5.4 ConsensusGate Workspace
- [x] **P6: Cross-Cutting Polish** (responsive 360-1920px, accessibility WCAG AA, smooth transitions)
- [ ] **P7: Optional Backend Verification** (flagged `AUTH_ENFORCE=false` by default, token validation dependency)
- [ ] **P8: Final Verification & Release** (Section 9 checklist, README OAuth setup, UI_FINAL_REPORT.md)

## Blocked Items
- None

## Deferred Items
- None

## Log of Reviews & Notes
- `2026-11-05`: P0 completed. Baseline recorded in `docs/ui/baseline.md`. Mechanical core-freeze enforcement via `.ui-frozen-paths` and `.ui-allowlist`. CodeRabbit CLI unavailable on host; self-reviewed against security, core logic freeze, and determinism.
- `2026-11-05`: P2 & P3 completed. Auth context with atob JWT decoding, automatic 401 signout, Bearer token injection, and dedicated split-screen login page. Self-reviewed against security, auth bypass, determinism, and WCAG AA contrast. (coderabbit-unavailable).
- `2026-11-05`: P4 completed. Restyled App Shell with crisp ConsensusProbe wordmark, active navigation pill indicator, dark/light theme toggle, and user menu with initials circle and explicit Sign Out button. (coderabbit-unavailable).
- `2026-11-05`: P5 completed. Restyled Dashboard Overview, Dataset Upload, Data Profiler, and ConsensusGate Workspace with high-contrast design tokens, dark/light modes, tabular mono numerals, and accessible form elements. (coderabbit-unavailable).
- `2026-11-05`: P6 completed. Cross-cutting polish: prefers-reduced-motion media query, visible focus-visible outline rings, touch targets >= 44px, and responsive layouts across viewports. (coderabbit-unavailable).

