"""Classical-era keyboard sonatas (1.8): sonatas.html in each language, and a section on every score-metric page.

Reads data/derived/sonata_metrics_by_movement.csv (sonata_metrics.py). Every number in the prose is computed
from that table. J. C. Bach's composition years are not in the source metadata, so he stays out of anything
ordered by date and appears in the tables only (owner decision, 2026-11-09).
"""
from __future__ import annotations

import html
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from registry import METRICS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/derived"
SONATA_FILES = ["sonata_metrics_by_movement.csv"]
MET = {m["id"]: m for m in METRICS}

NAME = {
    "D. Scarlatti": ("D. 스카를라티", "D. Scarlatti"),
    "W. F. Bach": ("W. F. 바흐", "W. F. Bach"),
    "C. P. E. Bach": ("C. P. E. 바흐", "C. P. E. Bach"),
    "J. C. Bach": ("J. C. 바흐", "J. C. Bach"),
    "Mozart": ("모차르트", "Mozart"),
    "Koželuh": ("코젤루흐", "Koželuh"),
    "Beethoven": ("베토벤", "Beethoven"),
}
FULL = {
    "D. Scarlatti": ("도메니코 스카를라티(1685–1757)", "Domenico Scarlatti (1685–1757)"),
    "W. F. Bach": ("빌헬름 프리데만 바흐(1710–1784)", "Wilhelm Friedemann Bach (1710–1784)"),
    "C. P. E. Bach": ("카를 필리프 에마누엘 바흐(1714–1788)", "Carl Philipp Emanuel Bach (1714–1788)"),
    "J. C. Bach": ("요한 크리스티안 바흐(1735–1782)", "Johann Christian Bach (1735–1782)"),
    "Mozart": ("볼프강 아마데우스 모차르트(1756–1791)", "Wolfgang Amadeus Mozart (1756–1791)"),
    "Koželuh": ("레오폴트 코젤루흐(1747–1818)", "Leopold Koželuh (1747–1818)"),
    "Beethoven": ("루트비히 판 베토벤(1770–1827)", "Ludwig van Beethoven (1770–1827)"),
}
# colour index in build_site's --s palette: Beethoven and Mozart keep theirs, the five new composers share grey
COLOR = {"Beethoven": 1, "Mozart": 2}
NEW_COLOR = 3
UNDATED = {"J. C. Bach"}
LEAD = ["pitch_range_semitones", "chromatic_ratio", "notes_per_quarter", "pitch_class_entropy",
        "seventh_chord_ratio", "applied_chord_ratio", "local_key_changes_per_100_measures", "chord_vocabulary_per_100_labels"]
SMALL_N = 10


def esc(s):
    return html.escape("" if s is None else str(s))


def nm(c, lang):
    return NAME[c][0 if lang == "ko" else 1]


@lru_cache(maxsize=1)
def _load() -> pd.DataFrame:
    s = pd.read_csv(D / "sonata_metrics_by_movement.csv", low_memory=False)
    p19 = D / "score_metrics_19_by_movement.csv"  # 1.9 metrics
    if p19.exists():
        s = s.merge(pd.read_csv(p19), on=["corpus", "piece_id"], how="left")
    ys = pd.to_numeric(s["composed_start"], errors="coerce")
    ye = pd.to_numeric(s["composed_end"], errors="coerce")
    s["year_mid"] = (ys + ye.fillna(ys)) / 2
    s.loc[s["composer"].isin(UNDATED), "year_mid"] = float("nan")
    return s


def load() -> pd.DataFrame:
    return _load().copy()


def composer_order(s: pd.DataFrame) -> list[str]:
    c = s[s["in_cohort"]]
    yr = c.groupby("composer")["year_mid"].median()
    dated = sorted([k for k in yr.index if pd.notna(yr[k])], key=lambda k: yr[k])
    return dated + [k for k in c["composer"].unique() if k not in dated]


def score_mids() -> list[str]:
    return [m["id"] for m in METRICS if m["table"] == "score"]


