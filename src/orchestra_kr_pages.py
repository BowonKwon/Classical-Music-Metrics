"""Section 7 of the orchestra page (1.19): Korean orchestras' own subscription programs.

Reads the tables written by orch_kr.py (data/derived/orch_kr_*.csv, orch_kr_summary.json). Every number in the
text is computed here from those tables. No ranking: measures side by side.
"""
from __future__ import annotations

import html
import json
from itertools import combinations
from pathlib import Path

import pandas as pd
import fig_notes  # noqa: E402  (1.22.3: chart notes)

from history_glance import josa

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/derived"
KR_FILES = ["orch_kr_works.csv", "orch_kr_concerts.csv", "orch_kr_coverage_by_year.csv", "orch_kr_summary.csv", "orch_kr_cosine.csv", "orch_kr_composer_shares.csv",
            "orch_kr_decades.csv", "orch_kr_decade_pairs.csv", "orch_kr_kinds.csv", "orch_kr_top_works.csv", "orch_kr_festival_works.csv", "orch_kr_festival_vs_home.csv", "orch_kr_skipped_concerts.csv"]
KR_ALIAS_FILES = ["orch_kr_composer_alias.csv", "orch_kr_not_composer.csv", "orch_kr_festival_manual.csv"]
COL = {"seoul": "var(--g1)", "suwon": "var(--g5)", "bucheon": "var(--g2)", "busan": "var(--g4)"}
ON = {"seoul": ("서울시향", "Seoul Phil"), "suwon": ("수원시향", "Suwon Phil"), "bucheon": ("부천필", "Bucheon Phil"), "busan": ("부산시향", "Busan Phil")}
FULL = {"seoul": ("서울시립교향악단", "Seoul Philharmonic Orchestra"), "suwon": ("수원시립교향악단", "Suwon Philharmonic Orchestra"),
        "bucheon": ("부천필하모닉오케스트라", "Bucheon Philharmonic Orchestra"), "busan": ("부산시립교향악단", "Busan Philharmonic Orchestra")}
ORDER = ["seoul", "suwon", "bucheon", "busan"]
LONG = ["suwon", "busan"]
BUSAN_URL = "https://www.bscc.or.kr/04_art/?mcode=0404011300&amp;mode=2&amp;no=10275&amp;page=1&amp;mgb=art"


def esc(s):
    return html.escape("" if s is None else str(s))


def load():
    g = lambda n: pd.read_csv(D / n, dtype={"home_same_year": str, "home_other_years": str, "home_same_year_canceled": str}, keep_default_na=False) if "festival_vs" in n else pd.read_csv(D / n)  # noqa: E731
    return {"cov": g("orch_kr_coverage_by_year.csv"), "summ": g("orch_kr_summary.csv").set_index("orch"), "cos": g("orch_kr_cosine.csv"),
            "sh": g("orch_kr_composer_shares.csv"), "dec": g("orch_kr_decades.csv"), "dp": g("orch_kr_decade_pairs.csv"), "kinds": g("orch_kr_kinds.csv"),
            "top": g("orch_kr_top_works.csv"), "fest": g("orch_kr_festival_vs_home.csv"), "works": pd.read_csv(D / "orch_kr_works.csv", dtype=str, keep_default_na=False),
            "conc": pd.read_csv(D / "orch_kr_concerts.csv", dtype=str, keep_default_na=False), "skip": pd.read_csv(D / "orch_kr_skipped_concerts.csv", dtype=str, keep_default_na=False),
            "man": pd.read_csv(ROOT / "data/aliases/orch_kr_festival_manual.csv", dtype=str, keep_default_na=False),
            "notname": pd.read_csv(ROOT / "data/aliases/orch_kr_not_composer.csv", dtype={"as_read": str, "class": str, "note": str}, keep_default_na=False), "j": json.loads((D / "orch_kr_summary.json").read_text(encoding="utf-8"))}


# ───────────── charts ─────────────
TTL = 'style="font-weight:600;font-size:12px;fill:var(--fg)"'


