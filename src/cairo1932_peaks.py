"""Scale peaks from the 1932 Cairo Congress recordings (1.7): data/derived/scales_cairo1932.csv

  python src/cairo1932_peaks.py

Source: B. Bozkurt, "An Open Research Dataset of the 1932 Cairo Congress of Arab Music (ORD-CC32)",
arXiv:2506.14503 (2025); data Zenodo 10.5281/zenodo.15682346, file CairoCong1932_features_plots_2025-06-17.zip,
CC BY-NC 4.0. Put the zip in data/raw/ordcc32/ (not in git).

Method, following the dataset's own code (code/tuning_analysis.py, code/common_tools.py):
  * recordings with a maqam tag, a manual tonic label and vocal-only = False, minus the authors' exclude list;
  * for each, the tonic-aligned octave-folded mean histogram (60 bins of 20 cents), normalised to sum 1;
  * average over the recordings of one maqam x region;
  * maxima: rotate the minimum to bin 0, local maxima, 3-point parabolic interpolation.
The dataset stores features as Python pickles. They are read with a whitelisting unpickler that accepts
only the numpy reconstruction functions the files use (checked with pickletools), so no other code can run.
"""
from __future__ import annotations

import io
import pickle
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ZIP = ROOT / "data/raw/ordcc32/CairoCong1932_features_plots_2025-06-17.zip"
OUT = ROOT / "data/derived/scales_cairo1932.csv"
EXCLUDE = ["CD 6/11.", "CD 6/12.", "CD 8/04.", "CD 15/01.", "CD 15/05.", "CD 18/04."]  # authors' list, tuning_analysis.py
GROUPS = [("rast", "Egypt"), ("rast", "Iraq"), ("bayati", "Egypt"), ("bayati", "Iraq")]
BINS = 60

_ALLOW = {("numpy.core.multiarray", "_reconstruct"), ("numpy._core.multiarray", "_reconstruct"),
          ("numpy", "ndarray"), ("numpy", "dtype"),
          ("numpy.core.multiarray", "scalar"), ("numpy._core.multiarray", "scalar")}


class _NumpyOnly(pickle.Unpickler):
    def find_class(self, module, name):
        if (module, name) not in _ALLOW:
            raise pickle.UnpicklingError(f"blocked {module}.{name}")
        import importlib
        return getattr(importlib.import_module(module.replace("numpy.core", "numpy._core")), name)


def peaks(h: np.ndarray) -> list[tuple[float, float]]:
    sh = int(np.argmin(h))
    r = np.roll(h, -sh)
    out = []
    for i in range(1, len(r) - 1):
        if r[i] > r[i - 1] and r[i] > r[i + 1]:
            y0, y1, y2 = r[i - 1], r[i], r[i + 1]
            a, b = (y0 - 2 * y1 + y2) / 2, (y2 - y0) / 2
            x = i - b / (2 * a) if a != 0 else i
            out.append((((x + sh) % BINS) * 1200 / BINS, float(np.interp(x, np.arange(len(r)), r))))
    return sorted(out)


def main() -> None:
    z = zipfile.ZipFile(ZIP)
    meta = pd.read_csv(io.BytesIO(z.read("allfiles_metadata.csv")))
    pick = {}
    for n in z.namelist():
        if n.endswith(".pickle"):
            cd, rest = n.split("/", 1)
            pick[(cd, rest.split(".")[0])] = n
    rows = []
    for mode, region in GROUPS:
        sel = meta[(meta["mode"] == mode) & (meta["region"] == region) & (~meta["vocal-only"].astype(bool)) & meta["tonic_Hz"].notna()]
        hs, used = [], []
        for path in sel["path"]:
            if any(path.startswith(e) for e in EXCLUDE):
                continue
            cd, rest = path.split("/", 1)
            d = _NumpyOnly(io.BytesIO(z.read(pick[(cd, rest.split(".")[0])]))).load()
            if "oct_warped_hist_mean_wrt_tonic" in d:
                h = np.asarray(d["oct_warped_hist_mean_wrt_tonic"], float)
                hs.append(h / h.sum())
                used.append(path.split(".")[0])
        avg = np.sum(hs, axis=0)
        pk = peaks(avg)
        top = max(v for _, v in pk)
        for c, v in pk:
            rows.append(dict(maqam=mode, region=region, n_recordings=len(hs), peak_cents=round(c, 3), relative_height=round(v / top, 3),
                             recordings=";".join(used), license="CC-BY-NC-4.0"))
    pd.DataFrame(rows).to_csv(OUT, index=False, encoding="utf-8", lineterminator="\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(rows)} peaks")


if __name__ == "__main__":
    main()
