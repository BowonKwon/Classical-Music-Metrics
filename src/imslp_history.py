"""Tempo markings and instrument use over time, from IMSLP work pages (CC BY-SA 4.0).

  python src/imslp_history.py

Inputs: data/raw/imslp/*.jsonl (composer categories and category_symphonies.jsonl),
fields "Number of Movements/Sections", "Year/Date of Composition", "InstrDetail".

Outputs (data/derived/):
  imslp_movement_tempo.csv     one row per movement line with a recognised tempo word
  imslp_tempo_by_period.csv    25-year bin x tempo class: share of movements (symphonies category)
  imslp_tempo_language.csv     25-year bin: share of movements whose tempo word is not Italian
  imslp_instrument_use.csv     25-year bin x instrument: share of symphonies whose InstrDetail names it
"""
from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from work_activity import years  # noqa: E402

# Italian tempo words, slow -> fast, with an ordinal rank
ITALIAN = ["grave", "largo", "larghetto", "lento", "adagio", "adagietto", "andante", "andantino", "moderato",
           "allegretto", "allegro", "vivo", "vivace", "vivacissimo", "presto", "prestissimo"]
CLASS = {"grave": "slow", "largo": "slow", "larghetto": "slow", "lento": "slow", "adagio": "slow", "adagietto": "slow",
         "andante": "moderately slow", "andantino": "moderately slow", "moderato": "moderate",
         "allegretto": "moderately fast", "allegro": "fast", "vivo": "fast", "vivace": "fast", "vivacissimo": "very fast", "presto": "very fast", "prestissimo": "very fast"}
# vernacular tempo words (German, French, English, Russian transliteration rare) -> class
VERNACULAR = {
    "langsam": "slow", "sehr langsam": "slow", "breit": "slow", "getragen": "slow", "feierlich": "slow",
    "mässig": "moderate", "massig": "moderate", "gemächlich": "moderately slow", "gehend": "moderately slow", "ruhig": "moderately slow",
    "bewegt": "moderately fast", "lebhaft": "fast", "rasch": "fast", "schnell": "very fast", "sehr schnell": "very fast", "stürmisch": "fast",
    "lent": "slow", "très lent": "slow", "modéré": "moderate", "modérément": "moderate", "animé": "fast", "vif": "fast", "très vif": "very fast", "rapide": "very fast",
    "slow": "slow", "slowly": "slow", "moderately": "moderate", "fast": "fast", "quick": "fast", "lively": "fast",
}
CLASSES = ["slow", "moderately slow", "moderate", "moderately fast", "fast", "very fast"]
IT_RE = re.compile(r"\b(" + "|".join(sorted(ITALIAN, key=len, reverse=True)) + r")\b", re.I)
VN_RE = re.compile(r"\b(" + "|".join(sorted(map(re.escape, VERNACULAR), key=len, reverse=True)) + r")\b", re.I)

INSTRUMENTS = {
    "piccolo": r"piccolo", "flute": r"\bflutes?\b", "oboe": r"\boboes?\b", "English horn": r"english horn|cor anglais",
    "clarinet": r"(?<!bass )\bclarinets?\b", "bass clarinet": r"bass clarinet", "bassoon": r"(?<!contra)(?<!double )\bbassoons?\b",
    "contrabassoon": r"contrabassoon|double bassoon", "horn": r"(?<!english )(?<!basset )\bhorns?\b", "trumpet": r"\btrumpets?\b",
    "trombone": r"\btrombones?\b", "tuba": r"\btubas?\b", "timpani": r"timpani",
    "other percussion": r"percussion|bass drum|cymbal|triangle|snare|side drum|tam tam|glockenspiel|xylophone|\bbells?\b|tambourine|castanets|whip|tubular",
    "harp": r"\bharps?\b", "celesta": r"celesta", "organ": r"\borgan(o)?\b", "piano": r"\bpiano(forte)?\b", "saxophone": r"saxophone",
    "harpsichord / continuo": r"harpsichord|continuo",
}


BUNDLE = re.compile(r"^\s*\d+\s+(symphonies|sinfonias|sinfonie|sinfonien|symphonies?\b)", re.I)


def single_orchestral_symphony(r: dict) -> bool:
    """Keep one-symphony pages for orchestra: drop list pages, bundles ("6 Symphonies, Op.3")
    and organ-only symphonies (Widor, Vierne), which are symphonies but not orchestral."""
    title = r.get("Work Title") or ""
    page = r.get("page") or ""
    if page.startswith("List of") or not (r.get("Tags") or ""):
        return False
    if BUNDLE.search(title):
        return False
    if (r.get("Instrumentation") or "").strip().lower() in ("organ", "organ solo"):
        return False
    return True


def movement_lines(text: str | None) -> list[str]:
    if not isinstance(text, str):
        return []
    t = re.sub(r"\{\{K\|[^}]*\}\}", " ", text)
    t = re.sub(r"\{\{[^}]*\}\}|<[^>]+>|\[\[|\]\]", " ", t)
    return [l.strip("#*: ").strip() for l in t.split("\n") if l.strip().startswith(("#", "*"))]


