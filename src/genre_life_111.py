"""1.11: composers' work across their lives by genre (design 67), for 30 composers.

Big groups keep the 1.2 classifier (work_activity.classify) so the six groups match the 'Works & history' page,
with vocal split into sacred and secular. Sub-genres come from the IMSLP tags and instrumentation by the
rules in SUB below, fixed before computing (design 67 §5). Counting unit: work pages; durations where IMSLP
gives an average duration (about a third of pages) as a secondary view.

The first ten composers are read from data/raw/imslp (1.2), the twenty added in 1.11 from data/raw/imslp_111;
nothing in the 1.2 tables changes.

Outputs (data/derived):
  genre_life_works.csv      one row per work page: composer, years, age, group, subgenre, duration, date_basis
                            (composition | publication = first publication within the composer's life, used only
                            where no composition year is known; owner decision 2026-11-10 | none)
  genre_life_age.csv        composer x 5-year age bin x subgenre: work pages and minutes
  genre_life_era.csv        25-year period x subgenre: mean over composers of each composer's share (one vote per
                            composer), with the pooled share for comparison
"""
from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import work_activity as wa  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# IMSLP category -> name in the reviewed Wikidata table (data/aliases/composer_wikidata.csv)
WD_NAME = {"Fauré, Gabriel": "Faure [Fauré], Gabriel-Urbain", "Saint-Saëns, Camille": "Saint-Saens [Saint-Saëns], Camille",
           "Rimsky-Korsakov, Nikolay": "Rimsky-Korsakov, Nikolai"}
# not in the NY Phil table (never performed there): Wikidata Q57286, checked 2026-11-10
EXTRA_LIFE = {"Hensel, Fanny": (1805, 1847, "Q57286")}

GROUPS = ["stage", "sacred", "secular", "orchestral", "chamber", "keyboard", "other"]
GROUP_NAME = {"stage": ("무대", "Stage"), "sacred": ("종교 성악", "Sacred vocal"), "secular": ("세속 성악", "Secular vocal"),
              "orchestral": ("관현악", "Orchestral"), "chamber": ("실내악", "Chamber"), "keyboard": ("건반", "Keyboard"),
              "other": ("기타", "Other")}
SACRED = re.compile(r"\b(sacred|masses|mass|requiems?|oratorios?|passions?|motets?|psalms?|hymns?|chorales|magnificats?|anthems?|vespers|te deum|stabat mater|litan\w*|graduals?|offertor\w*|antiphons?|responsor\w*|lamentations?)\b")
# (subgenre id, ko, en, group, pattern on " tags " + " instrumentation ", lower case); first match wins within the group
SUB = [
    ("opera", "오페라", "Opera", "stage", r"\b(operas?|singspiele?|operettas?|zarzuelas?|opera seria|opera buffa|dramma)\b"),
    ("stage_other", "발레·극부수음악 등", "Ballet, incidental music etc.", "stage", r"."),
    ("mass", "미사·레퀴엠", "Masses, requiems", "sacred", r"\b(masses|mass|requiems?)\b"),
    ("oratorio", "오라토리오·수난곡", "Oratorios, passions", "sacred", r"\b(oratorios?|passions?)\b"),
    ("sacred_cantata", "종교 칸타타", "Sacred cantatas", "sacred", r"\b(sacred cantatas?|cantatas?)\b"),
    ("sacred_other", "모테트·시편·코랄 등", "Motets, psalms, chorales etc.", "sacred", r"."),
    ("song", "가곡·리트", "Songs, lieder", "secular", r"\b(lieder|(folk)?songs?|chansons?|m[eé]lodies|romances?)\b"),
    ("secular_cantata", "아리아·세속 칸타타", "Arias, secular cantatas", "secular", r"\b(arias?|cantatas?|serenatas?|scenas?)\b"),
    ("secular_choral", "합창곡·마드리갈 등", "Choral pieces, madrigals etc.", "secular", r"."),
    ("symphony", "교향곡", "Symphonies", "orchestral", r"\bsymphonies\b"),
    ("concerto", "협주곡", "Concertos", "orchestral", r"\b(concertos?|concerti)\b"),
    ("overture_poem", "서곡·교향시", "Overtures, symphonic poems", "orchestral", r"^(?!.*\bsuites?\b).*\b(overtures?|symphonic poems?|tone poems?)\b"),
    ("orch_other", "모음곡·세레나데·춤곡 등", "Suites, serenades, dances etc.", "orchestral", r"."),
    ("string_quartet", "현악 4중주", "String quartets", "chamber", r"(?=.*\bquartets?\b)(?=.*\b2vn va vc\b)|\bstring quartets?\b"),
    ("ensemble", "3~9중주", "Trios to nonets", "chamber", r"\b(trios?|quartets?|quintets?|sextets?|septets?|octets?|nonets?)\b"),
    ("duo", "2중주·독주+반주", "Duos, solo with accompaniment", "chamber", r"\b(sonatas?|duets?|duos?)\b|\b(vn|va|vc|fl|ob|cl|hn|bn|rec|vdg|gui) (pf|bc|kbd|hpd)\b"),
    ("chamber_other", "그 밖의 실내악", "Other chamber", "chamber", r"."),
    ("organ", "오르간", "Organ", "keyboard", None),  # decided from the tags only (see subgenre_of)
    ("kb_sonata", "건반 소나타", "Keyboard sonatas", "keyboard", r"\bsonat(as?|inas?)\b"),
    ("kb_counterpoint", "변주곡·푸가·전주곡 등", "Variations, fugues, preludes etc.", "keyboard", r"\b(variations?|fugues?|preludes?|fantasias?|fantasies|toccatas?|inventions?|canons?|ricercars?)\b"),
    ("kb_pieces", "소품·춤곡", "Pieces, dances", "keyboard", r"."),
    ("other", "기타", "Other", "other", r"."),
]
SUB_INFO = {s[0]: s for s in SUB}


