#!/usr/bin/env python3
"""Security scanner: AST checks + pattern grep."""
import ast, os, re, sys

DANGEROUS_CALLS = {'eval', 'exec'}
DANGEROUS_ATTRS = {'pickle.load', 'pickle.loads', 'os.system'}
SECRET_PATTERNS = [
    re.compile(r'sk-[a-zA-Z0-9]{20,}'),
    re.compile(r'AKIA[A-Z0-9]{16}'),
    re.compile(r'BEGIN' + ' PRIVATE KEY'),
    re.compile(r'BEGIN' + ' RSA PRIVATE KEY'),
    re.compile(r'AIzaSy[a-zA-Z0-9_-]{33}'),
    re.compile(r'\d{6,}-[a-z0-9]+\.apps\.googleusercontent\.com'),
]
SKIP_DIRS = {'node_modules', '.git', '__pycache__', '.logs', '.venv', 'venv', '.pytest_cache', 'dist'}
SKIP_FILES = {'.env.example', '.env', '.env.local', '.env.production'}


def check_ast(filepath):
    violations = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            tree = ast.parse(f.read(), filename=filepath)
    except SyntaxError:
        return violations
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check bare name calls: eval(), exec()
            if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_CALLS:
                violations.append((filepath, node.lineno, f"dangerous call: {node.func.id}()"))
            # Check attribute calls: pickle.load(), os.system()
            if isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name):
                    full = f"{node.func.value.id}.{node.func.attr}"
                    if full in DANGEROUS_ATTRS:
                        violations.append((filepath, node.lineno, f"dangerous call: {full}()"))
            # Check subprocess with shell=True — catches aliased imports too (M7)
            if isinstance(node.func, ast.Attribute) and node.func.attr in ('call', 'run', 'Popen', 'check_call', 'check_output'):
                for kw in node.keywords:
                    if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        violations.append((filepath, node.lineno, "subprocess with shell=True"))
            if isinstance(node.func, ast.Name) and node.func.id in ('call', 'run', 'Popen', 'check_call', 'check_output'):
                for kw in node.keywords:
                    if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                        violations.append((filepath, node.lineno, "subprocess with shell=True"))
    return violations


def check_secrets(filepath):
    violations = []
    if os.path.basename(filepath) in SKIP_FILES:
        return violations
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for i, line in enumerate(f, 1):
                for pat in SECRET_PATTERNS:
                    if pat.search(line):
                        violations.append((filepath, i, f"secret pattern: {pat.pattern}"))
    except (OSError, UnicodeDecodeError):
        pass
    return violations


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    violations = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            fp = os.path.join(dirpath, fn)
            if fn.endswith('.py'):
                violations.extend(check_ast(fp))
            if fn.endswith(('.py', '.js', '.ts', '.tsx', '.env', '.toml', '.yaml', '.yml', '.json', '.txt')):
                violations.extend(check_secrets(fp))
    if violations:
        for fp, line, msg in violations:
            print(f"{fp}:{line}: {msg}")
        sys.exit(1)
    print("Security check passed.")
    sys.exit(0)


if __name__ == '__main__':
    main()
