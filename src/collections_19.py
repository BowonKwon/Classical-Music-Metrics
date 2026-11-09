"""1.9: Romantic piano miniatures and two more string-quartet collections, the 39 score metrics per movement.

Same functions as sonata_metrics.corpus_rows (score_metrics + score_metrics_13), same cadence rule
(a collection or work without cadence labels gets blanks, not zeros).

Output: data/derived/collections_19_by_movement.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sonata_metrics as son  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# (folder, composer, collection label, license, group)
COLLECTIONS = [
    ("chopin_mazurkas", "Chopin", "mazurkas", "CC-BY-NC-SA-4.0", "piano"),
    ("schumann_kinderszenen", "Schumann", "kinderszenen", "CC-BY-NC-SA-4.0", "piano"),
    ("liszt_pelerinage", "Liszt", "annees_de_pelerinage", "CC-BY-NC-SA-4.0", "piano"),
    ("grieg_lyric_pieces", "Grieg", "lyric_pieces", "CC-BY-NC-SA-4.0", "piano"),
    ("tchaikovsky_seasons", "Tchaikovsky", "the_seasons", "CC-BY-NC-SA-4.0", "piano"),
    ("dvorak_silhouettes", "Dvořák", "silhouettes", "CC-BY-NC-SA-4.0", "piano"),
    ("medtner_tales", "Medtner", "tales", "CC-BY-NC-SA-4.0", "piano"),
    ("pleyel_quartets", "Pleyel", "string_quartets", "CC-BY-NC-SA-4.0", "quartet"),
    ("mendelssohn_quartets", "Mendelssohn", "string_quartets", "CC-BY-NC-SA-4.0", "quartet"),
    ("ABC", "Beethoven", "string_quartets", "CC-BY-NC-SA-4.0", "quartet"),  # recomputed; tests check it equals the published rows
]


def norm_annotators(s: str) -> str:
    """'John heilig' and 'John Heilig' are one person; keep the first spelling met in title case."""
    if pd.isna(s):
        return ""
    parts = [p.strip() for p in str(s).split(",") if p.strip()]
    return ", ".join(" ".join(w[:1].upper() + w[1:] for w in p.split(" ")) for p in parts)


def main(raw: Path = ROOT / "data/raw", out: Path = ROOT / "data/derived") -> pd.DataFrame:
    parts = []
    for folder, comp, coll, lic, grp in COLLECTIONS:
        d = son.corpus_rows(raw, folder, comp, coll, lic)
        d["group"] = grp
        print(folder, len(d))
        parts.append(d)
    df = pd.concat(parts, ignore_index=True)
    df["annotators"] = df["annotators"].map(norm_annotators)
    if "n_cadence_labels" in df:
        no_cad = df.groupby("corpus")["n_cadence_labels"].transform("sum") == 0
        no_cad_work = df.groupby(["corpus", "work_number"], dropna=False)["n_cadence_labels"].transform("sum") == 0
        df.loc[no_cad | no_cad_work, son.CAD_COLS] = float("nan")
    df = df.drop(columns=["genre"])
    df.to_csv(out / "collections_19_by_movement.csv", index=False, encoding="utf-8", lineterminator="\n")
    return df


if __name__ == "__main__":
    main()
