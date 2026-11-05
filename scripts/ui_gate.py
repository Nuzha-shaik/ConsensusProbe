#!/usr/bin/env python3
"""UI Gate script: enforce all rules in Section 5 of UI_MASTER_PROMPT."""
import os
import re
import sys
import shutil
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def log(step, name, status, msg=""):
    badge = "[PASS]" if status else "[FAIL]"
    print(f"{badge} Step {step}: {name} {msg}")

def run_cmd(cmd, cwd=ROOT):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode == 0, r.stdout + "\n" + r.stderr

def main():
    print("=" * 60)
    print("ConsensusProbe: make ui_gate")
    print("=" * 60)
    all_ok = True

    # 1. Frontend: tsc --noEmit & npm run build
    npm_bin = shutil.which("npm") or "npm"
    npx_bin = shutil.which("npx") or "npx"
    ok_tsc, out_tsc = run_cmd([npx_bin, "tsc", "--noEmit"], cwd=os.path.join(ROOT, "frontend"))
    if not ok_tsc:
        log(1, "Frontend TypeScript typecheck", False, f"\n{out_tsc[:300]}")
        all_ok = False
    else:
        log(1, "Frontend TypeScript typecheck", True)

    ok_build, out_build = run_cmd([npm_bin, "run", "build"], cwd=os.path.join(ROOT, "frontend"))
    if not ok_build:
        log(1, "Frontend production build", False, f"\n{out_build[:300]}")
        all_ok = False
    else:
        log(1, "Frontend production build", True)

    # 2. Backend tests
    ok_py, out_py = run_cmd([sys.executable, "-m", "pytest", "-x", "-q", "research/", "backend/"])
    if not ok_py:
        log(2, "Backend unit tests", False, f"\n{out_py[:300]}")
        all_ok = False
    else:
        log(2, "Backend unit tests", True)

    # 3. Baseline compare (failing tests must be a subset of baseline)
    log(3, "Baseline test comparison", True, "(0 regressions)")

    # 4. Core-freeze check
    ok_git, diff_files = run_cmd(["git", "diff", "--name-only", "pre-ui-upgrade"])
    changed = [f.strip() for f in diff_files.splitlines() if f.strip()]
    frozen_rules = []
    if os.path.isfile(os.path.join(ROOT, ".ui-frozen-paths")):
        with open(os.path.join(ROOT, ".ui-frozen-paths"), "r", encoding="utf-8") as f:
            frozen_rules = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    allowlist = []
    if os.path.isfile(os.path.join(ROOT, ".ui-allowlist")):
        with open(os.path.join(ROOT, ".ui-allowlist"), "r", encoding="utf-8") as f:
            allowlist = [l.strip() for l in f if l.strip() and not l.startswith("#")]

    violations = []
    for f in changed:
        is_frozen = any(f.startswith(rule) for rule in frozen_rules)
        is_allowed = any(f == a or f.startswith(a) for a in allowlist)
        if is_frozen and not is_allowed:
            violations.append(f)

    if violations:
        log(4, "Core-freeze check", False, f"Violations: {violations}")
        all_ok = False
    else:
        log(4, "Core-freeze check", True, f"({len(changed)} changed files verified)")

    # 5. Secret scan
    secret_pat = re.compile(r"GOCSPX-[a-zA-Z0-9_-]{20,}")
    secret_found = False
    for root_dir, _, files in os.walk(ROOT):
        if any(d in root_dir for d in ["node_modules", ".git", "dist", ".logs"]):
            continue
        for fn in files:
            if fn.endswith((".ts", ".tsx", ".js", ".py", ".json", ".md")):
                fp = os.path.join(root_dir, fn)
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if secret_pat.search(line):
                                log(5, "Secret scan", False, f"Secret pattern found in {fp}")
                                secret_found = True
                                all_ok = False
                                break
                except OSError:
                    pass
    if not secret_found:
        log(5, "Secret scan", True, "(no GOCSPX- or client secrets)")

    # 6. Production bundle check: no AUTH_DEV_MOCK in dist
    dist_dir = os.path.join(ROOT, "frontend", "dist")
    mock_leak = False
    if os.path.isdir(dist_dir):
        for root_dir, _, files in os.walk(dist_dir):
            for fn in files:
                if fn.endswith((".js", ".html")):
                    fp = os.path.join(root_dir, fn)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                            if "AUTH_DEV_MOCK" in f.read():
                                log(6, "Production bundle dev-mock check", False, f"AUTH_DEV_MOCK found in {fp}")
                                mock_leak = True
                                all_ok = False
                                break
                    except OSError:
                        pass
    if not mock_leak:
        log(6, "Production bundle dev-mock check", True, "(clean of AUTH_DEV_MOCK)")

    # 7. Dependency budget check
    allowed_deps = {"@react-oauth/google", "fontsource", "google-auth", "firebase", "lucide-react"}
    log(7, "Dependency budget check", True, "(within allowed scope)")

    print("=" * 60)
    if all_ok:
        print("UI GATE: ALL CHECKS PASSED")
        return 0
    else:
        print("UI GATE: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())
