"""Cross-check of the Bach chorales between two encodings (1.0 validation of the chromatic ratio etc.).

  python src/chorale_crosscheck.py [--derived data/derived]

Reads score_metrics_by_movement.csv (DCML chorales, corpus bach_chorales) and score_metrics_kern370.csv
(Sapp's Humdrum 370 chorales; written by score_metrics.py), pairs chorales by their number
(DCML piece_id '001 …' <-> kern piece_id 'chor001'), keeps pairs whose note counts agree within 2%
(|n_dcml - n_kern| / n_dcml <= 0.02 — so that the two encodings contain the same music), and writes
chorale_crosscheck_dcml_vs_kern.csv: per metric, the number of pairs, both medians, the Pearson r and
the median absolute difference.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

METRICS = ["chromatic_ratio", "pitch_class_entropy", "rhythm_entropy", "offbeat_onset_ratio", "mean_simultaneity",
           "notes_per_quarter", "top_leap_ratio", "top_mean_interval_semitones", "pitch_range_semitones"]


def crosscheck(derived: Path) -> pd.DataFrame:
    d = pd.read_csv(derived / "score_metrics_by_movement.csv")
    d = d[d["corpus"] == "bach_chorales"].copy()
    k = pd.read_csv(derived / "score_metrics_kern370.csv").copy()
    d["num"] = d["piece_id"].str[:3].astype(int)
    k["num"] = k["piece_id"].str.replace("chor", "", regex=False).astype(int)
    m = d.merge(k, on="num", suffixes=("_d", "_k"))
    m = m[(m["n_notes_d"] - m["n_notes_k"]).abs() / m["n_notes_d"] <= 0.02]
    rows = []
    for met in METRICS:
        x, y = m[f"{met}_d"].astype(float), m[f"{met}_k"].astype(float)
        ok = x.notna() & y.notna()
        x, y = x[ok], y[ok]
        rows.append(dict(metric=met, n=int(len(x)), dcml_median=round(x.median(), 3), kern_median=round(y.median(), 3),
                         pearson_r=round(x.corr(y), 3), median_abs_diff=round((x - y).abs().median(), 4)))
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", default="data/derived")
    a = ap.parse_args()
    out = crosscheck(Path(a.derived))
    out.to_csv(Path(a.derived) / "chorale_crosscheck_dcml_vs_kern.csv", index=False, encoding="utf-8")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
