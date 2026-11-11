"""1.11: 'Composers and genres' page (genres.html), design 67.

Forest and trees (Shneiderman 1996; Tennekes & de Jonge 2014): six big groups, each with one hue from the
validated categorical palette (slots 1-6 in palette order, which is also the stacking order, so every touching
pair passes the adjacent CVD check); clicking a group in the legend expands it into its sub-genres, drawn in
lightness steps of that hue (each ramp validated as ordinal), while the other groups fold into grey.
Works dated only by a first publication within the composer's life are hatched.
Every number in the prose comes from data/derived/genre_life_*.csv (genre_life_111.py).
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import genre_life_111 as gl  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/derived"
FILES = ["genre_life_works.csv", "genre_life_age.csv", "genre_life_era.csv", "genre_life_validation.csv"]
ORDER = ["orchestral", "secular", "chamber", "keyboard", "sacred", "stage", "other"]  # stacking order = palette order
BASE = {"light": {"orchestral": "#2a78d6", "secular": "#eb6834", "chamber": "#1baf7a", "keyboard": "#eda100", "sacred": "#e87ba4", "stage": "#008300", "other": "#9a9a96"},
        "dark": {"orchestral": "#3987e5", "secular": "#d95926", "chamber": "#199e70", "keyboard": "#c98500", "sacred": "#d55181", "stage": "#008300", "other": "#6e6f73"}}
SHADES = {"light": {"orchestral": ["#8fb4e4", "#6690c8", "#3d6ead", "#0e4c92"], "secular": ["#dea08a", "#b1664b", "#842c00"],
                    "chamber": ["#82c1a2", "#51a17c", "#0e8158", "#006136"], "keyboard": ["#cfaa77", "#b18546", "#926100", "#743e00"],
                    "sacred": ["#db9cb1", "#be758e", "#9f4e6d", "#81264e"], "stage": ["#94bf90", "#125d10"], "other": ["#9a9a96"]},
          "dark": {"orchestral": ["#3f6596", "#5e86bc", "#7ea9e3", "#9fceff"], "secular": ["#8e503a", "#c78168", "#ffb598"],
                   "chamber": ["#287353", "#4a9673", "#6bba94", "#8cdfb7"], "keyboard": ["#815b1f", "#a57c3f", "#ca9e5f", "#f1c17f"],
                   "sacred": ["#8c4c64", "#b16c84", "#d88da7", "#ffafcb"], "stage": ["#437040", "#a5dc9f"], "other": ["#6e6f73"]}}
SUBS = {g: [s[0] for s in gl.SUB if s[3] == g] for g in ORDER}
NAME = {
    "Bach, Johann Sebastian": ("바흐", "Bach"), "Haydn, Franz Joseph": ("하이든", "Haydn"), "Mozart, Wolfgang Amadeus": ("모차르트", "Mozart"),
    "Beethoven, Ludwig van": ("베토벤", "Beethoven"), "Schubert, Franz": ("슈베르트", "Schubert"), "Brahms, Johannes": ("브람스", "Brahms"),
    "Tchaikovsky, Pyotr Ilyich": ("차이콥스키", "Tchaikovsky"), "Dvorak, Antonín": ("드보르자크", "Dvořák"), "Mahler, Gustav": ("말러", "Mahler"),
    "Stravinsky, Igor": ("스트라빈스키", "Stravinsky"), "Monteverdi, Claudio": ("몬테베르디", "Monteverdi"), "Purcell, Henry": ("퍼셀", "Purcell"),
    "Vivaldi, Antonio": ("비발디", "Vivaldi"), "Handel, George Frideric": ("헨델", "Handel"), "Telemann, Georg Philipp": ("텔레만", "Telemann"),
    "Gluck, Christoph Willibald": ("글루크", "Gluck"), "Mendelssohn, Felix": ("멘델스존", "Mendelssohn"), "Hensel, Fanny": ("파니 헨젤", "Fanny Hensel"),
    "Schumann, Clara": ("클라라 슈만", "Clara Schumann"), "Chopin, Frédéric": ("쇼팽", "Chopin"), "Liszt, Franz": ("리스트", "Liszt"),
    "Schumann, Robert": ("로베르트 슈만", "Robert Schumann"), "Verdi, Giuseppe": ("베르디", "Verdi"), "Wagner, Richard": ("바그너", "Wagner"),
    "Bruckner, Anton": ("브루크너", "Bruckner"), "Fauré, Gabriel": ("포레", "Fauré"), "Debussy, Claude": ("드뷔시", "Debussy"),
    "Saint-Saëns, Camille": ("생상스", "Saint-Saëns"), "Ravel, Maurice": ("라벨", "Ravel"), "Rimsky-Korsakov, Nikolay": ("림스키코르사코프", "Rimsky-Korsakov"),
}
WARN_NONE = 0.30


def esc(s):
    return html.escape("" if s is None else str(s))


def css() -> str:
    def block(mode):
        v = "".join(f"--gg-{g}:{c};" for g, c in BASE[mode].items())
        for g in ORDER:
            for i, sid in enumerate(SUBS[g]):
                sh = SHADES[mode][g]
                v += f"--gs-{sid}:{sh[min(i, len(sh) - 1)]};"
        return v
    rules = []
    for g in ORDER:
        rules.append(f".gl .g-{g}{{fill:var(--gg-{g})}}.gl-key .g-{g}{{background:var(--gg-{g})}}")
        rules.append(f"body[data-exp] .gl .g-{g}{{fill:var(--fg3);opacity:.28}}")
        rules.append(f"body[data-exp={g}] .gl .g-{g}{{opacity:1}}")
        for sid in SUBS[g]:
            rules.append(f"body[data-exp={g}] .gl .s-{sid}{{fill:var(--gs-{sid})}}.gl-sub .s-{sid}{{background:var(--gs-{sid})}}")
        rules.append(f"body:not([data-exp={g}]) .gl-sub[data-g={g}]{{display:none}}")
    return ("<style>:root{" + block("light") + "}@media(prefers-color-scheme:dark){:root:not([data-theme=\"light\"]){" + block("dark") + "}}"
            ":root[data-theme=\"dark\"]{" + block("dark") + "}" + "".join(rules)
            + ".gl-key{display:flex;flex-wrap:wrap;gap:.4rem;margin:.5rem 0}.gl-key button,.gl-sub span{font:inherit;font-size:.85rem;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg);padding:.15rem .55rem;cursor:pointer;display:inline-flex;align-items:center;gap:.35rem}"
            ".gl-key i,.gl-sub i{display:inline-block;width:.9rem;height:.9rem;border-radius:3px}.gl-key button[aria-pressed=true]{border-color:var(--accent);box-shadow:inset 0 -2px 0 var(--accent)}"
            ".gl-sub{display:flex;flex-wrap:wrap;gap:.4rem;margin:.2rem 0 .6rem}.gl-sub span{cursor:default}"
            ".gl-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:.6rem}.gl-grid figure{margin:0;padding:.4rem .5rem;border:1px solid var(--line2);border-radius:8px;background:var(--card)}"
            ".gl-grid figcaption{font-size:.8rem;color:var(--fg2)}.gl .ax{font-size:10px;fill:var(--fg3)}</style>")


JS = ("<script>(function(){var b=document.querySelectorAll('.gl-key button');b.forEach(function(x){x.addEventListener('click',function(){"
      "var g=x.getAttribute('data-g'),on=document.body.getAttribute('data-exp')===g;if(on||g==='all'){document.body.removeAttribute('data-exp')}else{document.body.setAttribute('data-exp',g)}"
      "b.forEach(function(y){y.setAttribute('aria-pressed',(!on&&y.getAttribute('data-g')===g&&g!=='all')?'true':'false')})})})})();</script>")


def legend(lang: str) -> str:
    k = 0 if lang == "ko" else 1
    btn = "".join(f"<button type='button' data-g='{g}' aria-pressed='false'><i class='g-{g}'></i>{esc(gl.GROUP_NAME[g][k])}</button>" for g in ORDER)
    btn += f"<button type='button' data-g='all' aria-pressed='false'>{'모두 접기' if k == 0 else 'Collapse all'}</button>"
    subs = "".join(f"<div class='gl-sub' data-g='{g}'>" + "".join(f"<span><i class='s-{sid}'></i>{esc(gl.SUB_INFO[sid][1 if k == 0 else 2])}</span>" for sid in SUBS[g]) + "</div>" for g in ORDER)
    return f"<div class='gl-key' role='group'>{btn}</div>{subs}"


def composer_svg(a: pd.DataFrame, comp: str, birth: int, death: int, lang: str) -> str:
    k = lang == "ko"
    w, h, m = 260, 120, 18
    bins = list(range(0, int(death - birth) + 1, 5))
    x0, x1 = 10, max(bins[-1] + 5, 45)
    sub = a[a.composer == comp]
    tot = sub.groupby("age_bin")["works"].sum()
    ymax = max(1, int(tot.max()) if len(tot) else 1)
    px = lambda v: m + (v - x0) / (x1 - x0) * (w - m - 4)  # noqa: E731
    bw = (w - m - 4) / ((x1 - x0) / 5) - 1.2
    out = [f"<line x1='{m}' y1='{h - 14}' x2='{w - 4}' y2='{h - 14}' stroke='var(--grid)'/>"]
    for ab in sorted(sub.age_bin.unique()):
        y = h - 14
        g = sub[sub.age_bin == ab]
        for grp in ORDER:
            for sid in SUBS[grp]:
                for basis in ("composition", "publication"):
                    n = int(g[(g.subgenre == sid) & (g.date_basis == basis)]["works"].sum())
                    if n == 0:
                        continue
                    hh = n / ymax * (h - 30)
                    y -= hh
                    tip = f"{NAME[comp][0 if k else 1]} {ab}~{ab + 4}{'세' if k else ''}: {gl.SUB_INFO[sid][1 if k else 2]} {n}{'면' if k else (' page' if n == 1 else ' pages')}" + ((" (출판 연도로 둔 작품)" if k else " (dated by publication)") if basis == "publication" else "")
                    out.append(f"<rect x='{px(ab):.1f}' y='{y:.1f}' width='{bw:.1f}' height='{hh:.1f}' class='g-{grp} s-{sid}'><title>{esc(tip)}</title></rect>")
                    if basis == "publication":
                        out.append(f"<rect x='{px(ab):.1f}' y='{y:.1f}' width='{bw:.1f}' height='{hh:.1f}' fill='url(#glhatch)' pointer-events='none'/>")
    for t in range(20, x1 + 1, 20):
        out.append(f"<text x='{px(t):.1f}' y='{h - 3}' text-anchor='middle' class='ax'>{t}</text>")
    out.append(f"<text x='{m - 2}' y='12' text-anchor='end' class='ax'>{ymax}</text>")
    return f"<svg class='gl' viewBox='0 0 {w} {h}' width='100%' role='img' aria-label='{esc(NAME[comp][0 if k else 1])}'>{''.join(out)}</svg>"


def era_heatmap(era: pd.DataFrame, lang: str, ramp_light: list[str]) -> str:
    k = lang == "ko"
    periods = sorted(era.period.unique())
    rows = [sid for g in ORDER for sid in SUBS[g]]
    x0, y0, cw, ch = 200, 40, (900 - 200) / len(periods), 18
    h = y0 + len(rows) * ch + 10
    piv = era.pivot_table(index="subgenre", columns="period", values="share_per_composer", aggfunc="first")
    pool = era.pivot_table(index="subgenre", columns="period", values="share_pooled", aggfunc="first")
    ncomp = era.groupby("period").n_composers.first()
    out = []
    for j, p in enumerate(periods):
        out.append(f"<text x='{x0 + j * cw + cw / 2:.1f}' y='{y0 - 22}' text-anchor='middle' class='km-lab'>{p}</text>"
                   f"<text x='{x0 + j * cw + cw / 2:.1f}' y='{y0 - 8}' text-anchor='middle' class='km-lab' style='font-size:9px'>n={int(ncomp[p])}</text>")
    edges = [0.025, 0.05, 0.10, 0.20, 0.35]  # fixed bins (%), six steps
    for i, sid in enumerate(rows):
        y = y0 + i * ch
        g = gl.SUB_INFO[sid][3]
        out.append(f"<rect x='{x0 - 14}' y='{y + 2}' width='8' height='{ch - 4}' style='fill:var(--gg-{g})'/>")
        out.append(f"<text x='{x0 - 18}' y='{y + 13}' text-anchor='end' class='km-lab'>{esc(gl.SUB_INFO[sid][1 if k else 2])}</text>")
        for j, p in enumerate(periods):
            v = piv.loc[sid, p] if (sid in piv.index and p in piv.columns) else np.nan
            if pd.isna(v) or v <= 0:
                continue
            step = int(np.searchsorted(edges, v, side='right'))
            dim = " opacity='.45'" if ncomp[p] < 3 else ""
            pv = pool.loc[sid, p] if (sid in pool.index and p in pool.columns) else 0
            tip = f"{p}–{p + 24} · {gl.SUB_INFO[sid][1 if k else 2]}: {v * 100:.1f}% ({'작곡가 평균' if k else 'mean over composers'}; {'작품면 합산' if k else 'pooled'} {pv * 100:.1f}%)"
            out.append(f"<rect x='{x0 + j * cw + 1:.1f}' y='{y + 1}' width='{cw - 2:.1f}' height='{ch - 2}' rx='2' class='yb{step + 1}'{dim}><title>{esc(tip)}</title></rect>")
            if v >= 0.05:
                out.append(f"<text x='{x0 + j * cw + cw / 2:.1f}' y='{y + 13}' text-anchor='middle' class='km-lab' style='font-size:9px' pointer-events='none'>{v * 100:.0f}</text>")
    leg = "".join(f"<rect x='{x0 + i * 70}' y='{h + 4}' width='60' height='12' rx='2' class='yb{i + 1}'/><text x='{x0 + i * 70 + 30}' y='{h + 30}' text-anchor='middle' class='km-lab'>{lab}</text>" for i, lab in enumerate(['<2.5%', '2.5–5', '5–10', '10–20', '20–35', '35%+']))
    return f"<svg class='pm' viewBox='0 0 900 {h + 40}' width='100%' role='img' aria-label='{'시대 × 세부 장르' if k else 'Period by sub-genre'}'>{''.join(out)}{leg}</svg>"


def render(lang, table_html):
    import colour_19 as col19
    import piecemap_pages as pmp
    k = lang == "ko"
    W = pd.read_csv(D / "genre_life_works.csv", low_memory=False)
    A = pd.read_csv(D / "genre_life_age.csv")
    E = pd.read_csv(D / "genre_life_era.csv")
    comps = W.groupby("composer").birth.first().sort_values().index.tolist()
    life = W.groupby("composer")[["birth", "death"]].first()
    basis = W.groupby("composer").date_basis.value_counts(normalize=True).unstack(fill_value=0)
    b = [col19.css() + pmp.css() + css(),
         "<svg width='0' height='0' style='position:absolute'><defs><pattern id='glhatch' width='5' height='5' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'><line x1='0' y1='0' x2='0' y2='5' stroke='var(--card)' stroke-opacity='.8' stroke-width='1.4'/></pattern></defs></svg>",
         f"<h1>{'작곡가와 장르' if k else 'Composers and genres'}</h1><p class='lead'>"
         + (f"작곡가 {len(comps)}명이 생애의 어느 때에 어떤 장르를 썼는가. IMSLP 작품면 {len(W):,}개를 큰 갈래 여섯(그 밖에 「기타」)과 세부 장르 {sum(len(v) for v in SUBS.values()) - 1}개로 나눴다." if k else
            f"What {len(comps)} composers wrote, and when in their lives. {len(W):,} IMSLP work pages in six big groups (plus 'other') and {sum(len(v) for v in SUBS.values()) - 1} sub-genres.") + "</p>"]
    # 1. forest + trees
    b.append(("<h2>1. 생애의 장르 흐름</h2><p>작곡가마다 가로는 나이(5년 단위), 세로는 그 나이에 쓴 작품면 수다. 세로 눈금은 작곡가마다 다르다(왼쪽 위 숫자가 최댓값). 처음에는 큰 갈래 여섯 색만 보인다. 범례의 갈래를 누르면 그 갈래가 세부 장르로 펼쳐지고 나머지는 회색으로 접힌다. 빗금은 작곡 연도가 없어 생전 출판 연도로 둔 작품이다. 막대에 마우스를 올리면 장르와 작품면 수가 나온다.</p>"
              if k else "<h2>1. Genres across a life</h2><p>For each composer, age in 5-year steps across, work pages written at that age up. Each composer has their own vertical scale (the number at the top left is the maximum). At first only the six big groups are coloured; click a group in the legend to expand it into its sub-genres while the others fold into grey. Hatching marks works without a composition year, placed at a first publication within the composer's life. Hover over a bar for the genre and count.</p>")
             + legend(lang))
    figs = []
    for c in comps:
        bd, dd = int(life.loc[c, "birth"]), int(life.loc[c, "death"])
        none = float(basis.loc[c].get("none", 0))
        pub = float(basis.loc[c].get("publication", 0))
        n = int((W.composer == c).sum())
        warn = (f" ⚠ {'연도 없음' if k else 'undated'} {none * 100:.0f}%" if none > WARN_NONE else "")
        cap = (f"{NAME[c][0 if k else 1]} ({bd}{'?' if c == 'Purcell, Henry' else ''}–{dd}) · {n:,}{'면' if k else ' pages'}" + (f" · {'출판 연도' if k else 'publication'} {pub * 100:.0f}%" if pub >= 0.05 else "") + warn)
        figs.append(f"<figure>{composer_svg(A, c, bd, dd, lang)}<figcaption>{esc(cap)}</figcaption></figure>")
    b.append("<div class='gl-grid'>" + "".join(figs) + "</div>")
    # 2. era heatmap
    b.append(("<h2>2. 시대와 세부 장르</h2><p>25년 구간마다, 그 구간에 작품면이 있는 작곡가 각자의 세부 장르 비율을 낸 뒤 평균했다(작곡가 한 사람이 한 표, n은 그 구간의 작곡가 수). 작품면이 많은 작곡가(텔레만 1,431면, 바흐 1,246면)가 구간을 차지하지 않게 하려는 것이다. 칸 안 숫자는 %(5% 이상만), 마우스를 올리면 작품면을 모두 합친 비율도 나온다. 왼쪽 색 띠가 큰 갈래다. 작곡가가 세 명 미만인 구간(흐린 칸)은 한두 사람의 비율이다.</p>"
              if k else "<h2>2. Period and sub-genre</h2><p>For each 25-year period, each composer with work pages in it gets their own sub-genre shares, and these are averaged (one vote per composer; n is the number of composers). This keeps prolific composers (Telemann 1,431 pages, Bach 1,246) from taking over a period. Numbers are % (5% and over only); hover for the pooled share over all work pages. The colour strip on the left is the big group. Periods with fewer than three composers (faded cells) are one or two people's shares.</p>")
             + era_heatmap(E, lang, pmp.YEAR_RAMPS["light"]))
    # 3. coverage and duration
    rows = []
    for c in comps:
        g = W[W.composer == c]
        r = dict(name=NAME[c][0 if k else 1], n=len(g), comp=basis.loc[c].get("composition", 0), pub=basis.loc[c].get("publication", 0),
                 none=basis.loc[c].get("none", 0), dur=g.duration_min.notna().mean())
        for grp in ("orchestral", "secular", "sacred"):
            r[f"p_{grp}"] = (g.group == grp).mean()
            gd = g.dropna(subset=["duration_min"])
            r[f"m_{grp}"] = gd[gd.group == grp].duration_min.sum() / gd.duration_min.sum() if gd.duration_min.sum() > 0 else np.nan
        rows.append(r)
    tb = pd.DataFrame(rows)
    nm = lambda g: gl.GROUP_NAME[g][0 if k else 1]  # noqa: E731
    b.append(("<h2>3. 연도 근거와 연주 시간</h2><p>IMSLP는 가곡 한 곡도 교향곡 하나도 작품면 하나다. 그래서 작품면 수로 세면 짧은 곡을 많이 쓴 작곡가에서 성악·소품의 비중이 커진다. 연주 시간이 적힌 작품면(오른쪽 「연주 시간 있음」)만으로 시간 비중을 따로 냈다. 두 비중이 크게 다르면 세는 단위가 그림을 바꾸고 있다는 뜻이다.</p>"
              if k else "<h2>3. Dating and duration</h2><p>On IMSLP a single song and a whole symphony are one work page each, so counting pages inflates the share of vocal music and short pieces for composers who wrote many of them. Shares by duration use only pages that give a duration ('with duration'). Where the two shares differ much, the counting unit is changing the picture.</p>")
             + table_html(tb, [("name", "작곡가" if k else "Composer", None), ("n", "작품면" if k else "pages", "d"),
                               ("comp", "작곡 연도" if k else "composition yr", ".0%"), ("pub", "출판 연도" if k else "publication yr", ".0%"), ("none", "연도 없음" if k else "undated", ".0%"),
                               ("dur", "연주 시간 있음" if k else "with duration", ".0%"),
                               ("p_orchestral", f"{nm('orchestral')} ({'작품면' if k else 'pages'})", ".0%"), ("m_orchestral", f"{nm('orchestral')} ({'시간' if k else 'time'})", ".0%"),
                               ("p_secular", f"{nm('secular')} ({'작품면' if k else 'pages'})", ".0%"), ("m_secular", f"{nm('secular')} ({'시간' if k else 'time'})", ".0%"),
                               ("p_sacred", f"{nm('sacred')} ({'작품면' if k else 'pages'})", ".0%"), ("m_sacred", f"{nm('sacred')} ({'시간' if k else 'time'})", ".0%")], "gl_tbl", lang, filt=False))
    # 4. method and limits
    other = (W.subgenre.isin(["other"])).mean()
    V = pd.read_csv(D / "genre_life_validation.csv")
    V = V.assign(g=V.group_rules == V.group_blind, s=V.subgenre_rules == V.subgenre_blind)
    rng = np.random.default_rng(1911)

    def agree(x):  # agreement and a bootstrap 95% interval
        x = np.asarray(x)
        lo, hi = np.percentile([x[rng.integers(0, len(x), len(x))].mean() for _ in range(2000)], [2.5, 97.5])
        return dict(n=len(x), a=x.mean() * 100, lo=lo * 100, hi=hi * 100)

    SEC = ["song", "secular_cantata", "secular_choral"]
    acc, sec = {}, {}
    for part in [V[V["round"] <= 4]] + [V[V["round"] == r] for r in sorted(set(V["round"])) if r > 4]:  # rounds added later are drawn after the earlier ones, so the published intervals stay as they were
        acc.update({r: dict(big=agree(g.g), sub=agree(g.s)) for r, g in part[part.stratum == "main"].groupby("round")})  # the main sample: 40 pages per big group
        sec.update({(r, sg): agree(g.s) for (r, sg), g in part[(part.group_rules == "secular") & (part["round"] >= 3)].groupby(["round", "subgenre_rules"])})  # main + extra
    v2 = V[V["round"] == 2]
    weak2 = v2[v2.subgenre_rules == "secular_choral"].s  # the weakest sub-genre of round 2 with ten pages or more
    c4 = V[(V["round"] == 4) & (V.subgenre_rules == "secular_cantata") & ~V.s]
    c4_sacred = int((c4.subgenre_blind == "sacred_cantata").sum())
    tg = W.tags.fillna("")
    n_other = int((W.group == "other").sum())
    r6c = None  # set below
    d7 = V[(V["round"] == 7) & ~V.s]
    d7_sacred = int(((d7.group_rules == "secular") & (d7.group_blind == "sacred")).sum())  # sacred by text, secular by tag
    d7_opera = int(((d7.subgenre_rules == "secular_cantata") & (d7.subgenre_blind == "opera")).sum())  # arias written for insertion into operas
    cell = lambda d: f"{d['a']:.1f}% ({d['lo']:.1f}{'~' if k else '–'}{d['hi']:.1f})"  # noqa: E731
    scell = lambda d: f"{d['a']:.1f}% ({d['lo']:.1f}{'~' if k else '–'}{d['hi']:.1f}; {d['n']})"  # noqa: E731
    rules_lab = {1: ("1.11 초안", "1.11 draft"), 2: ("1.11", "1.11"), 3: ("1.12.1 첫 수정", "1.12.1, first revision"), 4: ("1.12.1", "1.12.1"),
                 5: ("1.12.2", "1.12.2"), 6: ("1.12.3 첫 수정", "1.12.3, first revision"), 7: ("1.12.3 (지금의 분류)", "1.12.3 (the present classification)")}
    vrows = "".join(
        f"<tr><td>{r}</td><td>{rules_lab[r][0 if k else 1]}</td><td class='num'>{int((V['round'] == r).sum())}</td><td class='num'>{cell(acc[r]['big'])}</td><td class='num'>{cell(acc[r]['sub'])}</td>"
        + "".join(f"<td class='num'>{scell(sec[(r, sg)]) if (r, sg) in sec else '—'}</td>" for sg in SEC) + "</tr>" for r in sorted(acc))
    vhead = ("<tr><th>회차</th><th>잰 규칙</th><th class='num'>표본</th><th class='num'>큰 갈래</th><th class='num'>세부 장르</th>" if k else
             "<tr><th>Round</th><th>Rules measured</th><th class='num'>Sample</th><th class='num'>Big groups</th><th class='num'>Sub-genres</th>") \
        + "".join(f"<th class='num'>{gl.SUB_INFO[sg][1 if k else 2]}</th>" for sg in SEC) + "</tr>"
    vtab = f"<div class='wrap'><table><thead>{vhead}</thead><tbody>{vrows}</tbody></table></div>"
    choral_ko, choral_en = gl.SUB_INFO["secular_choral"][1], gl.SUB_INFO["secular_choral"][2]
    cant_ko, cant_en = gl.SUB_INFO["secular_cantata"][1], gl.SUB_INFO["secular_cantata"][2]
    ens_ko, ens_en = gl.SUB_INFO["ensemble"][1], gl.SUB_INFO["ensemble"][2]
    r3c = sec[(3, "secular_choral")]
    r6c = sec[(6, "secular_cantata")]
    val_ko = ("<li><b>분류 정확도.</b> 독립 검토자(Codex)가 우리 분류를 보지 않고 같은 체계로 작품면을 다시 분류했고, 그 답이 규칙의 분류와 같은 비율(일치율)을 쟀다. "
              "계산 전에 정한 기준은 큰 갈래 95%, 세부 장르 85%이고, 1.12.1에서 세속 성악의 세부 장르 셋에도 각각 85%를 두었다. 일곱 번 쟀다. 회차마다 앞 회차에 쓴 면을 빼고 새로 뽑았고, 규칙은 표본을 뽑기 전에 고쳤다."
              + vtab +
              "<p style='font-size:.9rem'>큰 갈래·세부 장르는 큰 갈래마다 40면씩 뽑은 주 표본 240면의 일치율이다. 오른쪽 세 칸은 규칙이 그 세부 장르로 분류한 면(주 표본과, 세속 성악에서 세부 장르마다 40면씩 더 뽑은 보강 표본) 가운데 검토자가 같은 답을 낸 비율이다. 괄호 안은 95% 구간(부트스트랩)이고 세미콜론 뒤는 면 수다.</p>"
              "<p><b>1.11(1·2차).</b> 1차에서 규칙의 체계적 결함 다섯 가지(트리오 소나타, 서곡-모음곡, 합창이 붙은 가곡, 오르간 판정, 소나티나)를 고쳤다. "
              f"2차에서 가장 낮은 세부 장르는 「합창곡·마드리갈 등」({len(weak2)}면 중 {weak2.mean() * 100:.0f}%)이었다. 독창 노래가 합창 쪽으로 가거나 종교 가사의 칸티클이 세속으로 간 경우였다.</p>"
              f"<p><b>1.12.1(3·4차).</b> 세속 성악을 다시 나눴다. 목소리가 하나인 곡은 반주에 따라 가곡이나 아리아로, 성부가 둘 이상이면 「{choral_ko}」으로, 칸타타·세레나타·오드는 합창 표지보다 먼저 「{cant_ko}」로 보냈다. 종교 표지(칸티클, 아베 마리아 등)를 더했고, 악기를 가리키는 bass·tenor 표기를 목소리로 읽던 것을 바로잡았다. "
              f"3차에서 「{choral_ko}」이 {r3c['n']}면 중 {r3c['a']:.1f}%로 기준에 못 미쳤다. 어긋난 면을 따라가 보니 큰 갈래의 결함이 둘 있었다. "
              "태그가 operas가 아닌 무대 작품(lyric dramas, dramma giocoso 등 34면, 베르디의 오페라 13면 포함)이 세속 성악에 있었고, 성악 장르 이름이 붙었지만 편성은 건반뿐인 51면(무언가, 오르간 코랄 등)이 성악에 있었다. "
              "이 둘을 고친 분류를 4차로 쟀다. 3차 값은 고치기 전의 측정값이다.</p>"
              "<p><b>1.12.2(5차).</b> 4차의 불일치에서 본 결함을 고쳤다. 원칙은 태그의 편성 표기가 장르 이름보다 앞선다는 것이다. "
              "편성이 건반뿐이면 장르 이름이 협주곡·서곡이어도 건반으로 보냈다(49면. 바흐의 건반 독주 협주곡, 텔레만의 건반 서곡 등). "
              f"<code>2vn bc</code>처럼 숫자가 붙은 편성 코드를 읽지 못해 「기타」에 있던 트리오 소나타 등을 실내악으로 보냈다(「기타」 247면 → {n_other}면). "
              "현악 합주와 관악 합주는 관현악으로, 기계 악기(플루트 시계, 뮤직 박스)는 기타로, 목소리가 없는 무대 모음곡(「호두까기 인형」 모음곡 등 5면)은 관현악으로 보냈다. 태그가 없는 면은 제목의 Concerto와 Requiem만 읽는다. 이 분류를 5차로 쟀다.</p>"
              "<p><b>1.12.3(6·7차).</b> 5차의 불일치에서 본 결함을 고쳤다. 편성이 현악 4중주(바이올린 둘·비올라·첼로)이면 이름이 달라도 현악 4중주로 보냈다(22면). "
              "이름은 협주곡인데 태그의 편성이 아홉 성부 이하(통주저음은 실제로 여럿이 맡아도 한 성부로 센다)이고 관현악·현악 합주 표기가 없으면 실내악으로 보냈다(텔레만의 4성부 협주곡, 비발디의 실내 협주곡 등 56면). 텔레만 작품 번호 TWV 1(교회 칸타타)의 면은 태그와 관계없이 종교 칸타타로(18면), 통주저음·건반 반주의 독창 아리아는 가곡으로(9면) 보냈다. "
              "태그가 secular oratorios·secular hymns인 29면은 이름의 oratorios·hymns 때문에 종교 성악에 있었는데, 세속 성악으로 옮겼다. "
              f"6차에서 「{cant_ko}」가 {r6c['n']}면 중 {r6c['a']:.1f}%로 기준에 못 미쳤다. 어긋난 7면 중 5면이 이 세부 장르로 보낸 세속 오라토리오였다. 분류 체계에 세속 오라토리오의 자리가 없어 검토자의 답이 갈렸다. "
              f"그래서 「{cant_ko}」의 뜻에 세속 오라토리오를 적어 넣고(지시문 한 줄), 6차에서 본 작은 결함 14면(편성 설명의 낱말을 잘못 읽어 관현악에 있던 하이든의 노투르노 5면 등)을 고친 뒤 7차로 다시 쟀다. 7차가 지금 분류의 측정값이고, 6차 값은 고치기 전의 측정값이다. "
              "다만 세속 오라토리오 16면 가운데 7면은 5·6차 표본에 이미 쓰여서 7차 표본에는 1면만 들었다. 7차는 그 자리를 고친 효과를 거의 재지 못한다.</p>"
              f"<p><b>남은 한계.</b> 규칙은 IMSLP 태그를 따른다. 4차에서 「{cant_ko}」의 불일치 {len(c4)}면 중 {c4_sacred}면은 태그가 secular cantatas인데 검토자가 가사와 용도를 보고 종교 칸타타로 판단한 작품이었다(바흐와 멘델스존). "
              f"7차의 불일치 {len(d7)}면 가운데 {d7_sacred}면은 태그가 세속(songs, arias, secular cantatas, carols 등)인데 검토자가 가사를 보고 종교 성악으로 판단한 곡이고, {d7_opera}면은 오페라에 넣으려고 쓴 아리아(태그는 arias)를 검토자가 무대 작품으로 본 경우다. 이런 곡은 태그 규칙으로 가릴 수 없다. "
              "브란덴부르크 협주곡 6번은 태그의 편성이 여섯 성부와 통주저음뿐이어서 규칙대로라면 실내악이지만 협주곡에 두었다. 새 바흐 전집은 여섯 곡을 모두 관현악 작품(제VII부 2권)에 넣고, 독일 국립도서관의 작품 전거도 이 곡을 협주곡·합주 협주곡으로 분류한다. 성부마다 한 사람이 연주하는 현악 실내악으로 보는 해설도 있다. "
              "합창이 붙은 무대 모음곡(「다프니스와 클로에」 모음곡 등)은 무대에 남아 있다. 분류 체계에 관악 합주와 기계 악기의 자리가 따로 없어 각각 관현악과 기타로 보냈다. "
              "3차부터의 지시문은 세속 세부 장르 셋의 경계(중창과 캐논은 합창 쪽, 관현악 반주의 독창 아리아는 칸타타 쪽)를 2차보다 분명하게 적었고, 7차의 지시문은 세속 오라토리오 한 줄이 더 있다. 그래서 세속 세부 장르의 값은 회차끼리 같은 조건의 비교가 아니다. 세부 장르별 표본은 수십 면이어서 구간이 넓다. "
              "일곱 차례의 검증표는 <a href='../data/genres/genre_life_validation.csv'>CSV</a>로 공개한다. 일치율은 검토자와 규칙이 같은 답을 낸 비율이지 정답률이 아니다.</p></li>")
    val_en = ("<li><b>Classification accuracy.</b> An independent reviewer (Codex) reclassified work pages blind under the same scheme, and agreement is the share of pages where the reviewer's answer equals the rules'. "
              "The thresholds fixed beforehand were 95% for big groups and 85% for sub-genres; 1.12.1 added 85% for each of the three secular vocal sub-genres. There were seven rounds. Each drew a fresh sample that left out the pages of earlier rounds, and the rules were revised before the sample was drawn."
              + vtab +
              "<p style='font-size:.9rem'>Big groups and sub-genres: agreement on the main sample of 240 pages, 40 from each big group. The three columns on the right: among pages the rules put in that sub-genre (the main sample plus 40 extra pages per secular sub-genre), the share where the reviewer gave the same answer. In brackets, the bootstrap 95% interval and, after the semicolon, the number of pages.</p>"
              "<p><b>1.11 (rounds 1 and 2).</b> The first round led to fixes for five systematic faults (trio sonatas, overture-suites, songs with chorus, organ, sonatinas). "
              f"In the second round the weakest sub-genre was 'Choral pieces, madrigals etc.' ({weak2.mean() * 100:.0f}% of {len(weak2)} pages): solo songs went to choral, and canticles with sacred texts went to secular.</p>"
              f"<p><b>1.12.1 (rounds 3 and 4).</b> Secular vocal music was divided anew. A piece for one voice is a song or an aria depending on its accompaniment; two or more voice parts go to '{choral_en}'; cantatas, serenatas and odes go to '{cant_en}' before any chorus marker is read. Sacred markers were added (canticles, Ave Maria and others), and 'bass' and 'tenor' naming instruments are no longer read as voices. "
              f"In the third round '{choral_en}' fell short at {r3c['a']:.1f}% of {r3c['n']} pages. Following the disagreements turned up two faults in the big groups: "
              "stage works tagged other than 'operas' (lyric dramas, dramma giocoso and others; 34 pages, 13 of them Verdi operas) sat in secular vocal, and 51 pages with a vocal genre name but a keyboard-only scoring (songs without words, organ chorales) sat in vocal. "
              "The fourth round measured the classification with these two fixed; the third-round figures are from before the fix.</p>"
              "<p><b>1.12.2 (round 5).</b> The faults seen in the fourth round's disagreements were fixed, on one principle: the scoring in the tags comes before the genre name. "
              "A keyboard-only scoring makes a keyboard work even when the name is concerto or overture (49 pages: Bach's concertos for solo keyboard, Telemann's keyboard overtures and others). "
              f"Scoring codes with a number in front, such as <code>2vn bc</code>, were not being read, which had left trio sonatas and the like in 'Other'; they are now chamber music ('Other' goes from 247 pages to {n_other}). "
              "String orchestra and wind band go to orchestral, mechanical instruments (flute clocks, music boxes) to other, and suites without voices drawn from stage works (the Nutcracker suite and four more) to orchestral. For pages without tags, only 'Concerto' and 'Requiem' are read from the title. The fifth round measured this classification.</p>"
              "<p><b>1.12.3 (rounds 6 and 7).</b> The faults seen in the fifth round's disagreements were fixed. A work scored for string quartet (two violins, viola, cello) is a string quartet whatever its name (22 pages). "
              "A work named concerto whose tags give nine parts or fewer (continuo counts as one part, however many play it) and no orchestra or string ensemble is chamber music (56 pages: Telemann's concertos in four parts, Vivaldi's chamber concertos and others). Pages with the Telemann catalogue number TWV 1 (church cantatas) are sacred cantatas whatever their tags (18 pages), and arias for one voice with continuo or keyboard are songs (9 pages). "
              "The 29 pages tagged 'secular oratorios' or 'secular hymns' had been in sacred vocal because of the words 'oratorios' and 'hymns'; they moved to secular vocal. "
              f"In the sixth round '{cant_en}' fell short at {r6c['a']:.1f}% of {r6c['n']} pages. Five of the seven disagreements were secular oratorios, which the revision had sent to this sub-genre: the scheme had no place for them, and the reviewer's answers went different ways. "
              f"So secular oratorios were written into the meaning of '{cant_en}' (one line of the instructions), 14 pages with small faults seen in the sixth round were fixed (among them five Haydn notturni that sat in orchestral because a word in the instrumentation was misread), and a seventh round measured the result. The seventh round measures the present classification; the sixth-round figures are from before the fix. "
              "Of the 16 secular oratorios, however, 7 had already been used in rounds five and six, and only one fell into the seventh sample, so the seventh round says almost nothing about the effect of that change.</p>"
              f"<p><b>What remains.</b> The rules follow the IMSLP tags. In the fourth round, {c4_sacred} of the {len(c4)} disagreements in '{cant_en}' were works tagged 'secular cantatas' that the reviewer judged sacred from their texts and occasions (Bach and Mendelssohn). "
              f"Of the {len(d7)} disagreements in the seventh round, {d7_sacred} are works with secular tags (songs, arias, secular cantatas, carols and others) that the reviewer judged sacred from their texts, and {d7_opera} are arias written for insertion into operas (tagged 'arias') that the reviewer placed under stage. Tag rules cannot tell these apart. "
              "Brandenburg Concerto No. 6 is scored in its tags for six parts and continuo, which the rule would send to chamber music, but it is kept as a concerto: the Neue Bach-Ausgabe puts all six Brandenburg Concertos among the orchestral works (Series VII, vol. 2), and the German National Library's work record classes it as a concerto and a concerto grosso. Some writers describe it as string chamber music with one player to a part. "
              "Suites with chorus drawn from stage works (the Daphnis et Chloé suites and others) remain under stage. The scheme has no place of its own for wind band or mechanical instruments, which went to orchestral and other. "
              "From round three on, the instructions spelled out the borders of the three secular sub-genres more clearly than in round two (vocal ensembles and canons with choral; solo arias with orchestra with cantatas), and round seven added the line on secular oratorios, so the secular sub-genre figures are not like-for-like comparisons across rounds. With a few dozen pages per sub-genre the intervals are wide. "
              "All seven rounds are published as a <a href='../data/genres/genre_life_validation.csv'>CSV</a>. Agreement is the share where the reviewer and the rules gave the same answer, not a rate of correct answers.</p></li>")
    b.append(("<h2>4. 분류 방법과 한계</h2><ul>"
              "<li>큰 갈래는 1.2 「작품·역사」 면의 분류(IMSLP 장르 태그와 편성)를 그대로 쓰고, 성악만 종교·세속으로 나눴다. 세부 장르는 태그 규칙으로 정했다(규칙은 <code>genre_life_111.py</code>의 SUB). 각 갈래의 마지막 세부 장르(「… 등」)는 앞의 규칙에 걸리지 않은 작품이다. "
              f"어느 갈래에도 들지 않은 「기타」는 {other * 100:.1f}%다.</li>"
              "" + val_ko + "<li>작품면은 작품 목록 전체가 아니다. IMSLP에 면이 없는 작품, 편곡·다른 작곡가 이름의 면은 빠진다. 20세기 작곡가는 저작권 때문에 늦은 작품의 면이 적을 수 있으나, 빠진 작품의 수와 이유는 이 자료로 확인할 수 없다.</li>"
              "<li>작곡 연도가 없고 생전 출판 연도가 있는 작품은 출판 연도에 두었다(빗금). 출판 연도는 「그때까지는 작곡되었다」는 상한일 뿐이다(연 단위로만 생전 여부를 가렸다). 쓸 수 있는 작곡 연도도 생전 출판 연도도 없는 작품(「…까지」 같은 경계 연도만 있는 작품 포함)이 30%를 넘는 작곡가에는 ⚠를 달았다.</li>"
              "<li>색: 큰 갈래 여섯은 검증된 범주 색이고, 쌓는 순서를 범례 순서와 같게 고정해 맞닿는 색끼리 색각 이상 모의에서 구별되게 했다. 세부 장르는 같은 색상 안의 명도 단계다. 위계를 색으로 드러낸다는 Tennekes·de Jonge(2014)의 취지를 빌렸으나, 원 방법(형제 범주마다 색상을 나눔)과 달리 여기서는 같은 색상에서 명도만 바꾼 변형이다. 한 화면에 보이는 색은 갈래를 펼쳐도 그 갈래의 단계와 회색뿐이다.</li></ul>"
              if k else "<h2>4. Method and limits</h2><ul>"
              "<li>Big groups use the classification of the 1.2 'Works & history' page (IMSLP genre tags and instrumentation), with vocal split into sacred and secular. Sub-genres come from tag rules (SUB in <code>genre_life_111.py</code>); the last sub-genre of each group ('… etc.') holds works the earlier rules did not catch. "
              f"'Other', outside every group, is {other * 100:.1f}%.</li>"
              "" + val_en + "<li>Work pages are not complete work lists: works without an IMSLP page, arrangements and pages titled for other composers are missing. Twentieth-century composers may have fewer pages for late works because of copyright, but how many works are missing, and why, cannot be checked from these data.</li>"
              "<li>Works with no composition year but a first publication within the composer's life are placed at that year (hatched). A publication year only bounds the composition from above (whether it fell within the composer's life is checked by year only). Composers with more than 30% of works having neither a usable composition year nor a publication within their life (works with only a bound such as 'before 1720' included) are marked ⚠.</li>"
              "<li>Colour: the six big groups use validated categorical colours, stacked in legend order so that touching colours stay apart under colour-vision-deficiency simulation. Sub-genres are lightness steps within the same hue. This borrows the aim of Tennekes & de Jonge (2014), showing a hierarchy through colour, but varies their method (which gives sibling categories different hues) by changing lightness only. Expanding a group shows only its steps and grey.</li></ul>"))
    b.append("<p class='src'>" + ("자료·출처: " if k else "Data and sources: ")
             + "IMSLP work pages (CC BY-SA 4.0; derived tables carry the same licence); Wikidata (birth and death years); "
             "Shneiderman, B. (1996), 'The eyes have it: a task by data type taxonomy for information visualizations', <i>IEEE Symposium on Visual Languages</i>; "
             "Tennekes, M. & de Jonge, E. (2014), 'Tree Colors: color schemes for tree-structured data', <i>IEEE TVCG</i> 20(12): 2072–2081. "
             + (" 표의 데이터: <a href='../data/genres/genre_life_works.csv'>작품면별</a>·<a href='../data/genres/genre_life_age.csv'>나이별</a>·<a href='../data/genres/genre_life_era.csv'>시대별</a> CSV."
                if k else " Data: <a href='../data/genres/genre_life_works.csv'>by work page</a>, <a href='../data/genres/genre_life_age.csv'>by age</a>, <a href='../data/genres/genre_life_era.csv'>by period</a> (CSV).") + "</p>")
    b.append(JS)
    return "".join(b)


def build(lang, path, page_fn, table_html):
    k = lang == "ko"
    title = "작곡가와 장르" if k else "Composers and genres"
    desc = "작곡가 30명의 생애에 걸친 장르 흐름" if k else "Genres across the lives of 30 composers"
    path.write_text(page_fn(lang, title, render(lang, table_html), desc=desc, active="genres"), encoding="utf-8")
