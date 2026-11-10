"""1.12: vector and matrix summaries of a movement (design 72; rules fixed there before computing).

A  Pitch-class distribution and its discrete Fourier transform. Notes are preprocessed as for key_clarity
   (grace notes dropped, ties merged, onsets only; pitch class = MIDI mod 12; weight = merged duration).
     pc_0 .. pc_11      share of the total duration on each pitch class (C = 0)
     dft_mag_1 .. 6     |X_k| / X_0 with X_k = sum_n w_n exp(-2 pi i k n / 12)  (normalisation of Viaccoz et al. 2023)
     dft_phase_1 .. 6   angle of X_k in radians (published, not interpreted)
B  Root transitions: successive chord labels in the same local key whose root changes (the unit of
   fifth_root_motion_ratio, 1.9). Roots are positions on the line of fifths from the local tonic, folded to
   -5..+6 (12 classes); a transition whose two roots fold onto the same class is dropped and counted.
     per collection and local-key mode: a 12 x 12 count matrix and its transition entropy = the row-frequency-
       weighted mean of H(B | A = a) / log2(11) (the row quantity is eq. 3 of Moss et al. 2019; the weighted
       mean is ours), on all transitions and rarefied to RARE_N transitions (mean of RARE_REPS draws without
       replacement); 95% interval from BOOT_REPS bootstrap resamples of movements, each rarefied once
     per movement: root_motion_entropy = entropy of the folded root-motion steps (11 classes) / log2(11);
       blank under MIN_ROOT_STEPS steps
D  Variation inside a movement, on windows of WINDOW_BARS measures (mc, no overlap; an incomplete last window is
   dropped; blank under MIN_WINDOWS windows):
     chromatic_window_sd   population SD of the windows' chromatic ratio (the definition of chromatic_ratio)
     density_window_cv     SD / mean of the windows' note density (onsets per quarter of the window's length)

Outputs (data/derived): score_metrics_112_by_movement.csv, root_transitions_112.csv,
root_transition_entropy_112.csv. Nothing in the earlier tables changes.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_metrics as sm  # noqa: E402
import score_metrics_19 as s19  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RARE_N, RARE_REPS, BOOT_REPS, SEED = 400, 200, 200, 112
MIN_ROOT_STEPS = 30
WINDOW_BARS, MIN_WINDOWS = 4, 4
LOG11 = math.log2(11)
MODES = ("major", "minor")


# ---------------------------------------------------------------- A
def pc_weights(on: pd.DataFrame) -> np.ndarray:
    return np.bincount((on["midi"].to_numpy() % 12).astype(int), weights=on["dur_merged"].to_numpy(dtype=float), minlength=12)


def dft(w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(|X_k| / X_0, angle X_k) for k = 1..6 of a 12-vector of non-negative weights."""
    x = np.fft.fft(np.asarray(w, dtype=float))
    return np.abs(x[1:7]) / x[0].real, np.angle(x[1:7])


# ---------------------------------------------------------------- D
def window_series(on: pd.DataFrame, measures: pd.DataFrame) -> list[tuple[int, float, float]]:
    """(first mc, note density, chromatic ratio or NaN) of every complete window with a positive length."""
    mq = measures.set_index("mc")["duration_qb"].astype(float)
    n_win = int(measures["mc"].max()) // WINDOW_BARS  # complete windows only
    win = (on["mc"].to_numpy().astype(int) - 1) // WINDOW_BARS
    diat = ((on["tpc"] >= on["keysig"] - 1) & (on["tpc"] <= on["keysig"] + 5)).to_numpy()
    out = []
    for k in range(n_win):
        ln = float(sum(mq.get(m, 0.0) for m in range(k * WINDOW_BARS + 1, k * WINDOW_BARS + WINDOW_BARS + 1)))
        if ln <= 0:
            continue
        sel = win == k
        n = int(sel.sum())
        out.append((k * WINDOW_BARS + 1, n / ln, 1.0 - float(diat[sel].mean()) if n else float("nan")))
    return out


