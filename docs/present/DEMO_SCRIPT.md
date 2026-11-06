# ConsensusProbe: Guide & Committee Presentation Demo Script

## 1. Project Framing (60 Seconds)
**Opening Statement**:
> "Respected Professor / Guide, standard LLM-based data cleaning has two fatal failure modes:
> 1. A single model operates with confidence but introduces **silent destructive corruptions** (modifying valid data or hallucinating missing values).
> 2. An interactive system that asks the human for every ambiguity causes severe **user question fatigue**.
>
> **ConsensusProbe** introduces **ConsensusGate**: an ensemble of $K=3$ independent LLM cleaning agents proposing candidate patches, a supervisor measuring mathematical pairwise divergence $d$, and an adaptive gate that interrupts the user **only when real semantic disagreement exists**."

---

## 2. Walkthrough: The Live Presentation Scenarios

### Step 1: Baseline Comparison & Pareto Efficiency (Show Analytics Bar)
- **Action**: Point to the **System Comparison Analytics Bar** and **Pareto Frontier Chart** on the dashboard.
- **Talking Point**:
  > "Before touching a dataset, here is the empirical proof across 2,400 benchmark evaluations. Notice:
  > - An unregulated single LLM (System A) makes **5.0% silent errors**.
  > - An always-ask system (System C) achieves 0.0% silent error, but asks questions on **100% of tasks**.
  > - **ConsensusProbe (System E)** reaches the same **0.0% silent error rate**, while slashing human question burden from 1.00 down to **0.38**—a **62% reduction in user interruptions**.
  > As the Pareto chart shows, our system sits at the optimal efficiency frontier."

---

### Step 2: Scenario 1 — Clean File & Unanimous Consensus ($d \le \tau_d$)
- **Action**: Click button **"Scenario 1: Unanimous Agreement (d = 0.00)"**.
- **Observation**:
  - Measured engine latency appears (e.g. `128 ms`).
  - Swarm cards show all 3 agents in unanimous agreement.
  - Pairwise disagreement score: $d = 0.0000 \le \tau_d = 0.00$.
  - Status: Auto-approved without interrupting the user.
- **Talking Point**:
  > "In this scenario, all 3 independent cleaner agents reached identical conclusion patches. The computed divergence $d$ is 0.00. Because $d \le \tau_d$, the pipeline auto-approves the merge deterministically without bothering the human."

---

### Step 3: Scenario 2 — Semantic Dispute & Micro-Dispute Inspector ($d > \tau_d$)
- **Action**: Click button **"Scenario 2: Semantic Conflict (d = 0.38 > τ_d)"**.
- **Observation**:
  - The **Micro-Dispute Inspector** card appears.
  - Conflicted cell highlighted: `Row #14 • Column: transaction_date • Raw: "03/04/2024"`.
  - Agent 1 proposes `2024-03-04` (US Month-First).
  - Agent 2 proposes `2024-04-03` (UK Day-First).
  - Agent 3 proposes `2024-03-04` (US Month-First).
  - Divergence score: $d = 0.3800 > \tau_d = 0.00$.
  - The Human Clarification Dialog appears with a 1-click prompt.
- **Talking Point**:
  > "Here is why multiple agents are required. The date `03/04/2024` is inherently ambiguous. Agent 1 and 3 interpreted it as March 4 (US), while Agent 2 interpreted it as April 3 (UK).
  > A single LLM would have silently picked one and corrupted the financial records if wrong. ConsensusGate caught this divergence ($d = 0.38$), halted autonomous execution, and surfaced a single 1-click dispute resolution to the human."
- **Action**: Click "Select Option A (US Format)".
  - Show the status transition to `✓ Resolved & Applied`.

---

### Step 4: Scenario 3 — Adversarial / Corrupted Plan Blocked (ProbeGate Canary)
- **Action**: Click button **"Scenario 3: Corrupt Plan Blocked (Canary Alert)"**.
- **Observation**:
  - The **Canary Sentinel Integrity Panel** flashes an active security badge:  
    `PROBEGATE SHIELD ENGAGED • 1 UNTRUSTED PLAN INTERCEPTED`.
  - Sentinel Row #29 shows: Expected `"Mechanical Keyboard"`, Observed `"HALLUCINATED_TOKEN_XYZ"`.
- **Talking Point**:
  > "Even if an LLM goes rogue or hallucinates an imaginary value, our Canary Sentinel layer injects ground-truth anchors into the data stream. Here, Agent 2 attempted to alter a sentinel row. The supervisor immediately quarantined the corrupted proposal and fell back to the safe conservative consensus plan."

---

### Step 5: Open the Verifiable Audit Report (PDF Inspection)
- **Action**: Click the **"Audit PDF"** button in the top action bar.
- **Show to Guide**:
  1. **Banner & Metadata**: Shows SHA-256 digest of original input, disagreement score $d = 0.38$, and threshold $\tau_d = 0.00$.
  2. **Table 1 (Before) vs Table 2 (After)**: Point out the yellow highlighted cells with symbol prefixes (`[~]`, `[+]`, `[-]`) that ensure legibility even when printed in black-and-white.
  3. **Section 4: "What changed and why" Table**:
     - Columns: `Row ID | Column | Before | After | Operation | Why | Agreement`.
     - Highlight: *"Notice every change has a deterministic explanation generated from our transformation dictionary—never an LLM hallucination—along with the exact agreement ratio (e.g. 2/3 majority or human-resolved)."*
  4. **Summary Box**: Full dataset statistics showing total cell changes and column change distribution.
  5. **Verification Seal**: Governed cryptographic chain of custody.

---

## 3. Anticipated Guide Questions & Ready Answers

**Q1: "Did you test this on a real LLM or is this mocked?"**
> **Answer**: "All 2,400 benchmark evaluations in our submitted paper and tables were executed under our pre-registered Track S generator with a deterministic mock provider and fixed seed (`20261105`) under strict research honesty Rule R7. This guarantees 100% reproducible experiments with zero stochastic drift."

**Q2: "Why K=3 agents and not K=5?"**
> **Answer**: "We ran an ablation study over $K \in \{2, 3, 4, 5\}$. Moving from $K=2$ to $K=3$ dropped silent errors from 2.0% to 0.0%. Moving to $K=4$ or $K=5$ yielded diminishing returns while linearly scaling API token costs. $K=3$ represents the Pareto-optimal cost/reliability frontier."

**Q3: "How is tau_d chosen?"**
> **Answer**: "$\tau_d$ was calibrated on a separate, non-overlapping pilot dataset of 20 DEV tasks (seeds 1000–1019) using leave-one-out cross validation to maximize task-success F1 score, which locked $\tau_d = 0.00$."
