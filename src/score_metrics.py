"""Score-based metrics from DCML corpora (TSV tables produced by ms3) and
Humdrum **kern files (via music21).

Every metric is defined once, in `note_metrics` / `harmony_metrics`, and the
same functions run over every corpus so that Bach and Beethoven are measured
with identical code.

Usage:
  python src/score_metrics.py --raw data/raw --out data/derived
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from fractions import Fraction
from pathlib import Path

import pandas as pd

# --------------------------------------------------------------------------
# Corpus registry: (folder, composer, collection label, license)
# --------------------------------------------------------------------------
DCML_CORPORA = [
    ("bach_chorales", "Bach", "chorales", "CC0-1.0"),
    ("bach_en_fr_suites", "Bach", "english_french_suites", "CC-BY-NC-SA-4.0"),
    ("bach_solo", "Bach", "solo_violin_cello_flute", "CC-BY-NC-SA-4.0"),
    ("ABC", "Beethoven", "string_quartets", "CC-BY-NC-SA-4.0"),
    ("beethoven_piano_sonatas", "Beethoven", "piano_sonatas", "CC-BY-NC-SA-4.0"),
]
KERN_CORPORA = [
    ("bach-370-chorales", "Bach", "chorales_kern370", "CC-BY-NC-SA-4.0"),
]


def frac(x) -> Fraction:
    if isinstance(x, Fraction):
        return x
    if pd.isna(x):
        return Fraction(0)
    s = str(x)
    if "/" in s:
        n, d = s.split("/")
        return Fraction(int(n), int(d))
    return Fraction(s)


def entropy(counter: Counter) -> float:
    n = sum(counter.values())
    if n == 0:
        return float("nan")
    return -sum((c / n) * math.log2(c / n) for c in counter.values())


# --------------------------------------------------------------------------
# Note-level metrics. Input: DataFrame with columns
#   onset_qb (float), dur_qb (float), midi (int), tpc (int, fifths, C=0),
#   staff (int), voice (int), keysig (int, sharps + / flats -),
#   beat_unit (Fraction, e.g. 1/4), mc_onset (Fraction within measure),
#   grace (bool), tied_cont (bool: continuation of a tie, not a new onset)
# --------------------------------------------------------------------------
def merge_ties(df: pd.DataFrame) -> pd.DataFrame:
    """Attach tie-continuation fragments to the note they prolong.

    Returns the frame sorted by onset with two new columns:
      dur_merged  for onset rows, the full tied duration; for fragments, their own
      attached    True for a continuation fragment that was merged into an onset
    A fragment is attached to an onset note of the same MIDI pitch whose current
    end equals the fragment's onset (same staff and voice preferred). Fragments
    that cannot be attached stay as sounding, non-onset notes.
    """
    df = df.sort_values(["onset_qb", "staff", "voice"]).reset_index(drop=True)
    dur = df["dur_qb"].to_numpy(dtype=float).copy()
    end = df["onset_qb"].to_numpy(dtype=float) + dur
    attached = [False] * len(df)
    staff = df["staff"].to_numpy()
    voice = df["voice"].to_numpy()
    open_: dict = {}
    for i, (on, d, midi, st, vo, cont) in enumerate(zip(df["onset_qb"], df["dur_qb"], df["midi"], staff, voice, df["tied_cont"])):
        if cont:
            best = None
            for j in open_.get(midi, []):
                if abs(end[j] - on) < 1e-6:
                    if best is None or (staff[j] == st and voice[j] == vo):
                        best = j
            if best is not None:
                dur[best] += d
                end[best] += d
                attached[i] = True
                continue
        lst = open_.setdefault(midi, [])
        lst[:] = [j for j in lst if end[j] >= on - 1e-6]
        lst.append(i)
    df["dur_merged"] = dur
    df["attached"] = attached
    return df


def top_line(snd: pd.DataFrame) -> pd.Series:
    """Highest sounding pitch at each onset position, kept only where that
    highest note itself starts there. `snd` holds every sounding note (onsets
    with merged durations plus unattached tie fragments) with `is_onset`."""
    import heapq

    notes = snd[["onset_qb", "dur_merged", "midi", "is_onset"]].sort_values("onset_qb").to_numpy()
    heap: list = []  # (-midi, end, onset, is_onset)
    seq, idx = [], []
    i, n = 0, len(notes)
    positions = sorted(set(notes[:, 0].tolist()))
    for t in positions:
        while i < n and notes[i, 0] <= t:
            o, d, m, iso = notes[i]
            heapq.heappush(heap, (-m, o + d, o, bool(iso)))
            i += 1
        while heap and heap[0][1] <= t + 1e-9:
            heapq.heappop(heap)
        if heap and heap[0][3] and abs(heap[0][2] - t) < 1e-9:
            seq.append(-heap[0][0])
            idx.append(t)
    return pd.Series(seq, index=idx, dtype=float)


def note_metrics(df: pd.DataFrame, length_qb: float) -> dict:
    df = merge_ties(df[~df["grace"]].copy())
    snd = df[~df["attached"]].copy()  # every sounding note
    snd["is_onset"] = ~snd["tied_cont"]
    on = snd[snd["is_onset"]]  # real onsets, with tied durations merged
    out: dict = {}
    out["n_notes"] = int(len(on))
    out["n_tie_fragments"] = int(df["tied_cont"].sum())
    out["n_tie_fragments_unattached"] = int(snd["tied_cont"].sum())
    if len(on) == 0:
        return out
    out["n_staves"] = int(df["staff"].nunique())
    out["pitch_min_midi"] = int(on["midi"].min())
    out["pitch_max_midi"] = int(on["midi"].max())
    out["pitch_range_semitones"] = out["pitch_max_midi"] - out["pitch_min_midi"]
    out["pitch_mean_midi"] = float(on["midi"].mean())
    out["pitch_sd_midi"] = float(on["midi"].std(ddof=0))

    # chromatic ratio: tpc outside the diatonic set of the prevailing key signature
    # Diatonic tonal pitch classes for a signature with k sharps: k-1 .. k+5
    diat = (on["tpc"] >= on["keysig"] - 1) & (on["tpc"] <= on["keysig"] + 5)
    out["chromatic_ratio"] = float(1 - diat.mean())
    out["pitch_class_entropy"] = entropy(Counter((on["midi"] % 12).tolist()))
    out["tpc_vocabulary"] = int(on["tpc"].nunique())

    # rhythm (durations after tying)
    durs = Counter(on["dur_merged"].round(6).tolist())
    out["rhythm_entropy"] = entropy(durs)
    out["duration_vocabulary"] = len(durs)
    out["mean_duration_qb"] = float(on["dur_merged"].mean())
    on_beat = on.apply(lambda r: (r["mc_onset"] % r["beat_unit"]) == 0, axis=1)
    out["offbeat_onset_ratio"] = float(1 - on_beat.mean())

    # texture
    positions = on.groupby("onset_qb").size()
    out["n_onset_positions"] = int(len(positions))
    out["mean_simultaneity"] = float(positions.mean())
    out["notes_per_quarter"] = out["n_notes"] / length_qb if length_qb and length_qb > 0 else float("nan")

    # melody of the top line: at each onset position, the highest *sounding*
    # pitch (tied notes keep sounding for their full length); the position is
    # kept only when that highest note itself starts there.
    top = top_line(snd)
    if len(top) >= 2:
        iv = top.diff().dropna().abs()
        out["top_n_notes"] = int(len(top))
        out["top_mean_interval_semitones"] = float(iv.mean())
        out["top_leap_ratio"] = float((iv >= 3).mean())  # minor third or larger
        out["top_step_ratio"] = float(((iv >= 1) & (iv <= 2)).mean())
        out["top_repeat_ratio"] = float((iv == 0).mean())
        out["top_range_semitones"] = int(top.max() - top.min())
        d = top.diff().dropna()
        d = d[d != 0]
        out["top_direction_changes_per_note"] = (
            float(((d.shift() * d) < 0).sum() / len(d)) if len(d) else float("nan")
        )
    return out


# --------------------------------------------------------------------------
# Harmony metrics from DCML harmonies.tsv (DCML harmony annotation standard)
# --------------------------------------------------------------------------
SEVENTH_FIGS = {"7", "65", "43", "2", "42"}


def harmony_metrics(h: pd.DataFrame, n_measures: int, length_qb: float) -> dict:
    out: dict = {}
    h = h[h["chord"].notna() & (h["chord"] != "")].copy()
    out["n_chord_labels"] = int(len(h))
    if len(h) == 0 or n_measures == 0:
        return out
    out["chords_per_measure"] = len(h) / n_measures
    out["mean_chord_duration_qb"] = float(h["duration_qb"].astype(float).mean())
    out["chord_vocabulary"] = int(h["chord"].nunique())
    out["chord_vocabulary_per_100_labels"] = 100 * out["chord_vocabulary"] / len(h)
    numeral = h["numeral"].fillna("")
    out["chromatic_numeral_ratio"] = float(numeral.str.contains(r"[#b]").mean())
    out["applied_chord_ratio"] = float(h["relativeroot"].notna().mean())
    fig = h["figbass"].fillna("").astype(str)
    out["seventh_chord_ratio"] = float(fig.isin(SEVENTH_FIGS).mean())
    out["inversion_ratio"] = float(fig.isin({"6", "64", "65", "43", "2", "42"}).mean())
    lk = h["localkey"].fillna("")
    changes = (lk != lk.shift()).sum() - 1
    out["local_key_changes"] = int(max(changes, 0))
    out["local_key_changes_per_100_measures"] = 100 * out["local_key_changes"] / n_measures
    out["local_key_vocabulary"] = int(lk.nunique())
    # cadence labels exist only in corpora whose annotation version records them;
    # a corpus-wide absence is reported as NaN by the caller (see dcml_corpus)
    cad = h["cadence"].fillna("") if "cadence" in h else pd.Series([], dtype=str)
    n_cad = int((cad != "").sum())
    out["n_cadence_labels"] = n_cad
    out["cadences_per_100_measures"] = 100 * n_cad / n_measures
    out["pac_ratio_of_cadences"] = float((cad == "PAC").sum() / n_cad) if n_cad else float("nan")
    out["minor_local_key_ratio"] = float(h["localkey_is_minor"].astype(float).mean())
    return out


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------
def load_dcml_notes(path: Path, measures: pd.DataFrame) -> pd.DataFrame:
    n = pd.read_csv(path, sep="\t", dtype=str)
    keysig = measures.set_index("mc")["keysig"].astype(int)
    df = pd.DataFrame(
        {
            "onset_qb": n["quarterbeats"].map(lambda x: float(frac(x))),
            "dur_qb": n["duration_qb"].astype(float),
            "midi": n["midi"].astype(int),
            "tpc": n["tpc"].astype(int),
            "staff": n["staff"].astype(int),
            "voice": n["voice"].astype(int),
            "keysig": n["mc"].astype(int).map(keysig).fillna(0).astype(int),
            "beat_unit": n["timesig"].map(lambda t: Fraction(1, int(t.split("/")[1]))),
            "mc_onset": n["mc_onset"].map(frac),
            "grace": n["gracenote"].notna() if "gracenote" in n else False,
            # tied: 1 = tie starts, 0 = middle, -1 = tie end. Middle/end are continuations
            "tied_cont": n["tied"].isin(["0", "-1"]) if "tied" in n else False,
        }
    )
    return df


def dcml_corpus(raw: Path, folder: str, composer: str, collection: str, lic: str):
    base = raw / folder
    meta = pd.read_csv(base / "metadata.tsv", sep="\t", dtype=str)
    rows = []
    for _, m in meta.iterrows():
        piece = m["piece"]
        npath = base / "notes" / f"{piece}.notes.tsv"
        mpath = base / "measures" / f"{piece}.measures.tsv"
        if not npath.exists():
            continue
        measures = pd.read_csv(mpath, sep="\t", dtype=str)
        measures["mc"] = measures["mc"].astype(int)
        notes = load_dcml_notes(npath, measures)
        n_measures = int(m["last_mn"])
        row = {
            "corpus": folder,
            "composer": composer,
            "collection": collection,
            "piece_id": piece,
            "work": m.get("workTitle", ""),
            "work_number": m.get("workNumber", ""),
            "movement": m.get("movementNumber", ""),
            "movement_title": m.get("movementTitle", ""),
            "composed_start": m.get("composed_start", ""),
            "composed_end": m.get("composed_end", ""),
            "n_measures": n_measures,
            "length_qb": float(m["length_qb"]),
            "annotated_key": m.get("annotated_key", ""),
            "license": lic,
        }
        row.update(note_metrics(notes, float(m["length_qb"])))
        hpath = base / "harmonies" / f"{piece}.harmonies.tsv"
        if hpath.exists():
            h = pd.read_csv(hpath, sep="\t", dtype=str)
            row.update(harmony_metrics(h, n_measures, float(m["length_qb"])))
        rows.append(row)
    return rows


def kern_corpus(raw: Path, folder: str, composer: str, collection: str, lic: str):
    from music21 import converter, pitch as m21pitch

    def tpc_of(p: m21pitch.Pitch) -> int:
        steps = {"C": 0, "D": 2, "E": 4, "F": -1, "G": 1, "A": 3, "B": 5}
        alter = int(p.accidental.alter) if p.accidental else 0
        return steps[p.step] + 7 * alter

    rows = []
    for f in sorted((raw / folder / "kern").glob("*.krn")):
        try:
            s = converter.parse(str(f))
        except Exception as e:  # keep going, record failure
            rows.append({"corpus": folder, "piece_id": f.stem, "error": str(e)[:200]})
            continue
        meta = {}
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("!!!") and ":" in line:
                k, v = line[3:].split(":", 1)
                meta[k.strip()] = v.strip()
        recs = []
        parts = list(s.parts)
        for si, part in enumerate(parts, start=1):
            flat = part.flatten()
            ks_events = [(e.offset, e.sharps) for e in flat.getElementsByClass("KeySignature")]
            ts_events = [(e.offset, e) for e in flat.getElementsByClass("TimeSignature")]
            for n in flat.notes:
                pitches = n.pitches
                ks = 0
                for off, sh in ks_events:
                    if off <= n.offset:
                        ks = sh
                ts = None
                for off, t in ts_events:
                    if off <= n.offset:
                        ts = t
                beat_unit = Fraction(1, ts.denominator) if ts is not None else Fraction(1, 4)
                meas = n.getContextByClass("Measure")
                m_off = meas.offset if meas is not None else 0
                # offset within measure in whole-note units (ms3 convention)
                mc_onset = Fraction(n.offset - m_off).limit_denominator(64) / 4
                tie_cont = n.tie is not None and n.tie.type in ("continue", "stop")
                for p in pitches:
                    recs.append(
                        {
                            "onset_qb": float(n.offset),
                            "dur_qb": float(n.quarterLength),
                            "midi": int(p.midi),
                            "tpc": tpc_of(p),
                            "staff": si,
                            "voice": 1,
                            "keysig": ks,
                            "beat_unit": beat_unit,
                            "mc_onset": mc_onset,
                            "grace": n.duration.isGrace,
                            "tied_cont": tie_cont,
                        }
                    )
        df = pd.DataFrame(recs)
        # music21 orders kern spines top part first, so staff 1 is already the top line
        n_measures = len(parts[0].getElementsByClass("Measure")) if parts else 0
        row = {
            "corpus": folder,
            "composer": composer,
            "collection": collection,
            "piece_id": f.stem,
            "work": meta.get("OTL@@DE", meta.get("OTL", "")),
            "work_number": meta.get("SCT", ""),
            "n_measures": n_measures,
            "length_qb": float(s.duration.quarterLength),
            "license": lic,
        }
        row.update(note_metrics(df, float(s.duration.quarterLength)))
        rows.append(row)
    return rows


def git_head(path: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/derived")
    ap.add_argument("--skip-kern", action="store_true")
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    rows, manifest = [], {}
    for folder, comp, coll, lic in DCML_CORPORA:
        r = dcml_corpus(raw, folder, comp, coll, lic)
        print(folder, len(r), "pieces")
        rows += r
        manifest[folder] = {"git_head": git_head(raw / folder), "pieces": len(r), "license": lic}
    if not a.skip_kern:
        for folder, comp, coll, lic in KERN_CORPORA:
            r = kern_corpus(raw, folder, comp, coll, lic)
            print(folder, len(r), "pieces")
            rows += r
            manifest[folder] = {"git_head": git_head(raw / folder), "pieces": len(r), "license": lic}

    df = pd.DataFrame(rows)
    # corpora with no cadence labels at all: not annotated, not zero
    if "n_cadence_labels" in df:
        no_cad = df.groupby("corpus")["n_cadence_labels"].transform("sum") == 0
        df.loc[no_cad, ["cadences_per_100_measures", "pac_ratio_of_cadences"]] = float("nan")
    df.to_csv(out / "score_metrics_by_movement.csv", index=False, encoding="utf-8")
    (out / "score_metrics_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(df.groupby(["composer", "collection"]).size())


if __name__ == "__main__":
    main()
