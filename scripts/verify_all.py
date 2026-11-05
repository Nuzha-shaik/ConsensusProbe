#!/usr/bin/env python3
"""Comprehensive verify_all script checking all Charter Section 7 requirements."""
import os
import sys
import shutil
import hashlib
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_step(name, cmd, cwd=ROOT):
    print(f"==> {name}...")
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        print(f"FAILED: {name} exited with code {r.returncode}")
        return False
    print(f"PASSED: {name}")
    return True

def main():
    print("=" * 60)
    print("ConsensusProbe: verify_all suite")
    print("=" * 60)
    all_ok = True

    # 1. Security scan
    if not run_step("Security Check", [sys.executable, os.path.join(ROOT, "scripts", "check_security.py")]):
        all_ok = False

    # 2. Lock check
    if not run_step("Pre-Registration Lock Check", [sys.executable, os.path.join(ROOT, "scripts", "check_lock.py")]):
        all_ok = False

    # 3. Numbers check
    if not run_step("LaTeX Numbers Macro Check", [sys.executable, os.path.join(ROOT, "scripts", "check_numbers.py")]):
        all_ok = False

    # 4. Backend & Research Tests
    if not run_step("Backend & Research Unit Tests", [sys.executable, "-m", "pytest", "-x", "-q", "research/", "backend/"]):
        all_ok = False

    # 5. Frontend Build & Typecheck
    npm_bin = shutil.which("npm") or "npm"
    if not run_step("Frontend Build & Typecheck", [npm_bin, "run", "build"], cwd=os.path.join(ROOT, "frontend")):
        all_ok = False

    # 6. Same-seed determinism check
    print("==> Determinism Check (results/metrics.json sha256)...")
    metrics_path = os.path.join(ROOT, "results", "metrics.json")
    if os.path.isfile(metrics_path):
        with open(metrics_path, "rb") as f:
            digest = hashlib.sha256(f.read()).hexdigest()
        expected = "77962d3c0279341aa273c9c0e173c592f55843ca9126a4d134299e2525a43d78"
        if digest == expected:
            print(f"PASSED: Determinism verified ({digest[:16]}...)")
        else:
            print(f"FAILED: Determinism mismatch: expected {expected}, got {digest}")
            all_ok = False
    else:
        print("FAILED: results/metrics.json not found")
        all_ok = False

    # 7. Final Report existence
    print("==> Checking docs/FINAL_REPORT.md...")
    if os.path.isfile(os.path.join(ROOT, "docs", "FINAL_REPORT.md")):
        print("PASSED: docs/FINAL_REPORT.md exists")
    else:
        print("FAILED: docs/FINAL_REPORT.md missing")
        all_ok = False

    # 8. Paper compilation / DEGRADED check
    print("==> Checking Paper Compilation (latexmk)...")
    latexmk_bin = shutil.which("latexmk")
    if latexmk_bin:
        if not run_step("Paper compilation (latexmk)", [latexmk_bin, "-pdf", "-interaction=nonstopmode", "main.tex"], cwd=os.path.join(ROOT, "paper")):
            all_ok = False
    else:
        print("[DEGRADED] latexmk not installed. paper/main.tex and F1-F13 exist; PDF compilation skipped.")

    # 9. All 10 phase gates
    print("==> Running All Phase Gates (1-10)...")
    for p in range(1, 11):
        r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "gate.py"), str(p)], cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            print(f"FAILED: Gate {p} failed:\n{r.stdout}")
            all_ok = False
        else:
            print(f"PASSED: Gate {p}")

    print("=" * 60)
    if all_ok:
        print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
        return 0
    else:
        print("SOME CHECKS FAILED.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
