"""Performance metrics from the ASAP dataset (Foscarin et al., ISMIR 2020;
CC BY-NC-SA 4.0): piano performances with beat annotations.

Per performance (one MIDI file):
  duration_s            last annotated beat minus first annotated beat
  n_beats               number of annotated beats (b, db; bR excluded)
  tempo_mean_bpm        60 / mean inter-beat interval (IBI)
  tempo_median_bpm      60 / median IBI
  ibi_cv                sd(IBI) / mean(IBI) — global tempo variability
  local_tempo_change    median |log2(IBI_i / IBI_{i-1})| — beat-to-beat rubato
  tempo_drift           log2(tempo of last quarter / tempo of first quarter)
  velocity_mean/sd      MIDI note-on velocity statistics (0-127)
  velocity_range_p95_p5 dynamic range
  n_notes               note-on count in the performance MIDI

Per piece: number of performances and the across-performer spread of mean
tempo (coefficient of variation) and of duration.

Per-performance rows are computed for every performance and carry the `aligned`
flag (score_and_performance_aligned). The per-piece summary keeps only aligned
performances. Composers: Bach, Beethoven, Mozart (Mozart added in 1.1).

Pedals (1.4), per performance MIDI, in asap_pedal.csv / asap_pedal_summary.csv:
  span_s              first note-on to last note-off, in seconds (tempo map applied)
  sustain_ratio       share of the span with the damper pedal down: CC64 value >= 64
                      (the MIDI convention for on/off). The recordings carry continuous CC64
                      values (half-pedalling), so sustain_ratio_any (value > 0) is kept as well.
  soft_used           True if CC67 (una corda) reaches 64 or more anywhere in the span
  soft_ratio          share of the span with CC67 >= 64
The pedal is taken as up before its first message in the file: ASAP cuts each performance
out of a longer MAESTRO recording, so a pedal already held at the cut is not seen. CC
messages of all channels are read as one pedal (the files use channel 0). Every performance
of the three composers is used (beat alignment is not needed for pedals). The recordings are
competition performances (International Piano-e-Competition, via MAESTRO) captured as MIDI
by the piano itself.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import mido
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent  # repository root; default paths do not depend on the working directory


def beat_times(ann_path: Path) -> np.ndarray:
    t = []
    for line in ann_path.read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        label = parts[2].split(",")[0]
        if label in ("b", "db"):
            t.append(float(parts[0]))
    return np.array(sorted(t))


def midi_velocities(path: Path) -> np.ndarray:
    try:
        m = mido.MidiFile(str(path))
    except Exception:
        return np.array([])
    v = [msg.velocity for tr in m.tracks for msg in tr if msg.type == "note_on" and msg.velocity > 0]
    return np.array(v)


PEDAL_ON = 64


def midi_events(path: Path):
    """(note span (first on, last off) in seconds, {64: [(t, value)], 67: [...]}) or None if the file cannot be read."""
    try:
        m = mido.MidiFile(str(path))
    except Exception:
        return None
    t, first_on, last_off, cc = 0.0, None, None, {64: [], 67: []}
    for msg in m:  # merged tracks; msg.time is seconds since the previous message
        t += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            first_on = t if first_on is None else first_on
            last_off = t if last_off is None else max(last_off, t)
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            last_off = t if last_off is None else max(last_off, t)
        elif msg.type == "control_change" and msg.control in cc:
            cc[msg.control].append((t, msg.value))
    return (first_on, last_off), cc


def time_down(events: list, span: tuple, on=lambda v: v >= PEDAL_ON) -> float:
    """Seconds inside span during which the pedal counts as down. Up before the first event."""
    a, b = span
    if a is None or b is None or b <= a:
        return float("nan")
    total, state, t0 = 0.0, False, a
    for t, v in sorted(events, key=lambda e: e[0]) + [(math.inf, None)]:
        lo, hi = max(t0, a), min(t, b)
        if state and hi > lo:
            total += hi - lo
        if v is None:
            break
        state, t0 = on(v), t
    return total


def pedal_metrics(path: Path) -> dict:
    ev = midi_events(path)
    if ev is None:
        return {}
    (a, b), cc = ev
    if a is None or b is None or b <= a:
        return {"span_s": float("nan")}
    span = b - a
    soft = time_down(cc[67], (a, b))
    return {
        "span_s": span,
        "n_cc64": len(cc[64]),
        "n_cc67": len(cc[67]),
        "sustain_ratio": time_down(cc[64], (a, b)) / span,
        "sustain_ratio_any": time_down(cc[64], (a, b), on=lambda v: v > 0) / span,
        "soft_used": bool(soft > 0),
        "soft_ratio": soft / span,
    }


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    """95% Wilson score interval for a proportion k/n."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    c = z * z / n
    mid = (p + c / 2) / (1 + c)
    half = z / (1 + c) * math.sqrt(p * (1 - p) / n + c / (4 * n))
    return (mid - half, mid + half)


