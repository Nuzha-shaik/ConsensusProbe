#!/usr/bin/env python3
"""Generate cryptographic pre-registration lock: prereg/lock.json."""
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCKED_FILES = [
    "configs/frozen.toml",
    "prereg/PREREG.md",
    "research/track_s.py",
    "research/tests/test_p2.py",
    "research/tests/test_p3_track_s.py",
    "research/tests/test_p4_policies.py",
    "research/tests/test_p5_canary.py",
]

def sha256_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    lock_dict = {}
    for rel_path in LOCKED_FILES:
        full_path = os.path.join(ROOT, rel_path.replace("/", os.sep))
        if not os.path.isfile(full_path):
            print(f"ERROR: Cannot lock missing file {rel_path}")
            sys.exit(1)
        lock_dict[rel_path] = sha256_file(full_path)

    lock_file = os.path.join(ROOT, "prereg", "lock.json")
    with open(lock_file, "w", encoding="utf-8") as f:
        json.dump(lock_dict, f, indent=2, sort_keys=True)

    print(f"Successfully locked {len(lock_dict)} files into prereg/lock.json")

if __name__ == "__main__":
    main()
