"""1.9: 'Romantic piano miniatures' page (romantic.html) and a section on every score-metric page.

Reads data/derived/collections_19_by_movement.csv (collections_19.py), sonata_metrics_by_movement.csv (1.8)
and score_metrics_19_by_movement.csv (score_metrics_19.py, the four 1.9 metrics). Every number in the prose
is computed from those tables.

Keyboard line: the six dated 1.8 sonata collections and the seven Romantic collections, in order of median
composition year. String quartets: Pleyel, Beethoven (ABC) and Mendelssohn. Cadence metrics are left out of
the quartet comparison: only Pleyel carries cadence labels.
"""
from __future__ import annotations

import html
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import colour_19 as col19  # noqa: E402
import sonata_pages as son  # noqa: E402
from registry import METRICS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/derived"
FILES = ["collections_19_by_movement.csv", "score_metrics_19_by_movement.csv", "keymaps_19.csv"]
MET = {m["id"]: m for m in METRICS}

NAME = dict(son.NAME, **{
    "Chopin": ("쇼팽", "Chopin"), "Schumann": ("슈만", "Schumann"), "Liszt": ("리스트", "Liszt"),
    "Grieg": ("그리그", "Grieg"), "Tchaikovsky": ("차이콥스키", "Tchaikovsky"), "Dvořák": ("드보르자크", "Dvořák"),
    "Medtner": ("메트너", "Medtner"), "Pleyel": ("플레옐", "Pleyel"), "Mendelssohn": ("멘델스존", "Mendelssohn"),
})
FULL = {
    "Chopin": ("프레데리크 쇼팽(1810–1849)", "Fryderyk Chopin (1810–1849)"),
    "Schumann": ("로베르트 슈만(1810–1856)", "Robert Schumann (1810–1856)"),
    "Liszt": ("프란츠 리스트(1811–1886)", "Franz Liszt (1811–1886)"),
    "Grieg": ("에드바르 그리그(1843–1907)", "Edvard Grieg (1843–1907)"),
    "Tchaikovsky": ("표트르 차이콥스키(1840–1893)", "Pyotr Tchaikovsky (1840–1893)"),
    "Dvořák": ("안토닌 드보르자크(1841–1904)", "Antonín Dvořák (1841–1904)"),
    "Medtner": ("니콜라이 메트너(1880–1951)", "Nikolai Medtner (1880–1951)"),
    "Pleyel": ("이그나츠 플레옐(1757–1831)", "Ignaz Pleyel (1757–1831)"),
    "Mendelssohn": ("펠릭스 멘델스존(1809–1847)", "Felix Mendelssohn (1809–1847)"),
    "Beethoven": son.FULL["Beethoven"],
}
WORK = {  # collection titles
    "chopin_mazurkas": ("마주르카", "Mazurkas"), "schumann_kinderszenen": ("어린이 정경", "Kinderszenen"),
    "liszt_pelerinage": ("순례의 해", "Années de pèlerinage"), "grieg_lyric_pieces": ("서정 소품", "Lyric Pieces"),
    "tchaikovsky_seasons": ("사계", "The Seasons"), "dvorak_silhouettes": ("실루엣", "Silhouettes"),
    "medtner_tales": ("옛이야기", "Tales"), "pleyel_quartets": ("현악 4중주", "String quartets"),
    "mendelssohn_quartets": ("현악 4중주", "String quartets"), "ABC": ("현악 4중주", "String quartets"),
}
ROMANTIC_COLOR, CLASSICAL_COLOR = 0, son.NEW_COLOR  # --s1 is free on this page (no Bach)
NEW19 = ["key_clarity", "fifth_root_motion_ratio", "key_change_distance_median", "outside_5oct_ratio"]
LEAD = son.LEAD + NEW19
CAD = ["cadences_per_100_measures", "pac_ratio_of_cadences"]
SMALL_N = son.SMALL_N


def esc(s):
    return html.escape("" if s is None else str(s))


def nm(c, lang):
    return NAME[c][0 if lang == "ko" else 1]


def _year(df):
    ys = pd.to_numeric(df["composed_start"], errors="coerce")
    ye = pd.to_numeric(df["composed_end"], errors="coerce")
    return (ys + ye.fillna(ys)) / 2