def recording_level(ped: pd.DataFrame) -> pd.DataFrame:
    """1.4 (owner decision 2026-11-04): ASAP cuts some MAESTRO recordings into several pieces (start/end in
    metadata.csv). Count each recording once: pedal-down time and span are summed over its pieces, and the soft
    pedal counts as used if any piece uses it. Pieces without a MAESTRO path are recordings on their own."""
    p = ped.assign(_sus=ped["sustain_ratio"] * ped["span_s"], _any=ped["sustain_ratio_any"] * ped["span_s"],
                   _soft=ped["soft_ratio"] * ped["span_s"])
    g = p.groupby("recording", sort=True)
    rec = pd.DataFrame({"composer": g["composer"].first(), "n_pieces_in_recording": g.size(), "span_s": g["span_s"].sum(),
                        "soft_used": g["soft_used"].any()})
    rec["sustain_ratio"] = g["_sus"].sum() / rec["span_s"]
    rec["sustain_ratio_any"] = g["_any"].sum() / rec["span_s"]
    rec["soft_ratio"] = g["_soft"].sum() / rec["span_s"]
    return rec.reset_index()


def pedal_tables(raw: Path, meta: pd.DataFrame, ann: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for _, r in meta.iterrows():
        mp = r.get("maestro_midi_performance")
        row = {"composer": r["composer"], "title": r["title"], "performance": Path(r["midi_performance"]).stem,
               "recording": mp if isinstance(mp, str) and mp else r["midi_performance"],
               "aligned": ann.get(r["midi_performance"], {}).get("score_and_performance_aligned")}
        row.update(pedal_metrics(raw / r["midi_performance"]))
        rows.append(row)
    ped = pd.DataFrame(rows)
    out = []
    pieces = ped.dropna(subset=["sustain_ratio"])
    ok = recording_level(pieces)
    for comp, g in [(c, ok[ok["composer"] == c]) for c in sorted(ok["composer"].unique())] + [("all", ok)]:
        k, n = int(g["soft_used"].sum()), len(g)
        lo, hi = wilson(k, n)
        gp = pieces if comp == "all" else pieces[pieces["composer"] == comp]
        out.append({"composer": comp, "n_performances": n, "n_asap_files": len(gp), "n_pieces": gp["title"].nunique(),
                    "sustain_ratio_median": g["sustain_ratio"].median(), "sustain_ratio_q1": g["sustain_ratio"].quantile(.25),
                    "sustain_ratio_q3": g["sustain_ratio"].quantile(.75), "sustain_ratio_any_median": g["sustain_ratio_any"].median(),
                    "soft_used_n": k, "soft_used_share": k / n if n else float("nan"), "soft_used_ci95_low": lo, "soft_used_ci95_high": hi,
                    "soft_ratio_median_when_used": g.loc[g["soft_used"], "soft_ratio"].median()})
    return ped, pd.DataFrame(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data/raw"))
    ap.add_argument("--out", default=str(ROOT / "data/derived"))
    ap.add_argument("--composers", default="Bach,Beethoven,Mozart")
    a = ap.parse_args()
    raw, out = Path(a.raw) / "asap-dataset", Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    comps = set(a.composers.split(","))

    meta = pd.read_csv(raw / "metadata.csv")
    ann = json.load(open(raw / "asap_annotations.json", encoding="utf-8"))
    rows = []
    for _, r in meta[meta["composer"].isin(comps)].iterrows():
        bt = beat_times(raw / r["performance_annotations"])
        aligned = ann.get(r["midi_performance"], {}).get("score_and_performance_aligned")
        row = {
            "composer": r["composer"],
            "title": r["title"],
            "folder": r["folder"],
            "performance": Path(r["midi_performance"]).stem,
            "has_audio": isinstance(r["audio_performance"], str),
            "aligned": aligned,
            "n_beats": int(len(bt)),
        }
        if len(bt) >= 8:
            ibi = np.diff(bt)
            ibi = ibi[ibi > 0]
            row["duration_s"] = float(bt[-1] - bt[0])
            row["tempo_mean_bpm"] = 60 / ibi.mean()
            row["tempo_median_bpm"] = 60 / np.median(ibi)
            row["ibi_cv"] = float(ibi.std() / ibi.mean())
            lr = np.abs(np.log2(ibi[1:] / ibi[:-1]))
            row["local_tempo_change"] = float(np.median(lr))
            q = max(len(ibi) // 4, 1)
            row["tempo_drift_log2"] = float(math.log2(ibi[:q].mean() / ibi[-q:].mean()))
        v = midi_velocities(raw / r["midi_performance"])
        if len(v):
            row["n_notes"] = int(len(v))
            row["velocity_mean"] = float(v.mean())
            row["velocity_sd"] = float(v.std())
            row["velocity_range_p95_p5"] = float(np.percentile(v, 95) - np.percentile(v, 5))
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(out / "asap_performance_metrics.csv", index=False, encoding="utf-8", lineterminator="\n")

    ok = df[df["aligned"] == True].dropna(subset=["tempo_mean_bpm"])  # noqa: E712
    piece = ok.groupby(["composer", "title"]).agg(
        n_performances=("performance", "size"),
        tempo_mean_bpm_median=("tempo_mean_bpm", "median"),
        tempo_cv_across_performers=("tempo_mean_bpm", lambda x: x.std() / x.mean() if len(x) > 1 else np.nan),
        tempo_min_bpm=("tempo_mean_bpm", "min"),
        tempo_max_bpm=("tempo_mean_bpm", "max"),
        duration_median_s=("duration_s", "median"),
        duration_cv=("duration_s", lambda x: x.std() / x.mean() if len(x) > 1 else np.nan),
        ibi_cv_median=("ibi_cv", "median"),
        local_tempo_change_median=("local_tempo_change", "median"),
        velocity_sd_median=("velocity_sd", "median"),
    ).reset_index()
    piece.to_csv(out / "asap_piece_summary.csv", index=False, encoding="utf-8", lineterminator="\n")
    ped, ped_sum = pedal_tables(raw, meta[meta["composer"].isin(comps)], ann)
    ped.to_csv(out / "asap_pedal.csv", index=False, encoding="utf-8", lineterminator="\n")
    ped_sum.to_csv(out / "asap_pedal_summary.csv", index=False, encoding="utf-8", lineterminator="\n")
    recording_level(ped.dropna(subset=["sustain_ratio"])).to_csv(out / "asap_pedal_recordings.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(ped_sum.to_string())
    print(df.groupby("composer").size(), "\n", ok.groupby("composer").size())
    print(piece.groupby("composer")[["tempo_cv_across_performers", "ibi_cv_median", "local_tempo_change_median", "velocity_sd_median"]].median())
    print(piece.sort_values("n_performances", ascending=False).head(10).to_string())


if __name__ == "__main__":
    main()
