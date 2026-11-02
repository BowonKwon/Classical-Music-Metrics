"""Composer work-activity metrics from IMSLP work pages (CC BY-SA 4.0), with
NY Phil reception matched by catalogue number. Prototype for 1.2.

  python src/work_activity.py            # data/raw/imslp/*.jsonl -> data/derived/imslp_*.csv

Per work page:
  year_start / year_end   first and last four-digit year in "Year/Date of Composition",
                          kept only inside the composer's life (birth+4 .. death);
                          year_uncertain = the field says ca., ?, or before / after
  age_start               year_start - birth year (Wikidata, reviewed table)
  genre                   one of six groups from IMSLP tags (see GENRE_RULES)
  duration_min            "Average Duration" parsed to minutes
  orch_parts              wind + brass + percussion + harp/keyboard parts parsed from
                          InstrDetail (strings counted as none); only where InstrDetail exists
  catalogue               normalised catalogue key used to match NY Phil titles

Outputs (data/derived/):
  imslp_works.csv                 one row per work page
  imslp_composer_year.csv         composer x year x genre, works spread evenly over year ranges
  imslp_composer_age.csv          composer x 5-year age bin: share of dated works
  imslp_reception_period.csv      composer x 5-year composition bin: share of dated works
                                  vs share of NY Phil work performances (U1) of matched works
  imslp_symphony_orchestration.csv  symphonies with parsed parts
"""
from __future__ import annotations

import glob
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent  # repository root; default paths do not depend on the working directory

GENRES = ["orchestral", "stage", "vocal", "chamber", "keyboard", "other"]
GENRE_KO = {"orchestral": "관현악", "stage": "극음악", "vocal": "성악", "chamber": "실내악", "keyboard": "건반", "other": "기타"}
VOICE = re.compile(r"(^|\s)(v|vv|sop|mez|alt|ten|bar|bass|ch|mch|mch2|wch|cch|chorus|voice)(\s|$)")
STAGE = re.compile(r"\b(operas?|singspiele?|ballets?|incidental music|melodramas?|stage works?|operettas?|zarzuelas?|intermezzos? \(stage\))\b")
VOCAL_GENRE = re.compile(r"\b(lieder|songs?|arias?|cantatas?|masses|mass|requiems?|oratorios?|motets?|chorales|choruses|hymns?|psalms?|magnificats?|sacred|canons? for voices|partsongs?)\b")
ORCH = re.compile(r"\b(symphonies|concertos?|overtures?|serenades for orch|orch)\b")
CHAMBER = re.compile(r"\b(trios?|quartets?|quintets?|sextets?|septets?|octets?|nonets?|duets?|duos?|divertimentos?)\b|(^|\s)(vn|va|vc|db|fl|ob|cl|bn|hn|tpt|gui|lute|vdg|rec)\s")
KEYBOARD = re.compile(r"(^|\s)(pf|pf4h|2pf|kbd|org|hpd|clavichord|chorale preludes?|inventions?)(\s|$|,)")


def classify(tags: str, instr: str) -> str:
    t = (tags or "").lower()
    i = (instr or "").lower()
    if STAGE.search(t) or STAGE.search(i):
        return "stage"
    if "chorale prelude" in t:
        return "keyboard"
    tt = " " + t.replace(";", " ").replace(",", " ") + " "
    if VOCAL_GENRE.search(t) or VOICE.search(tt) or re.search(r"\s\d*vv\s", tt) or re.search(r"\b(voices?|choir|chorus|soprano|tenor)\b", i):
        return "vocal"
    if ORCH.search(t) or "orchestra" in i:
        return "orchestral"
    # a solo keyboard instrumentation wins over "duets/trios" in the tags (voices, not players: BWV 802-805)
    if re.fullmatch(r"\s*(keyboard|organ|harpsichord|piano|clavichord)(\s*\([^)]*\))?\s*", i):
        return "keyboard"
    if KEYBOARD.search(tt) and not CHAMBER.search(tt.replace(" pf ", " ")):
        return "keyboard"
    if CHAMBER.search(tt) or re.search(r"\b(violin|cello|flute|string)\b", i):
        return "chamber"
    if re.search(r"\b(piano|organ|harpsichord|keyboard)\b", i):
        return "keyboard"
    return "other"


