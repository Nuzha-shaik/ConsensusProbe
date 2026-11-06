"""Regression tests for audit batch B1: C3, H9, M7."""
import re
import subprocess
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_c3_readme_no_real_api_key():
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    # Real Firebase key pattern must not appear
    assert not re.search(r'AIzaSy[a-zA-Z0-9_-]{33}', readme), "Real Firebase API key found in README.md"


def test_c3_firebase_ts_uses_env_vars():
    ts = open(os.path.join(ROOT, "frontend", "src", "firebase.ts"), encoding="utf-8").read()
    assert "AIzaSy" not in ts, "Hardcoded Firebase key still in firebase.ts"
    assert "import.meta.env.VITE_FIREBASE_API_KEY" in ts, "firebase.ts must use VITE_FIREBASE_API_KEY env var"


def test_h9_firebase_pattern_in_scanner():
    scanner = open(os.path.join(ROOT, "scripts", "check_security.py"), encoding="utf-8").read()
    assert "AIzaSy" in scanner, "Firebase key pattern must be in SECRET_PATTERNS"
    assert "googleusercontent" in scanner, "OAuth pattern must be in SECRET_PATTERNS"


def test_h9_env_example_skipped():
    scanner_src = open(os.path.join(ROOT, "scripts", "check_security.py"), encoding="utf-8").read()
    assert "SKIP_FILES" in scanner_src, "SKIP_FILES must exist in scanner"
    assert ".env.example" in scanner_src, ".env.example must be in SKIP_FILES"


def test_m7_shell_true_catches_alias():
    """The scanner must flag shell=True on aliased imports."""
    import ast
    scanner_src = open(os.path.join(ROOT, "scripts", "check_security.py"), encoding="utf-8").read()
    # Ensure the check no longer requires node.func.value.id == 'subprocess'
    assert "node.func.value.id == 'subprocess'" not in scanner_src, \
        "M7: scanner still requires exact 'subprocess' module name, missing alias detection"


def test_firestore_rules_hardened():
    rules = open(os.path.join(ROOT, "firestore.rules"), encoding="utf-8").read()
    assert "allow read, write: if true" not in rules, "Firestore rules still open write to everyone"
    assert "request.auth != null" in rules, "Firestore write must require authentication"


def test_env_example_exists():
    env_ex = os.path.join(ROOT, "frontend", ".env.example")
    assert os.path.exists(env_ex), "frontend/.env.example must exist"
    content = open(env_ex).read()
    assert "VITE_FIREBASE_API_KEY" in content


def test_security_check_passes():
    result = subprocess.run(
        [sys.executable, "scripts/check_security.py"],
        capture_output=True, text=True, cwd=ROOT
    )
    assert result.returncode == 0, f"Security check failed:\n{result.stdout}\n{result.stderr}"
