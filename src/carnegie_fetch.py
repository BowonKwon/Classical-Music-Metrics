"""Fetch orchestra appearances at Carnegie Hall from the CC0 SPARQL endpoint (data.carnegiehall.org).

Carnegie Hall Performance History is CC0 1.0 (GeoNames parts CC BY 3.0). robots.txt asks for Crawl-delay 10
and disallows per-entity RDF pages, so this script uses only the SPARQL endpoint, one request at a time,
sleeping SLEEP seconds between requests. Raw result pages are stored unmodified under data/raw/carnegiehall/.

Three passes, all paged with LIMIT/OFFSET over a stable ORDER BY:
  events  one row per (event, orchestra): date, event label, description, orchestra name
  works   one row per (event, work performance): work, work label, composer, composer label
  composers  composer -> Wikidata QID (skos:exactMatch), for joining to NY Phil names by QID

Usage: python src/carnegie_fetch.py [--pass events|works|both] [--page 5000]
Resumable: existing page files are skipped.
"""
import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "carnegiehall"
ENDPOINT = "https://data.carnegiehall.org/sparql/"
SLEEP = 11
UA = "Mozilla/5.0 (research script; classical-metrics)"

PFX = """PREFIX chr: <http://data.carnegiehall.org/vocabulary/roles/>
PREFIX schema: <http://schema.org/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dct: <http://purl.org/dc/terms/>
"""

Q_EVENTS = PFX + """SELECT ?ev ?date ?evLabel ?desc ?org ?orgLabel WHERE {
  ?ev chr:orchestra ?org .
  OPTIONAL { ?ev schema:startDate ?date }
  OPTIONAL { ?ev rdfs:label ?evLabel }
  OPTIONAL { ?ev schema:description ?desc }
  OPTIONAL { ?org rdfs:label ?orgLabel }
} ORDER BY ?ev ?org LIMIT %d OFFSET %d"""

Q_WORKS = PFX + """SELECT ?ev ?sub ?work ?workLabel ?comp ?compLabel WHERE {
  { SELECT DISTINCT ?ev WHERE { ?ev chr:orchestra ?o } }
  ?ev schema:subEvent ?sub .
  ?sub schema:workPerformed ?work .
  OPTIONAL { ?work rdfs:label ?workLabel }
  OPTIONAL { ?work dct:creator ?comp . OPTIONAL { ?comp rdfs:label ?compLabel } }
} ORDER BY ?ev ?sub ?comp LIMIT %d OFFSET %d"""

Q_COMPOSERS = PFX + """PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT ?comp ?wd WHERE {
  { SELECT DISTINCT ?comp WHERE { ?e chr:orchestra ?o . ?e schema:subEvent ?s . ?s schema:workPerformed ?w . ?w dct:creator ?comp } }
  ?comp skos:exactMatch ?wd . FILTER(STRSTARTS(STR(?wd), "http://www.wikidata.org/entity/"))
} ORDER BY ?comp ?wd LIMIT %d OFFSET %d"""


def run(query: str) -> dict:
    body = urllib.parse.urlencode({"query": query}).encode()
    req = urllib.request.Request(ENDPOINT, body, {"User-Agent": UA, "Accept": "application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        raw = r.read()
    if raw.lstrip()[:1] != b"{":
        raise RuntimeError("non-JSON response (possibly blocked): " + raw[:200].decode("utf-8", "replace"))
    return json.loads(raw)


def fetch(name: str, template: str, page: int) -> int:
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    total, i = 0, 0
    while True:
        f = d / f"page-{i:04d}.json"
        if f.exists():
            n = len(json.loads(f.read_text(encoding="utf-8"))["results"]["bindings"])
        else:
            res = run(template % (page, i * page))
            f.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
            n = len(res["results"]["bindings"])
            print(f"{name} page {i}: {n} rows", flush=True)
            time.sleep(SLEEP)
        total += n
        if n < page:
            return total
        i += 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pass", dest="which", default="both", choices=["events", "works", "composers", "both"])
    ap.add_argument("--page", type=int, default=5000)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"source": ENDPOINT, "license": "CC0 1.0 (Carnegie Hall Performance History)", "fetched": time.strftime("%Y-%m-%d"),
                "page": a.page, "queries": {"events": Q_EVENTS, "works": Q_WORKS, "composers": Q_COMPOSERS}, "rows": {}}
    if a.which in ("events", "both"):
        manifest["rows"]["events"] = fetch("events", Q_EVENTS, a.page)
    if a.which in ("works", "both"):
        manifest["rows"]["works"] = fetch("works", Q_WORKS, a.page)
    if a.which == "composers":
        manifest["rows"]["composers"] = fetch("composers", Q_COMPOSERS, a.page)
        old = OUT / "_manifest.json"
        if old.exists():
            prev = json.loads(old.read_text(encoding="utf-8"))
            prev["rows"].update(manifest["rows"]); prev["queries"]["composers"] = Q_COMPOSERS; manifest = prev
    (OUT / "_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(manifest["rows"])


if __name__ == "__main__":
    main()