def years(s: str | None):
    if not isinstance(s, str) or not s.strip():
        return None, None, False
    s2 = re.sub(r"\{\{[^}]*\}\}", " ", s)
    # full dates (1815-20-09, 1808-12-22): keep the year only, so the day is not read as an end year
    s2 = re.sub(r"(?<!\d)(1[5-9]\d\d|20[0-2]\d)-(\d{1,2})-(\d{1,2})(?!\d)", r"\1", s2)
    # several dated versions ("1816 (1st version)<br>1823 (4th version)"): the first entry dates the composition
    if re.search(r"version", s2, re.I):
        s2 = re.split(r"<br\s*/?>|\n|;", s2, maxsplit=1)[0]
    # revisions and later versions are not part of the composition span
    s2 = re.split(r"\b(revised|rev\.|revision|2nd version|second version|arr\.|arranged)\b", s2, maxsplit=1, flags=re.I)[0]
    ys = [int(y) for y in re.findall(r"(?<!\d)(1[5-9]\d\d|20[0-2]\d)(?!\d)", s2)]
    if not ys:
        return None, None, False
    start = ys[0]
    end = start
    if re.search(r"(?<!\d)(1[5-9]\d\d)\s+or\s+(1[5-9]\d\d)", s2):  # alternatives ("1818 or 1824"): not a span
        return start, start, "circa"
    m = re.search(r"(?<!\d)(1[5-9]\d\d)\s*[-–—/]\s*(\d{2,4})(?!\d)", s2)
    if m and int(m.group(1)) == start:
        e = m.group(2)
        e = int(str(start)[: 4 - len(e)] + e)
        if e >= start:
            end = e
    elif len(ys) > 1 and ys[1] >= start and ys[1] - start <= 30:
        end = ys[1]
    if re.search(r"\b(or\s+)?(before|after|earlier|later)\b|terminus|\bpost\b|\bante\b|^\s*by\b", s2, re.I):
        kind = "terminus"  # only a bound is known: not a composition year
    elif re.search(r"ca\.|\?|circa|c\.\s*\d", s2, re.I):
        kind = "circa"
    else:
        kind = "range" if end > start else "exact"
    return start, end, kind


def duration(s: str | None):
    if not isinstance(s, str):
        return np.nan
    h = re.search(r"(\d+(?:\.\d+)?)\s*hours?", s)
    m = re.search(r"(\d+(?:\.\d+)?)\s*min", s)
    sec = re.search(r"(\d+)\s*sec", s)
    if not (h or m or sec):
        return np.nan
    return (float(h.group(1)) * 60 if h else 0) + (float(m.group(1)) if m else 0) + (int(sec.group(1)) / 60 if sec else 0)


WORDNUM = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "eight": 8}
INSTR = r"(piccolos?|flutes?|alto flutes?|oboes?|english horns?|cor anglais|clarinets?|bass clarinets?|basset horns?|bassoons?|contrabassoons?|horns?|trumpets?|cornets?|trombones?|bass trombones?|tubas?|ophicleides?|timpani|percussion|bass drum|snare drum|side drum|cymbals?|triangles?|tam tams?|glockenspiel|xylophone|celesta|harps?|organ|piano|harpsichord|tambourine|castanets|bells?|tubular bells|whip|rute|cowbells?|harmonium|mandolin|guitar)"


