"""1.9 colour figures for romantic.html (design 62): key maps and a collection x metric heatmap.

Diverging key-signature scale: flats blue, sharps orange, no accidentals (or the home key's signature) grey.
Six steps per arm; OKLCH ramps checked with the dataviz validator (--ordinal: monotone lightness, visible
step gaps, light end >= 2:1 against the chart surface) for the light (#ffffff) and dark (#232428) cards.
Minor keys are hatched at 45 degrees rather than darkened, so mode never rests on colour alone.
"""
from __future__ import annotations

import html
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/derived"
KM_FILE = "keymaps_19.csv"

KEY_RAMPS = {
    "light": dict(p=["#dea279", "#ce8c5e", "#be7641", "#ae5f1f", "#9e4900", "#8d3200"],
                  m=["#98b3d7", "#7c9dc8", "#6087b9", "#4571aa", "#285c9b", "#02468b"], z="#c9c9c9"),
    "dark": dict(p=["#8a542d", "#a26940", "#ba7e54", "#d29368", "#eba97c", "#ffc091"],
                 m=["#385984", "#4c709e", "#6087b9", "#759fd5", "#8bb8f2", "#a1d1ff"], z="#55565a"),
}
ROLE = {"typical": ("전조 횟수가 중앙값에 가장 가까운 곡", "closest to the median number of key changes"),
        "most": ("전조가 가장 많은 곡", "most key changes"), "fewest": ("전조가 가장 적은 곡", "fewest key changes")}
NAME_KO = {"F": "바", "C": "다", "G": "사", "D": "라", "A": "가", "E": "마", "B": "나"}
HATCH = ("<defs><pattern id='kmhatch' width='6' height='6' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'>"
         "<line x1='0' y1='0' x2='0' y2='6' stroke='var(--fg)' stroke-opacity='.45' stroke-width='1.6'/></pattern></defs>")


def esc(s):
    return html.escape("" if s is None else str(s))


def step_class(v: float) -> str:
    v = int(max(-6, min(6, round(v))))
    return "z" if v == 0 else (f"p{v}" if v > 0 else f"m{-v}")


def css() -> str:
    def block(mode):
        r = KEY_RAMPS[mode]
        return ("".join(f"--kp{i + 1}:{c};" for i, c in enumerate(r["p"]))
                + "".join(f"--km{i + 1}:{c};" for i, c in enumerate(r["m"])) + f"--kz:{r['z']};")
    rules = []
    for c in ["z"] + [f"p{i}" for i in range(1, 7)] + [f"m{i}" for i in range(1, 7)]:
        var = "--kz" if c == "z" else f"--k{c}"
        rules.append(f"body:not([data-km=abs]) .kr-{c},body[data-km=abs] .ka-{c},.kh-{c}{{fill:var({var})}}")
    return ("<style>:root{" + block("light") + "}"
            "@media(prefers-color-scheme:dark){:root:not([data-theme=\"light\"]){" + block("dark") + "}}"
            ":root[data-theme=\"dark\"]{" + block("dark") + "}"
            + "".join(rules)
            + "body[data-km=abs] .km-rel,body:not([data-km=abs]) .km-abs{display:none}"
            ".km-toggle{display:flex;gap:.5rem;flex-wrap:wrap;margin:.6rem 0}"
            ".km-toggle button{font:inherit;font-size:.9rem;padding:.25rem .7rem;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg2);cursor:pointer}"
            ".km-toggle button[aria-pressed=true]{border-color:var(--accent);color:var(--fg);box-shadow:inset 0 -2px 0 var(--accent)}"
            ".km-lab{font-size:11px;fill:var(--fg);paint-order:stroke;stroke:var(--card);stroke-width:3px;stroke-linejoin:round}"
            "</style>")


JS = ("<script>(function(){var b=document.querySelectorAll('.km-toggle button');function set(m){document.body.setAttribute('data-km',m);"
      "b.forEach(function(x){x.setAttribute('aria-pressed',x.getAttribute('data-km')===m?'true':'false')})}"
      "b.forEach(function(x){x.addEventListener('click',function(){set(x.getAttribute('data-km'))})})})();</script>")


def key_name(tonic: int, minor: bool, lang: str) -> str:
    idx, acc = (tonic + 1) % 7, (tonic + 1) // 7
    letter = "FCGDAEB"[idx]
    if lang == "ko":
        pre = ("겹" if abs(acc) >= 2 else "") + ("올림" if acc > 0 else "내림" if acc < 0 else "")
        return f"{pre}{NAME_KO[letter]}{'단조' if minor else '장조'}"
    return f"{letter}{('♯' * acc) if acc > 0 else ('♭' * -acc)} {'minor' if minor else 'major'}"