@lru_cache(maxsize=1)
def _frames():
    s19 = pd.read_csv(D / "score_metrics_19_by_movement.csv")
    c19 = pd.read_csv(D / "collections_19_by_movement.csv", low_memory=False).merge(s19, on=["corpus", "piece_id"], how="left")
    p110 = D / "score_metrics_110_by_movement.csv"  # 1.10 metrics
    if p110.exists():
        c19 = c19.merge(pd.read_csv(p110), on=["corpus", "piece_id"], how="left")
    c19["year_mid"] = _year(c19)
    sonatas = son.load()
    sonatas = sonatas[sonatas["in_cohort"]].copy()
    sonatas["era"] = "classical"
    piano = c19[c19["group"] == "piano"].copy()
    piano["era"] = "romantic"
    kb = pd.concat([sonatas, piano], ignore_index=True)
    qt = c19[c19["group"] == "quartet"].copy()
    return kb, qt


def frames():
    kb, qt = _frames()
    return kb.copy(), qt.copy()


def order(df: pd.DataFrame) -> list[str]:
    yr = df.groupby("composer")["year_mid"].median()
    return sorted([k for k in yr.index if pd.notna(yr[k])], key=lambda k: yr[k])


def color(comp: str, era: str) -> int:
    if comp in son.COLOR:
        return son.COLOR[comp]
    return ROMANTIC_COLOR if era == "romantic" else CLASSICAL_COLOR


def strip_groups(df: pd.DataFrame, mid: str, lang: str):
    out = []
    for comp in order(df):
        g = df[df["composer"] == comp]
        vs = g[mid].astype(float)
        if vs.notna().any():
            out.append((nm(comp, lang), vs.tolist(), color(comp, g["era"].iloc[0] if "era" in g else "")))
    return out


def summary(df: pd.DataFrame, mids: list[str]) -> pd.DataFrame:
    rows = []
    for comp in order(df):
        g = df[df["composer"] == comp]
        r = dict(composer=comp, corpus=g["corpus"].iloc[0], movements=len(g), bars=int(g["n_measures"].sum()),
                 labelled=int(g["has_harmony"].sum()),
                 y0=pd.to_numeric(g["composed_start"], errors="coerce").min(), y1=pd.to_numeric(g["composed_end"], errors="coerce").max(),
                 year=g["year_mid"].median(), era=g["era"].iloc[0] if "era" in g else "",
                 annot=", ".join(sorted({a.split(" (")[0].strip() for x in g["annotators"].dropna().astype(str) for a in x.split(",") if a.strip() and not a.strip().startswith("unknown")})),
                 std=", ".join(sorted(v for v in g["harmony_version"].dropna().astype(str).unique() if v)))
        for mid in mids:
            r[mid] = g[mid].median() if mid in g else float("nan")
        rows.append(r)
    return pd.DataFrame(rows)


def score_mids() -> list[str]:
    return [m["id"] for m in METRICS if m["table"] == "score"]


def _stat_table(df, m, lang, table_html, stat_spec, tid, keep=None):
    k = lang == "ko"
    summ = []
    for comp in order(df):
        v = df.loc[df["composer"] == comp, m["id"]].astype(float).dropna()
        if len(v):
            summ.append(dict(group=nm(comp, lang), n=len(v), median=v.median(), q1=v.quantile(.25), q3=v.quantile(.75), mn=v.min(), mx=v.max()))
    if not summ:
        return ""
    st = lambda v, f=m["fmt"]: stat_spec(v, f)  # noqa: E731
    return table_html(pd.DataFrame(summ), [("group", "작곡가" if k else "Composer", None), ("n", "악장" if k else "movements", "d"), ("median", "중앙값" if k else "median", st),
                                           ("q1", "Q1", st), ("q3", "Q3", st), ("mn", "최소" if k else "min", m["fmt"]), ("mx", "최대" if k else "max", m["fmt"])], tid, lang, filt=False)


def kb_legend(legend, lang):
    k = lang == "ko"
    return legend([("베토벤" if k else "Beethoven", 1), ("모차르트" if k else "Mozart", 2),
                   ("고전기 건반 소나타" if k else "Classical-era sonatas", CLASSICAL_COLOR), ("낭만기 피아노 소품" if k else "Romantic piano pieces", ROMANTIC_COLOR)])


