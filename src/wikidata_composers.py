"""Wikidata candidates for NY Phil composers: birth and death years.

  python src/wikidata_composers.py [--min-perf 10]

Reads data/derived/nyphil_composer_summary.csv (persons with at least --min-perf
U1 performances), searches Wikidata for each name and keeps candidates that are
humans with a music occupation and a birth date. Writes
data/aliases/composer_wikidata_candidates.csv with an automatic status:

  ok         one plausible candidate (or all plausible candidates share birth/death years),
             born at least 5 years before the composer's first NY Phil season
  ambiguous  several plausible candidates with different years
  conflict   best candidate fails the first-season check
  none       no plausible candidate

The reviewed file data/aliases/composer_wikidata.csv is the one the metrics read;
it starts as a copy of this output and is corrected by hand (status ok_manual,
with a note). This script never overwrites the reviewed file.
Wikidata content is CC0.
"""
from __future__ import annotations

import argparse
import re
import time
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent  # repository root; default paths do not depend on the working directory

API = "https://www.wikidata.org/w/api.php"
UA = {"User-Agent": "ClassicalMusicMetrics/1.1 (https://github.com/BowonKwon/Classical-Music-Metrics)"}
HUMAN = "Q5"
MUSIC_OCC = {
    "Q36834",   # composer
    "Q158852",  # conductor
    "Q486748",  # pianist
    "Q639669",  # musician
    "Q753110",  # songwriter
    "Q1259917", # violinist
    "Q1415090", # film score composer
    "Q855091",  # guitarist
    "Q15981151",# jazz musician
    "Q806349",  # bandleader
    "Q765778",  # organist
    "Q13219637",# cellist
    "Q16145150",# music arranger
    "Q1198887", # music director
    "Q14915627",# musicologist
    "Q2865819", # opera singer
    "Q177220",  # singer
    "Q20198542",# music educator
}
# an occupation also counts if it is a subclass of one of these (e.g. "classical composer")
MUSIC_ROOTS = ["Q36834", "Q639669", "Q158852", "Q177220", "Q486748"]


def search_name(archive: str) -> list[str]:
    """Archive authority string -> search strings, most specific first."""
    s = re.sub(r"\(.*?\)", "", archive)
    # "Bartok [Bartók]" -> "Bartók"; "Crawford [Seeger]" keeps both forms as alternatives
    accented = re.sub(r"(\S+) \[([^\]]+)\]", r"\2", s)
    plain = re.sub(r"\s*\[[^\]]+\]", "", s)
    out = []
    for form in (accented, plain):
        parts = [p.strip() for p in form.split(",") if p.strip()]
        if not parts:
            continue
        surname, rest = parts[0], parts[1:]
        suffix = [p for p in rest if re.fullmatch(r"(I|II|III|Jr\.|Sr\.)", p)]
        given = [p for p in rest if p not in suffix]
        name = " ".join(given + [surname] + suffix).replace('"', "")
        name = re.sub(r"\s+", " ", name).strip()
        if name and name not in out:
            out.append(name)
        if surname not in out and not given:
            out.append(surname)
        # without initials, honorifics and suffixes: "Edward A. MacDowell" -> "Edward MacDowell"
        g2 = [w for p in given for w in p.split() if not re.fullmatch(r"([A-Z]\.)+|Sir|Padre", w)]
        simple = re.sub(r"\s+", " ", " ".join(g2 + [surname]).replace('"', "")).strip()
        if simple and simple not in out:
            out.append(simple)
    return out


def music_closure(session, occs: set[str]) -> set[str]:
    """Occupations among occs that are MUSIC_OCC or subclasses of a MUSIC_ROOTS item."""
    occs = sorted(occs)
    out = set(MUSIC_OCC)
    for i in range(0, len(occs), 200):
        q = "SELECT DISTINCT ?o WHERE { VALUES ?o { %s } VALUES ?r { %s } ?o wdt:P279* ?r }" % (
            " ".join("wd:" + o for o in occs[i:i + 200]), " ".join("wd:" + r for r in MUSIC_ROOTS))
        r = session.post(SPARQL, data={"query": q, "format": "json"}, headers=UA, timeout=120)
        r.raise_for_status()
        out |= {b["o"]["value"].rsplit("/", 1)[1] for b in r.json()["results"]["bindings"]}
        time.sleep(1)
    return out


def human_search(session, text: str) -> list[str]:
    """Full-text search restricted to humans (CirrusSearch), for names the label search misses."""
    res = get(session, action="query", list="search", srsearch=f"{text} haswbstatement:P31=Q5", srlimit=10, srnamespace=0)
    return [h["title"] for h in res.get("query", {}).get("search", [])]


SPARQL = "https://query.wikidata.org/sparql"


