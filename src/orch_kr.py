"""Korean orchestras' own concert programs (1.19): Suwon, Bucheon and Busan beside the Seoul Philharmonic.

Inputs (committed derived tables; the saved concert pages and the Busan record book are not in the repository):
  data/derived/orch_kr_works.csv      one row per work on a concert program (composer + title as written, canonical composer)
  data/derived/orch_kr_concerts.csv   one row per listed concert (kind, canceled flag, whether a program was found as text)
  data/derived/seoulphil_works.csv    Seoul Philharmonic (1.5), titles with attributed composers
  data/derived/orch_kr_festival_works.csv  Symphony Festival programs 2022-2026 for these orchestras
  data/aliases/composer_wikidata.csv  birth and death years

Unit: one work on one concert program = 1. Suwon and Bucheon programs are announcements on concert pages; the Busan
rows come from the orchestra's own record book (1962-2021). Comparison across the four uses subscription concerts
only, in the years all four sources cover (WINDOW). Suwon and Busan, the two long series, are also set out by decade.
Outputs: data/derived/orch_kr_*.csv and orch_kr_summary.json (read by orchestra_kr_pages.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D, ALI = ROOT / "data/derived", ROOT / "data/aliases"
WINDOW = (2009, 2021)      # Seoul's public data start in 2009; the Busan record book ends in 2021
SEED = 0
REPS = 500
SUB = "정기"
ORDER = ["seoul", "suwon", "bucheon", "busan"]
LONG = ["suwon", "busan"]  # series that reach back to the 1980s or earlier
DEC_N = 90                 # works drawn per decade for the size-matched decade values; decades with fewer works are left out
KEY = {"수원시립교향악단": "suwon", "부천필하모닉오케스트라": "bucheon", "부산시립교향악단": "busan"}


def load():
    w = pd.read_csv(D / "orch_kr_works.csv", dtype=str, keep_default_na=False)
    c = pd.read_csv(D / "orch_kr_concerts.csv", dtype=str, keep_default_na=False)
    for df in (w, c):
        df["orch"] = df["orchestra"].map(KEY)
        df["year"] = pd.to_numeric(df["year"], errors="coerce")
    c["n_with_composer"] = pd.to_numeric(c["n_with_composer"])
    canc = set(c[c.cancelled == "1"].concert_id)
    c = c[c.cancelled != "1"]
    w["canceled"] = w.concert_id.isin(canc)
    # composer identity: the canonical (NY Phil) name when matched, otherwise the name as written on the page
    w["cid"] = np.where(w.composer != "", w.composer, "ko:" + w.composer_as_written)
    w = w[w.status.isin(["matched", "unmatched"])]
    return w[~w.canceled], c, w[w.canceled]


def load_seoul():
    s = pd.read_csv(D / "seoulphil_works.csv")
    s = s[(s.type_ko == "정기공연") & (s.series == "관현악")].copy()      # orchestral subscription series only (chamber series left out)
    s["year"] = s.date.str[:4].astype(int)
    return s


def shares(v: pd.Series) -> pd.Series:
    v = v[v > 0]
    return v / v.sum()


def cosine(a: pd.Series, b: pd.Series) -> float:
    """Written to 12 decimals by the callers: the last digits of a floating-point dot product differ between environments."""
    v = pd.concat([shares(a), shares(b)], axis=1).fillna(0).sort_index()      # a fixed order of summation: the last digit no longer depends on the order of the inputs
    return float(v.iloc[:, 0] @ v.iloc[:, 1] / np.sqrt((v.iloc[:, 0] ** 2).sum() * (v.iloc[:, 1] ** 2).sum()))


def rarefy(counts: pd.Series, n: int, reps: int = REPS, seed: int = SEED) -> dict:
    """Top-10 share and number of composers depend on sample size: draw n works without replacement, reps times."""
    pool = np.repeat(counts.index.to_numpy(), counts.round().astype(int).to_numpy())
    if n > len(pool):
        return {}
    rng = np.random.default_rng(seed)
    t10, dist = [], []
    for _ in range(reps):
        _, cnt = np.unique(rng.choice(pool, n, replace=False), return_counts=True)
        cnt = np.sort(cnt)[::-1]
        t10.append(cnt[:10].sum() / n); dist.append(len(cnt))
    return {"top10_mean": float(np.mean(t10)), "top10_lo": float(np.percentile(t10, 2.5)), "top10_hi": float(np.percentile(t10, 97.5)),
            "distinct_mean": float(np.mean(dist)), "distinct_lo": float(np.percentile(dist, 2.5)), "distinct_hi": float(np.percentile(dist, 97.5))}


def living(df: pd.DataFrame, cid: str, year: str) -> dict:
    """Works by composers alive in the concert year (Wikidata dates). Low end: unknown dates counted as dead; high end: as alive."""
    wd = pd.read_csv(ALI / "composer_wikidata.csv").dropna(subset=["birth_year"]).drop_duplicates("composer").set_index("composer")
    b, d = df[cid].map(wd["birth_year"]), df[cid].map(wd["death_year"])
    known = b.notna()
    alive = known & (d.isna() | (d >= df[year]))
    n = len(df)
    return {"living_known": int(known.sum()), "living_n": int(alive.sum()), "living_share_known": float(alive.sum() / known.sum()) if known.any() else None,
            "living_lo": float(alive.sum() / n) if n else None, "living_hi": float((alive.sum() + (n - known.sum())) / n) if n else None}


def ranked(v: pd.Series) -> pd.Series:
    """Counts in descending order, ties by name, so that a rerun in another environment writes the same text (the order of tied names used to depend on the environment)."""
    return v.sort_index().sort_values(ascending=False, kind="mergesort")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    w, c, wc = load()
    s = load_seoul()
    lo, hi = WINDOW
    out = {"window": [lo, hi], "seed": SEED, "reps": REPS, "decade_n": DEC_N}

    # 1) coverage by year: listed concerts and those with a program found as text
    cov = (c.dropna(subset=["year"]).groupby(["orch", "kind", "year"]).agg(concerts=("concert_id", "size"), with_program=("n_with_composer", lambda x: int((x > 0).sum())),
                                                                          works=("n_with_composer", "sum")).reset_index())
    sy = s.groupby("year").agg(concerts=("concert_id", "nunique"), works=("title", "size"), attributed=("composer", lambda x: int(x.notna().sum()))).reset_index()
    # with_program means the same for all four: concerts with at least one work whose composer is known (Seoul: an attributed composer)
    sy.insert(0, "orch", "seoul"); sy.insert(1, "kind", SUB)
    sy["with_program"] = sy.year.map(s.dropna(subset=["composer"]).groupby("year").concert_id.nunique()).fillna(0).astype(int)
    cov = pd.concat([cov, sy], ignore_index=True)
    cov["year"] = cov["year"].astype("Int64")
    cov.to_csv(D / "orch_kr_coverage_by_year.csv", index=False, encoding="utf-8", lineterminator="\n")

    # 2) subscription concerts in the common window
    sub = w[(w.kind == SUB) & w.year.between(lo, hi)]
    csub = c[(c.kind == SUB) & c.year.between(lo, hi)]
    sw = s[s.year.between(lo, hi)]
    vec = {o: sub[sub.orch == o].groupby("cid").size().astype(float) for o in ORDER if o != "seoul"}
    vec["seoul"] = sw.dropna(subset=["composer"]).groupby("composer").size().astype(float)
    n_min = int(min(v.sum() for v in vec.values()))
    rows = []
    for o in ORDER:
        v = ranked(vec[o])
        sh = v / v.sum()
        if o == "seoul":
            n_all, n_attr = len(sw), int(sw.composer.notna().sum())
            conc, prog = sw.concert_id.nunique(), sw.dropna(subset=["composer"]).concert_id.nunique()
            lv = living(sw.dropna(subset=["composer"]).assign(cid=lambda d: d.composer), "cid", "year")
            lv["living_lo"] = lv["living_n"] / n_all; lv["living_hi"] = (lv["living_n"] + (n_all - lv["living_known"])) / n_all
            matched = n_attr
        else:
            g = sub[sub.orch == o]
            n_all = n_attr = len(g)
            cc = csub[csub.orch == o]
            conc, prog = len(cc), int((cc.n_with_composer > 0).sum())
            lv = living(g, "cid", "year")
            matched = int((g.status == "matched").sum())
        r = rarefy(v, n_min)
        rows.append({"orch": o, "concerts": conc, "concerts_with_program": prog, "works": n_all, "works_with_composer": n_attr, "works_matched_to_canonical": matched,
                     "distinct_composers": len(v), "top_composer": v.index[0], "top_composer_share": float(sh.iloc[0]),
                     "top10_share_attributed": float(sh.iloc[:10].sum()),
                     "top10_lo": float(v.iloc[:10].sum() / n_all), "top10_hi": float((v.iloc[:10].sum() + (n_all - n_attr)) / n_all),
                     "hhi": float((sh ** 2).sum()), "rarefied_n": n_min, **{"rarefied_" + k: x for k, x in r.items()}, **lv})
    summ = pd.DataFrame(rows)
    summ.to_csv(D / "orch_kr_summary.csv", index=False, encoding="utf-8", lineterminator="\n")
    out["rarefied_n"] = n_min

    # 3) pairwise cosine of composer shares
    pairs = []
    for i, a in enumerate(ORDER):
        for b_ in ORDER[i + 1:]:
            both = pd.concat([shares(vec[a]), shares(vec[b_])], axis=1).fillna(0)
            pairs.append({"a": a, "b": b_, "cosine": round(cosine(vec[a], vec[b_]), 12), "shared_composers": int(((both.iloc[:, 0] > 0) & (both.iloc[:, 1] > 0)).sum())})
    pd.DataFrame(pairs).to_csv(D / "orch_kr_cosine.csv", index=False, encoding="utf-8", lineterminator="\n")

    # 4) composer shares side by side (union of the four)
    tab = pd.concat([shares(vec[o]).rename(o + "_share") for o in ORDER] + [vec[o].rename(o + "_works") for o in ORDER], axis=1).fillna(0)
    tab["mean_share"] = tab[[o + "_share" for o in ORDER]].mean(axis=1)
    tab = tab.sort_index().sort_values("mean_share", ascending=False, kind="mergesort").reset_index().rename(columns={"index": "composer"})
    ko = dict(zip(w.cid, w.composer_ko))
    tab["composer_ko"] = tab.composer.map(lambda x: ko.get(x, "") or (x[3:] if x.startswith("ko:") else ""))
    tab.to_csv(D / "orch_kr_composer_shares.csv", index=False, encoding="utf-8", lineterminator="\n")

    # 5) the long series by decade (subscription concerts, every year with programs)
    lw = w[w.orch.isin(LONG) & (w.kind == SUB)].copy()
    lw["decade"] = (lw.year // 10 * 10).astype(int)
    lc = c[c.orch.isin(LONG) & (c.kind == SUB)].dropna(subset=["year"]).copy()
    lc["decade"] = (lc.year // 10 * 10).astype(int)
    dec, dvec = [], {}
    for (o, d_), g in lw.groupby(["orch", "decade"]):
        v = ranked(g.groupby("cid").size()).astype(float)
        dvec[(o, int(d_))] = v
        cc = lc[(lc.orch == o) & (lc.decade == d_)]
        r = rarefy(v, DEC_N) if len(g) >= DEC_N else {}
        dec.append({"orch": o, "decade": int(d_), "first_year": int(g.year.min()), "last_year": int(g.year.max()), "concerts": len(cc),
                    "concerts_with_program": int((cc.n_with_composer > 0).sum()), "works": len(g), "distinct_composers": len(v),
                    "top3": "; ".join(f"{k} {x / len(g):.0%}" for k, x in v.head(3).items()), "top10_share": float(v.iloc[:10].sum() / len(g)),
                    "top10_n90_mean": r.get("top10_mean"), "top10_n90_lo": r.get("top10_lo"), "top10_n90_hi": r.get("top10_hi"),
                    "unmatched_share": float((g.status == "unmatched").mean())})
    dec = pd.DataFrame(dec)
    dec.to_csv(D / "orch_kr_decades.csv", index=False, encoding="utf-8", lineterminator="\n")
    dp = []
    a, b_ = LONG
    for d_ in sorted({k[1] for k in dvec}):
        if (a, d_) in dvec and (b_, d_) in dvec and min(dvec[(a, d_)].sum(), dvec[(b_, d_)].sum()) >= DEC_N:
            both = pd.concat([shares(dvec[(a, d_)]), shares(dvec[(b_, d_)])], axis=1).fillna(0)
            dp.append({"a": a, "b": b_, "decade": d_, "cosine": round(cosine(dvec[(a, d_)], dvec[(b_, d_)]), 12),
                       "shared_composers": int(((both.iloc[:, 0] > 0) & (both.iloc[:, 1] > 0)).sum())})
    pd.DataFrame(dp).to_csv(D / "orch_kr_decade_pairs.csv", index=False, encoding="utf-8", lineterminator="\n")

    # 6) kinds of concert
    kinds = []
    wall = pd.read_csv(D / "orch_kr_works.csv", dtype=str, keep_default_na=False)
    call = pd.read_csv(D / "orch_kr_concerts.csv", dtype=str, keep_default_na=False)
    wall = wall[~wall.concert_id.isin(set(call[call.cancelled == "1"].concert_id))]      # canceled concerts enter no figure, title-only lines included
    wall["orch"] = wall.orchestra.map(KEY)
    for (o, k), g in wall.groupby(["orch", "kind"]):
        st = g.status.value_counts()
        cc = c[(c.orch == o) & (c.kind == k)]
        gm = g[g.status.isin(["matched", "unmatched"])]
        ids = np.where(gm.composer != "", gm.composer, "ko:" + gm.composer_as_written)
        v = ranked(pd.Series(ids).value_counts())
        kinds.append({"orch": o, "kind": k, "concerts": len(cc), "concerts_with_program": int((cc.n_with_composer > 0).sum()),
                      "works_with_composer": int(st.get("matched", 0) + st.get("unmatched", 0)), "matched_to_canonical": int(st.get("matched", 0)),
                      "lines_without_composer": int(st.get("no_composer", 0)), "distinct_composers": len(v),
                      "top5": "; ".join(f"{a_} {x / len(gm):.0%}" for a_, x in v.head(5).items()) if len(gm) else ""})
    pd.DataFrame(kinds).to_csv(D / "orch_kr_kinds.csv", index=False, encoding="utf-8", lineterminator="\n")

    # 7) most often programmed works (composer + work key), subscription concerts, all years with programs
    tw = w[(w.kind == SUB) & (w.work_key != "") & w.orch.isin(["suwon", "bucheon", "busan"])]
    top = (tw.groupby(["orch", "cid", "work_key"]).agg(n=("concert_id", "size"), first=("year", "min"), last=("year", "max"), composer_ko=("composer_ko", "first"),
                                                      example=("title", "first")).reset_index().sort_values(["orch", "n", "cid", "work_key"], ascending=[True, False, True, True]))
    top.groupby("orch").head(25).to_csv(D / "orch_kr_top_works.csv", index=False, encoding="utf-8", lineterminator="\n")

    # 8) festival vs home: was the work an orchestra took to the Symphony Festival also on one of its own subscription programs?
    f = pd.read_csv(D / "orch_kr_festival_works.csv", dtype=str, keep_default_na=False)
    f = f[f.orchestra.isin(KEY)].copy()
    f["orch"] = f.orchestra.map(KEY)
    f["cid"] = np.where(f.composer != "", f.composer, "ko:" + f.composer_ko)
    home, home_c = w[w.kind == SUB], wc[wc.kind == SUB]
    # the same work written differently on the two programs (read by hand, one row per festival work): data/aliases/orch_kr_festival_manual.csv
    man = pd.read_csv(ALI / "orch_kr_festival_manual.csv", dtype=str, keep_default_na=False)
    man = {(m.orch, m.festival_date, m.festival_title): (m.home_concert_id, m.home_title) for m in man.itertuples()}
    res = []
    for r in f.itertuples():
        key, key_c = (home.work_key == r.work_key), (home_c.work_key == r.work_key)
        if (r.orch, r.date, r.title) in man:
            hid, ht = man[(r.orch, r.date, r.title)]
            hit, hit_c = (home.concert_id == hid) & (home.title == ht), (home_c.concert_id == hid) & (home_c.title == ht)
            assert hit.any() or hit_c.any(), (hid, ht)
            key, key_c = key | hit, key_c | hit_c
        h = home[(home.orch == r.orch) & (home.cid == r.cid) & key]
        same = h[h.year == int(r.year)]
        hc = home_c[(home_c.orch == r.orch) & (home_c.cid == r.cid) & key_c & (home_c.year == int(r.year))]
        res.append({"orch": r.orch, "festival_date": r.date, "composer": r.cid, "composer_ko": r.composer_ko, "title": r.title, "work_key": r.work_key,
                    "home_same_year": "; ".join(sorted(same.date)), "home_same_year_canceled": "; ".join(sorted(hc.date)), "home_other_years": "; ".join(sorted(set(h.date) - set(same.date))),
                    "home_programs_that_year": int(c[(c.orch == r.orch) & (c.kind == SUB) & (c.year == int(r.year)) & (c.n_with_composer > 0)].shape[0])})
    pd.DataFrame(res).to_csv(D / "orch_kr_festival_vs_home.csv", index=False, encoding="utf-8", lineterminator="\n")

    out["totals"] = {}
    for o in ("suwon", "bucheon", "busan"):
        cs_, ws_ = c[(c.orch == o) & (c.kind == SUB)], w[(w.orch == o) & (w.kind == SUB)]
        out["totals"][o] = {"subscription_concerts": int(len(cs_)), "with_program": int((cs_.n_with_composer > 0).sum()), "works": int(len(ws_)),
                            "subscription_concerts_without_date": int(cs_.year.isna().sum()),
                            "first_year": int(cs_.year.min()), "last_year": int(cs_.year.max()),
                            "first_program_year": int(ws_.year.min()), "last_program_year": int(ws_.year.max())}
    (D / "orch_kr_summary.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(summ.round(3).T.to_string())
    print(pd.DataFrame(pairs).round(3).to_string())
    print(dec.round(3).to_string())
    print(pd.DataFrame(dp).round(3).to_string())
    print(pd.DataFrame(kinds).to_string())
    print(json.dumps(out["totals"], ensure_ascii=False))


if __name__ == "__main__":
    main()
