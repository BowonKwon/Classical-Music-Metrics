"""'Works & history' page (1.2): composer work activity, symphony orchestration,
tempo markings, instrument use (IMSLP, CC BY-SA 4.0) and the historical pitch of a'
(Ellis 1885/1895, public domain). Korean and English.

  build_site.py calls build(lang, path, page_fn).
  python src/history_pages.py   ->  proto/ko.html, proto/en.html (standalone preview)

Reads data/derived/imslp_*.csv (work_activity.py, imslp_history.py) and
data/proto/ellis_pitch_table1.csv (transcription). Genre colors are a validated
5-slot set (dataviz validator, light and dark, adjacent pairs) plus neutral grey.
"""
from __future__ import annotations

import html
import math
import sys
from pathlib import Path

import history_glance
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent  # repository root; default paths do not depend on the working directory

sys.path.insert(0, str(Path(__file__).parent))

LANG = "ko"


def t(ko: str, en: str) -> str:
    return ko if LANG == "ko" else en


GENRES = ["orchestral", "stage", "vocal", "chamber", "keyboard", "other"]
GNAME = {"orchestral": ("관현악", "Orchestral"), "stage": ("극음악", "Stage"), "vocal": ("성악", "Vocal"),
         "chamber": ("실내악", "Chamber"), "keyboard": ("건반", "Keyboard"), "other": ("기타", "Other")}
GCSS = """
:root{--g1:#3a6fb0;--g2:#b5833f;--g3:#2e9a7c;--g4:#7f63ad;--g5:#c24f4f;--g6:#a7a49c}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--g1:#5a8ccf;--g2:#b5863a;--g3:#2f9e7e;--g4:#9078c4;--g5:#d0605e;--g6:#5f6168}}
:root[data-theme="dark"]{--g1:#5a8ccf;--g2:#b5863a;--g3:#2f9e7e;--g4:#9078c4;--g5:#d0605e;--g6:#5f6168}
.panel{margin:0 0 .4rem}.panel h3{margin:.9rem 0 .2rem;font-size:.95rem}.grid2{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:.6rem 1rem}
.box{background:color-mix(in srgb,var(--accent) 7%,var(--card));border:1px solid color-mix(in srgb,var(--accent) 25%,var(--line));border-radius:8px;padding:.6rem .9rem;font-size:.92rem;margin:.6rem 0 1.2rem}
.toc a{margin-right:1rem}
"""
ORDER = ["Bach, Johann Sebastian", "Haydn, Franz Joseph", "Mozart, Wolfgang Amadeus", "Beethoven, Ludwig van", "Schubert, Franz",
         "Brahms, Johannes", "Tchaikovsky, Pyotr Ilyich", "Dvorak, Antonín", "Mahler, Gustav", "Stravinsky, Igor"]
TEMPO = ["slow", "moderately slow", "moderate", "moderately fast", "fast", "very fast"]
TEMPO_KO = {"slow": "느림", "moderately slow": "보통 느림", "moderate": "보통", "moderately fast": "보통 빠름", "fast": "빠름", "very fast": "매우 빠름"}
TEMPO_C = ["#2b5a92", "#8fb0d6", "#c4c1b8", "#dcb57a", "#b5833f", "#7d5420"]  # diverging: slow (blue) | neutral | fast (sand)
RAMP = ["#e9f1fc", "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]  # sequential blue
INSTR_ORDER = ["harpsichord / continuo", "oboe", "horn", "bassoon", "flute", "trumpet", "timpani", "clarinet", "piccolo", "trombone",
               "contrabassoon", "English horn", "other percussion", "harp", "tuba", "bass clarinet", "celesta", "piano", "organ", "saxophone"]
INSTR_KO = {"harpsichord / continuo": "하프시코드·통주저음", "oboe": "오보에", "horn": "호른", "bassoon": "바순", "flute": "플루트",
            "trumpet": "트럼펫", "timpani": "팀파니", "clarinet": "클라리넷", "piccolo": "피콜로", "trombone": "트롬본",
            "contrabassoon": "콘트라바순", "English horn": "잉글리시 호른", "other percussion": "그 밖의 타악기", "harp": "하프",
            "tuba": "튜바", "bass clarinet": "베이스 클라리넷", "celesta": "첼레스타", "piano": "피아노", "organ": "오르간", "saxophone": "색소폰"}
PITCH_KIND = [("church", "교회·오르간", "Church / organ", "var(--g1)"), ("theatre", "오페라·관현악·극장·악대", "Opera / orchestra / theatre / band", "var(--g2)"),
              ("other", "기타(소리굽쇠·악기 등)", "Other (forks, instruments)", "var(--g6)")]


def esc(s):
    return html.escape("" if s is None else str(s))


def name(c):
    if LANG == "ko":
        from build_site import KO_NAME
        return KO_NAME.get(c, c.split(",")[0])
    return c.split(",")[0]


def gname(g):
    return GNAME[g][0] if LANG == "ko" else GNAME[g][1]


def tname(k):
    return TEMPO_KO[k] if LANG == "ko" else k


def iname(k):
    return INSTR_KO.get(k, k) if LANG == "ko" else k


def ticks(lo, hi, n=5):
    span = hi - lo or 1
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10)), key=lambda s: abs(s - raw))
    v = math.ceil(lo / step) * step
    out = []
    while v <= hi + 1e-9:
        out.append(round(v, 6))
        v += step
    return out


