#!/usr/bin/env python3
"""Verify that results/numbers.tex macros exactly match computed results/*.json."""
import os
import re
import sys
from scripts.make_numbers import compute_macros

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NUMBERS_TEX = os.path.join(ROOT, "results", "numbers.tex")

MACRO_REGEX = re.compile(r"\\newcommand\{\\([a-zA-Z0-9]+)\}\{(.*)\}")

def main():
    if not os.path.isfile(NUMBERS_TEX):
        print(f"FAIL: {NUMBERS_TEX} does not exist.")
        sys.exit(1)

    expected_macros = compute_macros()

    existing_macros = {}
    with open(NUMBERS_TEX, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            match = MACRO_REGEX.match(line)
            if match:
                existing_macros[match.group(1)] = match.group(2)

    mismatches = []
    for k, v in expected_macros.items():
        if k not in existing_macros:
            mismatches.append(f"Missing macro: {k}")
        elif existing_macros[k] != v:
            mismatches.append(f"Value mismatch for {k}: expected '{v}', found '{existing_macros[k]}'")

    for k in existing_macros:
        if k not in expected_macros:
            mismatches.append(f"Unexpected extra macro: {k}")

    if mismatches:
        for m in mismatches[:10]:
            print(f"FAIL: {m}")
        sys.exit(1)

    print(f"check_numbers passed: all {len(expected_macros)} macros match results/*.json perfectly.")
    sys.exit(0)

if __name__ == "__main__":
    main()
