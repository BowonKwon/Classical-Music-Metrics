"""Beethoven symphonies: a tempo index from track lengths (1.18).

The bmetr tempi (Martín-Castro & Ucar 2020) were measured from the audio of 36 complete cycles.
Conductors outside that set can only be added through track lengths. A track's length mixes
tempo with repeats (taken or not, unknown), so the index uses only the seven inner movements of
Symphonies 2-8 that carry no repeat sign in bmetr's `sym.marks` (bar.rep = 0) and are not
finales: 2/II, 3/II, 4/II, 5/II, 6/II, 7/II, 8/II. Of the eleven repeat-free movements, the finales (2/IV, 6/V,
8/IV) are left out because live recordings may end with applause and the last track of a disc carries more
trailing silence, and 6/IV (the storm) because it runs into the finale and discs may cut the track elsewhere.

    k = theoretical duration at the marks, no repeats (bmetr formula) / track length

k = 1 means as marked; 0.8 means 80% of the marked speed (the movement took 1.25 times as long).

Two sub-commands:

  export  — from tables cut out of the MusicBrainz core dump (src/mb_dump_extract.py, then
            src/mb_beethoven.py), write the small CC0 extract this script needs to
            data/raw/musicbrainz/ (candidates, their Beethoven symphony recordings, track lengths,
            the releases whose barcodes match the bmetr albums).
  compute — (default) read data/raw/musicbrainz/ and the bmetr-derived tables, select one
            recording per movement by fixed rules, and write data/derived/beethoven_length_*.csv.

    python src/beethoven_length.py export --bsym <dir> --persons <persons csv>
    python src/beethoven_length.py compute
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/musicbrainz"
DER = ROOT / "data/derived"
INNER = [(2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2), (8, 2)]
REPEAT_FREE_11 = INNER + [(2, 4), (6, 4), (6, 5), (8, 4)]
PLAUSIBLE = 1.5          # drop a track whose k differs from the 36-conductor median of that movement by more than this factor
SPREAD_FLAG_S = 3.0      # flag a recording whose track lengths on different releases differ by more than this
BOOT_B, BOOT_SEED = 2000, 20261116
DUMP = dict(name="mbdump.tar.bz2", export="20261114-002230",
            url="https://data.metabrainz.org/pub/musicbrainz/data/fullexport/20261114-002230/mbdump.tar.bz2",
            sha256="da4f1afcbca8ca54eb6362ae45173543f079e8491d097a376d060551d1a03335", bytes=7738103395,
            licence="CC0 1.0 (MusicBrainz core data)")

# Conductors the site owner asked for by name, and the genealogy project's pinned ("requested") list.
REQUESTED = ["Q153778", "Q60813", "Q160706",  # Chung Myung-whun, Christian Thielemann, Carlos Kleiber
             "Q13003", "Q57285", "Q154895", "Q84241", "Q128085", "Q152505", "Q61205", "Q117710", "Q151608",
             "Q155712", "Q165671", "Q157635", "Q276038", "Q371795", "Q158370", "Q700791", "Q57425", "Q61180",
             "Q537083", "Q323075", "Q1675318", "Q59828688", "Q496386", "Q9298953", "Q78526"]


def fold(s: str) -> frozenset:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower().replace(",", " ")
    return frozenset(s.split())


# ------------------------------------------------------------------ export
def export(bsym: Path, persons: Path, out: Path = RAW):
    out.mkdir(parents=True, exist_ok=True)
    r = lambda f: pd.read_csv(bsym / f, dtype=str)  # noqa: E731
    MV, RW, AR = r("bsym_movement_works.csv"), r("bsym_recording_work.csv"), r("bsym_artist_recording.csv")
    REC, ACN, TR, MED, REL = r("bsym_recording.csv"), r("bsym_credit.csv"), r("bsym_tracks.csv"), r("bsym_medium.csv"), r("bsym_releases.csv")
    ART, AW = r("bsym_artists.csv"), r("artists_wikidata.csv")
    gid = dict(zip(ART.id, ART.gid)); name = dict(zip(ART.id, ART.name))
    rgid = dict(zip(REC.id, REC.gid))

    # candidates: genealogy persons with a MusicBrainz artist, plus how each maps to the bmetr 36
    p = pd.read_csv(persons, encoding="utf-8-sig", dtype=str)
    aw = AW.drop_duplicates("q")
    p = p.merge(aw[["q", "artist", "gid"]], left_on="wikidata_q", right_on="q", how="inner")
    bm = pd.read_csv(DER / "beethoven_symphony_recordings.csv", dtype=str)
    key = {fold(c): c for c in bm.conductor}
    p["bmetr_conductor"] = p.name_en.map(lambda n: key.get(fold(n), ""))
    p["requested"] = p.wikidata_q.isin(REQUESTED)

    # movement recordings, conductor by relationship (else by artist credit, if the artist conducts elsewhere)
    mw = MV.set_index("work")
    rw = RW[RW.kind == "mv"].merge(MV[["work", "symphony", "movement", "work_name"]], on="work")
    rw = rw[~rw.work_name.str.contains(r"S\. ?\d|arr\.|transcr", case=False, regex=True)]
    nmv = rw.groupby("recording").apply(lambda g: g[["symphony", "movement"]].drop_duplicates().shape[0], include_groups=False).rename("n_mv")
    rw = rw.drop_duplicates("recording").merge(nmv, left_on="recording", right_index=True)
    cond = AR[AR.role == "conductor"][["artist", "recording", "year"]].assign(via="relationship")
    known = set(cond.artist)
    cr = REC[["id", "artist_credit"]].rename(columns={"id": "recording"}).merge(ACN, on="artist_credit")
    cr = cr[cr.artist.isin(known) & ~cr.recording.isin(set(cond.recording))][["artist", "recording"]].assign(year=np.nan, via="artist credit")
    C = pd.concat([cond, cr]).merge(rw[["recording", "symphony", "movement", "n_mv", "work_name"]], on="recording")
    orch = AR[AR.role == "orchestra"].groupby("recording").artist.agg(lambda x: "; ".join(sorted(name.get(a, a) for a in set(x))))
    C["orchestra"] = C.recording.map(orch).fillna("")
    C = C[C.artist.isin(set(p.artist))]
    C["artist_mbid"] = C.artist.map(gid)
    C["recording_mbid"] = C.recording.map(rgid)
    C = C.drop_duplicates(["artist", "recording"])

    # tracks of those recordings, with their releases
    t = TR[TR.recording.isin(set(C.recording))].merge(MED[["id", "release", "position"]].rename(columns={"id": "medium", "position": "medium_pos"}), on="medium")
    t = t.drop(columns=["name"]).merge(REL[["id", "gid", "name", "rg_gid", "rg_name", "barcode", "first_year", "status"]].rename(columns={"id": "release"}), on="release")
    t["recording_mbid"] = t.recording.map(rgid)
    tracks = t[["recording_mbid", "gid", "name", "rg_gid", "rg_name", "barcode", "first_year", "status", "medium_pos", "position", "length"]].rename(
        columns={"gid": "release_mbid", "name": "release_name", "rg_gid": "release_group_mbid", "rg_name": "release_group_name", "position": "track_pos", "length": "length_ms"})

    # releases whose barcode equals a bmetr album UPC (leading zeros ignored): all single-movement symphony tracks
    norm = lambda b: str(b).lstrip("0") if pd.notna(b) and str(b).strip() else None  # noqa: E731
    REL["bc"] = REL.barcode.map(norm); bm["bc"] = bm.upc.map(norm)
    hit = bm.merge(REL[["id", "gid", "name", "bc"]], on="bc")
    bt = TR[TR.medium.isin(set(MED[MED.release.isin(set(hit.id))].id))].merge(MED[["id", "release"]].rename(columns={"id": "medium"}), on="medium")
    bt = bt.merge(rw[["recording", "symphony", "movement", "n_mv"]], on="recording").merge(hit[["id", "gid", "conductor", "upc"]].rename(columns={"id": "release"}), on="release")
    bt["recording_mbid"] = bt.recording.map(rgid)
    barcode = bt[["conductor", "upc", "gid", "recording_mbid", "symphony", "movement", "n_mv", "length"]].rename(columns={"gid": "release_mbid", "length": "length_ms"})

    cand = p[["wikidata_q", "name_ko", "name_en", "tier", "gid", "requested", "bmetr_conductor"]].rename(columns={"gid": "artist_mbid"})
    cand = cand[cand.artist_mbid.isin(set(C.artist_mbid)) | cand.requested]
    recs = C[["artist_mbid", "recording_mbid", "symphony", "movement", "n_mv", "work_name", "orchestra", "year", "via"]].rename(columns={"year": "link_year"})
    for df, f in ((cand, "candidates.csv"), (recs, "conductor_recordings.csv"), (tracks, "tracks.csv"), (barcode, "bmetr_barcode_tracks.csv")):
        df.sort_values(list(df.columns[:2])).to_csv(out / f, index=False, encoding="utf-8", lineterminator="\n")
    man = dict(source=DUMP, schema_sequence=int((bsym.parent / "extract" / "SCHEMA_SEQUENCE").read_text(encoding="utf-8").strip()) if (bsym.parent / "extract" / "SCHEMA_SEQUENCE").exists() else None,
               files={f: int(len(pd.read_csv(out / f, dtype=str))) for f in ("candidates.csv", "conductor_recordings.csv", "tracks.csv", "bmetr_barcode_tracks.csv")},
               note="Extract of the MusicBrainz core dump: Beethoven symphony movement recordings of the listed conductors, "
                    "with the track lengths of every release carrying them. Arrangements (Liszt S. numbers, 'arr.', 'transcr.') excluded. "
                    "Candidate names and tiers come from the site owner's conductor-genealogy list; Wikidata IDs are matched through MusicBrainz URL relationships.")
    (out / "manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print({k: v for k, v in man["files"].items()})


# ------------------------------------------------------------------ compute
def k_table_36() -> pd.DataFrame:
    d = pd.read_csv(DER / "beethoven_symphony_duration_ratio.csv")
    d["k"] = d.theo_no_rep_s / d.duration
    return d


def spearman_boot(x, y, rng) -> tuple[float, float, float]:
    x, y = np.asarray(x), np.asarray(y)
    rho = stats.spearmanr(x, y).statistic
    b = [stats.spearmanr(x[i], y[i]).statistic for i in (rng.choice(len(x), len(x)) for _ in range(BOOT_B))]
    return float(rho), float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))


def audio_validation(d: pd.DataFrame) -> list[dict]:
    """How well does the length index rank the 36 conductors like the bmetr audio tempo?"""
    cs = pd.read_csv(DER / "beethoven_symphony_conductor_summary.csv").set_index("conductor")
    marks = pd.read_csv(DER / "beethoven_symphony_marks.csv")
    rows = []
    sets = {"inner7": INNER, "repeat_free11": REPEAT_FREE_11}
    for lab, mvs in sets.items():
        x = d[[(a, b) in mvs for a, b in zip(d.symphony, d.movement)]]
        km = x.groupby("conductor").k.median().reindex(cs.index)
        rho, lo, hi = spearman_boot(km.values, cs.median_ratio.values, np.random.default_rng(BOOT_SEED))
        rows.append(dict(check="audio_vs_length", movements=lab, n_movements=len(mvs), n=len(cs), rho=rho, lo=lo, hi=hi))
    for lab, col in (("all33_no_repeats", "theo_no_rep_s"), ("all33_with_repeats", "theo_with_rep_s")):
        x = d[d.symphony <= 8]
        km = (x[col] / x.duration).groupby(x.conductor).median().reindex(cs.index)
        rows.append(dict(check="audio_vs_length", movements=lab, n_movements=33, n=len(cs), rho=float(stats.spearmanr(km, cs.median_ratio).statistic), lo=np.nan, hi=np.nan))
    x = d[[(a, b) in INNER for a, b in zip(d.symphony, d.movement)]]
    km = x.groupby("conductor").k.median().reindex(cs.index)
    rk = (km.rank() - cs.median_ratio.rank()).abs()
    rows.append(dict(check="rank_gap_inner7", movements="inner7", n_movements=7, n=len(cs), rho=float(rk.mean()), lo=float(rk.median()), hi=float(rk.max())))
    return rows


def one_orchestra(sel: pd.DataFrame) -> bool:
    """True when every selected recording carries an orchestra credit and all name the same single orchestra."""
    o = sel.orchestra.fillna("")
    if (o == "").any():
        return False
    return len({x for v in o for x in v.split("; ") if x}) == 1


def pick_cycle(r: pd.DataFrame, t: pd.DataFrame) -> pd.DataFrame:
    """One recording per inner movement, taken from one release group (a boxed cycle).
    Among release groups, in this order: the most of the conductor's inner movements; seven picks naming one
    orchestra (every pick credited); the most of the conductor's symphonies; the most releases; the earliest
    first release; then the release-group MBID. Within a group, per movement: the recording on the most
    distinct releases, then the earliest link year, then the recording MBID."""
    on = t.merge(r[["recording_mbid", "symphony", "movement"]], on="recording_mbid")
    inner = on[[(a, b) in INNER for a, b in zip(on.symphony, on.movement)]]
    if inner.empty:
        return r.iloc[0:0]
    g = on.groupby("release_group_mbid").agg(n_sym=("symphony", "nunique"), n_rel=("release_mbid", "nunique"), first=("first_year", "min"))
    gi = inner.groupby("release_group_mbid").apply(lambda x: x[["symphony", "movement"]].drop_duplicates().shape[0], include_groups=False).rename("n_inner")
    g = g.join(gi, how="inner").reset_index()

    def pick(rg):
        recs = set(inner[inner.release_group_mbid == rg].recording_mbid)
        return r[r.recording_mbid.isin(recs)].sort_values(["n_releases", "link_year", "recording_mbid"], ascending=[False, True, True]).drop_duplicates(["symphony", "movement"])
    g["one_orch"] = [one_orchestra(pick(rg)) for rg in g.release_group_mbid]
    g = g.sort_values(["n_inner", "one_orch", "n_sym", "n_rel", "first", "release_group_mbid"], ascending=[False, False, False, False, True, True])
    best = g.iloc[0]
    sel = pick(best.release_group_mbid)
    rg_name = t[t.release_group_mbid == best.release_group_mbid].release_group_name.iloc[0]
    return sel.assign(release_group_mbid=best.release_group_mbid, release_group_name=rg_name)


def pick_partial(r: pd.DataFrame) -> pd.DataFrame:
    """When no release group carries all seven: per movement the recording on the most releases, then the earliest
    link year. A conductor counts as complete ("full") only if the seven selected recordings name one orchestra."""
    return r.sort_values(["n_releases", "link_year", "recording_mbid"], ascending=[False, True, True]).drop_duplicates(["symphony", "movement"]).assign(
        release_group_mbid="", release_group_name="")


MERGE_TOL = 0.02   # records of one orchestra whose lengths differ by at most 2% are taken as one performance


def performances(r: pd.DataFrame, T: pd.DataFrame) -> pd.DataFrame:
    """All distinct performances of one conductor (partial table, 1.18).
    Same movement + orchestra + link year = one performance. A record without a year joins the dated
    performance of the same orchestra whose median length is within MERGE_TOL (the closest one), otherwise
    undated records of that orchestra form their own performance(s) by the same tolerance. Length is the
    median over the merged records; their range is kept and flagged when it exceeds MERGE_TOL."""
    first = T.groupby("recording_mbid").first_year.min()
    rows = []
    for (sy, mv, orch), g in r.groupby(["symphony", "movement", "orchestra"], dropna=False):
        groups = []   # list of [year, [rows]]
        for y, gy in g[g.link_year.notna()].groupby("link_year"):
            groups.append([int(y), list(gy.itertuples())])
        for x in g[g.link_year.isna()].sort_values("length_ms").itertuples():
            best, gap = None, None
            for grp in groups:
                med = float(np.median([z.length_ms for z in grp[1]]))
                d = abs(x.length_ms - med) / med
                if d <= MERGE_TOL and (gap is None or d < gap):
                    best, gap = grp, d
            if best is None:
                groups.append([None, [x]])
            else:
                best[1].append(x)
        for y, recs in groups:
            ls = [z.length_ms for z in recs]
            med = float(np.median(ls))
            rows.append(dict(symphony=sy, movement=mv, orchestra=orch or "", year=y, n_records=len(recs),
                             recording_mbids=" ".join(sorted(z.recording_mbid for z in recs)),
                             length_s=med / 1000, length_min_s=min(ls) / 1000, length_max_s=max(ls) / 1000,
                             records_disagree=(max(ls) - min(ls)) / med > MERGE_TOL,
                             n_releases=int(T[T.recording_mbid.isin({z.recording_mbid for z in recs})].release_mbid.nunique()),
                             first_release_year=float(np.nanmin([first.get(z.recording_mbid, np.nan) for z in recs])) if any(pd.notna(first.get(z.recording_mbid, np.nan)) for z in recs) else np.nan))
    return pd.DataFrame(rows)


def compute(raw: Path = RAW, out: Path = DER):
    d = k_table_36()
    inner36 = d[[(a, b) in INNER for a, b in zip(d.symphony, d.movement)]].copy()
    mv_med = inner36.groupby(["symphony", "movement"]).k.median()
    theo = inner36.groupby(["symphony", "movement"]).theo_no_rep_s.first()

    cand = pd.read_csv(raw / "candidates.csv", dtype=str, keep_default_na=False)
    cand["requested"] = cand.requested.eq("True")
    R = pd.read_csv(raw / "conductor_recordings.csv", dtype={"artist_mbid": str, "recording_mbid": str})
    T = pd.read_csv(raw / "tracks.csv", dtype={"recording_mbid": str, "release_mbid": str, "release_group_mbid": str, "barcode": str})
    T = T[T.length_ms.notna()]
    # one value per distinct release (median of duplicate track rows on that release), then the median over releases
    TR1 = T.groupby(["recording_mbid", "release_mbid"]).length_ms.median().reset_index()
    L = TR1.groupby("recording_mbid").length_ms.agg(length_ms="median", lmin="min", lmax="max", n_releases="size").reset_index()
    R = R[R.n_mv == 1].merge(L, on="recording_mbid")
    R = R[[(a, b) in INNER for a, b in zip(R.symphony, R.movement)]].copy()
    R["theo_s"] = [theo[(a, b)] for a, b in zip(R.symphony, R.movement)]
    R["k"] = R.theo_s / (R.length_ms / 1000)
    R["rel_to_36"] = [k / mv_med[(a, b)] for a, b, k in zip(R.symphony, R.movement, R.k)]
    R["implausible"] = (R.rel_to_36 > PLAUSIBLE) | (R.rel_to_36 < 1 / PLAUSIBLE)
    R["spread_s"] = (R.lmax - R.lmin) / 1000
    dropped = R[R.implausible]
    R = R[~R.implausible]

    rows, mrows, pipe = [], [], []
    for c in cand.itertuples():
        r = R[R.artist_mbid == c.artist_mbid]
        sel = pick_cycle(r, T)
        if sel[["symphony", "movement"]].drop_duplicates().shape[0] < 7:
            sel = pick_partial(r)
        n7 = sel[["symphony", "movement"]].drop_duplicates().shape[0] == 7
        named = {x for v in sel.orchestra.fillna("") for x in v.split("; ") if x}
        blank = (sel.orchestra.fillna("") == "").any()
        status = ("full" if n7 and one_orchestra(sel) else
                  "orchestra_missing" if n7 and blank and len(named) <= 1 else
                  "several_orchestras" if n7 else "partial")
        if sel.empty:
            rows.append(dict(wikidata_q=c.wikidata_q, name_en=c.name_en, name_ko=c.name_ko, requested=c.requested, bmetr_conductor=c.bmetr_conductor or "", status="none", n_movements=0))
            continue
        rec = dict(wikidata_q=c.wikidata_q, name_en=c.name_en, name_ko=c.name_ko, requested=c.requested, bmetr_conductor=c.bmetr_conductor or "",
                   status=status, n_movements=len(sel), k_median=sel.k.median(), k_q1=sel.k.quantile(.25), k_q3=sel.k.quantile(.75),
                   orchestra="; ".join(sorted(set(sel.orchestra.fillna("")))), link_years=",".join(sorted({str(int(y)) for y in sel.link_year.dropna()})),
                   release_group=sel.release_group_name.iloc[0], n_spread_flag=int((sel.spread_s > SPREAD_FLAG_S).sum()),
                   movements=" ".join(f"{a}/{b}" for a, b in sorted(zip(sel.symphony, sel.movement))))
        rows.append(rec)
        for x in sel.itertuples():
            mrows.append(dict(wikidata_q=c.wikidata_q, name_en=c.name_en, source="musicbrainz", status=status, symphony=x.symphony, movement=x.movement,
                              recording_mbid=x.recording_mbid, orchestra=x.orchestra, link_year=x.link_year, release_group=x.release_group_name,
                              length_s=x.length_ms / 1000, n_releases=x.n_releases, spread_s=x.spread_s, theo_s=x.theo_s, k=x.k,
                              median_k_36=mv_med[(x.symphony, x.movement)], rel_to_36=x.rel_to_36))
        if c.bmetr_conductor and status == "full":
            bmk = inner36[inner36.conductor == c.bmetr_conductor].k.median()
            pipe.append(dict(bmetr_conductor=c.bmetr_conductor, k_bmetr=bmk, k_musicbrainz=rec["k_median"], diff=rec["k_median"] - bmk,
                             release_group=rec["release_group"], orchestra=rec["orchestra"], link_years=rec["link_years"]))
    S = pd.DataFrame(rows)
    # who is new on the figure: complete cycle, not one of the 36; partial rows only for requested conductors
    S["on_figure"] = (S.status == "full") & S.bmetr_conductor.eq("")
    S["in_partial_table"] = S.status.isin(["partial", "several_orchestras", "orchestra_missing"]) & S.requested & S.bmetr_conductor.eq("")
    # partial table: every distinct performance, no representative pick
    prow = []
    for c in S[S.in_partial_table].itertuples():
        pf = performances(R[R.artist_mbid == cand.set_index("wikidata_q").artist_mbid[c.wikidata_q]], T)
        pf.insert(0, "name_ko", c.name_ko); pf.insert(0, "name_en", c.name_en); pf.insert(0, "wikidata_q", c.wikidata_q)
        prow.append(pf)
    PA = pd.concat(prow, ignore_index=True)
    PA["theo_s"] = [theo[(a, b)] for a, b in zip(PA.symphony, PA.movement)]
    PA["k"] = PA.theo_s / PA.length_s
    PA["median_k_36"] = [mv_med[(a, b)] for a, b in zip(PA.symphony, PA.movement)]
    PA["rel_to_36"] = PA.k / PA.median_k_36
    PA = PA.sort_values(["name_en", "symphony", "movement", "year"], na_position="last")
    for col in ("k_median", "k_q1", "k_q3"):
        S.loc[S.status != "full", col] = np.nan   # a summary over a hand-picked subset of movements is not shown

    # the 36 from bmetr
    b36 = inner36.groupby("conductor").k.agg(k_median="median", k_q1=lambda x: x.quantile(.25), k_q3=lambda x: x.quantile(.75), n_movements="size").reset_index()
    rec36 = pd.read_csv(DER / "beethoven_symphony_recordings.csv")[["conductor", "orchestra", "date", "ptype"]]
    b36 = b36.merge(rec36, on="conductor").assign(source="bmetr")
    new = S[S.on_figure].assign(source="musicbrainz", conductor=lambda x: x.name_en, ptype="")
    idx = pd.concat([b36[["conductor", "source", "ptype", "orchestra", "date", "n_movements", "k_median", "k_q1", "k_q3"]],
                     new[["conductor", "source", "ptype", "orchestra", "link_years", "n_movements", "k_median", "k_q1", "k_q3", "requested", "wikidata_q", "release_group"]].rename(columns={"link_years": "date"})])
    idx = idx.sort_values("k_median").reset_index(drop=True)

    M = pd.DataFrame(mrows)
    M = M[M.status == "full"]   # partial conductors: see beethoven_length_partial.csv
    m36 = inner36.assign(source="bmetr", name_en=inner36.conductor, length_s=inner36.duration, theo_s=inner36.theo_no_rep_s,
                         median_k_36=[mv_med[(a, b)] for a, b in zip(inner36.symphony, inner36.movement)])
    m36["rel_to_36"] = m36.k / m36.median_k_36
    M = pd.concat([m36[["name_en", "source", "symphony", "movement", "length_s", "theo_s", "k", "median_k_36", "rel_to_36"]], M])

    # checks
    V = audio_validation(d)
    bt = pd.read_csv(raw / "bmetr_barcode_tracks.csv", dtype={"release_mbid": str})
    bt = bt[(bt.n_mv == 1) & bt.length_ms.notna()]
    bt = bt[[(a, b) in INNER for a, b in zip(bt.symphony, bt.movement)]]
    bt = bt.merge(d[["conductor", "symphony", "movement", "duration"]], on=["conductor", "symphony", "movement"])
    # per conductor the release carrying the most of the seven movements; ties: the smaller release MBID
    best = bt.groupby(["conductor", "release_mbid"]).size().reset_index(name="n").sort_values(["n", "release_mbid"], ascending=[False, True]).drop_duplicates("conductor", keep="first")
    # one recording per movement on that release: the smaller recording MBID (Wand No. 5 has two)
    bt = bt.merge(best[["conductor", "release_mbid"]]).sort_values("recording_mbid").drop_duplicates(["conductor", "symphony", "movement"])
    bt["diff_s"] = bt.length_ms / 1000 - bt.duration
    bt["rel_diff"] = bt.diff_s / bt.duration
    per = bt.groupby("conductor").rel_diff.apply(lambda x: x.abs().median())
    off = set(per[per > 0.02].index)   # the release carrying this barcode is another recording (median gap above 2%)
    for lab, x in (("all", bt), ("same_recording", bt[~bt.conductor.isin(off)])):
        V.append(dict(check=f"barcode_{lab}", movements="inner7", n_movements=7, n=int(x.conductor.nunique()), rho=float(x.diff_s.median()),
                      lo=float(x.diff_s.quantile(.25)), hi=float(x.diff_s.quantile(.75)), n_tracks=int(len(x)),
                      share_within_10s=float((x.diff_s.abs() <= 10).mean()), max_abs_rel=float(x.rel_diff.abs().max()),
                      excluded=";".join(sorted(off)) if lab == "same_recording" else ""))
    P = pd.DataFrame(pipe)
    if len(P):
        V.append(dict(check="pipeline_vs_bmetr", movements="inner7", n_movements=7, n=len(P), rho=float(stats.spearmanr(P.k_bmetr, P.k_musicbrainz).statistic),
                      lo=float((P["diff"].abs() < 0.02).sum()), hi=float(P["diff"].abs().max())))
    V.append(dict(check="dropped_implausible", movements="inner7", n_movements=7, n=int(len(dropped)), rho=np.nan, lo=np.nan, hi=np.nan))

    out.mkdir(parents=True, exist_ok=True)
    w = dict(index=False, encoding="utf-8", lineterminator="\n")
    idx.to_csv(out / "beethoven_length_index.csv", **w)
    S.to_csv(out / "beethoven_length_candidates.csv", **w)
    M.to_csv(out / "beethoven_length_movements.csv", **w)
    V = pd.DataFrame(V).rename(columns={"rho": "value"})  # value: rho, or seconds / counts as the check says
    V.to_csv(out / "beethoven_length_checks.csv", **w)
    P.to_csv(out / "beethoven_length_pipeline.csv", **w)
    PA.to_csv(out / "beethoven_length_partial.csv", **w)
    bt.to_csv(out / "beethoven_length_barcode.csv", **w)
    dropped[["artist_mbid", "recording_mbid", "symphony", "movement", "orchestra", "length_ms", "k", "rel_to_36"]].to_csv(out / "beethoven_length_dropped.csv", **w)
    print(V.round(3).to_string())
    print("on figure: bmetr", len(b36), "new", int(S.on_figure.sum()), "| partial table", int(S.in_partial_table.sum()))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")
    e = sub.add_parser("export"); e.add_argument("--bsym", required=True); e.add_argument("--persons", required=True)
    sub.add_parser("compute")
    a = ap.parse_args()
    if a.cmd == "export":
        export(Path(a.bsym), Path(a.persons))
    else:
        compute()


if __name__ == "__main__":
    main()
