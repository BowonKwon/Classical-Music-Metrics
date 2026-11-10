"""1.12: self-similarity matrices of sample movements (design 72 §3 C), with the window series of §3 D.

For each measure (mc, score order, repeats not unfolded) the duration-weighted pitch-class distribution of the
notes that start in it (same preprocessing as key_clarity). S[i, j] = cosine of the vectors of measures i and j;
a measure without notes has no value. Pitch classes are absolute, so a theme that returns in another key is
less similar to its first appearance than one that returns in the same key.

Movements (fixed before computing): the 1.9 key-map movements (per collection the movement whose number of key
changes is closest to the collection median, the most, the fewest), and by the same rule for the three
collections with harmony labels that have no key map (Bach suites, Bach solo, J. C. Bach). No chorales.

Outputs: data/derived/ssm_112_index.csv and data/derived/ssm_112/{corpus}__{piece}.json with
  n            number of measures
  mn           measure number (as printed) of each mc
  empty        indices of measures without notes
  upper        the strict upper triangle row by row, two hex digits per cell = round(255 * S)
  windows      [first mc, note density, chromatic ratio or null] for each complete 4-bar window
  keys         local-key stretches as in the 1.9 key maps: [first mn, last mn, key signature minus the home
               key's, minor (0/1), DCML local-key label]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import keymaps_19 as km  # noqa: E402
import score_metrics as sm  # noqa: E402
import score_metrics_112 as s112  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXTRA = ["bach_en_fr_suites", "bach_solo", "jc_bach_sonatas"]
LEVELS = 255


def chosen(derived: Path) -> list[tuple[str, str, str]]:
    kmaps = pd.read_csv(derived / "keymaps_19.csv")[["corpus", "piece_id", "role"]].drop_duplicates()
    out = [(r.corpus, r.piece_id, r.role) for r in kmaps.itertuples()]
    s = pd.read_csv(derived / "score_metrics_19_by_movement.csv")
    for corpus in EXTRA:
        out += [(corpus, p, role) for role, p in km.choose(s[s.corpus == corpus])]
    return out


def bar_vectors(on: pd.DataFrame, n_bars: int) -> np.ndarray:
    v = np.zeros((n_bars, 12))
    np.add.at(v, (on["mc"].to_numpy().astype(int) - 1, (on["midi"].to_numpy() % 12).astype(int)), on["dur_merged"].to_numpy(dtype=float))
    return v


def cosine_matrix(v: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(v, axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        u = v / norm[:, None]
    s = u @ u.T
    s[norm == 0, :] = np.nan
    s[:, norm == 0] = np.nan
    return s


def encode_upper(s: np.ndarray) -> str:
    n = len(s)
    q = np.rint(np.nan_to_num(s, nan=0.0).clip(0, 1) * LEVELS).astype(int)
    return "".join("".join(format(x, "02x") for x in q[i, i + 1:]) for i in range(n - 1))


def piece(raw: Path, corpus: str, piece_id: str) -> dict:
    base = raw / corpus
    measures = pd.read_csv(base / "measures" / f"{piece_id}.measures.tsv", sep="\t", dtype=str)
    measures["mc"] = measures["mc"].astype(int)
    npath = base / "notes" / f"{piece_id}.notes.tsv"
    notes = sm.load_dcml_notes(npath, measures)
    notes["mc"] = pd.read_csv(npath, sep="\t", dtype=str, usecols=["mc"])["mc"].astype(int).to_numpy()
    df = sm.merge_ties(notes[~notes["grace"]].copy())
    on = df[~df["attached"] & ~df["tied_cont"]]
    n = int(measures["mc"].max())
    s = cosine_matrix(bar_vectors(on, n))
    empty = [int(i) for i in np.where(np.isnan(np.diag(s)))[0]]
    win = [[int(mc), round(d, 4), None if np.isnan(c) else round(c, 4)] for mc, d, c in s112.window_series(on, measures)]
    mn = measures.sort_values("mc")["mn"].astype(int).tolist()
    keys = []
    hpath = base / "harmonies" / f"{piece_id}.harmonies.tsv"
    if hpath.exists():  # local-key stretches as in the 1.9 key maps: [first mn, last mn, signature minus the home key's, minor?, label]
        meta = pd.read_csv(base / "metadata.tsv", sep="\t", dtype=str).set_index("piece")
        segs = km.segments(pd.read_csv(hpath, sep="\t", dtype=str), float(meta.loc[piece_id, "length_qb"]), int(meta.loc[piece_id, "last_mn"]))
        keys = [[int(g["mn_start"]), int(g["mn_end"]), int(g["sig_rel"]), int(g["minor"]), g["localkey"]] for g in segs]
    return dict(corpus=corpus, piece_id=piece_id, n=n, mn=mn, empty=empty, upper=encode_upper(s), windows=win, keys=keys)


def main(raw: Path = ROOT / "data/raw", out: Path = ROOT / "data/derived") -> pd.DataFrame:
    (out / "ssm_112").mkdir(exist_ok=True)
    rows = []
    for corpus, piece_id, role in chosen(out):
        d = piece(raw, corpus, piece_id)
        d["role"] = role
        (out / "ssm_112" / f"{corpus}__{piece_id}.json").write_text(json.dumps(d, separators=(",", ":")), encoding="utf-8", newline="\n")
        rows.append(dict(corpus=corpus, piece_id=piece_id, role=role, n_measures=d["n"], n_empty=len(d["empty"]), n_windows=len(d["windows"])))
        print(corpus, piece_id, d["n"], flush=True)
    idx = pd.DataFrame(rows)
    idx.to_csv(out / "ssm_112_index.csv", index=False, encoding="utf-8", lineterminator="\n")
    return idx


if __name__ == "__main__":
    main()
