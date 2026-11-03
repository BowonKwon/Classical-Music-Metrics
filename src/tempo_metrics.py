"""Beethoven symphony tempo metrics from the bmetr data package
(Martín-Castro & Ucar 2020, PLOS ONE 15(12): e0243616; MIT license).

Two transparent measures are computed from the authors' raw tables, without
re-running their audio pipeline:

1. duration_ratio  — performed track length divided by the theoretical
   duration implied by Beethoven's metronome marks. Because we do not know
   which repeats each conductor took, two bounds are given:
   ratio_no_repeats (theoretical duration without repeats) and
   ratio_with_repeats. A ratio above 1 means slower than the marks.
   Theoretical duration per section (minutes) = (bar.tot - bar.1) * beat / mark,
   plus bar.rep * beat / mark with repeats (formula from help(sym.data)).

2. coda_tempo_diff — the authors' single tempo estimate sampled at the end of
   each track (sym.sample) minus the metronome mark of the same section.
   The extraction algorithm sometimes returns a multiple or fraction of the
   true tempo ("harmonics"); when tempo/mark falls outside [0.6, 1.4] we
   rectify by the factor in {1/3, 1/2, 2/3, 3/2, 2, 3} that brings the ratio
   closest to 1, and flag the row.

3. tempo trend by recording year (1.4) — coda_tempo_diff_bpm (symphonies 1-8, usable rows) against
   the recording year, in bpm per decade. Recording year = midpoint of the years written in the
   `date` column (the recording dates; `year` is the album's release year and is not used).
   Each conductor contributes one cycle, so conductor and recording year cannot be separated:
   the slope describes how tempo and recording year vary together across 36 cycles, not an
   effect of the year. Rows of beethoven_symphony_tempo_trend.csv:
     movement_fe        within-movement slope (one intercept per symphony movement, so marks
                        cancel), cluster-robust SE by conductor (CR1), 95% interval from
                        2,000 conductor-bootstrap resamples (seed fixed)
     movement_fe_start  the same with the first recording year instead of the midpoint
     movement_fe_ptype  the same, also with one intercept per performance type
     conductor_median   OLS of each conductor's median difference on the year (n = 36),
                        classical SE, bootstrap interval over conductors

Usage: python src/tempo_metrics.py --raw data/raw --out data/derived
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadr

ROOT = Path(__file__).resolve().parent.parent  # repository root; default paths do not depend on the working directory

HARMONICS = [1 / 3, 1 / 2, 2 / 3, 3 / 2, 2, 3]
BOOT_B, BOOT_SEED = 2000, 20261102


def recording_years(date) -> tuple[float, float, float]:
    """(first, last, midpoint) of the four-digit years written in a bmetr `date` cell ('1972- 1975' -> 1972, 1975, 1973.5)."""
    ys = [int(y) for y in re.findall(r"\d{4}", "" if date is None else str(date))]
    if not ys:
        return (math.nan, math.nan, math.nan)
    return (float(min(ys)), float(max(ys)), (min(ys) + max(ys)) / 2)


def ols_cluster(X: np.ndarray, y: np.ndarray, groups: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """OLS coefficients and CR1 cluster-robust standard errors.

    V = c (X'X)^-1 [sum_g (X_g' e_g)(X_g' e_g)'] (X'X)^-1,  c = G/(G-1) * (N-1)/(N-K)."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    n, k = X.shape
    xtx_inv = np.linalg.pinv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    e = y - X @ beta
    meat = np.zeros((k, k))
    ug = pd.unique(groups)
    for g in ug:
        sg = X[groups == g].T @ e[groups == g]
        meat += np.outer(sg, sg)
    G = len(ug)
    c = G / (G - 1) * (n - 1) / (n - k) if G > 1 and n > k else math.nan
    dv = np.diag(c * xtx_inv @ meat @ xtx_inv)
    # a bootstrap resample can repeat one conductor so often that X is rank-deficient: SE undefined there
    return beta, np.where(dv >= 0, np.sqrt(np.abs(dv)), np.nan)


def fe_design(df: pd.DataFrame, xcol: str, fe_cols: list[str]) -> np.ndarray:
    """[x, one dummy per level of the first FE column, dummies minus one level for the others]."""
    parts = [df[[xcol]].to_numpy(float)]
    for i, c in enumerate(fe_cols):
        d = pd.get_dummies(df[c].astype(str), dtype=float)
        parts.append(d.to_numpy() if i == 0 else d.iloc[:, 1:].to_numpy())
    return np.hstack(parts)


def ols_slope(x, y) -> tuple[float, float]:
    """Simple regression y = a + b x: slope b and its classical SE sqrt(s^2 / Sxx), s^2 = SSR / (n - 2)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    xd = x - x.mean()
    sxx = float((xd ** 2).sum())
    b = float((xd * (y - y.mean())).sum() / sxx)
    a = y.mean() - b * x.mean()
    ssr = float(((y - a - b * x) ** 2).sum())
    return b, math.sqrt(ssr / (len(x) - 2) / sxx) if len(x) > 2 else math.nan


def tempo_trend(s: pd.DataFrame, rec: pd.DataFrame, boot_b: int = BOOT_B, seed: int = BOOT_SEED) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Trend of coda_tempo_diff_bpm with recording year (symphonies 1-8, usable rows). Returns (trend rows, per-conductor table)."""
    yrs = rec[["conductor", "date"]].copy()
    yrs[["rec_year_first", "rec_year_last", "rec_year_mid"]] = [recording_years(v) for v in yrs["date"]]
    ok = s[~s["unusable"] & (s["symphony"] != 9)].drop(columns=["date"], errors="ignore").merge(yrs, on="conductor")
    ok["mv"] = ok["symphony"].astype(int).astype(str) + "/" + ok["movement"].astype(int).astype(str)
    cond = ok.groupby(["conductor", "ptype", "date", "rec_year_first", "rec_year_last", "rec_year_mid"], sort=True).agg(
        n_movements=("coda_tempo_diff_bpm", "size"), median_diff_bpm=("coda_tempo_diff_bpm", "median")).reset_index()
    names = cond["conductor"].to_numpy()
    rng = np.random.default_rng(seed)
    draws = [rng.choice(len(names), len(names), replace=True) for _ in range(boot_b)]
    by_c = {c: g for c, g in ok.groupby("conductor", sort=True)}

    def fe_fit(df, xcol, fes):
        b, se = ols_cluster(fe_design(df, xcol, fes), df["coda_tempo_diff_bpm"].to_numpy(float), df["conductor"].to_numpy())
        return b[0], se[0]

    def boot(fn):
        vals = np.array([fn(idx) for idx in draws], float)
        return np.nanpercentile(vals, [2.5, 97.5])

    rows = []
    for model, xcol, fes in (("movement_fe", "rec_year_mid", ["mv"]), ("movement_fe_start", "rec_year_first", ["mv"]),
                             ("movement_fe_ptype", "rec_year_mid", ["mv", "ptype"])):
        b, se = fe_fit(ok, xcol, fes)

        def one(idx, xcol=xcol, fes=fes):
            df = pd.concat([by_c[names[i]].assign(conductor=f"{names[i]}#{j}") for j, i in enumerate(idx)], ignore_index=True)
            return fe_fit(df, xcol, fes)[0] if df[xcol].nunique() > 1 else math.nan
        lo, hi = boot(one)
        rows.append(dict(model=model, year=xcol, n_obs=len(ok), n_conductors=ok["conductor"].nunique(), slope_bpm_per_decade=10 * b,
                         se_bpm_per_decade=10 * se, ci95_low=10 * lo, ci95_high=10 * hi, se_kind="cluster CR1 (conductor)",
                         year_min=ok[xcol].min(), year_max=ok[xcol].max()))
    b, se = ols_slope(cond["rec_year_mid"], cond["median_diff_bpm"])
    x, y = cond["rec_year_mid"].to_numpy(float), cond["median_diff_bpm"].to_numpy(float)
    lo, hi = boot(lambda idx: ols_slope(x[idx], y[idx])[0] if len(set(x[idx])) > 1 else math.nan)
    rows.append(dict(model="conductor_median", year="rec_year_mid", n_obs=len(cond), n_conductors=len(cond), slope_bpm_per_decade=10 * b,
                     se_bpm_per_decade=10 * se, ci95_low=10 * lo, ci95_high=10 * hi, se_kind="classical OLS",
                     year_min=cond["rec_year_mid"].min(), year_max=cond["rec_year_mid"].max()))
    return pd.DataFrame(rows), cond


def load(raw: Path, name: str) -> pd.DataFrame:
    r = pyreadr.read_r(str(raw / "bmetr" / "data" / f"{name}.rda"))
    df = next(iter(r.values()))
    for c in df.select_dtypes("category").columns:
        df[c] = df[c].astype(str)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data/raw"))
    ap.add_argument("--out", default=str(ROOT / "data/derived"))
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    marks = load(raw, "sym.marks")
    rec = load(raw, "sym.recordings")
    dur = load(raw, "sym.duration")
    samp = load(raw, "sym.sample")

    # --- theoretical durations per movement (seconds)
    marks["theo_no_rep_s"] = (marks["bar.tot"] - marks["bar.1"]) * marks["beat"] / marks["mark"] * 60
    marks["theo_with_rep_s"] = marks["theo_no_rep_s"] + marks["bar.rep"] * marks["beat"] / marks["mark"] * 60
    theo = marks.groupby(["symphony", "movement"]).agg(
        theo_no_rep_s=("theo_no_rep_s", "sum"),
        theo_with_rep_s=("theo_with_rep_s", "sum"),
        n_sections=("section", "nunique"),
        main_mark=("mark", "first"),
        main_character=("character", "first"),
    ).reset_index()

    d = dur.merge(theo, on=["symphony", "movement"]).merge(rec[["conductor", "orchestra", "date", "year", "ptype"]], on="conductor")
    d["ratio_no_repeats"] = d["duration"] / d["theo_no_rep_s"]
    d["ratio_with_repeats"] = d["duration"] / d["theo_with_rep_s"]
    d["recording_year_start"] = d["date"].str.extract(r"(\d{4})").astype(float)

    # --- coda sample vs mark of the sampled section
    s = samp.merge(marks[["symphony", "movement", "section", "mark", "character", "tsig"]],
                   on=["symphony", "movement", "section"], how="left")
    s["ratio_raw"] = s["tempo"] / s["mark"]
    s["rectified"] = False
    s["tempo_rectified"] = s["tempo"]
    bad = (s["ratio_raw"] < 0.6) | (s["ratio_raw"] > 1.4)
    for i in s.index[bad & s["mark"].notna() & (s["tempo"] > 0)]:
        r = s.at[i, "ratio_raw"]
        best = min(HARMONICS, key=lambda h: abs(r / h - 1))
        if 0.6 <= r / best <= 1.4:
            s.at[i, "tempo_rectified"] = s.at[i, "tempo"] / best
            s.at[i, "rectified"] = True
    s["coda_tempo_diff_bpm"] = s["tempo_rectified"] - s["mark"]
    s["coda_tempo_ratio"] = s["tempo_rectified"] / s["mark"]
    s["unusable"] = (s["tempo"] <= 0) | s["mark"].isna() | ((s["coda_tempo_ratio"] < 0.6) | (s["coda_tempo_ratio"] > 1.4))
    s = s.merge(rec[["conductor", "orchestra", "date", "year", "ptype"]], on="conductor")
    s["recording_year_start"] = s["date"].str.extract(r"(\d{4})").astype(float)

    d.to_csv(out / "beethoven_symphony_duration_ratio.csv", index=False, encoding="utf-8", lineterminator="\n")
    s.to_csv(out / "beethoven_symphony_coda_tempo.csv", index=False, encoding="utf-8", lineterminator="\n")
    marks.to_csv(out / "beethoven_symphony_marks.csv", index=False, encoding="utf-8", lineterminator="\n")
    rec.to_csv(out / "beethoven_symphony_recordings.csv", index=False, encoding="utf-8", lineterminator="\n")

    # --- summaries
    mv = d.groupby(["symphony", "movement", "main_mark", "main_character"]).agg(
        n=("conductor", "size"),
        duration_median_s=("duration", "median"),
        ratio_no_rep_median=("ratio_no_repeats", "median"),
        ratio_with_rep_median=("ratio_with_repeats", "median"),
    ).reset_index()
    cond = s[~s["unusable"] & (s["symphony"] != 9)].groupby(["conductor", "ptype", "date"]).agg(
        n_movements=("coda_tempo_diff_bpm", "size"),
        median_diff_bpm=("coda_tempo_diff_bpm", "median"),
        q1_diff_bpm=("coda_tempo_diff_bpm", lambda x: x.quantile(0.25)),
        q3_diff_bpm=("coda_tempo_diff_bpm", lambda x: x.quantile(0.75)),
        median_ratio=("coda_tempo_ratio", "median"),
        n_rectified=("rectified", "sum"),
    ).reset_index().sort_values("median_diff_bpm")
    mv.to_csv(out / "beethoven_symphony_movement_summary.csv", index=False, encoding="utf-8", lineterminator="\n")
    cond.to_csv(out / "beethoven_symphony_conductor_summary.csv", index=False, encoding="utf-8", lineterminator="\n")
    trend, cyear = tempo_trend(s, rec)
    trend.to_csv(out / "beethoven_symphony_tempo_trend.csv", index=False, encoding="utf-8", lineterminator="\n")
    cyear.to_csv(out / "beethoven_symphony_conductor_year.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(trend.to_string())
    print("movements", len(mv), "conductors", len(cond))
    print("coda rows", len(s), "rectified", int(s["rectified"].sum()), "unusable", int(s["unusable"].sum()))
    print(cond[["conductor", "ptype", "median_diff_bpm", "n_movements"]].to_string())
    print(s[~s.unusable & (s.symphony != 9)].groupby("ptype")["coda_tempo_diff_bpm"].describe())


if __name__ == "__main__":
    main()
