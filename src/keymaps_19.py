"""1.9: key maps. For three movements per collection, the local-key segments as annotated by DCML.

A segment runs from the first label in a local key to the next change (or the end of the movement). Each
segment carries the key signature of its local key two ways:
  sig_abs  sharps (+) or flats (-) of the local key itself (a minor key takes its relative major's signature)
  sig_rel  sig_abs minus the signature of the movement's global key, so the home key is 0
Both are on the line of fifths, not folded: F-sharp major is +6, G-flat major -6, as written.

Movements chosen by a fixed rule (design 62): per collection, among movements with harmony labels, the one
whose number of key changes is closest to the collection median, the most, and the fewest (ties: piece id).

Output: data/derived/keymaps_19.csv
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_metrics_19 as s19  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

KEYBOARD = ["scarlatti_sonatas", "wf_bach_sonatas", "cpe_bach_keyboard", "mozart_piano_sonatas", "kozeluh_sonatas",
            "beethoven_piano_sonatas", "chopin_mazurkas", "schumann_kinderszenen", "liszt_pelerinage",
            "tchaikovsky_seasons", "dvorak_silhouettes", "grieg_lyric_pieces", "medtner_tales"]
QUARTETS = ["pleyel_quartets", "ABC", "mendelssohn_quartets"]
LETTER = {"F": -1, "C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5}


def tonic_fifths(key: str) -> tuple[int, bool]:
    """'c#' -> (7, True): C-sharp minor; 'Bb' -> (-2, False)."""
    k = str(key).strip()
    f = LETTER[k[0].upper()] + 7 * (k[1:].count("#") - k[1:].count("b"))
    return f, k[0].islower()


def segments(h: pd.DataFrame, length_qb: float, last_mn: int | None = None) -> list[dict]:
    g = h.dropna(subset=["localkey", "quarterbeats"]).copy()
    if g.empty:
        return []
    g["qb"] = g["quarterbeats"].map(lambda x: float(Fraction(str(x))))
    g = g.sort_values("qb", kind="mergesort")
    gk = str(h["globalkey"].dropna().iloc[0])
    gt, gmin = tonic_fifths(gk)
    gsig = gt - 3 * int(gmin)
    out = []
    lk = g["localkey"].astype(str).tolist()
    qb = g["qb"].tolist()
    mn = g["mn"].astype(int).tolist()
    # a change in the middle of a bar ends the previous segment in that bar, not the one before (Codex 61)
    onset0 = [Fraction(str(x)) == 0 for x in g["mn_onset"].fillna("0")] if "mn_onset" in g else [True] * len(g)
    last = int(last_mn) if last_mn is not None else int(max(mn))
    starts = [0] + [i for i in range(1, len(lk)) if lk[i] != lk[i - 1]]
    for j, i in enumerate(starts):
        end_i = starts[j + 1] if j + 1 < len(starts) else None
        r = s19.key_fifths(lk[i], gmin)
        if r is None:
            continue
        rel_t, minor = r
        sig_abs = gt + rel_t - 3 * int(minor)
        out.append(dict(start_qb=0.0 if j == 0 else qb[i], end_qb=qb[end_i] if end_i is not None else length_qb,
                        mn_start=mn[i], mn_end=(mn[end_i] - (1 if onset0[end_i] else 0)) if end_i is not None else last,
                        localkey=lk[i], tonic_abs=gt + rel_t, minor=bool(minor), sig_abs=sig_abs, sig_rel=sig_abs - gsig,
                        globalkey=gk))
    return out


def choose(s: pd.DataFrame) -> list[tuple[str, str]]:
    s = s.dropna(subset=["n_key_changes_19"]).sort_values("piece_id")
    if s.empty:
        return []
    med = s["n_key_changes_19"].median()
    rep = s.assign(d=(s["n_key_changes_19"] - med).abs()).sort_values(["d", "piece_id"]).iloc[0]["piece_id"]
    most = s.sort_values(["n_key_changes_19", "piece_id"], ascending=[False, True]).iloc[0]["piece_id"]
    least = s.sort_values(["n_key_changes_19", "piece_id"]).iloc[0]["piece_id"]
    out, seen = [], set()
    for role, p in (("typical", rep), ("most", most), ("fewest", least)):
        if p not in seen:
            out.append((role, p))
            seen.add(p)
    return out


def main(raw: Path = ROOT / "data/raw", out: Path = ROOT / "data/derived") -> pd.DataFrame:
    s = pd.read_csv(out / "score_metrics_19_by_movement.csv")
    rows = []
    for corpus in KEYBOARD + QUARTETS:
        meta = pd.read_csv(raw / corpus / "metadata.tsv", sep="\t", dtype=str).set_index("piece")
        for role, piece in choose(s[s.corpus == corpus]):
            h = pd.read_csv(raw / corpus / "harmonies" / f"{piece}.harmonies.tsv", sep="\t", dtype=str)
            for i, seg in enumerate(segments(h, float(meta.loc[piece, "length_qb"]), int(meta.loc[piece, "last_mn"]))):
                rows.append(dict(corpus=corpus, piece_id=piece, role=role, seg=i, length_qb=float(meta.loc[piece, "length_qb"]), **seg))
    df = pd.DataFrame(rows)
    df.to_csv(out / "keymaps_19.csv", index=False, encoding="utf-8", lineterminator="\n")
    return df


if __name__ == "__main__":
    main()
