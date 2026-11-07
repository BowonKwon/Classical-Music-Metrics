"""Seoul Phil x NY Phil numbers from the raw archives, and an unpublished draft of the orchestra page.

  python src/proto_orchestras.py   ->  data/derived/orch_seoul_vs_nyphil.csv, orch_seoul_vs_nyphil_summary.json
                                       proto/orchestras.html (ko), proto/orchestras-en.html (en)

Needs data/raw (NY Phil complete.json) and seoulphil_works.csv (seoulphil_attrib.py). The page itself lives in
orchestra_pages.py, which the site build uses.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from build_site import CSS, JS  # noqa: E402
import repertoire_metrics as rm  # noqa: E402
from orchestra_pages import GCSS, T, load, render  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D, ALI, RAW = ROOT / "data/derived", ROOT / "data/aliases", ROOT / "data/raw"
SEED, DRAWS = 0, 500

UNATT = [  # rough classes of unattributed Seoul titles, for the limits note (Codex B-extra: claim was unquantified)
    ("premiere", r"premi[eè]re|commission|new work|초연|world premiere"),
    ("generic", r"^(?:(?:violin|viola|cello|piano|flute|clarinet|trumpet|horn|timpani|oboe|harp|sheng|double bass|guitar)\s+)?(?:concerto|symphony|sonata|sonatine|sinfonia|sinfonietta|overture|divertimento|passacaglia|romance|serenade|suite|quartet|quintet|sextet|septet|octet|trio)(?:\s+(?:for\s+[a-z ,&]+|no\.?\s*\d+|in\s+[a-g](?:[- ](?:flat|sharp))?\s+(?:major|minor)|op\.\s*\d+[\w.,\s]*))*\s*$"),
]


def seoul_vs_nyphil() -> tuple[pd.DataFrame, dict]:
    """Same computation as seoulphil_compare.py, saved for the page."""
    df = rm.apply_aliases(rm.load_entries(RAW), ALI / "nyphil_composers.csv")
    yr = pd.to_numeric(df["first_date"].str[:4], errors="coerce")
    df = df[yr.between(2009, 2025)]  # calendar years, same as Seoul (Codex B17: seasons 2009-10..2025-26 ran into 2026)
    pall = rm.to_pairs(df)
    pall = pall[pall["sub"] > 0]
    excluded = pall[pall.flag != "person"].groupby("flag")["sub"].sum().astype(int).to_dict()
    p = pall[pall.flag == "person"].copy()
    ny = p.groupby("composer")["sub"].sum()
    w = pd.read_csv(D / "seoulphil_works.csv")
    allsp = w[(w.type_ko == "정기공연") & w.date.str[:4].astype(int).between(2009, 2025)].copy()
    sp = allsp[allsp.composer.notna()]
    spv = sp.groupby("composer").size().astype(float)
    N = len(allsp)

    def sh(v):
        v = v[v > 0]
        return v / v.sum()
    t = pd.concat([sh(spv).rename("seoul_share"), sh(ny).rename("nyphil_sub_share"), spv.rename("seoul_titles"), ny.rename("nyphil_sub_u1")], axis=1).fillna(0)
    cos = float(t.seoul_share @ t.nyphil_sub_share / np.sqrt((t.seoul_share ** 2).sum() * (t.nyphil_sub_share ** 2).sum()))
    top_hi = float(sh(spv).sort_values(ascending=False).head(10).sum())
    top_lo = float(spv.sort_values(ascending=False).head(10).sum() / N)
    pool = np.repeat(ny.index.to_numpy(), ny.round().astype(int).to_numpy())
    rng = np.random.default_rng(SEED)
    vals = []
    for _ in range(DRAWS):
        _, c = np.unique(rng.choice(pool, N, replace=False), return_counts=True)
        vals.append(np.sort(c)[::-1][:10].sum() / N)
    # robustness: drop 2020-21, when the Seoul data carry cancelled and changed concerts (Codex audit 41: F052, F057)
    yrs = allsp.date.str[:4].astype(int)
    a2 = allsp[~yrs.isin([2020, 2021])]
    n2 = len(a2)
    lo2 = float(a2[a2.composer.notna()].groupby("composer").size().sort_values(ascending=False).head(10).sum() / n2)
    rng2 = np.random.default_rng(SEED)
    v2 = []
    for _ in range(DRAWS):
        _, c = np.unique(rng2.choice(pool, n2, replace=False), return_counts=True)
        v2.append(np.sort(c)[::-1][:10].sum() / n2)
    wd = pd.read_csv(ALI / "composer_wikidata.csv").drop_duplicates("composer").set_index("composer")

    def alive(c, y):
        if not isinstance(c, str) or c not in wd.index or pd.isna(wd.at[c, "birth_year"]):
            return np.nan
        b, d_ = wd.at[c, "birth_year"], wd.at[c, "death_year"]
        return float(b <= y and (pd.isna(d_) or d_ >= y))
    allsp["alive"] = [alive(c, int(d[:4])) for c, d in zip(allsp.composer, allsp.date)]
    un = allsp[allsp.composer.isna()].title.str.replace(r" \[part \d+\]$", "", regex=True).str.strip()
    cls = pd.Series("other", index=un.index)
    for nm_, rx in reversed(UNATT):
        cls[un.str.contains(rx, case=False, regex=True)] = nm_
    p["alive"] = [alive(c, y) for c, y in zip(p.composer, p.season_start)]
    q = p[p.alive.notna()]
    summ = {
        "window": "2009-2025", "seoul_titles": N, "seoul_attributed": int(len(sp)), "seoul_coverage": round(len(sp) / N, 4),
        "nyphil_sub_u1": int(ny.sum()), "cosine": round(cos, 4),
        "seoul_top10_lo": round(top_lo, 4), "seoul_top10_attributed_only": round(top_hi, 4),
        "seoul_top10_max": round(float((spv.sort_values(ascending=False).head(10).sum() + (N - len(sp))) / N), 4),
        "seoul_unattributed": int(N - len(sp)), "seoul_undated_attributed": int((allsp.composer.notna() & allsp.alive.isna()).sum()),
        "seoul_unattributed_classes": cls.value_counts().to_dict(), "nyphil_excluded_by_flag": excluded,
        "window_rule": "Seoul: concert date 2009-2025; NY Phil: programmes whose first concert is dated 2009-2025",
        "nyphil_top10_rarefied_mean": round(float(np.mean(vals)), 4),
        "nyphil_top10_rarefied_95": [round(float(x), 4) for x in np.percentile(vals, [2.5, 97.5])],
        "seoul_living_lo": round(float(allsp.alive.sum() / N), 4),
        "seoul_living_hi": round(float((allsp.alive.sum() + allsp.alive.isna().sum()) / N), 4),
        "nyphil_living": round(float((q.alive * q["sub"]).sum() / q["sub"].sum()), 4),
        "nyphil_living_dated_coverage": round(float(q["sub"].sum() / p["sub"].sum()), 4),
        "by_method": allsp.method.value_counts().to_dict(), "seed": SEED, "draws": DRAWS, "excl_2020_21": {"seoul_titles": n2, "seoul_top10_lo": round(lo2, 4), "nyphil_top10_hi": round(float(np.percentile(v2, 97.5)), 4)}, "nyphil_window_concert_dates": [str(df.first_date.min()), str(df.last_date.max())],
    }
    t = t.sort_values("seoul_share", ascending=False).reset_index().rename(columns={"index": "composer"})
    return t, summ


def page(lang: str, body: str) -> str:
    k = lang == "ko"
    title = T[lang]["title"] + T[lang]["draft"]
    return f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600&display=swap" rel="stylesheet">
<script>(function(){{var q=new URLSearchParams(location.search).get("theme");if(q==="light"||q==="dark"){{localStorage.setItem("cmm-theme",q)}}var v=localStorage.getItem("cmm-theme");if(v)document.documentElement.setAttribute("data-theme",v)}})();</script>
<style>{CSS}{GCSS}</style></head><body><header><span class="brand">{T[lang]['brand']}</span><div class="right"><a href="{'orchestras-en.html' if k else 'orchestras.html'}">{'English' if k else '한국어'}</a> <button id="theme" class="theme" type="button">◑</button></div></header><main>{body}</main><script>{JS}</script></body></html>"""


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sv, s = seoul_vs_nyphil()
    sv.to_csv(D / "orch_seoul_vs_nyphil.csv", index=False, encoding="utf-8", lineterminator="\n")
    (D / "orch_seoul_vs_nyphil_summary.json").write_text(json.dumps(s, ensure_ascii=False, indent=1), encoding="utf-8")
    out = ROOT / "proto"
    out.mkdir(exist_ok=True)
    for lang, fn in (("ko", "orchestras.html"), ("en", "orchestras-en.html")):
        (out / fn).write_text(page(lang, render(lang, *load(), draft=True)), encoding="utf-8")
        print("wrote proto/" + fn)
    print(json.dumps(s, ensure_ascii=False))


if __name__ == "__main__":
    main()