def sig_text(v: int, lang: str) -> str:
    if v == 0:
        return "조표 없음" if lang == "ko" else "no accidentals"
    return f"{'♯' if v > 0 else '♭'}{abs(v)}"


def rel_text(v: int, lang: str) -> str:
    if v == 0:
        return "으뜸조와 같은 조표" if lang == "ko" else "same signature as the home key"
    if lang == "ko":
        return f"으뜸조보다 {'♯' if v > 0 else '♭'} 쪽으로 {abs(v)}칸"
    return f"{abs(v)} step{'s' if abs(v) > 1 else ''} to the {'sharp' if v > 0 else 'flat'} side of the home key"


def scale_legend(lang: str) -> str:
    k = lang == "ko"
    x0, cw = 230, 40
    cells = []
    for v in range(-6, 7):
        x = x0 + (v + 6) * cw
        rel = "0" if v == 0 else f"{v:+d}".replace("-", "−")
        ab = "0" if v == 0 else sig_text(v, lang)
        cells.append(f"<rect x='{x + 1}' y='4' width='{cw - 2}' height='16' rx='2' class='kh-{step_class(v)}'/>"
                     f"<text x='{x + cw / 2}' y='34' text-anchor='middle' class='km-lab km-rel'>{rel}</text>"
                     f"<text x='{x + cw / 2}' y='34' text-anchor='middle' class='km-lab km-abs'>{ab}</text>")
    hx = x0 + 13 * cw + 20
    side = f"<text x='{x0 - 8}' y='16' text-anchor='end' class='km-lab'>{'♭ 쪽 ← → ♯ 쪽' if k else 'flat side ← → sharp side'}</text>"
    minor = (f"<rect x='{hx}' y='4' width='{cw}' height='16' rx='2' class='kh-z'/><rect x='{hx}' y='4' width='{cw}' height='16' rx='2' fill='url(#kmhatch)'/>"
             f"<text x='{hx + cw + 8}' y='16' class='km-lab'>{'빗금 = 단조' if k else 'hatched = minor'}</text>")
    return f"<svg viewBox='0 0 900 42' width='100%' role='img' aria-label='{'조표 색 범례' if k else 'Key-signature colour legend'}'>{HATCH}{side}{''.join(cells)}{minor}</svg>"


def keymap_svg(df: pd.DataFrame, corpus: str, lang: str, label: str) -> str:
    k = lang == "ko"
    sub = df[df.corpus == corpus]
    pieces = list(dict.fromkeys(sub["piece_id"]))
    w, x0, bh, gap = 900, 230, 18, 8
    pw = w - x0 - 20
    h = 22 + len(pieces) * (bh + gap)
    out = [f"<text x='0' y='14' class='km-lab' style='font-weight:600'>{esc(label)}</text>"]
    for i, p in enumerate(pieces):
        g = sub[sub.piece_id == p]
        y = 22 + i * (bh + gap)
        role = ROLE[g["role"].iloc[0]][0 if k else 1]
        out.append(f"<text x='{x0 - 8}' y='{y + 13}' text-anchor='end' class='km-lab'><title>{esc(role)}</title>{esc(p)}</text>")
        total = float(g["length_qb"].iloc[0])
        for r in g.itertuples():
            xa, xb = x0 + pw * r.start_qb / total, x0 + pw * min(r.end_qb, total) / total
            wd = max(xb - xa - 1, 0.8)
            tip = (f"{r.mn_start}–{r.mn_end}{'마디' if k else ' (bars)'} · {r.localkey} · {key_name(r.tonic_abs, r.minor, lang)} · "
                   f"{'조표' if k else 'signature'} {sig_text(r.sig_abs, lang)} · {rel_text(r.sig_rel, lang)}")
            out.append(f"<rect x='{xa:.1f}' y='{y}' width='{wd:.1f}' height='{bh}' class='kr-{step_class(r.sig_rel)} ka-{step_class(r.sig_abs)}'><title>{esc(tip)}</title></rect>")
            if r.minor:
                out.append(f"<rect x='{xa:.1f}' y='{y}' width='{wd:.1f}' height='{bh}' fill='url(#kmhatch)' pointer-events='none'/>")
            if wd > 34:
                out.append(f"<text x='{xa + 4:.1f}' y='{y + 13}' class='km-lab' pointer-events='none'>{esc(r.localkey)}</text>")
    return f"<svg viewBox='0 0 {w} {h}' width='100%' role='img' aria-label='{esc(label)}'>{''.join(out)}</svg>"


