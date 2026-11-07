"""Cross-orchestra repertoire comparison (1.5 prototype). No ranking: metrics side by side.

Sources (each adapter returns the common table COLS):
  nyphil      NY Phil Performance History (CC0). Unit U1: one row per (program, work), weight = number of concerts.
  gewandhaus  Hartmann-Enke, Gewandhaus repertoire research dataset 1781-1895 (Zenodo 5995965, CC BY 4.0).
              One row per work performed in a subscription-series concert (extra concerts excluded by the source); weight 1.
  carnegie    Carnegie Hall Performance History (CC0), events with an orchestra role; weight 1 per (event, work).
              Visiting orchestras' New York appearances only - a touring sample, not a home-season repertoire.
  seoulphil   Seoul Philharmonic, Seoul Open Data OA-22909/OA-22910 (KOGL Type 1). Added when the Korean file is in.

Composer identity: each source keeps its own name string in composer_raw; `composer` is the NY Phil canonical
name when the crosswalk finds one (exact normalized match, then surname + given-name initials if unique),
otherwise the source string. The crosswalk is written to data/aliases/orch_composer_xwalk.csv for review.

Living share: NY Phil and Carnegie use Wikidata birth/death years (composer_wikidata.csv, matched names only, the
unmatched share is reported); Gewandhaus uses the source's own 'Status Leben' flag (1 = alive on the concert date).
"""
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import repertoire_metrics as rm  # noqa: E402

RAW = ROOT / "data" / "raw"
DER = ROOT / "data" / "derived"
ALI = ROOT / "data" / "aliases"
COLS = ["orchestra", "date", "season_start", "concert_id", "composer_raw", "work", "weight", "alive"]
NON_PERSON = {"[s. n.]", "", "Traditional", "Anonymous", "Anon."}


PARTICLES = {"von", "van", "de", "di", "da", "y", "le", "la", "du", "der"}


def norm(s: str) -> str:
    """Lowercase ASCII; ß -> ss; bracketed variants '[Méhul]' dropped. Digits are kept, so a disambiguated
    'Schubert, Franz (1808-1878)' never equals 'Schubert, Franz'."""
    s = re.sub(r"\[[^\]]*\]", "", (s or "").replace("ß", "ss").replace("ẞ", "ss"))
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9,() -]", "", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def split_name(name: str) -> tuple[str, list[str]]:
    n = norm(name)
    if "," not in n or "(" in n:
        return "", []
    sur, given = n.split(",", 1)
    return sur.strip(), [w for w in re.split(r"[ -]", given) if w and w not in PARTICLES]


def compatible(g1: list[str], g2: list[str]) -> bool:
    """Same person if the full (3+ letter) given names of one are a subset of the other's (Joseph ~ Franz Joseph,
    but Johann Heinrich !~ Johann Carl), or their first given names agree in the first three letters
    (Georg ~ George). A bare initial never matches. True homonyms (Franz Anton Schubert) go in the manual table."""
    full1, full2 = {w for w in g1 if len(w) >= 3}, {w for w in g2 if len(w) >= 3}
    if full1 and full2 and (full1 <= full2 or full2 <= full1):
        return True
    return bool(g1 and g2 and len(g1[0]) >= 3 and len(g2[0]) >= 3 and g1[0][:3] == g2[0][:3])


def load_nyphil() -> pd.DataFrame:
    df = rm.apply_aliases(rm.load_entries(RAW), ALI / "nyphil_composers.csv")
    pairs = rm.to_pairs(df)
    pairs = pairs[pairs["flag"] == "person"]
    first = df.groupby("program_id")["first_date"].first()
    return pd.DataFrame({
        "orchestra": "nyphil", "date": pairs["program_id"].map(first).values, "season_start": pairs["season_start"].values,
        "concert_id": pairs["program_id"].astype(str).values, "composer_raw": pairs["composer"].values,
        "work": pairs["work_id"].astype(str).values, "weight": pairs["u1"].astype(float).values, "alive": np.nan})


