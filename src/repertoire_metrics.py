"""Repertoire metrics from the New York Philharmonic Performance History
(github.com/nyphilarchive/PerformanceHistory, CC0).

Unit of count: one "work performance" = one work entry on one program,
multiplied by the number of concerts in that program (a program given four
times counts four). Intermissions and entries without a composer are dropped.

Outputs (data/derived/):
  nyphil_composer_season.csv   — per season × composer: performances, share
  nyphil_season_summary.csv    — per season: totals, distinct composers,
                                 Bach/Beethoven share, HHI, top-10 composer share
  nyphil_work_frequency.csv    — Bach and Beethoven works ranked by performances
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd


def norm_composer(name: str) -> str:
    return re.sub(r"\s+", " ", name or "").strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/derived")
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    data = json.load(open(raw / "PerformanceHistory" / "Programs" / "json" / "complete.json", encoding="utf-8"))
    rows = []
    for p in data["programs"]:
        n_concerts = max(len(p.get("concerts", [])), 1)
        season = p.get("season", "")
        dates = [c.get("Date", "")[:10] for c in p.get("concerts", [])]
        first_date = min(dates) if dates else ""
        for w in p.get("works", []):
            comp = norm_composer(w.get("composerName", ""))
            if not comp or w.get("interval"):
                continue
            rows.append(
                {
                    "season": season,
                    "season_start": int(season[:4]) if season[:4].isdigit() else None,
                    "first_date": first_date,
                    "program_id": p.get("programID"),
                    "n_concerts": n_concerts,
                    "orchestra": p.get("orchestra"),
                    "composer": comp,
                    "work_id": w.get("ID"),
                    "work_title": w.get("workTitle", ""),
                    "movement": w.get("movement", ""),
                    "conductor": w.get("conductorName", ""),
                }
            )
    df = pd.DataFrame(rows)
    df["is_bach"] = df["composer"].str.startswith("Bach, Johann Sebastian")
    df["is_beethoven"] = df["composer"].str.startswith("Beethoven, Ludwig van")

    cs = df.groupby(["season", "season_start", "composer"])["n_concerts"].sum().rename("performances").reset_index()
    tot = cs.groupby("season")["performances"].transform("sum")
    cs["share"] = cs["performances"] / tot
    cs.to_csv(out / "nyphil_composer_season.csv", index=False, encoding="utf-8")

    def season_stats(g: pd.DataFrame) -> pd.Series:
        shares = g["share"]
        top = g.sort_values("performances", ascending=False)
        return pd.Series(
            {
                "work_performances": g["performances"].sum(),
                "distinct_composers": len(g),
                "bach_share": g.loc[g["composer"].str.startswith("Bach, Johann Sebastian"), "share"].sum(),
                "beethoven_share": g.loc[g["composer"].str.startswith("Beethoven, Ludwig van"), "share"].sum(),
                "hhi": float((shares ** 2).sum()),
                "top10_share": float(top["share"].head(10).sum()),
                "top_composer": top["composer"].iloc[0],
            }
        )

    ss = cs.groupby(["season", "season_start"]).apply(season_stats).reset_index()
    ss["n_programs"] = df.groupby("season")["program_id"].nunique().reindex(ss["season"]).values
    ss.to_csv(out / "nyphil_season_summary.csv", index=False, encoding="utf-8")

    bb = df[df["is_bach"] | df["is_beethoven"]]
    wf = bb.groupby(["composer", "work_title"]).agg(
        performances=("n_concerts", "sum"),
        programs=("program_id", "nunique"),
        first_season=("season", "min"),
        last_season=("season", "max"),
    ).reset_index().sort_values("performances", ascending=False)
    wf.to_csv(out / "nyphil_work_frequency.csv", index=False, encoding="utf-8")

    print("work performances", int(df["n_concerts"].sum()), "programs", df["program_id"].nunique(), "seasons", df["season"].nunique())
    print(ss[["season", "work_performances", "distinct_composers", "bach_share", "beethoven_share", "hhi"]].iloc[::20].to_string())
    print(wf.head(15).to_string())


if __name__ == "__main__":
    main()
