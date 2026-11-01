"""Work lists from IMSLP (imslp.org, wiki content CC BY-SA 4.0) for composer
work-activity metrics.

  python src/imslp_works.py fetch [--composers ...]   # API -> data/raw/imslp/*.jsonl (raw wikitext fields)
  python src/imslp_works.py parse                     # -> data/derived/imslp_works.csv

Fetch uses the MediaWiki API (api.php is not disallowed by robots.txt) with a
2-second delay between requests (robots.txt Crawl-delay: 2). The User-Agent
names this project; no personal data is sent.

Parsed fields per work page: title, catalogue number, key, year/date of
composition (start/end year), average duration (minutes), piece style, IMSLP
tags (genre), instrumentation and InstrDetail (orchestral parts).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

API = "https://imslp.org/api.php"
UA = {"User-Agent": "ClassicalMusicMetrics/1.2 (https://github.com/BowonKwon/Classical-Music-Metrics)"}
DELAY = 2.0
COMPOSERS = {
    # NY Phil archive name -> IMSLP category
    "Bach, Johann Sebastian": "Bach, Johann Sebastian",
    "Haydn, Franz Joseph": "Haydn, Joseph",
    "Mozart, Wolfgang Amadeus": "Mozart, Wolfgang Amadeus",
    "Beethoven, Ludwig van": "Beethoven, Ludwig van",
    "Schubert, Franz": "Schubert, Franz",
    "Brahms, Johannes": "Brahms, Johannes",
    "Tchaikovsky, Pyotr Ilyich": "Tchaikovsky, Pyotr",
    "Dvorak, Antonín": "Dvořák, Antonín",
    "Mahler, Gustav": "Mahler, Gustav",
    "Stravinsky, Igor": "Stravinsky, Igor",
}
FIELDS = ["Work Title", "Alternative Title", "Opus/Catalogue Number", "I-Catalogue Number", "Key", "Movements Header",
          "Number of Movements/Sections", "Year/Date of Composition", "First Performance", "Year of First Publication",
          "Average Duration", "Piece Style", "Language", "Instrumentation", "InstrDetail", "Tags"]


def workinfo(text: str) -> str:
    """The WORK INFO block verbatim (kept so that later fields need no refetch)."""
    i = text.find("WORK INFO")
    if i < 0:
        return ""
    j = text.find("*****COMMENTS*****", i)
    return text[i:j if j > 0 else i + 6000]


def api(session, **params):
    params["format"] = "json"
    for attempt in range(5):
        r = session.get(API, params=params, headers=UA, timeout=60)
        if r.status_code == 200:
            time.sleep(DELAY)
            return r.json()
        time.sleep(DELAY * (attempt + 2))
    r.raise_for_status()


def category_members(session, cat: str) -> list[str]:
    out, cont = [], {}
    while True:
        d = api(session, action="query", list="categorymembers", cmtitle=f"Category:{cat}", cmlimit=500, cmnamespace=0, **cont)
        out += [m["title"] for m in d["query"]["categorymembers"]]
        # MediaWiki 1.18 (IMSLP) signals more pages with "query-continue"; newer versions use "continue"
        nxt = d.get("continue", {}).get("cmcontinue") or d.get("query-continue", {}).get("categorymembers", {}).get("cmcontinue")
        if not nxt:
            return out
        cont = {"cmcontinue": nxt}


def field(text: str, name: str) -> str | None:
    m = re.search(r"\|\s*" + re.escape(name) + r"\s*=(.*?)(?=\n\s*\||\n\s*\}\}|\Z)", text, re.S)
    return m.group(1).strip() if m else None


def fetch(composers: list[str], out_dir: Path, categories: dict | None = None) -> None:
    s = requests.Session()
    out_dir.mkdir(parents=True, exist_ok=True)
    targets = categories or {name: COMPOSERS[name] for name in composers}
    for name, cat in targets.items():
        titles = category_members(s, cat)
        rows = []
        for i in range(0, len(titles), 50):
            d = api(s, action="query", prop="revisions", rvprop="content|ids", titles="|".join(titles[i:i + 50]))
            for p in d["query"]["pages"].values():
                if "revisions" not in p:
                    continue
                t = p["revisions"][0]["*"]
                rows.append({"composer": name, "imslp_category": cat, "page": p["title"], "revid": p["revisions"][0]["revid"],
                             **{k: field(t, k) for k in FIELDS}, "workinfo": workinfo(t), "redirect": t.lstrip().upper().startswith("#REDIRECT")})
        path = out_dir / (re.sub(r"[^a-z]+", "_", name.lower()).strip("_") + ".jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(name, "category members", len(titles), "pages", len(rows), flush=True)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["fetch", "parse"])
    ap.add_argument("--composers", nargs="*", default=list(COMPOSERS))
    ap.add_argument("--raw", default="data/raw/imslp")
    ap.add_argument("--category", help="fetch a whole IMSLP category instead of composer categories, e.g. Symphonies")
    a = ap.parse_args()
    if a.cmd == "fetch":
        if a.category:
            fetch([], Path(a.raw), {f"category:{a.category}": a.category})
        else:
            fetch(a.composers, Path(a.raw))


if __name__ == "__main__":
    main()
