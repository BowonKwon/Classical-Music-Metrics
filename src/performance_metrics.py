"""Performance metrics from the ASAP dataset (Foscarin et al., ISMIR 2020;
CC BY-NC-SA 4.0): Bach and Beethoven piano performances with beat annotations.

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

Only performances whose beat count matches the score (score_and_performance_aligned)
are used for tempo; others are kept with a flag.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import mido
import numpy as np
import pandas as pd


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/derived")
    ap.add_argument("--composers", default="Bach,Beethoven")
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
    df.to_csv(out / "asap_performance_metrics.csv", index=False, encoding="utf-8")

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
    piece.to_csv(out / "asap_piece_summary.csv", index=False, encoding="utf-8")
    print(df.groupby("composer").size(), "\n", ok.groupby("composer").size())
    print(piece.groupby("composer")[["tempo_cv_across_performers", "ibi_cv_median", "local_tempo_change_median", "velocity_sd_median"]].median())
    print(piece.sort_values("n_performances", ascending=False).head(10).to_string())


if __name__ == "__main__":
    main()