def window_metrics(on: pd.DataFrame, measures: pd.DataFrame) -> dict:
    ser = window_series(on, measures)
    dens = [d for _, d, _ in ser]
    chrom = [c for _, _, c in ser if not math.isnan(c)]
    out: dict = {"n_windows_112": len(dens)}
    if len(dens) >= MIN_WINDOWS and np.mean(dens) > 0:
        out["density_window_cv"] = float(np.std(dens) / np.mean(dens))
    if len(chrom) >= MIN_WINDOWS:
        out["chromatic_window_sd"] = float(np.std(chrom))
    return out


def note_112(notes: pd.DataFrame, measures: pd.DataFrame) -> dict:
    """`notes` = sm.load_dcml_notes(...) with an added integer column mc."""
    df = sm.merge_ties(notes[~notes["grace"]].copy())
    on = df[~df["attached"] & ~df["tied_cont"]]
    out: dict = {}
    if len(on) == 0:
        return out
    w = pc_weights(on)
    if w.sum() > 0:
        mag, ph = dft(w)
        out.update({f"pc_{i}": float(w[i] / w.sum()) for i in range(12)})
        out.update({f"dft_mag_{k}": float(mag[k - 1]) for k in range(1, 7)})
        out.update({f"dft_phase_{k}": float(ph[k - 1]) for k in range(1, 7)})
    out.update(window_metrics(on, measures))
    return out


# ---------------------------------------------------------------- B
def fold12(x) -> np.ndarray:
    """Line-of-fifths position folded enharmonically to -5..+6."""
    return (np.asarray(x).astype(int) + 5) % 12 - 5


