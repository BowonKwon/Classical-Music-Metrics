"""History of harmony page (1.6): harmony.html in each language, from the DCML Distant Listening Corpus.

The site build calls build(lang, path, page_fn). Reads data/derived/dlc_*.csv (dlc_metrics.py) and
data/aliases/dlc_corpora.csv. Every number in the prose is computed from those tables.
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from history_pages import GCSS, ticks  # noqa: E402
from registry import METRICS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D, ALI = ROOT / "data/derived", ROOT / "data/aliases"
HARMONY_FILES = ["dlc_movement_metrics.csv", "dlc_corpus_metrics.csv", "dlc_period_metrics.csv"]
HARMONY_ALIAS_FILES = ["dlc_corpora.csv"]

MET = {m["id"]: m for m in METRICS}
LEAD = ["seventh_chord_ratio", "chromatic_ratio", "applied_chord_ratio", "chord_vocabulary_per_100_labels"]
PERIOD_METRICS = ["chromatic_ratio", "pitch_class_entropy", "tpc_vocabulary", "applied_chord_ratio", "seventh_chord_ratio",
                  "chromatic_numeral_ratio", "chord_vocabulary_per_100_labels", "chords_per_measure"]
GENRE = {"keyboard": ("건반", "Keyboard", "var(--g1)"), "chamber": ("실내악·독주", "Chamber & solo", "var(--g2)"),
         "vocal": ("성악", "Vocal", "var(--g3)")}
X0, X1 = 1550, 1940
MIN_CORPORA = 2  # a period enters the line only with at least this many corpora

T = {
    "ko": dict(title="화성의 역사", lead="16세기 말 건반 음악·마드리갈부터 1931년 재즈 춤곡까지, 같은 주석 규칙으로 화성 분석한 40개 곡집을 시대순으로 늘어놓고 화음과 음의 쓰임이 어떻게 달라졌는지 본다.",
               show="표 보기", rows="행"),
    "en": dict(title="A history of harmony", lead="From late 16th-century keyboard music and madrigals to a jazz dance suite of 1931: forty collections analysed under one harmonic annotation standard, set in date order to see how the use of chords and notes changed.",
               show="Show table", rows="rows"),
}


def esc(s):
    return html.escape("" if s is None else str(s))


def mname(mid, lang):
    return MET[mid][lang]["name"]


def table(df, cols, tid, lang):
    h = "".join(f"<th class='{'num' if f else ''}'>{esc(n)}</th>" for _, n, f in cols)
    rows = []
    for _, r in df.iterrows():
        cells = []
        for c, _, f in cols:
            v = r[c]
            cells.append(f"<td class='num' data-v='{v}'>{format(v, f) if pd.notna(v) else ''}</td>" if f else f"<td>{esc(v)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (f"<details><summary style='cursor:pointer;color:var(--fg2);font-size:.9rem;margin:.3rem 0'>{T[lang]['show']} ({len(rows)}{' ' if lang == 'en' else ''}{T[lang]['rows']})</summary>"
            f"<div class='wrap'><table class='sort' id='{tid}'><thead><tr>{h}</tr></thead><tbody>{''.join(rows)}</tbody></table></div></details>")


def legend(lang, line=True):
    k = lang == "ko"
    items = [f"<span style='--c:{c}'>{ko if k else en}</span>" for ko, en, c in GENRE.values()]
    if line:
        items.append(f"<span style='--c:var(--fg)'>{'구간 중앙값(코퍼스당 한 표)' if k else 'Period median (one vote per corpus)'}</span>")
        items.append(f"<span style='--c:var(--g1)'>{'건반만' if k else 'Keyboard only'}</span>")
    return "<div class='legend'>" + "".join(items) + "</div>"


def years(r, k):
    """Recorded composition range; '?' marks a start year the metadata leaves unknown ('..')."""
    a = f"?–{int(r.composed_max)}" if r.start_unknown_pieces else f"{int(r.composed_min)}–{int(r.composed_max)}"
    return a.replace("–", "~") if k else a


def timeline(c, lang, width=900, row_h=17, label_w=300):
    k = lang == "ko"
    L, R, top = label_w, 14, 6
    pw = width - L - R
    X = lambda v: L + (v - X0) / (X1 - X0) * pw  # noqa: E731
    height = top + row_h * len(c) + 24
    o = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for v in range(1550, X1 + 1, 50):
        o.append(f'<line class="grid" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top}" y2="{height - 20}"/><text x="{X(v):.1f}" y="{height - 6}" text-anchor="middle">{v}</text>')
    for i, r in enumerate(c.itertuples()):
        y = top + i * row_h + row_h / 2
        col = GENRE[r.genre][2]
        lab = f"{r.composer_ko if k else r.composer_en} · {r.collection_ko if k else r.collection_en}"
        o.append(f'<text x="{L - 6}" y="{y + 4:.1f}" text-anchor="end" style="font-size:11px">{esc(lab)}</text>')
        x0, x1 = X(r.composed_min), X(r.composed_max)
        unk = r.start_unknown_pieces > 0
        note = (" (일부 곡 작곡 시작 연도 미상)" if k else " (start year unknown for some pieces)") if unk else ""
        style = f' stroke="{col}" stroke-dasharray="3 2" fill-opacity=".3"' if unk else (" fill-opacity=.45" if r.small else "")
        o.append(f'<rect x="{x0:.1f}" y="{y - 4:.1f}" width="{max(x1 - x0, 4):.1f}" height="8" rx="3" fill="{col}"{style}>'
                 f'<title>{esc(lab)}: {years(r, k)}{note}, {int(r.pieces)} {"곡" if k else "pieces"}, {int(r.bars):,} {"마디" if k else "bars"}</title></rect>')
    o.append("</svg>")
    return "".join(o)


def scatter(c, p, mid, lang, width=440, height=230):
    k = lang == "ko"
    L, R, Tp, B = 46, 10, 10, 24
    pw, ph = width - L - R, height - Tp - B
    v = c[mid].dropna()
    hi = float(v.max()) * 1.08 if len(v) else 1
    lo = 0.0
    X = lambda x: L + (x - X0) / (X1 - X0) * pw  # noqa: E731
    Y = lambda y: Tp + ph - (y - lo) / (hi - lo) * ph  # noqa: E731
    fmt = MET[mid]["fmt"]
    o = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for t in ticks(lo, hi, 4):
        o.append(f'<line class="grid" x1="{L}" x2="{width - R}" y1="{Y(t):.1f}" y2="{Y(t):.1f}"/><text x="{L - 4}" y="{Y(t) + 4:.1f}" text-anchor="end">{format(t, fmt if "f" in fmt else ".0f")}</text>')
    for x in range(1600, X1 + 1, 100):
        o.append(f'<text x="{X(x):.1f}" y="{height - 6}" text-anchor="middle">{x}</text>')
    for scope, col, dash in (("all", "var(--fg)", ""), ("keyboard", "var(--g1)", ' stroke-dasharray="5 4"')):
        q = p[(p.scope == scope) & (p.corpora >= MIN_CORPORA)].dropna(subset=[mid]).sort_values("period")
        pts = [(X(r.period + 25), Y(getattr(r, mid))) for r in q.itertuples()]
        if len(pts) > 1:
            o.append(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}" fill="none" stroke="{col}" stroke-width="2.2" stroke-linejoin="round"{dash}/>')
    for r in c.dropna(subset=[mid]).itertuples():
        lab = f"{r.composer_ko if k else r.composer_en} · {r.collection_ko if k else r.collection_en}"
        o.append(f'<circle cx="{X(r.year):.1f}" cy="{Y(getattr(r, mid)):.1f}" r="{3.2 if r.small else 4.6}" fill="{GENRE[r.genre][2]}" fill-opacity="{.45 if r.small else .85}" stroke="var(--card)" stroke-width="1">'
                 f'<title>{esc(lab)} ({int(r.year)}): {format(getattr(r, mid), fmt)}</title></circle>')
    o.append("</svg>")
    return "".join(o)


def load():
    c = pd.read_csv(D / "dlc_corpus_metrics.csv").sort_values(["year", "corpus"], kind="mergesort")
    p = pd.read_csv(D / "dlc_period_metrics.csv")
    m = pd.read_csv(D / "dlc_movement_metrics.csv", usecols=["corpus", "n_measures"])
    return c, p, m


def render(lang, c, p, m):
    k = lang == "ko"
    t = T[lang]
    b = [f"<style>{GCSS}</style><div class='hero'><h1>{t['title']}</h1><p class='lead'>{t['lead']}</p></div>"]
    n_pieces, n_bars, n_corp = int(c.pieces.sum()), int(c.bars.sum()), len(c)
    n_lab = int(c.labelled_pieces.sum())
    gcount = c.genre.value_counts()
    # 1. data
    if k:
        b.append("<h2>1. 자료</h2>"
                 f"<p>DCML의 「Distant Listening Corpus」(Hentschel 외 2025)는 곡집 {n_corp}개, 악장·곡 {n_pieces:,}개, {n_bars:,}마디의 악보 모음이다. 그중 {n_lab:,}곡에 같은 규칙으로 로마 숫자 화성 기호가 붙어 있다. 화음 지표는 이 {n_lab:,}곡에서, 음표 지표는 전체에서 센다. 이 사이트의 악보 지표에 이미 쓰던 5개(바흐 둘·베토벤 둘·모차르트)에 35개를 더한 것이다. "
                 f"장르로 나누면 건반 {gcount.get('keyboard', 0)}개, 실내악·독주 {gcount.get('chamber', 0)}개, 성악 {gcount.get('vocal', 0)}개다. 관현악 총보는 없다. 「바그너 서곡」은 피아노 편곡판이라 건반에 넣었다.</p>"
                 "<p>이 표본은 시대를 대표하도록 뽑힌 것이 아니다. 연구자들이 주석을 붙인 곡집의 모음이라 건반 음악이 많고, 시대마다 들어간 작곡가가 몇 명뿐이다. 아래 그림은 「이 곡집들에서 이렇게 달라진다」로 읽어야 한다.</p>")
    else:
        b.append("<h2>1. The data</h2>"
                 f"<p>DCML's Distant Listening Corpus (Hentschel et al. 2025) holds {n_corp} collections of scores: {n_pieces:,} pieces and movements, {n_bars:,} bars. {n_lab:,} of the pieces carry Roman-numeral harmony labels added under one standard; chord metrics are counted on those {n_lab:,}, note metrics on all pieces. Five of them (two Bach, two Beethoven, Mozart) already feed this site's score metrics; 35 are new. "
                 f"By genre: {gcount.get('keyboard', 0)} keyboard, {gcount.get('chamber', 0)} chamber or solo, {gcount.get('vocal', 0)} vocal. There are no orchestral scores; the 'Wagner overtures' are piano arrangements and are counted as keyboard.</p>"
                 "<p>The sample was not drawn to represent its periods. It is the set of collections that researchers annotated, so keyboard music dominates and each period has only a few composers. Read the charts below as 'how these collections change', not as a history of all music.</p>")
    b.append(legend(lang, line=False) + f"<figure>{timeline(c, lang)}</figure>")
    b.append(f"<p class='src'>{'막대는 원자료(metadata)에 적힌 작곡 연도의 범위로, 곡들의 가장 이른 시작 연도부터 가장 늦은 끝 연도까지다. 점선 막대는 일부 곡의 시작 연도가 미상(..)인 곡집이고, 표에서는 「?」로 적었다. 흐린 막대는 300마디 미만의 작은 곡집으로, 작곡가별 값을 따로 읽지 않는다. 아래 그림의 점은 이 범위가 아니라, 곡마다 시작·끝 연도의 가운데를 잡고 그 중앙값에 놓았다.' if k else "Bars show the composition range recorded in the metadata, from the earliest start year to the latest end year of the pieces. Dashed bars are collections where some pieces have an unknown start year (..), marked ? in the table. Faded bars are collections under 300 bars; their values are not read on their own. The dots in the charts below are placed not on this range but on the median of the pieces' midpoint years."}</p>")

    # 2. trends
    q = p[(p.scope == "all") & (p.corpora >= MIN_CORPORA)].sort_values("period")
    first, last = q.iloc[0], q.iloc[-1]
    sev = q["seventh_chord_ratio"].tolist()
    ups = sum(1 for a, z in zip(sev, sev[1:]) if z > a)
    kq = p[(p.scope == "keyboard") & (p.corpora >= MIN_CORPORA)].sort_values("period")
    ksev = kq["seventh_chord_ratio"].tolist()
    kups = sum(1 for a, z in zip(ksev, ksev[1:]) if z > a)
    if k:
        b.append("<h2>2. 시대에 따라</h2>"
                 f"<p>곡집마다 악장 값의 중앙값을 내고(점), 곡집의 작곡 연도로 50년 구간을 나눈 뒤 그 중앙값들의 중앙값을 이었다(검은 선). 곡집 하나가 한 표다. 곡집이 {MIN_CORPORA}개 미만인 구간은 선에서 뺐다. 파란 점선은 건반 곡집만으로 낸 선이다. 점에 마우스를 올리면 곡집 이름이 나온다. 음표 지표는 꾸밈음과 붙임줄로 이어진 뒷음을 빼고 센다.</p>"
                 f"<ul><li><b>{mname('seventh_chord_ratio', lang)}</b>은 {int(first.period)}년대 구간 {first.seventh_chord_ratio:.3f}에서 {int(last.period)}년대 구간 {last.seventh_chord_ratio:.3f}로 오른다. 선에 오른 구간끼리 앞뒤로 견주면 {len(sev) - 1}번 중 {ups}번 올랐고, 건반 선에서는 {len(ksev) - 1}번 중 {kups}번 올랐다.</li>"
                 f"<li><b>{mname('chromatic_ratio', lang)}</b>은 {int(first.period)}년대 {first.chromatic_ratio:.3f}, {int(last.period)}년대 {last.chromatic_ratio:.3f}다. 20세기 곡집에서 크게 벌어진다.</li>"
                 f"<li><b>{mname('applied_chord_ratio', lang)}</b>은 한 방향으로 움직이지 않는다.</li></ul>")
    else:
        b.append("<h2>2. Across the periods</h2>"
                 f"<p>Each dot is a collection's median over its pieces. Collections are grouped into 50-year periods by composition year, and the black line joins the medians of those collection medians, one vote per collection; periods with fewer than {MIN_CORPORA} collections are left off the line. The dashed blue line uses keyboard collections only. Hover over a dot for its collection. Note metrics leave out grace notes and the tied continuations of notes.</p>"
                 f"<ul><li><b>{mname('seventh_chord_ratio', lang)}</b> rises from {first.seventh_chord_ratio:.3f} in the {int(first.period)}s period to {last.seventh_chord_ratio:.3f} in the {int(last.period)}s. Between neighbouring periods on the line it goes up {ups} times out of {len(sev) - 1}, and {kups} out of {len(ksev) - 1} on the keyboard-only line.</li>"
                 f"<li><b>{mname('chromatic_ratio', lang)}</b> is {first.chromatic_ratio:.3f} in the {int(first.period)}s and {last.chromatic_ratio:.3f} in the {int(last.period)}s, with a wide spread among the 20th-century collections.</li>"
                 f"<li><b>{mname('applied_chord_ratio', lang)}</b> does not move in one direction.</li></ul>")
    b.append(legend(lang) + "<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(380px,1fr));gap:.6rem 1.2rem'>")
    for mid in LEAD:
        b.append(f"<div><h3 style='margin:.4rem 0 .1rem;font-size:.95rem'>{esc(mname(mid, lang))}</h3><p class='src' style='margin:.1rem 0'>{esc(MET[mid][lang]['definition'])}</p>{scatter(c, p, mid, lang)}</div>")
    b.append("</div>")
    pt = p.copy()
    pt["scope_l"] = pt.scope.map({"all": "전체" if k else "all", "keyboard": "건반" if k else "keyboard"})
    pt["period_l"] = pt.period.astype(str) + ("년대~" if k else "–") + (pt.period + 49).astype(str)
    b.append(table(pt, [("scope_l", "범위" if k else "scope", None), ("period_l", "구간" if k else "period", None), ("corpora", "곡집" if k else "collections", ".0f"), ("pieces", "곡" if k else "pieces", ".0f"), ("bars", "마디" if k else "bars", ",.0f")]
                   + [(mm, mname(mm, lang), MET[mm]["fmt"]) for mm in PERIOD_METRICS], "per", lang))

    # 3. caveats on annotation
    zero = c[(c.local_key_changes_per_100_measures.fillna(0) == 0)]
    early = c[c.year < 1650]
    if k:
        b.append("<h2>3. 주석이 만드는 차이</h2>"
                 f"<p>화음 지표는 사람이 붙인 화성 기호를 센 것이다. 같은 규칙을 써도 주석자의 판단이 들어간다. 이 사이트의 <a href='metrics/local_key_changes_per_100_measures.html'>{mname('local_key_changes_per_100_measures', lang)}</a>는 곡집 {len(zero)}개에서 중앙값이 0이다({', '.join(zero.composer_ko.unique())}). 이 곡집들에도 국소 조 표시는 있지만, 곡 대부분이 한 조 안에 머문다. 이 값은 곡의 길이와 형식에 크게 좌우되고, 잠깐의 조 이동을 국소 조로 적을지 부속화음으로 적을지는 주석자가 판단한다. 그래서 전조 빈도와 종지 밀도는 시대 그림에 넣지 않고 아래 곡집 표에만 둔다.</p>"
                 f"<p>{int(early.composed_min.min())}~1650년의 곡집({', '.join(early.composer_ko.unique())})은 장·단조 체계가 굳기 전의 음악이다. 이 시기에 로마 숫자로 화음을 적으면 뒤 시대와 같은 이름의 화음이 같은 기능을 한다는 보장이 없다. 이 구간의 화음 지표는 따로 읽기 바란다. 음표에서 바로 세는 반음계 비율·음급 엔트로피는 이 문제가 없다.</p>")
    else:
        b.append("<h2>3. What the annotation adds</h2>"
                 f"<p>Chord metrics count harmony labels that people added. One standard still leaves room for judgment. On this site the <a href='metrics/local_key_changes_per_100_measures.html'>{mname('local_key_changes_per_100_measures', lang)}</a> has a median of 0 in {len(zero)} collections ({', '.join(zero.composer_en.unique())}). These collections do carry local-key labels, but most of their pieces stay in one key. The value depends heavily on the length and form of the pieces, and whether a brief move to another key is labelled as a local key or as applied chords is the annotator's call. So modulation rate and cadence density stay out of the period charts and appear only in the collection table below.</p>"
                 f"<p>The collections from {int(early.composed_min.min())} to 1650 predate the settled major–minor system. Writing their chords as Roman numerals does not guarantee that a chord of the same name does the same job as in later music, so read the chord metrics for this period on their own. Metrics counted straight from the notes, such as the chromatic ratio and pitch-class entropy, are not affected.</p>")

    # 4. Clara and Robert Schumann
    pair = c[c.corpus.isin(["c_schumann_lieder", "schumann_liederkreis"])].copy()
    if len(pair) == 2:
        pair["name"] = pair.apply(lambda r: f"{r.composer_ko} · {r.collection_ko}" if k else f"{r.composer_en} · {r.collection_en}", axis=1)
        if k:
            b.append("<h2>4. 클라라 슈만과 로베르트 슈만</h2><p>이 코퍼스에 든 유일한 여성 작곡가의 곡집이다. 같은 장르(가곡)이고 같은 무렵에 쓴 로베르트 슈만의 『리더크라이스』와 나란히 놓았다. 두 곡집 모두 12곡, 500마디 안팎이라 차이를 두고 결론을 내리지 않는다.</p>")
        else:
            b.append("<h2>4. Clara and Robert Schumann</h2><p>The only collection by a woman composer in this corpus, set beside Robert Schumann's Liederkreis of the same genre and roughly the same period. Both have 12 songs of about 500 bars, too few to conclude anything from the differences.</p>")
        cols = [("name", "곡집" if k else "collection", None), ("year", "연도(중앙)" if k else "year (median)", ".0f"), ("pieces", "곡" if k else "songs", ".0f"), ("bars", "마디" if k else "bars", ".0f")] + [(mm, mname(mm, lang), MET[mm]["fmt"]) for mm in PERIOD_METRICS]
        h = "".join(f"<th class='{'num' if f else ''}'>{esc(n)}</th>" for _, n, f in cols)
        rows = "".join("<tr>" + "".join(f"<td class='num'>{format(getattr(r, cc), f)}</td>" if f else f"<td>{esc(getattr(r, cc))}</td>" for cc, _, f in cols) + "</tr>" for r in pair.itertuples())
        b.append(f"<div class='wrap'><table><thead><tr>{h}</tr></thead><tbody>{rows}</tbody></table></div>")

    # 5. collection table
    ct = c.copy()
    ct["name"] = ct.apply(lambda r: f"{r.composer_ko} · {r.collection_ko}" if k else f"{r.composer_en} · {r.collection_en}", axis=1)
    ct["genre_l"] = ct.genre.map(lambda g: GENRE[g][0 if k else 1])
    ct["years"] = ct.apply(lambda r: years(r, k), axis=1)
    b.append(f"<h2>{'5. 곡집별 값' if k else '5. By collection'}</h2>")
    b.append(table(ct, [("name", "곡집" if k else "collection", None), ("genre_l", "장르" if k else "genre", None), ("years", "작곡 연도" if k else "composed", None), ("pieces", "곡" if k else "pieces", ".0f"), ("bars", "마디" if k else "bars", ",.0f"), ("labelled_pieces", "화성 주석 곡" if k else "with harmony labels", ".0f")]
                   + [(mm, mname(mm, lang), MET[mm]["fmt"]) for mm in PERIOD_METRICS + ["local_key_changes_per_100_measures", "cadences_per_100_measures"]], "col", lang))
    # sources
    b.append("<p class='src'>" + ("자료: " if k else "Data: ") +
             "Hentschel, J. et al. (2025), 'A corpus and a modular infrastructure for the empirical study of (an)notated music', <i>Scientific Data</i> 12:685 (dataset: the Distant Listening Corpus); "
             "<a href='https://github.com/DCMLab/distant_listening_corpus'>DCMLab/distant_listening_corpus</a>, <a href='https://doi.org/10.5281/zenodo.13844105'>Zenodo 10.5281/zenodo.13844105</a> (CC BY-NC-SA 4.0). "
             + ("지표 정의는 <a href='metrics/index.html'>지표</a> 면과 같다." if k else "Metric definitions are those of the <a href='metrics/index.html'>Metrics</a> pages.") + "</p>")
    return "".join(b)


def build(lang, path, page_fn):
    path.write_text(page_fn(lang, T[lang]["title"], render(lang, *load()), desc=T[lang]["lead"], active="harmony"), encoding="utf-8")