def group_of(tags: str, instr: str) -> str:
    g = wa.classify(tags, instr)
    if g == "vocal":
        return "sacred" if SACRED.search((tags or "").lower()) else "secular"
    return g


PLAYER = re.compile(r"^(\d*)(vn|va|vc|db|fl|ob|cl|bn|hn|tpt|tbn|rec|viol|vdg|gui|lute|pf|hpd|kbd|org|bc|harp|mand|ehn|bcl|cbn|bfl)$")
CHOIR = re.compile(r"(^|\s)(ch|mch|wch|cch|chorus|\d+(sop|mez|alt|ten|bar|bass|vv|v))(\s|$)")


def players(tags: str) -> int:
    """Largest player count among the scoring codes in the tags ('2vn bc' = 3, 'vn vc pf' = 3); 0 if none."""
    best = 0
    for seg in (tags or "").lower().split(";"):
        toks = seg.split()
        if not toks or not all(PLAYER.match(t) for t in toks):
            continue
        best = max(best, sum(int(PLAYER.match(t).group(1) or 1) for t in toks))
    return best


def subgenre_of(group: str, tags: str, instr: str) -> str:
    """Rules revised once after the Codex blind check (design 67 §10): trio sonatas and other works for three or more
    players are ensembles; overture-suites are suites; songs for chorus or several voices are choral; organ only
    when the tags say organ; sonatinas are sonatas."""
    t = (tags or "").lower()
    text = " " + t.replace(";", " ").replace(",", " ") + " " + (instr or "").lower() + " "
    if group == "chamber" and not re.search(r"(?=.*\bquartets?\b)(?=.*\b2vn va vc\b)", text) and players(t) >= 3:
        return "ensemble"
    if group == "secular" and CHOIR.search(" " + t.replace(";", " ") + " "):
        return "secular_choral"
    if group == "keyboard":
        if re.search(r"(^|[\s;])org(\s|;|$)|\borgan\b|chorale preludes?", t):
            return "organ"
    for sid, _ko, _en, g, pat in SUB:
        if g == group and pat is not None and re.search(pat, text):
            return sid
    return "other"


def life_table() -> pd.DataFrame:
    wd = pd.read_csv(ROOT / "data/aliases/composer_wikidata.csv").set_index("composer")[["birth_year", "death_year"]]
    return wd


