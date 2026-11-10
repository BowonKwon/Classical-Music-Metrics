"""1.10: the piece map (design 63 §2 B, rules fixed in §8 before computing).

Every movement on the site becomes one vector of score metrics; two principal-component maps are drawn:
  notes    note metrics only, every movement with no missing value among them (chorales included)
  harmony  note and chord metrics, movements with harmony labels and no missing value among them
Metric selection (fixed beforehand): drop a metric if |Spearman(metric, log length_qb)| > 0.5 over the movements
of that map, or if more than 30% of those movements lack it. For the harmony map the 30% is counted among
movements with harmony labels (counted over all movements, the 361 unannotated chorales alone would remove every
chord metric; noted in design 63 §8).
z-scores (population SD), principal components by SVD, the sign of each component set so that its largest
absolute loading is positive. Stability: 200 bootstrap resamples of movements and leave-one-collection-out;
|correlation| of each component's loadings with the full-data loadings.

Outputs (data/derived): piecemap_110_points.csv, piecemap_110_loadings.csv, piecemap_110_stability.csv,
piecemap_110_selection.csv, piecemap_110_z.csv (z-scores used for the fingerprints).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from registry import METRICS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/derived"
RHO_MAX, MISS_MAX, N_BOOT, SEED, STABLE = 0.5, 0.30, 200, 1910, 0.8
# Added after the first computation (design 63 §9): metrics undefined by definition for whole collections or for
# some pieces. Kept under the 30% rule, they made complete-case selection drop entire collections (all quartets,
# Bach's solo works) from the harmony map: 475 of 793 movements.
DOMAIN_LIMITED = {"outside_5oct_ratio": "keyboard collections only", "cadences_per_100_measures": "collections with cadence labels",
                  "pac_ratio_of_cadences": "collections with cadence labels", "key_change_distance_median": "blank without a key change",
                  "phrase_len_median": "needs three phrase ends", "phrase_4_8_ratio": "needs three phrase ends"}
NOTE_GROUPS = ("pitch", "rhythm", "texture", "melody")


def all_movements() -> pd.DataFrame:
    a = pd.read_csv(D / "score_metrics_by_movement.csv", low_memory=False)
    a = a[a["collection"] != "chorales_kern370"]
    b = pd.read_csv(D / "score_metrics_13_by_movement.csv", low_memory=False).drop(columns=["license"])
    base = a.merge(b, on=["corpus", "piece_id"], how="left")
    son = pd.read_csv(D / "sonata_metrics_by_movement.csv", low_memory=False)
    son = son[~son["corpus"].isin(set(base["corpus"]))]
    c19 = pd.read_csv(D / "collections_19_by_movement.csv", low_memory=False)
    c19 = c19[~c19["corpus"].isin(set(base["corpus"]))]
    keep = ["corpus", "piece_id", "composer", "collection", "work", "movement_title", "composed_start", "composed_end", "length_qb", "n_measures"]
    mids = [m["id"] for m in METRICS if m["table"] == "score"]
    frames = []
    for f in (base, son, c19):
        cols = [c for c in keep + mids if c in f.columns]
        frames.append(f[cols])
    df = pd.concat(frames, ignore_index=True)
    for extra in ("score_metrics_19_by_movement.csv", "score_metrics_110_by_movement.csv"):
        p = D / extra
        if p.exists():
            e = pd.read_csv(p)
            e = e[[c for c in e.columns if c in ("corpus", "piece_id") or c in mids]]
            df = df.drop(columns=[c for c in e.columns if c not in ("corpus", "piece_id") and c in df.columns]).merge(e, on=["corpus", "piece_id"], how="left")
    ys = pd.to_numeric(df["composed_start"], errors="coerce")
    ye = pd.to_numeric(df["composed_end"], errors="coerce")
    df["year"] = (ys + ye.fillna(ys)) / 2
    df.loc[df["composer"] == "J. C. Bach", "year"] = np.nan  # composition years unconfirmed (1.8)
    return df


def metric_groups() -> tuple[list[str], list[str]]:
    sc = [m for m in METRICS if m["table"] == "score"]
    notes = [m["id"] for m in sc if m["group"] in NOTE_GROUPS]
    harm = [m["id"] for m in sc if m["group"] == "harmony"]
    return notes, harm


def select(df: pd.DataFrame, cands: list[str], base_rows: pd.Series) -> pd.DataFrame:
    rows = []
    sub = df[base_rows]
    loglen = np.log(sub["length_qb"].astype(float))
    for mid in cands:
        if mid not in sub:
            continue
        v = pd.to_numeric(sub[mid], errors="coerce")
        miss = float(v.isna().mean())
        ok = v.notna()
        rho = float(spearmanr(v[ok], loglen[ok]).statistic) if ok.sum() > 10 and v[ok].nunique() > 1 else float("nan")
        reason = "domain" if mid in DOMAIN_LIMITED else ("missing" if miss > MISS_MAX else ("length" if np.isnan(rho) or abs(rho) > RHO_MAX else ""))
        rows.append(dict(metric=mid, missing=miss, rho_loglen=rho, kept=reason == "", reason=reason))
    return pd.DataFrame(rows)


def pca(X: np.ndarray, k: int = 2):
    Z = (X - X.mean(0)) / X.std(0, ddof=0)
    U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    V = Vt[:k].T.copy()
    for j in range(k):
        if V[np.argmax(np.abs(V[:, j])), j] < 0:
            V[:, j] *= -1
    scores = Z @ V
    expl = (S ** 2) / (S ** 2).sum()
    return Z, V, scores, expl[:k]


def stability(X: np.ndarray, groups: np.ndarray, V: np.ndarray) -> dict:
    rng = np.random.default_rng(SEED)
    boot = [[], []]
    for _ in range(N_BOOT):
        idx = rng.integers(0, len(X), len(X))
        _, Vb, _, _ = pca(X[idx])
        for j in range(2):
            boot[j].append(abs(np.corrcoef(V[:, j], Vb[:, j])[0, 1]))
    loo = [[], []]
    for g in np.unique(groups):
        m = groups != g
        _, Vl, _, _ = pca(X[m])
        for j in range(2):
            loo[j].append(abs(np.corrcoef(V[:, j], Vl[:, j])[0, 1]))
    return {f"pc{j + 1}_boot_median": float(np.median(boot[j])) for j in range(2)} | {f"pc{j + 1}_loo_min": float(np.min(loo[j])) for j in range(2)}


def main(out: Path = D) -> dict:
    df = all_movements()
    notes, harm = metric_groups()
    has_h = df[harm].notna().any(axis=1)
    sel_n = select(df, notes, pd.Series(True, index=df.index))
    sel_h = select(df, notes + harm, has_h)
    sel_n["map"], sel_h["map"] = "notes", "harmony"
    pts, loads, stab, zs = [], [], [], []
    for name, sel, base in (("notes", sel_n, pd.Series(True, index=df.index)), ("harmony", sel_h, has_h)):
        use = sel.loc[sel.kept, "metric"].tolist()
        sub = df[base].dropna(subset=use)
        X = sub[use].astype(float).to_numpy()
        Z, V, S, ex = pca(X)
        st = stability(X, sub["corpus"].to_numpy(), V)
        stab.append(dict(map=name, n_movements=len(sub), n_metrics=len(use), pc1_explained=ex[0], pc2_explained=ex[1], **st))
        loads += [dict(map=name, metric=m, pc1=V[i, 0], pc2=V[i, 1]) for i, m in enumerate(use)]
        p = sub[["corpus", "piece_id", "composer", "year"]].copy()
        p["map"], p["pc1"], p["pc2"] = name, S[:, 0], S[:, 1]
        pts.append(p)
        if name == "harmony":
            z = pd.DataFrame(Z, columns=use)
            z.insert(0, "piece_id", sub["piece_id"].to_numpy())
            z.insert(0, "corpus", sub["corpus"].to_numpy())
            zs.append(z)
    pd.concat(pts).to_csv(out / "piecemap_110_points.csv", index=False, lineterminator="\n")
    pd.DataFrame(loads).to_csv(out / "piecemap_110_loadings.csv", index=False, lineterminator="\n")
    pd.DataFrame(stab).to_csv(out / "piecemap_110_stability.csv", index=False, lineterminator="\n")
    pd.concat([sel_n, sel_h]).to_csv(out / "piecemap_110_selection.csv", index=False, lineterminator="\n")
    zs[0].round(3).to_csv(out / "piecemap_110_z.csv", index=False, lineterminator="\n")
    # annotated vs note-only departure (design 63 §8): Spearman with a 95% bootstrap interval
    s110 = pd.read_csv(out / "score_metrics_110_by_movement.csv").dropna(subset=["departure_mean", "departure_mean_notes"])
    x, y = s110["departure_mean"].to_numpy(), s110["departure_mean_notes"].to_numpy()
    rng = np.random.default_rng(SEED)
    bs = [spearmanr(x[i], y[i]).statistic for i in (rng.integers(0, len(x), len(x)) for _ in range(1000))]
    pd.DataFrame([dict(n=len(x), rho=spearmanr(x, y).statistic, ci_lo=np.percentile(bs, 2.5), ci_hi=np.percentile(bs, 97.5))]).to_csv(
        out / "piecemap_110_departure.csv", index=False, lineterminator="\n")
    return dict(stability=pd.DataFrame(stab))


if __name__ == "__main__":
    r = main()
    print(r["stability"].to_string())