def tempo_of(line: str):
    m = IT_RE.search(line)
    vn = VN_RE.search(line)
    if m and (not vn or m.start() <= vn.start()):
        w = m.group(1).lower()
        return w, CLASS[w], "it"
    if vn:
        w = vn.group(1).lower()
        return w, VERNACULAR.get(w, VERNACULAR.get(w.replace("ä", "a"), None)), "vernacular"
    return None, None, None


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    raw = pd.concat([pd.read_json(f, lines=True) for f in glob.glob("data/raw/imslp/*.jsonl")], ignore_index=True)
    raw = raw.astype(object).where(raw.notna(), None)
    raw["source"] = np.where(raw["composer"].astype(str).str.startswith("category:"), "symphonies", "composer")
    out = Path("data/derived")
    rows = []
    for r in raw.to_dict("records"):
        ys, ye, kind = years(r.get("Year/Date of Composition"))
        if ys is None or kind == "terminus" or not (1650 <= ys <= 2026):
            continue
        if r["source"] == "symphonies" and not single_orchestral_symphony(r):
            continue
        lines = movement_lines(r.get("Number of Movements/Sections"))
        for i, line in enumerate(lines, 1):
            w, cls, lang = tempo_of(line)
            rows.append({"source": r["source"], "page": r["page"], "year": ys, "line_no": i, "tempo_word": w, "tempo_class": cls, "lang": lang, "line": line[:120]})
    ALL = pd.DataFrame(rows).drop_duplicates(subset=["page", "line_no"])
    M = ALL[ALL.tempo_word.notna()]
    M.to_csv(out / "imslp_movement_tempo.csv", index=False, encoding="utf-8")
    sym_pages = raw.loc[raw.source == "symphonies", "page"]
    S = M[M.page.isin(sym_pages)].copy()
    S["bin"] = (S.year // 25 * 25).astype(int)
    SA = ALL[ALL.page.isin(sym_pages)].copy()
    SA["bin"] = (SA.year // 25 * 25).astype(int)
    tp = S.groupby(["bin", "tempo_class"]).size().rename("n").reset_index()
    tp["share"] = tp.n / tp.groupby("bin").n.transform("sum")
    tp = tp.merge(S.groupby("bin").size().rename("movements").reset_index(), on="bin")
    tp.to_csv(out / "imslp_tempo_by_period.csv", index=False, encoding="utf-8")
    lang = S.groupby("bin").apply(lambda g: pd.Series({"movements": len(g), "non_italian_share": (g.lang == "vernacular").mean(), "works": g.page.nunique()})).reset_index()
    # recognition: listed lines (movements, parts and version headers) vs lines with a recognised tempo word
    lang = lang.merge(SA.groupby("bin").size().rename("listed_lines").reset_index(), on="bin", how="left")
    lang["recognised_share"] = lang["movements"] / lang["listed_lines"]
    lang.to_csv(out / "imslp_tempo_language.csv", index=False, encoding="utf-8")
    # first-movement and overall tempo word frequency (all sources)
    # instruments
    sy = raw[raw.source == "symphonies"].copy()
    inst = []
    for r in sy.to_dict("records"):
        ys, ye, kind = years(r.get("Year/Date of Composition"))
        d = r.get("InstrDetail")
        if ys is None or kind == "terminus" or not d or not (1700 <= ys <= 2026) or not single_orchestral_symphony(r):
            continue
        t = re.sub(r"\{\{[^}]*\}\}|<[^>]+>", " ", d).lower()
        t = re.sub(r"[\s\-]+", " ", t)  # "English-horn", "bass  clarinet" -> single spaces for the boundary patterns
        rec = {"page": r["page"], "year": ys}
        for k, pat in INSTRUMENTS.items():
            rec[k] = bool(re.search(pat, t))
        inst.append(rec)
    I = pd.DataFrame(inst)
    I["bin"] = (I.year // 25 * 25).astype(int)
    use = I.groupby("bin")[list(INSTRUMENTS)].mean().reset_index().melt(id_vars="bin", var_name="instrument", value_name="share")
    use = use.merge(I.groupby("bin").size().rename("symphonies").reset_index(), on="bin")
    use.to_csv(out / "imslp_instrument_use.csv", index=False, encoding="utf-8")
    I.to_csv(out / "imslp_symphony_instruments.csv", index=False, encoding="utf-8")
    print("movements with tempo word", len(M), "of which symphonies category", len(S))
    print(lang.round(3).to_string())
    print(tp.pivot(index="bin", columns="tempo_class", values="share").reindex(columns=CLASSES).round(2).to_string())
    print("symphonies with InstrDetail and year", len(I))
    print(use.pivot(index="bin", columns="instrument", values="share").round(2).to_string())


if __name__ == "__main__":
    main()
