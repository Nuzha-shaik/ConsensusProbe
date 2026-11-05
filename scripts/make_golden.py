#!/usr/bin/env python3
"""Generate and lock the golden answer key artifacts for ConsensusProbe (Rule R1).

Reads docs/golden/input/3_-Badly-Structured-Sales-Data-3.xlsx and outputs:
1. docs/golden/golden_truth.csv
2. docs/golden/golden_metrics.json
3. docs/golden/dirty3.csv
4. docs/golden/GOLDEN.sha256
"""
from __future__ import annotations

import argparse
import csv
import datetime
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = ROOT / "docs" / "golden"
INPUT_XLSX = GOLDEN_DIR / "input" / "3_-Badly-Structured-Sales-Data-3.xlsx"
TRUTH_CSV = GOLDEN_DIR / "golden_truth.csv"
METRICS_JSON = GOLDEN_DIR / "golden_metrics.json"
DIRTY_CSV = GOLDEN_DIR / "dirty3.csv"
SHA256_FILE = GOLDEN_DIR / "GOLDEN.sha256"

def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def verify_integrity() -> bool:
    if not SHA256_FILE.is_file():
        print(f"[FAIL] Missing sha256 checksum file: {SHA256_FILE}", file=sys.stderr)
        return False
    all_ok = True
    with open(SHA256_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(maxsplit=1)
            if len(parts) != 2:
                continue
            expected_hash, rel_path = parts
            target_path = ROOT / rel_path.replace("/", os.sep)
            if not target_path.is_file():
                print(f"[FAIL] Target file missing: {rel_path}", file=sys.stderr)
                all_ok = False
                continue
            actual_hash = compute_sha256(target_path)
            if actual_hash != expected_hash:
                print(f"[FAIL] Checksum mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}", file=sys.stderr)
                all_ok = False
            else:
                print(f"[PASS] {rel_path}")
    return all_ok

def generate_golden() -> int:
    if not INPUT_XLSX.is_file():
        print(f"Error: Missing input workbook at {INPUT_XLSX}", file=sys.stderr)
        return 1

    import openpyxl

    wb = openpyxl.load_workbook(INPUT_XLSX, data_only=True)
    if "Clean 3" not in wb.sheetnames or "Dirty 3" not in wb.sheetnames:
        print("Error: Workbook must contain sheets 'Clean 3' and 'Dirty 3'", file=sys.stderr)
        return 1

    # 1. Process Clean 3 (the answer key)
    ws_clean = wb["Clean 3"]
    clean_rows = []
    header = [cell.value for cell in ws_clean[1]]
    for r in range(2, ws_clean.max_row + 1):
        vals = [ws_clean.cell(r, c).value for c in range(1, len(header) + 1)]
        if all(v is None for v in vals):
            continue
        ship_mode, segment, order_id, order_date, sales = vals
        if isinstance(order_date, (datetime.datetime, datetime.date)):
            order_date_str = order_date.strftime("%Y-%m-%d")
        else:
            order_date_str = str(order_date).strip()
        sales_val = float(sales)
        clean_rows.append({
            "Ship Mode": str(ship_mode).strip(),
            "Segment": str(segment).strip(),
            "Order ID": str(order_id).strip(),
            "Order Date": order_date_str,
            "Sales": sales_val,
        })

    # Sort per spec: Ship Mode, Segment, Order ID (ascending)
    clean_rows.sort(key=lambda x: (x["Ship Mode"], x["Segment"], x["Order ID"]))

    # Write golden_truth.csv
    with open(TRUTH_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Ship Mode", "Segment", "Order ID", "Order Date", "Sales"])
        for row in clean_rows:
            writer.writerow([
                row["Ship Mode"],
                row["Segment"],
                row["Order ID"],
                row["Order Date"],
                f"{row['Sales']:.9g}" if isinstance(row['Sales'], float) else row['Sales'],
            ])
    print(f"Wrote {len(clean_rows)} rows to {TRUTH_CSV}")

    # 2. Compute golden metrics
    total_sales = sum(r["Sales"] for r in clean_rows)
    ship_modes: dict[str, dict[str, float | int]] = {}
    for r in clean_rows:
        sm = r["Ship Mode"]
        if sm not in ship_modes:
            ship_modes[sm] = {"orders": 0, "sales": 0.0}
        ship_modes[sm]["orders"] += 1
        ship_modes[sm]["sales"] += r["Sales"]
    for sm in ship_modes:
        ship_modes[sm]["sales"] = round(ship_modes[sm]["sales"], 2)

    segments: dict[str, dict[str, float | int]] = {}
    for r in clean_rows:
        seg = r["Segment"]
        if seg not in segments:
            segments[seg] = {"orders": 0, "sales": 0.0}
        segments[seg]["orders"] += 1
        segments[seg]["sales"] += r["Sales"]
    for seg in segments:
        segments[seg]["sales"] = round(segments[seg]["sales"], 2)

    groups_12: dict[str, dict[str, float | int]] = {}
    for r in clean_rows:
        key = f"{r['Ship Mode']} x {r['Segment']}"
        if key not in groups_12:
            groups_12[key] = {"orders": 0, "sales": 0.0}
        groups_12[key]["orders"] += 1
        groups_12[key]["sales"] += r["Sales"]
    for k in groups_12:
        groups_12[k]["sales"] = round(groups_12[k]["sales"], 2)

    metrics_data = {
        "record_count": len(clean_rows),
        "total_sales": round(total_sales, 2),
        "total_sales_raw": total_sales,
        "rows_kept": len(clean_rows),
        "rows_dropped": 1,  # Grand Total
        "cells_imputed": 0,
        "ship_mode_breakdown": ship_modes,
        "segment_breakdown": segments,
        "group_12_breakdown": groups_12,
        "completeness_before": round(3.0 / 14.0, 4),
        "completeness_after": 1.0,
        "mismatches_vs_truth": 0,
    }

    with open(METRICS_JSON, "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)
    print(f"Wrote metrics to {METRICS_JSON}")

    # 3. Export Dirty 3 as CSV
    ws_dirty = wb["Dirty 3"]
    with open(DIRTY_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        for r in range(1, ws_dirty.max_row + 1):
            row_vals = []
            for c in range(1, 15):
                val = ws_dirty.cell(r, c).value
                if val is None:
                    row_vals.append("")
                elif isinstance(val, (datetime.datetime, datetime.date)):
                    row_vals.append(val.strftime("%Y-%m-%d"))
                elif isinstance(val, float):
                    row_vals.append(repr(val))
                else:
                    row_vals.append(str(val))
            writer.writerow(row_vals)
    print(f"Wrote Dirty 3 to {DIRTY_CSV}")

    # 4. Generate GOLDEN.sha256
    files_to_hash = [
        (INPUT_XLSX, "docs/golden/input/3_-Badly-Structured-Sales-Data-3.xlsx"),
        (TRUTH_CSV, "docs/golden/golden_truth.csv"),
        (METRICS_JSON, "docs/golden/golden_metrics.json"),
        (DIRTY_CSV, "docs/golden/dirty3.csv"),
    ]
    checksum_lines = []
    for abs_p, rel_p in files_to_hash:
        checksum_lines.append(f"{compute_sha256(abs_p)}  {rel_p}")

    with open(SHA256_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(checksum_lines) + "\n")
    print(f"Wrote locked checksums to {SHA256_FILE}")

    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="Generate and lock golden answer key.")
    parser.add_argument("--check", action="store_true", help="Verify integrity of locked files against GOLDEN.sha256")
    args = parser.parse_args()

    if args.check:
        ok = verify_integrity()
        return 0 if ok else 1
    return generate_golden()

if __name__ == "__main__":
    sys.exit(main())
