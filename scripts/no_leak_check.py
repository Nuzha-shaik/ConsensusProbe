#!/usr/bin/env python3
"""Enforce Rule R2 (NO LEAKAGE) for ConsensusProbe.

Scans application source code in frontend/src/ and backend/ to ensure:
1. No answer-key sheet names ("Clean 3") or truth filenames ("golden_truth", "golden_metrics").
2. No golden answer constants (391721, 49332, 227613, 195580, 121885, 74255, 93758, 21017)
   hardcoded as literals in application logic.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Directories to scan for forbidden leakage
SCAN_DIRS = [
    ROOT / "frontend" / "src",
    ROOT / "backend" / "app",
]

# Forbidden string / literal patterns in application code
FORBIDDEN_PATTERNS = [
    (re.compile(r'\bClean 3\b', re.IGNORECASE), "Sheet name 'Clean 3'"),
    (re.compile(r'\bgolden_truth\b', re.IGNORECASE), "Answer key filename 'golden_truth'"),
    (re.compile(r'\bgolden_metrics\b', re.IGNORECASE), "Answer key filename 'golden_metrics'"),
    (re.compile(r'\b391721(?:\.91)?\b'), "Golden total sales constant 391721.91"),
    (re.compile(r'\b49332(?:\.57)?\b'), "Golden First Class sales constant 49332.57"),
    (re.compile(r'\b227613(?:\.55)?\b'), "Golden Standard Class sales constant 227613.55"),
    (re.compile(r'\b195580(?:\.97)?\b'), "Golden Consumer segment sales constant 195580.97"),
    (re.compile(r'\b121885(?:\.93)?\b'), "Golden Corporate segment sales constant 121885.93"),
    (re.compile(r'\b74255(?:\.00)?\b'), "Golden Home Office sales constant 74255.00"),
    (re.compile(r'\b93758(?:\.61)?\b'), "Golden Second Class sales constant 93758.61"),
    (re.compile(r'\b21017(?:\.17)?\b'), "Golden Same Day sales constant 21017.17"),
]

def check_file(path: Path) -> list[str]:
    # Skip test files and fixtures
    p_str = str(path).replace("\\", "/")
    if "/__tests__/" in p_str or "/__fixtures__/" in p_str or ".test." in p_str or ".spec." in p_str:
        return []

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        return [f"Could not read {path}: {e}"]

    violations = []
    for pattern, desc in FORBIDDEN_PATTERNS:
        matches = pattern.findall(text)
        if matches:
            violations.append(f"{path.relative_to(ROOT)}: Found forbidden literal '{matches[0]}' ({desc})")
    return violations

def main() -> int:
    print("=" * 60)
    print("ConsensusProbe: scripts/no_leak_check.py (Rule R2)")
    print("=" * 60)

    all_violations: list[str] = []
    for scan_dir in SCAN_DIRS:
        if not scan_dir.is_dir():
            continue
        for root, _, files in os.walk(scan_dir):
            for file in files:
                if file.endswith((".ts", ".tsx", ".js", ".jsx", ".py")):
                    p = Path(root) / file
                    all_violations.extend(check_file(p))

    if all_violations:
        print(f"[FAIL] Found {len(all_violations)} leakage violation(s):", file=sys.stderr)
        for v in all_violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    print("[PASS] No-leak check clean: 0 golden literals or truth filenames found in application code.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