def summary(s: pd.DataFrame) -> pd.DataFrame:
    c = s[s["in_cohort"]]
    rows = []
    for comp in composer_order(s):
        g = c[c["composer"] == comp]
        r = dict(composer=comp, movements=len(g), bars=int(g["n_measures"].sum()),
                 labelled=int(g["has_harmony"].sum()),
                 y0=pd.to_numeric(g["composed_start"], errors="coerce").min(),
                 y1=pd.to_numeric(g["composed_end"], errors="coerce").max(),
                 year=g["year_mid"].median(),
                 annot=", ".join(sorted({a.split(" (")[0].strip() for x in g["annotators"].dropna().astype(str) for a in x.split(",") if a.strip() and not a.strip().startswith("unknown")})),
                 std=", ".join(sorted(g["harmony_version"].dropna().astype(str).unique())))
        for mid in score_mids():
            r[mid] = g[mid].median()
        rows.append(r)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ section on each score-metric page
def metric_section(m: dict, lang: str, svg_strip, legend, table_html, stat_spec) -> str:
    s = load()
    k = lang == "ko"
    c = s[s["in_cohort"]]
    groups, summ, missing = [], [], []
    for comp in composer_order(s):
        vs = c.loc[c["composer"] == comp, m["id"]].astype(float)
        name = nm(comp, lang)
        if vs.notna().sum() == 0:
            missing.append(name)
            continue
        if comp not in UNDATED:
            groups.append((name, vs.tolist(), COLOR.get(comp, NEW_COLOR)))
        v = vs.dropna()
        summ.append(dict(group=name + (" (연도 미확인)" if k and comp in UNDATED else " (year unconfirmed)" if comp in UNDATED else ""),
                         n=len(v), median=v.median(), q1=v.quantile(.25), q3=v.quantile(.75), mn=v.min(), mx=v.max()))
    if not summ:
        return ""
    head = "고전기 건반 소나타" if k else "Classical-era keyboard sonatas"
    intro = ("모차르트·베토벤 소나타를 같은 시대의 건반 소나타 곡집 다섯과 나란히 놓았다. 위에서 아래로 작곡 연도 중앙값 순이다. "
             "J. C. 바흐 곡집은 원자료에 출판 연도(1765·1780)만 있고 작곡 연도가 없어 그림에서 빼고 표에만 두었다. 자세한 설명은 <a href='../sonatas.html'>고전기 건반 소나타</a> 면에 있다."
             if k else
             "Mozart's and Beethoven's sonatas beside five keyboard-sonata collections of their time, top to bottom by median year of composition. "
             "For J. C. Bach's collection the source data give only publication years (1765, 1780), not years of composition, so it is left out of the chart and shown in the table only. "
             "See the <a href='../sonatas.html'>Classical-era keyboard sonatas</a> page.")
    cap = []
    if missing:
        cap.append(("값 없음: " if k else "No value: ") + ", ".join(missing) + (" (종지 표지가 주석되지 않은 곡집)" if k and m["id"] in ("cadences_per_100_measures", "pac_ratio_of_cadences") else " (no cadence labels in this collection)" if m["id"] in ("cadences_per_100_measures", "pac_ratio_of_cadences") else ""))
    small = [x["group"] for x in summ if x["n"] < SMALL_N]
    if small:
        cap.append(("악장 10개 미만: " if k else "Fewer than 10 movements: ") + ", ".join(small))
    if m["group"] == "harmony":
        cap.append("화음 지표는 곡집마다 다른 주석자가 붙인 화성 기호를 센 것이라 주석자의 판단도 함께 잰다." if k
                   else "Chord metrics count harmony labels added by different annotators in each collection, so they measure the annotators' judgment as well.")
    leg = legend([("베토벤" if k else "Beethoven", 1), ("모차르트" if k else "Mozart", 2), ("새로 더한 곡집" if k else "Added collections", NEW_COLOR)])
    st = lambda v, f=m["fmt"]: stat_spec(v, f)  # noqa: E731
    t_coll, t_n, t_med = ("작곡가" if k else "Composer"), ("악장" if k else "movements"), ("중앙값" if k else "median")
    tbl = table_html(pd.DataFrame(summ), [("group", t_coll, None), ("n", t_n, "d"), ("median", t_med, st), ("q1", "Q1", st), ("q3", "Q3", st),
                                          ("mn", "최소" if k else "min", m["fmt"]), ("mx", "최대" if k else "max", m["fmt"])], f"son_{m['id']}", lang, filt=False)
    return (f"<h2>{head}</h2><p>{intro}</p>{leg}<figure>{svg_strip(groups, m['fmt'], xlabel=m['unit'], med_label=t_med)}"
            f"<figcaption>{'점 하나가 악장 하나, 세로 막대는 중앙값.' if k else 'One dot per movement; vertical bar = median.'} {' '.join(cap)}</figcaption></figure>{tbl}")