def load_gewandhaus() -> pd.DataFrame:
    d = pd.read_csv(RAW / "gewandhaus_zenodo" / "GWH_1781-1895_repertory_research_data.csv", sep=";", encoding="utf-8-sig", dtype=str)
    d = d[~d["Komponisten"].fillna("").isin(NON_PERSON)]
    alive = d["Status Leben"].map({"1": 1.0, "0": 0.0})
    return pd.DataFrame({
        "orchestra": "gewandhaus", "date": d["Datum"].str.replace("/", "-"), "season_start": d["Saison"].str[:4].astype(int),
        "concert_id": d["Datum"], "composer_raw": d["Komponisten"], "work": d["Comp+werk"], "weight": 1.0, "alive": alive})


CARNEGIE_NON_PERSON = {"Anonymous", "Composers, Various", "Unknown composer of folk songs", "Unknown author of spoken text",
                       "Unknown composer of spirituals", "Dance", "Traditional"}
SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii"}


def invert(label: str) -> str:
    """Carnegie labels are 'Given Surname' ('Ludwig van Beethoven', 'Johann Strauss Jr.'); NY Phil uses
    'Surname, Given'. Last token (before a Jr./Sr. suffix) becomes the surname; particles stay with the given
    names, where compatible() ignores them. Single-token names and names with commas are left alone."""
    if not isinstance(label, str) or "," in label:
        return label
    t = label.split()
    suf = []
    while t and t[-1].lower() in SUFFIXES:
        suf.insert(0, t.pop())
    if len(t) < 2:
        return label
    return f"{t[-1]}, {' '.join(t[:-1] + suf)}"


def load_carnegie() -> pd.DataFrame | None:
    base = RAW / "carnegiehall"
    if not (base / "works").exists() or not (base / "events").exists():
        return None
    import json

    def rows(sub):
        out = []
        for f in sorted((base / sub).glob("page-*.json")):
            for b in json.loads(f.read_text(encoding="utf-8"))["results"]["bindings"]:
                out.append({k: v["value"] for k, v in b.items()})
        return pd.DataFrame(out)
    ev, wk = rows("events"), rows("works")
    if ev.empty or wk.empty:
        return None
    ev = ev.drop_duplicates(["ev", "org"])
    wk = wk[wk.get("compLabel", pd.Series(dtype=str)).fillna("") != ""]
    wk = wk[~wk["compLabel"].isin(CARNEGIE_NON_PERSON)]
    m = wk.merge(ev[["ev", "date", "orgLabel"]], on="ev")
    m["date"] = m["date"].str[:10]
    yr = m["date"].str[:4].astype(int)
    mo = m["date"].str[5:7].astype(int)
    return pd.DataFrame({
        "orchestra": "carnegie:" + m["orgLabel"].fillna("?"), "date": m["date"], "season_start": np.where(mo >= 8, yr, yr - 1),
        "concert_id": m["ev"], "composer_raw": m["compLabel"].map(invert), "work": m["work"], "weight": 1.0, "alive": np.nan})


def crosswalk(names: pd.Series, canon: pd.Series) -> pd.DataFrame:
    """Order: manual table (data/aliases/orch_composer_manual.csv: composer_raw, composer, note) -> exact normalized
    -> same surname with compatible given names, only when exactly one canonical candidate qualifies."""
    canon = pd.Series(canon.unique())
    exact = {norm(c): c for c in canon}
    by_sur: dict[str, list] = {}
    for c in canon:
        s, g = split_name(c)
        if s:
            by_sur.setdefault(s, []).append((c, g))
    mpath = ALI / "orch_composer_manual.csv"
    manual = dict(pd.read_csv(mpath, dtype=str)[["composer_raw", "composer"]].values) if mpath.exists() else {}
    rows = []
    for n in pd.Series(names.unique()):
        if n in manual:
            rows.append((n, manual[n] if manual[n] != "-" else n, "manual" if manual[n] != "-" else "manual_none"))
            continue
        if norm(n) in exact:
            rows.append((n, exact[norm(n)], "exact"))
            continue
        s, g = split_name(n)
        cands = [c for c, cg in by_sur.get(s, []) if compatible(g, cg)]
        rows.append((n, cands[0], "surname+given") if len(cands) == 1 else (n, n, "unmatched"))
    return pd.DataFrame(rows, columns=["composer_raw", "composer", "method"])


