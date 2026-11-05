# Human-Only Tasks and External Service Logs

This file tracks tasks requiring human intervention, missing local tools, or external services per Section 1 (HUMAN-ONLY TASKS).

---

## 1. CodeRabbit CLI
- **Status**: CodeRabbit CLI (`coderabbit` / `cr`) is not installed on this local environment.
- **Action Taken**: Performing rigorous written self-reviews against security, determinism, logic, a11y, and backend-freeze categories for all phases (P0–P8).
- **Human Action** (Optional): If desired, install CodeRabbit CLI (`npm install -g coderabbit` or via official installer) and set `CODERABBIT_API_KEY`.

---

## 2. LaTeX Distribution (latexmk / pdflatex)
- **Status**: Not installed on host Windows machine.
- **Action Taken**: Phase 7 PDF results brief marked optional/degraded; metric data exported cleanly to `report/metrics.json`.
- **Human Action** (Optional): Install MiKTeX or TeXLive if local compilation of `results_brief.tex` is desired.

---

## 3. Production Deployment Approval
- **Status**: Production deployment strictly gated by presence of `docs/plans/APPROVE_PROD`.
- **Human Action**: Create `docs/plans/APPROVE_PROD` to authorize production deployment to Firebase live site.
