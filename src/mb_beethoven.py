"""Beethoven symphony recordings by conductor, from the MusicBrainz core dump (CC0).
Usage: python -I mb_beethoven.py <extract_dir> <out_dir>
Writes:
  bsym_recordings.csv  recording-level: recording, symphony, movement, n_movement_works, conductor ids, orchestra ids, link years
  bsym_tracks.csv      track-level: recording, release, medium pos, track pos, length_ms
  bsym_releases.csv    release: id, gid, name, release_group, rg_name, barcode, first date
  artists_wikidata.csv artist id, gid, name, wikidata Q
"""
import sys, re, os, csv, collections
import pandas as pd

E, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
RD = dict(sep="\t", header=None, quoting=csv.QUOTE_NONE, na_values=["\\N"], keep_default_na=False,
          dtype=str, engine="c", on_bad_lines="warn", encoding="utf-8")

def read(name, cols, usecols=None, chunks=False):
    kw = dict(RD, names=cols)
    if usecols: kw["usecols"] = usecols
    if chunks: kw["chunksize"] = 2_000_000
    return pd.read_csv(os.path.join(E, name), **kw)

LT = read("link_type", ["id", "parent", "child_order", "gid", "e0", "e1", "name", "description", "link_phrase",
                         "reverse_link_phrase", "long_link_phrase", "last_updated", "is_deprecated", "has_dates",
                         "c0", "c1"], usecols=["id", "e0", "e1", "name"])
def lt(e0, e1, name):
    r = LT[(LT.e0 == e0) & (LT.e1 == e1) & (LT.name == name)]
    assert len(r) == 1, (e0, e1, name, r)
    return r.id.iloc[0]
LT_COND_REC = lt("artist", "recording", "conductor")
LT_ORCH_REC = lt("artist", "recording", "performing orchestra")
LT_COND_REL = lt("artist", "release", "conductor")
LT_ORCH_REL = lt("artist", "release", "performing orchestra")
LT_COMPOSER = lt("artist", "work", "composer")
LT_PERF = lt("recording", "work", "performance")
LT_PARTS = lt("work", "work", "parts")
print("link types", LT_COND_REC, LT_ORCH_REC, LT_COND_REL, LT_ORCH_REL, LT_COMPOSER, LT_PERF, LT_PARTS)

LINK = read("link", ["id", "link_type", "by", "bm", "bd", "ey", "em", "ed", "attribute_count", "created", "ended"],
            usecols=["id", "link_type", "by", "ey"])
link_type_of = dict(zip(LINK.id, LINK.link_type))
link_by = dict(zip(LINK.id, LINK.by))
links_of = lambda t: set(LINK.id[LINK.link_type == t])

A = read("artist", ["id", "gid", "name", "sort_name", "bdy", "bdm", "bdd", "edy", "edm", "edd", "type", "area",
                     "gender", "comment", "edits_pending", "last_updated", "ended", "begin_area", "end_area"],
         usecols=["id", "gid", "name", "sort_name", "type", "comment"])
beet = A[(A.name == "Ludwig van Beethoven")]
print("beethoven rows", beet[["id", "gid", "comment"]].values.tolist())
BEET = set(beet.id)

# composer links -> Beethoven works
law = read("l_artist_work", ["id", "link", "e0", "e1", "ep", "lu", "lo", "c0", "c1"], usecols=["link", "e0", "e1"])
comp_links = links_of(LT_COMPOSER)
bw = set(law.e1[law.e0.isin(BEET) & law.link.isin(comp_links)])
W = read("work", ["id", "gid", "name", "type", "comment", "ep", "lu"], usecols=["id", "gid", "name", "comment"])
W = W[W.id.isin(bw)]
rx_mv = re.compile(r"^Symphony no\.\s*([1-9])\b[^:]*:\s*([IVX]+)\.")
rx_sym = re.compile(r"^Symphony no\.\s*([1-9])\b[^:]*$")
ROM = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5}
mv_rows = []
for r in W.itertuples():
    m = rx_mv.match(r.name or "")
    if m and m.group(2) in ROM:
        mv_rows.append((r.id, r.gid, int(m.group(1)), ROM[m.group(2)], r.name, r.comment))
MV = pd.DataFrame(mv_rows, columns=["work", "work_gid", "symphony", "movement", "work_name", "work_comment"])
SY = W[W.name.fillna("").str.match(rx_sym)]
print("movement works", len(MV), MV.groupby(["symphony", "movement"]).size().to_dict())
print("symphony works", len(SY), SY.name.head(20).tolist())
MV.to_csv(os.path.join(OUT, "bsym_movement_works.csv"), index=False)
SY.to_csv(os.path.join(OUT, "bsym_symphony_works.csv"), index=False)

# recordings of movement works
perf_links = links_of(LT_PERF)
rw = []
for ch in read("l_recording_work", ["id", "link", "e0", "e1", "ep", "lu", "lo", "c0", "c1"], usecols=["link", "e0", "e1"], chunks=True):
    rw.append(ch[ch.e1.isin(set(MV.work)) | ch.e1.isin(set(SY.id))])
RW = pd.concat(rw)
RW["kind"] = RW.e1.map(lambda w: "mv" if w in set(MV.work) else "sym")
print("recording-work rows", len(RW), RW.kind.value_counts().to_dict())
RECS = set(RW.e0)

