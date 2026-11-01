"""Repertoire metrics from the New York Philharmonic Performance History
(github.com/nyphilarchive/PerformanceHistory, CC0).

Counting units (each multiplied by the number of concerts the program was given):
  U0  one work entry on one program (the 1.0 unit). Two excerpts from the same
      work on one program count twice.
  U1  one (program, work) pair: all entries of a work on a program count once.
      Default unit from 1.1.
  U2  U1 restricted to complete performances: none of the work's entries on that
      program names a movement or excerpt.
A "subscription" series repeats U1 counting only concerts whose event type is
"Subscription Season". Intermissions and entries without a composer are dropped.

Composer names are the archive's own authority strings. data/aliases/nyphil_composers.csv
flags strings that are not a single composer (traditional, anthem, unattributed,
non_work, multiple). Flagged strings stay in every denominator; they are not
counted as composers, and each flag is one bucket in the concentration index.

If data/aliases/composer_wikidata.csv exists, its birth and death years give
repertoire age and the living-composer share.

Outputs (data/derived/):
  nyphil_composer_season.csv    season x composer: U0/U1/U2/subscription counts, shares
  nyphil_season_summary.csv     season: totals, composers, Bach/Beethoven/Mozart shares,
                                HHI, top-10 share, excerpt share, living share, repertoire
                                age (U1, with U0 columns kept for comparison with 1.0)
  nyphil_composer_summary.csv   composer: totals, excerpt share, ranks, career span, peak
  nyphil_decade_top.csv         decade x rank (top 25 by U1)
  nyphil_canon_turnover.csv     decade: overlap of top-10/top-25 with the previous decade
  nyphil_work_frequency_all_top300.csv  works of all composers ranked by U1
  nyphil_work_frequency.csv     Bach, Beethoven and Mozart works ranked by U1
  nyphil_work_frequency_top50_composers.csv  15 most performed works of each top-50 composer
  nyphil_orchestra_programs.csv programs by ensemble name
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

FOCUS = {
    "bach": "Bach, Johann Sebastian",
    "beethoven": "Beethoven, Ludwig van",
    "mozart": "Mozart, Wolfgang Amadeus",
}
SUBSCRIPTION = "Subscription Season"


def norm_composer(name: str) -> str:
    return re.sub(r"\s+", " ", name or "").strip()


def load_entries(raw: Path) -> pd.DataFrame:
    data = json.load(open(raw / "PerformanceHistory" / "Programs" / "json" / "complete.json", encoding="utf-8"))
    rows = []
    for p in data["programs"]:
        concerts = p.get("concerts", [])
        n_concerts = max(len(concerts), 1)
        n_sub = sum(1 for c in concerts if c.get("eventType") == SUBSCRIPTION)
        season = p.get("season", "")
        dates = [c.get("Date", "")[:10] for c in concerts]
        for w in p.get("works", []):
            comp = norm_composer(w.get("composerName", ""))
            if not comp or w.get("interval"):
                continue
            rows.append(
                {
                    "season": season,
                    "season_start": int(season[:4]) if season[:4].isdigit() else None,
                    "first_date": min(dates) if dates else "",
                    "last_date": max(dates) if dates else "",
                    "program_id": p.get("programID"),
                    "n_concerts": n_concerts,
                    "n_sub": n_sub,
                    "orchestra": p.get("orchestra"),
                    "raw_composer": comp,
                    "work_id": str(w.get("ID", "")).split("*")[0],
                    "work_title": w.get("workTitle", ""),
                    "has_movement": bool(w.get("movement")),
                }
            )
    return pd.DataFrame(rows)


def apply_aliases(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    al = pd.read_csv(path, dtype=str)
    canon = dict(zip(al["raw_name"], al["canonical"]))
    flag = dict(zip(al["raw_name"], al["flag"]))
    df["composer"] = df["raw_composer"].map(lambda x: canon.get(x, x))
    df["flag"] = df["raw_composer"].map(lambda x: flag.get(x, "person"))
    return df


def to_pairs(df: pd.DataFrame) -> pd.DataFrame:
    """One row per (program, work): the U1 unit. complete = no entry names a movement."""
    g = df.groupby(["program_id", "work_id"], sort=False)
    pairs = g.agg(
        season=("season", "first"),
        season_start=("season_start", "first"),
        n_concerts=("n_concerts", "first"),
        n_sub=("n_sub", "first"),
        composer=("composer", "first"),
        flag=("flag", "first"),
        work_title=("work_title", "first"),
        any_movement=("has_movement", "any"),
        n_entries=("has_movement", "size"),
    ).reset_index()
    pairs["u1"] = pairs["n_concerts"]
    pairs["u2"] = np.where(pairs["any_movement"], 0, pairs["n_concerts"])
    pairs["u0"] = pairs["n_concerts"] * pairs["n_entries"]
    pairs["sub"] = pairs["n_sub"]
    return pairs


def bucket(composer: pd.Series, flag: pd.Series) -> np.ndarray:
    """Entity for the concentration index: the composer, or one bucket per flag."""
    return np.where(flag == "person", composer, "[" + flag + "]")


def season_table(pairs: pd.DataFrame, col: str) -> pd.DataFrame:
    p = pairs[pairs[col] > 0]
    cs = p.groupby(["season", "season_start", "composer", "flag"])[col].sum().rename("perf").reset_index()
    cs["share"] = cs["perf"] / cs.groupby("season")["perf"].transform("sum")
    return cs


def concentration(cs: pd.DataFrame) -> pd.DataFrame:
    """Per season: HHI over persons + flag buckets, top-10 person share, distinct persons, focus shares."""
    cs = cs.assign(entity=bucket(cs["composer"], cs["flag"]))
    ent = cs.groupby(["season", "entity"])["share"].sum().reset_index()
    hhi = ent.groupby("season")["share"].apply(lambda s: float((s ** 2).sum())).rename("hhi")
    persons = cs[cs["flag"] == "person"]
    distinct = persons.groupby("season")["composer"].nunique().rename("distinct_composers")
    top10 = persons.groupby("season")["share"].apply(lambda s: float(s.nlargest(10).sum())).rename("top10_share")
    top = persons.sort_values(["perf", "composer"], ascending=[False, True]).groupby("season")["composer"].first().rename("top_composer")
    out = pd.concat([hhi, distinct, top10, top], axis=1)
    for k, name in FOCUS.items():
        out[f"{k}_share"] = cs[cs["composer"] == name].groupby("season")["share"].sum()
    out[[f"{k}_share" for k in FOCUS]] = out[[f"{k}_share" for k in FOCUS]].fillna(0.0)
    return out


def weighted_median(values: np.ndarray, weights: np.ndarray) -> float:
    if len(values) == 0 or weights.sum() == 0:
        return float("nan")
    o = np.argsort(values, kind="stable")
    v, w = values[o], weights[o]
    c = np.cumsum(w)
    return float(v[np.searchsorted(c, c[-1] / 2.0)])


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/derived")
    ap.add_argument("--aliases", default="data/aliases")
    a = ap.parse_args()
    raw, out, aldir = Path(a.raw), Path(a.out), Path(a.aliases)
    out.mkdir(parents=True, exist_ok=True)

    df = apply_aliases(load_entries(raw), aldir / "nyphil_composers.csv")
    snapshot = df["last_date"].max()
    pairs = to_pairs(df)

    # ---------------- season x composer
    u1 = season_table(pairs, "u1")
    wide = u1.rename(columns={"perf": "perf_u1", "share": "share_u1"})
    for col in ("u0", "u2", "sub"):
        t = season_table(pairs, col).rename(columns={"perf": f"perf_{col}", "share": f"share_{col}"})
        wide = wide.merge(t, on=["season", "season_start", "composer", "flag"], how="outer")
    for c in [c for c in wide.columns if c.startswith(("perf_", "share_"))]:
        wide[c] = wide[c].fillna(0)
    wide = wide.sort_values(["season_start", "perf_u1"], ascending=[True, False])
    wide.to_csv(out / "nyphil_composer_season.csv", index=False, encoding="utf-8")

    # ---------------- season summary
    seasons = pairs.groupby(["season", "season_start"]).agg(
        n_programs=("program_id", "nunique"),
        work_performances=("u1", "sum"),
        work_performances_u0=("u0", "sum"),
        complete_performances=("u2", "sum"),
        subscription_performances=("sub", "sum"),
    ).reset_index().set_index("season")
    seasons["excerpt_share"] = 1 - seasons["complete_performances"] / seasons["work_performances"]
    seasons = seasons.join(concentration(u1))
    seasons = seasons.join(concentration(season_table(pairs, "u0")).add_suffix("_u0"))
    cs_sub = concentration(season_table(pairs, "sub"))
    seasons = seasons.join(cs_sub[["hhi", "distinct_composers", "top10_share"] + [f"{k}_share" for k in FOCUS]].add_suffix("_sub"))
    # 1.0 definition reproduced exactly for continuity: every composer string is a composer
    e0 = df.groupby(["season", "raw_composer"])["n_concerts"].sum().rename("p").reset_index()
    e0["s"] = e0["p"] / e0.groupby("season")["p"].transform("sum")
    seasons["hhi_v10"] = e0.groupby("season")["s"].apply(lambda s: float((s ** 2).sum()))
    seasons["distinct_composers_v10"] = e0.groupby("season")["raw_composer"].nunique()
    for k, name in FOCUS.items():
        seasons[f"{k}_share_v10"] = e0[e0["raw_composer"].str.startswith(name)].groupby("season")["s"].sum()
        seasons[f"{k}_share_v10"] = seasons[f"{k}_share_v10"].fillna(0.0)
    end = pd.to_datetime(seasons["season_start"].astype(int).astype(str) + "-08-31") + pd.DateOffset(years=1)
    seasons["season_complete"] = end <= pd.Timestamp(snapshot)

    # ---------------- composer dates (optional): repertoire age, living share
    wd_path = aldir / "composer_wikidata.csv"
    wd = None
    if wd_path.exists():
        wd = pd.read_csv(wd_path, dtype={"composer": str})
        ok = wd[wd["status"].isin(["ok", "ok_manual"])][["composer", "birth_year", "death_year"]]
        pp = pairs[pairs["flag"] == "person"].merge(ok, on="composer", how="left")
        rows = []
        for s, g in pp.groupby("season"):
            k = g[g["birth_year"].notna()]
            ss = int(g["season_start"].iloc[0])
            alive = (k["death_year"].isna() | (k["death_year"] > ss)).to_numpy()
            age = np.where(alive, 0.0, ss - k["death_year"].fillna(ss).to_numpy(float))
            w = k["u1"].to_numpy(float)
            rows.append(
                {
                    "season": s,
                    "dated_coverage": k["u1"].sum() / g["u1"].sum() if g["u1"].sum() else np.nan,
                    "living_share": float(w[alive].sum() / w.sum()) if w.sum() else np.nan,
                    # bounds over all person performances: undated composers all dead / all living
                    "living_share_low": float(w[alive].sum() / g["u1"].sum()) if g["u1"].sum() else np.nan,
                    "living_share_high": float((w[alive].sum() + g["u1"].sum() - w.sum()) / g["u1"].sum()) if g["u1"].sum() else np.nan,
                    "repertoire_age_median": weighted_median(age, w),
                }
            )
        seasons = seasons.join(pd.DataFrame(rows).set_index("season"))
    seasons = seasons.reset_index().sort_values("season_start")
    seasons.to_csv(out / "nyphil_season_summary.csv", index=False, encoding="utf-8")

    # ---------------- composer summary (career curve, excerpt share, ranks)
    comp = pairs.groupby(["composer", "flag"]).agg(
        perf_u0=("u0", "sum"), perf_u1=("u1", "sum"), perf_u2=("u2", "sum"), perf_sub=("sub", "sum"),
        n_programs=("program_id", "nunique"), n_works=("work_id", "nunique"),
        first_season=("season", "min"), last_season=("season", "max"), n_seasons=("season", "nunique"),
    ).reset_index()
    comp["excerpt_share"] = 1 - comp["perf_u2"] / comp["perf_u1"]
    persons = comp["flag"] == "person"
    for col in ("u0", "u1", "u2"):
        comp[f"rank_{col}"] = np.nan
        comp.loc[persons, f"rank_{col}"] = comp.loc[persons, f"perf_{col}"].rank(ascending=False, method="min")
    peak = u1[u1["flag"] == "person"].sort_values(["share", "season"], ascending=[False, True]).groupby("composer").first()
    comp = comp.merge(peak[["season", "share"]].rename(columns={"season": "peak_season", "share": "peak_share"}), left_on="composer", right_index=True, how="left")
    if wd is not None:
        comp = comp.merge(wd[["composer", "wikidata_qid", "birth_year", "death_year", "status"]].rename(columns={"status": "wikidata_status"}), on="composer", how="left")
    comp = comp.sort_values(["perf_u1", "composer"], ascending=[False, True])
    comp.to_csv(out / "nyphil_composer_summary.csv", index=False, encoding="utf-8")

    # ---------------- decade top 25 and canon turnover (persons, U1)
    pairs["decade"] = (pairs["season_start"] // 10 * 10).astype(int)
    pp = pairs[pairs["flag"] == "person"]
    dec = pp.groupby(["decade", "composer"])["u1"].sum().rename("perf_u1").reset_index()
    dec["share"] = dec["perf_u1"] / pairs.groupby("decade")["u1"].sum().reindex(dec["decade"]).values
    dec = dec.sort_values(["decade", "perf_u1", "composer"], ascending=[True, False, True])
    dec["rank"] = dec.groupby("decade").cumcount() + 1
    top = dec[dec["rank"] <= 25]
    top.to_csv(out / "nyphil_decade_top.csv", index=False, encoding="utf-8")
    trows, prev = [], None
    seasons_per_decade = pairs.groupby("decade")["season"].nunique()
    for d_, g in top.groupby("decade"):
        cur = {k: set(g.loc[g["rank"] <= k, "composer"]) for k in (10, 25)}
        row = {"decade": int(d_), "n_seasons": int(seasons_per_decade[d_])}
        for k in (10, 25):
            if prev is None:
                row[f"jaccard_top{k}"] = np.nan
                row[f"new_in_top{k}"] = ""
            else:
                row[f"jaccard_top{k}"] = len(cur[k] & prev[k]) / len(cur[k] | prev[k])
                row[f"new_in_top{k}"] = "; ".join(sorted(cur[k] - prev[k]))
        trows.append(row)
        prev = cur
    pd.DataFrame(trows).to_csv(out / "nyphil_canon_turnover.csv", index=False, encoding="utf-8")

    # ---------------- works
    wf = pairs.groupby(["composer", "work_id"]).agg(
        work_title=("work_title", "first"),
        performances=("u1", "sum"), performances_u0=("u0", "sum"), complete_performances=("u2", "sum"),
        programs=("program_id", "nunique"), first_season=("season", "min"), last_season=("season", "max"),
    ).reset_index().sort_values(["performances", "work_id"], ascending=[False, True])
    wf["rank"] = range(1, len(wf) + 1)
    wf.head(300).to_csv(out / "nyphil_work_frequency_all_top300.csv", index=False, encoding="utf-8")
    focus = wf[wf["composer"].isin(FOCUS.values())].rename(columns={"rank": "rank_all_composers"})
    focus.to_csv(out / "nyphil_work_frequency.csv", index=False, encoding="utf-8")
    top50 = comp.loc[(comp["flag"] == "person") & (comp["rank_u1"] <= 50), "composer"]
    w50 = wf[wf["composer"].isin(top50)].copy()
    w50["rank_in_composer"] = w50.groupby("composer").cumcount() + 1
    w50[w50["rank_in_composer"] <= 15].to_csv(out / "nyphil_work_frequency_top50_composers.csv", index=False, encoding="utf-8")
    df.groupby("orchestra")["program_id"].nunique().sort_values(ascending=False).rename("programs").reset_index().to_csv(out / "nyphil_orchestra_programs.csv", index=False, encoding="utf-8")

    print("snapshot", snapshot, "programs", df["program_id"].nunique(), "seasons", df["season"].nunique())
    print("U0", int(pairs["u0"].sum()), "U1", int(pairs["u1"].sum()), "U2", int(pairs["u2"].sum()), "sub", int(pairs["sub"].sum()))
    print("composer strings", df["composer"].nunique(), "persons", int(persons.sum()))
    print(comp.head(12)[["composer", "perf_u0", "perf_u1", "perf_u2", "excerpt_share", "rank_u1", "rank_u2"]].to_string())


if __name__ == "__main__":
    main()