def svg_coverage(cov: pd.DataFrame, win, k: bool, y0=1962, y1=2026) -> str:
    """One panel per orchestra: subscription concerts listed per year (light bar) and those with a program found as text (dark bar)."""
    W, L, R, ph, gap, top = 900, 46, 14, 84, 38, 46
    n = len(ORDER)
    pw = W - L - R
    bw = pw / (y1 - y0 + 1)
    H = top + n * ph + (n - 1) * gap + 64
    X = lambda y: L + (y - y0) * bw  # noqa: E731
    o = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{"해마다 정기연주회 수와 곡목을 옮긴 공연 수" if k else "Subscription concerts per year and those from which works were read"}">']
    o.append(f'<text x="{L}" y="14" {TTL}>{"해마다 목록에 오른 정기연주회 수(옅은 막대)와 작곡가가 적힌 곡목을 옮긴 공연 수(짙은 막대)" if k else "Subscription concerts listed each year (light bars) and those from which works with a named composer were read (dark bars)"}</text>')
    for i, orch in enumerate(ORDER):
        g = cov[(cov.orch == orch) & (cov.kind == "정기") & cov.year.between(y0, y1)]
        ymax = max(int(g.concerts.max()), 1)
        step = 10 if ymax > 20 else 5
        ymax = (ymax // step + 1) * step
        py = top + i * (ph + gap)
        Y = lambda v: py + ph - v / ymax * ph  # noqa: E731
        o.append(f'<rect x="{X(win[0]):.1f}" y="{py}" width="{(win[1] - win[0] + 1) * bw:.1f}" height="{ph}" fill="var(--g6)" fill-opacity=".13"/>')
        for v in range(0, ymax + 1, step):
            o.append(f'<line class="grid" x1="{L}" x2="{W - R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}"/><text x="{L - 5}" y="{Y(v) + 4:.1f}" text-anchor="end">{v}</text>')
        o.append(f'<text x="{L + 4}" y="{py + 12}" style="font-weight:600;fill:var(--fg)">{esc(FULL[orch][0 if k else 1])}</text>')
        if i == 0:
            o.append(f'<text x="{X(win[0]) + (win[1] - win[0] + 1) * bw / 2:.1f}" y="{py - 6}" text-anchor="middle">{"비교 기간" if k else "comparison years"} {win[0]}–{win[1]}</text>')
        for r in g.itertuples():
            x = X(int(r.year)) + 1
            tip = (f"{int(r.year)}년: 정기연주회 {int(r.concerts)}회, 곡목을 옮긴 공연 {int(r.with_program)}회" if k
                   else f"{int(r.year)}: {int(r.concerts)} subscription concerts, works read from {int(r.with_program)}")
            o.append(f'<rect x="{x:.1f}" y="{Y(r.concerts):.1f}" width="{bw - 2:.1f}" height="{py + ph - Y(r.concerts):.1f}" fill="{COL[orch]}" fill-opacity=".28"><title>{tip}</title></rect>')
            if r.with_program > 0:
                o.append(f'<rect x="{x:.1f}" y="{Y(r.with_program):.1f}" width="{bw - 2:.1f}" height="{py + ph - Y(r.with_program):.1f}" fill="{COL[orch]}"><title>{tip}</title></rect>')
        for y in range(1965, y1 + 1, 5):
            o.append(f'<text x="{X(y) + bw / 2:.1f}" y="{py + ph + 13}" text-anchor="middle">{y}</text>')
    o.append(f'<text x="{L + pw / 2:.1f}" y="{H - 26}" text-anchor="middle">{"공연 연도 (가로) · 그 해 공연 수 (세로, 악단마다 눈금이 다르다)" if k else "Concert year (horizontal) · concerts in that year (vertical; each panel has its own scale)"}</text>')
    o.append(f'<text x="{L + pw / 2:.1f}" y="{H - 9}" text-anchor="middle">{"막대가 없는 해는 그 악단의 자료가 없는 해다" if k else "A year without a bar is a year with no data for that orchestra"}</text>')
    o.append("</svg>")
    return "".join(o)


def svg_intervals(rows, title: str, xlabel: str, label_w=250) -> str:
    """rows: (label, color, lo, hi, mean, tooltip). A light bar = middle 95% of the draws, a dot = their mean; a row with lo == hi is a single dot."""
    W, L, R, top, rh = 900, label_w, 60, 34, 30
    vals = [v for r in rows for v in (r[2], r[3])]
    lo, hi = max(0.0, int(min(vals) * 10 - 1) / 10), min(1.0, int(max(vals) * 10 + 2) / 10)
    pw = W - L - R
    H = top + rh * len(rows) + 44
    X = lambda v: L + (v - lo) / (hi - lo) * pw  # noqa: E731
    o = [f'<svg viewBox="0 0 {W} {H}" role="img">', f'<text x="{L}" y="14" {TTL}>{esc(title)}</text>']
    v = lo
    while v <= hi + 1e-9:
        o.append(f'<line class="grid" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top - 6}" y2="{top + rh * len(rows)}"/><text x="{X(v):.1f}" y="{top + rh * len(rows) + 14}" text-anchor="middle">{v:.0%}</text>')
        v += 0.1
    for i, (lab, color, a, b_, m, tip) in enumerate(rows):
        y = top + i * rh + rh / 2
        o.append(f'<text x="{L - 10}" y="{y + 4:.1f}" text-anchor="end" style="fill:var(--fg)">{esc(lab)}</text>')
        if b_ - a > 1e-9:
            o.append(f'<rect x="{X(a):.1f}" y="{y - 5:.1f}" width="{X(b_) - X(a):.1f}" height="10" rx="4" fill="{color}" fill-opacity=".35"><title>{esc(tip)}</title></rect>')
        o.append(f'<circle cx="{X(m):.1f}" cy="{y:.1f}" r="5.5" fill="{color}"><title>{esc(tip)}</title></circle>')
        o.append(f'<text x="{X(b_ if b_ - a > 1e-9 else m) + 10:.1f}" y="{y + 4:.1f}">{m:.1%}</text>')
    o.append(f'<text x="{L + pw / 2:.1f}" y="{H - 6}" text-anchor="middle">{esc(xlabel)}</text>')
    o.append("</svg>")
    return "".join(o)


def svg_bars(rows, title: str, xlabel: str, keys, colors, names) -> str:
    """rows: (label, {key: share}). One thin bar per key under each label."""
    W, L, R, top = 900, 190, 56, 30
    rh = 12 * len(keys) + 12
    mx = max(max(d.values()) for _, d in rows) * 1.1
    pw = W - L - R
    H = top + rh * len(rows) + 40
    X = lambda v: L + v / mx * pw  # noqa: E731
    o = [f'<svg viewBox="0 0 {W} {H}" role="img">', f'<text x="{L}" y="14" {TTL}>{esc(title)}</text>']
    step = 0.05 if mx > 0.12 else 0.02
    v = 0.0
    while v <= mx:
        o.append(f'<line class="grid" x1="{X(v):.1f}" x2="{X(v):.1f}" y1="{top - 4}" y2="{top + rh * len(rows)}"/><text x="{X(v):.1f}" y="{top + rh * len(rows) + 14}" text-anchor="middle">{v:.0%}</text>')
        v += step
    for i, (lab, d) in enumerate(rows):
        y = top + i * rh
        o.append(f'<text x="{L - 8}" y="{y + rh / 2 + 2:.1f}" text-anchor="end" style="fill:var(--fg)">{esc(lab)}</text>')
        for j, key in enumerate(keys):
            o.append(f'<rect x="{L}" y="{y + 4 + j * 12:.1f}" width="{max(X(d[key]) - L, 0.5):.1f}" height="9" rx="2" fill="{colors[key]}"><title>{esc(lab)} — {esc(names[key])} {d[key]:.1%}</title></rect>')
    o.append(f'<text x="{L + pw / 2:.1f}" y="{H - 6}" text-anchor="middle">{esc(xlabel)}</text>')
    o.append("</svg>")
    return "".join(o)


def glance(k: bool, what: str, seen: str, caution: str) -> str:
    h = ("한눈에 보기", "무엇을 보는 절인가", "무엇이 보이는가", "조심할 것") if k else ("At a glance", "What this section looks at", "What shows", "Watch for")
    return (f"<aside class='glance'><p class='glance-h'>{h[0]}</p><dl><dt>{h[1]}</dt><dd>{what}</dd><dt>{h[2]}</dt><dd>{seen}</dd><dt>{h[3]}</dt><dd>{caution}</dd></dl></aside>")


def simple_table(head, rows, num_from=1) -> str:
    th = "".join(f"<th{' class=num' if i >= num_from else ''}>{esc(h)}</th>" for i, h in enumerate(head))
    tr = "".join("<tr>" + "".join(f"<td{' class=num' if i >= num_from else ''}>{c}</td>" for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f"<div class='wrap'><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>"


def listing(items, k: bool) -> str:
    """'A, B and C' / 'A, B, C'."""
    items = list(items)
    if k or len(items) < 2:
        return ", ".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


# ───────────── section ─────────────
def section(lang: str, num: int, name, table) -> str:
    """name(composer, lang) and table(df, cols, id, lang) come from orchestra_pages."""
    k = lang == "ko"
    d = load()
    S, j, cov = d["summ"], d["j"], d["cov"]
    lo, hi = j["window"]
    n_r, dn = int(j["rarefied_n"]), int(j["decade_n"])
    tot = j["totals"]
    on = lambda o: ON[o][0 if k else 1]  # noqa: E731
    full = lambda o: FULL[o][0 if k else 1]  # noqa: E731
    pct = lambda v: f"{v:.1%}"  # noqa: E731
    ko_from_tables = {r.composer: r.composer_ko for r in d["works"][["composer", "composer_ko"]].drop_duplicates().itertuples() if r.composer and r.composer_ko}

    def cname(c):
        if isinstance(c, str) and c.startswith("ko:"):
            return c[3:]
        n_ = name(c, lang)
        if k and not any("가" <= ch <= "힣" for ch in n_) and ko_from_tables.get(c):
            return ko_from_tables[c]
        return n_

    cs = {(r.a, r.b): r.cosine for r in d["cos"].itertuples()}
    seoul_ny = json.loads((D / "orch_seoul_vs_nyphil_summary.json").read_text(encoding="utf-8"))["cosine"]
    kinds = d["kinds"].set_index(["orch", "kind"])
    all_beet = all(S.at[o, "top_composer"] == "Beethoven, Ludwig van" for o in ORDER)
    small = S.works_with_composer.idxmin()
    others = [o for o in ORDER if o != small]
    by_mean = sorted(ORDER, key=lambda o: -S.at[o, "rarefied_top10_mean"])
    hi_pair, lo_pair = max(cs, key=cs.get), min(cs, key=cs.get)
    rngs = {o: (S.at[o, "rarefied_top10_lo"], S.at[o, "rarefied_top10_hi"]) for o in ORDER}
    b = []

    # heading and glance
    b.append(f"<h2 id='kr'>{num}. " + ("국내 교향악단의 정기연주회 프로그램 — 서울 · 수원 · 부천 · 부산" if k else "Korean orchestras' own subscription programs — Seoul, Suwon, Bucheon and Busan") + "</h2>")
    seen_ko = (f"곡 수를 {n_r}곡으로 맞추면 상위 10명 작곡가의 비율이 " + ", ".join(f"{on(o)} {pct(S.at[o, 'rarefied_top10_mean'])}" for o in by_mean) + "다. "
               f"작곡가 분포가 가장 닮은 짝은 {josa(on(hi_pair[0]), '과와')} {on(hi_pair[1])}(코사인 {cs[hi_pair]:.2f})이다. " + ("네 악단 모두 가장 많이 실린 작곡가는 베토벤이다." if all_beet else ""))
    seen_en = (f"Cut to {n_r} works each, the ten most programmed composers take " + listing([f"{pct(S.at[o, 'rarefied_top10_mean'])} at the {on(o)}" for o in by_mean], False) + ". "
               f"The closest pair by composer shares is {on(hi_pair[0])} and {on(hi_pair[1])} (cosine {cs[hi_pair]:.2f}). " + ("Beethoven is the most programmed composer at all four." if all_beet else ""))
    if k:
        b.append(glance(True,
                        f"교향악축제에 나오는 국내 악단이 자기 정기연주회 프로그램에 어떤 작곡가를 실어 왔는지를, 곡목을 글자로 얻을 수 있었던 네 악단으로 견준다. 네 악단은 자료가 모두 있는 {lo}~{hi}년으로 견주고, 자료가 긴 {on('suwon')}과 {on('busan')}은 10년 단위로 따로 본다.",
                        seen_ko,
                        "악단마다 자료의 성격과 남은 기간이 다르다. 수원 · 부천은 공연 면에 예고된 프로그램, 서울은 공개된 공연 정보, 부산은 악단이 펴낸 공연보다. 순위가 아니라 나란히 놓은 표다."))
        b.append(f"<p>{full('suwon')}과 {full('bucheon')}의 수치는 두 악단 누리집의 지난 공연 면에서 곡목을 옮겨 만든 것이다. {full('busan')}은 악단이 펴낸 「부산시립교향악단 공연보(1962-2021)」의 정기공연 표에서 옮겼다. 공연보는 그동안의 공연을 날짜순으로 적어 묶은 기록집이다"
                 f"(<a href='{BUSAN_URL}'>부산문화회관 누리집의 시립교향악단 「공연보」 게시글</a>에 실린 책자). {full('seoul')}은 6절과 같은 공개 자료를 쓰되 관현악 정기공연만 골랐다(실내악 시리즈는 뺐다). "
                 f"{on('suwon')} 누리집에는 {tot['suwon']['first_year']}년 정기연주회부터 올라 있고 곡목이 글자로 적힌 것은 {tot['suwon']['last_program_year']}년 상반기까지다. 그 뒤의 면은 프로그램이 그림 한 장이라 옮기지 않았다. "
                 f"{on('bucheon')} 아카이브의 정기연주회는 {tot['bucheon']['first_year']}년부터, {on('busan')} 공연보는 {tot['busan']['first_year']}년 제1회 정기연주회부터 {tot['busan']['last_year']}년까지다.</p>")
        b.append("<p>세는 단위는 「한 공연의 프로그램에 실린 한 작품 = 1」이다. 같은 프로그램을 이틀 올리면 공연이 따로 적힌 만큼 센다. 취소되거나 연기되었다고 적힌 공연은 뺐다. "
                 "작곡가 이름은 이 사이트의 다른 면과 같이 뉴욕 필하모닉 공연 기록의 이름 표기에 맞췄고, 그 표에 없는 이름은 자료에 적힌 표기 그대로 하나로 셌다. 그래서 아래의 「작곡가 수」는 사람 수가 아니라 작곡가 표기의 수다(단체 이름도 하나로 세고, 함께 지은 곡은 먼저 적힌 이름으로 셌다). "
                 "수원 · 부천 · 서울의 자료는 예고된 프로그램이고 부산의 자료는 악단이 정리한 공연보다. 어느 쪽도 실제로 연주된 곡을 따로 확인한 기록은 아니다.</p>")
    else:
        b.append(glance(False,
                        f"Which composers the Korean orchestras that appear at the Symphony Festival put on their own subscription programs, compared for the four orchestras whose programs could be read as text. The four are compared over {lo}–{hi}, the years all four sources cover; the two long series, {on('suwon')} and {on('busan')}, are also set out by decade.",
                        seen_en,
                        "The sources differ in kind and in the years they cover: programs announced on concert pages for Suwon and Bucheon, public concert data for Seoul, and the orchestra's own record book for Busan. The tables set measures side by side; they are not a ranking."))
        b.append(f"<p>The figures for the {full('suwon')} and the {full('bucheon')} come from the past-concert pages on the two orchestras' websites. Those for the {full('busan')} come from the subscription-concert tables of the orchestra's own record book, 부산시립교향악단 공연보 (1962–2021), "
                 f"a booklet posted on <a href='{BUSAN_URL}'>the orchestra's pages of the Busan Cultural Center website</a>. For the {full('seoul')} we use the same public data as in section 6, restricted to orchestral subscription concerts (the chamber series is left out). "
                 f"The {on('suwon')} site lists subscription concerts from {tot['suwon']['first_year']}, and programs appear as text through the first half of {tot['suwon']['last_program_year']}; later pages show the program only as an image, which we did not transcribe. "
                 f"Subscription concerts in the {on('bucheon')} archive start in {tot['bucheon']['first_year']}; the {on('busan')} record book runs from the first subscription concert in {tot['busan']['first_year']} to {tot['busan']['last_year']}.</p>")
        b.append("<p>The unit is one work on one concert program. A program given on two days counts once per listed concert. Concerts marked canceled or postponed are left out. "
                 "Composer names follow the New York Philharmonic performance history, as elsewhere on this site; a name missing from that list is counted as one under the spelling in the source. The number of composers below is therefore a number of names as written, not of persons (a group counts as one, and a joint work goes to the first name given). "
                 "The Suwon, Bucheon and Seoul data are announced programs and the Busan data are the orchestra's own record; none of them has been checked against what was actually played.</p>")

    # 7.1 coverage
    sw24 = cov[(cov.orch == "suwon") & (cov.kind == "정기") & (cov.year == 2024)].iloc[0]
    nd = int(tot["bucheon"].get("subscription_concerts_without_date", 0))
    seoul_last = int(cov[cov.orch == "seoul"].year.max())
    extra_ko = ((f" {on('bucheon')} 정기연주회 {nd}회는 면에 날짜가 없어 이 그림과 해마다의 표에 없다." if nd else "")
                + (f" {on('seoul')} 자료는 예고된 공연이라 {seoul_last}년 것까지 있고, 그림은 2026년까지만 그렸다." if seoul_last > 2026 else ""))
    extra_en = ((f" {nd} {on('bucheon')} subscription concerts carry no date on their pages and are missing from this chart and from the yearly table." if nd else "")
                + (f" The {on('seoul')} data are announcements and run to {seoul_last}; the chart stops at 2026." if seoul_last > 2026 else ""))
    b.append(f"<h3>{num}.1 {'자료가 덮는 해' if k else 'Years covered'}</h3>")
    b.append(fig_notes.fx(svg_coverage(cov, (lo, hi), k), ("네 악단의 자료가 해마다 정기연주회를 몇 번 덮는지, 그 가운데 곡목을 옮긴 공연이 몇 번인지를 악단마다 한 줄씩 막대로 그린 그림이다." if k else "For each of the four orchestras, how many subscription concerts the data list each year and from how many of them works were read, one row of bars per orchestra."), dict(how=(
        f"막대 하나가 한 해다. 옅은 막대는 그 해 목록에 오른 정기연주회 수, 짙은 막대는 그 가운데 작곡가가 적힌 곡목을 한 곡 이상 옮긴 공연 수다. 두 막대의 높이가 같으면 그 해 모든 정기연주회에서 곡목을 옮긴 것이다. 짙은 막대가 더 낮으면 그만큼 옮기지 못한 공연이 있다는 뜻이다. 곡목이 그림으로만 있거나 난이 빈 공연이 대부분이고, 글자로 있어도 작곡가 표기가 없어 세지 못한 공연이 섞여 있다. "
        f"예를 들어 {on('suwon')}의 2024년은 정기연주회 {int(sw24.concerts)}회 가운데 {int(sw24.with_program)}회에서만 곡목을 옮겼다. 회색 띠가 네 악단을 견주는 {lo}~{hi}년이다. "
        f"{on('busan')} 공연보는 공연마다 곡목이 함께 적혀 있어 두 막대가 늘 같다(두 막대가 겹쳐 짙은 막대만 보인다). {on('seoul')}의 짙은 막대는 작곡가를 붙인 곡이 한 곡 이상 있는 공연 수다({lo}~{hi}년 {int(S.at['seoul', 'concerts'])}회 가운데 {int(S.at['seoul', 'concerts_with_program'])}회).{extra_ko}" if k else
        f"Each bar is one year. The light bar is the number of subscription concerts listed that year; the dark bar is how many of them yielded at least one work with a named composer. Equal heights mean works were read from every subscription concert of that year. A lower dark bar means that many concerts yielded none: mostly concerts whose program exists only as an image or whose program block is empty, and some whose text names no composer. "
        f"For example, in 2024 the {on('suwon')} lists {int(sw24.concerts)} subscription concerts, and works were read from {int(sw24.with_program)} of them. The gray band marks {lo}–{hi}, the years used to compare the four orchestras. "
        f"The {on('busan')} record book gives the program with every concert, so its two bars always coincide (the dark bar covers the light one). For the {on('seoul')} the dark bar counts concerts with at least one work whose composer was attributed ({int(S.at['seoul', 'concerts_with_program'])} of {int(S.at['seoul', 'concerts'])} in {lo}–{hi}).{extra_en}")), lang))
    cv = cov[cov.kind == "정기"].assign(o=lambda x: x.orch.map(on))
    b.append(table(cv, [("o", "악단" if k else "orchestra", None), ("year", "연도" if k else "year", ".0f"), ("concerts", "정기연주회" if k else "subscription concerts", ".0f"),
                        ("with_program", "곡목을 옮긴 공연" if k else "with works read", ".0f"), ("works", "작품 수" if k else "works", ".0f")], "krcov", lang))

    # 7.2 side by side
    b.append(f"<h3>{num}.2 {f'네 악단을 나란히 — 정기연주회 {lo}~{hi}년' if k else f'The four side by side — subscription concerts {lo}–{hi}'}</h3>")
    rng = lambda r: (f"{pct(r.rarefied_top10_mean)} ({pct(r.rarefied_top10_lo)}–{pct(r.rarefied_top10_hi)})" if r.rarefied_top10_hi - r.rarefied_top10_lo > 1e-9 else pct(r.rarefied_top10_mean))  # noqa: E731
    drng = lambda r: (f"{r.rarefied_distinct_mean:.0f} ({r.rarefied_distinct_lo:.0f}–{r.rarefied_distinct_hi:.0f})" if r.rarefied_distinct_hi - r.rarefied_distinct_lo > 1e-9 else f"{r.rarefied_distinct_mean:.0f}")  # noqa: E731
    rows = [
        ("정기연주회 수" if k else "Subscription concerts", *[f"{int(S.at[o, 'concerts']):,}" for o in ORDER]),
        ("곡목을 옮긴 공연" if k else "Concerts with works read", *[f"{int(S.at[o, 'concerts_with_program']):,}" for o in ORDER]),
        ("프로그램에 실린 작품" if k else "Works on the programs", *[f"{int(S.at[o, 'works']):,}" for o in ORDER]),
        ("그 가운데 작곡가를 아는 작품" if k else "of which with a known composer", *[f"{int(S.at[o, 'works_with_composer']):,}" for o in ORDER]),
        ("작곡가 수" if k else "Composers", *[f"{int(S.at[o, 'distinct_composers']):,}" for o in ORDER]),
        ("가장 많이 실린 작곡가" if k else "Most programmed composer", *[f"{esc(cname(S.at[o, 'top_composer']))} {pct(S.at[o, 'top_composer_share'])}" for o in ORDER]),
        ("상위 10명의 비율(전체 곡 수 그대로)" if k else "Top-10 share (all works as they are)", *[pct(S.at[o, 'top10_share_attributed']) for o in ORDER]),
        (f"상위 10명의 비율({n_r}곡으로 맞춤)" if k else f"Top-10 share (cut to {n_r} works)", *[rng(S.loc[o]) for o in ORDER]),
        (f"작곡가 수({n_r}곡으로 맞춤)" if k else f"Composers (cut to {n_r} works)", *[drng(S.loc[o]) for o in ORDER]),
        ("생존 작곡가의 곡 비율(범위)" if k else "Works by living composers (range)", *[f"{pct(S.at[o, 'living_lo'])}–{pct(S.at[o, 'living_hi'])}" for o in ORDER]),
    ]
    b.append(simple_table([("지표" if k else "Measure")] + [full(o) for o in ORDER], rows))
    if k:
        b.append(f"<p><b>곡 수를 맞추는 이유.</b> 상위 10명의 비율과 작곡가 수는 곡 수가 적을수록 기계적으로 한쪽으로 쏠린다(곡이 적으면 작곡가도 적게 나온다). 그래서 곡이 가장 적은 {on(small)}의 {n_r}곡에 맞춰, 다른 세 악단의 작곡가를 아는 곡에서 {n_r}곡을 무작위로 500번 뽑아 평균과 가운데 95%의 범위를 냈다(같은 결과를 다시 낼 수 있게 무작위 뽑기의 출발값, 곧 난수 시드를 {j['seed']}으로 고정했다). "
                 f"괄호 안이 그 범위다. 범위가 넓은 것은 그만큼 어느 곡이 뽑히느냐에 따라 값이 흔들린다는 뜻이다. 이 범위는 지금 가진 표에서 곡을 다시 뽑았을 때의 흔들림이지, 악단의 레퍼토리 전체에 대한 신뢰구간(표본으로 전체의 값을 어림할 때 그 값이 들어 있을 만한 범위)이 아니다. 곡 수를 맞춘다고 해서 빠진 프로그램이나 자료의 성격 차이까지 고쳐지지는 않는다.</p>")
        b.append("<p><b>생존 작곡가의 범위.</b> 공연한 해에 살아 있던 작곡가의 곡이 차지하는 비율이다. 생몰년은 공개 지식 데이터베이스 위키데이터(Wikidata)에서 가져왔는데, 생몰년을 아는 작곡가만으로는 정할 수 없어서 범위로 적었다. 아래 값은 생몰년을 모르는 작곡가가 모두 세상을 떠난 사람이라고 본 값, 위 값은 모두 살아 있다고 본 값이다. "
                 "생몰년을 모르는 쪽에는 뉴욕 필 표에서 찾지 못한 이름과, 찾았지만 위키데이터에서 생몰년을 얻지 못한 작곡가가 함께 있다(서울시향은 작곡가를 붙이지 못한 곡도 여기에 든다). 그 가운데 살아 있는 작곡가가 있으므로 실제 값은 아래 값보다 클 수 있고, 아래 값이 0%라고 해서 살아 있는 작곡가의 곡을 싣지 않았다는 뜻은 아니다. 세상을 떠난 해의 공연까지는 살아 있던 것으로 셌다. 네 범위가 겹치므로 이 지표로는 판정하지 않는다.</p>")
    else:
        b.append(f"<p><b>Why cut to the same number of works.</b> The top-10 share and the number of composers move mechanically with sample size (fewer works bring fewer composers). So we cut the other three orchestras to the {n_r} works of the {on(small)}, the smallest sample, by drawing {n_r} works at random 500 times from their works with a known composer and reporting the mean and the middle 95% of the draws (the random seed, the starting value of the draws, is fixed at {j['seed']} so the result can be reproduced). "
                 f"The bracketed values are that range. A wide range means the value depends a good deal on which works happen to be drawn. The range shows how much the value moves when works are redrawn from the table we have; it is not a confidence interval for an orchestra's whole repertory, and matching the number of works does not correct for missing programs or for the different nature of the sources.</p>")
        b.append("<p><b>The range for living composers.</b> This is the share of works whose composer was alive in the concert year. Birth and death years come from Wikidata, a public knowledge base; the share cannot be pinned down with only the composers whose dates we know, so it is given as a range: the low end assumes every composer without known dates had died, the high end assumes they were all alive. "
                 "Names without dates are those not found in the reference list and those found there but without dates in Wikidata (for Seoul, works without an attributed composer are included too). Some of them are living, so the true value may lie above the low end, and a low end of 0% does not mean that no living composer was programmed. A concert in the year of a composer's death counts as within the composer's lifetime. The four ranges overlap, so we draw no conclusion from this measure.</p>")
    cc = d["conc"]
    cb = cc[(cc.orchestra == FULL["bucheon"][0]) & (cc.kind == "정기") & (cc.cancelled != "1") & pd.to_numeric(cc.year, errors="coerce").between(lo, hi)]
    n_gala, n_gala_w = int((cb.n_with_composer.astype(int) >= 9).sum()), int(cb[cb.n_with_composer.astype(int) >= 9].n_with_composer.astype(int).sum())
    js = d["sh"].set_index("composer")
    j2 = "Strauss, Johann, II"
    rest_j2 = [o for o in ORDER if o != "bucheon"]
    if k:
        b.append(f"<p><b>{on('bucheon')}의 정기연주회 회차.</b> {on('bucheon')}은 신년음악회와 경축음악회에도 정기연주회 회차를 붙인다. {lo}~{hi}년에 곡이 아홉 곡 이상 실린 정기연주회가 {n_gala}회 있고, 거기에 {n_gala_w}곡이 실려 있다({on('bucheon')} 작품 {int(S.at['bucheon', 'works']):,}곡의 {n_gala_w / S.at['bucheon', 'works']:.0%}). "
                 f"왈츠와 폴카(빠른 2박자의 춤곡)가 여러 곡 실리는 공연이어서 요한 슈트라우스 2세의 비율이 {on('bucheon')}에서 {pct(js.at[j2, 'bucheon_share'])}로, " + " · ".join(f"{on(o)} {pct(js.at[j2, o + '_share'])}" for o in rest_j2) + "보다 높다. 「정기연주회」가 가리키는 공연의 범위가 악단마다 같지 않다는 뜻이다.</p>")
    else:
        b.append(f"<p><b>What counts as a subscription concert at the {on('bucheon')}.</b> The {on('bucheon')} also numbers its New Year's and civic gala concerts as subscription concerts. In {lo}–{hi} there are {n_gala} subscription concerts with nine or more works on the program, {n_gala_w} works in all ({n_gala_w / S.at['bucheon', 'works']:.0%} of the {int(S.at['bucheon', 'works']):,} {on('bucheon')} works). "
                 f"These programs carry many waltzes and polkas, so Johann Strauss II takes {pct(js.at[j2, 'bucheon_share'])} at the {on('bucheon')}, against " + listing([f"{pct(js.at[j2, o + '_share'])} at the {on(o)}" for o in rest_j2], False) + ". The label \"subscription concert\" does not cover the same range of concerts at every orchestra.</p>")
    irows = []
    for o in ORDER:
        r = S.loc[o]
        a, b_, m = r.rarefied_top10_lo, r.rarefied_top10_hi, r.rarefied_top10_mean
        if b_ - a > 1e-9:
            tip = f"{on(o)}: 평균 {m:.1%}, 500번 뽑은 값의 95%가 {a:.1%}~{b_:.1%}" if k else f"{on(o)}: mean {m:.1%}, 95% of 500 draws between {a:.1%} and {b_:.1%}"
        else:
            tip = f"{on(o)}: {m:.1%} (전체 {n_r}곡 그대로)" if k else f"{on(o)}: {m:.1%} (all {n_r} works, no draw)"
        irows.append((full(o), COL[o], a, b_, m, tip))
    dot = S.at[small, "rarefied_top10_mean"]
    above_all = all(dot > rngs[o][1] for o in others)
    overlap_all = all(max(rngs[x][0], rngs[y][0]) <= min(rngs[x][1], rngs[y][1]) for x, y in combinations(others, 2))
    t2 = f"곡 수를 가장 적은 악단의 {n_r}곡에 맞췄을 때 상위 10명 작곡가가 차지하는 비율" if k else f"Share of the ten most programmed composers when the others are cut to the {n_r} works of the smallest sample"
    x2 = "상위 10명의 곡이 작곡가를 아는 곡에서 차지하는 비율 — 오른쪽일수록 적은 수의 작곡가에 몰려 있다" if k else "Works by the top ten composers as a share of works with a known composer — further right means more concentrated on a few composers"
    bars_ko = ", ".join(f"{on(o)} {pct(rngs[o][0])}~{pct(rngs[o][1])}" for o in others)
    bars_en = listing([f"{on(o)} {pct(rngs[o][0])}–{pct(rngs[o][1])}" for o in others], False)
    cap_ko = (f"점이 평균, 옅은 막대가 500번 뽑은 값의 가운데 95%다. {josa(on(small), '은는')} 자기 곡 전부({n_r}곡)라 점 하나다. 다른 세 악단의 막대는 {bars_ko}이다. "
              + (f"{on(small)}의 점({pct(dot)})은 세 막대보다 모두 오른쪽에 있다. 곡 수를 맞춘 뒤에도, 곡목을 옮길 수 있었던 {on(small)}의 정기연주회 프로그램이 상위 작곡가에 더 몰려 있다는 뜻이다. " if above_all else f"{on(small)}의 점은 {pct(dot)}이다. ")
              + ("나머지 세 악단의 막대는 서로 겹쳐서, 이 그림만으로는 그 셋을 가르지 못한다. " if overlap_all else "막대가 서로 겹치는 악단끼리는 이 그림만으로 가르지 못한다. ")
              + "막대는 곡을 다시 뽑았을 때 값이 흔들리는 범위이고 신뢰구간이 아니다.")
    cap_en = (f"The dot is the mean and the light bar the middle 95% of 500 draws. The {on(small)} is a single dot because it is its whole sample ({n_r} works). The bars of the other three are {bars_en}. "
              + (f"The {on(small)} dot ({pct(dot)}) lies to the right of all three bars: even at equal size, the {on(small)} subscription programs we could read lean more on the top composers. " if above_all else f"The {on(small)} dot is at {pct(dot)}. ")
              + ("The other three bars overlap one another, so this chart alone does not separate those three. " if overlap_all else "Where two bars overlap, this chart alone does not separate those orchestras. ")
              + "The bars show how the value moves when works are redrawn; they are not confidence intervals.")
    b.append(fig_notes.fx(svg_intervals(irows, t2, x2), ("네 악단의 정기연주회 곡목을 같은 곡 수로 맞춘 뒤, 상위 10명 작곡가가 차지하는 비율을 점과 막대로 견준 그림이다." if k else "The share of the ten most programmed composers in each orchestra's subscription programs, with every orchestra cut to the same number of works."), dict(how=(cap_ko if k else cap_en)), lang))

    # 7.3 composer shares
    sh = d["sh"]
    top = sh.head(15)
    rows3 = [(cname(r.composer), {o: getattr(r, o + "_share") for o in ORDER}) for r in top.itertuples()]
    leg = "".join(f"<span style='--c:{COL[o]}'>{esc(full(o))}</span>" for o in ORDER)
    b.append(f"<h3>{num}.3 {'작곡가별 비율' if k else 'Shares by composer'}</h3><div class='legend'>{leg}</div>")
    r0 = top.iloc[0]
    cols3 = [o + "_share" for o in ORDER]
    gaps = (top[cols3].max(axis=1) - top[cols3].min(axis=1)).sort_values(ascending=False).index[:2]

    def gap_txt(i, ko_):
        g3 = top.loc[i]
        g_hi, g_lo = max(ORDER, key=lambda o: g3[o + "_share"]), min(ORDER, key=lambda o: g3[o + "_share"])
        return (f"{cname(g3.composer)}({on(g_hi)} {pct(g3[g_hi + '_share'])}, {on(g_lo)} {pct(g3[g_lo + '_share'])})" if ko_
                else f"{cname(g3.composer)} ({pct(g3[g_hi + '_share'])} at the {on(g_hi)}, {pct(g3[g_lo + '_share'])} at the {on(g_lo)})")
    lead = all_beet and r0.composer == "Beethoven, Ludwig van"
    concl_ko = ((f"네 악단 모두에서 {cname(r0.composer)}의 막대가 가장 길다. " if lead else "")
                + f"악단 사이에 막대 길이가 크게 벌어지는 두 작곡가는 {gap_txt(gaps[0], True)}, {gap_txt(gaps[1], True)}다.")
    concl_en = ((f"At all four orchestras the longest bar is {cname(r0.composer)}'s. " if lead else "")
                + f"The two composers whose bars differ most across the orchestras are {gap_txt(gaps[0], False)} and {gap_txt(gaps[1], False)}.")
    t3 = f"네 악단 비율의 단순 평균이 높은 작곡가 15명 — 정기연주회 {lo}~{hi}년" if k else f"The 15 composers with the highest simple average of the four shares — subscription concerts {lo}–{hi}"
    x3 = "그 악단의 작곡가를 아는 작품 가운데 이 작곡가의 곡이 차지하는 비율 — 막대가 길수록 자주 실렸다" if k else "Share of the orchestra's works with a known composer that are by this composer — a longer bar means programmed more often"
    ex_ko = ", ".join(f"{on(o)} {pct(getattr(r0, o + '_share'))}" for o in ORDER)
    ex_en = listing([f"{pct(getattr(r0, o + '_share'))} at the {on(o)}" for o in ORDER], False)
    b.append(fig_notes.fx(svg_bars(rows3, t3, x3, ORDER, COL, {o: on(o) for o in ORDER}), ("네 악단의 정기연주회에서 많이 연주된 작곡가 열다섯 명이 악단마다 차지하는 비율을, 작곡가마다 막대 넷으로 그린 그림이다." if k else "The fifteen composers most played across the four orchestras' subscription concerts, with four bars per composer for the four orchestras' shares."), dict(how=(
        f"네 악단의 비율을 단순 평균해 높은 순서로 열다섯 명을 골랐다. 작곡가마다 막대 넷이 위에서부터 {', '.join(on(o) for o in ORDER)}이다. 예를 들어 {cname(r0.composer)}의 곡이 차지하는 비율은 {ex_ko}다. "
        f"{on('seoul')}의 비율은 작곡가를 아는 곡({int(S.at['seoul', 'works_with_composer']):,}곡)만으로 나눈 값이다. {concl_ko}" if k else
        f"The fifteen are those with the highest simple average of the four orchestras' shares. Under each composer the four bars are, from the top, {listing([on(o) for o in ORDER], False)}. For example, {cname(r0.composer)} accounts for {ex_en}. "
        f"{on('seoul')} shares are out of works with a known composer ({int(S.at['seoul', 'works_with_composer']):,}). {concl_en}")), lang))
    st = sh.assign(cn=sh.composer.map(cname))
    b.append(table(st, [("cn", "작곡가" if k else "composer", None)] + [(o + "_works", f"{on(o)} {'곡 수' if k else 'works'}", ".0f") for o in ORDER] + [(o + "_share", on(o), ".1%") for o in ORDER], "krsh", lang))
    cr = [(f"{on(a)} – {on(b_)}", f"{v:.3f}", f"{int(d['cos'][(d['cos'].a == a) & (d['cos'].b == b_)].shared_composers.iloc[0])}") for (a, b_), v in sorted(cs.items(), key=lambda x: -x[1])]
    b.append(simple_table(("악단 짝", "코사인 유사도", "둘 다에 나오는 작곡가 수") if k else ("Pair", "Cosine similarity", "Composers on both"), cr))
    if k:
        b.append(f"<p><b>코사인 유사도</b>는 두 악단의 작곡가별 비율이 얼마나 닮았는지를 0에서 1 사이로 잰 값이다. 두 악단이 같은 작곡가를 같은 비율로 실으면 1, 겹치는 작곡가가 하나도 없으면 0이다(이름은 계산에 쓰는 식에서 왔다). "
                 f"가장 닮은 짝은 {josa(on(hi_pair[0]), '과와')} {on(hi_pair[1])}({cs[hi_pair]:.2f}), 가장 덜 닮은 짝은 {josa(on(lo_pair[0]), '과와')} {on(lo_pair[1])}({cs[lo_pair]:.2f})이다. 6절에서 서울시향과 뉴욕 필을 견준 값은 {seoul_ny:.2f}이었다(기간과 범위가 달라 바로 견줄 수는 없다).</p>")
    else:
        b.append(f"<p><b>Cosine similarity</b> measures, between 0 and 1, how alike two orchestras' composer shares are: 1 if they program the same composers in the same proportions, 0 if they share no composer. "
                 f"{on(hi_pair[0])} and {on(hi_pair[1])} are the closest pair at {cs[hi_pair]:.2f}; {on(lo_pair[0])} and {on(lo_pair[1])} the least alike at {cs[lo_pair]:.2f}. In section 6 the Seoul Philharmonic against the New York Philharmonic gave {seoul_ny:.2f} (different years and scope, so not directly comparable).</p>")

    # 7.4 the two long series by decade
    dec, dp = d["dec"], d["dp"]
    dlab = lambda y: f"{int(y)}{'년대' if k else 's'}"  # noqa: E731
    b.append(f"<h3>{num}.4 {'긴 자료 둘 — ' + on('busan') + ' ' + str(tot['busan']['first_year']) + '년부터, ' + on('suwon') + ' ' + str(tot['suwon']['first_year']) + '년부터' if k else 'The two long series — ' + on('busan') + ' from ' + str(tot['busan']['first_year']) + ', ' + on('suwon') + ' from ' + str(tot['suwon']['first_year'])}</h3>")
    drows = []
    for o in ("busan", "suwon"):
        for r in dec[(dec.orch == o) & dec.top10_n90_mean.notna()].itertuples():
            tip = (f"{on(o)} {dlab(r.decade)}: 평균 {r.top10_n90_mean:.1%}, 95%가 {r.top10_n90_lo:.1%}~{r.top10_n90_hi:.1%} (그 10년의 작품 {int(r.works)}곡에서 {dn}곡씩)" if k
                   else f"{on(o)} {dlab(r.decade)}: mean {r.top10_n90_mean:.1%}, 95% between {r.top10_n90_lo:.1%} and {r.top10_n90_hi:.1%} ({dn} works drawn from the decade's {int(r.works)})")
            drows.append((f"{on(o)} {dlab(r.decade)}", COL[o], r.top10_n90_lo, r.top10_n90_hi, r.top10_n90_mean, tip))
    both = sorted(set(dec[(dec.orch == "busan") & dec.top10_n90_mean.notna()].decade) & set(dec[(dec.orch == "suwon") & dec.top10_n90_mean.notna()].decade))
    dx = dec.set_index(["orch", "decade"])
    clear = [y for y in both if dx.at[("suwon", y), "top10_n90_lo"] > dx.at[("busan", y), "top10_n90_hi"]]
    ex = dx.loc[("busan", both[0])]
    t4 = f"10년마다 {dn}곡으로 맞춘 상위 10명 작곡가의 비율 — 정기연주회" if k else f"Share of the ten most programmed composers by decade, cut to {dn} works — subscription concerts"
    b.append(fig_notes.fx(svg_intervals(drows, t4, x2, label_w=200), ("부산시향과 수원시향의 정기연주회에서 상위 10명 작곡가의 비율이 10년마다 어떻게 달랐는지, 같은 곡 수로 맞춰 견준 그림이다." if k else "How the share of the ten most programmed composers changed decade by decade in the Busan and Suwon subscription concerts, cut to the same number of works."), dict(how=(
        f"한 줄이 한 악단의 한 10년이다. 그 10년의 정기연주회 작품에서 {dn}곡을 500번 뽑아, 점은 평균이고 옅은 막대는 가운데 95%다. 예를 들어 {on('busan')}의 {dlab(both[0])}는 평균 {pct(ex.top10_n90_mean)}({pct(ex.top10_n90_lo)}~{pct(ex.top10_n90_hi)})이다. "
        f"두 악단이 함께 있는 {len(both)}개 10년 가운데 {len(clear)}개({', '.join(dlab(y) for y in clear) or '없음'})에서 {on('suwon')}의 막대가 {on('busan')}의 막대보다 온전히 오른쪽에 있고, 나머지에서는 겹친다(겹치는 폭은 10년마다 다르다 — 아래 표의 범위). "
        f"작품이 {dn}곡에 못 미치는 10년(두 악단의 2020년대)은 그리지 않았다. {on('suwon')} 1980년대 줄은 남은 곡목이 특히 짧다는 아래 단서와 함께 읽어야 한다." if k else
        f"Each row is one decade of one orchestra: {dn} works are drawn 500 times from that decade's subscription programs; the dot is the mean and the light bar the middle 95%. For example, the {on('busan')} in the {dlab(both[0])} has a mean of {pct(ex.top10_n90_mean)} ({pct(ex.top10_n90_lo)}–{pct(ex.top10_n90_hi)}). "
        f"In {len(clear)} of the {len(both)} decades the two share ({listing([dlab(y) for y in clear], False) or 'none'}) the {on('suwon')} bar lies entirely to the right of the {on('busan')} bar; in the others they overlap (by different amounts — see the ranges in the tables below). "
        f"Decades with fewer than {dn} works (the 2020s for both) are not drawn. The {on('suwon')} row for the 1980s should be read with the caveat below about its especially short surviving listings.")), lang))
    for o in ("busan", "suwon"):
        dr = []
        for r in dec[dec.orch == o].itertuples():
            t3_ = "; ".join(f"{esc(cname(x.rsplit(' ', 1)[0]))} {x.rsplit(' ', 1)[1]}" for x in str(r.top3).split("; "))
            cut = f"{pct(r.top10_n90_mean)} ({pct(r.top10_n90_lo)}–{pct(r.top10_n90_hi)})" if pd.notna(r.top10_n90_mean) else "—"
            dr.append((f"{dlab(r.decade)} ({int(r.first_year)}–{int(r.last_year)})", f"{int(r.concerts)}", f"{int(r.concerts_with_program)}", f"{int(r.works)}", f"{int(r.distinct_composers)}", cut, pct(r.unmatched_share), t3_))
        b.append(f"<p><b>{esc(full(o))}</b></p>" + simple_table(
            ("10년(자료가 있는 해)", "정기연주회", "곡목을 옮긴 공연", "작품 수", "작곡가 수", f"상위 10명의 비율({dn}곡으로 맞춤)", "이름 표와 맞추지 못한 표기의 곡", "가장 많이 실린 세 사람") if k else
            ("Decade (years with data)", "Subscription concerts", "With works read", "Works", "Composers", f"Top-10 share (cut to {dn} works)", "Works whose composer name was not matched", "Three most programmed"), dr))
    bz = dec[dec.orch == "busan"]
    not_beet = [f"{on(r.orch)} {dlab(r.decade)}" if k else f"{on(r.orch)} {dlab(r.decade)}" for r in dec.itertuples() if not str(r.top3).startswith("Beethoven, Ludwig van")]
    um_first, um_last = bz.iloc[0], bz[bz.works >= dn].iloc[-1]
    wb = d["works"]
    wb = wb[(wb.orchestra == FULL["busan"][0]) & (wb.kind == "정기") & (wb.status == "unmatched") & ~wb.concert_id.isin(set(cc[cc.cancelled == "1"].concert_id))]
    um_names = list(wb.composer_as_written.value_counts().head(3).index)
    dpr = [(dlab(r.decade), f"{r.cosine:.3f}", f"{int(r.shared_composers)}") for r in dp.itertuples()]
    if k:
        b.append(f"<p>{on('busan')} 공연보는 {tot['busan']['first_year']}년 제1회부터 {tot['busan']['last_year']}년까지 정기연주회 {tot['busan']['subscription_concerts']}회(취소 · 연기된 공연 제외)의 프로그램을 싣고 있어 여섯 번의 10년을 이어서 볼 수 있다. "
                 f"두 악단의 10년마다 가장 많이 실린 작곡가는 " + (f"{', '.join(not_beet)}만 빼고 모두 베토벤이다. " if not_beet else "모두 베토벤이다. ")
                 + f"뉴욕 필 이름 표와 맞추지 못한 표기의 곡은 {on('busan')}에서 {dlab(um_first.decade)} {pct(um_first.unmatched_share)}에서 {dlab(um_last.decade)} {pct(um_last.unmatched_share)}로 줄어든다. {on('busan')} 정기연주회에서 그런 이름으로 가장 많이 나오는 것은 {' · '.join(esc(x) for x in um_names)}이다. 이 비율은 이름 대조의 결과이지, 한국 작곡가의 곡이 프로그램에서 줄었다는 측정이 아니다.</p>")
        b.append(f"<p>두 악단의 작곡가 분포가 10년마다 얼마나 닮았는지(코사인 유사도)는 아래와 같다. {dlab(dp.decade.min())}부터 {dlab(dp.decade.max())}까지 {dp.cosine.min():.2f}~{dp.cosine.max():.2f} 사이다.</p>")
    else:
        b.append(f"<p>The {on('busan')} record book gives the programs of {tot['busan']['subscription_concerts']} subscription concerts (canceled and postponed ones left out) from the first in {tot['busan']['first_year']} to {tot['busan']['last_year']}, so six decades can be followed. "
                 f"At both orchestras the most programmed composer of each decade is Beethoven" + (f", except for the {listing(not_beet, False)}. " if not_beet else " throughout. ")
                 + f"Works whose composer's name could not be matched to the New York Philharmonic name list fall at the {on('busan')} from {pct(um_first.unmatched_share)} in the {dlab(um_first.decade)} to {pct(um_last.unmatched_share)} in the {dlab(um_last.decade)}. The names that occur most often among them in {on('busan')} subscription concerts are {listing([esc(x) for x in um_names], False)}. The share is a result of the name matching; it is not a measurement of how much music by Korean composers was programmed.</p>")
        b.append(f"<p>How alike the two orchestras' composer shares are in each decade (cosine similarity) is shown below: between {dp.cosine.min():.2f} and {dp.cosine.max():.2f} from the {dlab(dp.decade.min())} to the {dlab(dp.decade.max())}.</p>")
    canc_ids = set(cc[cc.cancelled == "1"].concert_id)
    ws_ = d["works"]
    ws_ = ws_[(ws_.kind == "정기") & ws_.status.isin(["matched", "unmatched"]) & ~ws_.concert_id.isin(canc_ids)]
    per = ws_.groupby(["orchestra", "concert_id"]).size().reset_index(name="n").merge(cc[["concert_id", "year"]], on="concert_id")
    per["decade"] = pd.to_numeric(per.year, errors="coerce") // 10 * 10

    def one(o, dec_):
        g_ = per[(per.orchestra == FULL[o][0]) & (per.decade == dec_)]
        return int((g_.n == 1).sum()), len(g_)
    s80, b80 = one("suwon", 1980), one("busan", 1980)
    b.append("<p>" + (f"{on('suwon')}의 1980년대는 남은 곡목이 특히 짧다. 곡목을 옮긴 공연 {s80[1]}회 가운데 {s80[0]}회에 한 곡만 적혀 있다({on('busan')}의 같은 10년은 {b80[1]}회 가운데 {b80[0]}회). "
                      "남아 있는 곡목이 그 공연 프로그램의 전부라는 보장은 없으므로, 10년 단위 값은 악단의 레퍼토리 전체가 아니라 남아 있는 곡목의 성질로 읽어야 한다." if k else
                      f"The surviving listings of the {on('suwon')} in the 1980s are especially short: {s80[0]} of the {s80[1]} concerts from which works were read list a single work ({b80[0]} of {b80[1]} at the {on('busan')}). "
                      "Nothing guarantees that a surviving listing is the whole program, so the decade values describe the listings that survive, not an orchestra's whole repertory.") + "</p>")
    b.append(simple_table((f"10년 ({on('suwon')} – {on('busan')})", "코사인 유사도", "둘 다에 나오는 작곡가 수") if k else (f"Decade ({on('suwon')} – {on('busan')})", "Cosine similarity", "Composers on both"), dpr))

    # 7.5 most programmed works
    tw = d["top"]
    b.append(f"<h3>{num}.5 {'정기연주회에 가장 자주 실린 작품' if k else 'Works most often on subscription programs'}</h3>")
    ties = {}
    for o in ("busan", "suwon", "bucheon"):
        g25 = tw[tw.orch == o]
        n10 = int(g25.n.iloc[9])
        ties[o] = int((g25.n == n10).sum() - (g25.head(10).n == n10).sum()) if int(g25.n.iloc[-1]) < n10 else None
        g = tw[tw.orch == o].head(10)
        rr = [(esc(cname(r.cid)), esc(r.work_key), f"{int(r.n)}", f"{int(r.first)}–{int(r.last)}") for r in g.itertuples()]
        span = f"{tot[o]['first_program_year']}–{tot[o]['last_program_year']}"
        b.append(f"<p><b>{esc(full(o))}</b> ({span})</p>" + simple_table(("작곡가", "작품", "프로그램에 실린 횟수", "처음–마지막 해") if k else ("Composer", "Work", "Times on a program", "First–last year"), rr, num_from=2))
    b.append("<p>" + ("같은 작품을 자료마다 다르게 적기 때문에(「교향곡 5번 운명」 「교향곡 제5번 다단조 작품 67」), 조와 작품 번호, 별명을 떼고 「갈래 + 번호」로 묶었다. 번호가 없는 작품은 갈래와 남은 이름이 같으면 한 작품으로 묶었다(멘델스존 「바이올린 협주곡」). 한 악장만 올린 줄도 그 작품으로 셌으므로 전곡을 올린 횟수가 아니다. "
                      "옛 출판 번호로 적힌 드보르자크의 교향곡과 슈베르트의 「미완성」 · 「그레이트」는 지금 쓰는 번호로 옮겼다. 표기가 달라 따로 세인 것과 자료의 오자 때문에 잘못 묶인 것이 남아 있을 수 있다. 기간이 악단마다 다르므로 횟수를 악단끼리 견주지 않는다. "
                      + "".join(f"{on(o)} 표는 마지막 줄과 횟수가 같은 작품이 표 밖에 {n_}개 더 있다. " for o, n_ in ties.items() if n_)
                      + "작품 이름은 자료의 한글 표기를 그대로 옮긴 것이다."
                      if k else "The sources write the same work in different ways, so keys, opus numbers and nicknames were dropped and works grouped by kind and number. A work without a number is grouped when its kind and remaining title agree (Mendelssohn's violin concerto). A line that gives a single movement counts for the work, so these are not counts of complete performances. "
                      "Dvořák symphonies written with their old publication numbers, and Schubert's Unfinished and Great, were moved to the numbers in use today. Some works written differently may still be counted apart, and misprints in the sources may have grouped a few wrongly. The periods differ by orchestra, so the counts should not be compared across orchestras. "
                      + "".join(f"In the {on(o)} table {n_} more work{'s' if n_ > 1 else ''} outside the table share{'' if n_ > 1 else 's'} the count of the last row. " for o, n_ in ties.items() if n_)
                      + "Work titles come from the Korean sources and are shown in Korean.") + "</p>")

    # 7.6 kinds of concert (Suwon)
    kp, kx = kinds.loc[("suwon", "기획")], kinds.loc[("suwon", "특별")]
    wk = d["works"]
    wk = wk[(wk.orchestra == FULL["suwon"][0]) & wk.status.isin(["matched", "unmatched"]) & ~wk.concert_id.isin(set(cc[cc.cancelled == "1"].concert_id))]
    wk = wk.assign(cid=lambda x: x.composer.where(x.composer != "", "ko:" + x.composer_as_written))
    a = wk[wk.kind == "정기"].cid.value_counts(normalize=True)
    p = wk[wk.kind.isin(["기획", "특별"])].cid.value_counts(normalize=True)
    names10 = list(p.head(10).index)
    rows2 = [(cname(c), {"plan": float(p.get(c, 0)), "sub": float(a.get(c, 0))}) for c in names10]
    lab2 = {"plan": "기획 · 특별 공연" if k else "planned and special concerts", "sub": "정기연주회" if k else "subscription concerts"}
    col2 = {"plan": "var(--g3)", "sub": "var(--g5)"}
    b.append(f"<h3>{num}.6 {on('suwon')}{'의 기획 · 특별 공연' if k else ': planned and special concerts'}</h3>")
    b.append(f"<div class='legend'><span style='--c:var(--g3)'>{lab2['plan']}</span><span style='--c:var(--g5)'>{lab2['sub']}</span></div>")
    n_plan_prog, n_plan = int(kp.concerts_with_program + kx.concerts_with_program), int(kp.concerts + kx.concerts)
    cp = cov[(cov.orch == "suwon") & cov.kind.isin(["기획", "특별"])]
    n_plan_1223 = int(cp[cp.year.between(2012, 2023)].with_program.sum())
    n_plan_w, n_plan_nc = int(kp.works_with_composer + kx.works_with_composer), int(kp.lines_without_composer + kx.lines_without_composer)
    c0 = names10[0]
    t6 = "수원시향 기획 · 특별 공연에 많이 실린 작곡가 10명과, 같은 작곡가의 정기연주회 비율" if k else "The ten composers most programmed in Suwon Phil planned and special concerts, with their share in subscription concerts"
    x6 = "그 종류의 공연에 실린 작품 가운데 이 작곡가의 곡이 차지하는 비율 — 막대가 길수록 자주 실렸다" if k else "Share of the works in that kind of concert that are by this composer — a longer bar means programmed more often"
    n_more = sum(1 for c_ in names10 if p.get(c_, 0) > a.get(c_, 0))
    b.append(fig_notes.fx(svg_bars(rows2, t6, x6, ['plan', 'sub'], col2, lab2), ("수원시향 기획 · 특별 공연에 많이 실린 작곡가 10명의 비율을, 같은 작곡가의 정기연주회 비율과 나란히 그린 그림이다." if k else "The ten composers most programmed in Suwon Phil planned and special concerts, each beside its share in subscription concerts."), dict(how=(
        f"작곡가마다 위 막대가 기획 · 특별 공연, 아래 막대가 정기연주회다. 예를 들어 {josa(cname(c0), '은는')} 기획 · 특별 공연 작품의 {pct(p.get(c0, 0))}, 정기연주회 작품의 {pct(a.get(c0, 0))}다. "
        f"기획 · 특별 공연은 목록에 {n_plan}회가 있지만 곡목을 옮긴 것은 {n_plan_prog}회({n_plan_1223}회가 2012~2023년 공연)이고, 거기서 작곡가가 적힌 작품 {n_plan_w:,}곡을 셌다. "
        f"영화 음악이나 뮤지컬 곡처럼 작곡가 없이 곡 이름만 적혔거나 작곡가를 읽지 못한 줄 {n_plan_nc}개는 세지 못했다. 열 명 가운데 {n_more}명은 기획 · 특별 공연 쪽 막대가 더 길다. "
        f"다만 기획 · 특별 공연의 곡목은 대부분 2012~2023년 것이고 정기연주회 곡목은 {tot['suwon']['first_program_year']}년부터라, 두 막대의 차이를 공연 종류의 차이로만 읽을 수는 없다." if k else
        f"For each composer the upper bar is planned and special concerts and the lower bar subscription concerts. For example, {cname(c0)} is {pct(p.get(c0, 0))} of the works in planned and special concerts and {pct(a.get(c0, 0))} in subscription concerts. "
        f"{n_plan} planned and special concerts are listed, but works were read from {n_plan_prog} ({n_plan_1223} of them from 2012–2023), giving {n_plan_w:,} works with a named composer. "
        f"{n_plan_nc} lines that give only a title without a composer (film music, musical numbers and the like), or whose composer could not be read, could not be counted. For {n_more} of the ten the planned-and-special bar is the longer one. "
        f"But most planned and special programs date from 2012–2023 while subscription programs go back to {tot['suwon']['first_program_year']}, so the difference between the two bars cannot be read as an effect of the kind of concert alone.")), lang))
    kb = kinds.loc[("busan", "특별")]
    b.append("<p>" + (f"{on('suwon')} 누리집은 공연마다 종류(정기 · 기획 · 특별 · 초청 등)를 적어 둔다. 악단끼리 견주는 표는 모두 정기연주회만으로 만들었다. {on('bucheon')} 아카이브에는 정기연주회 말고도 해설음악회 · 아침의 클래식 같은 공연이 함께 있는데 누리집이 종류를 따로 적지 않고, "
                      f"{on('busan')} 공연보에는 특별공연 {int(kb.concerts):,}회(취소된 공연 제외)와 교류 · 해외 연주회가 따로 실려 있다. 이들은 이 그림에 넣지 않았고 자료 표에만 들어 있다."
                      if k else f"The {on('suwon')} site labels each concert by kind (subscription, planned, special, guest and so on). All cross-orchestra tables use subscription concerts only. The {on('bucheon')} archive also holds talks-with-music and morning concerts without labeling kinds, "
                      f"and the {on('busan')} record book lists {int(kb.concerts):,} special concerts (canceled ones left out) as well as exchange and overseas concerts separately. These are not in this chart; they are in the data table only.") + "</p>")

    # 7.7 festival vs home
    f = d["fest"]
    f = f[f.orch.isin(["suwon", "bucheon"])]
    fr = []
    for r in f.itertuples():
        same = r.home_same_year or ("—" if r.home_programs_that_year else ("곡목 없음" if k else "no programs"))
        if r.home_same_year_canceled:
            same = (same + "; " if r.home_same_year else "") + r.home_same_year_canceled + (" (취소로 적힌 공연)" if k else " (concert marked canceled)")
        fr.append((on(r.orch), r.festival_date, esc(r.composer_ko if k else cname(r.composer)), esc(r.title), esc(same.replace("; ", ", ")), esc((r.home_other_years or "").replace("; ", ", "))))
    fa = f[f.home_programs_that_year > 0]
    hit = int((fa.home_same_year != "").sum())
    n_canc = int(((fa.home_same_year == "") & (fa.home_same_year_canceled != "")).sum())

    def near(r):
        ds = [abs((pd.Timestamp(x) - pd.Timestamp(r.festival_date)).days) for x in r.home_same_year.split("; ") if x]
        return min(ds) if ds else None
    gaps = [g_ for g_ in (near(r) for r in fa.itertuples()) if g_ is not None]
    within = sum(1 for g_ in gaps if g_ <= 14)
    b.append(f"<h3>{num}.7 {'교향악축제에 들고 간 곡과 자기 정기연주회' if k else 'Works taken to the Symphony Festival and the home programs'}</h3>")
    if k:
        b.append(f"<p>예술의전당 교향악축제(2022~2026년) 프로그램에 실린 곡이 같은 악단의 자기 정기연주회 프로그램에도 실렸는지를 작곡가와 작품으로 맞춰 보았다. "
                 f"{josa(on('suwon'), '과와')} {josa(on('bucheon'), '이가')} 축제 프로그램에 실은 곡은 {len(f)}곡이다. 그 가운데 그 해의 정기연주회 곡목을 얻은 {len(fa)}곡만 보면 {hit}곡이 같은 해 자기 정기연주회 프로그램에도 실려 있다. 그 {hit}곡 가운데 {within}곡은 축제 공연과 두 주 안에 든 날짜다. "
                 + (f"이 밖에 {n_canc}곡은 누리집에 취소로 적힌 정기연주회의 프로그램에 실려 있었다. " if n_canc else "")
                 + f"표기가 달라 자동으로 맞지 않은 {len(d['man'])}곡은 두 프로그램을 읽고 손으로 맞췄다(「탤리스」와 「탈리스」 등). "
                 + f"찾지 못한 곡은 표기가 달라 맞추지 못한 것일 수 있으므로 「싣지 않았다」는 뜻이 아니다. {on('suwon')}의 2025 · 2026년은 정기연주회 곡목이 글자로 없어 견줄 수 없고, {on('busan')}은 공연보가 {tot['busan']['last_year']}년까지라 견줄 수 없다.</p>")
    else:
        b.append(f"<p>For the works on the Seoul Arts Center Symphony Festival programs (2022–2026) we checked, by composer and work, whether the same orchestra also had them on one of its own subscription programs. "
                 f"The {on('suwon')} and the {on('bucheon')} put {len(f)} works on their festival programs. Looking only at the {len(fa)} from years for which home programs were found, {hit} are also on a home subscription program in the same year, {within} of those within two weeks of the festival concert. "
                 + (f"Another {n_canc} were on the program of a subscription concert that the site marks as canceled. " if n_canc else "")
                 + f"{len(d['man'])} works written differently on the two programs were matched by reading both (two Korean spellings of Tallis, for example). "
                 + f"A work not found may simply be written differently, so it does not mean it was not programmed. The {on('suwon')} cannot be checked for 2025 and 2026, when its programs are not available as text, nor the {on('busan')}, whose record book ends in {tot['busan']['last_year']}.</p>")
    b.append("<details><summary style='cursor:pointer;color:var(--fg2);font-size:.9rem;margin:.3rem 0'>" + (f"표 보기 ({len(fr)}행)" if k else f"Show table ({len(fr)} rows)") + "</summary>"
             + simple_table(("악단", "축제 공연일", "작곡가", "축제 프로그램의 곡", "같은 해 정기연주회 프로그램", "다른 해") if k else ("Orchestra", "Festival date", "Composer", "Work on the festival program", "Home program, same year", "Other years"), fr, num_from=9) + "</details>")
    b.append("<p class='src'>" + ("표에서 「—」는 그 해 정기연주회에서 옮긴 곡목 가운데 그 곡을 찾지 못했다는 뜻이고, 「곡목 없음」은 그 해 정기연주회 가운데 작곡가가 적힌 곡목을 옮긴 공연이 하나도 없다는 뜻이다. 곡 이름 뒤의 Op. · K. · FWV · M. · L. 등은 작품 번호와 작품 목록 번호다. " if k
                                  else "In the table a dash means the work was not found among the works read from that year's home subscription programs; \"no programs\" means that no home subscription concert of that year yielded a work with a named composer. Op., K., FWV, M., L. and the like after a title are opus and catalog numbers. ") + "</p>")
    b.append("<p class='src'>" + ("축제 프로그램은 <a href='https://bowonkwon.github.io/Conductors-Lineage/ko/repertoire.html'>「지휘의 계보」의 축제 레퍼토리 면</a>에서 정리한 표다." if k
                                  else "The festival programs are the table compiled for the <a href='https://bowonkwon.github.io/Conductors-Lineage/en/repertoire.html'>festival repertoire page of Conductors' lineage</a>.") + "</p>")

    # 7.8 how the tables were made
    aw = d["works"]
    aw = aw[~aw.concert_id.isin(set(cc[cc.cancelled == "1"].concert_id))]
    n_all = int(aw.status.isin(["matched", "unmatched"]).sum()); n_m = int((aw.status == "matched").sum()); n_nc = int((aw.status == "no_composer").sum())
    n_skip = int((d["skip"].reason == "chorus only").sum())
    nn = d["notname"]; nn_kept = nn[nn["class"] != "notice"]; nn_note = nn[nn["class"] == "notice"]
    n_nn, n_nn_kept, n_nn_note = len(nn), int(nn_kept.lines.sum()), int(nn_note.lines.sum())
    b.append(f"<h3>{num}.8 {'표를 만든 방법' if k else 'How the tables were made'}</h3>")
    if k:
        b.append(f"<p>수원 · 부천은 공연 면의 프로그램 난에서, 부산은 공연보 표의 프로그램 칸에서 「작곡가 표기로 시작하는 줄」을 작품 한 줄로 옮겼다(「베토벤 / 교향곡 제5번」 「슈만, 첼로 협주곡 가단조 작품 129」). 한 줄에 프로그램 전체를 쉼표로 이어 적은 면은 곡마다 나눴고, 한글 줄과 영문 줄이 같은 작품을 나란히 적은 면은 한 작품으로 합쳤다. "
                 f"악장 줄, 휴식 줄, 출연자 줄, 안내 줄은 세지 않았다. 세 악단의 모든 공연 종류를 통틀어 작곡가 자리에 이름이 적힌 작품은 {n_all:,}곡이고, 그 가운데 {n_m:,}곡({n_m / n_all:.1%})의 작곡가를 뉴욕 필 기록의 이름 표기에 맞췄다. 나머지 {n_all - n_m:,}곡은 지금의 대조로 그 표의 이름과 맞추지 못한 표기라 자료의 표기 그대로 두었다(그 표에 없는 한국 작곡가와 영화 · 뮤지컬 음악 작곡가, 그 표에 있지만 표기를 맞추지 못한 이름이 섞여 있고, 가수나 밴드처럼 작곡가가 아닐 수 있는 이름이나 작곡가 미상이라는 표시(Anonymous)가 작곡가 자리에 적힌 줄도 있다). "
                 f"작곡가 없이 곡 이름만 적힌 줄과 작곡가를 읽지 못한 줄 {n_nc:,}개는 작품 표에 남기되 어느 수치에도 넣지 않았다(이런 줄을 빠짐없이 옮긴 것은 아니다). 곡목과 작곡가는 자료에 적힌 것만 옮겼고, 자료에 없는 것을 채우지 않았다.</p>")
        b.append(f"<p><b>이름을 맞춘 방법과 한계.</b> 이름과 성을 다 적은 표기는 뉴욕 필 기록의 그 사람에게 맞췄다. 성만 적힌 이름은 그 기록에서 그 성으로 가장 많이 나오는 사람이고 20회 이상 나올 때만 자동으로 맞췄다(이 사이트가 이미 한글 이름을 정해 둔 작곡가 50명은 횟수와 관계없이 맞췄다). 그 밖의 표기는 곡 이름으로 확인해 손으로 올린 것만 맞췄다(「자료」 면에서 받을 수 있는 대조표 파일 orch_kr_composer_alias.csv). "
                 f"같은 성을 쓰는 사람이 여럿인 표기(슈트라우스, 웨버, 윌리엄스 등)는 곡 이름에 든 낱말로 갈랐고, 가르지 못하면 자료의 표기 그대로 두었다. 맞춘 결과는 「자료에 적힌 이름이 누구를 가리키는가」이며, 그 곡을 실제로 누가 지었는지를 따로 확인한 것은 아니다. "
                 f"이름과 곡 이름 사이에 구분 기호가 없는데 표에 없는 이름인 줄, 오자가 있는 줄처럼 이 규칙으로 읽지 못한 줄이 남아 있다. 거꾸로 규칙이 작곡가 표기로 읽었지만 자료에서는 곡 이름이거나 갈래 · 출연 표시인 말도 있었다(곡 이름을 작곡가보다 먼저 적은 「리베르 탱고 - 아스토르 피아졸라」, 「영화/…」 「김수희 노래/…」 같은 줄). 뉴욕 필 기록의 이름에 맞추지 못한 표기를 모두 훑어 이런 말 {n_nn}가지를 손으로 가려냈다(「자료」 면의 orch_kr_not_composer.csv). 그 말로 읽힌 {n_nn_kept + n_nn_note}줄 가운데 곡 이름이 있는 {n_nn_kept}줄은 작곡가를 읽지 못한 줄로 두었고, 안내 줄 {n_nn_note}줄은 뺐다. 가려내지 못한 말이 남아 있을 수 있다. {on('bucheon')} 아카이브에서 합창단의 공연이고 관현악단이 출연 단체로 적히지 않은 {n_skip}회는 뺐다(제목과 면의 출연 줄로 가렸다. 부천필코러스는 부천시립합창단의 옛 이름이다). 합창단원의 독창 · 중창 무대처럼 출연 줄에 단체 이름이 없는 공연은 남아 있을 수 있다. 합창단의 정기연주회에 관현악단이 함께 출연한 공연은 표에 남기되 부천필의 정기연주회로 세지 않았다. "
                 f"부산 공연보에서 순회공연처럼 여러 날짜가 프로그램 한 칸을 함께 쓰는 자리는 그 날짜마다 같은 프로그램으로 적었고, 「앵콜」 줄과 공연 속 활동(악기 체험, 동화 구연, 콩트 등)을 적은 줄은 세지 않았다. 작곡가와 편곡자를 함께 적은 줄은 작곡가의 곡으로, 편곡자만 적은 줄은 작곡가 없는 줄로 두었다.</p>")
    else:
        b.append(f"<p>From the program block of each Suwon and Bucheon concert page, and from the program column of the Busan record book's tables, every line that starts with a composer's name became one work. Pages that run the whole program on one line were split by work, and pages that give a Korean and an English line for the same work were merged. "
                 f"Movement lines, intermission lines, performer lines and notices were not counted. Across the three orchestras and all kinds of concert, {n_all:,} works carry a name in the composer's place, and for {n_m:,} of them ({n_m / n_all:.1%}) the name was matched to the New York Philharmonic list. The other {n_all - n_m:,} carry names this procedure could not match to that list and keep the name as written in the source (Korean composers and film and musical composers who are not in the list, names that are in it but that we could not match, and names written where a composer would be that may not be a composer's, such as singers and bands, or the word Anonymous). "
                 f"{n_nc:,} lines that give a title without a composer, or whose composer could not be read, stay in the works table but enter no figure (such lines were not carried over exhaustively). Works and composers were taken only from what the sources say; nothing was filled in from elsewhere.</p>")
        b.append(f"<p><b>How names were matched, and the limits.</b> A name written in full was matched to the person of that name in the New York Philharmonic records. A family name alone was matched automatically only to the person who appears most often under that name in the New York Philharmonic records, and only if that person appears there at least 20 times (the 50 composers whose Korean names this site had already fixed were matched regardless). Other spellings were matched only after checking the title by hand (the table orch_kr_composer_alias.csv, on the Data page). "
                 f"Names shared by several composers (Strauss, Weber and Webber, Williams and others) were separated by words in the title, and left as written when that failed. A match says whom the name in the source refers to; it is not a check of who actually wrote the piece. "
                 f"Some lines could not be read by these rules, such as a name missing from the list with no separator before the title, or a misspelled name. Conversely, the rules read some words as a composer that are a title, a genre label or a performer credit in the source (a line that gives the title before the composer, or one that begins with \"film\" or with a singer's name followed by \"sung by\"). We went through every spelling that was not matched to a New York Philharmonic name and listed {n_nn} such words by hand (orch_kr_not_composer.csv, on the Data page). Of the {n_nn_kept + n_nn_note} lines read with them, the {n_nn_kept} that carry a title are kept as lines whose composer could not be read, and the {n_nn_note} notices were dropped. Other such words may remain. {n_skip} concerts in the {on('bucheon')} archive that are concerts of a chorus with no orchestra named among the performers were left out (judged by the title and the performer line of the page; the chorus was formerly called the Bucheon Philharmonic Chorus). Concerts such as recitals by chorus members, whose performer line names no ensemble, may remain. A subscription concert of the chorus in which the orchestra also played stays in the table but is not counted as a {on('bucheon')} subscription concert. "
                 f"Where several dates share one program cell in the Busan record book (tours, for example), the program is entered for each of those dates; encore lines and lines for activities within a concert (instrument try-outs, storytelling, comic sketches) were not counted. A line naming a composer and an arranger counts for the composer; a line naming only an arranger has no composer.</p>")
    b.append("<p class='src'>" + ("자료: " if k else "Data: ") +
             "<a href='http://www.artsuwon.or.kr/?p=12'>" + ("수원시립예술단 연간공연일정" if k else "Suwon City Arts Group, yearly concert listings") + "</a>; "
             "<a href='https://www.bucheonphil.or.kr/front/M0000030/event/list.do'>" + ("부천시립예술단 아카이브 「공연모음」" if k else "Bucheon City Arts Group, concert archive") + "</a>; "
             f"<a href='{BUSAN_URL}'>" + ("부산문화회관, 「부산시립교향악단 공연보(1962-2021)」" if k else "Busan Cultural Center, Busan Philharmonic record book 1962–2021") + "</a> "
             + ("(2026년 11월 17일에 읽었다. 곡목과 작곡가라는 사실만 표로 옮겼고, 공연 면과 공연보 자체는 싣지 않는다.)" if k else "(read on 17 November 2026; only the facts of works and composers were tabulated, and the pages and the booklet themselves are not reproduced).") + "</p>")
    return "".join(b)