def keymap_section(lang: str, label_of) -> str:
    """label_of(corpus) -> collection label in the page language."""
    import keymaps_19
    k = lang == "ko"
    df = pd.read_csv(D / KM_FILE)
    head = ("<p>악장 하나를 막대 하나로 그리고, DCML 주석자가 정한 국소 조가 이어지는 구간마다 색을 칠했다. 가로는 악장 안의 위치(처음→끝)다. "
            "곡집마다 세 곡을 미리 정한 규칙으로 골랐다: 전조 횟수가 곡집 중앙값에 가장 가까운 곡, 가장 많은 곡, 가장 적은 곡(곡 이름에 마우스를 올리면 어느 쪽인지 나온다). 구간에 마우스를 올리면 마디·조·조표가 나온다.</p>"
            if k else
            "<p>Each bar is one movement, coloured by the local keys annotated by DCML, from beginning to end. "
            "Three pieces per collection, chosen by a fixed rule: the one whose number of key changes is closest to the collection median, the one with the most and the one with the fewest (hover over a piece name to see which). Hover over a segment for its bars, key and signature.</p>")
    toggle = ("<div class='km-toggle' role='group' aria-label='" + ("색 기준" if k else "Colour basis") + "'>"
              f"<button type='button' data-km='rel' aria-pressed='true'>{'으뜸조와의 거리로 칠하기' if k else 'Colour by distance from the home key'}</button>"
              f"<button type='button' data-km='abs' aria-pressed='false'>{'실제 조로 칠하기' if k else 'Colour by the actual key'}</button></div>")
    cap = ("<p class='src'><span class='km-rel'>"
           + ("지금 색은 <b>으뜸조와의 거리</b>다. 으뜸조와 조표가 같은 조(으뜸조와 그 나란한조)는 회색, 딸림조 쪽(♯ 방향)은 주황, 버금딸림조 쪽(♭ 방향)은 파랑이며, 멀수록 바탕과의 대비가 커진다(밝은 화면에서는 진해지고 어두운 화면에서는 밝아진다). 곡끼리 전조의 모양을 견주기 좋다."
              if k else "Colour now shows <b>distance from the home key</b>. Keys with the home key's signature (the home key and its relative) are grey, the dominant side (sharp direction) orange, the subdominant side (flat direction) blue, with more contrast against the background the further away (darker on a light screen, lighter on a dark one). Good for comparing the shape of modulation across pieces.")
           + "</span><span class='km-abs'>"
           + ("지금 색은 <b>실제 조</b>다. 조표 없는 조(다장조·가단조)가 회색이고, 올림표가 많을수록 주황, 내림표가 많을수록 파랑의 대비가 커진다. 곡마다 출발 색이 다르다."
              if k else "Colour now shows <b>the actual key</b>. Keys without accidentals (C major, A minor) are grey; more sharps, stronger orange; more flats, stronger blue. Each piece starts from its own colour.")
           + "</span> " + ("어느 쪽이든 색의 배열은 같은 5도권이고 기준점만 다르다. 색은 이명동음을 접지 않은 조표 차이고(올림바장조 +6, 내림사장조 −6), 여섯 칸을 넘는 조는 끝 칸으로 칠했다. 지표 「전조 거리」는 이명동음을 접어 0~6으로 세므로 색의 칸 수와 다를 수 있다. 0마디는 못갖춘마디다. 곡을 고를 때 동률이면 곡 번호 순으로 앞의 것을 골랐다."
                           if k else "Either way the colours follow the same circle of fifths; only the reference point differs. Colour uses the signature difference without enharmonic folding (F♯ major +6, G♭ major −6); keys beyond six steps take the end step. The metric 'key-change distance' folds enharmonically to 0–6, so it can differ from the number of colour steps. Bar 0 is a pickup bar. Ties in choosing pieces go to the lower piece number.") + "</p>")
    note = ("<p class='src'>" + ("국소 조는 DCML 주석자가 정한 것이다. 같은 악보라도 분석가에 따라 전조의 경계를 다르게 그을 수 있다. "
                                 "색은 5도권의 거리를 색의 거리로 옮긴 부호일 뿐, 어떤 조가 본래 어떤 색이라는 주장이 아니다. 스크랴빈이 『프로메테우스』에 쓴 색 건반(clavier à lumières)과 DCML 연구실의 Wavescapes(Viaccoz 외 2023)도 5도권을 따라 색을 배치했고, 장조를 밝게·단조를 어둡게 느끼는 연상은 Palmer 외(2013)의 실험에서 보고되었다. "
                                 "여기서는 파랑·주황 두 색과 회색으로 된 발산형 척도를 썼다. 같은 단계의 주황·파랑은 제1·2색맹 모의(Machado 외 2009)에서 OKLab ΔE 13~20만큼 떨어진다(기준 8 이상). 다만 밝은 화면의 가장 연한 단계(±1)는 정상 시각에서도 차이가 14.8로 작아, 툴팁과 범례 숫자로 보완한다. 사용자 시험은 하지 않았다. 단조는 명도를 바꾸지 않고 빗금으로 표시했다."
                                 if k else "Local keys are the DCML annotators'. Another analyst could draw the boundaries of a modulation differently. "
                                 "The colours encode distance on the circle of fifths; they make no claim that a key has a colour of its own. the colour keyboard (clavier à lumières) of Scriabin's Prometheus and the DCML lab's Wavescapes (Viaccoz et al. 2023) also laid out colour along the circle of fifths, and Palmer et al. (2013) report that people associate major with lighter and minor with darker colours. "
                                 "Here a diverging scale of two hues (blue, orange) and grey is used. Orange and blue of the same step are OKLab ΔE 13–20 apart under simulated protanopia and deuteranopia (Machado et al. 2009; target 8 or more). The palest steps (±1) on a light screen differ by only 14.8 even for normal vision, so tooltips and the legend's numbers back them up. No user testing was done. Minor keys are hatched rather than darkened.") + "</p>")
    blocks = []
    for part, corpora in ((("건반 곡집" if k else "Keyboard collections"), keymaps_19.KEYBOARD),
                          (("현악 4중주" if k else "String quartets"), keymaps_19.QUARTETS)):
        blocks.append(f"<h3 style='margin:1rem 0 .3rem'>{part}</h3>")
        for c in corpora:
            if c in set(df.corpus):
                blocks.append(f"<figure style='margin:.2rem 0'>{keymap_svg(df, c, lang, label_of(c))}</figure>")
    return head + toggle + scale_legend(lang) + cap + "".join(blocks) + note


