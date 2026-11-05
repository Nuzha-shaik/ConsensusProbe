#!/usr/bin/env python3
"""Phase gate checker."""
import subprocess, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(cmd):
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return r.returncode == 0

def gate_1():
    checks = []
    for d in ['frontend', 'backend/app', 'research', 'scripts', 'docs', 'prereg', 'results', 'refs', 'configs', 'paper']:
        checks.append((f"dir {d}", os.path.isdir(os.path.join(ROOT, d))))
    checks.append(("STATE.md", os.path.isfile(os.path.join(ROOT, 'docs', 'STATE.md'))))
    checks.append(("DEPS.md", os.path.isfile(os.path.join(ROOT, 'docs', 'DEPS.md'))))
    checks.append(("ARTIFACTS.md", os.path.isfile(os.path.join(ROOT, 'docs', 'ARTIFACTS.md'))))
    checks.append(("security", run([sys.executable, os.path.join(ROOT, 'scripts', 'check_security.py')])))
    checks.append(("related_work.csv", os.path.isfile(os.path.join(ROOT, 'refs', 'related_work.csv'))))
    return checks

def gate_2():
    checks = [
        ("research/operations.py", os.path.isfile(os.path.join(ROOT, 'research', 'operations.py'))),
        ("research/patch.py", os.path.isfile(os.path.join(ROOT, 'research', 'patch.py'))),
        ("research/mock_provider.py", os.path.isfile(os.path.join(ROOT, 'research', 'mock_provider.py'))),
        ("P2 tests", run([sys.executable, '-m', 'pytest', '-x', '-q', os.path.join(ROOT, 'research', 'tests')])),
    ]
    return checks

def gate_3():
    return [
        ("research/track_s.py", os.path.isfile(os.path.join(ROOT, 'research', 'track_s.py'))),
        ("configs/frozen.toml", os.path.isfile(os.path.join(ROOT, 'configs', 'frozen.toml'))),
        ("results/dev_calibration.json", os.path.isfile(os.path.join(ROOT, 'results', 'dev_calibration.json'))),
        ("P3 tests", run([sys.executable, '-m', 'pytest', '-x', '-q', os.path.join(ROOT, 'research', 'tests')])),
    ]

def gate_4():
    return [
        ("research/consensus.py", os.path.isfile(os.path.join(ROOT, 'research', 'consensus.py'))),
        ("research/policies.py", os.path.isfile(os.path.join(ROOT, 'research', 'policies.py'))),
        ("P4 tests", run([sys.executable, '-m', 'pytest', '-x', '-q', os.path.join(ROOT, 'research', 'tests')])),
    ]

def gate_5():
    return [
        ("research/canary.py", os.path.isfile(os.path.join(ROOT, 'research', 'canary.py'))),
        ("prereg/PREREG.md", os.path.isfile(os.path.join(ROOT, 'prereg', 'PREREG.md'))),
        ("prereg/lock.json", os.path.isfile(os.path.join(ROOT, 'prereg', 'lock.json'))),
        ("lock check", run([sys.executable, os.path.join(ROOT, 'scripts', 'check_lock.py')])),
    ]

def gate_6():
    return [
        ("results/metrics.json", os.path.isfile(os.path.join(ROOT, 'results', 'metrics.json'))),
        ("results/hypotheses.json", os.path.isfile(os.path.join(ROOT, 'results', 'hypotheses.json'))),
        ("results/ablations.json", os.path.isfile(os.path.join(ROOT, 'results', 'ablations.json'))),
    ]

def gate_7():
    return [
        ("backend/app/main.py", os.path.isfile(os.path.join(ROOT, 'backend', 'app', 'main.py'))),
        ("backend/app/models.py", os.path.isfile(os.path.join(ROOT, 'backend', 'app', 'models.py'))),
        ("backend tests", run([sys.executable, '-m', 'pytest', '-x', '-q', os.path.join(ROOT, 'backend', 'tests')])),
    ]

def gate_8():
    pkg = os.path.join(ROOT, 'frontend', 'package.json')
    checks = [("frontend/package.json", os.path.isfile(pkg))]
    if os.path.isdir(os.path.join(ROOT, 'frontend', 'node_modules')):
        checks.append(("npm build", run(['npm', 'run', 'build', '--prefix', os.path.join(ROOT, 'frontend')])))
    return checks

def gate_9():
    return [
        ("results/numbers.tex", os.path.isfile(os.path.join(ROOT, 'results', 'numbers.tex'))),
        ("paper/main.tex", os.path.isfile(os.path.join(ROOT, 'paper', 'main.tex'))),
        ("figures", all(
            os.path.isfile(os.path.join(ROOT, 'paper', 'figures', f'F{i}.pdf')) or
            os.path.isfile(os.path.join(ROOT, 'paper', 'figures', f'F{i}.png'))
            for i in range(1, 14)
        )),
    ]

def gate_10():
    return [
        ("README.md", os.path.isfile(os.path.join(ROOT, 'README.md'))),
        ("LICENSE", os.path.isfile(os.path.join(ROOT, 'LICENSE'))),
        (".env.example", os.path.isfile(os.path.join(ROOT, '.env.example'))),
        ("FINAL_REPORT.md", os.path.isfile(os.path.join(ROOT, 'docs', 'FINAL_REPORT.md'))),
    ]

GATES = {1: gate_1, 2: gate_2, 3: gate_3, 4: gate_4, 5: gate_5,
         6: gate_6, 7: gate_7, 8: gate_8, 9: gate_9, 10: gate_10}

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <phase>"); sys.exit(1)
    phase = int(sys.argv[1])
    if phase not in GATES:
        print(f"Unknown phase: {phase}"); sys.exit(1)
    checks = GATES[phase]()
    ok = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed: ok = False
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
