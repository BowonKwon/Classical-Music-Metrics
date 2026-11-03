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

1.4 (descriptive statistics only):
  nyphil_conductor_repertoire.csv  conductor: U1 conducted, seasons, composers, HHI, top composer,
                                Bach/Beethoven/Mozart shares, excerpt share, living share (with bounds),
                                women's share bounds (when the gender table exists)
  nyphil_new_work_survival.csv  Kaplan-Meier curve of time (seasons) from a work's first NY Phil
                                season to its first performance in a later season, by cohort
  nyphil_new_work_survival_summary.csv  per cohort: works, left-truncated works left out,
                                share re-performed within 10 seasons (1 - KM survival) with a 95% interval
  nyphil_women_share.csv        season: women composers' share of person U1 (lower bound, point among
                                composers with recorded gender, upper bound); written only when
                                data/aliases/composer_gender.csv (Wikidata P21) exists

Conductor names (data/aliases/nyphil_conductors.csv, written by --write-conductor-aliases, rules in
conductor_alias): the archive's conductorName string, normalized by
  R1 collapse white space and drop a space before a comma ("Barbirolli , John" -> "Barbirolli, John")
  R2 drop an empty name before ";" (";  Gilbert, Alan" -> "Gilbert, Alan")
  R3 several names joined by ";" -> flag multiple (kept as one bucket, not credited to either person)
  R4 "Not conducted" -> flag not_conducted, "Unknown" -> flag unknown
  R5 drop the archive's cross-reference notes "(use NNNN)" ("Rosenstock (use 5551), Milton" -> "Rosenstock, Milton")
