"""Wikidata sex or gender (P21) for the reviewed NY Phil composers (1.4).

  python src/wikidata_gender.py [--aliases data/aliases]

Reads data/aliases/composer_wikidata.csv (rows with status ok or ok_manual and a QID), asks the
Wikidata API for the P21 statements of those items (50 per request, one second between requests)
and writes data/aliases/composer_gender.csv:

  composer, wikidata_qid, p21_qids, gender

gender is the label of the preferred-rank P21 value (normal rank if none is preferred; deprecated
values are ignored): female, male, trans woman, trans man, intersex, non-binary, or 'other:<QID>'
for any other value; 'unknown' when the item has no P21 statement. Composers that are not in the
reviewed table (most of those with fewer than 10 performances) are not written and count as unknown
in repertoire_metrics.py, which reports the women composers' share as a lower bound (unknown = not
women), a point value among composers with a P21 value, and an upper bound (unknown = women).

The request carries no personal information: a project User-Agent and the item IDs only.
Wikidata content is CC0.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent  # repository root; default paths do not depend on the working directory

API = "https://www.wikidata.org/w/api.php"
UA = {"User-Agent": "ClassicalMusicMetrics/1.4 (https://github.com/BowonKwon/Classical-Music-Metrics)"}
P21_LABEL = {
    "Q6581072": "female",
    "Q6581097": "male",
    "Q1052281": "trans woman",
    "Q2449503": "trans man",
    "Q1097630": "intersex",
    "Q48270": "non-binary",
}


def p21_values(entity: dict) -> list[str]:
    """QIDs of the P21 values to use: preferred rank if any, else normal rank; deprecated never."""
    claims = [c for c in entity.get("claims", {}).get("P21", []) if c.get("rank") != "deprecated"]
    pref = [c for c in claims if c.get("rank") == "preferred"]
    out = []
    for c in pref or claims:
        dv = c.get("mainsnak", {}).get("datavalue", {}).get("value")
        if isinstance(dv, dict) and dv.get("id"):
            out.append(dv["id"])
    return out


def gender_label(qids: list[str]) -> str:
    if not qids:
        return "unknown"
    labels = sorted({P21_LABEL.get(q, f"other:{q}") for q in qids})
    # 1.4 owner decision (2026-11-04): several different P21 values -> unknown (counted in neither group; it widens the bounds)
    return labels[0] if len(labels) == 1 else "unknown"


def fetch(qids: list[str], session=None, pause: float = 1.0) -> dict[str, list[str]]:
    import requests
    session = session or requests.Session()
    out = {}
    for i in range(0, len(qids), 50):
        batch = qids[i:i + 50]
        params = {"action": "wbgetentities", "ids": "|".join(batch), "props": "claims", "format": "json"}
        r = session.get(API, params=params, headers=UA, timeout=60)
        r.raise_for_status()
        for q, ent in r.json().get("entities", {}).items():
            out[q] = p21_values(ent)
        time.sleep(pause)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aliases", default=str(ROOT / "data/aliases"))
    a = ap.parse_args()
    al = Path(a.aliases)
    wd = pd.read_csv(al / "composer_wikidata.csv", dtype=str)
    wd = wd[wd["status"].isin(["ok", "ok_manual"]) & wd["wikidata_qid"].notna()]
    got = fetch(sorted(set(wd["wikidata_qid"])))
    rows = [{"composer": r.composer, "wikidata_qid": r.wikidata_qid, "p21_qids": " ".join(got.get(r.wikidata_qid, [])),
             "gender": gender_label(got.get(r.wikidata_qid, []))} for r in wd.itertuples()]
    pd.DataFrame(rows).to_csv(al / "composer_gender.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(pd.DataFrame(rows)["gender"].value_counts().to_string())


if __name__ == "__main__":
    main()