# conductor / orchestra links on recordings
cl, ol = links_of(LT_COND_REC), links_of(LT_ORCH_REC)
ar = []
for ch in read("l_artist_recording", ["id", "link", "e0", "e1", "ep", "lu", "lo", "c0", "c1"], usecols=["link", "e0", "e1"], chunks=True):
    ch = ch[ch.e1.isin(RECS) & (ch.link.isin(cl) | ch.link.isin(ol))]
    ar.append(ch)
AR = pd.concat(ar)
AR["role"] = AR.link.map(lambda l: "conductor" if l in cl else "orchestra")
AR["year"] = AR.link.map(link_by)
print("artist-recording rows", len(AR), AR.role.value_counts().to_dict())

# recording names / artist credits
rc = []
for ch in read("recording", ["id", "gid", "name", "artist_credit", "length", "comment", "ep", "lu", "video"],
               usecols=["id", "gid", "name", "artist_credit", "length"], chunks=True):
    rc.append(ch[ch.id.isin(RECS)])
REC = pd.concat(rc)
acs = set(REC.artist_credit)
acn = []
for ch in read("artist_credit_name", ["artist_credit", "position", "artist", "name", "join_phrase"], usecols=["artist_credit", "artist"], chunks=True):
    acn.append(ch[ch.artist_credit.isin(acs)])
ACN = pd.concat(acn)
print("recordings", len(REC), "credit rows", len(ACN))

# tracks
tr = []
for ch in read("track", ["id", "gid", "recording", "medium", "position", "number", "name", "artist_credit", "length", "ep", "lu", "is_data_track"],
               usecols=["id", "recording", "medium", "position", "number", "name", "length"], chunks=True):
    tr.append(ch[ch.recording.isin(RECS)])
TR = pd.concat(tr)
meds = set(TR.medium)
MED = read("medium", ["id", "release", "position", "format", "name", "ep", "lu", "track_count", "gid"], usecols=["id", "release", "position", "format", "track_count"])
MED = MED[MED.id.isin(meds)]
rels = set(MED.release)
REL = read("release", ["id", "gid", "name", "artist_credit", "release_group", "status", "packaging", "language", "script", "barcode", "comment", "ep", "quality", "lu"],
           usecols=["id", "gid", "name", "release_group", "status", "barcode", "comment"])
REL = REL[REL.id.isin(rels)]
RG = read("release_group", ["id", "gid", "name", "artist_credit", "type", "comment", "ep", "lu"], usecols=["id", "gid", "name"])
RG = RG[RG.id.isin(set(REL.release_group))].rename(columns={"id": "release_group", "gid": "rg_gid", "name": "rg_name"})
REL = REL.merge(RG, on="release_group", how="left")
dates = []
for f, cols in (("release_country", ["release", "country", "y", "m", "d"]), ("release_unknown_country", ["release", "y", "m", "d"])):
    x = read(f, cols, usecols=["release", "y"])
    dates.append(x[x.release.isin(rels)])
DT = pd.concat(dates).dropna()
DT["y"] = DT.y.astype(int)
REL = REL.merge(DT.groupby("release").y.min().rename("first_year"), left_on="id", right_index=True, how="left")

# release-level conductor / orchestra
rcl, rol = links_of(LT_COND_REL), links_of(LT_ORCH_REL)
ars = read("l_artist_release", ["id", "link", "e0", "e1", "ep", "lu", "lo", "c0", "c1"], usecols=["link", "e0", "e1"])
ARS = ars[ars.e1.isin(rels) & (ars.link.isin(rcl) | ars.link.isin(rol))].copy()
ARS["role"] = ARS.link.map(lambda l: "conductor" if l in rcl else "orchestra")

# wikidata map
U = pd.concat([ch[ch.url.str.contains(r"wikidata\.org/.*/Q\d+$", na=False, regex=True)]
               for ch in read("url", ["id", "gid", "url", "ep", "lu"], usecols=["id", "url"], chunks=True)])
lau = read("l_artist_url", ["id", "link", "e0", "e1", "ep", "lu", "lo", "c0", "c1"], usecols=["e0", "e1"])
lau = lau[lau.e1.isin(set(U.id))].merge(U, left_on="e1", right_on="id")
lau["q"] = lau.url.str.extract(r"(Q\d+)")
AW = lau[["e0", "q"]].rename(columns={"e0": "artist"}).merge(A[["id", "gid", "name", "sort_name", "type"]], left_on="artist", right_on="id").drop(columns="id")

# write
RW.rename(columns={"e0": "recording", "e1": "work"}).to_csv(os.path.join(OUT, "bsym_recording_work.csv"), index=False)
AR.rename(columns={"e0": "artist", "e1": "recording"}).to_csv(os.path.join(OUT, "bsym_artist_recording.csv"), index=False)
REC.to_csv(os.path.join(OUT, "bsym_recording.csv"), index=False)
ACN.to_csv(os.path.join(OUT, "bsym_credit.csv"), index=False)
TR.to_csv(os.path.join(OUT, "bsym_tracks.csv"), index=False)
MED.to_csv(os.path.join(OUT, "bsym_medium.csv"), index=False)
REL.to_csv(os.path.join(OUT, "bsym_releases.csv"), index=False)
ARS.rename(columns={"e0": "artist", "e1": "release"}).to_csv(os.path.join(OUT, "bsym_artist_release.csv"), index=False)
AW.to_csv(os.path.join(OUT, "artists_wikidata.csv"), index=False)
A[A.id.isin(set(AR.e0) | set(ACN.artist) | set(ARS.e0))].to_csv(os.path.join(OUT, "bsym_artists.csv"), index=False)
print("done: tracks", len(TR), "releases", len(REL), "wikidata artists", len(AW))
