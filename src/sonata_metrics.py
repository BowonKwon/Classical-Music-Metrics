"""Classical-era keyboard sonatas (1.8): the 39 score metrics for seven DCML collections in one table.

Mozart and Beethoven piano sonatas are recomputed here with the same functions as score_metrics.py /
score_metrics_13.py; tests check that their rows equal the existing by-movement tables, so this file
adds composers without changing any published number.

Output: data/derived/sonata_metrics_by_movement.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_metrics as sm  # noqa: E402
import score_metrics_13 as s13  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# (folder, composer, collection label, license, keyboard instrument named in the edition)
SONATA_CORPORA = [
    ("scarlatti_sonatas", "D. Scarlatti", "keyboard_sonatas", "CC-BY-NC-SA-4.0"),
    ("wf_bach_sonatas", "W. F. Bach", "keyboard_sonatas", "CC-BY-NC-SA-4.0"),
    ("cpe_bach_keyboard", "C. P. E. Bach", "keyboard_works", "CC-BY-NC-SA-4.0"),
    ("jc_bach_sonatas", "J. C. Bach", "keyboard_sonatas", "CC-BY-NC-SA-4.0"),
    ("mozart_piano_sonatas", "Mozart", "piano_sonatas", "CC-BY-NC-SA-4.0"),
    ("kozeluh_sonatas", "Koželuh", "keyboard_sonatas", "CC-BY-NC-SA-4.0"),
    ("beethoven_piano_sonatas", "Beethoven", "piano_sonatas", "CC-BY-NC-SA-4.0"),
]
CAD_COLS = ["cadences_per_100_measures", "pac_ratio_of_cadences"]


def genre_of(title: str) -> str:
    t = str(title or "").strip().lower()
    for g in ("sonata", "fantasia", "rondo"):
        if t.startswith(g) or f"keyboard {g}" in t or f"piano {g}" in t:
            return g
    return "sonata" if "sonata" in t else "other"


def corpus_rows(raw: Path, folder: str, comp: str, coll: str, lic: str) -> pd.DataFrame:
    a = pd.DataFrame(sm.dcml_corpus(raw, folder, comp, coll, lic))
    base = raw / folder
    meta = pd.read_csv(base / "metadata.tsv", sep="\t", dtype=str).set_index("piece")
    b = []
    for piece in a["piece_id"]:
        measures = pd.read_csv(base / "measures" / f"{piece}.measures.tsv", sep="\t", dtype=str)
        measures["mc"] = measures["mc"].astype(int)
        notes = sm.load_dcml_notes(base / "notes" / f"{piece}.notes.tsv", measures)
        r = {"piece_id": piece}
        r.update(s13.note_13(notes))
        hpath = base / "harmonies" / f"{piece}.harmonies.tsv"
        if hpath.exists():
            r.update(s13.harmony_13(pd.read_csv(hpath, sep="\t", dtype=str)))
        b.append(r)
    df = a.merge(pd.DataFrame(b), on="piece_id", how="left", suffixes=("", "_13"))
    df["genre"] = [genre_of(meta.loc[p, "workTitle"]) for p in df["piece_id"]]
    df["annotators"] = [meta.loc[p].get("annotators", "") for p in df["piece_id"]]
    df["harmony_version"] = [meta.loc[p].get("harmony_version", "") for p in df["piece_id"]]
    df["has_harmony"] = [(base / "harmonies" / f"{p}.harmonies.tsv").exists() for p in df["piece_id"]]
    return df


def main(raw: Path = ROOT / "data/raw", out: Path = ROOT / "data/derived") -> pd.DataFrame:
    parts = []
    for folder, comp, coll, lic in SONATA_CORPORA:
        d = corpus_rows(raw, folder, comp, coll, lic)
        print(folder, len(d))
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    # same rule as score_metrics.py: no cadence labels in a corpus or work = not annotated, not zero
    if "n_cadence_labels" in df:
        no_cad = df.groupby("corpus")["n_cadence_labels"].transform("sum") == 0
        no_cad_work = df.groupby(["corpus", "work_number"], dropna=False)["n_cadence_labels"].transform("sum") == 0
        df.loc[no_cad | no_cad_work, CAD_COLS] = float("nan")
    df["in_cohort"] = df["genre"] == "sonata"
    df.to_csv(out / "sonata_metrics_by_movement.csv", index=False, encoding="utf-8", lineterminator="\n")
    print(df.groupby(["composer", "genre"]).size().to_string().encode("ascii", "replace").decode())
    return df


if __name__ == "__main__":
    main()