# ------------------------------------------------------------------ section on each score-metric page
def metric_section(m: dict, lang: str, svg_strip, legend, table_html, stat_spec) -> str:
    kb, qt = frames()
    k = lang == "ko"
    mid = m["id"]
    out = []
    if mid in kb and kb[mid].notna().any():
        g = strip_groups(kb, mid, lang)
        out.append(f"<h2>{'건반 음악 1740~1925' if k else 'Keyboard music, 1740–1925'}</h2><p>"
                   + ("1.8의 고전기 건반 소나타 곡집에 낭만기 피아노 소품 곡집 일곱을 이어 붙였다. 위에서 아래로 작곡 연도 중앙값 순이다(J. C. 바흐는 연도 미확인이라 뺐다). 소나타 악장과 성격 소품은 장르가 달라 길이와 짜임이 다르다. 자세한 설명은 <a href='../romantic.html'>낭만기 피아노 소품</a> 면에 있다."
                      if k else "The Classical-era keyboard sonatas of 1.8 continued with seven collections of Romantic piano pieces, top to bottom by median year of composition (J. C. Bach, whose years are unconfirmed, is left out). Sonata movements and character pieces differ in length and texture. See the <a href='../romantic.html'>Romantic piano miniatures</a> page.")
                   + "</p>" + kb_legend(legend, lang)
                   + f"<figure>{svg_strip(g, m['fmt'], xlabel=m['unit'], med_label='중앙값' if k else 'median', row_h=26)}<figcaption>{'점 하나가 악장(곡) 하나, 세로 막대는 중앙값.' if k else 'One dot per movement or piece; vertical bar = median.'}</figcaption></figure>"
                   + _stat_table(kb[kb["era"] == "romantic"], m, lang, table_html, stat_spec, f"rom_{mid}"))
    if mid not in CAD and mid in qt and qt[mid].notna().any():
        g = [(nm(c, lang), qt.loc[qt.composer == c, mid].astype(float).tolist(), 1 if c == "Beethoven" else CLASSICAL_COLOR) for c in order(qt) if qt.loc[qt.composer == c, mid].notna().any()]
        out.append(f"<h2>{'현악 4중주' if k else 'String quartets'}</h2><p>"
                   + ("플레옐(1784)·베토벤(1798~1826)·멘델스존(1827~1847)의 현악 4중주 악장. 세 곡집은 화성 주석 표준의 판이 모두 달라(2.3.0·1.0.0·2.1.0), 화음 지표 차이에는 주석 규칙의 차이가 섞여 있다."
                      if k else "String-quartet movements by Pleyel (1784), Beethoven (1798–1826) and Mendelssohn (1827–1847). The three collections use three versions of the harmony annotation standard (2.3.0, 1.0.0, 2.1.0), so differences in chord metrics mix in differences in the annotation rules.")
                   + f"</p><figure>{svg_strip(g, m['fmt'], xlabel=m['unit'], med_label='중앙값' if k else 'median', row_h=26)}</figure>"
                   + _stat_table(qt, m, lang, table_html, stat_spec, f"qt_{mid}"))
    return "".join(out)


# ------------------------------------------------------------------ the page
T = {
    "ko": dict(title="낭만기 피아노 소품", lead="쇼팽에서 메트너까지 낭만기 피아노 소품 곡집 일곱 개를 고전기 건반 소나타 뒤에 이어 놓고, 현악 4중주 셋을 나란히 본다."),
    "en": dict(title="Romantic piano miniatures", lead="Seven collections of Romantic piano pieces, from Chopin to Medtner, set after the Classical-era keyboard sonatas, and three string-quartet collections side by side."),
}


