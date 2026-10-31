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

Usage: python src/tempo_metrics.py --raw data/raw --out data/derived
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import pyreadr

HARMONICS = [1 / 3, 1 / 2, 2 / 3, 3 / 2, 2, 3]


def load(raw: Path, name: str) -> pd.DataFrame:
    r = pyreadr.read_r(str(raw / "bmetr" / "data" / f"{name}.rda"))
    df = next(iter(r.values()))
    for c in df.select_dtypes("category").columns:
        df[c] = df[c].astype(str)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/derived")
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

    d.to_csv(out / "beethoven_symphony_duration_ratio.csv", index=False, encoding="utf-8")
    s.to_csv(out / "beethoven_symphony_coda_tempo.csv", index=False, encoding="utf-8")
    marks.to_csv(out / "beethoven_symphony_marks.csv", index=False, encoding="utf-8")
    rec.to_csv(out / "beethoven_symphony_recordings.csv", index=False, encoding="utf-8")

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
    mv.to_csv(out / "beethoven_symphony_movement_summary.csv", index=False, encoding="utf-8")
    cond.to_csv(out / "beethoven_symphony_conductor_summary.csv", index=False, encoding="utf-8")
    print("movements", len(mv), "conductors", len(cond))
    print("coda rows", len(s), "rectified", int(s["rectified"].sum()), "unusable", int(s["unusable"].sum()))
    print(cond[["conductor", "ptype", "median_diff_bpm", "n_movements"]].to_string())
    print(s[~s.unusable & (s.symphony != 9)].groupby("ptype")["coda_tempo_diff_bpm"].describe())


if __name__ == "__main__":
    main()
