"""Generate paper/refs.bib from refs/related_work.csv."""
from __future__ import annotations
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(ROOT, "refs", "related_work.csv")
BIB_PATH = os.path.join(ROOT, "paper", "refs.bib")

def main():
    entries = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row["key"].strip()
            title = row.get("title", "").strip() or "Untitled"
            authors = row.get("authors", "").strip() or "Anonymous"
            venue = row.get("venue", "").strip() or "Preprint"
            year = row.get("year", "").strip() or "2025"
            doi = row.get("doi_or_url", "").strip()

            doi_line = f",\n  url = {{{doi}}}" if doi else ""
            entry = f"""@article{{{key},
  title = {{{title}}},
  author = {{{authors}}},
  journal = {{{venue}}},
  year = {{{year}}}{doi_line}
}}"""
            entries.append(entry)

    with open(BIB_PATH, "w", encoding="utf-8") as f:
        f.write("\n\n".join(entries) + "\n")
    print(f"Generated {len(entries)} BibTeX entries in {BIB_PATH}")

if __name__ == "__main__":
    main()
