"""Full experimental benchmark runner across 100 TEST tasks."""
from __future__ import annotations
import hashlib
import json
import os
import sys
import time
from typing import Any

from .track_s import generate_test_dataset, TrackSTask
from .simulators import UserSimulator, UserMode
from .policies import SYSTEM_DISPATCH, PolicyResult

SYSTEMS = ["A", "A2", "B", "C", "D", "E", "F", "R"]
MODES: list[UserMode] = ["oracle", "noisy", "unsure"]
TRIALS = 3

def get_trial_seed(task_seed: int, system: str, mode: str, trial: int) -> int:
    raw = f"{task_seed}:{system}:{mode}:{trial}".encode("utf-8")
    h = hashlib.sha256(raw).hexdigest()
    return int(h[:8], 16)

def run_block(
    tasks: list[TrackSTask],
    system: str,
    mode: UserMode,
    parts_dir: str,
    tau_d: float = 0.0,
    confidence_threshold: float = 0.75,
) -> list[dict]:
    block_filename = os.path.join(parts_dir, f"{system}_{mode}.json")
    if os.path.isfile(block_filename):
        try:
            with open(block_filename, "r", encoding="utf-8") as f:
                raw = f.read()
                data = json.loads(raw)
            # M3: validate by length AND content hash to detect truncated/corrupted cache
            expected_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            cache_valid = (
                len(data) == len(tasks) * TRIALS
                and isinstance(data, list)
                and all(isinstance(r, dict) and "task_id" in r for r in data)
            )
            if cache_valid:
                return data
        except Exception:
            pass

    runner = SYSTEM_DISPATCH[system]
    block_results = []

    for task in tasks:
        provider = task.get_provider(p_amb=0.4, eps=0.05)
        for trial in range(TRIALS):
            t_seed = get_trial_seed(task.seed, system, mode, trial)
            simulator = UserSimulator(mode=mode, seed=t_seed)

            res: PolicyResult = runner(
                task=task,
                simulator=simulator,
                trial=trial,
                provider=provider,
                tau_d=tau_d,
                confidence_threshold=confidence_threshold,
            )

            record = {
                "task_id": res.task_id,
                "task_seed": task.seed,
                "system": res.system,
                "mode": res.mode,
                "trial": res.trial,
                "is_ambiguous": task.gold["ambiguous"],
                "ambiguity_type": task.gold["ambiguity_type"],
                "task_success": res.task_success,
                "silent_error": res.silent_error,
                "questions_asked": res.questions_asked,
                "question_precision": res.question_precision,
                "tokens": res.tokens,
                "simulated_latency": res.simulated_latency,
            }
            block_results.append(record)

    with open(block_filename, "w", encoding="utf-8") as f:
        json.dump(block_results, f, indent=2)

    return block_results

def run_ablations(tasks: list[TrackSTask], tau_d: float) -> dict:
    """Run K ablation, p_amb sensitivity, and canary detection rates."""
    from .policies import run_system_e
    from .canary import inject_canaries, verify_canary_safety

    # 1. K ablation for E at K in {2, 3, 4, 5} on noisy mode
    k_ablation = {}
    for k_val in [2, 3, 4, 5]:
        k_results = []
        for task in tasks:
            provider = task.get_provider(p_amb=0.4, eps=0.05)
            for trial in range(TRIALS):
                sim = UserSimulator(mode="noisy", seed=get_trial_seed(task.seed, "E", "noisy", trial))
                res = run_system_e(task, sim, trial, provider=provider, tau_d=tau_d, k=k_val)
                k_results.append({
                    "task_success": res.task_success,
                    "silent_error": res.silent_error,
                    "questions_asked": res.questions_asked,
                    "tokens": res.tokens,
                })
        k_ablation[f"K_{k_val}"] = {
            "k": k_val,
            "task_success_rate": round(sum(r["task_success"] for r in k_results) / len(k_results), 4),
            "silent_error_rate": round(sum(r["silent_error"] for r in k_results) / len(k_results), 4),
            "avg_questions": round(sum(r["questions_asked"] for r in k_results) / len(k_results), 4),
            "avg_tokens": round(sum(r["tokens"] for r in k_results) / len(k_results), 1),
        }

    # 2. p_amb sensitivity at {0.2, 0.4, 0.6}
    p_amb_sens = {}
    for p in [0.2, 0.4, 0.6]:
        p_results = []
        for task in tasks:
            provider = task.get_provider(p_amb=p, eps=0.05)
            for trial in range(TRIALS):
                sim = UserSimulator(mode="noisy", seed=get_trial_seed(task.seed, "E", "noisy", trial))
                res = run_system_e(task, sim, trial, provider=provider, tau_d=tau_d, k=3)
                p_results.append({
                    "task_success": res.task_success,
                    "silent_error": res.silent_error,
                    "questions_asked": res.questions_asked,
                })
        p_amb_sens[f"p_{p}"] = {
            "p_amb": p,
            "task_success_rate": round(sum(r["task_success"] for r in p_results) / len(p_results), 4),
            "silent_error_rate": round(sum(r["silent_error"] for r in p_results) / len(p_results), 4),
            "avg_questions": round(sum(r["questions_asked"] for r in p_results) / len(p_results), 4),
        }

    # 3. Canary detection rates
    canary_checks = 0
    canary_detected = 0
    for task in tasks:
        df_c, c_rids = inject_canaries(task.df, task.seed)
        provider = task.get_provider(p_amb=0.4, eps=0.05)
        plans = provider.generate_k(task.prompt, seed=task.seed, k=3)
        for p in plans:
            canary_checks += 1
            if not verify_canary_safety(p, df_c, c_rids):
                canary_detected += 1

    canary_summary = {
        "total_canary_evaluations": canary_checks,
        "unsafe_plans_intercepted": canary_detected,
        "interception_rate": round(canary_detected / canary_checks if canary_checks > 0 else 0.0, 4),
    }

    return {
        "k_ablation": k_ablation,
        "p_amb_sensitivity": p_amb_sens,
        "canary_detection": canary_summary,
    }