def render(lang, svg_strip, legend, table_html, stat_spec):
    k = lang == "ko"
    kb, qt = frames()
    rom = kb[kb["era"] == "romantic"]
    mids = score_mids()
    sr, sk, sq = summary(rom, mids), summary(kb, mids), summary(qt, mids)
    n_score = len(mids)
    b = [col19.css() + f"<h1>{esc(T[lang]['title'])}</h1><p class='lead'>{esc(T[lang]['lead'])}</p>"]

    # 1. collections
    def coll_table(sm):
        rows = []
        for r in sm.itertuples():
            yrs = f"{int(r.y0)}–{int(r.y1)}" if pd.notna(r.y0) else ""
            rows.append(f"<tr><td>{esc(FULL[r.composer][0 if k else 1])}</td><td>{esc(WORK[r.corpus][0 if k else 1])}</td><td class='num'>{yrs}</td><td class='num'>{r.movements}</td><td class='num'>{r.bars:,}</td><td class='num'>{r.labelled}</td><td>{esc(r.annot)}</td><td>{esc(r.std) or '—'}</td></tr>")
        th = ["작곡가", "곡집", "작곡 연도", "곡·악장", "마디", "화성 주석", "주석자", "주석 표준 판"] if k else ["Composer", "Collection", "Composed", "Pieces", "Bars", "With harmony labels", "Annotators", "Standard version"]
        return f"<div class='wrap'><table><thead><tr>{''.join(f'<th>{h}</th>' for h in th)}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"

    n_rom, bars_rom = len(rom), int(rom["n_measures"].sum())
    b.append(("<h2>1. 곡집</h2><p>" + f"DCML이 같은 화성 주석 체계(DCML 표준, 곡집마다 판은 2.1~2.3)로 분석해 공개한 낭만기 피아노 곡집 일곱 개, {n_rom}곡 {bars_rom:,}마디다. 마주르카·서정 소품·어린이 정경처럼 짧은 성격 소품이 대부분이고, 리스트 「순례의 해」는 그보다 긴 곡이 많다. 이 면의 그림에서는 1.8의 고전기 건반 소나타 곡집 여섯(J. C. 바흐 제외) 뒤에 이어 놓는다."
              if k else "<h2>1. The collections</h2><p>" + f"Seven collections of Romantic piano music that DCML analysed under one harmony annotation standard and published: {n_rom} pieces, {bars_rom:,} bars. Most are short character pieces (mazurkas, lyric pieces, Kinderszenen); Liszt's Années de pèlerinage has many longer ones. The charts on this page set them after the six dated Classical-era sonata collections of 1.8 (J. C. Bach left out).")
             + "</p>" + coll_table(sr)
             + "<p class='src'>" + ("마디 수는 곡마다 악보의 마지막 마디 번호를 더한 값이다. 주석 표준 판이 둘 이상 적힌 곡집은 곡마다 판이 다르다." if k else "Bars are the sum of each piece's last bar number. Collections with more than one standard version have different versions for different pieces.") + "</p>")

    # 2. keyboard music strips
    b.append(("<h2>2. 건반 음악 1740~1925</h2><p>위에서 아래로 작곡 연도 중앙값 순이다. 점 하나가 악장(곡) 하나, 세로 막대는 중앙값. 지표 이름을 누르면 정의와 공식이 있는 지표 면으로 간다. 마지막 넷은 1.9에서 새로 더한 지표다.</p>"
              if k else "<h2>2. Keyboard music, 1740–1925</h2><p>Top to bottom by median year of composition. One dot per movement or piece; vertical bar = median. Click a metric's name for its definition and formula. The last four are new in 1.9.</p>")
             + kb_legend(legend, lang))
    for mid in LEAD:
        m = MET[mid]
        b.append(f"<h3 style='margin:1rem 0 .1rem'><a href='metrics/{mid}.html'>{esc(m[lang]['name'])}</a></h3><p class='src' style='margin:.1rem 0'>{esc(m[lang]['definition'])}</p>"
                 f"<figure>{svg_strip(strip_groups(kb, mid, lang), m['fmt'], xlabel=m['unit'], med_label='중앙값' if k else 'median', row_h=24)}</figure>")

    # 3. what the data show
    cl, ro = sk[sk.era == "classical"], sk[sk.era == "romantic"]
    items = []
    for mid in ["chromatic_ratio", "pitch_class_entropy", "key_clarity", "seventh_chord_ratio", "fifth_root_motion_ratio", "local_key_changes_per_100_measures", "key_change_distance_median", "outside_5oct_ratio"]:
        f = MET[mid]["fmt"]
        a, z = cl[mid].median(), ro[mid].median()
        def ext(fn):  # collections exactly tied at the extreme (not merely equal after rounding; Codex 61)
            best = fn(ro[mid])
            names = [nm(c, lang) for c, x in zip(ro.composer, ro[mid]) if x == best]
            return ("·" if k else ", ").join(names), format(best, f)
        hn, hv = ext(max)
        ln, lv = ext(min)
        items.append(f"<li><b><a href='metrics/{mid}.html'>{esc(MET[mid][lang]['name'])}</a></b>: "
                     + (f"곡집 중앙값의 중앙값이 고전기 곡집 {format(a, f)}, 낭만기 곡집 {format(z, f)}. 낭만기 안에서 가장 큰 곡집은 {hn}({hv}), 가장 작은 곡집은 {ln}({lv})."
                        if k else f"median of the collection medians: Classical-era {format(a, f)}, Romantic {format(z, f)}. Among the Romantic collections, highest {hn} ({hv}), lowest {ln} ({lv}).") + "</li>")
    hm = ["chromatic_ratio", "pitch_class_entropy", "key_clarity", "seventh_chord_ratio", "fifth_root_motion_ratio", "local_key_changes_per_100_measures", "key_change_distance_median", "outside_5oct_ratio"]
    heat = ("<figure>" + col19.heatmap(sk, hm, [MET[x][lang]["name"] for x in hm], [nm(c, lang) for c in sk.composer], [MET[x]["fmt"] for x in hm], lang)
            + col19.heat_legend(lang, len(sk)) + "<figcaption>" + ("파랑은 곡집 13개의 평균보다 낮고 주황은 높다. z는 곡집 중앙값 13개의 평균과 모표준편차(ddof=0)로 내고, 0.5 표준편차를 한 칸으로 반올림하며 ±3 표준편차에서 가장 진한 칸이다. 색은 지표마다 따로 맞춘 상대값이라 열끼리 색을 견주지 않는다. 칸에 마우스를 올리면 z 값이 나온다." if k else "Blue is below the mean of the 13 collections, orange above. z uses the mean and population standard deviation (ddof=0) of the 13 collection medians, rounded to steps of half a standard deviation and saturating at ±3. Colour is scaled separately for each metric, so do not compare colours across columns. Hover for the z value.") + "</figcaption></figure>")
    small = [nm(r.composer, lang) for r in sr.itertuples() if r.movements < SMALL_N]
    mixed = [nm(r.composer, lang) for r in sr.itertuples() if "," in r.std]
    nohar = [nm(r.composer, lang) for r in sr.itertuples() if r.labelled < r.movements]
    if k:
        b.append("<h2>3. 데이터가 보여 주는 것, 주의할 점</h2><p>곡집마다 중앙값을 내고, 고전기 곡집 여섯과 낭만기 곡집 일곱의 중앙값을 각각 다시 중앙값으로 묶었다(곡집 하나가 한 표; C. P. E. 바흐는 소나타 50악장만). 아래 열지도는 같은 중앙값을 곡집 13개의 평균과 견준 것이다(칸 안 숫자가 중앙값).</p>" + heat + "<ul>" + "".join(items) + "</ul>"
                 "<p><b>주의할 점.</b></p><ul>"
                 "<li>고전기 쪽은 소나타 악장, 낭만기 쪽은 대부분 짧은 성격 소품이다. 차이에는 시대의 차이와 장르의 차이가 섞여 있다. 곡 길이에 따라 달라질 수 있는 지표(전조 빈도·화음 어휘 등)는 특히 그렇다.</li>"
                 "<li>화음 지표는 사람이 붙인 화성 기호를 센 것이라 주석자의 판단도 함께 잰다. "
                 + (f"{', '.join(mixed)} 곡집은 곡마다 주석 표준 판이 다르다. " if mixed else "")
                 + (f"{', '.join(nohar)} 곡집에는 화성 주석이 없는 곡이 있어 화음 지표에서 빠진다. " if nohar else "")
                 + "조성 명료도와 5옥타브 밖 음 비율은 음표에서 바로 세므로 화성 주석자의 판단에 직접 의존하지 않는다(악보 판본과 입력 방식의 영향은 남는다).</li>"
                 + (f"<li>{', '.join(small)} 곡집은 곡이 10개가 안 되어 중앙값이 흔들리기 쉽다.</li>" if small else "")
                 + "<li>5옥타브 밖 음 비율의 기준(F1~F6)은 비교를 위해 고정한 음역이다. 시대마다, 악기마다 실제 건반 음역은 달랐다.</li>"
                 "<li>곡집은 연구자들이 주석한 것을 모은 것이지 시대를 대표하도록 뽑은 표본이 아니다. 쇼팽의 다른 장르, 브람스·멘델스존의 피아노 곡, 슈베르트 소나타 같은 큰 줄기가 빠져 있다.</li></ul>")
    else:
        b.append("<h2>3. What the data show, and what to watch for</h2><p>A median for each collection; then the median of those medians for the six Classical-era and the seven Romantic collections (one vote per collection; C. P. E. Bach: the 50 sonata movements only). The heatmap below sets the same medians against the mean of the 13 collections (the number in each cell is the median).</p>" + heat + "<ul>" + "".join(items) + "</ul>"
                 "<p><b>What to watch for.</b></p><ul>"
                 "<li>The Classical-era side is sonata movements, the Romantic side mostly short character pieces. Differences mix period with genre, especially for metrics that can vary with length (modulation rate, chord vocabulary).</li>"
                 "<li>Chord metrics count harmony labels that people added, so they measure the annotators' judgment as well. "
                 + (f"The {', '.join(mixed)} collections use different versions of the standard for different pieces. " if mixed else "")
                 + (f"The {', '.join(nohar)} collection has pieces without harmony labels; they drop out of the chord metrics. " if nohar else "")
                 + "Key clarity and the share of notes outside five octaves are counted from the notes and do not depend directly on the harmony annotators (score edition and encoding still matter).</li>"
                 + (f"<li>{', '.join(small)} has fewer than 10 pieces, so its medians move easily.</li>" if small else "")
                 + "<li>The five-octave reference (F1–F6) is fixed for comparison; real keyboard compasses differed by period and instrument.</li>"
                 "<li>The collections are the ones researchers annotated, not a sample drawn to represent the period. Large parts of the repertoire are missing: Chopin's other genres, the piano music of Brahms and Mendelssohn, Schubert's sonatas.</li></ul>")

    # 4. key maps
    comp_of = dict(zip(kb.corpus, kb.composer)) | dict(zip(qt.corpus, qt.composer))
    b.append(("<h2>4. 조성 지도</h2>" if k else "<h2>4. Key maps</h2>")
             + col19.keymap_section(lang, lambda c: nm(comp_of[c], lang) + (f" · {WORK[c][0 if k else 1]}" if c in WORK else "")))

    # 5. string quartets
    qmids = [x for x in LEAD if x != "outside_5oct_ratio"]
    b.append(("<h2>5. 현악 4중주</h2><p>플레옐(1784)·베토벤(1798~1826)·멘델스존(1827~1847)의 현악 4중주 악장이다. 베토벤 곡집은 이 사이트의 다른 면에 쓰는 것 그대로다(수치 동일).</p>"
              if k else "<h2>5. String quartets</h2><p>String-quartet movements by Pleyel (1784), Beethoven (1798–1826) and Mendelssohn (1827–1847). The Beethoven collection is the one used elsewhere on this site (same values).</p>")
             + coll_table(sq) + legend([("베토벤" if k else "Beethoven", 1), ("플레옐·멘델스존" if k else "Pleyel, Mendelssohn", CLASSICAL_COLOR)]))
    for mid in qmids:
        m = MET[mid]
        g = [(nm(c, lang), qt.loc[qt.composer == c, mid].astype(float).tolist(), 1 if c == "Beethoven" else CLASSICAL_COLOR) for c in order(qt) if qt.loc[qt.composer == c, mid].notna().any()]
        b.append(f"<h3 style='margin:1rem 0 .1rem'><a href='metrics/{mid}.html'>{esc(m[lang]['name'])}</a></h3><figure>{svg_strip(g, m['fmt'], xlabel=m['unit'], med_label='중앙값' if k else 'median', row_h=26)}</figure>")
    qsmall = [nm(r.composer, lang) for r in sq.itertuples() if r.movements < SMALL_N]
    b.append("<ul>" + ("<li>세 곡집의 화성 주석 표준 판이 모두 다르다(" + ", ".join(f"{nm(r.composer, lang)} {r.std}" for r in sq.itertuples()) + "). 화음 지표 차이에는 주석 규칙의 차이가 섞여 있을 수 있고, 그 크기는 이 자료로 따로 잴 수 없다.</li>"
                       "<li>종지 표지는 플레옐 곡집에만 있어 종지 지표 둘은 이 비교에 싣지 않는다.</li>"
                       + (f"<li>{', '.join(qsmall)} 곡집은 악장이 10개가 안 된다.</li>" if qsmall else "")
                       if k else
                       "<li>The three collections use different versions of the harmony annotation standard (" + ", ".join(f"{nm(r.composer, lang)} {r.std}" for r in sq.itertuples()) + "). Differences in chord metrics may mix in differences in the annotation rules, by an amount these data cannot separate.</li>"
                       "<li>Only the Pleyel collection carries cadence labels, so the two cadence metrics are left out of this comparison.</li>"
                       + (f"<li>{', '.join(qsmall)} has fewer than 10 movements.</li>" if qsmall else "")) + "</ul>")

    # 5. all medians
    cols = [("name", "작곡가" if k else "Composer", None), ("movements", "곡·악장" if k else "pieces", "d")] + [(mid, MET[mid][lang]["name"], MET[mid]["fmt"]) for mid in mids]
    tb = pd.concat([sk[sk.composer == "Beethoven"].assign(name=nm("Beethoven", lang) + (" (피아노 소나타)" if k else " (piano sonatas)")),
                    sr.assign(name=[nm(c, lang) for c in sr.composer]),
                    sq.assign(name=[nm(c, lang) + (" (4중주)" if k else " (quartets)") for c in sq.composer])], ignore_index=True)
    for c in CAD:
        tb.loc[tb.name.str.contains("4중주|quartets"), c] = float("nan")
    b.append((f"<h2>6. 지표 {n_score}개의 중앙값</h2>" if k else f"<h2>6. Medians of all {n_score} metrics</h2>")
             + "<p class='src'>" + ("화음 지표는 화성 주석이 있는 곡만 센다. 빈칸은 값 없음(4중주의 종지 지표는 위 이유로 비움)." if k else "Chord metrics count pieces with harmony labels only. Blank = no value (cadence metrics left blank for the quartets, as above).") + "</p>"
             + table_html(tb, cols, "rom_all", lang, filt=False))
    kk = ("Krumhansl, C. L. & Kessler, E. J. (1982), 'Tracing the dynamic changes in perceived tonal organization in a spatial representation of musical keys', "
          "<i>Psychological Review</i> 89(4): 334–368, <a href='https://doi.org/10.1037/0033-295X.89.4.334'>doi:10.1037/0033-295X.89.4.334</a>")
    b.append("<p class='src'>" + ("자료·출처: " if k else "Data and sources: ")
             + "Hentschel, J., Rammos, Y., Neuwirth, M. & Rohrmeier, M. (2025), 'A corpus and a modular infrastructure for the empirical study of (an)notated music', <i>Scientific Data</i> 12:685; "
             + "DCMLab corpora " + ", ".join(f"<a href='https://github.com/DCMLab/{c}'>{c}</a>" for c in ["chopin_mazurkas", "schumann_kinderszenen", "liszt_pelerinage", "grieg_lyric_pieces", "tchaikovsky_seasons", "dvorak_silhouettes", "medtner_tales", "pleyel_quartets", "mendelssohn_quartets", "ABC"]) + " (CC BY-NC-SA 4.0); "
             + kk + (" — 조성 명료도의 조성 프로필; " if k else " — tonal profiles for key clarity; ")
             + "Machado, G. M., Oliveira, M. M. & Fernandes, L. A. F. (2009), 'A physiologically-based model for simulation of color vision deficiency', <i>IEEE Transactions on Visualization and Computer Graphics</i> 15(6): 1291–1298" + (" — 조성 지도 색의 색각 이상 모의; " if k else " — colour-vision-deficiency simulation for the key-map colours; ")
             + "Viaccoz, C., Harasim, D., Moss, F. C. & Rohrmeier, M. (2022), 'Wavescapes', <i>Musicae Scientiae</i> 27(2): 390–427; Palmer, S. E., Schloss, K. B., Xu, Z. & Prado-León, L. R. (2013), 'Music–color associations are mediated by emotion', <i>PNAS</i> 110(22): 8836–8841."
             + (" 지표 정의는 <a href='metrics/index.html'>지표</a> 면과 같다. 표의 데이터는 <a href='../data/romantic/collections_19_by_movement.csv'>CSV</a>와 <a href='../data/romantic/score_metrics_19_by_movement.csv'>새 지표 CSV</a>로 내려받을 수 있다."
                if k else " Metric definitions are those of the <a href='metrics/index.html'>Metrics</a> pages. The data are downloadable as a <a href='../data/romantic/collections_19_by_movement.csv'>CSV</a> and a <a href='../data/romantic/score_metrics_19_by_movement.csv'>CSV of the new metrics</a>.")
             + "</p>")
    b.append(col19.JS)
    return "".join(b)


def build(lang, path, page_fn, svg_strip, legend, table_html, stat_spec):
    path.write_text(page_fn(lang, T[lang]["title"], render(lang, svg_strip, legend, table_html, stat_spec), desc=T[lang]["lead"], active="romantic"), encoding="utf-8")

