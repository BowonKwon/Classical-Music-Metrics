"""1.9: four new score metrics for every DCML collection on the site.

key_clarity               max over the 24 keys of the Pearson correlation between the movement's
                          duration-weighted pitch-class distribution and the Krumhansl-Kessler (1982)
                          probe-tone profile (Krumhansl-Schmuckler key finding). Notes only.
fifth_root_motion_ratio   among successive chord labels in the same local key whose root changes, the share
                          whose root falls a fifth (one step down the line of fifths: V -> I, ii -> V, V/V -> V).
key_change_distance_median  at each change of local key, the change in key signature (sharps minus flats,
                          enharmonically folded to 0..6); median over the movement. Blank if no change.
outside_5oct_ratio        share of notes below F1 (MIDI 29) or above F6 (MIDI 89). Keyboard collections only.

Notes go through the same preprocessing as score_metrics.note_metrics (grace notes dropped, ties merged,
onsets only). Output: data/derived/score_metrics_19_by_movement.csv keyed on (corpus, piece_id); nothing in
the earlier tables changes.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_metrics as sm  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Krumhansl & Kessler (1982) probe-tone ratings, tonic first (C major / C minor contexts)
KK_MAJOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
KK_MINOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
LOW, HIGH = 29, 89  # F1, F6

# (folder, keyboard?) for every collection that gets the new metrics
COLLECTIONS_19 = {
    # earlier tables (score_metrics.DCML_CORPORA)
    "bach_chorales": False, "bach_en_fr_suites": True, "bach_solo": False, "ABC": False,
    "beethoven_piano_sonatas": True, "mozart_piano_sonatas": True,
    # 1.8 sonatas
    "scarlatti_sonatas": True, "wf_bach_sonatas": True, "cpe_bach_keyboard": True, "jc_bach_sonatas": True,
    "kozeluh_sonatas": True,
    # 1.9
    "chopin_mazurkas": True, "grieg_lyric_pieces": True, "schumann_kinderszenen": True, "tchaikovsky_seasons": True,
    "liszt_pelerinage": True, "dvorak_silhouettes": True, "medtner_tales": True,
    "mendelssohn_quartets": False, "pleyel_quartets": False,
}

# scale degree -> position on the line of fifths from the tonic; minor follows the natural minor scale (DCML standard)
DEG_MAJOR = {1: 0, 2: 2, 3: 4, 4: -1, 5: 1, 6: 3, 7: 5}
DEG_MINOR = {1: 0, 2: 2, 3: -3, 4: -1, 5: 1, 6: -4, 7: -2}
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7}
_NUM = re.compile(r"^(b*|#*)(VII|VI|V|IV|III|II|I|vii|vi|v|iv|iii|ii|i)$")


def key_clarity(on: pd.DataFrame) -> float:
    w = np.zeros(12)
    np.add.at(w, (on["midi"].to_numpy() % 12).astype(int), on["dur_merged"].to_numpy(dtype=float))
    if w.sum() <= 0 or np.ptp(w) == 0:
        return float("nan")
    best = -1.0
    for prof in (KK_MAJOR, KK_MINOR):
        for t in range(12):
            best = max(best, float(np.corrcoef(w, np.roll(prof, t))[0, 1]))
    return best


def key_fifths(numeral: str, minor_context: bool) -> tuple[int, bool] | None:
    """Tonic of a local-key numeral on the line of fifths (relative to the global tonic) and whether it is minor.
    'vi/V' = vi of the key of V."""
    parts = str(numeral).split("/")
    base, ctx_minor = 0, minor_context
    for p in reversed(parts[1:]):  # innermost reference last: a/b/c = a of (b of c)
        r = key_fifths(p, ctx_minor)
        if r is None:
            return None
        base, ctx_minor = base + r[0], r[1]
    m = _NUM.match(parts[0])
    if not m:
        return None
    acc, rn = m.groups()
    deg = ROMAN[rn.upper()]
    f = (DEG_MINOR if ctx_minor else DEG_MAJOR)[deg] + 7 * (acc.count("#") - acc.count("b"))
    return base + f, rn.islower()


def harmony_19(h: pd.DataFrame) -> dict:
    out: dict = {}
    if "globalkey" not in h or "localkey" not in h:
        return out
    gk = h["globalkey"].dropna()
    gminor = bool(len(gk)) and str(gk.iloc[0])[:1].islower()
    # key changes (on every row: local-key changes can sit on rows without a chord)
    seq = h["localkey"].dropna().astype(str)
    seq = seq[seq != seq.shift()]
    sig = []
    for lk in seq:
        r = key_fifths(lk, gminor)
        sig.append(None if r is None else r[0] - 3 * int(r[1]))
    d = []
    for a, b in zip(sig, sig[1:]):
        if a is None or b is None:
            continue
        x = abs(b - a) % 12
        d.append(min(x, 12 - x))
    out["n_key_changes_19"] = len(d)
    if d:
        out["key_change_distance_median"] = float(np.median(d))
    # root motion between successive chord labels in the same local key
    c = h[h["chord"].notna() & (h["chord"] != "") & h["root"].notna()].copy()
    if len(c) >= 2:
        root = pd.to_numeric(c["root"], errors="coerce").to_numpy()
        lk = c["localkey"].astype(str).to_numpy()
        same = lk[1:] == lk[:-1]
        dr = root[1:] - root[:-1]
        ok = same & ~np.isnan(dr) & (dr != 0)
        out["n_root_changes"] = int(ok.sum())
        if ok.sum() > 0:
            out["fifth_root_motion_ratio"] = float((dr[ok] == -1).sum() / ok.sum())
    return out


def note_19(notes: pd.DataFrame, keyboard: bool) -> dict:
    df = sm.merge_ties(notes[~notes["grace"]].copy())
    snd = df[~df["attached"]]
    on = snd[~snd["tied_cont"]]
    out: dict = {}
    if len(on) == 0:
        return out
    out["key_clarity"] = key_clarity(on)
    if keyboard:
        out["outside_5oct_ratio"] = float(((on["midi"] < LOW) | (on["midi"] > HIGH)).mean())
    return out


def corpus_19(raw: Path, folder: str, keyboard: bool) -> list[dict]:
    base = raw / folder
    meta = pd.read_csv(base / "metadata.tsv", sep="\t", dtype=str)
    rows = []
    for piece in meta["piece"]:
        npath = base / "notes" / f"{piece}.notes.tsv"
        if not npath.exists():
            continue
        measures = pd.read_csv(base / "measures" / f"{piece}.measures.tsv", sep="\t", dtype=str)
        measures["mc"] = measures["mc"].astype(int)
        r = {"corpus": folder, "piece_id": piece}
        r.update(note_19(sm.load_dcml_notes(npath, measures), keyboard))
        hpath = base / "harmonies" / f"{piece}.harmonies.tsv"
        if hpath.exists():
            r.update(harmony_19(pd.read_csv(hpath, sep="\t", dtype=str)))
        rows.append(r)
    return rows


def main(raw: Path = ROOT / "data/raw", out: Path = ROOT / "data/derived") -> pd.DataFrame:
    rows = []
    for folder, kb in COLLECTIONS_19.items():
        r = corpus_19(raw, folder, kb)
        print(folder, len(r))
        rows += r
    df = pd.DataFrame(rows)
    df.to_csv(out / "score_metrics_19_by_movement.csv", index=False, encoding="utf-8", lineterminator="\n")
    return df


if __name__ == "__main__":
    main()
