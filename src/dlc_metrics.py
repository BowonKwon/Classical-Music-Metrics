"""1.6: score and harmony metrics over the 40 corpora of the DCML Distant Listening Corpus (DLC).

  python src/dlc_metrics.py   ->  data/derived/dlc_movement_metrics.csv   one row per piece/movement
                                  data/derived/dlc_corpus_metrics.csv     one row per corpus (medians)
                                  data/derived/dlc_period_metrics.csv     50-year periods, all corpora and keyboard only

Inputs: the 40 sub-corpus clones in data/raw/{corpus} (Hentschel et al. 2025, Scientific Data 12:685,
CC BY-NC-SA 4.0) and data/aliases/dlc_corpora.csv (composer, genre and display names, made by the editor).
Metric definitions are those of score_metrics.py; nothing is redefined here.

Period values give each corpus one vote: the period value is the median of the corpus medians, so that
large corpora (Corelli 149 pieces; Beethoven's two corpora 32,164 bars) do not decide a period alone.
A corpus is placed in the period of its median composition year (middle of composed_start and composed_end).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import score_metrics as sm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW, ALI, D = ROOT / "data/raw", ROOT / "data/aliases", ROOT / "data/derived"
LIC = "CC-BY-NC-SA-4.0"
PERIOD = 50
MIN_BARS = 300  # smaller corpora enter periods but get no composer-level line (design 36 section 10)

# Shown on the period axis: metrics that do not depend on whether an annotator marked local keys or cadences.
PERIOD_METRICS = ["chromatic_ratio", "pitch_class_entropy", "tpc_vocabulary",
                  "applied_chord_ratio", "seventh_chord_ratio", "chromatic_numeral_ratio",
                  "chord_vocabulary_per_100_labels", "chords_per_measure"]
# Corpus table only: annotation practice for local keys and cadences differs between corpora.
CORPUS_ONLY = ["local_key_changes_per_100_measures", "cadences_per_100_measures"]


def year(v) -> float:
    m = re.search(r"\d{4}", str(v))
    return float(m.group()) if m else float("nan")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    meta = pd.read_csv(ALI / "dlc_corpora.csv", dtype=str, keep_default_na=False)
    rows = []
    for r in meta.itertuples(index=False):
        rows += sm.dcml_corpus(RAW, r.corpus, r.composer, r.corpus, LIC)
    df = pd.DataFrame(rows).merge(meta[["corpus", "genre"]], on="corpus", how="left")
    ys, ye = df["composed_start"].map(year), df["composed_end"].map(year)
    df["year"] = (ys.fillna(ye) + ye.fillna(ys)) / 2
    # Composition range as recorded: earliest start, latest end. A start given as '..' (unknown) is
    # flagged rather than replaced, and the earliest known year stands in for drawing only.
    df["start_known"], df["end_known"] = ys, ye
    df["start_unknown"] = ys.isna()
    df = df.sort_values(["year", "corpus", "piece_id"], kind="mergesort").reset_index(drop=True)
    df.drop(columns=["start_known", "end_known"]).to_csv(D / "dlc_movement_metrics.csv", index=False, encoding="utf-8", lineterminator="\n")

    agg = {"pieces": ("piece_id", "size"), "bars": ("n_measures", "sum"), "year_min": ("year", "min"),
           "year_max": ("year", "max"), "year": ("year", "median"),
           "composed_min": ("start_known", "min"), "composed_max": ("end_known", "max"),
           "earliest_end": ("end_known", "min"), "start_unknown_pieces": ("start_unknown", "sum"),
           "labelled_pieces": ("n_chord_labels", lambda s: int((s.fillna(0) > 0).sum()))}
    agg.update({m: (m, "median") for m in PERIOD_METRICS + CORPUS_ONLY})
    c = df.groupby("corpus").agg(**agg).reset_index()
    c["composed_min"] = c[["composed_min", "earliest_end"]].min(axis=1)  # drawing only when starts are unknown
    c = meta.merge(c, on="corpus").sort_values("year", kind="mergesort")
    c["period"] = (c["year"] // PERIOD * PERIOD).astype(int)
    c["small"] = c["bars"] < MIN_BARS
    c.to_csv(D / "dlc_corpus_metrics.csv", index=False, encoding="utf-8", lineterminator="\n")

    out = []
    for scope, sub in (("all", c), ("keyboard", c[c["genre"] == "keyboard"])):
        for per, g in sub.groupby("period"):
            row = {"scope": scope, "period": int(per), "corpora": len(g), "pieces": int(g["pieces"].sum()), "bars": int(g["bars"].sum()),
                   "corpus_list": "; ".join(g["corpus"])}
            for m in PERIOD_METRICS:
                v = g[m].dropna()
                row[m] = v.median() if len(v) else float("nan")
                row[m + "_q1"] = v.quantile(.25) if len(v) else float("nan")
                row[m + "_q3"] = v.quantile(.75) if len(v) else float("nan")
                row[m + "_n"] = int(len(v))
            out.append(row)
    pd.DataFrame(out).to_csv(D / "dlc_period_metrics.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(f"{len(df)} pieces, {int(df['n_measures'].sum())} bars, {len(c)} corpora")
    print(pd.DataFrame(out)[["scope", "period", "corpora", "pieces", "chromatic_ratio", "applied_chord_ratio", "seventh_chord_ratio"]].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