# ------------------------------------------------------------------ the comparison page
N_SCORE = sum(m["table"] == "score" for m in METRICS)
T = {
    "ko": dict(title="고전기 건반 소나타", lead=f"스카를라티부터 베토벤까지, 같은 주석 규칙으로 분석한 건반 소나타 곡집 일곱 개를 악보 지표 {N_SCORE}개로 나란히 본다."),
    "en": dict(title="Classical-era keyboard sonatas", lead=f"From Scarlatti to Beethoven: seven keyboard-sonata collections analysed under one annotation standard, compared on the site's {N_SCORE} score metrics."),
}


def render(lang, s, svg_strip, legend, table_html, stat_spec):
    k = lang == "ko"
    sm = summary(s)
    c = s[s["in_cohort"]]
    cpe_other = s[(s["composer"] == "C. P. E. Bach") & ~s["in_cohort"]]
    n_mov, n_bars = len(c), int(c["n_measures"].sum())
    b = [f"<h1>{esc(T[lang]['title'])}</h1><p class='lead'>{esc(T[lang]['lead'])}</p>"]

    # 1. collections
    rows = []
    for r in sm.itertuples():
        yrs = ("미확인" if k else "unconfirmed") if r.composer in UNDATED else (f"{int(r.y0)}–{int(r.y1)}" if pd.notna(r.y0) else "")
        rows.append(f"<tr><td>{esc(FULL[r.composer][0 if k else 1])}</td><td class='num'>{yrs}</td><td class='num'>{r.movements}</td><td class='num'>{r.bars:,}</td><td class='num'>{r.labelled}</td><td>{esc(r.annot)}</td><td>{esc(r.std) or '—'}</td></tr>")
    th = ["작곡가", "작곡 연도", "악장", "마디", "화성 주석 악장", "주석자", "주석 표준 판"] if k else ["Composer", "Composed", "Movements", "Bars", "With harmony labels", "Annotators", "Standard version"]
    if k:
        b.append("<h2>1. 곡집</h2>"
                 f"<p>DCML(EPFL 디지털·인지 음악학 연구실)이 같은 화성 주석 규칙으로 분석해 공개한 건반 소나타 곡집 일곱 개, {n_mov}악장 {n_bars:,}마디다. 모차르트·베토벤은 이 사이트의 다른 면에 쓰는 곡집 그대로이고, 나머지 다섯이 1.8에서 더해졌다. "
                 f"C. P. E. 바흐 곡집에는 소나타 말고도 판타지아 {int((cpe_other.genre == 'fantasia').sum())}악장과 론도 {int((cpe_other.genre == 'rondo').sum())}악장이 있어(판타지아에는 「판타지아와 푸가」 1악장이 들어 있다), 비교에서는 소나타만 쓰고 나머지는 4절에 따로 두었다.</p>")
    else:
        b.append("<h2>1. The collections</h2>"
                 f"<p>Seven keyboard-sonata collections that DCML (the Digital and Cognitive Musicology Lab, EPFL) analysed under one harmony annotation standard and published: {n_mov} movements, {n_bars:,} bars. Mozart and Beethoven are the same collections used elsewhere on this site; the other five are new in 1.8. "
                 f"The C. P. E. Bach collection also holds {int((cpe_other.genre == 'fantasia').sum())} fantasia and {int((cpe_other.genre == 'rondo').sum())} rondo movements (the fantasias include one Fantasia and Fugue); the comparison uses the sonatas only, and the rest are shown separately in section 4.</p>")
    b.append(f"<div class='wrap'><table><thead><tr>{''.join(f'<th>{h}</th>' for h in th)}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")
    b.append("<p class='src'>" + ("작곡 연도는 원자료(metadata)의 작곡 시작·끝 연도다. J. C. 바흐 곡집은 시작 연도가 비어 있고 끝 연도 칸에는 출판 연도(Op. 5는 1765, Op. 17은 1780)만 있어 연도순 그림에서 뺐다. 마디 수는 악장마다 악보의 마지막 마디 번호를 더한 값이다. 주석자는 원자료에 적힌 이름이고, 스카를라티 곡집에는 이름 있는 주석자 앞에 「unknown」이 함께 적혀 있다(표에서는 뺐다)."
                                  if k else "Years are the start and end years of composition in the source metadata. For the J. C. Bach collection the start year is empty and the end-year field holds only the publication year (Op. 5, 1765; Op. 17, 1780), so it is kept out of the date-ordered charts. Bars are the sum of each movement's last bar number. Annotators are the names in the source data; the Scarlatti collection also lists 'unknown' ahead of the named annotators (left out of the table).") + "</p>")

    # 2. lead metrics
    b.append("<h2>2. 지표 여덟 개</h2>" if k else "<h2>2. Eight metrics</h2>")
    b.append("<p>" + ("위에서 아래로 작곡 연도 중앙값 순이다. 점 하나가 악장 하나, 세로 막대는 중앙값. 앞의 넷은 음표에서 바로 세고(꾸밈음과 붙임줄로 이어진 뒷음은 빼고 센다), 뒤의 넷은 화성 기호를 센다. 지표 이름을 누르면 정의와 공식이 있는 지표 면으로 간다."
                      if k else "Top to bottom by median year of composition. One dot per movement; vertical bar = median. The first four are counted from the notes (leaving out grace notes and the tied continuations of notes), the last four from the harmony labels. Click a metric's name for its definition and formula.") + "</p>")
    leg = legend([("베토벤" if k else "Beethoven", 1), ("모차르트" if k else "Mozart", 2), ("새로 더한 곡집" if k else "Added collections", NEW_COLOR)])
    b.append(leg)
    for mid in LEAD:
        m = MET[mid]
        groups = [(nm(comp, lang), c.loc[c.composer == comp, mid].astype(float).tolist(), COLOR.get(comp, NEW_COLOR))
                  for comp in composer_order(s) if comp not in UNDATED and c.loc[c.composer == comp, mid].notna().any()]
        b.append(f"<h3 style='margin:1rem 0 .1rem'><a href='metrics/{mid}.html'>{esc(m[lang]['name'])}</a></h3><p class='src' style='margin:.1rem 0'>{esc(m[lang]['definition'])}</p>"
                 f"<figure>{svg_strip(groups, m['fmt'], xlabel=m['unit'], med_label='중앙값' if k else 'median', row_h=26)}</figure>")

    # 3. what the data show / caveats
    def ext(mid):
        q = sm.dropna(subset=[mid]).sort_values(mid)
        lo, hi = q.iloc[0], q.iloc[-1]
        f = MET[mid]["fmt"]
        return nm(hi.composer, lang), format(hi[mid], f), nm(lo.composer, lang), format(lo[mid], f)
    dated = sm[~sm.composer.isin(UNDATED)].sort_values("year")
    rng_first, rng_last = dated.iloc[0], dated.iloc[-1]
    mid_lo, mid_hi = dated.iloc[1:-1]["pitch_range_semitones"].min(), dated.iloc[1:-1]["pitch_range_semitones"].max()
    items = []
    for mid in ["pitch_range_semitones", "chromatic_ratio", "seventh_chord_ratio", "local_key_changes_per_100_measures"]:
        hn, hv, ln, lv = ext(mid)
        items.append(f"<li><b><a href='metrics/{mid}.html'>{esc(MET[mid][lang]['name'])}</a></b>: " + (f"중앙값이 가장 큰 곡집은 {hn}({hv}), 가장 작은 곡집은 {ln}({lv})." if k else f"highest median {hn} ({hv}), lowest {ln} ({lv}).") + "</li>")
    small = [nm(r.composer, lang) for r in sm.itertuples() if r.movements < SMALL_N]
    nocad = [nm(r.composer, lang) for r in sm.itertuples() if pd.isna(r.cadences_per_100_measures)]
    if k:
        b.append("<h2>3. 데이터가 보여 주는 것, 주의할 점</h2><ul>" + "".join(items) +
                 f"<li>음역 중앙값은 연도가 가장 이른 {nm(rng_first.composer, lang)} 곡집이 {rng_first.pitch_range_semitones:.0f}반음, 가장 늦은 {nm(rng_last.composer, lang)} 곡집이 {rng_last.pitch_range_semitones:.0f}반음이고, 그 사이 곡집은 {mid_lo:.0f}~{mid_hi:.0f}반음이다. 건반 악기의 음역이 넓어진 것과 맞물리지만, 이 표만으로 악기 때문이라고 단정할 수는 없다.</li></ul>"
                 "<p><b>주의할 점.</b></p><ul>"
                 "<li>화음 지표는 사람이 붙인 화성 기호를 센 것이다. 곡집마다 주석자가 다르고, 코젤루흐 곡집은 주석 표준 2.1.0, 다른 곡집은 2.3.0이다(모차르트 곡집은 판 표시가 없다). 곡집 사이의 화음 지표 차이에는 작곡가의 차이와 주석자의 차이가 섞여 있다. 음표에서 바로 세는 지표(음역·반음계 비율·음표 밀도·음급 엔트로피 등)에는 주석자 문제가 없다. 다만 악보 판본과 인코딩의 차이는 남는다.</li>"
                 f"<li>{', '.join(nocad)} 곡집에는 종지 표지가 없어 종지 지표 두 개를 비워 두었다(0이 아니다).</li>"
                 f"<li>{', '.join(small)} 곡집은 악장이 10개가 안 되어 중앙값이 흔들리기 쉽다.</li>"
                 "<li>스카를라티 소나타는 대부분 단악장 이분형식의 하프시코드 곡이고(Rodda 2020), 베토벤 소나타는 피아노를 위한 여러 악장짜리 곡이다. 같은 「건반 소나타」라도 악기와 형식이 다르다.</li>"
                 "<li>곡집은 연구자들이 주석한 것을 모은 것이지 시대를 대표하도록 뽑은 표본이 아니다. 하이든·클레멘티 같은 중요한 소나타 작곡가가 빠져 있다.</li></ul>")
    else:
        b.append("<h2>3. What the data show, and what to watch for</h2><ul>" + "".join(items) +
                 f"<li>The median pitch range is {rng_first.pitch_range_semitones:.0f} semitones in the earliest collection ({nm(rng_first.composer, lang)}) and {rng_last.pitch_range_semitones:.0f} in the latest ({nm(rng_last.composer, lang)}); the collections in between have {mid_lo:.0f}–{mid_hi:.0f}. That goes with the widening compass of keyboard instruments, but this table alone cannot show the instrument was the cause.</li></ul>"
                 "<p><b>What to watch for.</b></p><ul>"
                 "<li>Chord metrics count harmony labels that people added. Each collection has different annotators, and the Koželuh collection uses version 2.1.0 of the standard where the others use 2.3.0 (the Mozart collection gives no version). Differences in chord metrics between collections mix differences between composers with differences between annotators. Metrics counted straight from the notes (pitch range, chromatic ratio, note density, pitch-class entropy and so on) do not depend on annotators, though differences in score editions and encoding remain.</li>"
                 f"<li>The {', '.join(nocad)} collection carries no cadence labels, so the two cadence metrics are left blank there (not zero).</li>"
                 f"<li>{', '.join(small)} has fewer than 10 movements, so its medians move easily.</li>"
                 "<li>Most Scarlatti sonatas are single-movement pieces in binary form for harpsichord (Rodda 2020); Beethoven's are multi-movement sonatas for the piano. 'Keyboard sonata' covers different instruments and forms.</li>"
                 "<li>The collections are the ones researchers annotated, not a sample drawn to represent the period. Important sonata composers such as Haydn and Clementi are missing.</li></ul>")

    # 4. C. P. E. Bach by genre
    rows4 = []
    for gname in ["sonata", "fantasia", "rondo"]:
        g = s[(s.composer == "C. P. E. Bach") & (s.genre == gname)]
        rows4.append(dict(genre={"sonata": ("소나타", "Sonata"), "fantasia": ("판타지아", "Fantasia"), "rondo": ("론도", "Rondo")}[gname][0 if k else 1],
                          n=len(g), **{mid: g[mid].median() for mid in LEAD}))
    b.append("<h2>4. C. P. E. 바흐 — 소나타와 다른 곡</h2>" if k else "<h2>4. C. P. E. Bach: sonatas and the other pieces</h2>")
    b.append(table_html(pd.DataFrame(rows4), [("genre", "장르" if k else "Genre", None), ("n", "악장" if k else "movements", "d")] + [(mid, MET[mid][lang]["name"], MET[mid]["fmt"]) for mid in LEAD], "cpe_genre", lang, filt=False))

    # 5. all 39 metrics
    cols = [("name", "작곡가" if k else "Composer", None), ("movements", "악장" if k else "movements", "d")] + [(mid, MET[mid][lang]["name"], MET[mid]["fmt"]) for mid in score_mids()]
    sm2 = sm.copy()
    sm2["name"] = [nm(x, lang) + ((" (연도 미확인)" if k else " (year unconfirmed)") if x in UNDATED else "") for x in sm2.composer]
    b.append(f"<h2>5. 지표 {len(score_mids())}개의 중앙값</h2>" if k else f"<h2>5. Medians of all {len(score_mids())} metrics</h2>")
    b.append("<p class='src'>" + ("소나타 악장만. 화음 지표는 화성 주석이 있는 악장만 센다(베토벤은 91악장 중 64악장). 빈칸은 값 없음." if k else "Sonata movements only. Chord metrics count movements with harmony labels only (Beethoven: 64 of 91). Blank = no value.") + "</p>")
    b.append(table_html(sm2, cols, "son_all", lang, filt=False))
    b.append("<p class='src'>" + ("자료·출처: " if k else "Data and sources: ") +
             "Rodda, K. (2020), <a href='https://blogs.loc.gov/nls-music-notes/2020/07/a-sonata-for-all-seasons-domenico-scarlatti/'>'A sonata for all seasons: Domenico Scarlatti'</a>, <i>NLS Music Notes</i>, Library of Congress, 23 July 2020; "
             "Hentschel, J., Rammos, Y., Neuwirth, M. & Rohrmeier, M. (2025), 'A corpus and a modular infrastructure for the empirical study of (an)notated music', <i>Scientific Data</i> 12:685; "
             "DCMLab corpora <a href='https://github.com/DCMLab/scarlatti_sonatas'>scarlatti_sonatas</a>, <a href='https://github.com/DCMLab/wf_bach_sonatas'>wf_bach_sonatas</a>, <a href='https://github.com/DCMLab/cpe_bach_keyboard'>cpe_bach_keyboard</a>, "
             "<a href='https://github.com/DCMLab/jc_bach_sonatas'>jc_bach_sonatas</a>, <a href='https://github.com/DCMLab/kozeluh_sonatas'>kozeluh_sonatas</a>, <a href='https://github.com/DCMLab/mozart_piano_sonatas'>mozart_piano_sonatas</a>, "
             "<a href='https://github.com/DCMLab/beethoven_piano_sonatas'>beethoven_piano_sonatas</a> (CC BY-NC-SA 4.0). "
             + ("지표 정의는 <a href='metrics/index.html'>지표</a> 면과 같다. 표의 데이터는 <a href='../data/sonatas/sonata_metrics_by_movement.csv'>악장별 CSV</a>로 받을 수 있다." if k
                else "Metric definitions are those of the <a href='metrics/index.html'>Metrics</a> pages. The data are downloadable as a <a href='../data/sonatas/sonata_metrics_by_movement.csv'>by-movement CSV</a>.") + "</p>")
    return "".join(b)


def build(lang, path, page_fn, svg_strip, legend, table_html, stat_spec):
    path.write_text(page_fn(lang, T[lang]["title"], render(lang, load(), svg_strip, legend, table_html, stat_spec), desc=T[lang]["lead"], active="sonatas"), encoding="utf-8")
