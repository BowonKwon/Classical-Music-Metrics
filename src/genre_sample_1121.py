"""1.12.1: third and fourth validation samples for the genre classification (design 72, section 3 E), each drawn after
the rules it measures were fixed. Round 4 follows the two faults found in round 3 and leaves out its pages too.

Frame: the 10,180 work pages minus the pages of all earlier rounds (genre_life_validation.csv).
  main           40 pages from each of the six big groups as classified by the revised rules (240)
  secular_extra  40 more pages from each of the three secular sub-genres, from what is left (120); the second
                 round had only 14 pages in the weakest sub-genre, too few to judge it
The 360 pages are shuffled and numbered; the reviewer sees composer, page, title, tags and instrumentation only.

Usage: python src/genre_sample_1121.py <folder for the blind file> <round: 3 or 4>
       python src/genre_sample_1121.py merge <round> <the reviewer's classification.csv>
The first writes <folder>/classification_sample.csv and the key (strata and the rules' labels) to
data/derived/audit_C<round>_key.csv, which is not published until the round is over. The second appends the finished
round to genre_life_validation.csv (the key joined to the reviewer's labels).

Round 4 can be drawn again from the published tables: genre_life_works.csv holds the classification it was drawn
from, and rounds 1 to 3 are in genre_life_validation.csv. Round 3 cannot: it was drawn from the classification
before the second revision, which survives only as the rules' labels of that round in the validation table.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/derived"
SEEDS = {3: 1913, 4: 1914}
PER_GROUP, PER_SUB = 40, 40
RULES_VERSION = {3: "1.12.1 first revision", 4: "1.12.1 second revision"}
COLS = ["round", "sample_id", "page", "group_rules", "subgenre_rules", "group_blind", "subgenre_blind", "confidence", "rules_version", "stratum"]


def draw(rnd: int) -> pd.DataFrame:
    SEED = SEEDS[rnd]
    W = pd.read_csv(D / "genre_life_works.csv", low_memory=False)
    V = pd.read_csv(D / "genre_life_validation.csv")
    used = set(V.loc[V["round"] < rnd, "page"])
    for earlier in range(3, rnd):  # a round not merged yet: its key
        if earlier not in set(V["round"]):
            used |= set(pd.read_csv(D / f"audit_C{earlier}_key.csv")["page"])
    pool = W[~W["page"].isin(used)]
    main = pool[pool["group"] != "other"].groupby("group", group_keys=False).sample(PER_GROUP, random_state=SEED).assign(stratum="main")
    rest = pool[~pool["page"].isin(main["page"])]
    extra = rest[rest["group"] == "secular"].groupby("subgenre", group_keys=False).sample(PER_SUB, random_state=SEED).assign(stratum="secular_extra")
    S = pd.concat([main, extra]).sample(frac=1, random_state=SEED).reset_index(drop=True)
    S.insert(0, "sample_id", range(1, len(S) + 1))
    return S


def main(folder: Path, rnd: int) -> pd.DataFrame:
    S = draw(rnd)
    assert len(S) == 6 * PER_GROUP + 3 * PER_SUB and not S["page"].duplicated().any()
    folder.mkdir(parents=True, exist_ok=True)
    S[["sample_id", "composer", "page", "work_title", "tags", "instrumentation"]].to_csv(
        folder / "classification_sample.csv", index=False, encoding="utf-8", lineterminator="\n")
    S[["sample_id", "page", "stratum", "group", "subgenre"]].to_csv(D / f"audit_C{rnd}_key.csv", index=False, encoding="utf-8", lineterminator="\n")
    return S


def merge(rnd: int, blind_csv: Path) -> pd.DataFrame:
    V = pd.read_csv(D / "genre_life_validation.csv")
    if "stratum" not in V.columns:
        V["stratum"] = "main"  # rounds 1 and 2 had the main sample only
    assert rnd not in set(V["round"]), f"round {rnd} is already in the table"
    K = pd.read_csv(D / f"audit_C{rnd}_key.csv").rename(columns={"group": "group_rules", "subgenre": "subgenre_rules"})
    B = pd.read_csv(blind_csv).rename(columns={"group": "group_blind", "subgenre": "subgenre_blind"})
    assert len(B) == len(K) and set(B["sample_id"]) == set(K["sample_id"]) and not set(K["page"]) & set(V["page"])
    M = K.merge(B[["sample_id", "group_blind", "subgenre_blind", "confidence"]], on="sample_id").assign(**{"round": rnd, "rules_version": RULES_VERSION[rnd]})
    out = pd.concat([V[COLS], M[COLS]], ignore_index=True)
    out.to_csv(D / "genre_life_validation.csv", index=False, encoding="utf-8", lineterminator="\n")
    return out


if __name__ == "__main__":
    if sys.argv[1] == "merge":
        v = merge(int(sys.argv[2]), Path(sys.argv[3]))
        print(v.groupby(["round", "rules_version", "stratum"]).size().to_dict())
    else:
        s = main(Path(sys.argv[1]), int(sys.argv[2]))
        print(len(s), s.groupby(["stratum", "group"]).size().to_dict())