def load_raw() -> pd.DataFrame:
    files = sorted(glob.glob(str(ROOT / "data/raw/imslp/*.jsonl"))) + sorted(glob.glob(str(ROOT / "data/raw/imslp_111/*.jsonl")))
    raw = pd.concat([pd.read_json(f, lines=True) for f in files], ignore_index=True)
    raw = raw.astype(object).where(raw.notna(), None)
    return raw[~raw["composer"].astype(str).str.startswith("category:")]


def build_works() -> pd.DataFrame:
    raw = load_raw()
    life = life_table()
    rows = []
    for r in raw.to_dict("records"):
        comp = r["composer"]
        if not any(r.get(k) for k in ("Work Title", "Tags", "Instrumentation", "Year/Date of Composition")):
            continue  # redirect / empty pages (same rule as 1.2)
        if not r["page"].endswith("(" + r["imslp_category"] + ")"):
            continue  # page filed under this composer but titled for another (same rule as 1.2)
        if comp in EXTRA_LIFE:
            b, d, _ = EXTRA_LIFE[comp]
        else:
            key = WD_NAME.get(comp, comp)
            b, d = life.loc[key, "birth_year"], life.loc[key, "death_year"]
        ys, ye, kind = wa.years(r.get("Year/Date of Composition"))
        if ys is not None and not (b + 4 <= ys <= d):
            ys = ye = None
        if ye is not None and ye > d:
            ye = int(d)
        basis = "composition" if (ys is not None and kind != "terminus") else None
        if basis is None:  # owner decision 11-10: fall back on a first-publication year within the composer's life
            ps = wa.years(r.get("Year of First Publication"))[0]
            if ps is not None and b + 4 <= ps <= d:
                ys, ye, kind, basis = ps, ps, "publication", "publication"
        tags, instr = r.get("Tags") or "", r.get("Instrumentation") or ""
        g = group_of(tags, instr)
        rows.append(dict(composer=comp, page=r["page"], revid=r["revid"], work_title=r.get("Work Title"), birth=int(b), death=int(d),
                         year_raw=r.get("Year/Date of Composition"), year_start=ys, year_end=ye,
                         year_kind=kind if ys is not None else None, age_start=(ys - b) if ys is not None else None,
                         date_basis=basis or "none",
                         group=g, subgenre=subgenre_of(g, tags, instr), tags=tags, instrumentation=instr,
                         duration_min=wa.duration(r.get("Average Duration"))))
    return pd.DataFrame(rows)


def main(out: Path = ROOT / "data/derived") -> pd.DataFrame:
    W = build_works()
    W.to_csv(out / "genre_life_works.csv", index=False, encoding="utf-8", lineterminator="\n")
    dated = W[W.date_basis != "none"].copy()
    dated["age_bin"] = (dated["age_start"] // 5 * 5).astype(int)
    age = (dated.groupby(["composer", "age_bin", "group", "subgenre", "date_basis"])
           .agg(works=("page", "size"), minutes=("duration_min", "sum"), with_duration=("duration_min", "count")).reset_index())
    age.to_csv(out / "genre_life_age.csv", index=False, encoding="utf-8", lineterminator="\n")
    dated["period"] = (dated["year_start"] // 25 * 25).astype(int)
    per_comp = dated.groupby(["period", "composer", "subgenre"]).size().unstack(fill_value=0)
    shares = per_comp.div(per_comp.sum(axis=1), axis=0)
    n_comp = shares.groupby(level="period").size()
    era = shares.groupby(level="period").mean().stack().rename("share_per_composer").reset_index()
    pooled = dated.groupby(["period", "subgenre"]).size()
    pooled = (pooled / pooled.groupby(level="period").transform("sum")).rename("share_pooled").reset_index()
    era = era.merge(pooled, on=["period", "subgenre"], how="left").fillna({"share_pooled": 0})
    era["n_composers"] = era["period"].map(n_comp)
    era.to_csv(out / "genre_life_era.csv", index=False, encoding="utf-8", lineterminator="\n")
    return W


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    W = main()
    print(len(W), W.composer.nunique())
    print(W.groupby("group").size().to_string())
    print((W.subgenre.str.endswith("other") | (W.subgenre == "other")).mean())