def ribbon(cy, birth, death, ymax, width=900, height=150):
    L, R, T, B = 42, 10, 8, 22
    x0, x1 = birth, death + 1
    pw, ph = width - L - R, height - T - B
    X = lambda v: L + (v - x0) / (x1 - x0) * pw  # noqa: E731
    Y = lambda v: T + ph - v / ymax * ph  # noqa: E731
    bw = max(pw / (x1 - x0) - 1.2, 1)
    o = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{t("연도별 장르별 작품면 수", "work pages per year by genre")}">',
         f'<rect x="{X(birth):.1f}" y="{T}" width="{X(death + 1) - X(birth):.1f}" height="{ph}" fill="var(--bg2)" rx="3"/>']
    for v in ticks(0, ymax, 3):
        o.append(f'<line class="grid" x1="{L}" x2="{width - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text x="{L - 5}" y="{Y(v) + 4:.1f}" text-anchor="end">{v:g}</text>')
    step = 10 if (x1 - x0) <= 60 else 20
    for yv in range(int(math.ceil(x0 / step) * step), x1, step):
        o.append(f'<text x="{X(yv) + bw / 2:.1f}" y="{height - 6}" text-anchor="middle">{yv} <tspan fill="var(--fg3)">({yv - birth}{t("세", "")})</tspan></text>')
    piv = cy.pivot_table(index="year", columns="genre", values="works", aggfunc="sum", fill_value=0)
    for yr, row in piv.iterrows():
        base, parts = 0.0, []
        for gi, g in enumerate(GENRES):
            v = float(row.get(g, 0))
            if v <= 0:
                continue
            y_top, y_bot = Y(base + v), Y(base)
            o.append(f'<rect x="{X(yr):.1f}" y="{y_top:.1f}" width="{bw:.1f}" height="{max(y_bot - y_top - 1.0, 0.6):.1f}" fill="var(--g{gi + 1})"/>')
            parts.append(f"{gname(g)} {v:.1f}")
            base += v
        o.append(f'<rect x="{X(yr):.1f}" y="{T}" width="{bw:.1f}" height="{ph}" fill="transparent"><title>{yr} ({t(f"{yr - birth}세", f"age {yr - birth}")}): {base:.1f} — {", ".join(parts)}</title></rect>')
    o.append("</svg>")
    return "".join(o)


def small_line(pts, xlo, xhi, ymax, fmt=".0%", width=300, height=130, color="var(--g1)", xsuffix=""):
    L, R, T, B = 36, 8, 8, 20
    pw, ph = width - L - R, height - T - B
    X = lambda v: L + (v - xlo) / (xhi - xlo) * pw  # noqa: E731
    Y = lambda v: T + ph - v / ymax * ph  # noqa: E731
    o = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for v in ticks(0, ymax, 3):
        o.append(f'<line class="grid" x1="{L}" x2="{width - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text x="{L - 4}" y="{Y(v) + 4:.1f}" text-anchor="end">{format(v, fmt)}</text>')
    step = 20 if (xhi - xlo) <= 100 else 40
    for xv in range(int(math.ceil(xlo / step) * step), int(xhi) + 1, step):
        o.append(f'<text x="{X(xv):.1f}" y="{height - 5}" text-anchor="middle">{xv}{xsuffix}</text>')
    if pts:
        area = f"M{X(pts[0][0]):.1f},{Y(0):.1f} " + " ".join(f"L{X(a):.1f},{Y(b):.1f}" for a, b in pts) + f" L{X(pts[-1][0]):.1f},{Y(0):.1f} Z"
        o.append(f'<path d="{area}" fill="{color}" fill-opacity=".14"/>')
        o.append('<path d="' + " ".join(f"{'M' if i == 0 else 'L'}{X(a):.1f},{Y(b):.1f}" for i, (a, b) in enumerate(pts)) + f'" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>')
        for a, b in pts:
            o.append(f'<circle cx="{X(a):.1f}" cy="{Y(b):.1f}" r="6" fill="transparent"><title>{a:g}{xsuffix}: {format(b, fmt)}</title></circle>')
    o.append("</svg>")
    return "".join(o)


def creation_vs_reception(df, width=300, height=140):
    L, R, T, B = 36, 8, 8, 20
    pw, ph = width - L - R, height - T - B
    x0, x1 = df["bin_start"].min(), df["bin_start"].max() + 5
    ymax = max(df["works_share"].max(), df["nyphil_share"].max()) * 1.15 or 1
    X = lambda v: L + (v - x0) / (x1 - x0) * pw  # noqa: E731
    Y = lambda v: T + ph - v / ymax * ph  # noqa: E731
    o = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for v in ticks(0, ymax, 3):
        o.append(f'<line class="grid" x1="{L}" x2="{width - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text x="{L - 4}" y="{Y(v) + 4:.1f}" text-anchor="end">{v:.0%}</text>')
    bw = pw / ((x1 - x0) / 5) - 3
    for r in df.itertuples():
        o.append(f'<rect x="{X(r.bin_start) + 1.5:.1f}" y="{Y(r.works_share):.1f}" width="{bw:.1f}" height="{max(Y(0) - Y(r.works_share), 0.5):.1f}" fill="var(--g6)" rx="2"><title>{r.bin_start}–{r.bin_start + 4}: {t("작품면", "work pages")} {r.works_share:.0%}</title></rect>')
    for r in df.itertuples():
        if pd.notna(r.nyphil_share) and r.nyphil_share > 0:
            o.append(f'<circle cx="{X(r.bin_start) + 1.5 + bw / 2:.1f}" cy="{Y(r.nyphil_share):.1f}" r="4.5" fill="var(--g1)" stroke="var(--card)" stroke-width="2"><title>{r.bin_start}–{r.bin_start + 4}: {t("뉴욕 필 연주", "NY Phil performances")} {r.nyphil_share:.0%}</title></circle>')
    step = 10 if (x1 - x0) <= 50 else 20
    for xv in range(int(math.ceil(x0 / step) * step), int(x1), step):
        o.append(f'<text x="{X(xv):.1f}" y="{height - 5}" text-anchor="middle">{xv}</text>')
    o.append("</svg>")
    return "".join(o)


