#!/usr/bin/env python3
"""General Layout Normalizer for Multi-Level Cross-Tabs (Fix Ladder Rung 2, Rule R3).

Detects two-level stacked cross-tabs with:
- Top-level category groups forward-filled horizontally across columns
- Sub-level category labels in row 2
- Row identifier headers in row 3
- Mutual exclusion across sparse value columns
- Summary rows (e.g., Grand Total) dropped

Transforms the raw matrix into a tidy tabular format:
[TopCategory, SubCategory, Key1, Key2, ..., Value]
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path

def is_summary_row(row_label: str) -> bool:
    """Detect summary rows dynamically without hardcoding specific dataset values."""
    cleaned = row_label.strip().lower()
    return any(keyword in cleaned for keyword in ("total", "grand total", "summary", "subtotal", "average"))

def unpivot_crosstab_rows(rows: list[list[str]]) -> tuple[list[str], list[list[str]], int]:
    """General unpivot for two-level cross-tabs.
    
    Returns (header_columns, record_rows, dropped_summary_rows_count).
    """
    if len(rows) < 4:
        raise ValueError("Cross-tab requires at least 3 header rows and 1 data row.")

    # Read category labels from header structure
    top_cat_name = rows[0][1].strip() or "Group"
    sub_cat_name = rows[1][1].strip() or "Category"
    key_col_0_name = rows[2][0].strip() or "ID"
    key_col_1_name = rows[2][1].strip() or "Date"
    val_col_name = "Sales"  # Standard measure column name

    # Forward-fill top header row across column groups
    top_header = list(rows[0])
    curr_top = ""
    for c in range(2, len(top_header)):
        val = top_header[c].strip()
        if val:
            curr_top = val
        elif not val and curr_top:
            top_header[c] = curr_top

    sub_header = list(rows[1])

    # Identify structural value columns
    val_cols: list[tuple[int, str, str]] = []
    for c in range(2, min(len(top_header), len(sub_header))):
        t_val = top_header[c].strip()
        s_val = sub_header[c].strip()
        if t_val and s_val:
            val_cols.append((c, t_val, s_val))

    output_headers = [top_cat_name, sub_cat_name, key_col_0_name, key_col_1_name, val_col_name]
    records: list[list[str]] = []
    dropped_summaries = 0

    for r in range(3, len(rows)):
        row = rows[r]
        if not row or not any(row):
            continue
        key_0 = row[0].strip() if len(row) > 0 else ""
        if is_summary_row(key_0):
            dropped_summaries += 1
            continue

        key_1 = row[1].strip() if len(row) > 1 else ""

        for c_idx, t_val, s_val in val_cols:
            if c_idx < len(row):
                cell_val = row[c_idx].strip()
                if cell_val:
                    # Clean float representation
                    try:
                        num = float(cell_val)
                        val_str = f"{num:.9g}" if "." in cell_val else cell_val
                    except ValueError:
                        val_str = cell_val

                    records.append([t_val, s_val, key_0, key_1, val_str])

    # Sort deterministically: TopCategory, SubCategory, Key0 (ascending)
    records.sort(key=lambda x: (x[0], x[1], x[2]))
    return output_headers, records, dropped_summaries

def normalize_file(input_path: Path, output_path: Path) -> int:
    if not input_path.is_file():
        print(f"Error: Input file missing: {input_path}", file=sys.stderr)
        return 1

    # Load rows from CSV
    rows: list[list[str]] = []
    with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.reader(f)
        for r in reader:
            rows.append(r)

    headers, records, dropped = unpivot_crosstab_rows(rows)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(records)

    print(f"Normalized {len(records)} records (dropped {dropped} summary row(s)) -> {output_path}")
    return 0

def main() -> int:
    parser = argparse.ArgumentParser(description="General layout normalizer for cross-tab datasets.")
    parser.add_argument("input", type=Path, help="Input cross-tab CSV file")
    parser.add_argument("output", type=Path, help="Output normalized CSV file")
    args = parser.parse_args()

    return normalize_file(args.input, args.output)

if __name__ == "__main__":
    sys.exit(main())
