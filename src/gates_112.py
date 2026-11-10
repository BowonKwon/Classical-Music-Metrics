"""1.12: which of the five candidate summaries become metrics (design 72 §6-1, fixed before computing).

A candidate is published as a metric only if it passes all three:
  length   |Spearman rho| with log(length_qb) <= 0.5 over the movements that have a value
           (root_motion_entropy: also with log(number of root steps))
  overlap  |Pearson r| <= 0.9 with each related existing metric (and, for the two Fourier magnitudes, with
           each other; if those two overlap, dft_mag_5 stays)
  missing  blank in at most 30% of movements (note candidates: every movement; root_motion_entropy: movements
           with harmony labels)
A candidate that fails stays in the CSV only, with the reason. A candidate that passes can still be withheld
(WITHHELD below, with the reason): the conditions are necessary, not sufficient.

Output: data/derived/metrics_112_gates.csv (one row per candidate and check).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import piecemap_110 as pm  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/derived"
RHO_MAX, R_MAX, MISS_MAX = 0.5, 0.9, 0.30
CANDIDATES = {
    # id: (base rows, length variables, related existing metrics)
    "dft_mag_5": ("all", ["length_qb"], ["key_clarity", "chromatic_ratio", "pitch_class_entropy", "dft_mag_1"]),
    "dft_mag_1": ("all", ["length_qb"], ["key_clarity", "chromatic_ratio", "pitch_class_entropy", "dft_mag_5"]),
    "root_motion_entropy": ("harmony", ["length_qb", "n_root_steps"], ["fifth_root_motion_ratio"]),
    "chromatic_window_sd": ("all", ["length_qb"], ["chromatic_ratio"]),
    "density_window_cv": ("all", ["length_qb"], ["notes_per_quarter"]),
}


def table() -> pd.DataFrame:
    df = pm.all_movements()
    new = pd.read_csv(D / "score_metrics_112_by_movement.csv")
    s19 = pd.read_csv(D / "score_metrics_19_by_movement.csv")[["corpus", "piece_id", "n_root_changes"]]
    df = df.merge(new, on=["corpus", "piece_id"], how="left").merge(s19, on=["corpus", "piece_id"], how="left")
    df["has_harmony"] = df["n_root_changes"].notna()
    return df


def gates(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cid, (base, lengths, related) in CANDIDATES.items():
        sub = df[df["has_harmony"]] if base == "harmony" else df
        v = pd.to_numeric(sub[cid], errors="coerce")
        ok = v.notna()
        miss = float(1 - ok.mean())
        rows.append(dict(candidate=cid, check="missing", against="", n=int(len(sub)), value=miss, limit=MISS_MAX, passed=miss <= MISS_MAX))
        for ln in lengths:
            x = np.log(pd.to_numeric(sub[ln], errors="coerce"))
            m = ok & x.notna() & np.isfinite(x)
            rho = float(spearmanr(v[m], x[m]).statistic)
            rows.append(dict(candidate=cid, check="length", against=f"log {ln}", n=int(m.sum()), value=rho, limit=RHO_MAX, passed=abs(rho) <= RHO_MAX))
        for rel in related:
            y = pd.to_numeric(sub[rel], errors="coerce")
            m = ok & y.notna()
            r = float(pearsonr(v[m], y[m]).statistic)
            rho = float(spearmanr(v[m], y[m]).statistic)
            rows.append(dict(candidate=cid, check="overlap", against=rel, n=int(m.sum()), value=r, spearman=rho, limit=R_MAX, passed=abs(r) <= R_MAX))
    g = pd.DataFrame(rows)
    # the two Fourier magnitudes against each other: dft_mag_5 stays
    pair = (g.candidate == "dft_mag_5") & (g.against == "dft_mag_1")
    g.loc[pair, "passed"] = True
    return g


def verdicts(g: pd.DataFrame) -> dict[str, bool]:
    """Which candidates pass all three conditions."""
    return {c: bool(g[g.candidate == c]["passed"].all()) for c in CANDIDATES}


# Decided after computing (2026-11-10; design 72 section 11): the conditions are necessary, not sufficient.
# A candidate that passes is still withheld if its values cannot be given a reading; it stays in the CSV.
WITHHELD = {"dft_mag_1": "no reading for its values in tonal music"}


def published(g: pd.DataFrame) -> list[str]:
    return [c for c, ok in verdicts(g).items() if ok and c not in WITHHELD]


def main(out: Path = D) -> pd.DataFrame:
    g = gates(table())
    g.to_csv(out / "metrics_112_gates.csv", index=False, encoding="utf-8", lineterminator="\n")
    return g


if __name__ == "__main__":
    g = main()
    print(g.to_string())
    print(verdicts(g))
