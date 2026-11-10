"""1.10: 'Piece map' page (map.html), design 63.

Reads the piecemap_110_* tables (piecemap_110.py) and score_metrics_110_by_movement.csv (score_metrics_110.py).
Every number in the prose comes from those tables. Axes are not named (design 63 §2 B); a component whose
leave-one-collection-out stability is below 0.8 is marked unstable and gets no interpretation (§8).
Point colour: composition year in six 35-year bins, one hue (validated ordinal ramps, light and dark).
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import colour_19 as col19  # noqa: E402
import romantic_pages as rom  # noqa: E402
from registry import METRICS  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/derived"
FILES = ["piecemap_110_points.csv", "piecemap_110_loadings.csv", "piecemap_110_stability.csv", "piecemap_110_selection.csv",
         "piecemap_110_z.csv", "piecemap_110_departure.csv", "score_metrics_110_by_movement.csv"]
MET = {m["id"]: m for m in METRICS}
STABLE = 0.8
YEAR0, YSTEP, NBIN = 1715, 35, 6
YEAR_RAMPS = {"light": ["#8fb4e4", "#729bcf", "#5682bb", "#3a6aa7", "#1c5293", "#003b7f"],
              "dark": ["#39659b", "#547cb0", "#6f95c5", "#8baedb", "#a7c7f0", "#c4e1ff"]}
COLL_LABEL = dict(rom.WORK, **{
    "bach_chorales": ("코랄", "Chorales"), "bach_en_fr_suites": ("영국·프랑스 모음곡", "English & French Suites"),
    "bach_solo": ("무반주 독주곡", "Solo works"), "ABC": ("현악 4중주", "String quartets"),
    "beethoven_piano_sonatas": ("피아노 소나타", "Piano sonatas"), "mozart_piano_sonatas": ("피아노 소나타", "Piano sonatas"),
    "scarlatti_sonatas": ("소나타", "Sonatas"), "wf_bach_sonatas": ("소나타", "Sonatas"), "cpe_bach_keyboard": ("건반 작품", "Keyboard works"),
    "jc_bach_sonatas": ("소나타", "Sonatas"), "kozeluh_sonatas": ("소나타", "Sonatas"),
})
NAMES = dict(rom.NAME, Bach=("바흐", "Bach"))


def esc(s):
    return html.escape("" if s is None else str(s))


def coll_name(corpus: str, composer: str, lang: str) -> str:
    k = 0 if lang == "ko" else 1
    return f"{NAMES.get(composer, (composer, composer))[k]} · {COLL_LABEL.get(corpus, (corpus, corpus))[k]}"


def year_bin(y) -> int | None:
    if pd.isna(y):
        return None
    return int(min(NBIN - 1, max(0, (y - YEAR0) // YSTEP)))


def css() -> str:
    def block(mode):
        return "".join(f"--y{i + 1}:{c};" for i, c in enumerate(YEAR_RAMPS[mode]))
    rules = "".join(f".pm .yb{i + 1}{{fill:var(--y{i + 1})}}.pm-leg .yb{i + 1}{{fill:var(--y{i + 1})}}" for i in range(NBIN))
    return ("<style>:root{" + block("light") + "}@media(prefers-color-scheme:dark){:root:not([data-theme=\"light\"]){" + block("dark") + "}}"
            ":root[data-theme=\"dark\"]{" + block("dark") + "}" + rules
            + ".pm circle{stroke:var(--card);stroke-width:.6;cursor:pointer}.pm circle.yb0{fill:none;stroke:var(--fg3);stroke-width:1}"
            ".pm circle.dim{opacity:.12}.pm circle.sel{stroke:var(--fg);stroke-width:1.6}"
            ".pm-ctl{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;margin:.5rem 0}.pm-ctl select{font:inherit;font-size:.9rem;padding:.2rem .4rem;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:6px}"
            ".pm-ax{font-size:11px;fill:var(--fg2)}</style>")


def scatter(pts: pd.DataFrame, lang: str, mapname: str, stab: pd.Series) -> str:
    k = lang == "ko"
    w, h, m = 900, 560, 48
    x, y = pts["pc1"].to_numpy(float), pts["pc2"].to_numpy(float)
    lo_x, hi_x, lo_y, hi_y = x.min(), x.max(), y.min(), y.max()
    px = lambda v: m + (v - lo_x) / (hi_x - lo_x) * (w - 2 * m)  # noqa: E731
    py = lambda v: h - m - (v - lo_y) / (hi_y - lo_y) * (h - 2 * m)  # noqa: E731
    out = [f"<line x1='{px(0):.1f}' y1='{m - 10}' x2='{px(0):.1f}' y2='{h - m + 10}' stroke='var(--grid)'/>",
           f"<line x1='{m - 10}' y1='{py(0):.1f}' x2='{w - m + 10}' y2='{py(0):.1f}' stroke='var(--grid)'/>"]
    order = np.argsort(pts["year"].fillna(0).to_numpy())  # later years drawn on top
    for i in order:
        r = pts.iloc[i]
        b = year_bin(r.year)
        cls = f"yb{b + 1}" if b is not None else "yb0"
        yr = f"{int(r.year)}" if pd.notna(r.year) else ("연도 미확인" if k else "year unconfirmed")
        tip = f"{coll_name(r.corpus, r.composer, lang)} · {r.piece_id} · {yr}"
        out.append(f"<circle cx='{px(r.pc1):.1f}' cy='{py(r.pc2):.1f}' r='3.2' class='{cls}' data-c='{esc(r.corpus)}' data-k='{esc(r.corpus)}|{esc(r.piece_id)}'><title>{esc(tip)}</title></circle>")
    e1, e2 = stab["pc1_explained"] * 100, stab["pc2_explained"] * 100
    u2 = stab["pc2_loo_min"] < STABLE
    out.append(f"<text x='{w / 2}' y='{h - 8}' text-anchor='middle' class='pm-ax'>{'1성분' if k else 'Component 1'} ({'설명 분산' if k else 'variance explained'} {e1:.0f}%)</text>")
    out.append(f"<text x='14' y='{h / 2}' text-anchor='middle' transform='rotate(-90 14 {h / 2})' class='pm-ax'>{'2성분' if k else 'Component 2'} ({e2:.0f}%){(' — 불안정' if k else ' — unstable') if u2 else ''}</text>")
    return f"<svg class='pm' id='pm-{mapname}' viewBox='0 0 {w} {h}' width='100%' role='img' aria-label='{'곡 지도' if k else 'Piece map'}'>{''.join(out)}</svg>"


def year_legend(lang: str) -> str:
    k = lang == "ko"
    cells = []
    for i in range(NBIN):
        a = YEAR0 + i * YSTEP
        lab = f"{a}–{a + YSTEP - 1}" if i < NBIN - 1 else f"{a}–"
        cells.append(f"<circle cx='{240 + i * 105}' cy='12' r='5' class='yb{i + 1}'/><text x='{250 + i * 105}' y='16' class='km-lab'>{lab}</text>")
    cells.append(f"<circle cx='{240 + NBIN * 105}' cy='12' r='5' fill='none' stroke='var(--fg3)'/><text x='{250 + NBIN * 105}' y='16' class='km-lab'>{'연도 미확인' if k else 'year unconfirmed'}</text>")
    return f"<svg class='pm-leg' viewBox='0 0 960 24' width='100%' role='img' aria-label='{'작곡 연도 범례' if k else 'Composition year legend'}'><text x='224' y='16' text-anchor='end' class='km-lab'>{'작곡 연도' if k else 'Composed'}</text>{''.join(cells)}</svg>"


def filter_ctl(pts: pd.DataFrame, lang: str, mapname: str) -> str:
    k = lang == "ko"
    opts = sorted({(r.corpus, coll_name(r.corpus, r.composer, lang)) for r in pts.itertuples()}, key=lambda t: t[1])
    o = "".join(f"<option value='{esc(c)}'>{esc(n)}</option>" for c, n in opts)
    return (f"<div class='pm-ctl'><label>{'곡집 강조' if k else 'Highlight a collection'} "
            f"<select data-pm='{mapname}'><option value=''>{'모두' if k else 'All'}</option>{o}</select></label></div>")


def loadings_table(L: pd.DataFrame, lang: str, mapname: str, table_html) -> str:
    k = lang == "ko"
    x = L[L["map"] == mapname]
    rows = []
    for pc in ("pc1", "pc2"):
        top = x.reindex(x[pc].abs().sort_values(ascending=False).index).head(5)
        for r in top.itertuples():
            rows.append(dict(pc=("1성분" if k else "Component 1") if pc == "pc1" else ("2성분" if k else "Component 2"),
                             metric=MET[r.metric][lang]["name"], v=getattr(r, pc)))
    return table_html(pd.DataFrame(rows), [("pc", "성분" if k else "Component", None), ("metric", "지표" if k else "Metric", None), ("v", "적재값" if k else "Loading", ".2f")], f"ld_{mapname}", lang, filt=False)


def fingerprint_block(lang: str) -> str:
    """Click a point in the harmony map -> its z-scores as a row of cells (JS reads the embedded JSON)."""
    k = lang == "ko"
    Z = pd.read_csv(D / "piecemap_110_z.csv")
    mids = [c for c in Z.columns if c not in ("corpus", "piece_id")]
    data = {"m": [MET[m][lang]["name"] for m in mids],
            "r": {f"{r.corpus}|{r.piece_id}": [round(float(v), 2) for v in r[2:]] for r in Z.itertuples(index=False)}}
    js = ("<script>(function(){var D=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"
          "function cls(z){var v=Math.max(-6,Math.min(6,Math.round(z*2)));return v===0?'kh-z':(v>0?'kh-p'+v:'kh-m'+(-v))}"
          "function show(key,label){var r=D.r[key],el=document.getElementById('pm-fp');if(!el)return;"
          "if(!r){el.innerHTML='<p class=\"src\">" + ("이 악장은 화음 지도에 없어 지문이 없다." if k else "This movement is not in the harmony map, so it has no fingerprint.") + "</p>';return}"
          "var w=900,x0=0,cw=(w-110)/r.length,s='<svg viewBox=\"0 0 '+w+' 160\" width=\"100%\" role=\"img\">';"
          "for(var i=0;i<r.length;i++){var x=x0+i*cw;s+='<rect x=\"'+(x+1).toFixed(1)+'\" y=\"4\" width=\"'+(cw-2).toFixed(1)+'\" height=\"22\" rx=\"2\" class=\"'+cls(r[i])+'\"><title>'+D.m[i]+': z = '+r[i]+'</title></rect>';"
          "s+='<text x=\"'+(x+cw/2).toFixed(1)+'\" y=\"34\" transform=\"rotate(50 '+(x+cw/2).toFixed(1)+' 34)\" class=\"km-lab\">'+D.m[i]+'</text>'}"
          "el.innerHTML='<p><b>'+label+'</b></p>'+s+'</svg>'}"
          "document.querySelectorAll('.pm circle').forEach(function(c){c.addEventListener('click',function(){"
          "document.querySelectorAll('.pm circle.sel').forEach(function(x){x.classList.remove('sel')});c.classList.add('sel');"
          "show(c.getAttribute('data-k'),c.querySelector('title').textContent)})});"
          "document.querySelectorAll('.pm-ctl select').forEach(function(s){s.addEventListener('change',function(){var v=s.value,svg=document.getElementById('pm-'+s.getAttribute('data-pm'));"
          "svg.querySelectorAll('circle').forEach(function(c){c.classList.toggle('dim',v!==''&&c.getAttribute('data-c')!==v)})})})})();</script>")
    head = ("<p>화음 지도의 점을 누르면 그 악장의 「지문」이 여기에 나온다. 칸 하나가 지표 하나이고, 색은 화음 지도에 들어간 793악장 평균과 견준 값(z)이다. 파랑은 평균보다 낮고 주황은 높다. 색 한 단계가 표준편차 0.5이고, ±3 표준편차에서 가장 진하다.</p>"
            if k else "<p>Click a point in the harmony map to see that movement's fingerprint here: one cell per metric, coloured by its z-score against the 793 movements of the harmony map (blue below the mean, orange above; one colour step per half a standard deviation, strongest at ±3).</p>")
    return head + "<div id='pm-fp'><p class='src'>" + ("(아직 고른 악장이 없다)" if k else "(no movement selected yet)") + "</p></div>" + js


def departure_section(lang: str, table_html, stat_spec) -> str:
    k = lang == "ko"
    s = pd.read_csv(D / "score_metrics_110_by_movement.csv")
    dep = pd.read_csv(D / "piecemap_110_departure.csv").iloc[0]
    ok = s.dropna(subset=["departure_mean", "departure_mean_notes"])
    w, h, m = 520, 400, 46
    hi = max(ok["departure_mean"].max(), ok["departure_mean_notes"].max())
    px = lambda v: m + v / hi * (w - 2 * m)  # noqa: E731
    py = lambda v: h - m - v / hi * (h - 2 * m)  # noqa: E731
    dots = "".join(f"<circle cx='{px(r.departure_mean):.1f}' cy='{py(r.departure_mean_notes):.1f}' r='2.4' fill='var(--s1)' fill-opacity='.45'><title>{esc(r.corpus)} · {esc(r.piece_id)}</title></circle>" for r in ok.itertuples())
    ticks = "".join(f"<text x='{px(t):.1f}' y='{h - m + 16}' text-anchor='middle' class='pm-ax'>{t}</text><text x='{m - 8}' y='{py(t) + 4:.1f}' text-anchor='end' class='pm-ax'>{t}</text>" for t in range(int(hi) + 1))
    axes = ticks + (f"<line x1='{px(0)}' y1='{py(0)}' x2='{px(hi)}' y2='{py(hi)}' stroke='var(--grid)' stroke-dasharray='4 4'/>"
            f"<text x='{w / 2}' y='{h - 8}' text-anchor='middle' class='pm-ax'>{'주석판 이탈도' if k else 'Annotated departure'}</text>"
            f"<text x='14' y='{h / 2}' text-anchor='middle' transform='rotate(-90 14 {h / 2})' class='pm-ax'>{'음표 추정 이탈도' if k else 'Note-only departure'}</text>")
    fig = f"<figure><svg viewBox='0 0 {w} {h}' width='100%' style='max-width:560px' role='img' aria-label='{'주석판과 음표 추정판의 비교' if k else 'Annotated vs note-only departure'}'>{axes}{dots}</svg>"
    more = float((ok["departure_mean_notes"] > ok["departure_mean"]).mean())
    cap = (f"<figcaption>점 하나가 악장 하나({int(dep.n)}악장). 점선은 두 값이 같은 자리다. 스피어먼 순위 상관 {dep.rho:.2f}(악장 단위 부트스트랩 95% 구간 {dep.ci_lo:.2f}~{dep.ci_hi:.2f}; 곡집·작품 단위의 묶임은 반영하지 않았다). "
           f"음표 추정판이 {more * 100:.0f}%의 악장에서 더 크다. 창이 짧아 추정된 조가 자주 바뀌는 효과, 기준 조를 다르게 잡는 효과 등이 함께 작용할 수 있으나, 이 자료로 원인을 가를 수는 없다. "
           "음표 추정판의 계산: 마디 기록(mc) 4개씩 겹치지 않는 창으로 나누고(마지막 짧은 창도 포함), 창마다 음 길이로 가중한 12음고류(옥타브를 무시한 음이름) 분포와 크룸한슬·케슬러(1982) 프로필"
           "(장조 6.35·2.23·3.48·2.33·4.38·4.09·2.52·5.19·2.39·3.66·2.29·2.88, 단조 6.33·2.68·3.52·5.38·2.60·3.53·2.54·4.75·3.98·2.69·3.34·3.17, 으뜸음부터 반음씩)의 상관이 가장 큰 조를 고른다. "
           "곡 전체의 조도 같은 방법으로 정하고, 창마다 그 조와의 조표 차(0~6으로 접음)를 창의 악보 길이로 가중 평균한다. 음표는 꾸밈음을 빼고, 붙임줄 뒷음은 같은 음높이·이어지는 시각의 앞 음에 합친다(성부가 달라도 잇는다).</figcaption></figure>"
           if k else
           f"<figcaption>One dot per movement ({int(dep.n)} movements); the dashed line is where the two agree. Spearman rank correlation {dep.rho:.2f} (95% bootstrap interval over movements, {dep.ci_lo:.2f}–{dep.ci_hi:.2f}; clustering by collection or work is not taken into account). "
           f"The note-only version is larger for {more * 100:.0f}% of movements. Short windows that make the estimated key change often and a different choice of reference key may both contribute, but these data cannot separate the causes. "
           "How the note-only version is computed: non-overlapping windows of 4 measure records (mc), the last shorter window included; in each, the key whose Krumhansl–Kessler (1982) profile "
           "(major 6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88; minor 6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17; from the tonic by semitone) correlates best with the duration-weighted pitch-class distribution. "
           "The whole movement's key is found the same way, and each window's signature difference from it (folded to 0–6) is averaged with the windows' notated lengths as weights. Grace notes are left out; a tied continuation is merged into a note of the same pitch ending where it starts (even in another voice).</figcaption></figure>")
    rows = []
    for c, g in s.dropna(subset=["departure_mean"]).groupby("corpus"):
        rows.append(dict(corpus=c, n=len(g), dm=g["departure_mean"].median(), ot=g["off_tonic_share"].median(), mx=g["departure_max"].median()))
    return fig + cap, rows


def render(lang, svg_strip, legend, table_html, stat_spec):
    k = lang == "ko"
    pts = pd.read_csv(D / "piecemap_110_points.csv")
    L = pd.read_csv(D / "piecemap_110_loadings.csv")
    st = pd.read_csv(D / "piecemap_110_stability.csv").set_index("map")
    sel = pd.read_csv(D / "piecemap_110_selection.csv")
    b = [col19.css() + css(), f"<h1>{'곡 지도' if k else 'Piece map'}</h1><p class='lead'>"
         + ("이 사이트의 악장 하나하나를 악보 지표 수십 개로 된 벡터로 보고, 그 벡터들을 평면에 놓았다. 두 성분에서 가까운 점은 그 두 방향에서 닮은 악장이다. 두 성분이 담는 퍼짐은 전체의 일부(화음 지도 24%, 음표 지도 38%)라서, 평면에서 가까워도 다른 지표에서는 다를 수 있다." if k else
            "Each movement on the site is treated as a vector of dozens of score metrics, and the vectors are laid out on a plane. Points close together are alike along these two directions. The two components hold only part of the spread (24% in the harmony map, 38% in the note map), so movements close on the plane can still differ on other metrics.") + "</p>"]
    # 1. method
    ex = sel[~sel["kept"].astype(bool)].drop_duplicates("metric")
    why = {"length": ("악장 길이와 상관이 커서", "correlated with movement length"), "missing": ("결측이 많아서", "too often missing"),
           "domain": ("정의상 일부 곡집·곡에만 값이 있어서", "defined only for some collections or pieces")}
    exl = " ".join(f"{why[c][0 if k else 1]}{':' if not k else ' 뺀 것:'} {', '.join(MET[m][lang]['name'] for m in ex.loc[ex.reason == c, 'metric'])}." for c in ("length", "domain", "missing") if (ex.reason == c).any())
    b.append(("<h2>1. 만든 방법</h2><ul>"
              "<li>지도마다, 그 지도에 들어간 악장(지표 값이 모두 있는 악장)을 기준으로 지표를 평균 0·표준편차 1(모표준편차)로 바꾼 뒤(z), 주성분 분석으로 가장 많이 퍼지는 두 방향을 찾아 가로(1성분)·세로(2성분)로 놓았다.</li>"
              "<li>최종 계산에 쓴 지표 고르기 규칙은 셋이다. 앞의 둘은 계산 전에 정했다: 악장 길이(로그)와의 스피어먼 상관 절댓값이 0.5를 넘는 지표와, 결측이 30%를 넘는 지표를 뺀다(화음 지도의 결측률은 화성 주석이 있는 악장 기준). 셋째 규칙인 「정의상 일부 곡집·곡에만 값이 있는 지표를 뺀다」는 첫 계산에서 4중주 곡집 전체가 지도에서 빠지는 것을 보고 더했다.</li>"
              "<li>축에 이름을 붙이지 않는다. 대신 성분마다 적재값이 큰 지표 다섯을 표로 적는다. 곡집 하나를 뺐을 때 적재값이 크게 바뀌는(상관 0.8 미만) 성분은 「불안정」으로 표시하고 해석하지 않는다.</li>"
              f"<li>{esc(exl)}</li></ul>"
              if k else
              "<h2>1. How it is made</h2><ul>"
              "<li>For each map, each metric is standardized over the movements in that map (those with every value present; mean 0, population SD 1); principal component analysis finds the two directions of greatest spread, drawn as the horizontal (component 1) and vertical (component 2) axes.</li>"
              "<li>The final computation uses three selection rules. The first two were fixed before computing: drop metrics whose |Spearman correlation| with log movement length exceeds 0.5, and those missing for more than 30% of movements (for the harmony map, counted among movements with harmony labels). The third, 'drop metrics defined only for some collections or pieces', was added after the first run dropped every string-quartet collection from the map.</li>"
              "<li>Axes are not named. Instead the five metrics with the largest loadings are listed for each component. A component whose loadings change much when one collection is left out (correlation below 0.8) is marked unstable and not interpreted.</li>"
              f"<li>Left out — {esc(exl)}</li></ul>"))
    # 2./3. maps
    for i, (mp, title_ko, title_en) in enumerate((("harmony", "화음 지도 — 음표 지표와 화음 지표", "Harmony map: note and chord metrics"),
                                                   ("notes", "음표 지도 — 음표 지표만", "Note map: note metrics only")), start=2):
        p = pts[pts["map"] == mp]
        s = st.loc[mp]
        q = p.dropna(subset=["year"])
        r1, r2 = q[["year", "pc1"]].corr(method="spearman").iloc[0, 1], q[["year", "pc2"]].corr(method="spearman").iloc[0, 1]
        stab_txt = ("부트스트랩 200회에서 적재값과의 상관 중앙값은 1성분 {:.2f}·2성분 {:.2f}, 곡집 하나씩 뺐을 때의 최솟값은 1성분 {:.2f}·2성분 {:.2f}다. 작곡 연도와의 스피어먼 상관은 1성분 {:.2f}, 2성분 {:.2f}."
                    if k else "Over 200 bootstrap resamples the median correlation with the full-data loadings is {:.2f} (component 1) and {:.2f} (component 2); leaving out one collection at a time, the minimum is {:.2f} and {:.2f}. Spearman correlation with composition year: {:.2f} (component 1), {:.2f} (component 2).").format(
            s.pc1_boot_median, s.pc2_boot_median, s.pc1_loo_min, s.pc2_loo_min, r1, r2).replace("-0", "−0")
        if s.pc2_loo_min < STABLE:
            stab_txt += (" 2성분은 곡집 하나에 따라 크게 바뀌므로 해석하지 않는다." if k else " Component 2 changes a lot with a single collection, so it is not interpreted.")
        stab_txt += (" 부트스트랩 값은 난수 시드에 따라 조금 달라지고(특히 불안정한 성분), 판정은 곡집 빼기 최솟값으로 한다." if k else " Bootstrap values vary a little with the random seed (especially for an unstable component); the verdict uses the leave-one-collection-out minimum.")
        b.append(f"<h2>{i}. {title_ko if k else title_en}</h2><p>"
                 + (f"{int(s.n_movements)}악장, 지표 {int(s.n_metrics)}개." if k else f"{int(s.n_movements)} movements, {int(s.n_metrics)} metrics.")
                 + ("" if mp == "notes" else (" 화성 주석이 있는 악장만 들어간다." if k else " Movements with harmony labels only."))
                 + (" 화성 주석이 없는 바흐 코랄도 들어간다." if (k and mp == "notes") else (" Bach's chorales, which have no harmony labels, are included." if mp == "notes" else ""))
                 + "</p>" + filter_ctl(p, lang, mp) + year_legend(lang)
                 + f"<figure>{scatter(p, lang, mp, s)}<figcaption>{stab_txt}</figcaption></figure>"
                 + loadings_table(L, lang, mp, table_html))
    # 4. fingerprint
    b.append(("<h2>4. 악장의 지문</h2>" if k else "<h2>4. A movement's fingerprint</h2>") + fingerprint_block(lang))
    # 5. departure
    fig, rows = departure_section(lang, table_html, stat_spec)
    comp_of = {r.corpus: r.composer for r in pts.itertuples()}
    tb = pd.DataFrame([dict(name=coll_name(r["corpus"], comp_of.get(r["corpus"], ""), lang), n=r["n"], dm=r["dm"], ot=r["ot"], mx=r["mx"]) for r in rows]).sort_values("dm")
    b.append(("<h2>5. 으뜸조에서 얼마나 멀리, 얼마나 오래</h2><p>1.10에서 더한 지표 셋(<a href='metrics/departure_mean.html'>으뜸조 이탈도</a>·<a href='metrics/off_tonic_share.html'>으뜸조 밖 시간 비율</a>·<a href='metrics/departure_max.html'>최대 이탈</a>)은 DCML 주석자가 붙인 국소 조로 계산한다. 아래 표는 곡집별 중앙값이다. 주석에 기대지 않는 방법과 견주려고, 음표만으로 조를 추정해 같은 값을 낸 대조판을 함께 그렸다. 어느 쪽이 맞는지를 가린 것은 아니다.</p>"
              if k else "<h2>5. How far from home, and for how long</h2><p>The three metrics added in 1.10 (<a href='metrics/departure_mean.html'>departure from the home key</a>, <a href='metrics/off_tonic_share.html'>time away from the home key</a>, <a href='metrics/departure_max.html'>furthest key</a>) use the local keys annotated by DCML. The table gives collection medians. For comparison with a method that does not rely on annotation, a version that finds keys from the notes alone is plotted against them. This does not decide which is right.</p>")
             + table_html(tb, [("name", "곡집" if k else "Collection", None), ("n", "악장" if k else "movements", "d"), ("dm", MET["departure_mean"][lang]["name"], ".2f"),
                               ("ot", MET["off_tonic_share"][lang]["name"], ".3f"), ("mx", MET["departure_max"][lang]["name"], ".1f")], "dep_tbl", lang, filt=False)
             + fig)
    b.append("<p class='src'>" + ("자료·출처: " if k else "Data and sources: ")
             + "DCMLab corpora (CC BY-NC-SA 4.0); Hentschel, J., Rammos, Y., Neuwirth, M. & Rohrmeier, M. (2025), <i>Scientific Data</i> 12:685; "
             "Harasim, D., Moss, F. C., Ramirez, M. & Rohrmeier, M. (2021), 'Exploring the foundations of tonality: statistical cognitive modeling of modes in the history of Western classical music', <i>Humanities and Social Sciences Communications</i> 8: 5"
             + (" — 곡 하나를 음 분포 공간의 한 점으로 보는 틀; " if k else " — a piece as a point in a space of pitch distributions; ")
             + "Weiß, C., Mauch, M., Dixon, S. & Müller, M. (2019; online 2018), 'Investigating style evolution of Western classical music: a computational approach', <i>Musicae Scientiae</i> 23(4): 486–507"
             + (" — 작곡 연도에 따른 연속적인 변화를 계산으로 살핀 연구; " if k else " — a computational study of continuous change over composition years; ")
             + "Herremans, D. & Chew, E. (2016), 'Tension ribbons: quantifying and visualising tonal tension', TENOR 2016"
             + (" — 음 묶음의 중심과 곡 전체 조의 중심 사이 거리(tensile strain, 나선 배열); " if k else " — distance between the centre of a cluster of notes and that of the global key (tensile strain, spiral array); ")
             + "Krumhansl, C. L. & Kessler, E. J. (1982), <i>Psychological Review</i> 89(4): 334–368" + (" — 조성 프로필. " if k else " — key profiles. ")
             + (" 표의 데이터는 <a href='../data/map/piecemap_110_points.csv'>점 좌표</a>·<a href='../data/map/piecemap_110_loadings.csv'>적재값</a>·<a href='../data/map/score_metrics_110_by_movement.csv'>이탈도</a> CSV로 내려받을 수 있다."
                if k else " Data: <a href='../data/map/piecemap_110_points.csv'>point coordinates</a>, <a href='../data/map/piecemap_110_loadings.csv'>loadings</a>, <a href='../data/map/score_metrics_110_by_movement.csv'>departure metrics</a> (CSV).") + "</p>")
    return "".join(b)


def build(lang, path, page_fn, svg_strip, legend, table_html, stat_spec):
    k = lang == "ko"
    title = "곡 지도" if k else "Piece map"
    desc = "악장마다 악보 지표 벡터를 평면에 놓은 지도와 지문, 으뜸조 이탈도" if k else "Movements laid out by their score metrics, with fingerprints and departure from the home key"
    path.write_text(page_fn(lang, title, render(lang, svg_strip, legend, table_html, stat_spec), desc=desc, active="map"), encoding="utf-8")