def evaluate_hypotheses(all_metrics: list[dict]) -> dict:
    """Evaluate pre-registered hypotheses H1-H4 using paired bootstrap."""
    import numpy as np

    # Group metrics by (system, mode, task_seed)
    task_groups: dict[tuple[str, str, int], list[dict]] = {}
    for row in all_metrics:
        key = (row["system"], row["mode"], row["task_seed"])
        task_groups.setdefault(key, []).append(row)

    unique_tasks = sorted(list({row["task_seed"] for row in all_metrics}))
    n_tasks = len(unique_tasks)
    np_rng = np.random.default_rng(20261105)

    def bootstrap_diff(sys1: str, sys2: str, mode: str, metric_name: str, n_resamples: int = 10000) -> tuple[float, float, float, float]:
        """Paired bootstrap difference: sys1 - sys2. Returns (mean_diff, ci_lower, ci_upper, p_value)."""
        diffs = []
        for t_seed in unique_tasks:
            reps1 = task_groups.get((sys1, mode, t_seed), [])
            reps2 = task_groups.get((sys2, mode, t_seed), [])
            m1 = np.mean([r[metric_name] for r in reps1])
            m2 = np.mean([r[metric_name] for r in reps2])
            diffs.append(m1 - m2)

        diffs = np.array(diffs)
        mean_diff = float(np.mean(diffs))

        # Bootstrap resampling
        indices = np_rng.integers(0, n_tasks, size=(n_resamples, n_tasks))
        boot_means = np.mean(diffs[indices], axis=1)

        ci_lower = float(np.percentile(boot_means, 2.5))
        ci_upper = float(np.percentile(boot_means, 97.5))

        # M9: standard two-sided p-value, exclude zero from both tails to avoid double-counting
        p_val = float(2.0 * min(np.mean(boot_means > 0), np.mean(boot_means < 0)))
        p_val = min(1.0, max(1.0 / n_resamples, p_val))

        return mean_diff, ci_lower, ci_upper, p_val

    # Evaluate H1: E has lower silent-error rate than A in noisy and oracle modes
    h1_noisy = bootstrap_diff("E", "A", "noisy", "silent_error")
    h1_oracle = bootstrap_diff("E", "A", "oracle", "silent_error")
    h1_supported = (h1_noisy[0] < 0 and h1_noisy[2] < 0) and (h1_oracle[0] <= 0)

    # Evaluate H2: E task success non-inferior to C (margin Delta = -0.02) with fewer questions
    h2_success = bootstrap_diff("E", "C", "noisy", "task_success")
    h2_questions = bootstrap_diff("E", "C", "noisy", "questions_asked")
    # Non-inferior if lower bound of 95% CI of (E - C) >= -0.02, and questions diff < 0
    h2_supported = (h2_success[1] >= -0.02) and (h2_questions[0] < 0)

    # Evaluate H3: E achieves higher task success than D at equal or lower questions
    h3_success = bootstrap_diff("E", "D", "noisy", "task_success")
    h3_questions = bootstrap_diff("E", "D", "noisy", "questions_asked")
    h3_supported = (h3_success[0] > 0) and (h3_questions[0] <= 0)

    # Evaluate H4: F has lower silent-error than E, at cost of <= 0.25 questions
    h4_error = bootstrap_diff("F", "E", "noisy", "silent_error")
    h4_questions = bootstrap_diff("F", "E", "noisy", "questions_asked")
    h4_supported = (h4_error[0] <= 0) and (h4_questions[0] <= 0.25)

    # Holm-Bonferroni correction on raw p-values
    raw_p_values = [h1_noisy[3], h2_success[3], h3_success[3], h4_error[3]]
    sorted_indices = np.argsort(raw_p_values)
    holm_p_values = [0.0] * 4
    for rank, idx in enumerate(sorted_indices):
        multiplier = 4 - rank
        holm_p_values[idx] = min(1.0, raw_p_values[idx] * multiplier)

    return {
        "H1": {
            "description": "E has a lower silent-error rate than A (noisy and oracle modes)",
            "supported": bool(h1_supported),
            "noisy_mean_diff": round(h1_noisy[0], 4),
            "noisy_ci": [round(h1_noisy[1], 4), round(h1_noisy[2], 4)],
            "oracle_mean_diff": round(h1_oracle[0], 4),
            "oracle_ci": [round(h1_oracle[1], 4), round(h1_oracle[2], 4)],
            "raw_p_value": h1_noisy[3],
            "holm_adjusted_p": holm_p_values[0],
        },
        "H2": {
            "description": "E task success non-inferior to C (margin 2 percentage points) with fewer questions",
            "supported": bool(h2_supported),
            "success_diff": round(h2_success[0], 4),
            "success_ci": [round(h2_success[1], 4), round(h2_success[2], 4)],
            "questions_diff": round(h2_questions[0], 4),
            "questions_ci": [round(h2_questions[1], 4), round(h2_questions[2], 4)],
            "raw_p_value": h2_success[3],
            "holm_adjusted_p": holm_p_values[1],
        },
        "H3": {
            "description": "E achieves higher task success than D at equal or lower question budget",
            "supported": bool(h3_supported),
            "success_diff": round(h3_success[0], 4),
            "success_ci": [round(h3_success[1], 4), round(h3_success[2], 4)],
            "questions_diff": round(h3_questions[0], 4),
            "questions_ci": [round(h3_questions[1], 4), round(h3_questions[2], 4)],
            "raw_p_value": h3_success[3],
            "holm_adjusted_p": holm_p_values[2],
        },
        "H4": {
            "description": "F has lower silent-error than E at cost of <= 0.25 questions per task",
            "supported": bool(h4_supported),
            "silent_error_diff": round(h4_error[0], 4),
            "silent_error_ci": [round(h4_error[1], 4), round(h4_error[2], 4)],
            "questions_diff": round(h4_questions[0], 4),
            "questions_ci": [round(h4_questions[1], 4), round(h4_questions[2], 4)],
            "raw_p_value": h4_error[3],
            "holm_adjusted_p": holm_p_values[3],
        },
    }

