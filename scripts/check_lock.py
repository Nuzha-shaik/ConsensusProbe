#!/usr/bin/env python3
"""Check pre-registration lock integrity."""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(ROOT, 'prereg', 'lock.json')

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    if not os.path.isfile(LOCK):
        print("No lock file yet"); sys.exit(0)
    with open(LOCK) as f:
        lock = json.load(f)
    ok = True
    for rel_path, expected in lock.items():
        full = os.path.join(ROOT, rel_path)
        if not os.path.isfile(full):
            print(f"MISSING: {rel_path}"); ok = False; continue
        actual = sha256_file(full)
        if actual != expected:
            print(f"CHANGED: {rel_path}"); ok = False
        else:
            print(f"OK: {rel_path}")
    if ok:
        print("Lock check passed."); sys.exit(0)
    else:
        print("Lock check FAILED."); sys.exit(1)

if __name__ == '__main__':
    main()
