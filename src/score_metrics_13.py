"""Score metrics new in 1.3 (P2), computed per movement from the DCML corpora.

Writes data/derived/score_metrics_13_by_movement.csv keyed by (corpus, piece_id); build_site merges it
into the 1.0-1.2 score table. Reuses the loaders and note handling of score_metrics.py so the notes
are the same ones the earlier metrics see (grace notes dropped, ties merged).

Harmony (DCML harmonies.tsv; annotated corpora only):
  dim7_ratio            chord_type == 'o7'                          / chord labels
  neapolitan_ratio      numeral == 'bII'                            / chord labels
  aug6_ratio            chord_type in {Ger, It, Fr}                 / chord labels
  predominant_chromatic_ratio  neapolitan_ratio + aug6_ratio (published; each alone is mostly 0)
  pedal_ratio           pedal column filled                         / chord labels
  phrase_len_median     median gap, in bars (mn), between consecutive phrase-end marks
                        ('}' , '}{' and the older '\\'); needs at least 3 phrase ends
  phrase_4_8_ratio      share of those gaps equal to 4 or 8 bars
Notes (all corpora):
  npvi_top              nPVI of top-line inter-onset intervals: 100/(m-1) * sum |d_k - d_k+1| / ((d_k + d_k+1)/2)
  post_leap_reversal    after a top-line leap (>= 3 semitones), share of next moves in the opposite direction
                        (repeated notes skipped); post_step_reversal is the same after a step (1-2) - baseline
  beat_crossing_ratio   share of onsets that start off the beat and last past the next beat
  motif_repeat_ratio    share of top-line signed-interval 4-grams that occur at least twice in the movement
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import score_metrics as sm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent  # repository root; default paths do not depend on the working directory

PHRASE_END = {"}", "}{", "\\\\", "\\"}


def harmony_13(h: pd.DataFrame) -> dict:
    out: dict = {}
    h_all = h  # phrase-end marks can sit on rows without a chord symbol; read them from every row
    h = h[h["chord"].notna() & (h["chord"] != "")].copy()
    if len(h) == 0:
        return out
    ct = h["chord_type"].fillna("") if "chord_type" in h else pd.Series("", index=h.index)
    out["dim7_ratio"] = float((ct == "o7").mean())
    out["neapolitan_ratio"] = float((h["numeral"].fillna("") == "bII").mean())
    out["aug6_ratio"] = float(ct.isin(["Ger", "It", "Fr"]).mean())
    out["predominant_chromatic_ratio"] = out["neapolitan_ratio"] + out["aug6_ratio"]  # each alone is mostly 0 per movement
    out["pedal_ratio"] = float(h["pedal"].notna().mean()) if "pedal" in h else float("nan")
    if "phraseend" in h_all:
        ends = h_all.loc[h_all["phraseend"].isin(PHRASE_END), "mn"].astype(int).tolist()
        # zero or negative gaps come from bar numbering (two marks in one bar, first/second endings that
        # reuse bar numbers); they are left out of both the median and the 4/8 share
        gaps = [b - a for a, b in zip(ends, ends[1:]) if b - a > 0]
        out["n_phrase_ends"] = len(ends)
        if len(ends) >= 3 and gaps:
            out["phrase_len_median"] = float(pd.Series(gaps).median())
            out["phrase_4_8_ratio"] = float(sum(g in (4, 8) for g in gaps) / len(gaps))
    return out


def top_line_with_onsets(snd: pd.DataFrame) -> pd.Series:
    return sm.top_line(snd)


def note_13(df: pd.DataFrame) -> dict:
    out: dict = {}
    df = sm.merge_ties(df[~df["grace"]].copy())
    snd = df[~df["attached"]].copy()
    snd["is_onset"] = ~snd["tied_cont"]
    on = snd[snd["is_onset"]]
    if len(on) == 0:
        return out
    # beat crossing: starts off the beat, lasts past the next beat (within the bar as notated)
    def crosses(r) -> bool:
        bu, pos = r["beat_unit"], r["mc_onset"]
        if pos % bu == 0:
            return False
        nxt = (pos // bu + 1) * bu
        return pos + Fraction(r["dur_merged"]).limit_denominator(64) / 4 > nxt
    out["beat_crossing_ratio"] = float(on.apply(crosses, axis=1).mean())

    top = sm.top_line(snd)
    if len(top) >= 3:
        ioi = pd.Series(top.index, dtype=float).diff().dropna()
        ioi = ioi[ioi > 0].tolist()
        if len(ioi) >= 2:
            s = sum(abs(a - b) / ((a + b) / 2) for a, b in zip(ioi, ioi[1:]))
            out["npvi_top"] = 100 * s / (len(ioi) - 1)
        iv = top.diff().dropna().tolist()
        mv = [x for x in iv if x != 0]  # repeated notes skipped
        after_leap = [(a, b) for a, b in zip(mv, mv[1:]) if abs(a) >= 3]
        after_step = [(a, b) for a, b in zip(mv, mv[1:]) if 1 <= abs(a) <= 2]
        if after_leap:
            out["n_leaps"] = len(after_leap)
            out["post_leap_reversal"] = sum(a * b < 0 for a, b in after_leap) / len(after_leap)
        if after_step:
            out["post_step_reversal"] = sum(a * b < 0 for a, b in after_step) / len(after_step)
        grams = [tuple(iv[i:i + 4]) for i in range(len(iv) - 3)]
        if grams:
            c = Counter(grams)
            out["motif_repeat_ratio"] = sum(n for n in c.values() if n >= 2) / len(grams)
    return out


def main(raw: Path = (ROOT / "data/raw"), out: Path = (ROOT / "data/derived")):
    rows = []
    for folder, comp, coll, lic in sm.DCML_CORPORA:
        base = raw / folder
        meta = pd.read_csv(base / "metadata.tsv", sep="\t", dtype=str)
        for _, m in meta.iterrows():
            piece = m["piece"] if "piece" in m else m["fname"]
            npath = base / "notes" / f"{piece}.notes.tsv"
            mpath = base / "measures" / f"{piece}.measures.tsv"
            if not npath.exists() or not mpath.exists():
                continue
            measures = pd.read_csv(mpath, sep="\t", dtype=str)
            measures["mc"] = measures["mc"].astype(int)
            notes = sm.load_dcml_notes(npath, measures)
            row = {"corpus": folder, "piece_id": piece, "license": lic}
            row.update(note_13(notes))
            hpath = base / "harmonies" / f"{piece}.harmonies.tsv"
            if hpath.exists():
                h = pd.read_csv(hpath, sep="\t", dtype=str)
                row.update(harmony_13(h))
            rows.append(row)
        print(folder, sum(r["corpus"] == folder for r in rows))
    df = pd.DataFrame(rows)
    df.to_csv(out / "score_metrics_13_by_movement.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(df.describe().T.round(3).to_string())


if __name__ == "__main__":
    main()
