# Human-Only Tasks and External Service Logs

This file tracks tasks requiring human intervention, missing local tools, or external services per Section 1 (HUMAN-ONLY TASKS).

---

## 1. CodeRabbit CLI
- **Status**: CodeRabbit CLI v0.9.2 is installed locally. Reviewing requires one-time OAuth authentication.
- **Action Taken**: Performing rigorous written self-reviews against the 7-point audit checklist for each phase per Section 3.
- **Human Action** (Optional): Run `coderabbit auth login` in a local terminal and authenticate in the browser if automated CodeRabbit cloud reviews are desired.

---

## 2. LaTeX Distribution (latexmk / pdflatex)
- **Status**: Not installed on host Windows machine.
- **Action Taken**: Phase 7 PDF results brief marked optional/degraded; metric data exported cleanly to `report/metrics.json`.
- **Human Action** (Optional): Install MiKTeX or TeXLive if local compilation of `results_brief.tex` is desired.

---

## 3. Production Deployment Approval
- **Status**: Production deployment strictly gated by presence of `docs/plans/APPROVE_PROD`.
- **Human Action**: Create `docs/plans/APPROVE_PROD` to authorize production deployment to Firebase live site.