def scatter(df, width=900, height=320):
    L, R, T, B = 46, 14, 14, 30
    pw, ph = width - L - R, height - T - B
    x0, x1 = df.year_start.min() - 5, df.year_start.max() + 5
    ymax = df.orch_parts.max() * 1.08
    X = lambda v: L + (v - x0) / (x1 - x0) * pw  # noqa: E731
    Y = lambda v: T + ph - v / ymax * ph  # noqa: E731
    o = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="symphony orchestration">']
    for v in ticks(0, ymax, 5):
        o.append(f'<line class="grid" x1="{L}" x2="{width - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{v:g}</text>')
    for xv in range(int(math.ceil(x0 / 25) * 25), int(x1), 25):
        o.append(f'<text x="{X(xv):.1f}" y="{height - 10}" text-anchor="middle">{xv}</text>')
    o.append(f'<text x="{L}" y="10">{t("관악·타악·건반 파트 수", "wind, brass, percussion and keyboard parts")}</text>')
    for r in df.itertuples():
        o.append(f'<circle cx="{X(r.year_start):.1f}" cy="{Y(r.orch_parts):.1f}" r="4" fill="var(--g1)" fill-opacity=".55" stroke="var(--card)" stroke-width="1.5"><title>{esc(name(r.composer))} {esc(r.work_title)} ({int(r.year_start)}): {int(r.orch_parts)}</title></circle>')
    med = df.groupby((df.year_start // 10) * 10)["orch_parts"].median()
    pts = [(y + 5, v) for y, v in med.items()]
    o.append('<path d="' + " ".join(f"{'M' if i == 0 else 'L'}{X(a):.1f},{Y(b):.1f}" for i, (a, b) in enumerate(pts)) + '" fill="none" stroke="var(--fg)" stroke-width="2"/>')
    o.append("</svg>")
    return "".join(o)


def stacked100(tp, bins, width=900, height=260):
    L, R, T, B = 46, 10, 10, 26
    pw, ph = width - L - R, height - T - B
    bw = pw / len(bins)
    o = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="tempo classes by period">']
    for v in (0, .25, .5, .75, 1):
        y = T + ph - v * ph
        o.append(f'<line class="grid" x1="{L}" x2="{width - R}" y1="{y:.1f}" y2="{y:.1f}"/><text x="{L - 5}" y="{y + 4:.1f}" text-anchor="end">{v:.0%}</text>')
    for i, b0 in enumerate(bins):
        g = tp[tp.bin == b0].set_index("tempo_class")
        base = 0.0
        x = L + i * bw + 3
        for k, c in zip(TEMPO, TEMPO_C):
            v = float(g["share"].get(k, 0.0))
            if v <= 0:
                continue
            o.append(f'<rect x="{x:.1f}" y="{T + ph - (base + v) * ph:.1f}" width="{bw - 6:.1f}" height="{max(v * ph - 2, 0.5):.1f}" fill="{c}"><title>{b0}–{b0 + 24} · {tname(k)}: {v:.0%} ({int(g["movements"].iloc[0])})</title></rect>')
            base += v
        o.append(f'<text x="{x + (bw - 6) / 2:.1f}" y="{height - 8}" text-anchor="middle">{b0}</text>')
    o.append("</svg>")
    return "".join(o)


def heatmap(iu, bins, instruments, width=900):
    L, T, cell_h = 150, 22, 22
    cw = (width - L - 10) / len(bins)
    height = T + cell_h * len(instruments) + 6
    o = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="instrument use by period">']
    for j, b0 in enumerate(bins):
        o.append(f'<text x="{L + j * cw + cw / 2:.1f}" y="14" text-anchor="middle">{b0}</text>')
    for i, ins in enumerate(instruments):
        y = T + i * cell_h
        o.append(f'<text x="{L - 8}" y="{y + cell_h * .68:.1f}" text-anchor="end">{esc(iname(ins))}</text>')
        for j, b0 in enumerate(bins):
            r = iu[(iu.instrument == ins) & (iu.bin == b0)]
            if r.empty:
                continue
            v = float(r.share.iloc[0])
            idx = min(int(v * (len(RAMP) - 1) + 0.5), len(RAMP) - 1)
            ink = "#ffffff" if idx >= 5 else "#1d1f24"
            o.append(f'<rect x="{L + j * cw + 1:.1f}" y="{y + 1}" width="{cw - 2:.1f}" height="{cell_h - 2}" fill="{RAMP[idx]}" rx="3"><title>{esc(iname(ins))} · {b0}–{b0 + 24}: {v:.0%} (n={int(r.symphonies.iloc[0])})</title></rect>')
            if v >= 0.05:
                o.append(f'<text x="{L + j * cw + cw / 2:.1f}" y="{y + cell_h * .68:.1f}" text-anchor="middle" style="fill:{ink};font-size:10px">{v * 100:.0f}</text>')
    o.append("</svg>")
    return "".join(o)


PITCH_BUILDING = ("church", "cathedral", "chapel", "minster", "abbey", "kirche")
PITCH_THEATRE = ("opera", "orchestra", "theatre", "theater", "conservatoire", "philharmonic", "concert", "band",
                 "military", "army")


def pitch_kind(particulars) -> str:
    """Rough grouping by use. A maker's trade ('organ-builder') is not a use, so it is removed before matching;
    a named opera / orchestra / band use wins over the bare word 'organ' unless a church building is named."""
    p = (particulars if isinstance(particulars, str) else "").lower()
    for trade in ("organ-builders", "organ-builder", "organ builders", "organ builder", "organists", "organist"):
        p = p.replace(trade, " ")
    if "mersenne's chamber pitch" in p:  # names a Hamburg church only for comparison
        return "other"
    building = p.startswith("*") or any(w in p for w in PITCH_BUILDING)
    if not building and any(w in p for w in PITCH_THEATRE):
        return "theatre"
    if building or "organ" in p:
        return "church"
    if any(w in p for w in PITCH_THEATRE):
        return "theatre"
    return "other"


def pitch_scatter(df, width=900, height=380):
    L, R, T, B = 50, 14, 14, 30
    pw, ph = width - L - R, height - T - B
    x0, x1, y0, y1 = 1350, 1890, 360, 580
    X = lambda v: L + (v - x0) / (x1 - x0) * pw  # noqa: E731
    Y = lambda v: T + ph - (v - y0) / (y1 - y0) * ph  # noqa: E731
    o = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="historical pitch of a">']
    for v in range(380, 581, 40):
        o.append(f'<line class="grid" x1="{L}" x2="{width - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text x="{L - 6}" y="{Y(v) + 4:.1f}" text-anchor="end">{v}</text>')
    o.append(f'<line x1="{L}" x2="{width - R}" y1="{Y(440):.1f}" y2="{Y(440):.1f}" stroke="var(--fg3)" stroke-dasharray="4 4"/><text x="{L + 6}" y="{Y(440) - 5:.1f}">440 Hz</text>')
    for xv in range(1350, 1891, 50):
        o.append(f'<text x="{X(xv):.1f}" y="{height - 10}" text-anchor="middle">{xv}</text>')
    o.append(f'<text x="{L}" y="10">{t("a′ 진동수 (Hz)", "frequency of a′ (Hz)")}</text>')
    col = {k: c for k, _, _, c in PITCH_KIND}
    d = df.dropna(subset=["year"])
    for r in d.itertuples():
        unc = r.date_qualifier in ("before", "after", "circa", "range")
        place = esc(r.place) if isinstance(r.place, str) else ""
        o.append(f'<circle cx="{X(r.year):.1f}" cy="{Y(r.vib):.1f}" r="4.2" fill="{col[r.kind]}" fill-opacity="{0.45 if unc else 0.8}" stroke="var(--card)" stroke-width="1.5"><title>{esc(r.date_raw)} · {place}: a′ {r.vib:g} Hz — {esc(str(r.particulars)[:110])} ({esc(r.authority)})</title></circle>')
    grp = d.groupby((d.year // 25) * 25)
    med = grp["vib"].median()[grp.size() >= 5]
    pts = [(y + 12.5, v) for y, v in med.items()]
    if len(pts) > 1:
        o.append('<path d="' + " ".join(f"{'M' if i == 0 else 'L'}{X(a):.1f},{Y(b):.1f}" for i, (a, b) in enumerate(pts)) + '" fill="none" stroke="var(--fg)" stroke-width="2"/>')
    o.append("</svg>")
    return "".join(o)


def table(df, cols, tid):
    h = "".join(f"<th class='{'num' if f else ''}'>{esc(n)}</th>" for _, n, f in cols)
    rows = []
    for _, r in df.iterrows():
        rows.append("<tr>" + "".join(f"<td class='num' data-v='{r[c]}'>{format(r[c], f) if pd.notna(r[c]) else ''}</td>" if f else f"<td>{esc(r[c]) if pd.notna(r[c]) else ''}</td>" for c, _, f in cols) + "</tr>")
    return (f"<details><summary style='cursor:pointer;color:var(--fg2);font-size:.9rem;margin:.3rem 0'>{t('표 보기', 'Show table')} ({len(rows)})</summary>"
            f"<div class='wrap'><table class='sort' id='{tid}'><thead><tr>{h}</tr></thead><tbody>{''.join(rows)}</tbody></table></div></details>")


def files(names, root="../data/"):
    return "<p class='files'>" + "".join(f'<a href="{root}{f}">{f}</a>' for f in names) + "</p>"


def render(lang: str, D: Path = (ROOT / "data/derived"), proto: Path = (ROOT / "data/proto"), data_root="../data/") -> str:
    global LANG
    LANG = lang
    W = pd.read_csv(D / "imslp_works.csv")
    CY = pd.read_csv(D / "imslp_composer_year.csv")
    AC = pd.read_csv(D / "imslp_composer_age.csv")
    RP = pd.read_csv(D / "imslp_reception_period.csv")
    SY = pd.read_csv(D / "imslp_symphony_orchestration.csv")
    MR = pd.read_csv(D / "imslp_nyphil_match_rate.csv")
    TP = pd.read_csv(D / "imslp_tempo_by_period.csv")
    TL = pd.read_csv(D / "imslp_tempo_language.csv")
    IU = pd.read_csv(D / "imslp_instrument_use.csv")
    EP = pd.read_csv(proto / "ellis_pitch_table1.csv")
    wd = pd.read_csv(ROOT / "data/aliases/composer_wikidata.csv").set_index("composer")
    okb_ = sorted(TL.loc[(TL.movements >= 20) & (TL.recognised_share >= 0.6), "bin"].astype(int).tolist())
    okb2_ = sorted(IU.loc[IU.symphonies >= 20, "bin"].drop_duplicates().astype(int).tolist())
    EPk = EP.assign(kind=EP["particulars"].map(pitch_kind))
    GL = history_glance.boxes(sys.modules[__name__], lang, W, AC, RP, MR, SY, TP, TL, IU, EPk, okb_, okb2_)
    n_term = int((W.year_kind == "terminus").sum())
    n_dated = int(W.year_start.notna().sum())
    legend = '<div class="legend">' + "".join(f'<span style="--c:var(--g{i + 1})">{gname(g)}</span>' for i, g in enumerate(GENRES)) + "</div>"
    im = data_root + "imslp/"
    b = [f"<style>{GCSS}</style>",
         f"<h1>{t('작품 활동과 역사', 'Works & history')}</h1>",
         "<p class='lead'>" + t("작곡가 10명의 작품 활동을 시기별로, 교향곡의 편성·템포 지시어·악기 사용의 변화를 IMSLP 작품면으로, 그리고 A음 높이의 역사를 Ellis 의 19세기 측정표로 본다. 1.2 에서 더했다.",
                               "Ten composers' work activity over their lives, changes in symphonic orchestration, tempo markings and instrument use from IMSLP work pages, and the history of the pitch of a′ from Ellis's 19th-century tables. Added in 1.2.") + "</p>",
         "<p class='toc'>" + "".join(f"<a href='#s{i}'>{i}. {x}</a>" for i, x in enumerate([t("경력 띠", "Career ribbons"), t("나이별 작품면", "Work pages by age"), t("쓴 시기와 연주 비율", "When it was written, how much it is played"),
                                                                                              t("교향곡 편성", "Symphony orchestration"), t("템포 지시어", "Tempo markings"), t("악기 사용", "Instrument use"), t("A음 높이", "Pitch of a′")], 1)) + "</p>",
         "<div class='box'>" + t(f"단위는 <b>IMSLP 작품면</b>이다 — 한 곡이 여러 면이거나 여러 곡이 한 면인 경우가 있어 「작곡한 작품 수」와 같지 않다. 10명의 작품면 {len(W):,}개(다른 작곡가로 재귀속돼 넘어간 면과 다른 작곡가 이름의 면은 뺐다), 작곡 연도가 적힌 면 {n_dated:,}개 가운데 「~이전/이후」처럼 한계만 적힌 {n_term}개는 연도 집계에서 뺐다. 수용은 뉴욕 필 공연 기록을 작품번호로 매칭했다.",
                                 f"The unit is the <b>IMSLP work page</b>: one work can span several pages and one page can hold several works, so this is not a count of works composed. {len(W):,} pages for the ten composers (pages re-attributed to, or titled under the name of, another composer are dropped); of the {n_dated:,} with a composition year, {n_term} that give only a bound ('before', 'after') are left out of year-based counts. Reception uses the NY Phil archive, matched by catalog number.") + "</div>"]
    # 1
    b.append(f"<h2 id='s1'>1. {t('경력 띠 — 해마다 무엇을 썼나', 'Career ribbons — what was written each year')}</h2>{GL[1]}<p>"
             + t("연도별 작품면 수(작곡 기간이 여러 해면 해마다 나누어 셈. 개정·후대 판본 연도는 넣지 않았다)를 장르별로 쌓았다. 옅은 바탕은 생애. 막대에 마우스를 올리면 그해 내역이 나온다. 작곡가마다 세로축이 다르다.",
                 "Work pages per year by genre (a work dated over several years is split evenly across them; revision and later-version dates are not included). The pale band is the lifespan. Hover over a bar to see that year's breakdown. Each composer's panel has its own vertical scale.") + "</p>" + legend)
    for c in ORDER:
        cy = CY[CY.composer == c]
        if cy.empty:
            continue
        bth, dth = int(wd.loc[c, "birth_year"]), int(wd.loc[c, "death_year"])
        ymax = max(cy.groupby("year")["works"].sum().max(), 1) * 1.05
        n = int((W.composer == c).sum())
        nd = int(((W.composer == c) & W.year_start.notna() & (W.year_kind != "terminus")).sum())
        b.append(f"<div class='panel'><h3>{esc(name(c))} <small style='color:var(--fg3);font-weight:400'>{bth}–{dth} · {t('작품면', 'pages')} {n} · {t('연도 확인', 'dated')} {nd}</small></h3><figure style='margin:.2rem 0;padding:.5rem .6rem'>{ribbon(cy, bth, dth, ymax)}</figure></div>")
    gt = W.groupby(["composer", "genre"]).size().unstack(fill_value=0).reindex(columns=GENRES, fill_value=0).reindex(ORDER).reset_index()
    gt["composer"] = gt["composer"].map(name)
    b.append(table(gt.rename(columns={g: gname(g) for g in GENRES}), [("composer", t("작곡가", "Composer"), None)] + [(gname(g), gname(g), "d") for g in GENRES], "gt"))
    # 2
    b.append(f"<h2 id='s2'>2. {t('나이별 작품면 비율 — 몇 살에 가장 많이 썼나', 'Work pages by age — when did they write most?')}</h2>{GL[2]}<p>"
             + t("작곡 연도가 확인된 작품면을 작곡 연도와 출생 연도의 차(만 나이가 아니다) 5년 구간으로 묶은 비율. 곡의 길이·규모는 통제하지 않아 「노동량」 비교가 아니다. 모든 칸이 같은 축(0~90세)이다.",
                 "Share of dated work pages by five-year bands of composition year minus birth year (not exact age). Length and scale are not controlled, so this is not a comparison of workload. All panels share one axis (age 0–90).") + "</p><div class='grid2'>")
    amax = AC.share.max() * 1.1
    for c in ORDER:
        a = AC[AC.composer == c].sort_values("age_bin")
        if a.empty:
            continue
        pk = a.loc[a.share.idxmax()]
        b.append(f"<div><h3 style='margin:.4rem 0 .1rem;font-size:.92rem'>{esc(name(c))} <small style='color:var(--fg3);font-weight:400'>{t('정점', 'peak')} {int(pk.age_bin)}–{int(pk.age_bin) + 4} {pk.share:.0%}</small></h3>{small_line([(r.age_bin, r.share) for r in a.itertuples()], 0, 90, amax, xsuffix=t('세', ''))}</div>")
    b.append("</div>")
    # 3
    b.append(f"<h2 id='s3'>3. {t('쓴 시기와 연주 비율', 'When it was written, how much it is played')}</h2>{GL[3]}<p>"
             + t("회색 막대는 작곡 시기(5년)별 작품면 비율, 파란 점은 <b>작곡 연도까지 매칭된</b> 뉴욕 필 연주(작품 연주 U1) 가운데 그 시기에 쓴 작품의 비율. 가로축은 연주 시점이 아니라 작곡 시기다. 같은 % 축이다. 점이 막대보다 높으면 그 시기 작품이 상대적으로 많이 연주된다. 한 오케스트라의 기록이다.",
                 "Gray bars: share of work pages composed in each five-year period. Blue dots: of the NY Phil work performances (U1) <b>matched to a dated page</b>, the share that falls on works from that period. The horizontal axis is the composition period, not the performance date; both are plotted on the same % axis. A dot above its bar means works from that period are played more than their share. One orchestra's record.") + "</p>"
             + f'<div class="legend"><span style="--c:var(--g6)">{t("작품면 비율", "share of work pages")}</span><span style="--c:var(--g1)">{t("뉴욕 필 연주 비율", "share of NY Phil performances")}</span></div><div class="grid2">')
    for c in ORDER:
        r = RP[RP.composer == c]
        mr = MR[MR.composer == c]
        if r.empty or mr.empty or mr.iloc[0].dated_u1_share < 0.5:
            continue
        b.append(f"<div><h3 style='margin:.4rem 0 .1rem;font-size:.92rem'>{esc(name(c))} <small style='color:var(--fg3);font-weight:400'>{t('연도까지 매칭', 'matched and dated')} {mr.iloc[0].dated_u1_share:.0%}</small></h3>{creation_vs_reception(r)}</div>")
    b.append("</div><p class='src'>" + t("스트라빈스키는 작품번호가 없어 매칭하지 못해 뺐다.", "Stravinsky is left out: his works carry no catalog numbers to match.") + "</p>")
    b.append(table(MR.assign(composer=MR.composer.map(name)), [("composer", t("작곡가", "Composer"), None), ("u1", t("뉴욕 필 작품 연주", "NY Phil work perf."), ".0f"), ("matched_u1_share", t("매칭", "matched"), ".0%"), ("dated_u1_share", t("연도까지", "dated"), ".0%")], "mr"))
    # 4
    b.append(f"<h2 id='s4'>4. {t('교향곡 편성 — 관악·타악·건반 파트 수', 'Symphony orchestration — wind, brass, percussion and keyboard parts')}</h2>{GL[4]}<p>"
             + t(f"이 10명의 교향곡 가운데 IMSLP 편성 상세가 있는 {len(SY)}곡(합창이 있는 교향곡 포함). 점 하나가 교향곡 하나, 검은 선은 10년 구간 중앙값. 편성란에 적힌 비현악 파트를 셌다(현악은 세지 않음, 수가 없는 악기는 1, 괄호 안 악기 포함, 타악기는 개별 악기가 적혀 있으면 그것만). 연주자 수나 악보의 실제 파트 수와 같다는 보장은 없다.",
                 f"The {len(SY)} symphonies by these ten composers whose IMSLP page has instrumentation details (choral symphonies included). One dot per symphony; the black line is the median per decade. Non-string parts as listed (strings not counted; an instrument without a number counts once; bracketed instruments included; percussion counted by named instrument when listed). This need not equal the number of players or of parts in the score.") + f"</p><figure>{scatter(SY)}</figure>")
    b.append(table(SY.sort_values("year_start").assign(composer=SY.composer.map(name)), [("composer", t("작곡가", "Composer"), None), ("work_title", t("작품", "Work"), None), ("year_start", t("연도", "Year"), ".0f"), ("orch_parts", t("파트", "Parts"), ".0f"), ("duration_min", t("연주 시간(분)", "Duration (min)"), ".0f")], "sy"))
    # 5
    okb = sorted(TL.loc[(TL.movements >= 20) & (TL.recognised_share >= 0.6), "bin"].astype(int).tolist())
    b.append(f"<h2 id='s5'>5. {t('템포 지시어의 구성 — 악장 줄에 어떤 템포어가 적혔나', 'Tempo markings — which tempo words the movement lists carry')}</h2>{GL[5]}<p>"
             + t("IMSLP 교향곡 범주(오르간 교향곡·여러 곡 묶음 면·목록 면 제외)의 악장 목록에서 줄마다 사전에 있는 첫 템포어(Adagio·Allegro·Vivo 등, 독일어·프랑스어 지시어 포함)를 뽑아 여섯 단계로 묶었다. <b>연주 속도(BPM)가 아니라 적힌 지시어의 구성</b>이다. 느린 서주가 있는 악장은 서주의 템포어로 잡히고, 판본이 둘 적힌 면은 두 판의 줄이 모두 들어간다. 25년 구간, 인식된 줄이 20개 이상이고 인식률(템포어가 잡힌 줄 / 목록 줄) 60% 이상인 구간만.",
                 "From the movement lists of the IMSLP Symphonies category (organ symphonies, multi-symphony pages and list pages excluded), the first tempo word on each line that is in the site's dictionary (Adagio, Allegro, Vivo …, German and French words included), grouped into six classes. <b>This is the make-up of written markings, not performed speed (BPM).</b> A movement with a slow introduction is classed by the introduction; pages listing two versions contribute both. 25-year bins with at least 20 recognized lines and a recognition rate (lines with a tempo word / listed lines) of at least 60%.") + "</p>"
             + '<div class="legend">' + "".join(f'<span style="--c:{c}">{tname(k)}</span>' for k, c in zip(TEMPO, TEMPO_C)) + f"</div><figure>{stacked100(TP, okb)}</figure>")
    tl = TL[TL.bin.isin(okb)]
    pts = [(int(r.bin), float(r.non_italian_share)) for r in tl.itertuples()]
    b.append(f"<h3>{t('이탈리아어가 아닌 템포 지시어의 비율', 'Share of non-Italian tempo words')}</h3><p>" + t("Langsam·Lebhaft·Modéré·Slowly처럼 자국어로 쓴 템포어가 템포어가 잡힌 줄 가운데 차지하는 비율.", "Tempo words in the vernacular (Langsam, Lebhaft, Modéré, Slowly …) as a share of lines with a recognized tempo word.") + "</p>"
             f"<figure>{small_line(pts, okb[0], okb[-1], max(p[1] for p in pts) * 1.2 or .1, fmt='.0%', width=900, height=200)}</figure>")
    b.append(table(TL[TL.movements >= 20], [("bin", t("25년 구간", "25-year bin"), ".0f"), ("works", t("교향곡", "symphonies"), ".0f"), ("listed_lines", t("목록 줄", "listed lines"), ".0f"), ("movements", t("템포어 인식 줄", "recognized lines"), ".0f"), ("recognised_share", t("인식률", "recognition"), ".0%"), ("non_italian_share", t("비이탈리아어", "non-Italian"), ".1%")], "tl"))
    # 6
    okb2 = sorted(IU.loc[IU.symphonies >= 20, "bin"].drop_duplicates().astype(int).tolist())
    nsy = int(IU.drop_duplicates("bin").loc[lambda d: d.symphonies >= 20, "symphonies"].sum())
    b.append(f"<h2 id='s6'>6. {t('악기 사용 변천 — 교향곡 편성란에 이름이 오른 악기', 'Instrument use — instruments named in symphony instrumentation')}</h2>{GL[6]}<p>"
             + t(f"IMSLP 교향곡 범주 3,140면 가운데 한 곡짜리 관현악 교향곡이면서 작곡 연도와 편성 상세가 모두 있는 {nsy}곡(구간당 20곡 이상인 구간만). 편성 상세가 없는 면이 70%를 넘어 <b>전체 교향곡의 확률 표본이 아니다</b>. 칸의 숫자는 그 25년 구간 교향곡 가운데 편성란에 그 악기 이름이 적힌 비율(%) — 선택·겸용 악기도 「적힘」으로 셌고, 실제 연주 여부나 최초 도입 시점을 뜻하지 않는다. 행 순서는 처음 절반을 넘는 구간 순으로 대략 맞췄다.",
                 f"Of the 3,140 pages in the IMSLP Symphonies category, the {nsy} single orchestral symphonies with both a composition year and instrumentation details (bins with at least 20 only). More than 70% of pages have no detail, so this is <b>not a probability sample of all symphonies</b>. Each cell is the share (%) of that bin's symphonies whose instrumentation names the instrument — optional and doubling instruments count as named; it does not show actual use or first introduction. Rows are roughly ordered by the first bin in which the share exceeds one half.") + f"</p><figure>{heatmap(IU, okb2, INSTR_ORDER)}</figure>")
    piv = IU[IU.bin.isin(okb2)].pivot(index="instrument", columns="bin", values="share").reindex(INSTR_ORDER).reset_index()
    piv["instrument"] = piv["instrument"].map(iname)
    piv.columns = [str(c) for c in piv.columns]
    b.append(table(piv, [("instrument", t("악기", "Instrument"), None)] + [(str(x), str(x), ".0%") for x in okb2], "iu"))
    # 7
    EP = EP.copy()
    EP["kind"] = EP["particulars"].map(pitch_kind)
    ed = EP.dropna(subset=["year"])
    kc = ed["kind"].value_counts()
    b.append(f"<h2 id='s7'>7. {t('A음 높이의 역사 — 1361~1880년대 a′ 의 진동수', 'The pitch of a′, 1361 to the 1880s')}</h2>{GL[7]}<p>"
             + t(f"A. J. Ellis 가 모은 역사적 음고 표(헬름홀츠 『On the Sensations of Tone』 영역 3판 1895, 부록 XX 섹션 H Table I, 495~504쪽 — 퍼블릭 도메인)를 쪽 이미지에서 옮기고 1885년 2판과 전부 대조한 {len(EP)}행 가운데 연도가 있는 {len(ed)}행. 점 하나가 Ellis 가 모은 a′ 기록 하나다. 대부분은 소리굽쇠·오르간 파이프·악기에서 잰 값이지만, 남은 파이프나 문헌에서 계산한 값과 제안·채택된 기준값(예: 1860년 Society of Arts 의 시행되지 않은 기준안, 1885년 런던 발명·음악 박람회의 채택값)도 있다. 가로축은 표에 적힌 연도라서 늘 측정한 해는 아니다. 오르간은 건립 연도가 붙은 것이 있고(1361년 할버슈타트 오르간은 프레토리우스가 적은 파이프 치수로 Ellis 가 모형을 만들어 계산한 값이다), 「1740~1812」 같은 기간은 첫해에 찍었다. 흐린 점은 연도가 「~이전/이후/무렵」이거나 기간인 것. 검은 선은 25년 구간 중앙값(5점 이상 구간)으로, 장소·기구·측정법이 다른 기록을 같은 무게로 합친 값이다. 점이 드문 구간을 건너 이어지므로 선이 지나는 해에 자료가 있다는 뜻은 아니다. 색은 설명 칸의 낱말로 나눈 용도의 대략의 구분이다. 제작자의 직업(오르간 제작자)은 용도로 보지 않았고, 교회 건물 이름이 없으면 오페라·관현악·악대 용도를 오르간보다 앞세웠다. 오페라 극장의 오르간처럼 둘에 걸치는 기록이 있어 시기별 용도 비교에는 쓰지 않는 편이 좋다. 같은 시기에도 장소와 용도에 따라 100 Hz 넘게 벌어진다. 이것은 측정된 표본의 분포이지 각 시대의 「표준」이 아니다. 표는 1880년대에서 끝난다.",
                 f"A. J. Ellis's table of historical pitches (Helmholtz, On the Sensations of Tone, tr. Ellis, 3rd ed. 1895, Appendix XX, Section H, Table I, pp. 495–504 — public domain), transcribed from the page images and checked line by line against the 2nd edition of 1885: {len(ed)} of {len(EP)} rows have a date. Each dot is one a′ record collected by Ellis. Most were measured from a fork, organ pipe or instrument, but some are computed from surviving pipes or from documents, and some are proposed or adopted standards (for example the Society of Arts' unexecuted standard of 1860 and the pitch adopted by the London Inventions and Music Exhibition of 1885). The horizontal axis is the date given in the table, which is not always the year of measurement: some organs carry the year they were built (the value for the Halberstadt organ of 1361 is Ellis's calculation from a model built to the pipe dimensions given by Praetorius), and periods such as 1740–1812 are plotted at their first year. Faint dots have dates given as before / after / about, or as a period. The black line is the median per 25-year bin (bins with five or more points); it weights records of different places, instruments and methods equally, and because it joins across sparse bins, a line passing through a year does not mean there are records for that year. Colors are a rough grouping by use, from words in the description. A maker's trade (organ-builder) is not treated as a use, and an opera, orchestra or band use takes precedence over the word 'organ' unless a church building is named. Some records belong to both, such as an organ in an opera house, so the colors are not suited to comparing uses across periods. Pitches of the same period differ by more than 100 Hz depending on place and use. This is the spread of the measured sample, not each era's 'standard'. The table ends in the 1880s.") + "</p>"
             + '<div class="legend">' + "".join(f'<span style="--c:{c}">{(k_ko if LANG == "ko" else k_en)} ({int(kc.get(k, 0))})</span>' for k, k_ko, k_en, c in PITCH_KIND) + f"</div><figure>{pitch_scatter(EP)}</figure>")
    kname = {k: (k_ko if LANG == "ko" else k_en) for k, k_ko, k_en, _ in PITCH_KIND}
    b.append(table(EP.assign(year=EP.year.astype("Int64").astype(str).replace("<NA>", ""), kind=EP.kind.map(kname)), [("vib", "a′ (Hz)", ".1f"), ("cents", t("센트", "cents"), ".0f"), ("date_raw", t("연도(원문)", "date (as printed)"), None), ("place", t("장소", "place"), None), ("particulars", t("설명", "particulars"), None), ("authority", t("관측", "observer"), None), ("kind", t("구분", "group"), None), ("page", t("쪽", "page"), ".0f")], "ep"))
    b.append("<p class='src'>" + t("자료", "Sources") + ": <a href='https://archive.org/details/onsensationsofto00helmrich'>Helmholtz, On the Sensations of Tone, tr. A. J. Ellis, 3rd ed. 1895</a> (Internet Archive); "
             + t("대조", "checked against") + " <a href='https://archive.org/details/onsensationston00unkngoog'>2nd ed. 1885</a>. "
             + t("옮겨 적으며 찾은 두 판의 차이 22건(대소문자·문장 부호 포함. 센트 1건 — 1885년판의 오식 300 → 330, 진동수 0건)은 전사 CSV 의 note 칸에 있다. Table II 는 Table I 을 용도별로 다시 엮은 색인이라 두 표를 합쳐 독립된 관측 수로 셀 수 없고, 진동수가 없는 서술 기록 6행이 들어 있다.", "The 22 differences between the editions found during transcription (capitals and punctuation included; one in cents — the 1885 misprint 300 for 330 — and none in frequency) are recorded in the note column of the transcription. Table II regroups Table I by use, so the two tables cannot be added up as independent observations; it also has six descriptive rows without a frequency.") + "</p>")
    b.append(files(["ellis/ellis_pitch_table1.csv", "ellis/ellis_pitch_table2.csv"], data_root))
    b.append("<h2>" + t("자료와 이용 허락", "Sources and licenses") + "</h2><p class='src'>" + t(
        "1~6절: <a href='https://imslp.org/'>IMSLP</a> 작품면(<a href='https://creativecommons.org/licenses/by-sa/4.0/'>CC BY-SA 4.0</a>)의 작곡 연도·장르 태그·편성·악장 칸을 엮은이가 파싱해 가공했다. 작품면 이름과 판 번호(revid)는 CSV 에 있다. 이 표들과 1~6절의 차트는 <b>CC BY-SA 4.0</b> 으로 공개한다(다른 표와 라이선스가 다르고, 사이트 글의 비영리 조건(CC BY-NC)은 이 차트에 적용하지 않는다). 수용은 <a href='https://github.com/nyphilarchive/PerformanceHistory'>뉴욕 필하모닉 공연 기록</a>(CC0), 생몰년은 <a href='https://www.wikidata.org/'>Wikidata</a>(CC0). 7절: 퍼블릭 도메인 원본을 엮은이가 옮겨 적은 표, CC BY 4.0. 편성 상세는 IMSLP 기여자가 적은 것이라 빠진 악기가 있을 수 있다(특히 18세기 팀파니·트럼펫·통주저음).",
        "Sections 1–6: composition year, genre tags, instrumentation and movement fields of <a href='https://imslp.org/'>IMSLP</a> work pages (<a href='https://creativecommons.org/licenses/by-sa/4.0/'>CC BY-SA 4.0</a>), parsed and transformed by the editor; page names and revision ids are in the CSVs. These tables and the charts in sections 1–6 are released under <b>CC BY-SA 4.0</b> (a different license from the other tables; the non-commercial condition on the site's text (CC BY-NC) does not apply to these charts). Reception: <a href='https://github.com/nyphilarchive/PerformanceHistory'>NY Phil Performance History</a> (CC0); dates: <a href='https://www.wikidata.org/'>Wikidata</a> (CC0). Section 7: the editor's transcription of a public-domain source, CC BY 4.0. Instrumentation details were entered by IMSLP contributors and may omit instruments (notably timpani, trumpets and continuo in the 18th century).") + "</p>")
    b.append(files([f"imslp/{f}" for f in ("imslp_works.csv", "imslp_composer_year.csv", "imslp_composer_age.csv", "imslp_reception_period.csv", "imslp_nyphil_match_rate.csv", "imslp_nyphil_matches.csv",
                                         "imslp_symphony_orchestration.csv", "imslp_movement_tempo.csv", "imslp_tempo_by_period.csv", "imslp_tempo_language.csv", "imslp_instrument_use.csv", "imslp_symphony_instruments.csv")], data_root))
    return "".join(b)


HISTORY_FILES = ["imslp_works.csv", "imslp_composer_year.csv", "imslp_composer_age.csv", "imslp_reception_period.csv", "imslp_nyphil_match_rate.csv", "imslp_nyphil_matches.csv",
                 "imslp_symphony_orchestration.csv", "imslp_movement_tempo.csv", "imslp_tempo_by_period.csv", "imslp_tempo_language.csv", "imslp_instrument_use.csv", "imslp_symphony_instruments.csv"]
ELLIS_FILES = ["ellis_pitch_table1.csv", "ellis_pitch_table2.csv"]


def build(lang: str, path: Path, page_fn) -> None:
    body = render(lang)
    path.write_text(page_fn(lang, t("작품 활동과 역사", "Works & history"), body, active="history"), encoding="utf-8")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from build_site import CSS, JS
    out = Path("proto")
    out.mkdir(exist_ok=True)
    for lang in ("ko", "en"):
        body = render(lang, data_root="../site/data/")
        page = f"""<!DOCTYPE html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>preview</title>
<script>(function(){{var q=new URLSearchParams(location.search).get("theme");if(q==="light"||q==="dark"){{localStorage.setItem("cmm-theme",q)}}var v=localStorage.getItem("cmm-theme");if(v)document.documentElement.setAttribute("data-theme",v)}})();</script>
<style>{CSS}</style></head><body><header><span class="brand">preview</span><div class="right"><button id="theme" class="theme" type="button">◑</button></div></header><main>{body}</main><script>{JS}</script></body></html>"""
        (out / f"{lang}.html").write_text(page, encoding="utf-8")
    print("wrote proto/ko.html, proto/en.html")


if __name__ == "__main__":
    main()
