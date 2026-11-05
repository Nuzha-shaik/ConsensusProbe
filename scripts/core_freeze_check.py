#!/usr/bin/env python3
"""Core freeze check script for ConsensusProbe 2.0 (Rule R1).

Verifies that git diff against pre-cp2 baseline touches NO backend paths
and touches ONLY explicitly allowed writable paths.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Allowed writable paths per Rule R1 + standard repo tooling
ALLOWED_PREFIXES = (
    "frontend/",
    "scripts/",
    "docs/",
    "report/",
    ".github/",
)

ALLOWED_EXACT_FILES = {
    "Makefile",
    "README.md",
    "firebase.json",
    ".firebaserc",
    "firestore.rules",
    "firestore.indexes.json",
    "update.tex",
    "playwright.config.ts",
    ".gitignore",
}

def load_backend_paths() -> list[str]:
    paths_file = ROOT / "scripts" / "backend_paths.txt"
    if not paths_file.is_file():
        return ["backend/", "research/"]
    lines = []
    with open(paths_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line.replace("\\", "/"))
    return lines

def main() -> int:
    cmd = ["git", "diff", "--name-only", "pre-cp2"]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[FAIL] git diff failed: {res.stderr}")
        return 1

    changed = [f.strip().replace("\\", "/") for f in res.stdout.splitlines() if f.strip()]
    backend_paths = load_backend_paths()

    backend_violations = []
    writable_violations = []

    for path in changed:
        # Check backend violation
        is_backend = any(path.startswith(bp) or path == bp.rstrip("/") for bp in backend_paths)
        if is_backend:
            backend_violations.append(path)

        # Check writable scope violation (R1)
        in_allowed_prefix = any(path.startswith(pfx) for pfx in ALLOWED_PREFIXES)
        is_allowed_file = path in ALLOWED_EXACT_FILES
        if not (in_allowed_prefix or is_allowed_file):
            writable_violations.append(path)

    has_error = False
    if backend_violations:
        print("[FAIL] Core Freeze Violation: Attempted modification to frozen backend paths:")
        for v in backend_violations:
            print(f"  - {v}")
        has_error = True

    if writable_violations:
        print("[FAIL] Rule R1 Violation: Attempted modification outside writable paths:")
        for v in writable_violations:
            print(f"  - {v}")
        has_error = True

    if not has_error:
        print(f"[PASS] Core freeze clean: {len(changed)} changed file(s) verified against pre-cp2 baseline.")
        return 0
    return 1

if __name__ == "__main__":
    sys.exit(main())