def living_from_wikidata(df: pd.DataFrame) -> pd.Series:
    wd = pd.read_csv(ALI / "composer_wikidata.csv")
    wd = wd.dropna(subset=["birth_year"]).drop_duplicates("composer").set_index("composer")
    yr = pd.to_numeric(df["date"].str[:4], errors="coerce")
    b = df["composer"].map(wd["birth_year"])
    dth = df["composer"].map(wd["death_year"])
    alive = np.where(b.isna(), np.nan, ((dth.isna()) | (dth >= yr)).astype(float))
    return pd.Series(alive, index=df.index)


def period_metrics(df: pd.DataFrame, period: str = "decade") -> pd.DataFrame:
    df = df.copy()
    df["period"] = (df["season_start"] // 10 * 10) if period == "decade" else df["season_start"]
    out = []
    for (o, p), g in df.groupby(["orchestra", "period"]):
        s = g.groupby("composer")["weight"].sum().sort_values(ascending=False)
        sh = s / s.sum()
        known = g["alive"].notna()
        w = g["weight"]
        out.append({
            "orchestra": o, "period": int(p), "concerts": g["concert_id"].nunique(), "work_performances": float(w.sum()),
            "distinct_composers": len(s), "top_composer": s.index[0], "top_composer_share": sh.iloc[0],
            "top10_share": sh.iloc[:10].sum(), "hhi": float((sh ** 2).sum()),
            "living_share": float((g.loc[known, "alive"] * w[known]).sum() / w[known].sum()) if known.any() else np.nan,
            "living_coverage": float(w[known].sum() / w.sum()),
        })
    return pd.DataFrame(out)


def overlap(df: pd.DataFrame, a: str, b: str) -> pd.DataFrame:
    df = df.assign(period=df["season_start"] // 10 * 10)
    out = []
    for p in sorted(set(df.loc[df.orchestra == a, "period"]) & set(df.loc[df.orchestra == b, "period"])):
        va = df[(df.orchestra == a) & (df.period == p)].groupby("composer")["weight"].sum()
        vb = df[(df.orchestra == b) & (df.period == p)].groupby("composer")["weight"].sum()
        v = pd.concat([va / va.sum(), vb / vb.sum()], axis=1).fillna(0)
        cos = float(v.iloc[:, 0] @ v.iloc[:, 1] / np.sqrt((v.iloc[:, 0] ** 2).sum() * (v.iloc[:, 1] ** 2).sum()))
        ta, tb = set(va.nlargest(20).index), set(vb.nlargest(20).index)
        out.append({"a": a, "b": b, "period": int(p), "cosine": cos, "top20_jaccard": len(ta & tb) / len(ta | tb),
                    "shared_composers": int(((v.iloc[:, 0] > 0) & (v.iloc[:, 1] > 0)).sum())})
    return pd.DataFrame(out)


def main():
    parts = [load_nyphil(), load_gewandhaus()]
    c = load_carnegie()
    if c is not None:
        parts.append(c)
    df = pd.concat(parts, ignore_index=True)
    ny = df[df.orchestra == "nyphil"]["composer_raw"]
    xw = crosswalk(df[df.orchestra != "nyphil"]["composer_raw"], ny)
    xw.to_csv(ALI / "orch_composer_xwalk.csv", index=False, encoding="utf-8", lineterminator="\n")
    df["composer"] = df["composer_raw"].map(dict(zip(xw.composer_raw, xw.composer))).fillna(df["composer_raw"])
    wd_alive = living_from_wikidata(df)
    df["alive"] = df["alive"].where(df["orchestra"] == "gewandhaus", wd_alive)
    df.to_csv(DER / "orch_performances.csv", index=False, encoding="utf-8", lineterminator="\n")
    pm = period_metrics(df)
    pm.to_csv(DER / "orch_decade_metrics.csv", index=False, encoding="utf-8", lineterminator="\n")
    ov = overlap(df, "nyphil", "gewandhaus")
    ov.to_csv(DER / "orch_overlap_nyphil_gewandhaus.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(xw["method"].value_counts().to_string())
    w = df[df.orchestra == "gewandhaus"].merge(xw, on="composer_raw")
    print("gewandhaus weight matched:", round(float(w.loc[w.method != "unmatched", "weight"].sum() / w["weight"].sum()), 3))
    print(pm[pm.orchestra.isin(["nyphil", "gewandhaus"]) & pm.period.between(1840, 1890)].round(3).to_string())
    print(ov.round(3).to_string())
    tp = touring_profiles(df)
    tp.to_csv(DER / "orch_touring_profiles.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(tp.round(3).to_string())
    vc = overlap(df.replace({"orchestra": {"carnegie:New York Philharmonic": "nyphil@carnegie"}}), "nyphil", "nyphil@carnegie")
    vc.to_csv(DER / "orch_check_nyphil_two_sources.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(vc.round(3).to_string())


FOCUS_TOURING = {
    "carnegie:Boston Symphony Orchestra": "Boston SO", "carnegie:Philadelphia Orchestra": "Philadelphia",
    "carnegie:Cleveland Orchestra": "Cleveland", "carnegie:Chicago Symphony Orchestra": "Chicago SO",
    "carnegie:Vienna Philharmonic Orchestra": "Vienna Phil", "carnegie:Berlin Philharmonic Orchestra": "Berlin Phil",
    "carnegie:Royal Concertgebouw Orchestra": "Concertgebouw", "carnegie:London Symphony Orchestra": "LSO",
    "carnegie:Leipzig Gewandhaus Orchestra": "Gewandhaus (NY tours)", "carnegie:Seoul Philharmonic Orchestra": "Seoul Phil (NY tours)",
}
WINDOWS = [(1955, 1989), (1990, 2026)]


def rarefied_baseline(home: pd.DataFrame, n: int, reps: int = 500, seed: int = 0) -> dict:
    """Top-10 share and composer count depend on sample size. Draw n work performances (without replacement,
    weights as counts) from NY Phil's home seasons in the same window; report the mean and 2.5-97.5 percentiles."""
    pool = np.repeat(home["composer"].to_numpy(), home["weight"].round().astype(int).to_numpy())
    if n <= 0 or n > len(pool):
        return {"base_top10_mean": np.nan, "base_top10_lo": np.nan, "base_top10_hi": np.nan, "base_distinct_mean": np.nan}
    rng = np.random.default_rng(seed)
    t10, dist = [], []
    for _ in range(reps):
        _, cnt = np.unique(rng.choice(pool, n, replace=False), return_counts=True)
        cnt = np.sort(cnt)[::-1]
        t10.append(cnt[:10].sum() / n); dist.append(len(cnt))
    return {"base_top10_mean": float(np.mean(t10)), "base_top10_lo": float(np.percentile(t10, 2.5)),
            "base_top10_hi": float(np.percentile(t10, 97.5)), "base_distinct_mean": float(np.mean(dist))}


def touring_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """Each focus orchestra's Carnegie Hall programs pooled over a window, set beside NY Phil's home seasons in the
    same window. A touring program is a selection (often the orchestra's showpieces), not a season."""
    out = []
    home = df[df.orchestra == "nyphil"]
    for lo, hi in WINDOWS:
        hw = home[home.season_start.between(lo, hi)]
        hv = hw.groupby("composer")["weight"].sum()
        hv = hv / hv.sum()
        groups = [("NY Phil (home seasons)", hw)] + [
            (lab, df[(df.orchestra == k) & df.season_start.between(lo, hi)]) for k, lab in FOCUS_TOURING.items()]
        for lab, g in groups:
            if g.empty:
                continue
            s = g.groupby("composer")["weight"].sum().sort_values(ascending=False)
            sh = s / s.sum()
            v = pd.concat([sh, hv], axis=1).fillna(0)
            known = g["alive"].notna()
            out.append({
                "window": f"{lo}-{hi}", "orchestra": lab, "concerts": g["concert_id"].nunique(), "work_performances": float(g["weight"].sum()),
                "distinct_composers": len(s), "top3": "; ".join(f"{c} {x:.0%}" for c, x in sh.head(3).items()),
                "top10_share": sh.iloc[:10].sum(), "hhi": float((sh ** 2).sum()),
                "living_share": float((g.loc[known, "alive"] * g.loc[known, "weight"]).sum() / g.loc[known, "weight"].sum()) if known.any() else np.nan,
                "living_coverage": float(g.loc[known, "weight"].sum() / g["weight"].sum()),
                **rarefied_baseline(hw, int(round(g["weight"].sum()))),
                "cosine_to_nyphil_home": float(v.iloc[:, 0] @ v.iloc[:, 1] / np.sqrt((v.iloc[:, 0] ** 2).sum() * (v.iloc[:, 1] ** 2).sum())),
            })
    return pd.DataFrame(out)


if __name__ == "__main__":
    main()
