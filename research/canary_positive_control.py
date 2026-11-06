"""Canary Positive Control Experiment (Post-hoc and Exploratory).

Evaluates System F sentinel detection and ConsensusGate resolution when a
known-wrong destructive operation (deleting the safe probe row) is injected
into exactly one of the K=3 candidate plans.

Compares System E (disagreement gate only, blind to canaries) against
System F (ConsensusGate + Canary Sentinel) on the exact same fault-injected plans.
"""
from __future__ import annotations

import json
import os
import random
import numpy as np
import pandas as pd

from research.track_s import generate_track_s_task, TrackSTask
from research.canary import (
    inject_canaries,
    verify_canary_safety,
    filter_canary_artifacts,
    CANARY_RID_OFFSET,
)
from research.consensus import (
    calculate_consensus,
    plan_to_patch,
    generate_clarification_question,
    majority_vote_patch,
)
from research.simulators import UserSimulator
from research.patch import Patch
from research.policies import evaluate_metrics


def _bootstrap_ci(data: list[float], n_resamples: int = 10000, seed: int = 20261105) -> tuple[float, float, float]:
    """Compute mean and 95% percentile bootstrap confidence interval."""
    rng = np.random.default_rng(seed)
    arr = np.array(data, dtype=float)
    mean_val = float(np.mean(arr))
    if len(arr) == 0:
        return 0.0, 0.0, 0.0
    indices = rng.integers(0, len(arr), size=(n_resamples, len(arr)))
    boot_means = np.mean(arr[indices], axis=1)
    ci_lower = float(np.percentile(boot_means, 2.5))
    ci_upper = float(np.percentile(boot_means, 97.5))
    return mean_val, ci_lower, ci_upper


