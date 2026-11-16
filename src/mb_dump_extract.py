"""Stream mbdump.tar.bz2 once and write only the tables we need (bytes as-is).
Usage: python -I mb_extract.py <mbdump.tar.bz2> <outdir>
"""
import sys, tarfile, shutil, os, time

WANT = {"artist", "url", "l_artist_url", "link", "link_type", "l_artist_recording", "l_artist_release",
        "l_artist_work", "l_recording_work", "work", "l_work_work", "recording", "track", "medium",
        "release", "release_group", "artist_credit_name", "release_country", "release_unknown_country"}

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
t0 = time.time()
with tarfile.open(src, "r|bz2") as tar:
    for m in tar:
        base = m.name.split("/")[-1]
        if m.name.startswith("mbdump/") and base in WANT and m.isfile():
            f = tar.extractfile(m)
            with open(os.path.join(out, base), "wb") as g:
                shutil.copyfileobj(f, g, 1 << 22)
            print(f"{time.time()-t0:7.0f}s  {base}  {m.size/1e6:,.0f} MB", flush=True)
        elif m.name in ("TIMESTAMP", "SCHEMA_SEQUENCE", "REPLICATION_SEQUENCE", "COPYING"):
            f = tar.extractfile(m)
            with open(os.path.join(out, m.name), "wb") as g:
                shutil.copyfileobj(f, g)
print("done", round(time.time() - t0), "s")