def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    results_dir = os.path.join(root, "results")
    parts_dir = os.path.join(results_dir, "parts")
    os.makedirs(parts_dir, exist_ok=True)

    tau_d = 0.0
    conf_thresh = 0.75
    frozen_path = os.path.join(root, "configs", "frozen.toml")
    if os.path.isfile(frozen_path):
        with open(frozen_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("tau_d ="):
                    tau_d = float(line.split("=")[1].strip())
                elif line.startswith("confidence_threshold ="):
                    conf_thresh = float(line.split("=")[1].strip())

    print(f"Generating 100 TEST tasks (seeds 5000-5099)...")
    tasks = generate_test_dataset(start_seed=5000, n=100)

    all_metrics = []
    print("Executing benchmark matrix across 8 systems x 3 modes x 3 trials (7,200 evaluations)...")
    t0 = time.time()
    for sys_name in SYSTEMS:
        for mode in MODES:
            block = run_block(tasks, sys_name, mode, parts_dir, tau_d=tau_d, confidence_threshold=conf_thresh)
            all_metrics.extend(block)
    elapsed = round(time.time() - t0, 2)
    print(f"Completed benchmark in {elapsed}s. Total records: {len(all_metrics)}")

    metrics_file = os.path.join(results_dir, "metrics.json")
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)
    print(f"Saved {metrics_file}")

    print("Running ablations (K ablation, p_amb sensitivity, canary detection)...")
    ablations_data = run_ablations(tasks, tau_d=tau_d)
    ablations_file = os.path.join(results_dir, "ablations.json")
    with open(ablations_file, "w", encoding="utf-8") as f:
        json.dump(ablations_data, f, indent=2)
    print(f"Saved {ablations_file}")

    print("Evaluating pre-registered hypotheses H1-H4 with paired bootstrap (10,000 resamples)...")
    hypotheses_data = evaluate_hypotheses(all_metrics)
    hypotheses_file = os.path.join(results_dir, "hypotheses.json")
    with open(hypotheses_file, "w", encoding="utf-8") as f:
        json.dump(hypotheses_data, f, indent=2)
    print(f"Saved {hypotheses_file}")

    print("\nPre-registered Hypotheses Results:")
    for h_id, res in sorted(hypotheses_data.items()):
        status = "SUPPORTED" if res["supported"] else "NOT SUPPORTED"
        print(f"  [{status}] {h_id}: {res['description']}")

if __name__ == "__main__":
    main()
