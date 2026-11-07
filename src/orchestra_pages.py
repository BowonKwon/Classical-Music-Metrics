"""Orchestra repertoire comparison page (1.5): orchestras.html in each language.

Site build: build_site.py calls build(lang, path, page_fn); it reads only committed derived tables
(data/derived/orch_*.csv, orch_seoul_vs_nyphil_summary.json). The Seoul x NY Phil numbers are computed
from the raw archives by proto_orchestras.py, which also writes an unpublished draft of this page.
No ranking and no composite score: comparison tables only.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from build_site import KO_NAME  # noqa: E402
from history_pages import GCSS, ticks  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D, ALI = ROOT / "data/derived", ROOT / "data/aliases"

# published tables (copied to site/data/orch/ and listed on the data page)
ORCH_FILES = ["orch_touring_profiles.csv", "orch_check_nyphil_two_sources.csv", "orch_overlap_nyphil_gewandhaus.csv",
              "orch_seoul_vs_nyphil.csv", "seoulphil_works.csv"]
ORCH_ALIAS_FILES = ["orch_composer_xwalk.csv", "orch_composer_manual.csv", "seoulphil_title_manual.csv"]

ORCH = {  # key in orch_touring_profiles.csv -> (ko, en)
    "NY Phil (home seasons)": ("뉴욕 필하모닉(홈 시즌)", "New York Philharmonic (home seasons)"),
    "Boston SO": ("보스턴 심포니 오케스트라", "Boston Symphony Orchestra"),
    "Philadelphia": ("필라델피아 오케스트라", "Philadelphia Orchestra"),
    "Cleveland": ("클리블랜드 오케스트라", "Cleveland Orchestra"),
    "Chicago SO": ("시카고 심포니 오케스트라", "Chicago Symphony Orchestra"),
    "Vienna Phil": ("빈 필하모닉", "Vienna Philharmonic"),
    "Berlin Phil": ("베를린 필하모닉", "Berlin Philharmonic"),
    "Concertgebouw": ("로열 콘세르트헤바우 오케스트라", "Royal Concertgebouw Orchestra"),
    "LSO": ("런던 심포니 오케스트라", "London Symphony Orchestra"),
    "Gewandhaus (NY tours)": ("라이프치히 게반트하우스 오케스트라", "Leipzig Gewandhaus Orchestra"),
    "Seoul Phil (NY tours)": ("서울시립교향악단", "Seoul Philharmonic Orchestra"),
}

T = {
    "ko": {
        "title": "악단 레퍼토리 비교",
        "draft": " — 시안",
        "brand": "서양 고전 음악 메트릭스 · 시안",
        "lead": "공개된 공연 기록이 있는 악단들의 레퍼토리를 같은 단위로 맞춰 견준다. 순위는 매기지 않는다.",
        "proto": "공개 전 시안이다. 수치는 블라인드 검증 전이며 바뀔 수 있다.",
        "show": "표 보기",
        "rows": "행",
    },
    "en": {
        "title": "Orchestra repertoire compared",
        "draft": " — draft",
        "brand": "Classical Music Metrics · draft",
        "lead": "Repertoire of orchestras with public performance records, counted in the same unit and set side by side. No ranking.",
        "proto": "Unpublished draft. Figures have not yet been checked blind and may change.",
        "show": "Show table",
        "rows": "rows",
    },
}


def esc(s):
    return html.escape("" if s is None else str(s))


def load_ko_names() -> dict:
    names = dict(KO_NAME)
    p = ALI / "composer_ko_labels_wikidata.csv"
    if p.exists():
        for r in pd.read_csv(p, dtype=str, keep_default_na=False).itertuples(index=False):
            names.setdefault(r.composer, r.ko_alt or r.ko_label)
    return names


KO = load_ko_names()
# NY Phil canonical forms without diacritics in the bracket slot
EN_FIX = {"Dvorak, Antonín": "Antonín Dvořák", "Smetana, Bedrich": "Bedřich Smetana", "Janacek [Janácek], Leoš": "Leoš Janáček"}


def name(c: str, lang: str) -> str:
    if not isinstance(c, str):
        return ""
    if lang == "ko" and KO.get(c):  # an empty Wikidata label falls through to the Latin form (Codex B18)
        return KO[c]
    if lang == "en" and c in EN_FIX:
        return EN_FIX[c]
    # 'Bartok [Bartók], Béla' -> 'Béla Bartók'; 'Strauss, Johann, II' -> 'Johann Strauss II'
    parts = [p.strip() for p in c.split(",")]
    sur = re.sub(r"^.*\[(.+)\]$", r"\1", parts[0])
    given = re.sub(r"\s*\[.*\]", "", parts[1]) if len(parts) > 1 else ""
    tail = " " + parts[2] if len(parts) > 2 else ""
    return f"{given} {sur}{tail}".strip()


def table(df: pd.DataFrame, cols, tid: str, lang: str) -> str:
    h = "".join(f"<th class='{'num' if f else ''}'>{esc(n)}</th>" for _, n, f in cols)
    rows = []
    for _, r in df.iterrows():
        cells = []
        for c, _, f in cols:
            v = r[c]
            if f:
                cells.append(f"<td class='num' data-v='{v}'>{format(v, f) if pd.notna(v) else ''}</td>")
            else:
                cells.append(f"<td>{esc(v)}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (f"<details><summary style='cursor:pointer;color:var(--fg2);font-size:.9rem;margin:.3rem 0'>{T[lang]['show']} ({len(rows)}{' ' if lang == 'en' else ''}{T[lang]['rows']})</summary>"
            f"<div class='wrap'><table class='sort' id='{tid}'><thead><tr>{h}</tr></thead><tbody>{''.join(rows)}</tbody></table></div></details>")


def svg_interval(items, lo_x, hi_x, width=900, row_h=30, label_w=300, xlabel="", legend=("", "")) -> str:
    """items: (label, observed_lo, observed_hi, base_lo, base_hi). A grey bar = size-matched NY Phil range;
    a dot (or a dark bar when observed is itself a range) = this orchestra."""
    L, R, top = label_w, 16, 8
    pw = width - L - R
    height = top + row_h * len(items) + 30
    X = lambda v: L + (v - lo_x) / (hi_x - lo_x) * pw  # noqa: E731
    o = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for v in ticks(lo_x, hi_x, 6):
        o.append(f'<line class="grid" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top}" y2="{height - 24}"/><text x="{X(v):.1f}" y="{height - 8}" text-anchor="middle">{v:.0%}</text>')
    for i, (lab, olo, ohi, blo, bhi) in enumerate(items):
        y = top + i * row_h + row_h / 2
        o.append(f'<text x="{L - 8}" y="{y + 4:.1f}" text-anchor="end">{esc(lab)}</text>')
        o.append(f'<rect x="{X(blo):.1f}" y="{y - 6:.1f}" width="{max(X(bhi) - X(blo), 2):.1f}" height="12" rx="3" fill="var(--g6)" fill-opacity=".55"><title>{esc(legend[0])}: {blo:.1%}–{bhi:.1%}</title></rect>')
        if abs(ohi - olo) < 1e-9:
            o.append(f'<circle cx="{X(olo):.1f}" cy="{y:.1f}" r="5" fill="var(--g1)"><title>{esc(lab)}: {olo:.1%}</title></circle>')
        else:
            o.append(f'<rect x="{X(olo):.1f}" y="{y - 3:.1f}" width="{X(ohi) - X(olo):.1f}" height="6" rx="3" fill="var(--g1)"><title>{esc(legend[1])}: {olo:.1%}–{ohi:.1%}</title></rect>')
    if xlabel:
        o.append(f'<text x="{L + pw / 2:.1f}" y="{height}" text-anchor="middle" style="fill:var(--fg3)"></text>')
    o.append("</svg>")
    return "".join(o)


def svg_pairs(rows, width=900, row_h=24, label_w=200, lab=("", "")) -> str:
    """rows: (label, a, b) shares; two thin bars per row (a = Seoul, b = NY Phil)."""
    L, R, top = label_w, 50, 6
    pw = width - L - R
    mx = max(max(a, b) for _, a, b in rows) * 1.08
    height = top + row_h * len(rows) + 26
    X = lambda v: L + v / mx * pw  # noqa: E731
    o = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for v in ticks(0, mx, 5):
        o.append(f'<line class="grid" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top}" y2="{height - 22}"/><text x="{X(v):.1f}" y="{height - 6}" text-anchor="middle">{v:.0%}</text>')
    for i, (name_, a, b) in enumerate(rows):
        y = top + i * row_h
        o.append(f'<text x="{L - 8}" y="{y + row_h / 2 + 4:.1f}" text-anchor="end">{esc(name_)}</text>')
        o.append(f'<rect x="{L}" y="{y + 3:.1f}" width="{X(a) - L:.1f}" height="8" rx="2" fill="var(--g1)"><title>{esc(lab[0])} {a:.1%}</title></rect>')
        o.append(f'<rect x="{L}" y="{y + 12:.1f}" width="{X(b) - L:.1f}" height="8" rx="2" fill="var(--g2)"><title>{esc(lab[1])} {b:.1%}</title></rect>')
    o.append("</svg>")
    return "".join(o)


def dline(pts, xlo, xhi, lang, width=900, height=200) -> str:
    """Decade line (cosine 0-1). Tooltips name the decade (proto_work_activity.small_line labels 5-year bins)."""
    L, R, T_, B = 40, 36, 8, 22
    pw, ph = width - L - R, height - T_ - B
    X = lambda v: L + (v - xlo) / (xhi - xlo) * pw  # noqa: E731
    Y = lambda v: T_ + ph - v * ph  # noqa: E731
    dec = (lambda a: f"{a}년대") if lang == "ko" else (lambda a: f"{a}s")
    o = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for v in (0, .25, .5, .75, 1):
        o.append(f'<line class="grid" x1="{L}" x2="{width - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text x="{L - 4}" y="{Y(v) + 4:.1f}" text-anchor="end">{v:.2f}</text>')
    for a, _ in pts:
        o.append(f'<text x="{X(a):.1f}" y="{height - 5}" text-anchor="middle">{dec(a)}</text>')
    o.append('<path d="' + " ".join(f"{'M' if i == 0 else 'L'}{X(a):.1f},{Y(b):.1f}" for i, (a, b) in enumerate(pts)) + '" fill="none" stroke="var(--g1)" stroke-width="2" stroke-linejoin="round"/>')
    for a, b in pts:
        o.append(f'<circle cx="{X(a):.1f}" cy="{Y(b):.1f}" r="4" fill="var(--g1)"><title>{dec(a)}: {b:.3f}</title></circle>')
    o.append("</svg>")
    return "".join(o)



def render(lang: str, tour: pd.DataFrame, check: pd.DataFrame, gw: pd.DataFrame, sv: pd.DataFrame, s: dict, draft: bool = False) -> str:
    """Page body (no html/head). draft=True adds the unpublished-draft banner."""
    k = lang == "ko"
    oname = lambda o: ORCH.get(o, (o, o))[0 if k else 1]  # noqa: E731
    title = T[lang]["title"] + (T[lang]["draft"] if draft else "")
    b = [f"<style>{GCSS}</style><div class='hero'><h1>{title}</h1><p class='lead'>{T[lang]['lead']}</p></div>"]
    if draft:
        b.append(f"<div class='proto'>{T[lang]['proto']}</div>")

    # 1 why no ranking
    if k:
        b.append("<h2>1. 순위를 매기지 않는 이유</h2>"
                 "<p>합성 점수는 가중치를 어떻게 주느냐가 곧 결과가 되는데, 그 가중치를 정당화할 외부 기준이 없다. 공개된 공연 기록도 미국 대형 악단과 서울시향에 몰려 있다. 빈 필·베를린 필·콘세르트헤바우는 누리집에서 공연 기록을 검색할 수 있게 해 두었지만, 전체를 내려받을 수 있는 공개 데이터나 API는 찾지 못했다. 그래서 이 면에서는 그 악단들이 카네기홀에서 한 공연만 보인다.</p>"
                 "<p>평론가 투표로 순위를 낸 사례는 있다(Gramophone 2008, Bachtrack 2015·2023). 그러나 Bachtrack 투표는 평론가 16명(2015)·15명(2023)의 판단이다. 이 면은 순위 대신 지표마다 따로 비교 표를 둔다.</p>")
    else:
        b.append("<h2>1. Why there is no ranking</h2>"
                 "<p>A composite score is only as good as its weights, and there is no outside standard to justify them. Public performance records are also concentrated in large US orchestras and the Seoul Philharmonic. The Vienna and Berlin Philharmonics and the Concertgebouw have searchable concert archives on their websites, but we found no public bulk download or API for the full record, so on this page they appear only through their Carnegie Hall concerts.</p>"
                 "<p>Critics' polls exist (Gramophone 2008, Bachtrack 2015 and 2023), but the Bachtrack polls reflect the views of 16 (2015) and 15 (2023) critics. This page sets out one comparison table per measure instead.</p>")

    # 2 sources
    src = [
        ("뉴욕 필하모닉 공연 기록" if k else "New York Philharmonic Performance History", "1842–2026", "CC0",
         "공연 × 작품(U1)" if k else "concert × work (U1)"),
        ("카네기홀 공연 기록(SPARQL)" if k else "Carnegie Hall performance history (SPARQL)", "1891–2026", "CC0",
         "카네기홀 공연 × 작품, 출연 악단별" if k else "Carnegie Hall concert × work, by performing orchestra"),
        ("게반트하우스 연주회 프로그램(Hartmann-Enke, Zenodo 5995965)" if k else "Gewandhaus concert programmes (Hartmann-Enke, Zenodo 5995965)", "1781–1895", "CC BY 4.0",
         "연주회 × 작품" if k else "concert × work"),
        ("서울시립교향악단 공연 정보(서울 열린데이터광장 OA-22909·22910)" if k else "Seoul Philharmonic concerts (Seoul Open Data OA-22909, OA-22910)", "2009–2027", "KOGL 1" if not k else "공공누리 제1유형",
         "공연 × 곡목 문자열 → 작품으로 나눔" if k else "concert × programme string, split into works"),
    ]
    hd = ("자료", "기간", "이용 조건", "세는 단위") if k else ("Source", "Years", "Licence", "Unit")
    b.append(f"<h2>2. {'자료' if k else 'Sources'}</h2><div class='wrap'><table><thead><tr>" + "".join(f"<th>{h}</th>" for h in hd) + "</tr></thead><tbody>"
             + "".join("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in r) + "</tr>" for r in src) + "</tbody></table></div>")
    b.append("<p>" + ("서울시향 자료의 곡목 칸에는 대개 곡명만 있고 작곡가가 없다(일부 행에만 작곡가 이름이 섞여 있다). 곡명으로 작곡가를 붙이는 방법은 6절에 있다. 생몰년은 Wikidata(CC0)에서 가져왔다."
                     if k else "The Seoul Philharmonic programme field mostly gives titles only, without composers (a few rows include a composer's name). Section 6 explains how composers were attached by title. Birth and death years are from Wikidata (CC0).") + "</p>")

    # 3 two-source check
    ck = check.sort_values("period")
    pts = [(int(r.period), float(r.cosine)) for r in ck.itertuples()]
    home, post = ck[ck.period <= 1960].cosine, ck[ck.period >= 1970].cosine
    hr, pr = f"{home.min():.2f}~{home.max():.2f}", f"{post.min():.2f}~{post.max():.2f}"
    if k:
        b.append(f"<h2>3. 카네기홀 기록은 믿을 만한가</h2><p>같은 악단을 두 출처에서 잰 결과를 견줬다. 뉴욕 필의 자체 기록과 카네기홀 기록에서 각각 작곡가 점유율을 구하고, 두 분포가 얼마나 닮았는지를 코사인 유사도(1이면 같은 분포)로 쟀다. 뉴욕 필이 카네기홀을 본거지로 쓰던 시기(1892~1962년)에 해당하는 1890~1960년대에는 {hr}로 거의 같다. 1962년 링컨 센터로 옮긴 뒤로는 카네기홀 출연이 특별 공연 몇 건으로 줄어 {pr}로 떨어진다. 따라서 이 면의 카네기홀 수치는 <b>그 악단이 카네기홀에서 한 공연</b>에 대한 것이다.</p>")
    else:
        b.append(f"<h2>3. Can the Carnegie Hall records be trusted?</h2><p>We measured the same orchestra from two sources. Composer shares for the New York Philharmonic were computed from its own archive and from the Carnegie Hall records, and compared by cosine similarity (1 means identical distributions). In the 1890s–1960s, covering the years Carnegie Hall was the orchestra's home (1892–1962), the two agree closely ({hr.replace('~', '–')}). After the move to Lincoln Center in 1962 its Carnegie appearances shrink to a few special concerts and the similarity falls to {pr.replace('~', '–')}. Carnegie figures on this page therefore describe <b>what an orchestra played at Carnegie Hall</b>.</p>")
    b.append(f"<figure>{dline(pts, 1890, 2020, lang)}</figure>")
    b.append(table(ck.assign(period=ck.period.astype(str) + ("s" if not k else "년대")), [("period", "10년" if k else "decade", None), ("cosine", "코사인" if k else "cosine", ".3f"), ("top20_jaccard", "상위 20명 자카드" if k else "top-20 Jaccard", ".2f"), ("shared_composers", "공통 작곡가" if k else "shared composers", ".0f")], "ck", lang))

    # 4 touring
    if k:
        b.append("<h2>4. 카네기홀 투어 프로그램의 쏠림</h2><p>상위 10명 작곡가가 연주 작품에서 차지하는 비율이다. 이 비율은 표본이 작을수록 기계적으로 커진다. 그래서 뉴욕 필 홈 시즌에서 같은 수의 작품을 500번 무작위로 뽑아 얻은 범위(회색 막대, 95%)와 견준다. 파란 점이 회색 막대 오른쪽에 있으면 크기를 맞춘 뒤에도 프로그램이 상위 작곡가에 더 몰려 있다는 뜻이다.</p>")
    else:
        b.append("<h2>4. How narrow are touring programmes at Carnegie Hall?</h2><p>The share of performed works by the ten most-played composers. This share rises mechanically as samples get smaller, so each orchestra is set against the range obtained by drawing the same number of works 500 times from New York Philharmonic home seasons (grey bar, 95%). A blue dot to the right of the grey bar means the programmes lean towards the top composers even after matching sample size.</p>")
    leg = ("뉴욕 필 같은 크기 기준" if k else "NY Phil size-matched range", "")
    for win in ("1955-1989", "1990-2026"):
        tw = tour[(tour.window == win) & (tour.orchestra != "NY Phil (home seasons)")]
        items = [(f"{oname(r.orchestra)} ({int(r.concerts)})", r.top10_share, r.top10_share, r.base_top10_lo, r.base_top10_hi) for r in tw.itertuples()]
        b.append(f"<h3>{win.replace('-', '–')} <small style='color:var(--fg3);font-weight:400'>{'괄호는 공연 수' if k else 'concerts in brackets'}</small></h3><figure>{svg_interval(items, 0.2, 1.0, legend=leg)}</figure>")
    tt = tour.copy()
    tt["orch"] = tt.orchestra.map(oname)
    tt["top3"] = tt.top3.map(lambda s: "; ".join(f"{name(x.rsplit(' ', 1)[0], lang)} {x.rsplit(' ', 1)[1]}" for x in str(s).split("; ")))
    b.append(table(tt, [("window", "기간" if k else "period", None), ("orch", "악단" if k else "orchestra", None), ("concerts", "공연" if k else "concerts", ".0f"),
                        ("work_performances", "작품 연주" if k else "work performances", ".0f"), ("distinct_composers", "작곡가 수" if k else "composers", ".0f"),
                        ("top10_share", "상위 10명" if k else "top 10", ".1%"), ("base_top10_lo", "기준 하한" if k else "baseline low", ".1%"), ("base_top10_hi", "기준 상한" if k else "baseline high", ".1%"),
                        ("living_share", "생존 작곡가" if k else "living composers", ".1%"), ("cosine_to_nyphil_home", "뉴욕 필과 코사인" if k else "cosine to NY Phil", ".2f"), ("top3", "상위 3명" if k else "top 3", None)], "tt", lang))
    vis = tour[tour.orchestra != "NY Phil (home seasons)"]
    above = vis.top10_share > vis.base_top10_hi + 1e-12
    inside = vis[~above]
    n_in = ", ".join(f"{oname(r.orchestra)} {r.window.replace('-', '–')}" for r in inside.itertuples())
    if k:
        b.append(f"<p>표본 {len(vis)}개 가운데 {int(above.sum())}개가 기준 범위 위에 있다. 범위 안에 든 것은 {n_in or '없음'}이다. 서울시향은 공연 2회·작곡가 10명이라 상위 10명 점유율이 정의상 100%가 된다. 그래서 이 지표로는 판정할 수 없다. "
                 "이 결과는 투어 프로그램의 성격을 보여 줄 뿐이고 악단 자체의 성격을 말해 주지 않는다. 악단은 투어에 대표 레퍼토리를 들고 온다.</p>")
    else:
        b.append(f"<p>{int(above.sum())} of {len(vis)} samples sit above the range; inside it: {n_in or 'none'}. The Seoul Philharmonic sample has 2 concerts and 10 composers, so its top-10 share is 100% by definition and says nothing. "
                 "This describes touring programmes, not the orchestras themselves: orchestras bring their calling-card repertoire on tour.</p>")

    # 5 Gewandhaus
    g = gw.sort_values("period")
    gp = [(int(r.period), float(r.cosine)) for r in g.itertuples()]
    if k:
        b.append("<h2>5. 19세기 라이프치히와 뉴욕</h2><p>게반트하우스 연주회 프로그램(1781–1895)과 뉴욕 필 기록이 겹치는 1840~1890년대를 10년마다 견줬다. 두 악단의 작곡가 점유율 코사인은 1850년대 0.92에서 1890년대 0.67로 내려간다(게반트하우스 자료는 1895년 3월 28일 연주회에서 끝나므로 1890년대는 1890년~1895년 3월이다). 이 자료로는 원인을 가릴 수 없다. 이름을 맞추는 표에 민감한 수치라서, 첫 시안에서 동명이인을 잘못 맞췄을 때는 1840년대 값이 0.71이었다.</p>")
    else:
        b.append("<h2>5. Leipzig and New York in the nineteenth century</h2><p>The Gewandhaus programmes (1781–1895) and the New York Philharmonic records overlap from the 1840s to the 1890s and are compared decade by decade. The cosine between their composer shares falls from 0.92 in the 1850s to 0.67 in the 1890s (the Gewandhaus data end with the concert of 28 March 1895, so the 1890s cover 1890 to March 1895). These data cannot say why. The figure is sensitive to the name-matching table: in the first draft, before namesakes were separated, the 1840s value was 0.71.</p>")
    b.append(f"<figure>{dline(gp, 1840, 1890, lang, height=190)}</figure>")
    b.append(table(g.assign(period=g.period.astype(str) + ("s" if not k else "년대")), [("period", "10년" if k else "decade", None), ("cosine", "코사인" if k else "cosine", ".3f"), ("top20_jaccard", "상위 20명 자카드" if k else "top-20 Jaccard", ".2f"), ("shared_composers", "공통 작곡가" if k else "shared composers", ".0f")], "gw", lang))

    # 6 Seoul
    lo95, hi95 = s["nyphil_top10_rarefied_95"]
    gap = s["seoul_top10_lo"] - hi95
    ex = s["nyphil_excluded_by_flag"]
    exs = sum(ex.values())
    uc = s["seoul_unattributed_classes"]
    if k:
        b.append(f"<h2>6. 서울시향과 뉴욕 필 — 정기공연 2009–2025년</h2><p>두 악단의 정기공연을 연주 날짜 기준으로 같은 기간(2009~2025년)에 맞췄다. 뉴욕 필은 시즌이 9월에 시작하므로 시즌 단위가 아니라 프로그램의 첫 연주일로 거렀다. 서울시향 {s['seoul_titles']:,}곡 가운데 {s['seoul_attributed']:,}곡({s['seoul_coverage']:.1%})에 작곡가를 붙였다. "
                 f"뉴욕 필은 정기 시즌 작품 연주 {s['nyphil_sub_u1']:,}건이다. 작곡가 이름이 아닌 항목(전승곡·국가·미상·작품 아님)과 두 사람 이상이 함께 적힌 표기(예: 「Perlmutter / Wohl」)는 {exs}건이라 뺐다.</p>")
    else:
        b.append(f"<h2>6. Seoul and New York — subscription concerts 2009–2025</h2><p>Both orchestras' subscription concerts are matched by concert date (2009–2025). New York seasons start in September, so its programmes are selected by first concert date rather than by season. Of {s['seoul_titles']:,} Seoul Philharmonic works, {s['seoul_attributed']:,} ({s['seoul_coverage']:.1%}) have an attributed composer. "
                 f"The New York Philharmonic has {s['nyphil_sub_u1']:,} subscription work performances; {exs} entries that do not name a single composer (traditional, anthems, unknown, non-works, and joint credits such as \"Perlmutter / Wohl\") are left out.</p>")
    rows = [
        ("작곡가 점유율 코사인" if k else "cosine of composer shares", f"{s['cosine']:.3f}", "—"),
        ("상위 10명 점유율" if k else "top-10 share", f"{s['seoul_top10_lo']:.1%}–{s['seoul_top10_max']:.1%} ({'작곡가를 붙인 곡만' if k else 'attributed only'} {s['seoul_top10_attributed_only']:.1%})", f"{s['nyphil_top10_rarefied_mean']:.1%} ({lo95:.1%}–{hi95:.1%})"),
        ("생존 작곡가 비율" if k else "living composers", f"{s['seoul_living_lo']:.1%}–{s['seoul_living_hi']:.1%}", f"{s['nyphil_living']:.1%}"),
    ]
    hd = ("지표", "서울시향", "뉴욕 필") if k else ("Measure", "Seoul Phil", "NY Phil")
    b.append("<div class='wrap'><table><thead><tr>" + "".join(f"<th>{h}</th>" for h in hd) + "</tr></thead><tbody>" + "".join("<tr>" + "".join(f"<td>{esc(x)}</td>" for x in r) + "</tr>" for r in rows) + "</tbody></table></div>")
    if k:
        b.append(f"<p>서울시향 값이 범위로 나오는 것은 작곡가를 모르는 곡이 있어서다. 상위 10명 점유율의 하한은 미귀속 {s['seoul_unattributed']}곡이 모두 상위 10명 밖이라고 본 값이고, 상한은 모두 상위 10명의 곡이라고 본 값이다. 괄호 안 값은 작곡가를 붙인 곡만으로 나눈 비율이다. "
                 f"생존 작곡가 비율에서 「모르는 곡」은 미귀속 {s['seoul_unattributed']}곡에 생몰년을 확인하지 못한 작곡가의 곡 {s['seoul_undated_attributed']}곡을 더한 것이다. 뉴욕 필 상위 10명 값은 서울시향과 같은 곡 수를 500번 뽑은 평균과 95% 범위다(난수 시드 {s['seed']}).</p>"
                 f"<ul><li><b>레퍼토리는 많이 닮았다.</b> 코사인 {s['cosine']:.2f}.</li>"
                 f"<li><b>서울시향이 상위 작곡가에 더 몰려 있다.</b> 서울시향 하한 {s['seoul_top10_lo']:.1%}가 뉴욕 필 범위의 상한 {hi95:.1%}보다 높다. 미귀속 곡이 어떻게 갈리든 이 순서는 바뀌지 않는다. 다만 차이가 {gap * 100:.1f}%포인트라 귀속 오류에 민감하다.</li>"
                 f"<li><b>취소·변경 공연을 빼도 같다.</b> 서울시향 공연 정보에는 취소되거나 프로그램이 바뀐 공연이 섞여 있다. 2020년 정기공연 정보는 63건으로, 2015~2025년의 다른 해(37~52건)보다 많다. 2020·2021년을 빼면 서울시향 하한 {s['excl_2020_21']['seoul_top10_lo']:.1%}, 뉴욕 필 범위 상한 {s['excl_2020_21']['nyphil_top10_hi']:.1%}로 차이가 오히려 커진다.</li>"
                 "<li><b>생존 작곡가 비율은 판정하지 않는다.</b> 서울시향 범위가 넓고 뉴욕 필 값을 품는다.</li></ul>"
                 f"<p>미귀속 {s['seoul_unattributed']}곡을 곡명으로 대강 나누면, 「Violin Concerto」처럼 장르·번호만 있는 곡이 {uc.get('generic', 0)}곡, 초연·위촉 표시가 있는 곡이 {uc.get('premiere', 0)}곡, 나머지 {uc.get('other', 0)}곡이다. 나머지에는 한국 작곡가의 곡과 작곡가를 확인하지 못한 현대곡이 많다.</p>")
    else:
        b.append(f"<p>Seoul values are ranges because some works have unknown composers. The low end of the top-10 share assumes all {s['seoul_unattributed']} unattributed works fall outside the top ten; the high end assumes they all belong to the top ten. The bracketed value divides by attributed works only. "
                 f"For living composers, the unknowns are the {s['seoul_unattributed']} unattributed works plus {s['seoul_undated_attributed']} works by composers without known dates. The NY Phil top-10 value is the mean and 95% range of 500 draws of the same number of works (random seed {s['seed']}).</p>"
                 f"<ul><li><b>The repertoire is very similar.</b> Cosine {s['cosine']:.2f}.</li>"
                 f"<li><b>Seoul leans more on its top composers.</b> Seoul's low end, {s['seoul_top10_lo']:.1%}, is above the top of the NY range, {hi95:.1%}, so the order holds however the unattributed works fall. The gap is {gap * 100:.1f} percentage points, so it is sensitive to attribution errors.</li>"
                 f"<li><b>Cancelled and changed concerts do not change this.</b> The Seoul data include concerts that were cancelled or whose programme changed. There are 63 subscription entries for 2020, against 37 to 52 in the other years from 2015 to 2025. Without 2020 and 2021, Seoul's low end is {s['excl_2020_21']['seoul_top10_lo']:.1%} and the top of the NY range {s['excl_2020_21']['nyphil_top10_hi']:.1%}, so the gap widens.</li>"
                 "<li><b>No verdict on living composers.</b> Seoul's range is wide and contains the NY value.</li></ul>"
                 f"<p>Sorted roughly by title, the {s['seoul_unattributed']} unattributed works are {uc.get('generic', 0)} bare genre titles such as \"Violin Concerto\", {uc.get('premiere', 0)} marked as premieres or commissions, and {uc.get('other', 0)} others, many of them by Korean composers or contemporary pieces whose composer we could not establish.</p>")
    top = sv.head(15)
    lab = ("서울시향", "뉴욕 필") if k else ("Seoul Phil", "NY Phil")
    b.append(f"<h3>{'서울시향 상위 15명' if k else 'Seoul Philharmonic top 15'}</h3><div class='legend'><span style='--c:var(--g1)'>{lab[0]}</span><span style='--c:var(--g2)'>{lab[1]}</span></div>"
             f"<figure>{svg_pairs([(name(r.composer, lang), r.seoul_share, r.nyphil_sub_share) for r in top.itertuples()], lab=lab)}</figure>")
    sx = sv.set_index("composer")
    sh_ = lambda c, col: float(sx.at[c, col]) if c in sx.index else 0.0  # noqa: E731
    bs, bn = sh_("Beethoven, Ludwig van", "seoul_share"), sh_("Beethoven, Ludwig van", "nyphil_sub_share")
    js, jn = sh_("Bach, Johann Sebastian", "seoul_share"), sh_("Bach, Johann Sebastian", "nyphil_sub_share")
    diff = (sx.seoul_share - sx.nyphil_sub_share)
    big = diff.abs().idxmax()
    big_ko = f"가장 큰 차이는 {name(big, lang)}에서 난다(서울시향 {sh_(big, 'seoul_share'):.1%}, 뉴욕 필 {sh_(big, 'nyphil_sub_share'):.1%})."
    big_en = f"The largest gap is {name(big, lang)} (Seoul {sh_(big, 'seoul_share'):.1%}, NY {sh_(big, 'nyphil_sub_share'):.1%})."
    b.append("<p>" + (f"{big_ko} 반대쪽으로는 바흐가 서울시향 {js:.1%}, 뉴욕 필 {jn:.1%}다. 서울시향 점유율은 작곡가를 붙인 곡만으로 나눈 값이다."
                      if k else f"{big_en} In the other direction, Bach is {js:.1%} in Seoul and {jn:.1%} in New York. Seoul shares are out of attributed works only.") + "</p>")
    svt = sv[sv.seoul_titles > 0].assign(cn=lambda d: d.composer.map(lambda c: name(c, lang)))
    b.append(table(svt, [("cn", "작곡가" if k else "composer", None), ("seoul_titles", "서울시향 곡 수" if k else "Seoul works", ".0f"), ("seoul_share", "서울시향" if k else "Seoul", ".1%"), ("nyphil_sub_share", "뉴욕 필" if k else "NY Phil", ".1%")], "sv", lang))
    meth = s["by_method"]
    mlab = {"exact": ("카네기홀 곡명과 완전 일치", "exact match to a Carnegie Hall title"), "manual": ("수동표", "hand-made table"),
            "feature": ("장르·번호·작품번호·조성 일치", "genre, number, opus and key match"), "catalog": ("작품목록 번호(BWV·K. 등)", "catalogue number (BWV, K., etc.)"),
            "none": ("작곡가를 붙이지 못함", "not attributed")}
    if k:
        b.append("<h3>작곡가를 붙인 방법</h3><p>곡목 문자열을 작품 단위로 나눈 뒤 다음 순서로 작곡가를 붙였다. 작품목록 번호(BWV·K.·D. 등)를 먼저 보고, 카네기홀 곡명과 완전히 같은지 본다. 그다음 장르·번호·작품번호·조성이 같은 참조 곡명이 한 작곡가로 모이는지 본다. 곡명에 고유어가 있으면 참조 곡명에도 그 고유어가 있어야 하고, 조성이 적혀 있으면 조성도 같아야 한다. 규칙으로 정해지지 않으면 손으로 만든 표를 쓴다. 「Violin Concerto」처럼 장르명뿐이거나 후보가 둘 이상인 곡에는 작곡가를 붙이지 않았다.</p>")
    else:
        b.append("<h3>How composers were attached</h3><p>Programme strings were split into works, then attributed in this order: a catalogue number (BWV, K., D. and so on); an exact match to a Carnegie Hall title; then reference titles sharing genre, number, opus and key, used only when they point to one composer. A title with its own distinctive words must share one with the reference titles, and a stated key must match. What the rules cannot settle goes to a hand-made table. Bare genre titles such as \"Violin Concerto\", and titles with more than one candidate composer, were left unattributed.</p>")
    b.append("<div class='wrap'><table><thead><tr><th>" + ("방법" if k else "Method") + "</th><th class='num'>" + ("곡 수" if k else "works") + "</th></tr></thead><tbody>"
             + "".join(f"<tr><td>{mlab[m][0 if k else 1]}</td><td class='num'>{meth.get(m, 0):,}</td></tr>" for m in ("catalog", "exact", "feature", "manual", "none")) + "</tbody></table></div>")

    # 7 limits
    if k:
        b.append("<h2>7. 한계</h2><ul>"
                 "<li>빈 필·베를린 필·콘세르트헤바우는 카네기홀 공연만 보인다. 홈 시즌 기록은 누리집에서 검색할 수 있으나 내려받을 수 있는 공개 데이터를 찾지 못했다.</li>"
                 "<li>서울시향의 작곡가 귀속은 곡명과 공연 정보에 기댄다. 미귀속 곡은 무작위가 아니다(6절). 공연 정보는 예정 프로그램이라 취소·변경된 공연이 섞여 있고, 공개 데이터에는 취소 표시가 없다. 뉴욕 필 기록은 실제 연주 기록이다.</li>"
                 "<li>카네기홀 작곡가는 Wikidata ID 없이 이름으로만 맞췄다. 동명이인은 수동표로 갈랐다.</li>"
                 "<li>편곡은 뉴욕 필 아카이브 관행을 따랐다. 단순 편곡은 원작곡가로, 편곡자의 작품 목록에 든 재구성(「풀치넬라」 등)은 편곡자로 셌다.</li>"
                 "<li>코사인과 상위 10명 점유율은 「무엇을 얼마나 자주 하나」만 잰다. 연주의 질이나 해석은 재지 않는다.</li></ul>")
    else:
        b.append("<h2>7. Limits</h2><ul>"
                 "<li>The Vienna and Berlin Philharmonics and the Concertgebouw appear only through their Carnegie Hall concerts; their home seasons can be searched on their websites, but we found no downloadable public data.</li>"
                 "<li>Seoul attributions rest on titles and concert pages. Unattributed works are not random (section 6). The Seoul data list planned programmes, including concerts later cancelled or changed, with no cancellation flag; the New York records are of concerts actually given.</li>"
                 "<li>Carnegie Hall composers were matched by name, without Wikidata IDs. Namesakes were separated by a hand-made table.</li>"
                 "<li>Arrangements follow New York Philharmonic archive practice: simple arrangements count for the original composer, recompositions in the arranger's own catalogue (Pulcinella and the like) for the arranger.</li>"
                 "<li>Cosine and top-10 share measure only what is played and how often, not how well.</li></ul>")
    b.append("<p class='src'>" + ("자료: " if k else "Data: ") +
             "<a href='https://github.com/nyphilarchive/PerformanceHistory'>New York Philharmonic Performance History</a> (CC0); "
             "<a href='https://data.carnegiehall.org/'>Carnegie Hall Data Lab</a> (CC0); "
             "<a href='https://doi.org/10.5281/zenodo.5995965'>Hartmann-Enke, Gewandhaus concert programmes</a> (CC BY 4.0); "
             "<a href='https://data.seoul.go.kr/'>" + ("서울 열린데이터광장" if k else "Seoul Open Data Plaza") + "</a> OA-22909, OA-22910 (" + ("공공누리 제1유형" if k else "KOGL Type 1") + "); "
             "<a href='https://www.wikidata.org/'>Wikidata</a> (CC0).</p>")
    return "".join(b)


def load() -> tuple:
    tour = pd.read_csv(D / "orch_touring_profiles.csv")
    check = pd.read_csv(D / "orch_check_nyphil_two_sources.csv")
    gw = pd.read_csv(D / "orch_overlap_nyphil_gewandhaus.csv")
    sv = pd.read_csv(D / "orch_seoul_vs_nyphil.csv")
    s = json.loads((D / "orch_seoul_vs_nyphil_summary.json").read_text(encoding="utf-8"))
    return tour, check, gw, sv, s


def build(lang: str, path: Path, page_fn) -> None:
    body = render(lang, *load())
    path.write_text(page_fn(lang, T[lang]["title"], body, desc=T[lang]["lead"], active="orchestras"), encoding="utf-8")
