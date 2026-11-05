#!/usr/bin/env python3
"""Token check script for ConsensusProbe 2.0 (Rule R5).

Ensures all colors originate from tokens.css via CSS variables or semantic Tailwind classes.
Flags hex, rgb, rgba, hsl, and hsla literals outside tokens.css in frontend/src/.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "frontend" / "src"

# Allowed brand-specific logo fills (official Google G logo asset)
BRAND_ALLOWLIST = {
    "#4285F4", "#4285f4",
    "#34A853", "#34a853",
    "#FBBC05", "#fbbc05",
    "#EA4335", "#ea4335",
}

HEX_PATTERN = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGB_PATTERN = re.compile(r"\b(rgba?|hsla?)\s*\(")

def check_tokens() -> int:
    if not SRC_DIR.is_dir():
        print(f"[FAIL] frontend/src directory not found at {SRC_DIR}")
        return 1

    violations = []

    for root, _, files in os.walk(SRC_DIR):
        for f in files:
            if not f.endswith((".ts", ".tsx", ".css")):
                continue
            if f == "tokens.css":
                continue

            filepath = Path(root) / f
            rel_path = filepath.relative_to(ROOT)

            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as fp:
                    for line_num, line in enumerate(fp, 1):
                        stripped = line.strip()
                        # Ignore comments
                        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                            continue

                        # Check hex literals
                        for match in HEX_PATTERN.findall(line):
                            if match in BRAND_ALLOWLIST:
                                continue
                            violations.append((str(rel_path), line_num, f"Hex literal: {match}", stripped))

                        # Check rgb/rgba/hsl/hsla literals
                        for match in RGB_PATTERN.findall(line):
                            violations.append((str(rel_path), line_num, f"Color function literal: {match}", stripped))

            except OSError as e:
                print(f"[WARN] Could not read {rel_path}: {e}")

    if violations:
        print(f"[FAIL] Found {len(violations)} raw color literal(s) outside tokens.css (Rule R5 violation):")
        for file, line, msg, code in violations:
            print(f"  {file}:{line} -> {msg} | `{code}`")
        return 1

    print("[PASS] Token check clean: 0 raw color literals outside tokens.css.")
    return 0

if __name__ == "__main__":
    sys.exit(check_tokens())