def orch_parts(s: str | None):
    if not isinstance(s, str) or not s.strip():
        return np.nan
    t = re.sub(r"\{\{[^}]*\}\}|<[^>]+>|\[\[|\]\]", " ", s).lower()
    t = re.sub(r"[()\[\]]", " , ", t)  # keep parenthesised instruments (e.g. "continuo (harpsichord)")
    t = re.sub(r"[\s\-]+", " ", t)
    total = 0
    perc_items = 0
    has_perc_word = False
    for m in re.finditer(r"(?:(\d+)|\b(a|an|one|two|three|four|five|six|eight)\b)?\s*" + INSTR, t):
        n = m.group(1) or m.group(2)
        k = int(n) if n and n.isdigit() else WORDNUM.get(n, 1) if n else 1
        name = m.group(3)
        if name == "percussion":
            has_perc_word = True
            continue
        if re.match(r"(bass drum|snare drum|side drum|cymbals?|triangles?|tam tams?|glockenspiel|xylophone|tambourine|castanets|bells?|tubular bells|whip|rute|cowbells?)$", name):
            perc_items += min(k, 12)
            continue
        total += min(k, 12)
    # "percussion" as a group word counts once only when no individual percussion instrument is listed
    total += perc_items if perc_items else (1 if has_perc_word else 0)
    return total if total > 0 else np.nan


CAT = {
    "Bach, Johann Sebastian": [r"BWV\s*(\d+[a-z]?)"],
    "Haydn, Franz Joseph": [r"(?:Hob\.?|H\.|HaydnHob\|n\d+\|)\s*([IVXL]+[a-z]?:\s*[A-Za-z]?\d+[a-z]?)"],
    "Mozart, Wolfgang Amadeus": [r"\bK\.?\s*(\d+[a-z]?)"],
    "Beethoven, Ludwig van": [r"Op\.?\s*(\d+[a-z]?)(?:\s*,?\s*No\.?\s*(\d+))?", r"WoO\s*(\d+)"],
    "Schubert, Franz": [r"\bD\.?\s*(\d+[a-z]?)"],
    "Brahms, Johannes": [r"Op\.?\s*(\d+)(?:\s*,?\s*No\.?\s*(\d+))?"],
    "Tchaikovsky, Pyotr Ilyich": [r"Op\.?\s*(\d+[a-z]?)"],
    "Dvorak, Antonín": [r"Op\.?\s*(\d+)", r"\bB\.?\s*(\d+)"],
    "Mahler, Gustav": [],
    "Stravinsky, Igor": [],
}


def cat_keys(composer: str, text: str) -> list[str]:
    keys = []
    for k, pat in enumerate(CAT.get(composer, [])):
        for m in re.finditer(pat, text if isinstance(text, str) else "", re.I):
            g = [x for x in m.groups() if x]
            keys.append(f"{k}:" + ".".join(x.upper().replace(" ", "") for x in g))  # keep "No." (Op.18 No.3 is not Op.18 No.1)
    return keys


