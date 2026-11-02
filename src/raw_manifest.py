"""Record the commit of every raw input that is a git clone.

  python src/raw_manifest.py [--raw data/raw] [--out data/derived/raw_manifest.json]

Only folders under data/raw/ that are themselves git clones (their own .git) are recorded:
a folder without one (data/raw/imslp/, fetched from the IMSLP API) has no commit, and asking
git there would return the commit of the enclosing repository instead. Run it after the
metric scripts, from the same clones they read; the public data/ folder carries the file.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # repository root; default paths do not depend on the working directory


def manifest(raw: Path) -> dict:
    man = {}
    for d in sorted(raw.iterdir(), key=lambda p: p.name):
        if not (d / ".git").exists():
            continue
        man[d.name] = subprocess.check_output(["git", "-C", str(d), "rev-parse", "HEAD"], text=True).strip()
    return man


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data/raw"))
    ap.add_argument("--out", default=str(ROOT / "data/derived/raw_manifest.json"))
    a = ap.parse_args()
    man = manifest(Path(a.raw))
    Path(a.out).write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(len(man), "clones recorded ->", a.out)


if __name__ == "__main__":
    main()
