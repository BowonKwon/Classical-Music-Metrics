"""1.10: how far and how long a movement leaves its home key (design 63).

From the annotated local keys (as in the 1.9 key maps, now for every movement with harmony labels):
  departure_mean     time-weighted mean distance of the local key's signature from the home key's,
                     folded enharmonically to 0..6 (the scale of key_change_distance_median)
  off_tonic_share    share of the time spent at a distance above 0 (the home key and its relative count as home)
  departure_max      the largest such distance
A note-only check that needs no annotation (not a published metric; a comparison figure):
  departure_mean_notes  the same mean with keys found by Krumhansl-Schmuckler on 4-bar windows (no overlap),
                        measured from the key found the same way for the whole movement

Output: data/derived/score_metrics_110_by_movement.csv keyed on (corpus, piece_id).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keymaps_19 as km  # noqa: E402
import score_metrics as sm  # noqa: E402
import score_metrics_19 as s19  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WINDOW_BARS = 4


def fold(d: float) -> int:
    x = abs(int(round(d))) % 12
    return min(x, 12 - x)


def departure(segs: list[dict]) -> dict:
    if not segs:
        return {}
    w = np.array([max(s["end_qb"] - s["start_qb"], 0.0) for s in segs])
    d = np.array([fold(s["sig_rel"]) for s in segs])
    if w.sum() <= 0:
        return {}
    return dict(departure_mean=float((w * d).sum() / w.sum()), off_tonic_share=float(w[d > 0].sum() / w.sum()),
                departure_max=int(d.max()))


def ks_key(w: np.ndarray) -> tuple[int, bool] | None:
    """Krumhansl-Schmuckler: (tonic pitch class, minor?) of the best-correlating of the 24 keys."""
    if w.sum() <= 0 or np.ptp(w) == 0:
        return None
    best, arg = -2.0, None
    for minor, prof in ((False, s19.KK_MAJOR), (True, s19.KK_MINOR)):
        for t in range(12):
            r = float(np.corrcoef(w, np.roll(prof, t))[0, 1])
            if r > best:
                best, arg = r, (t, minor)
    return arg


def ks_sig(key: tuple[int, bool]) -> int:
    t, minor = key
    f = (t * 7) % 12  # pitch class -> position on the circle of fifths (C = 0, G = 1, ...)
    return f - 3 * int(minor)


def departure_notes(notes: pd.DataFrame, measures: pd.DataFrame) -> dict:
    df = sm.merge_ties(notes[~notes["grace"]].copy())
    on = df[~df["attached"] & ~df["tied_cont"]].copy()
    if on.empty:
        return {}
    pcw = lambda g: np.bincount((g["midi"].to_numpy() % 12).astype(int), weights=g["dur_merged"].to_numpy(float), minlength=12)  # noqa: E731
    home = ks_key(pcw(on))
    if home is None:
        return {}
    hs = ks_sig(home)
    # 4-bar windows by measure count (mc), weighted by their notated length
    mq = measures.set_index("mc")["duration_qb"].astype(float) if "duration_qb" in measures else None
    on["win"] = (on["mc"].astype(int) - 1) // WINDOW_BARS if "mc" in on else None
    num = den = 0.0
    n = 0
    for wi, g in on.groupby("win"):
        k = ks_key(pcw(g))
        if k is None:
            continue
        mcs = range(wi * WINDOW_BARS + 1, wi * WINDOW_BARS + WINDOW_BARS + 1)
        ln = float(sum(mq.get(m, 0.0) for m in mcs)) if mq is not None else 1.0
        num += ln * fold(ks_sig(k) - hs)
        den += ln
        n += 1
    return dict(departure_mean_notes=num / den, n_windows=n) if den > 0 else {}


def corpus_110(raw: Path, folder: str) -> list[dict]:
    base = raw / folder
    meta = pd.read_csv(base / "metadata.tsv", sep="\t", dtype=str).set_index("piece")
    rows = []
    for piece in meta.index:
        npath = base / "notes" / f"{piece}.notes.tsv"
        if not npath.exists():
            continue
        measures = pd.read_csv(base / "measures" / f"{piece}.measures.tsv", sep="\t", dtype=str)
        measures["mc"] = measures["mc"].astype(int)
        notes = sm.load_dcml_notes(npath, measures)
        notes["mc"] = pd.read_csv(npath, sep="\t", dtype=str, usecols=["mc"])["mc"].astype(int).to_numpy()
        r = {"corpus": folder, "piece_id": piece}
        r.update(departure_notes(notes, measures))
        hpath = base / "harmonies" / f"{piece}.harmonies.tsv"
        if hpath.exists():
            h = pd.read_csv(hpath, sep="\t", dtype=str)
            if "localkey" in h and h["localkey"].notna().any():
                r.update(departure(km.segments(h, float(meta.loc[piece, "length_qb"]), int(meta.loc[piece, "last_mn"]))))
        rows.append(r)
    return rows


def main(raw: Path = ROOT / "data/raw", out: Path = ROOT / "data/derived") -> pd.DataFrame:
    rows = []
    for folder in s19.COLLECTIONS_19:
        r = corpus_110(raw, folder)
        print(folder, len(r), flush=True)
        rows += r
    df = pd.DataFrame(rows)
    df.to_csv(out / "score_metrics_110_by_movement.csv", index=False, encoding="utf-8", lineterminator="\n")
    return df


if __name__ == "__main__":
    main()