def title_key(text: str) -> str | None:
    m = re.search(r"symphon\w*\s*no\.?\s*(\d+)", text if isinstance(text, str) else "", re.I)
    return f"sym{m.group(1)}" if m else None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    raw = pd.concat([pd.read_json(f, lines=True) for f in sorted(glob.glob(str(ROOT / "data/raw/imslp/*.jsonl")))], ignore_index=True)
    raw = raw.astype(object).where(raw.notna(), None)  # missing fields -> None, not NaN
    raw = raw[~raw["composer"].astype(str).str.startswith("category:")]  # whole-category fetches are for imslp_history.py
    wd = pd.read_csv(ROOT / "data/aliases/composer_wikidata.csv")
    life = wd.set_index("composer")[["birth_year", "death_year"]]
    rows = []
    n_redirect = 0
    n_other_composer = 0
    for r in raw.to_dict("records"):
        comp = r["composer"]
        if not any(r.get(k) for k in ("Work Title", "Tags", "Instrumentation", "Year/Date of Composition")):
            n_redirect += 1  # redirect pages (e.g. works re-attributed to other composers) carry no work fields
            continue
        if not r["page"].endswith("(" + r["imslp_category"] + ")"):
            n_other_composer += 1  # page filed under this composer but titled for another (arrangers, pasticcio)
            continue
        b, d = life.loc[comp, "birth_year"], life.loc[comp, "death_year"]
        ys, ye, kind = years(r.get("Year/Date of Composition"))
        if ys is not None and not (b + 4 <= ys <= d):
            ys = ye = None
        if ye is not None and ye > d:
            ye = int(d)
        tags = r.get("Tags") or ""
        g = classify(tags, r.get("Instrumentation"))
        rows.append({
            "composer": comp, "page": r["page"], "revid": r["revid"], "work_title": r.get("Work Title"),
            "catalogue": r.get("Opus/Catalogue Number") or "", "movements": r.get("Movements/Sections"),
            "year_raw": r.get("Year/Date of Composition"), "year_start": ys, "year_end": ye, "year_kind": kind if ys is not None else None,
            "age_start": (ys - b) if ys is not None else None, "genre": g, "genre_ko": GENRE_KO[g],
            "is_symphony": "symphonies" in tags.lower(), "tags": tags,
            "instrumentation": r.get("Instrumentation"), "instr_detail": r.get("InstrDetail"),
            "duration_min": duration(r.get("Average Duration")),
            # parts for every orchestral work and every symphony (choral symphonies are classed vocal but belong on the scatter)
            "orch_parts": orch_parts(r.get("InstrDetail")) if (g == "orchestral" or "symphonies" in tags.lower()) else np.nan,
        })
    W = pd.DataFrame(rows)
    out = (ROOT / "data/derived")
    W.to_csv(out / "imslp_works.csv", index=False, encoding="utf-8", lineterminator="\n")

    # composer x year x genre (spread over ranges)
    D_ = W[W.year_start.notna() & (W.year_kind != "terminus")]
    yy = []
    for r in D_.itertuples():
        span = range(int(r.year_start), int(r.year_end) + 1)
        for y in span:
            yy.append((r.composer, y, r.genre, 1 / len(span)))
    CY = pd.DataFrame(yy, columns=["composer", "year", "genre", "works"]).groupby(["composer", "year", "genre"])["works"].sum().reset_index()
    CY.to_csv(out / "imslp_composer_year.csv", index=False, encoding="utf-8", lineterminator="\n")

    # age curve: share of dated works by 5-year age bin
    A = D_.dropna(subset=["age_start"]).copy()
    A["age_bin"] = (A["age_start"] // 5 * 5).astype(int)
    AC = A.groupby(["composer", "age_bin"]).size().rename("works").reset_index()
    AC["share"] = AC["works"] / AC.groupby("composer")["works"].transform("sum")
    AC.to_csv(out / "imslp_composer_age.csv", index=False, encoding="utf-8", lineterminator="\n")

    # reception: match NY Phil works (U1) by catalogue key / symphony number
    ny = pd.read_csv(out / "nyphil_work_frequency_top50_composers.csv")
    nyall = json.load(open(ROOT / "data/raw/PerformanceHistory/Programs/json/complete.json", encoding="utf-8"))
    # full work list per composer from the pairs table is not saved; rebuild U1 per work id quickly
    from repertoire_metrics import load_entries, apply_aliases, to_pairs  # noqa: E402
    pairs = to_pairs(apply_aliases(load_entries((ROOT / "data/raw")), (ROOT / "data/aliases/nyphil_composers.csv")))
    wf = pairs.groupby(["composer", "work_id"]).agg(title=("work_title", "first"), u1=("u1", "sum")).reset_index()
    wf = wf[wf["composer"].isin(CAT)]
    index = {}
    collisions = 0
    # deterministic: pages in name order; the first page per key wins, collisions are counted
    for r in W.sort_values("page").itertuples():
        for k in cat_keys(r.composer, r.catalogue) + ([title_key(r.work_title)] if r.composer in ("Haydn, Franz Joseph", "Mozart, Wolfgang Amadeus", "Mahler, Gustav", "Beethoven, Ludwig van", "Brahms, Johannes", "Tchaikovsky, Pyotr Ilyich", "Dvorak, Antonín", "Schubert, Franz", "Stravinsky, Igor") and title_key(r.work_title) else []):
            if (r.composer, k) in index:
                collisions += 1
            index.setdefault((r.composer, k), r.Index)
    match = []
    for r in wf.itertuples():
        keys = cat_keys(r.composer, r.title) + ([title_key(r.title)] if title_key(r.title) else [])
        # exact key (with No.) first; fall back to the opus-level key only for a collection page (e.g. "6 String Quartets, Op.18")
        base = [k.split(".")[0] for k in keys if "." in k]
        hit = next((index[(r.composer, k)] for k in keys if (r.composer, k) in index), None)
        if hit is None:
            hit = next((index[(r.composer, k)] for k in base if (r.composer, k) in index), None)
        match.append(hit)
    wf["imslp_row"] = match
    wf["year_start"] = wf["imslp_row"].map(lambda i: W.loc[int(i), "year_start"] if pd.notna(i) and W.loc[int(i), "year_kind"] != "terminus" else np.nan)
    rate = wf.assign(m=wf["imslp_row"].notna()).groupby("composer").apply(lambda g: pd.Series({"u1": g.u1.sum(), "matched_u1_share": g.loc[g.m, "u1"].sum() / g.u1.sum(), "dated_u1_share": g.loc[g.year_start.notna(), "u1"].sum() / g.u1.sum()}))
    rate.to_csv(out / "imslp_nyphil_match_rate.csv", encoding="utf-8", lineterminator="\n")
    wf.to_csv(out / "imslp_nyphil_matches.csv", index=False, encoding="utf-8", lineterminator="\n")
    rec = []
    for c in CAT:
        w_ = D_[D_.composer == c]
        p_ = wf[(wf.composer == c) & wf.year_start.notna()]
        if not len(w_):
            continue
        lo = int(w_.year_start.min() // 5 * 5)
        for b0 in range(lo, int(w_.year_start.max()) + 1, 5):
            rec.append({"composer": c, "bin_start": b0,
                        "works_share": ((w_.year_start >= b0) & (w_.year_start < b0 + 5)).mean(),
                        "nyphil_share": p_.loc[(p_.year_start >= b0) & (p_.year_start < b0 + 5), "u1"].sum() / p_.u1.sum() if p_.u1.sum() else np.nan})
    pd.DataFrame(rec).to_csv(out / "imslp_reception_period.csv", index=False, encoding="utf-8", lineterminator="\n")

    S = W[W.is_symphony & W.orch_parts.notna() & W.year_start.notna()][["composer", "page", "work_title", "year_start", "orch_parts", "duration_min"]]
    S.to_csv(out / "imslp_symphony_orchestration.csv", index=False, encoding="utf-8", lineterminator="\n")

    print("works", len(W), "dated", int(W.year_start.notna().sum()), "of which terminus-only", int((W.year_kind == "terminus").sum()), "redirect/empty pages dropped", n_redirect, "other-composer pages dropped", n_other_composer, "catalogue key collisions", collisions)
    print(W.groupby("composer").year_kind.value_counts().unstack(fill_value=0).to_string())
    print(W.groupby("composer").agg(n=("page", "size"), dated=("year_start", lambda s: s.notna().mean())).round(2).to_string())
    print(W.groupby(["composer", "genre_ko"]).size().unstack(fill_value=0).to_string())
    print(rate.round(3).to_string())
    print("symphonies with parts", len(S)); print(S.sort_values("year_start").to_string()[:2500])


if __name__ == "__main__":
    main()