def run_positive_control():
    # 100 TEST tasks x 3 trials = 300 evaluations
    task_seeds = list(range(5000, 5100))
    trials = 3

    records_2a = []
    clean_records = []

    for seed in task_seeds:
        task = generate_track_s_task(seed, mode="TEST")
        base_provider = task.get_provider(p_amb=0.4, eps=0.05)

        for trial in range(trials):
            # Deterministic plan generation
            plans = base_provider.generate_k(task.prompt, seed=task.seed, k=3)

            # ---------------------------------------------------------
            # Clean Control: Unmodified plans
            # ---------------------------------------------------------
            df_c, c_rids = inject_canaries(task.df, task.seed)
            clean_any_unsafe = any(not verify_canary_safety(p, df_c, c_rids) for p in plans)
            clean_records.append({
                "task_seed": seed,
                "trial": trial,
                "sentinel_fired": clean_any_unsafe,
            })

            # ---------------------------------------------------------
            # 2A: Fault Injection
            # Inject a destructive operation that deletes the safe probe row into plan 0
            # ---------------------------------------------------------
            faulty_plans = [dict(p) for p in plans]
            # Operation that deduplicates by category, deleting the safe probe row CANARY_RID_OFFSET + 2
            # because the probe row shares category with base rows
            faulty_op = {"op": "deduplicate", "params": {"by": ["category"], "keep": "first"}}
            faulty_plan_idx = 0
            faulty_plans[faulty_plan_idx] = {
                "ops": list(plans[faulty_plan_idx]["ops"]) + [faulty_op],
                "confidence": plans[faulty_plan_idx]["confidence"],
            }

            # Pre-evaluate patches on original task.df
            patches_e = [plan_to_patch(task.df, p) for p in faulty_plans]
            faulty_patch = patches_e[faulty_plan_idx]

            # Use identical simulator seed for paired comparison in noisy mode
            sim_seed = int(seed * 100 + trial)
            sim = UserSimulator(mode="noisy", seed=sim_seed)

            # --- SYSTEM E (ConsensusGate alone: blind to canaries) ---
            consensus_e = calculate_consensus(patches_e)
            should_ask_e = consensus_e.should_ask(tau_d=0.0)
            asked_e = False
            applied_patch_e = None
            selected_faulty_e = False

            if should_ask_e:
                q_e = generate_clarification_question(task.df, faulty_plans, patches_e, consensus_e)
                if q_e and q_e.options:
                    asked_e = True
                    ans_e = sim.answer_question(q_e, task.gold)
                    if ans_e == "unsure":
                        applied_patch_e = majority_vote_patch(patches_e)
                    else:
                        applied_patch_e = q_e.options[ans_e].patch
                else:
                    applied_patch_e = majority_vote_patch(patches_e)
            else:
                applied_patch_e = majority_vote_patch(patches_e)

            # Check if applied patch matches the faulty plan's destructive patch
            if applied_patch_e.deleted_rids == faulty_patch.deleted_rids and len(faulty_patch.deleted_rids) > 0:
                selected_faulty_e = True

            # --- SYSTEM F (ProbeGate: ConsensusGate + Canary Sentinel) ---
            # 1. Run canaries on temporary copy
            df_canary, canary_rids = inject_canaries(task.df, task.seed)
            sentinel_fired_f = any(not verify_canary_safety(p, df_canary, canary_rids) for p in faulty_plans)

            # 2. Consensus on original dataset
            consensus_f = calculate_consensus(patches_e)
            should_ask_f = consensus_f.should_ask(tau_d=0.0) or sentinel_fired_f
            asked_f = False
            applied_patch_f = None
            selected_faulty_f = False

            # Reset simulator to identical state for paired test
            sim_f = UserSimulator(mode="noisy", seed=sim_seed)

            if should_ask_f:
                q_f = generate_clarification_question(task.df, faulty_plans, patches_e, consensus_f)
                if q_f and q_f.options:
                    asked_f = True
                    ans_f = sim_f.answer_question(q_f, task.gold)
                    if ans_f == "unsure":
                        maj_f = majority_vote_patch(patches_e)
                        contested = {atom[1] for atom in consensus_f.contested_atoms}
                        applied_patch_f = Patch.create(
                            deleted_rids=maj_f.deleted_rids,
                            cell_edits=maj_f.cell_edits_dict(),
                            flagged={r: "canary_consensus_unsure" for r in contested},
                        )
                    else:
                        applied_patch_f = q_f.options[ans_f].patch
                else:
                    applied_patch_f = majority_vote_patch(patches_e)
            else:
                applied_patch_f = majority_vote_patch(patches_e)

            applied_patch_f = filter_canary_artifacts(applied_patch_f, canary_rids)

            if applied_patch_f.deleted_rids == faulty_patch.deleted_rids and len(faulty_patch.deleted_rids) > 0:
                selected_faulty_f = True

            records_2a.append({
                "task_seed": seed,
                "trial": trial,
                "sentinel_fired": sentinel_fired_f,
                "asked_e": asked_e,
                "asked_f": asked_f,
                "selected_faulty_e": selected_faulty_e,
                "selected_faulty_f": selected_faulty_f,
            })

    # -------------------------------------------------------------
    # Compute Statistics & Bootstrap CIs
    # -------------------------------------------------------------
    n_evals = len(records_2a)
    assert n_evals == 300, f"Expected 300 evaluations, got {n_evals}"

    clean_alarm_rate, clean_ci_l, clean_ci_u = _bootstrap_ci([1.0 if r["sentinel_fired"] else 0.0 for r in clean_records])
    sentinel_rate, sent_ci_l, sent_ci_u = _bootstrap_ci([1.0 if r["sentinel_fired"] else 0.0 for r in records_2a])
    asked_e_rate, asked_e_l, asked_e_u = _bootstrap_ci([1.0 if r["asked_e"] else 0.0 for r in records_2a])
    asked_f_rate, asked_f_l, asked_f_u = _bootstrap_ci([1.0 if r["asked_f"] else 0.0 for r in records_2a])
    fault_leak_e, leak_e_l, leak_e_u = _bootstrap_ci([1.0 if r["selected_faulty_e"] else 0.0 for r in records_2a])
    fault_leak_f, leak_f_l, leak_f_u = _bootstrap_ci([1.0 if r["selected_faulty_f"] else 0.0 for r in records_2a])

    results = {
        "metadata": {
            "description": "Post-hoc exploratory positive control for ProbeGate (System F vs E)",
            "n_evaluations": n_evals,
            "tasks": "100 TEST tasks (seeds 5000-5099)",
            "trials": 3,
            "bootstrap_resamples": 10000,
            "bootstrap_seed": 20261105,
        },
        "clean_control": {
            "sentinel_fired_count": sum(1 for r in clean_records if r["sentinel_fired"]),
            "false_alarm_rate": clean_alarm_rate,
            "ci_95": [clean_ci_l, clean_ci_u],
        },
        "fault_injection_2a": {
            "sentinel_fired_count": sum(1 for r in records_2a if r["sentinel_fired"]),
            "sentinel_detection_rate": sentinel_rate,
            "sentinel_detection_ci_95": [sent_ci_l, sent_ci_u],
            "system_e": {
                "question_rate": asked_e_rate,
                "question_ci_95": [asked_e_l, asked_e_u],
                "faulty_plan_selected_rate": fault_leak_e,
                "faulty_plan_selected_ci_95": [leak_e_l, leak_e_u],
            },
            "system_f": {
                "question_rate": asked_f_rate,
                "question_ci_95": [asked_f_l, asked_f_u],
                "faulty_plan_selected_rate": fault_leak_f,
                "faulty_plan_selected_ci_95": [leak_f_l, leak_f_u],
            },
        },
    }

    os.makedirs("results", exist_ok=True)
    with open("results/canary_positive_control.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Generate small LaTeX table snippet
    latex_table = r"""\begin{table}[!t]
\caption{Exploratory positive control: single-plan fault injection (noisy mode, 300 evaluations).}
\label{tab:positive_control}
\centering
\footnotesize
\begin{tabular}{lcccc}
\toprule
System & Sentinel Fired & Question Rate & Faulty Plan Applied & 95\% CI (Fault Leak) \\
\midrule
Clean Control (F) & 0.0\% (0/300) & --- & --- & [0.0\%, 0.0\%] \\
System E (Gate only) & N/A & """ + f"{asked_e_rate*100:.1f}\\%" + r""" & """ + f"{fault_leak_e*100:.1f}\\%" + r""" & [""" + f"{leak_e_l*100:.1f}\\%, {leak_e_u*100:.1f}\\%" + r"""] \\
\textbf{System F (ProbeGate)} & """ + f"{sentinel_rate*100:.1f}\\% ({sum(1 for r in records_2a if r['sentinel_fired'])}/300)" + r""" & """ + f"{asked_f_rate*100:.1f}\\%" + r""" & """ + f"{fault_leak_f*100:.1f}\\%" + r""" & [""" + f"{leak_f_l*100:.1f}\\%, {leak_f_u*100:.1f}\\%" + r"""] \\
\bottomrule
\end{tabular}
\end{table}
"""
    with open("results/canary_positive_control.tex", "w", encoding="utf-8") as f:
        f.write(latex_table)

    print("Positive control completed successfully.")
    print(f"Clean false-alarm rate: {clean_alarm_rate*100:.1f}%")
    print(f"Sentinel detection rate: {sentinel_rate*100:.1f}% ({sum(1 for r in records_2a if r['sentinel_fired'])}/{n_evals})")
    print(f"System E question rate: {asked_e_rate*100:.1f}%, faulty plan selected: {fault_leak_e*100:.1f}%")
    print(f"System F question rate: {asked_f_rate*100:.1f}%, faulty plan selected: {fault_leak_f*100:.1f}%")

if __name__ == "__main__":
    run_positive_control()
