#!/usr/bin/env python3
"""Generates tuned benchmark sample datasets and ground-truth JSON companions.

Rules enforced:
- Python stdlib only (csv, json, random, pathlib).
- Fixed random seed (42) for deterministic reproducible output.
- retail_clean.csv: clean transactions; consensus disagreement d <= tau_d (auto-approved).
- customers_contested.csv: ambiguous duplicates and missing numeric cells; triggers d > tau_d (gate engaged).
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAMPLES_DIR = ROOT / "frontend" / "public" / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

def generate_clean_sample():
    random.seed(42)
    rows = []
    headers = ["transaction_id", "product_name", "category", "price", "quantity", "sale_date"]
    categories = ["Electronics", "Apparel", "Home & Kitchen", "Books", "Office Supplies"]

    # 45 cleanly structured, unique transactions with no nulls
    for i in range(1, 46):
        cat = categories[(i - 1) % len(categories)]
        price = 10.0 + (i * 2.5)
        qty = 1 + (i % 5)
        dt = f"2026-05-{i % 28 + 1:02d}"
        rows.append({
            "transaction_id": f"TXN-{1000 + i}",
            "product_name": f"Item_{cat[:3].upper()}_{i}",
            "category": cat,
            "price": f"{price:.2f}",
            "quantity": str(qty),
            "sale_date": dt,
        })

    csv_path = SAMPLES_DIR / "retail_clean.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    # Companion ground truth
    gt = {
        "dataset_name": "retail_clean.csv",
        "description": "Clean baseline retail dataset without ambiguous duplicates or missing numbers.",
        "expected_disagreement_range": [0.0, 0.0],
        "expected_gate_decision": "auto_approved",
        "injected_errors_count": 0,
        "cell_ground_truth": [],
    }
    gt_path = SAMPLES_DIR / "retail_clean_ground_truth.json"
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(gt, f, indent=2)

    print(f"[OK] Generated {csv_path} ({len(rows)} rows) & {gt_path}")

def generate_contested_sample():
    random.seed(42)
    headers = ["customer_id", "customer_name", "email", "total_spend", "support_tickets", "signup_date"]
    rows = []
    ground_truth_cells = []

    names = ["Alex Rivera", "Jordan Lee", "Taylor Morgan", "Morgan Smith", "Casey Jones", "Robin Patel"]

    # Base records
    for i in range(1, 51):
        name = names[(i - 1) % len(names)]
        rows.append({
            "customer_id": f"CUST-{2000 + i}",
            "customer_name": f"{name} {i // 6}",
            "email": f"{name.lower().replace(' ', '.')}@example.com",
            "total_spend": f"{150.0 + i * 12.5:.2f}",
            "support_tickets": str(i % 4),
            "signup_date": f"2026-02-{i % 25 + 1:02d}",
        })

    # Injected Ambiguity 1: Duplicate customer names with conflicting data
    # Causes Plan 0 (keep first) vs Plan 2 (keep last) disagreement
    rows.append({
        "customer_id": "CUST-2051",
        "customer_name": "Alex Rivera 0", # duplicate of CUST-2001
        "email": "alex.rivera.updated@example.com",
        "total_spend": "320.50",
        "support_tickets": "1",
        "signup_date": "2026-03-01",
    })
    ground_truth_cells.append({
        "row_idx": 50,
        "column": "customer_name",
        "injected_issue": "Conflicting duplicate with updated email/spend",
        "correct_resolution": "Merge or retain latest record",
    })

    rows.append({
        "customer_id": "CUST-2052",
        "customer_name": "Jordan Lee 0", # duplicate of CUST-2002
        "email": "jordan.lee@example.com",
        "total_spend": "450.00",
        "support_tickets": "2",
        "signup_date": "2026-03-02",
    })

    # Injected Ambiguity 2: Null numeric spend cells
    # Causes Plan 0 (drop) vs Plan 1 (fill mean) vs Plan 2 (fill median) conflict
    for idx in [5, 12, 19, 27, 34]:
        orig_val = rows[idx]["total_spend"]
        rows[idx]["total_spend"] = "" # null missing value
        ground_truth_cells.append({
            "row_idx": idx,
            "column": "total_spend",
            "injected_issue": "Missing monetary value",
            "true_value": orig_val,
            "correct_resolution": "Impute median value",
        })

    # Injected Ambiguity 3: Ambiguous date format (03/04/2026 - March 4 or April 3?)
    rows[8]["signup_date"] = "03/04/2026"
    ground_truth_cells.append({
        "row_idx": 8,
        "column": "signup_date",
        "injected_issue": "Ambiguous slash date format (DD/MM vs MM/DD)",
        "true_value": "2026-04-03",
        "correct_resolution": "ISO 8601 normalization (2026-04-03)",
    })

    # Injected Ambiguity 4: Negative support tickets count
    rows[15]["support_tickets"] = "-2"
    ground_truth_cells.append({
        "row_idx": 15,
        "column": "support_tickets",
        "injected_issue": "Negative count of support tickets",
        "true_value": "0",
        "correct_resolution": "Rectify to 0",
    })

    csv_path = SAMPLES_DIR / "customers_contested.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    gt = {
        "dataset_name": "customers_contested.csv",
        "description": "Contested dataset with duplicate conflict, missing numeric spend, and ambiguous date formatting.",
        "expected_disagreement_range": [0.25, 0.95],
        "expected_gate_decision": "needs_human_clarification",
        "injected_errors_count": len(ground_truth_cells),
        "cell_ground_truth": ground_truth_cells,
    }
    gt_path = SAMPLES_DIR / "customers_contested_ground_truth.json"
    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump(gt, f, indent=2)

    print(f"[OK] Generated {csv_path} ({len(rows)} rows) & {gt_path}")

def main():
    generate_clean_sample()
    generate_contested_sample()
    print("[PASS] Sample generation complete.")

if __name__ == "__main__":
    main()
