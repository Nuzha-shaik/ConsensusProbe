"""Pilot calibration on DEV dataset: calibrate tau_d and freeze parameters."""
from __future__ import annotations
import hashlib
import itertools
import json
import os
import sys
import numpy as np

from research.track_s import generate_dev_dataset
from research.consensus import plan_to_patch, calculate_consensus

def run_calibration(
    start_seed: int = 1000,
    n_tasks: int = 20,
    k_pilot: int = 5,
    k_eval: int = 3,
    p_amb: float = 0.4,
    eps: float = 0.05,
) -> dict:
    dev_tasks = generate_dev_dataset(start_seed=start_seed, n=n_tasks)

    # Hash the DEV dataset for reproducibility
    hasher = hashlib.sha256()
    for t in dev_tasks:
        hasher.update(str(t.seed).encode("utf-8"))
        hasher.update(t.df.to_csv(index=False).encode("utf-8"))
        hasher.update(json.dumps(t.gold, sort_keys=True, default=str).encode("utf-8"))
    dev_data_hash = hasher.hexdigest()

    # Generate K=5 plans per task
    task_eval_data = []
    for task in dev_tasks:
        provider = task.get_provider(p_amb=p_amb, eps=eps)
        plans = provider.generate_k(task.prompt, seed=task.seed, k=k_pilot)
        patches = [plan_to_patch(task.df, p) for p in plans]

        # All subsets of size k_eval (3)
        combos = list(itertools.combinations(range(k_pilot), k_eval))
        for combo in combos:
            sub_patches = [patches[idx] for idx in combo]
            res = calculate_consensus(sub_patches)
            task_eval_data.append({
                "task_id": task.task_id,
                "is_ambiguous": task.gold["ambiguous"],
                "score": res.score,
                "has_destructive_or_transformative": res.has_destructive_or_transformative,
            })

    # Evaluate candidate tau_d values
    thresholds = [round(x, 4) for x in np.linspace(0.0, 1.0, 101)]
    best_f1 = -1.0
    best_tau_d = 0.0
    curve = []

    for tau in thresholds:
        tp = fp = fn = tn = 0
        for item in task_eval_data:
            # Ask iff score > tau AND has_destructive_or_transformative
            ask = (item["score"] > tau) and item["has_destructive_or_transformative"]
            actual = item["is_ambiguous"]

            if ask and actual:
                tp += 1
            elif ask and not actual:
                fp += 1
            elif not ask and actual:
                fn += 1
            else:
                tn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        acc = (tp + tn) / len(task_eval_data) if task_eval_data else 0.0

        curve.append({
            "tau_d": tau,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "accuracy": round(acc, 4),
        })

        # Maximize F1, tie-break to smaller tau_d
        if f1 > best_f1:
            best_f1 = f1
            best_tau_d = tau

    # Fallback if best_tau_d == 0.0 but multiple have same F1
    result = {
        "best_tau_d": best_tau_d,
        "best_f1": round(best_f1, 4),
        "k": k_eval,
        "p_amb": p_amb,
        "eps": eps,
        "dev_seeds": list(range(start_seed, start_seed + n_tasks)),
        "dev_data_hash": dev_data_hash,
        "curve": curve,
    }
    return result

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(root, "results")
    configs_dir = os.path.join(root, "configs")
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(configs_dir, exist_ok=True)

    print("Running DEV pilot calibration...")
    res = run_calibration()

    cal_path = os.path.join(results_dir, "dev_calibration.json")
    with open(cal_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"Saved calibration curve to {cal_path}")
    print(f"Optimal tau_d: {res['best_tau_d']} with F1: {res['best_f1']}")

    # Write configs/frozen.toml
    frozen_path = os.path.join(configs_dir, "frozen.toml")
    toml_content = f"""# Frozen parameters calibrated on DEV dataset
tau_d = {res['best_tau_d']}
p_amb = {res['p_amb']}
eps = {res['eps']}
k = {res['k']}
dev_seeds = {res['dev_seeds']}
test_seed_start = 5000
test_tasks_count = 100
confidence_threshold = 0.75
dev_data_hash = "{res['dev_data_hash']}"
"""
    with open(frozen_path, "w", encoding="utf-8") as f:
        f.write(toml_content)
    print(f"Saved frozen configuration to {frozen_path}")

if __name__ == "__main__":
    main()
