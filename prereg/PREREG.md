# Pre-Registration Plan: ConsensusProbe Benchmark

## 1. Study Overview
This pre-registration specifies the experimental evaluation of ConsensusGate (System E) and CanaryGate (System F) against baseline cleaning systems (A, A2, B, C, D, R) on the Track S retail/inventory benchmark.

## 2. Pre-Registered Hypotheses
- **H1 (Silent Error Reduction)**: System E achieves a significantly lower silent-error rate than System A in both noisy and oracle simulation modes.
- **H2 (Non-Inferiority to Eager Interrogation)**: System E achieves non-inferior task success relative to System C (non-inferiority margin $\Delta = 0.02$, or 2 percentage points) while asking strictly fewer clarification questions per task.
- **H3 (Frontier Dominance over Confidence Thresholds)**: System E achieves higher task success than System D at an equal or lower clarification question budget.
- **H4 (Canary Safety Enhancement)**: System F achieves a lower silent-error rate than System E, at an additional question cost not exceeding 0.25 questions per task.

## 3. Experimental Design & Benchmark Tasks
- **Benchmark**: 100 held-out TEST tasks (seeds 5000–5099), completely disjoint from DEV calibration tasks (seeds 1000–1019).
- **Ambiguity Taxonomy**: Controlled 50% ambiguous tasks spanning 5 distinct categories:
  1. `duplicate_id_vs_name`
  2. `category_granularity`
  3. `missing_strategy`
  4. `recalculate_basis`
  5. `type_coercion`
- **User Simulation Modes**:
  - `oracle`: Always selects gold-aligned option.
  - `noisy`: Selects gold-aligned option with probability 0.8; random alternative with probability 0.2.
  - `unsure`: Returns "unsure" with probability 0.3 (triggering majority fallback with flagged rows); oracle with probability 0.7.
- **Trials**: 3 independent trials per task-system-mode tuple (`TRIALS = 3`), with seeds derived via `sha256(task_seed, system, mode, trial)`. Total task evaluations = 100 tasks × 8 systems × 3 modes × 3 trials = 7,200 runs.

## 4. Systems Under Evaluation
1. **System A**: Single LLM plan ($K=1$), no user interaction.
2. **System A2**: Ensembled majority-vote of $K=3$ plans, no interaction (token-matched control).
3. **System B**: Single plan + heuristic schema validators (row drop > 20%, null rate > 30%).
4. **System C**: Eager interactive policy (always asks for confirmation/clarification).
5. **System D**: Confidence-thresholded policy (asks when self-reported confidence < $\tau_c = 0.75$).
6. **System E (ConsensusGate)**: Disagreement-based interactive gate ($\tau_d = 0.0$ calibrated on DEV).
7. **System F (ProbeGate)**: ConsensusGate + canary probe verification.
8. **System R**: Stochastic baseline asking questions with probability equal to System E's empirical DEV ask rate.

## 5. Metrics & Definitions
- **Task Success**: 1 if all gold required edits are applied AND zero forbidden edits are applied; 0 otherwise.
- **Silent Error**: 1 if a forbidden destructive or transformative edit is applied without asking a clarification question or setting an inspection flag; 0 otherwise.
- **Questions Asked**: Integer count of interactive clarification rounds per task (0, 1, or 2).
- **Question Precision**: Proportion of asked clarification questions that occurred on genuinely ambiguous tasks.
- **Tokens**: Total whitespace token count across prompts and generated outputs.
- **Simulated Latency**: Modeled execution latency (base 1.0 unit + 0.5 per clarification round).

## 6. Statistical Analysis Protocol
- **Unit of Analysis**: The task (averaging across the 3 independent trials).
- **Inference Method**: Non-parametric paired bootstrap with 10,000 resamples, fixed RNG seed (`seed=20261105`).
- **Confidence Intervals**: 95% two-sided bias-corrected and accelerated (BCa) / percentile bootstrap intervals.
- **Multiple Comparisons**: Holm-Bonferroni step-down procedure applied across primary hypotheses H1–H4.
- **Exclusion Rules**: Zero tasks, trials, or runs excluded. All data generated will be reported.

## 7. Threats to Validity & Mock Honesty (Rule R7)
Experiments run with `LLM_PROVIDER=mock` and `BUDGET_USD=0` evaluate policy logic, decision gates, and consensus mechanisms under a controlled generative noise model, not live proprietary API calls. Claims of performance apply to simulated stochastic agent policies and do not claim universal generalization to unverified commercial models without further empirical validation.