def heatmap(rows: pd.DataFrame, mids: list[str], names: list[str], labels: list[str], fmts: list[str], lang: str) -> str:
    """rows: one row per collection with a column per metric; z per metric over these rows; half an SD per step."""
    k = lang == "ko"
    rows = rows.reset_index(drop=True)
    x0, y0, ch = 150, 84, 24
    cw = (900 - x0) / len(mids)
    h = y0 + len(rows) * ch + 8
    out = []
    for j, nmj in enumerate(names):
        x = x0 + j * cw + cw / 2
        out.append(f"<text x='{x:.1f}' y='{y0 - 8}' text-anchor='start' transform='rotate(-28 {x:.1f} {y0 - 8})' class='km-lab'>{esc(nmj)}</text>")
    for i in range(len(rows)):
        y = y0 + i * ch
        out.append(f"<text x='{x0 - 8}' y='{y + 16}' text-anchor='end' class='km-lab'>{esc(labels[i])}</text>")
        for j, mid in enumerate(mids):
            col = rows[mid].astype(float)
            sd = col.std(ddof=0)
            v = rows.loc[i, mid]
            if pd.isna(v) or not sd:
                continue
            z = (v - col.mean()) / sd
            x = x0 + j * cw
            tip = f"{labels[i]} · {names[j]}: {format(v, fmts[j])} (z = {z:+.2f})".replace("-", "−")
            out.append(f"<rect x='{x + 1:.1f}' y='{y + 1}' width='{cw - 2:.1f}' height='{ch - 2}' rx='2' class='kh-{step_class(z * 2)}'><title>{esc(tip)}</title></rect>"
                       f"<text x='{x + cw / 2:.1f}' y='{y + 16}' text-anchor='middle' class='km-lab' pointer-events='none'>{format(v, fmts[j])}</text>")
    return f"<svg viewBox='0 0 900 {h}' width='100%' role='img' aria-label='{'곡집별 중앙값 열지도' if k else 'Heatmap of collection medians'}'>{''.join(out)}</svg>"


def heat_legend(lang: str, n: int) -> str:
    k = lang == "ko"
    x0, cw = 230, 40
    cells = "".join(f"<rect x='{x0 + (v + 6) * cw + 1}' y='4' width='{cw - 2}' height='14' rx='2' class='kh-{step_class(v)}'/>" for v in range(-6, 7))
    return (f"<svg viewBox='0 0 900 40' width='100%' role='img' aria-label='{'열지도 범례' if k else 'Heatmap legend'}'>"
            f"<text x='{x0 - 8}' y='15' text-anchor='end' class='km-lab'>{f'{n}개 곡집 평균보다 낮음' if k else f'below the mean of {n} collections'}</text>{cells}"
            f"<text x='{x0 + 13 * cw + 8}' y='15' class='km-lab'>{'높음' if k else 'above'}</text>"
            f"<text x='{x0 + 6.5 * cw}' y='34' text-anchor='middle' class='km-lab'>{'한 칸 = 표준편차 0.5' if k else 'one step = half a standard deviation'}</text></svg>")