def transitions(h: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(root before, root after, local key minor?) for successive chord labels in the same local key whose
    root changes; roots as annotated (not folded). Same selection as score_metrics_19.harmony_19."""
    empty = (np.array([], dtype=int), np.array([], dtype=int), np.array([], dtype=bool))
    if "root" not in h or "localkey" not in h:
        return empty
    c = h[h["chord"].notna() & (h["chord"] != "") & h["root"].notna()]
    if len(c) < 2:
        return empty
    root = pd.to_numeric(c["root"], errors="coerce").to_numpy()
    lk = c["localkey"].astype(str).to_numpy()
    if "localkey_is_minor" in c:
        minor = c["localkey_is_minor"].astype(str).isin(["1", "1.0", "True", "true"]).to_numpy()
    else:  # the local key's own numeral: lower case = minor ('vi/V' is the vi of V)
        minor = np.array([s.split("/")[0].lstrip("#b")[:1].islower() for s in lk])
    dr = root[1:] - root[:-1]
    ok = (lk[1:] == lk[:-1]) & ~np.isnan(dr) & (dr != 0)
    return root[:-1][ok].astype(int), root[1:][ok].astype(int), minor[:-1][ok]


def entropy_bits(counts: np.ndarray) -> float:
    c = np.asarray(counts, dtype=float)
    c = c[c > 0]
    p = c / c.sum()
    return float(-(p * np.log2(p)).sum())


def root_motion_entropy(a: np.ndarray, b: np.ndarray) -> tuple[int, float]:
    step = fold12(b - a)
    step = step[step != 0]
    if len(step) < MIN_ROOT_STEPS:
        return len(step), float("nan")
    return len(step), entropy_bits(np.bincount(step + 5, minlength=12)) / LOG11


def matrix(fa: np.ndarray, fb: np.ndarray) -> np.ndarray:
    m = np.zeros((12, 12))
    np.add.at(m, (fa + 5, fb + 5), 1)
    return m


def transition_entropy(m: np.ndarray) -> float:
    """Row-frequency-weighted mean of the rows' entropy / log2(11)."""
    rows = m.sum(axis=1)
    n = rows.sum()
    if n <= 0:
        return float("nan")
    return float(sum(rows[i] / n * entropy_bits(m[i]) / LOG11 for i in range(12) if rows[i] > 0))


def rarefied(fa: np.ndarray, fb: np.ndarray, rng: np.random.Generator, reps: int) -> float:
    if len(fa) < RARE_N:
        return float("nan")
    vals = []
    for _ in range(reps):
        i = rng.choice(len(fa), RARE_N, replace=False)
        vals.append(transition_entropy(matrix(fa[i], fb[i])))
    return float(np.mean(vals))


def collection_tables(per_mov: dict[tuple[str, str], tuple]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """per_mov: (corpus, piece) -> (a, b, minor). Returns (matrix rows, entropy rows)."""
    corpora = sorted({k[0] for k in per_mov})
    mrows, erows = [], []
    for ci, corpus in enumerate(corpora):
        movs = [v for k, v in sorted(per_mov.items()) if k[0] == corpus]
        for mi, mode in enumerate(MODES):
            parts = []
            for a, b, minor in movs:
                s = minor if mode == "minor" else ~minor
                fa, fb = fold12(a[s]), fold12(b[s])
                parts.append((fa, fb))
            fa = np.concatenate([p[0] for p in parts]) if parts else np.array([], dtype=int)
            fb = np.concatenate([p[1] for p in parts]) if parts else np.array([], dtype=int)
            same = fa == fb
            n_drop = int(same.sum())
            fa, fb = fa[~same], fb[~same]
            m = matrix(fa, fb)
            for i in range(12):
                for j in range(12):
                    if m[i, j] > 0:
                        mrows.append(dict(corpus=corpus, mode=mode, from_fifths=i - 5, to_fifths=j - 5, count=int(m[i, j])))
            rng = np.random.default_rng([SEED, ci, mi])
            r = rarefied(fa, fb, rng, RARE_REPS)
            lo = hi = float("nan")
            n_boot = 0
            if not np.isnan(r):
                clean = [(x[~(x == y)], y[~(x == y)]) for x, y in parts]
                vals = []
                for _ in range(BOOT_REPS):
                    pick = rng.integers(0, len(clean), len(clean))
                    xa = np.concatenate([clean[i][0] for i in pick])
                    xb = np.concatenate([clean[i][1] for i in pick])
                    if len(xa) < RARE_N:
                        continue
                    vals.append(rarefied(xa, xb, rng, 1))
                n_boot = len(vals)
                if vals:
                    lo, hi = (float(v) for v in np.percentile(vals, [2.5, 97.5]))
            erows.append(dict(corpus=corpus, mode=mode, n_movements=sum(1 for p in parts if len(p[0])), n_transitions=int(len(fa)),
                              n_dropped_enharmonic=n_drop, entropy_all=transition_entropy(m), entropy_rarefied=r,
                              ci_low=lo, ci_high=hi, n_boot=n_boot, rare_n=RARE_N))
    return pd.DataFrame(mrows), pd.DataFrame(erows)


# ---------------------------------------------------------------- run
def corpus_112(raw: Path, folder: str, per_mov: dict) -> list[dict]:
    base = raw / folder
    meta = pd.read_csv(base / "metadata.tsv", sep="\t", dtype=str)
    rows = []
    for piece in meta["piece"]:
        npath = base / "notes" / f"{piece}.notes.tsv"
        if not npath.exists():
            continue
        measures = pd.read_csv(base / "measures" / f"{piece}.measures.tsv", sep="\t", dtype=str)
        measures["mc"] = measures["mc"].astype(int)
        notes = sm.load_dcml_notes(npath, measures)
        notes["mc"] = pd.read_csv(npath, sep="\t", dtype=str, usecols=["mc"])["mc"].astype(int).to_numpy()
        r = {"corpus": folder, "piece_id": piece}
        r.update(note_112(notes, measures))
        hpath = base / "harmonies" / f"{piece}.harmonies.tsv"
        if hpath.exists():
            a, b, minor = transitions(pd.read_csv(hpath, sep="\t", dtype=str))
            if len(a):
                per_mov[(folder, piece)] = (a, b, minor)
                r["n_root_steps"], r["root_motion_entropy"] = root_motion_entropy(a, b)
        rows.append(r)
    return rows


def main(raw: Path = ROOT / "data/raw", out: Path = ROOT / "data/derived") -> pd.DataFrame:
    rows, per_mov = [], {}
    for folder in s19.COLLECTIONS_19:
        r = corpus_112(raw, folder, per_mov)
        print(folder, len(r), flush=True)
        rows += r
    df = pd.DataFrame(rows)
    df.to_csv(out / "score_metrics_112_by_movement.csv", index=False, encoding="utf-8", lineterminator="\n")
    mat, ent = collection_tables(per_mov)
    mat.to_csv(out / "root_transitions_112.csv", index=False, encoding="utf-8", lineterminator="\n")
    ent.to_csv(out / "root_transition_entropy_112.csv", index=False, encoding="utf-8", lineterminator="\n")
    return df


if __name__ == "__main__":
    main()