def facts(session, qids: list[str]) -> dict[str, dict]:
    """P31/P106/P569/P570 and English label for many items, in SPARQL batches."""
    out: dict[str, dict] = {}
    for i in range(0, len(qids), 150):
        chunk = qids[i:i + 150]
        q = """SELECT ?item ?label ?p31 ?occ ?birth ?bprec ?brank ?death ?dprec ?drank WHERE {
  VALUES ?item { %s }
  OPTIONAL { ?item wdt:P31 ?p31 }
  OPTIONAL { ?item wdt:P106 ?occ }
  OPTIONAL { ?item p:P569 ?bs . ?bs wikibase:rank ?brank . ?bs psv:P569 [ wikibase:timeValue ?birth; wikibase:timePrecision ?bprec ] FILTER(?brank != wikibase:DeprecatedRank) }
  OPTIONAL { ?item p:P570 ?ds . ?ds wikibase:rank ?drank . ?ds psv:P570 [ wikibase:timeValue ?death; wikibase:timePrecision ?dprec ] FILTER(?drank != wikibase:DeprecatedRank) }
  OPTIONAL { ?item rdfs:label ?label FILTER(LANG(?label) = "en") }
}""" % " ".join("wd:" + x for x in chunk)
        for attempt in range(5):
            r = session.post(SPARQL, data={"query": q, "format": "json"}, headers=UA, timeout=120)
            if r.status_code == 200:
                break
            time.sleep(5 * (attempt + 1))
        r.raise_for_status()
        for b in r.json()["results"]["bindings"]:
            qid = b["item"]["value"].rsplit("/", 1)[1]
            d = out.setdefault(qid, {"p31": set(), "occ": set(), "birth": set(), "death": set(), "label": ""})
            if "p31" in b:
                d["p31"].add(b["p31"]["value"].rsplit("/", 1)[1])
            if "occ" in b:
                d["occ"].add(b["occ"]["value"].rsplit("/", 1)[1])
            for k in ("birth", "death"):
                if k in b and int(b[k[0] + "prec"]["value"]) >= 9:
                    v = b[k]["value"]
                    y = int(v[:5]) if v[0] in "+-" else int(v[:4])
                    pref = b[k[0] + "rank"]["value"].endswith("PreferredRank")
                    d[k].add((y, pref))
            if "label" in b:
                d["label"] = b["label"]["value"]
        time.sleep(1)
    # best rank only: preferred values if any, else all normal-rank values
    for d in out.values():
        for k in ("birth", "death"):
            pref = {y for y, p in d[k] if p}
            d[k] = pref or {y for y, _ in d[k]}
    return out


def get(session, **params):
    params.update(format="json")
    for attempt in range(4):
        r = session.get(API, params=params, headers=UA, timeout=30)
        if r.status_code == 200:
            return r.json()
        time.sleep(2 ** attempt)
    r.raise_for_status()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-perf", type=int, default=10)
    ap.add_argument("--summary", default=str(ROOT / "data/derived/nyphil_composer_summary.csv"))
    ap.add_argument("--out", default=str(ROOT / "data/aliases/composer_wikidata_candidates.csv"))
    a = ap.parse_args()
    comp = pd.read_csv(a.summary)
    comp = comp[(comp["flag"] == "person") & (comp["perf_u1"] >= a.min_perf)]
    s = requests.Session()
    found: dict[str, tuple[list[str], list[str]]] = {}
    for n, (_, c) in enumerate(comp.iterrows(), 1):
        qids, searched = [], []
        for q in search_name(c["composer"]):
            searched.append(q)
            res = get(s, action="wbsearchentities", search=q, language="en", type="item", limit=7)
            for hit in res.get("search", []):
                if hit["id"] not in qids:
                    qids.append(hit["id"])
            time.sleep(0.1)
        found[c["composer"]] = (qids, searched)
        if n % 50 == 0:
            print("searched", n, flush=True)
    allq = sorted({q for qs, _ in found.values() for q in qs})
    print("candidate items", len(allq), flush=True)
    F = facts(s, allq)
    MUS = music_closure(s, {o for d in F.values() for o in d["occ"]})

    def plausible(q):
        d = F.get(q)
        return bool(d) and HUMAN in d["p31"] and bool(d["occ"] & MUS) and bool(d["birth"])

    via = {}
    for _, c in comp.iterrows():
        qids, searched = found[c["composer"]]
        if any(plausible(q) for q in qids):
            via[c["composer"]] = "label"
            continue
        extra = []
        for text in search_name(c["composer"])[-1:] + search_name(c["composer"])[:1]:
            extra += [q for q in human_search(s, text) if q not in qids and q not in extra]
            time.sleep(0.1)
        found[c["composer"]] = (qids + extra, searched + ["fulltext"])
        via[c["composer"]] = "fulltext"
    newq = sorted({q for qs, _ in found.values() for q in qs} - set(F))
    if newq:
        F.update(facts(s, newq))
        MUS |= music_closure(s, {o for q in newq for o in F.get(q, {}).get("occ", set())})
    print("fulltext fallback for", sum(v == "fulltext" for v in via.values()), flush=True)
    rows = []
    for _, c in comp.iterrows():
        first = int(str(c["first_season"])[:4])
        qids, searched = found[c["composer"]]
        cands = []
        for q in qids:
            d = F.get(q)
            if not plausible(q):
                continue
            cands.append({"qid": q, "label": d["label"], "birth": min(d["birth"]), "death": min(d["death"]) if d["death"] else None,
                          "date_conflict": len(d["birth"]) > 1 or len(d["death"]) > 1})
        row = {"composer": c["composer"], "perf_u1": int(c["perf_u1"]), "first_season": c["first_season"], "via": via[c["composer"]], "search": " | ".join(searched)}
        if not cands:
            row.update(status="none")
        else:
            best = cands[0]
            years = {(x["birth"], x["death"]) for x in cands}
            row.update(wikidata_qid=best["qid"], wikidata_label=best["label"], birth_year=best["birth"], death_year=best["death"],
                       n_candidates=len(cands), multiple_dates_in_item=best["date_conflict"],
                       alternatives="; ".join(f'{x["qid"]} {x["label"]} {x["birth"]}-{x["death"] or ""}' for x in cands[1:4]))
            if best["birth"] > first - 5:
                row["status"] = "conflict"
            elif len(years) > 1:
                row["status"] = "ambiguous"
            else:
                row["status"] = "ok"
        rows.append(row)
    out = pd.DataFrame(rows)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.out, index=False, encoding="utf-8", lineterminator="\n")
    print(out["status"].value_counts())


if __name__ == "__main__":
    main()