Accent variants written in brackets ("Furtwangler [Furtwängler], Wilhelm") are the archive's own authority
form and are kept as they are; no two strings in the snapshot differ only by accents or case after R1-R5.
A work without a conductorName is bucketed as "[none recorded]".
"""
from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent  # repository root; default paths do not depend on the working directory

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
                    "raw_conductor": w.get("conductorName") or "",
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
    """One row per (program, work): the U1 unit. complete = no entry names a movement.

    Entries without a work ID are keyed by composer and title, so different works on one program are not merged."""
    df = df.copy()
    noid = df["work_id"].astype(object).fillna("").astype(str).eq("")
    df.loc[noid, "work_id"] = "noid:" + df.loc[noid, "composer"].astype(str) + "|" + df.loc[noid, "work_title"].astype(str)
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
        **({"conductor": ("conductor", "first"), "conductor_flag": ("conductor_flag", "first")} if "conductor" in df else {}),
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


# ---------------------------------------------------------------- 1.4: conductors
NONE_RECORDED = "[none recorded]"


def conductor_alias(raw: str) -> tuple[str, str, str]:
    """(canonical, flag, rules applied) for one conductorName string (rules R1-R5 in the module docstring)."""
    rules = []
    x = raw or ""
    if not x.strip():
        return NONE_RECORDED, "none_recorded", "empty"
    y = re.sub(r"\s+", " ", x).strip()
    y = re.sub(r"\s+,", ",", y)
    if y != x:
        rules.append("R1")
    z = re.sub(r"^(;\s*)+", "", y)
    if z != y:
        rules.append("R2")
    y = z
    z = re.sub(r"\s*\(use \d+\)", "", y)
    if z != y:
        rules.append("R5")
    y = z
    parts = [q.strip() for q in y.split(";") if q.strip()]
    if len(parts) > 1:
        rules.append("R3")
        return "; ".join(parts), "multiple", "+".join(rules)
    y = parts[0] if parts else ""
    if y.lower() == "not conducted":
        return "Not conducted", "not_conducted", "+".join(rules + ["R4"])
    if y.lower() == "unknown":
        return "Unknown", "unknown", "+".join(rules + ["R4"])
    return y, "person", "+".join(rules)


def conductor_alias_table(df: pd.DataFrame) -> pd.DataFrame:
    """One row per raw conductorName string: canonical form, flag, rules, number of work entries."""
    n = df.groupby("raw_conductor").size()
    rows = []
    for raw, k in n.items():
        c, f, r = conductor_alias(raw)
        rows.append({"raw_name": raw, "canonical": c, "flag": f, "rules": r, "n_entries": int(k)})
    return pd.DataFrame(rows).sort_values(["canonical", "raw_name"], kind="mergesort")


def apply_conductor_aliases(df: pd.DataFrame, path: Path | None) -> pd.DataFrame:
    """Canonical conductor per entry from the reviewed table; strings not in it fall back to the same rules."""
    table = {}
    if path is not None and path.exists():
        al = pd.read_csv(path, dtype=str, keep_default_na=False)
        table = {r.raw_name: (r.canonical, r.flag) for r in al.itertuples()}
    res = [table.get(x) or conductor_alias(x)[:2] for x in df["raw_conductor"]]
    df["conductor"] = [c for c, _ in res]
    df["conductor_flag"] = [f for _, f in res]
    return df


def conductor_repertoire(pairs: pd.DataFrame, wd: pd.DataFrame | None, gender: pd.DataFrame | None) -> pd.DataFrame:
    """Repertoire composition of the works each conductor led (U1). Descriptive only."""
    pp = pairs.copy()
    persons = pp["flag"] == "person"
    rows = []
    dated = None
    if wd is not None:
        dated = wd[wd["status"].isin(["ok", "ok_manual"])][["composer", "death_year"]]
    gmap = None if gender is None else dict(zip(gender["composer"], gender["gender"]))
    for (c, f), g in pp.groupby(["conductor", "conductor_flag"], sort=True):
        tot = g["u1"].sum()
        gp = g[g["flag"] == "person"]
        share = gp.groupby("composer")["u1"].sum()
        share = share.loc[sorted(share.index, key=lambda k: (-share[k], k))]  # ties: alphabetical
        ent = pd.Series(bucket(g["composer"], g["flag"]), index=g.index)
        e_share = g.groupby(ent)["u1"].sum() / tot
        row = {"conductor": c, "conductor_flag": f, "perf_u1": int(tot), "n_programs": g["program_id"].nunique(),
               "first_season": g["season"].min(), "last_season": g["season"].max(), "n_seasons": g["season"].nunique(),
               "distinct_composers": int(gp["composer"].nunique()), "hhi": float((e_share ** 2).sum()),
               "top_composer": share.index[0] if len(share) else "", "top_composer_share": float(share.iloc[0] / tot) if len(share) else np.nan,
               "excerpt_share": float(1 - g["u2"].sum() / tot)}
        for k, name in FOCUS.items():
            row[f"{k}_share"] = float(g.loc[g["composer"] == name, "u1"].sum() / tot)
        ptot = gp["u1"].sum()
        if dated is not None and ptot:
            k = gp.merge(dated, on="composer", how="inner")
            alive = (k["death_year"].isna() | (k["death_year"] > k["season_start"])).to_numpy()
            w = k["u1"].to_numpy(float)
            row["dated_coverage"] = float(w.sum() / ptot)
            row["living_share"] = float(w[alive].sum() / w.sum()) if w.sum() else np.nan
            row["living_share_low"] = float(w[alive].sum() / ptot)
            row["living_share_high"] = float((w[alive].sum() + ptot - w.sum()) / ptot)
        if gmap is not None and ptot:
            row.update(women_bounds(gp["composer"].map(gmap).fillna("unknown"), gp["u1"]))
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["perf_u1", "conductor"], ascending=[False, True], kind="mergesort")


# ---------------------------------------------------------------- 1.4: new-work survival
def kaplan_meier(times: np.ndarray, events: np.ndarray, z: float = 1.959963984540054) -> pd.DataFrame:
    """Kaplan-Meier survival with Greenwood variance and a log(-log) 95% interval.

    times: follow-up in seasons; events: True = re-performed at that time, False = censored then.
    Censored at t means still at risk at t (events at t are counted first)."""
    t = np.asarray(times, float)
    e = np.asarray(events, bool)
    rows, surv, gw = [], 1.0, 0.0
    for u in np.unique(t[e]):
        n = int((t >= u).sum())
        d = int(((t == u) & e).sum())
        c = int(((t == u) & ~e).sum())
        surv *= 1 - d / n
        gw += d / (n * (n - d)) if n > d else math.inf
        if 0 < surv < 1 and math.isfinite(gw):
            se = math.sqrt(gw) / abs(math.log(surv))
            lo, hi = surv ** math.exp(z * se), surv ** math.exp(-z * se)
        else:
            lo = hi = surv
        rows.append({"t": float(u), "n_risk": n, "n_event": d, "n_censor_at_t": c, "surv": surv, "surv_ci95_low": lo, "surv_ci95_high": hi})
    return pd.DataFrame(rows, columns=["t", "n_risk", "n_event", "n_censor_at_t", "surv", "surv_ci95_low", "surv_ci95_high"])


def km_at(curve: pd.DataFrame, t: float) -> tuple[float, float, float]:
    """Survival and its interval at time t (step function; 1 before the first event)."""
    c = curve[curve["t"] <= t]
    if c.empty:
        return 1.0, 1.0, 1.0
    r = c.iloc[-1]
    return float(r["surv"]), float(r["surv_ci95_low"]), float(r["surv_ci95_high"])


def work_followup(pairs: pd.DataFrame, end_season: int, first_season: int) -> pd.DataFrame:
    """Per work: first season, first later season (re-performance), follow-up and event.

    Re-performance = the work on a program in a later season than its first (another program in the
    same season belongs to the first run). Follow-up ends at end_season (the last completed season);
    later seasons are not looked at. Works first seen in first_season (the archive's first season)
    are left-truncated: what came before is unknown, so they are marked and left out of the curves."""
    p = pairs[(pairs["flag"] == "person") & (pairs["season_start"] <= end_season)]
    rows = []
    for (comp, wid), g in p.groupby(["composer", "work_id"], sort=True):
        ss = sorted(set(int(x) for x in g["season_start"]))
        s0 = ss[0]
        later = [x for x in ss if x > s0]
        ev = bool(later)
        rows.append({"composer": comp, "work_id": wid, "work_title": g["work_title"].iloc[0], "first_season_start": s0,
                     "next_season_start": later[0] if ev else np.nan, "event": ev,
                     "time": (later[0] - s0) if ev else (end_season - s0), "left_truncated": s0 == first_season})
    return pd.DataFrame(rows)


SURV_YEARS = 10
COHORTS = [("all", None, None), ("1843-1899", 1843, 1899), ("1900-1949", 1900, 1949), ("1950-1999", 1950, 1999), ("2000-", 2000, None)]


def new_work_survival(pairs: pd.DataFrame, wd: pd.DataFrame | None, end_season: int, first_season: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """KM curves of time to re-performance, each by cohort of first season, for
      living_composer    works by composers alive in the work's first season (reviewed Wikidata dates:
                         death year after that season, or none)
      living_or_undated  the same plus works by composers without reviewed dates (sensitivity: most of
                         them have fewer than 10 performances and are likely living)
      all_works          every work by a person composer"""
    w = work_followup(pairs, end_season, first_season)
    sets = [("all_works", w)]
    if wd is not None:
        ok = wd[wd["status"].isin(["ok", "ok_manual"])][["composer", "birth_year", "death_year"]]
        m = w.merge(ok, on="composer", how="left")
        living = m["birth_year"].notna() & (m["death_year"].isna() | (m["death_year"] > m["first_season_start"]))
        undated = m["birth_year"].isna()  # no reviewed Wikidata dates (mostly composers with < 10 performances)
        sets[0:0] = [("living_composer", m[living]), ("living_or_undated", m[living | undated])]
    curves, summ = [], []
    for name, d in sets:
        for coh, a, b in COHORTS:
            g = d[(d["first_season_start"] >= (a or -1)) & (d["first_season_start"] <= (b or 10 ** 6))]
            used = g[~g["left_truncated"]]
            cv = kaplan_meier(used["time"].to_numpy(), used["event"].to_numpy())
            curves.append(cv.assign(set=name, cohort=coh))
            s10, lo, hi = km_at(cv, SURV_YEARS)
            full = used[(used["event"] & (used["time"] <= SURV_YEARS)) | (used["time"] >= SURV_YEARS)]
            summ.append({"set": name, "cohort": coh, "n_works": len(g), "n_left_truncated": int(g["left_truncated"].sum()),
                         "n_used": len(used), "n_reperformed": int(used["event"].sum()),
                         "reperf_10y_km": 1 - s10, "reperf_10y_ci95_low": 1 - hi, "reperf_10y_ci95_high": 1 - lo,
                         "n_full_10y_followup": len(full),
                         "reperf_10y_naive": float((full["event"] & (full["time"] <= SURV_YEARS)).mean()) if len(full) else np.nan})
    cols = ["set", "cohort", "t", "n_risk", "n_event", "n_censor_at_t", "surv", "surv_ci95_low", "surv_ci95_high"]
    return pd.concat(curves, ignore_index=True)[cols], pd.DataFrame(summ)


# ---------------------------------------------------------------- 1.4: women composers
WOMEN = {"female", "trans woman"}


def women_bounds(gender: pd.Series, weight: pd.Series) -> dict:
    """Women's share of weight. gender: 'female', 'male', 'trans woman', other P21 labels, or 'unknown'
    (no Wikidata item, or no P21 statement). low: unknown counted as not women; high: unknown counted as
    women; point: among composers with a recorded P21 value only."""
    g = gender.astype(str).to_numpy()
    w = np.asarray(weight, float)
    tot = w.sum()
    women = w[np.isin(g, list(WOMEN))].sum()
    unknown = w[g == "unknown"].sum()
    known = tot - unknown
    return {"gender_coverage": known / tot if tot else np.nan,
            "women_share_low": women / tot if tot else np.nan,
            "women_share": women / known if known else np.nan,
            "women_share_high": (women + unknown) / tot if tot else np.nan}


def women_share_by_season(pairs: pd.DataFrame, gender: pd.DataFrame) -> pd.DataFrame:
    gmap = dict(zip(gender["composer"], gender["gender"]))
    pp = pairs[pairs["flag"] == "person"]
    rows = []
    for (s, ss), g in pp.groupby(["season", "season_start"], sort=True):
        rows.append({"season": s, "season_start": ss, "person_u1": int(g["u1"].sum()),
                     **women_bounds(g["composer"].map(gmap).fillna("unknown"), g["u1"])})
    return pd.DataFrame(rows).sort_values("season_start")


def main():
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data/raw"))
    ap.add_argument("--out", default=str(ROOT / "data/derived"))
    ap.add_argument("--aliases", default=str(ROOT / "data/aliases"))
    ap.add_argument("--write-conductor-aliases", action="store_true",
                    help="(re)write data/aliases/nyphil_conductors.csv from the rules before computing")
    a = ap.parse_args()
    raw, out, aldir = Path(a.raw), Path(a.out), Path(a.aliases)
    out.mkdir(parents=True, exist_ok=True)

    df = apply_aliases(load_entries(raw), aldir / "nyphil_composers.csv")
    if a.write_conductor_aliases:
        conductor_alias_table(df).to_csv(aldir / "nyphil_conductors.csv", index=False, encoding="utf-8", lineterminator="\n")
    df = apply_conductor_aliases(df, aldir / "nyphil_conductors.csv")
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
    wide.to_csv(out / "nyphil_composer_season.csv", index=False, encoding="utf-8", lineterminator="\n")

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
    seasons.to_csv(out / "nyphil_season_summary.csv", index=False, encoding="utf-8", lineterminator="\n")

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
    comp.to_csv(out / "nyphil_composer_summary.csv", index=False, encoding="utf-8", lineterminator="\n")

    # ---------------- decade top 25 and canon turnover (persons, U1)
    pairs["decade"] = (pairs["season_start"] // 10 * 10).astype(int)
    pp = pairs[pairs["flag"] == "person"]
    dec = pp.groupby(["decade", "composer"])["u1"].sum().rename("perf_u1").reset_index()
    dec["share"] = dec["perf_u1"] / pairs.groupby("decade")["u1"].sum().reindex(dec["decade"]).values
    dec = dec.sort_values(["decade", "perf_u1", "composer"], ascending=[True, False, True])
    dec["rank"] = dec.groupby("decade").cumcount() + 1
    top = dec[dec["rank"] <= 25]
    top.to_csv(out / "nyphil_decade_top.csv", index=False, encoding="utf-8", lineterminator="\n")
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
    pd.DataFrame(trows).to_csv(out / "nyphil_canon_turnover.csv", index=False, encoding="utf-8", lineterminator="\n")

    # ---------------- works
    wf = pairs.groupby(["composer", "work_id"]).agg(
        work_title=("work_title", "first"),
        performances=("u1", "sum"), performances_u0=("u0", "sum"), complete_performances=("u2", "sum"),
        programs=("program_id", "nunique"), first_season=("season", "min"), last_season=("season", "max"),
    ).reset_index().sort_values(["performances", "work_id"], ascending=[False, True])
    wf["rank"] = range(1, len(wf) + 1)
    wf.head(300).to_csv(out / "nyphil_work_frequency_all_top300.csv", index=False, encoding="utf-8", lineterminator="\n")
    focus = wf[wf["composer"].isin(FOCUS.values())].rename(columns={"rank": "rank_all_composers"})
    focus.to_csv(out / "nyphil_work_frequency.csv", index=False, encoding="utf-8", lineterminator="\n")
    top50 = comp.loc[(comp["flag"] == "person") & (comp["rank_u1"] <= 50), "composer"]
    w50 = wf[wf["composer"].isin(top50)].copy()
    w50["rank_in_composer"] = w50.groupby("composer").cumcount() + 1
    w50[w50["rank_in_composer"] <= 15].to_csv(out / "nyphil_work_frequency_top50_composers.csv", index=False, encoding="utf-8", lineterminator="\n")
    df.groupby("orchestra")["program_id"].nunique().sort_values(ascending=False).rename("programs").reset_index().to_csv(out / "nyphil_orchestra_programs.csv", index=False, encoding="utf-8", lineterminator="\n")

    # ---------------- 1.4: conductors, new-work survival, women composers
    gpath = aldir / "composer_gender.csv"
    gender = pd.read_csv(gpath, dtype=str) if gpath.exists() else None
    conductor_repertoire(pairs, wd, gender).to_csv(out / "nyphil_conductor_repertoire.csv", index=False, encoding="utf-8", lineterminator="\n")
    done = seasons[seasons["season_complete"]]
    end_season = int(done["season_start"].max()) if len(done) else int(seasons["season_start"].max())
    curve, summ = new_work_survival(pairs, wd, end_season, int(seasons["season_start"].min()))
    curve.to_csv(out / "nyphil_new_work_survival.csv", index=False, encoding="utf-8", lineterminator="\n")
    summ.to_csv(out / "nyphil_new_work_survival_summary.csv", index=False, encoding="utf-8", lineterminator="\n")
    if gender is not None:
        women_share_by_season(pairs, gender).to_csv(out / "nyphil_women_share.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(summ.to_string())

    print("snapshot", snapshot, "programs", df["program_id"].nunique(), "seasons", df["season"].nunique())
    print("U0", int(pairs["u0"].sum()), "U1", int(pairs["u1"].sum()), "U2", int(pairs["u2"].sum()), "sub", int(pairs["sub"].sum()))
    print("composer strings", df["composer"].nunique(), "persons", int(persons.sum()))
    print(comp.head(12)[["composer", "perf_u0", "perf_u1", "perf_u2", "excerpt_share", "rank_u1", "rank_u2"]].to_string())


if __name__ == "__main__":
    main()
