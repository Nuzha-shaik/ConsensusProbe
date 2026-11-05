#!/usr/bin/env python3
"""Forbidden literals check script for ConsensusProbe 2.0 (Rule R2).

Ensures headline numbers from old mockups (98.4, 94.2, 58%, etc.) are not hardcoded
into frontend source components.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "frontend" / "src"

# Forbidden metric literals from old mockup benchmarks
FORBIDDEN_PATTERNS = [
    (re.compile(r"\b98\.4%?\b"), "Forbidden literal 98.4 (old mock headline)"),
    (re.compile(r"\b94\.2%?\b"), "Forbidden literal 94.2 (old mock headline)"),
    (re.compile(r"\b58%?\b"), "Forbidden literal 58% (old mock headline)"),
]

def check_literals() -> int:
    if not SRC_DIR.is_dir():
        print(f"[FAIL] frontend/src directory not found at {SRC_DIR}")
        return 1

    violations = []

    for root, _, files in os.walk(SRC_DIR):
        for f in files:
            if not f.endswith((".ts", ".tsx", ".html")):
                continue
            # Allow tests or test fixtures to mention forbidden values in negative tests
            if "__tests__" in root or "__fixtures__" in root:
                continue

            filepath = Path(root) / f
            rel_path = filepath.relative_to(ROOT)

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
                    for line_num, line in enumerate(fp, 1):
                        stripped = line.strip()
                        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                            continue

                        for pattern, desc in FORBIDDEN_PATTERNS:
                            if pattern.search(line):
                                violations.append((str(rel_path), line_num, desc, stripped))

            except OSError as e:
                print(f"[WARN] Could not read {rel_path}: {e}")

    if violations:
        print(f"[FAIL] Found {len(violations)} forbidden literal(s) in frontend source (Rule R2 violation):")
        for file, line, msg, code in violations:
            print(f"  {file}:{line} -> {msg} | `{code}`")
        return 1

    print("[PASS] No-literals check clean: 0 forbidden mock literals found in frontend/src.")
    return 0

if __name__ == "__main__":
    sys.exit(check_literals())
