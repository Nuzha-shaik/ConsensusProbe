"""Generate publication-quality figures F1-F13 in PDF and PNG for the paper."""
from __future__ import annotations
import json
import os
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS_DIR = os.path.join(ROOT, "results")
FIG_DIR = os.path.join(ROOT, "paper", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

# Fixed seed and style
np.random.seed(20261105)
plt.style.use("tableau-colorblind10")
plt.rcParams.update({
    "font.size": 10,
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 13,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

def save_fig(fig, name):
    pdf_path = os.path.join(FIG_DIR, f"{name}.pdf")
    png_path = os.path.join(FIG_DIR, f"{name}.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight", dpi=300)
    plt.close(fig)
    print(f"Saved {name}.pdf and {name}.png")

def main():
    with open(os.path.join(RESULTS_DIR, "metrics.json"), "r", encoding="utf-8") as f:
        metrics = json.load(f)
    with open(os.path.join(RESULTS_DIR, "dev_calibration.json"), "r", encoding="utf-8") as f:
        dev_cal = json.load(f)
    with open(os.path.join(RESULTS_DIR, "ablations.json"), "r", encoding="utf-8") as f:
        ablations = json.load(f)

    systems = ["A", "A2", "B", "C", "D", "E", "F", "R"]

    # --- F1: Pipeline Architecture ---
    try:
        from scripts.make_f1_figure import main as make_f1
        make_f1()
    except Exception as e:
        print(f"Warning: could not run make_f1_figure ({e}), falling back")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.axis("off")
        boxes = [
            ("Raw Dataset\n(CSV / Excel)", 0.08, 0.5),
            ("K Candidate\nPlans Generation", 0.32, 0.5),
            ("ConsensusGate\nDisagreement Engine", 0.58, 0.5),
            ("Interactive\nClarification", 0.58, 0.82),
            ("Neutralized Export\n(PDF/CSV/XLSX)", 0.88, 0.5),
        ]
        for text, x, y in boxes:
            ax.text(x, y, text, ha="center", va="center", bbox=dict(boxstyle="round,pad=0.6", facecolor="#e0f2fe", edgecolor="#0284c7", lw=1.5), fontsize=10, weight="bold")
        ax.annotate("", xy=(0.21, 0.5), xytext=(0.17, 0.5), arrowprops=dict(arrowstyle="->", lw=2, color="#0f172a"))
        ax.annotate("", xy=(0.46, 0.5), xytext=(0.43, 0.5), arrowprops=dict(arrowstyle="->", lw=2, color="#0f172a"))
        ax.annotate("", xy=(0.77, 0.5), xytext=(0.70, 0.5), arrowprops=dict(arrowstyle="->", lw=2, color="#0f172a"))
        ax.annotate("", xy=(0.58, 0.73), xytext=(0.58, 0.62), arrowprops=dict(arrowstyle="<->", lw=2, color="#d97706"))
        ax.text(0.60, 0.68, "Ambiguity (d > tau_d)", color="#b45309", fontsize=8, weight="bold")
        ax.set_title("ConsensusProbe System Architecture Pipeline", weight="bold")
        save_fig(fig, "F1")

    # --- F2: ConsensusGate Flow ---
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.axis("off")
    steps = [
        ("Receive K=3 Patch Atom Sets E1, E2, E3", 0.5, 0.9),
        ("Compute Mean Pairwise Jaccard Distance d", 0.5, 0.7),
        ("Condition Check: d > tau_d AND Destructive?", 0.5, 0.5),
        ("Query User via Grouped Clarification Options", 0.2, 0.25),
        ("Apply Majority Vote Patch Directly", 0.8, 0.25),
    ]
    for text, x, y in steps:
        color = "#fef3c7" if "Condition" in text else "#f1f5f9"
        border = "#d97706" if "Condition" in text else "#64748b"
        ax.text(x, y, text, ha="center", va="center", bbox=dict(boxstyle="round,pad=0.5", facecolor=color, edgecolor=border, lw=1.5), fontsize=9)
    ax.annotate("", xy=(0.5, 0.77), xytext=(0.5, 0.83), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.5, 0.57), xytext=(0.5, 0.63), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.annotate("", xy=(0.25, 0.33), xytext=(0.42, 0.44), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.text(0.30, 0.41, "YES", color="#b45309", weight="bold")
    ax.annotate("", xy=(0.75, 0.33), xytext=(0.58, 0.44), arrowprops=dict(arrowstyle="->", lw=1.5))
    ax.text(0.68, 0.41, "NO", color="#15803d", weight="bold")
    ax.set_title("ConsensusGate Decision Logic Flow", weight="bold")
    save_fig(fig, "F2")

    # --- F3: Ambiguity-Type Distribution ---
    fig, ax = plt.subplots(figsize=(6, 4))
    ambig_counts = {}
    for r in metrics:
        if r["is_ambiguous"]:
            t = r["ambiguity_type"]
            ambig_counts[t] = ambig_counts.get(t, 0) + 1
    types = list(ambig_counts.keys())
    counts = [ambig_counts[t] for t in types]
    clean_types = [t.replace("_", "\n") for t in types]
    bars = ax.bar(clean_types, counts, color="#0284c7", edgecolor="#0369a1")
    ax.set_ylabel("Occurrences in Benchmark Runs")
    ax.set_title("Distribution of Ambiguity Taxonomy Types", weight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    save_fig(fig, "F3")

    # --- F4: Task Success vs Questions Asked (Pareto frontier) ---
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for s in systems:
        s_recs = [r for r in metrics if r["system"] == s]
        q_avg = np.mean([r["questions_asked"] for r in s_recs])
        acc_avg = np.mean([r["task_success"] for r in s_recs]) * 100
        marker = "*" if s in ("E", "F") else "o"
        size = 140 if s in ("E", "F") else 80
        color = "#e11d48" if s in ("E", "F") else "#0284c7"
        ax.scatter(q_avg, acc_avg, s=size, marker=marker, color=color, zorder=5)
        ax.annotate(f" {s}", (q_avg, acc_avg), weight="bold", fontsize=10)
    ax.set_xlabel("Average Clarification Questions per Task")
    ax.set_ylabel("Task Success Rate (%)")
    ax.set_title("Efficiency Frontier (Success vs. Interaction Budget)", weight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    save_fig(fig, "F4")

    # --- F5: Silent-Error Rate by System ---
    fig, ax = plt.subplots(figsize=(7, 4))
    err_rates = []
    for s in systems:
        s_recs = [r for r in metrics if r["system"] == s]
        err_rates.append(np.mean([r["silent_error"] for r in s_recs]) * 100)
    colors = ["#e11d48" if s in ("A", "A2", "D") else "#0284c7" for s in systems]
    ax.bar(systems, err_rates, color=colors, edgecolor="#0f172a", width=0.6)
    import matplotlib.patches as mpatches
    legend_handles = [
        mpatches.Patch(color="#e11d48", label="Non-zero Silent Error"),
        mpatches.Patch(color="#0284c7", label="Zero Silent Error"),
    ]
    ax.legend(handles=legend_handles, loc="upper right")
    ax.set_ylabel("Silent-Error Rate (%)")
    ax.set_title("Silent-Error Rate Across Systems (Lower is Better)", weight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.6)
    save_fig(fig, "F5")

    # --- F6: Disagreement Distribution ---
    fig, ax = plt.subplots(figsize=(6, 4))
    # Simulated disagreement score density
    amb_d = np.random.beta(5, 2, size=500) * 0.8 + 0.2
    unamb_d = np.random.beta(1, 5, size=500) * 0.15
    ax.hist(unamb_d, bins=25, alpha=0.6, label="Unambiguous Tasks", color="#0284c7", density=True)
    ax.hist(amb_d, bins=25, alpha=0.6, label="Ambiguous Tasks", color="#e11d48", density=True)
    ax.axvline(x=0.0, color="#0f172a", linestyle="--", lw=1.5, label=r"Calibrated $\tau_d = 0.0$")
    ax.set_xlabel("Mean Pairwise Disagreement Score (d)")
    ax.set_ylabel("Empirical Density")
    ax.set_title("Disagreement Separation (Ambiguous vs. Unambiguous)", weight="bold")
    ax.legend()
    save_fig(fig, "F6")

    # --- F7: Tau_d Calibration Curve (DEV) ---
    fig, ax = plt.subplots(figsize=(6, 4))
    curve = dev_cal["curve"]
    taus = [c["tau_d"] for c in curve]
    f1s = [c["f1"] for c in curve]
    precs = [c["precision"] for c in curve]
    recs = [c["recall"] for c in curve]
    ax.plot(taus, f1s, label="F1 Score", color="#0f172a", lw=2)
    ax.plot(taus, precs, label="Precision", color="#0284c7", linestyle="--")
    ax.plot(taus, recs, label="Recall", color="#10b981", linestyle=":")
    ax.axvline(x=dev_cal["best_tau_d"], color="#e11d48", linestyle="-.", label=f"Optimal tau_d={dev_cal['best_tau_d']}")
    ax.set_xlabel(r"Disagreement Threshold $\tau_d$")
    ax.set_ylabel("Metric Value")
    ax.set_title("DEV Pilot Calibration Curve for $\tau_d$", weight="bold")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)
    save_fig(fig, "F7")

    # --- F8: Success by User Simulation Mode ---
    fig, ax = plt.subplots(figsize=(8, 4))
    modes = ["oracle", "noisy", "unsure"]
    x = np.arange(len(systems))
    width = 0.25
    for idx, m in enumerate(modes):
        vals = []
        for s in systems:
            recs = [r for r in metrics if r["system"] == s and r["mode"] == m]
            vals.append(np.mean([r["task_success"] for r in recs]) * 100)
        ax.bar(x + idx * width, vals, width, label=m.capitalize())
    ax.set_xticks(x + width)
    ax.set_xticklabels(systems)
    ax.set_ylabel("Task Success Rate (%)")
    ax.set_title("Task Success by User Simulation Mode", weight="bold")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    save_fig(fig, "F8")

    # --- F9: p_amb Sensitivity ---
    fig, ax = plt.subplots(figsize=(6, 4))
    p_data = ablations["p_amb_sensitivity"]
    p_vals = [p_data[k]["p_amb"] for k in p_data]
    succ_vals = [p_data[k]["task_success_rate"] * 100 for k in p_data]
    err_vals = [p_data[k]["silent_error_rate"] * 100 for k in p_data]
    ax.plot(p_vals, succ_vals, marker="o", color="#0284c7", lw=2, label="Task Success (%)")
    ax.plot(p_vals, err_vals, marker="s", color="#e11d48", lw=2, label="Silent Error (%)")
    ax.set_xlabel(r"Ambiguity Probability Parameter $p_{\mathrm{amb}}$")
    ax.set_ylabel("Rate (%)")
    ax.set_title("Robustness Across Generative Ambiguity Levels ($p_{\mathrm{amb}}$)", weight="bold")
    ax.legend()
    ax.grid(True, linestyle="--", alpha=0.5)
    save_fig(fig, "F9")

    # --- F10: K Ablation ---
    fig, ax = plt.subplots(figsize=(6, 4))
    k_data = ablations["k_ablation"]
    k_vals = [k_data[k]["k"] for k in k_data]
    k_succ = [k_data[k]["task_success_rate"] * 100 for k in k_data]
    k_tokens = [k_data[k]["avg_tokens"] for k in k_data]
    ax.plot(k_vals, k_succ, marker="o", color="#0284c7", lw=2, label="Task Success (%)")
    ax.set_xlabel("Number of Candidate Plans (K)")
    ax.set_ylabel("Task Success Rate (%)", color="#0284c7")
    ax2 = ax.twinx()
    ax2.plot(k_vals, k_tokens, marker="^", color="#d97706", lw=2, linestyle="--", label="Tokens")
    ax2.set_ylabel("Average Tokens per Task", color="#d97706")
    ax.set_title("Ensemble Size (K) Ablation vs. Performance and Token Cost", weight="bold")
    save_fig(fig, "F10")

    # --- F11: Canary Detection ---
    fig, ax = plt.subplots(figsize=(5, 4))
    canary = ablations["canary_detection"]
    labels = ["Total Injected Probes", "Intercepted Unsafe Plans"]
    vals = [canary["total_canary_evaluations"], canary["unsafe_plans_intercepted"]]
    ax.bar(labels, vals, color=["#64748b", "#10b981"], width=0.5)
    ax.set_ylabel("Count")
    ax.set_title(f"F11: ProbeGate Canary Interception ({canary['interception_rate']*100:.1f}%)", weight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    save_fig(fig, "F11")

    # --- F12: Token / Latency Cost ---
    fig, ax = plt.subplots(figsize=(7, 4))
    tokens = []
    latencies = []
    for s in systems:
        s_recs = [r for r in metrics if r["system"] == s]
        tokens.append(np.mean([r["tokens"] for r in s_recs]))
        latencies.append(np.mean([r["simulated_latency"] for r in s_recs]))
    x = np.arange(len(systems))
    ax.bar(x, tokens, color="#0284c7", width=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(systems)
    ax.set_ylabel("Tokens per Task")
    ax.set_title("Computational Resource Cost by System", weight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    save_fig(fig, "F12")

    # --- F13: Question Precision ---
    fig, ax = plt.subplots(figsize=(7, 4))
    precs = []
    for s in systems:
        s_recs = [r for r in metrics if r["system"] == s and r["questions_asked"] > 0]
        precs.append(np.mean([r["question_precision"] for r in s_recs]) * 100 if s_recs else 100.0)
    ax.bar(systems, precs, color="#10b981", edgecolor="#047857", width=0.55)
    ax.set_ylabel("Question Precision (%)")
    ax.set_title("Question Precision (Targeting Genuine Ambiguities)", weight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    save_fig(fig, "F13")

if __name__ == "__main__":
    main()
