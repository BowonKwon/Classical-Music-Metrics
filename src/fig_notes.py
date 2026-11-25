"""Chart notes (1.22.3): a line above each chart saying what it draws, and labelled paragraphs under it —
in short, how the chart works, reading one value, easy to misread, terms.

Every number in these sentences is computed here or by the page module from the same lists the chart is drawn
from; nothing is typed in by hand. The notes explain; they do not change a value, a rule or a claim. Charts drawn
in a series from one template (the metric pages, the composer pages, the rows of the scales page) get their notes
from one function each, with the values of that chart filled in.
"""
from __future__ import annotations

import html
import math

import axis
import takeaways

MINUS = "−"
LAB = {"ko": {"short": "한눈에", "how": "그림 보는 법", "one": "숫자 하나 읽어 보기", "nums": "수로 보면", "mis": "잘못 읽기 쉬운 것", "terms": "낱말 풀이"},
       "en": {"short": "In short", "how": "How the chart works", "one": "Reading one value", "nums": "The numbers", "mis": "Easy to misread", "terms": "Terms"}}
ORDER = ("short", "how", "one", "nums", "mis", "terms")
CSS = (" .fi{font-size:.92rem;color:var(--fg2);margin:0 0 .5rem;line-height:1.55}"
       " figcaption .cp{margin:.45rem 0 0} figcaption .cp:first-child{margin-top:0} figcaption .cp b{color:var(--fg);margin-right:.35rem}"
       " .fnotes{font-size:.86rem;color:var(--fg2);line-height:1.5;margin:.4rem 0 1rem} .fnotes .cp{margin:.4rem 0 0}"
       " .fnotes .cp b{color:var(--fg);margin-right:.35rem} .fnotes summary{cursor:pointer;color:var(--fg);font-weight:600;margin:.2rem 0}"
       " :lang(ko) .fi,:lang(ko) .fnotes{word-break:keep-all;overflow-wrap:anywhere}")


def esc(s) -> str:
    return html.escape(str(s), quote=False)


def parts_html(parts, lang: str) -> str:
    """Labelled paragraphs in the fixed order. parts: dict key -> HTML text (or list of pairs); empty texts are left out."""
    d = dict(parts)
    return "".join(f'<p class="cp"><b>{LAB[lang][k]}</b> {d[k].strip()}</p>' for k in ORDER if d.get(k) and d[k].strip())


def fx(svg: str, intro: str, parts, lang: str, attrs: str = "", after_svg: str = "") -> str:
    """A chart with its line above and its labelled paragraphs below (HTML strings; the caller escapes)."""
    if not svg:
        return ""
    return f'<figure{attrs}><p class="fi">{intro}</p>{svg}{after_svg}<figcaption>{parts_html(parts, lang)}</figcaption></figure>'


SUMMARY = {"ko": "이 그림들을 읽는 법 (눌러서 펼치기)", "en": "How to read these charts (click to open)"}


def block(intro: str, parts, lang: str) -> str:
    """Notes for a set of small charts drawn from one template (no <figure> of their own): the line once, and the
    shared paragraphs folded under it (v1 4.02 — the charts are not pushed down the screen by a long explanation)."""
    return f'<div class="fnotes"><p class="fi">{intro}</p><details><summary>{SUMMARY[lang]}</summary>{parts_html(parts, lang)}</details></div>'


def tr(lang, ko, en):
    return ko if lang == "ko" else en


# ----------------------------------------------------------------- numbers
def num(v, spec: str) -> str:
    """A value in the chart's format, real minus sign."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    return format(v, spec).replace("-", MINUS)


def med_num(v, spec: str) -> str:
    """A median in the chart's format (one more decimal when an integer metric lands on a half)."""
    return axis.num(v, spec)


def season(x) -> str:
    """Season label from its start year: 1842 -> 1842–43."""
    x = int(x)
    return f"{x}–{str(x + 1)[-2:]}"


def median(vs) -> float:
    return axis._median(vs)


def _clean(vs):
    return sorted(float(v) for v in vs if v == v)


# ----------------------------------------------------------------- strip plots (one dot per item, one row per group)
STRIP_MIS = {
    "ko": "줄 안에서 점이 위아래로 흩어진 것은 값이 아니다. 겹침을 줄이려고 줄 안에서 위아래로 조금 옮겼을 뿐이고, 그래도 겹치는 점이 있다. 줄마다 점의 수가 다르므로, 점이 빽빽한 줄이 값이 큰 줄은 아니다.",
    "en": "The up-and-down scatter of dots within a row is not a value; dots are only moved a little up or down within the row to reduce overlap, and some still overlap. Rows have different numbers of dots, so a crowded row is not a row with larger values.",
}
MEDIAN_TERM = {
    "ko": "중앙값 — 값을 크기 순으로 늘어놓았을 때 한가운데 값(개수가 짝수면 가운데 두 값의 평균). 몇 개의 튀는 값에 덜 끌려간다.",
    "en": "Median — the middle value when the values are put in order (the mean of the two middle ones for an even count); a few extreme values move it little.",
}
QUART_TERM = {
    "ko": "1사분위·3사분위 — 값을 크기 순으로 늘어놓았을 때 아래에서 4분의 1, 4분의 3 되는 자리의 값. 그 사이에 가운데 절반이 들어 있다.",
    "en": "First and third quartile — the values a quarter and three quarters of the way up the ordered values; the middle half lies between them.",
}


def plural_en(unit: str) -> str:
    """'movement' -> 'movements'; 'movement or piece' -> 'movements or pieces' (v1 4.05)."""
    return " or ".join(w + "s" for w in unit.split(" or "))


def strip_one(groups, spec: str, lang: str, unit_ko: str = "악장", unit_en: str = "movement") -> str:
    """Read the top row of a strip plot: number of dots, its median bar, its range."""
    for name, vs, *_ in groups:
        v = _clean(vs)
        if len(v) >= 2:
            m = median(v)
            if lang == "ko":
                return (f"맨 위 「{esc(name)}」 줄에는 점이 {len(v):,}개 있다. 굵은 세로 막대(중앙값)가 {med_num(m, spec)}에 있으니, 이 줄 {unit_ko}의 절반은 이 값보다 작거나 같고 "
                        f"절반은 크거나 같다. 가장 왼쪽 점은 {num(v[0], spec)}, 가장 오른쪽 점은 {num(v[-1], spec)}{axis.kp(num(v[-1], spec), '이다', '다')}.")
            return (f"The top row, '{esc(name)}', has {len(v):,} dots. Its thick vertical bar (the median) sits at {med_num(m, spec)}: half of its {plural_en(unit_en)} are at or below that value "
                    f"and half at or above. The leftmost dot is {num(v[0], spec)}, the rightmost {num(v[-1], spec)}.")
    return ""


def strip_how(lang: str, unit_ko: str = "악장", unit_en: str = "movement", row_ko: str = "", row_en: str = "") -> str:
    if lang == "ko":
        return (f"점 하나가 {unit_ko} 하나다. 줄 하나가 {row_ko or '한 묶음'}이고, 가로 위치가 그 {unit_ko}의 값이다(아래 축 이름에 오른쪽일수록 무엇인지 적었다). "
                f"줄마다 있는 굵은 세로 막대가 그 줄의 중앙값이다. 점에 마우스를 대거나 누르면 값이 뜬다.")
    return (f"Each dot is one {unit_en}. Each row is {row_en or 'one group'}; the horizontal position is the value (the axis title below says what further right means). "
            f"The thick vertical bar in each row is that row's median. Hover over or tap a dot to see its value.")


# ----------------------------------------------------------------- bar charts (one bar per item)
def tied_names(names, lang: str, unit_ko: str = "개", unit_en: str = "") -> str:
    """Names tied at an extreme (v1 2.02): one name as it is; two to five all named with a 'tied' mark;
    more than five, the first three and the count."""
    ns = [esc(n) for n in names]
    sep = "·" if lang == "ko" else ", "
    if len(ns) == 1:
        return ns[0]
    if len(ns) <= 5:
        return sep.join(ns) + tr(lang, " 공동", " (tied)")
    return tr(lang, f"{sep.join(ns[:3])} 등 {len(ns)}{unit_ko} 공동", f"{sep.join(ns[:3])} and {len(ns) - 3} more{(' ' + unit_en) if unit_en else ''} (tied)")


def display_ties(pairs, x, spec: str, lang: str, fmt=None) -> str:
    """v1 2.03: names whose value is not exactly the extreme but prints the same at the precision shown."""
    f = fmt or (lambda v: num(v, spec))
    ns = [esc(n) for n, v in pairs if v != x and f(v) == f(x)]
    if not ns:
        return ""
    sep = "·" if lang == "ko" else ", "
    lst = sep.join(ns[:3]) + (tr(lang, f" 등 {len(ns)}개", f" and {len(ns) - 3} more") if len(ns) > 3 else "")
    return tr(lang, f" 표시한 자릿수({f(x)})로는 {lst}도 같다.", f" At the precision shown ({f(x)}), the same value also appears for {lst}.")


def bars_extremes(items, spec: str, lang: str) -> str:
    """Largest and smallest bar (exact ties named together; display-precision ties said after)."""
    vals = [(n, v) for n, v, *_ in items if v == v]
    if len(vals) < 2:
        return ""
    hi, lo = max(v for _, v in vals), min(v for _, v in vals)

    def who(x):
        return tied_names([n for n, v in vals if v == x], lang)
    return tr(lang, f"가장 큰 값은 {who(hi)}({num(hi, spec)}), 가장 작은 값은 {who(lo)}({num(lo, spec)}){axis.kp(who(lo), '이다', '다')}.",
              f"The largest value is {who(hi)} ({num(hi, spec)}); the smallest is {who(lo)} ({num(lo, spec)}).".replace(" (tied) (", " (tied, ")) + display_ties(vals, hi, spec, lang) + display_ties(vals, lo, spec, lang)


# ----------------------------------------------------------------- line charts
def line_points(pts):
    return [(x, y) for x, y in pts if y == y]


def line_short(series, spec: str, lang: str, xlab=lambda x: str(x), names=True) -> str:
    """For each line: its first and last point and its highest point."""
    out = []
    for name, pts, *_ in series:
        p = line_points(pts)
        if len(p) < 2:
            continue
        (fx_, fy), (lx, ly) = p[0], p[-1]
        hy = max(y for _, y in p)
        hxs = [xlab(x) for x, y in p if y == hy]
        who = (f"「{esc(name)}」 선은 " if lang == "ko" else f"The '{esc(name)}' line ") if names else ("값은 " if lang == "ko" else "The value ")
        dt = display_ties([(xlab(x), y) for x, y in p], hy, spec, lang)
        if len(hxs) > 1:   # v1 2.10: a highest value reached more than once names every place
            top = tr(lang, f"가장 높은 값은 {num(hy, spec)}이고, {tied_names(hxs, lang).removesuffix(' 공동')}{axis.kp(tied_names(hxs, lang).removesuffix(' 공동'), '이', '가')} 함께 그 값이다.",
                     f"its highest value is {num(hy, spec)}, shared by {tied_names(hxs, lang).removesuffix(' (tied)')}.")
        else:
            top = tr(lang, f"가장 높은 값은 {hxs[0]}의 {num(hy, spec)}{axis.kp(num(hy, spec), '이다', '다')}.", f"its highest value is {num(hy, spec)}, in {hxs[0]}.")
        if lang == "ko":
            out.append(f"{who}{xlab(fx_)} {num(fy, spec)}에서 {xlab(lx)} {num(ly, spec)}{axis.ro(num(ly, spec))} 간다. {top}{dt}")
        else:
            out.append(f"{who}goes from {num(fy, spec)} in {xlab(fx_)} to {num(ly, spec)} in {xlab(lx)}; {top}{dt}")
    return " ".join(out)


def line_one(series, spec: str, lang: str, xlab=lambda x: str(x), what_ko: str = "", what_en: str = "") -> str:
    """Read the highest point of the first line."""
    for name, pts, *_ in series:
        p = line_points(pts)
        if not p:
            continue
        hy = max(y for _, y in p)
        hx_all = [x for x, y in p if y == hy]
        hx = hx_all[0]
        if len(hx_all) > 1:   # v1 2.10: a tied highest point is read out with all its places
            whr = tied_names([xlab(x) for x in hx_all], lang)
            return tr(lang, f"「{esc(name)}」 선의 가장 높은 점은 {whr.removesuffix(' 공동')}에 함께 있고 값은 {num(hy, spec)}{axis.kp(num(hy, spec), '이다', '다')}.",
                      f"The highest points of the '{esc(name)}' line are at {whr.removesuffix(' (tied)')}, value {num(hy, spec)}.")
        if lang == "ko":
            return f"「{esc(name)}」 선의 가장 높은 점은 {xlab(hx)}에 있고 값은 {num(hy, spec)}{axis.kp(num(hy, spec), '이다', '다')}{(' — ' + what_ko.format(v=num(hy, spec), x=xlab(hx))) if what_ko else ''}."
        return f"The highest point of the '{esc(name)}' line is at {xlab(hx)}, value {num(hy, spec)}{('; ' + what_en.format(v=num(hy, spec), x=xlab(hx))) if what_en else ''}."
    return ""


def pct(v, d: int = 1) -> str:
    return format(float(v), f".{d}%")


def season_of(label) -> str:
    return takeaways.season(label)


def strip_parts(groups, spec: str, lang: str, unit_ko="악장", unit_en="movement", row_ko="", row_en="",
                how_extra="", mis_extra="", full=True, scope=False, coll_ko="곡집", coll_en="collection") -> dict:
    """Notes for one strip plot. full=False leaves out the paragraphs a block above the series already gives."""
    p = {"short": esc(axis.strip_note(groups, spec, lang, coll_ko, coll_en, scope=scope)),
         "one": strip_one(groups, spec, lang, unit_ko, unit_en)}
    if full:
        p["how"] = strip_how(lang, unit_ko, unit_en, row_ko, row_en) + (" " + how_extra if how_extra else "")
        p["mis"] = STRIP_MIS[lang] + (" " + mis_extra if mis_extra else "")
        p["terms"] = MEDIAN_TERM[lang]
    else:
        if how_extra:
            p["how"] = how_extra
        if mis_extra:
            p["mis"] = mis_extra
    return p


def strip_block(lang: str, intro: str, unit_ko="악장", unit_en="movement", row_ko="", row_en="", how_extra="", mis_extra="") -> str:
    """The shared paragraphs for a series of strip plots, once above the series."""
    return block(intro, {"how": strip_how(lang, unit_ko, unit_en, row_ko, row_en) + (" " + how_extra if how_extra else ""),
                         "mis": STRIP_MIS[lang] + (" " + mis_extra if mis_extra else ""), "terms": MEDIAN_TERM[lang]}, lang)


def bars_one(items, spec: str, lang: str, what_ko="", what_en="") -> str:
    """Read the first bar."""
    for n, v, *_ in items:
        if v == v:
            if lang == "ko":
                return f"맨 위 막대 「{esc(n)}」의 값은 {num(v, spec)}{axis.kp(num(v, spec), '이다', '다')}{(' — ' + what_ko.format(v=num(v, spec))) if what_ko else ''}."
            return f"The top bar, '{esc(n)}', is {num(v, spec)}{('; ' + what_en.format(v=num(v, spec))) if what_en else ''}."
    return ""


# ----------------------------------------------------------------- metric pages (one template per kind of table)
def metric_score(groups, m, lang, missing_txt: str) -> tuple[str, dict]:
    """The by-collection strip plot of a score metric page."""
    name = m[lang]["name"]
    intro = tr(lang, f"{esc(name)}의 값을 악장마다 점 하나로 찍어, 작곡가와 모음별로 한 줄씩 늘어놓은 그림이다.",
               f"{esc(name)} for every movement, one dot each, with one row per composer and collection.")
    mis = tr(lang, "줄 사이에는 작곡가만 다른 것이 아니라 편성·장르·주석자도 다르다. 코랄과 피아노 소나타의 차이를 작곡가의 차이로만 읽을 수 없다.",
             "Rows differ in instruments, genre and annotators as well as in composer, so a gap between the chorales and the piano sonatas cannot be read as a difference between composers alone.")
    p = strip_parts(groups, m["fmt"], lang, "악장", "movement", "한 작곡가의 한 모음(색은 작곡가, 위 범례)", "one collection by one composer (color = composer, legend above)",
                    how_extra=missing_txt, mis_extra=mis, coll_ko="모음", coll_en="collection")
    return intro, p


def metric_strip_more(groups, m, lang, intro_ko, intro_en, unit_ko="악장", unit_en="movement", how_ko="", how_en="", mis_ko="", mis_en="") -> tuple[str, dict]:
    """A further strip plot on a metric page (keyboard sonatas, Romantic pieces, string quartets): the shared
    paragraphs are under the first chart of the page, so this one says what it draws and what it shows."""
    p = strip_parts(groups, m["fmt"], lang, unit_ko, unit_en, full=False, how_extra=tr(lang, how_ko, how_en) or tr(lang, "읽는 법은 이 면 맨 위 그림과 같다 — 점 하나가 악장 하나, 굵은 세로 막대가 중앙값.", "Read it like the first chart on this page: one dot per movement, the thick vertical bar is the median."),
                    mis_extra=tr(lang, mis_ko, mis_en))
    return tr(lang, intro_ko, intro_en), p


BPM_TERM = {"ko": "bpm — 1분에 치는 박의 수(beats per minute). 여기서는 녹음의 악장 끝부분(코다) 한 구간에서 템포 추정기로 잰 템포에서 베토벤의 메트로놈 표기를 뺀 차이라, −12면 그 구간이 표기보다 1분에 12박 느리다는 뜻이다. 악장 전체의 템포를 잰 값이 아니다.",
            "en": "bpm — beats per minute. Here it is the tempo estimated by a tempo tracker in one passage at the end of the movement (the coda) minus Beethoven's metronome mark, so −12 means that passage runs twelve beats a minute slower than the mark. It is not a tempo for the whole movement."}
STYLE_TERM = {"ko": "시대연주 — 작곡 당시의 악기와 연주 관행을 따르려는 연주(historically informed performance). 세 갈래 분류는 원자료에 적힌 그대로다.",
              "en": "HIP — historically informed performance, which tries to follow the instruments and practice of the composer's time. The three groups are the classification given in the source data."}


def metric_coda(items, lang, n_mov: str, faster_n: int, faster_of: int, years=True) -> tuple[str, dict]:
    """Bars of conductor medians of (measured − mark). items: (label, value, color slot)."""
    n = len(items)
    slower = sum(1 for _, v, *_ in items if v < 0)
    first = items[0]
    intro = tr(lang, f"지휘자 {n}명의 베토벤 교향곡 1~8번 녹음에서 악장 끝부분(코다)에서 잰 템포가 메트로놈 표기보다 얼마나 느린지(또는 빠른지), {n_mov}악장의 중앙값을 지휘자마다 막대 하나로 그린 그림이다.",
               f"How much slower (or faster) than Beethoven's metronome marks the tempo measured at the end of each movement (the coda) is in the Symphony 1–8 recordings of each of {n} conductors: the median over {n_mov} movements, one bar per conductor.")
    v = num(first[1], "+.1f")
    p = {"short": bars_extremes(items, "+.1f", lang) + (tr(lang, f" {n}명 모두의 막대가 0보다 왼쪽(표기보다 느림)에 있다.", f" All {n} bars lie left of zero (slower than the mark).") if slower == n else
                                                       tr(lang, f" {n}명 가운데 {slower}명의 막대가 0보다 왼쪽(표기보다 느림)에 있다.", f" {slower} of the {n} bars lie left of zero (slower than the mark).")),
         "how": tr(lang, f"막대 하나가 지휘자 하나다. 막대 끝의 값은 그 지휘자의 {n_mov}악장 값(측정한 템포 − 표기, bpm)의 중앙값이다. 세로선 0이 표기대로이고, 왼쪽으로 갈수록 표기보다 느리다. 0보다 오른쪽(표기보다 빠름)에 막대가 없으면 가로축이 0 근처에서 끝난다. 색은 연주 양식(위 범례){', 괄호 안은 양식과 녹음 연도다' if years else ', 괄호 안은 양식이다'}.",
                   f"Each bar is one conductor. Its end is the median, over {n_mov} movements, of measured tempo minus the mark, in bpm. The vertical line at 0 is the mark itself; further left is slower. When no bar lies right of 0 (faster than the mark), the axis ends near 0. Color is the performance style (legend above); in brackets, the style{' and the recording year' if years else ''}."),
         "one": tr(lang, f"맨 위 막대 「{esc(first[0])}」는 {v}{axis.kp(v, '이다', '다')}. 이 지휘자의 {n_mov}악장 값을 늘어놓으면 한가운데가 표기보다 1분에 {num(abs(first[1]), '.1f')}박 {'느리다' if first[1] < 0 else '빠르다'}는 뜻이다.",
                   f"The top bar, '{esc(first[0])}', is {v}: the middle of this conductor's {n_mov} movement values is {num(abs(first[1]), '.1f')} beats a minute {'slower' if first[1] < 0 else 'faster'} than the mark."),
         "mis": tr(lang, f"막대는 악장 값들의 가운데 값이다. 한 지휘자의 모든 악장이 막대만큼 느린 것은 아니다. 지휘자·악장 조합 하나하나로 보면 {faster_of:,}건 가운데 {faster_n}건은 표기보다 빠르다. 값은 악장 끝 구간 하나에서 잰 템포라, 악장 전체가 그만큼 느렸다는 뜻은 아니다.",
                   f"A bar is the middle of the movement values; not every movement of that conductor is that slow. Taken one conductor-movement pair at a time, {faster_n} of {faster_of:,} are faster than the mark. The tempo comes from one passage at the end of each movement, so it does not say the whole movement was that slow."),
         "terms": BPM_TERM[lang] + " " + STYLE_TERM[lang]}
    return intro, p


def metric_duration(items, lang, n_cond: int) -> tuple[str, dict]:
    """Bars of movement medians of (actual duration ÷ metronome duration)."""
    over = sum(1 for _, v, *_ in items if v > 1)
    first = items[0]
    intro = tr(lang, f"베토벤 교향곡 악장 {len(items)}개마다, 녹음의 트랙 길이가 메트로놈 표기대로 반복 없이 연주했다고 계산한 시간의 몇 배인지 그린 그림이다.",
               f"For each of {len(items)} movements of Beethoven's symphonies, the recorded track duration divided by the duration computed for playing at the metronome mark without repeats.")
    p = {"short": bars_extremes(items, ".2f", lang) + tr(lang, f" {len(items)}악장 가운데 {over}악장이 1보다 크다(표기보다 오래 걸린다).", f" {over} of the {len(items)} movements are above 1 (take longer than the mark)."),
         "how": tr(lang, f"막대 하나가 악장 하나다(교향곡 번호/악장 번호, 빠르기말, 메트로놈 표기 숫자 MM). 표기 숫자가 어느 음표의 박인지는 악장마다 다르고 이 자료에는 숫자만 있다. 이론 시간은 악보의 구간마다 (첫째 괄호 마디를 뺀 마디 수) × 마디당 박 수 ÷ MM 으로 분을 구해 더하고, 60을 곱해 초로 바꾼 값이다. 값은 지휘자 {n_cond}명의 (트랙 길이 ÷ 반복 없이 계산한 이론 시간) 중앙값이다. 1이면 이론 시간과 같고, 1.10이면 그보다 10% 오래 걸린다.",
                   f"Each bar is one movement (symphony/movement, tempo word, metronome number MM). Which note value the number counts differs from movement to movement, and the data hold the number only. The theoretical time adds up, section by section of the score, (bars less any first-ending bars) × beats per bar ÷ MM in minutes, times 60 for seconds. The value is the median over {n_cond} conductors of track length ÷ the theoretical time without repeats. 1 means the same as that time; 1.10 means 10% longer."),
         "one": tr(lang, f"맨 위 막대 「{esc(first[0])}」는 {num(first[1], '.2f')}배다. 지휘자들의 가운데 값이 반복 없이 표기대로 계산한 시간보다 {num((first[1] - 1) * 100, '.0f')}% 길다는 뜻이다.",
                   f"The top bar, '{esc(first[0])}', is {num(first[1], '.2f')}: the conductors' middle value takes {num((first[1] - 1) * 100, '.0f')}% longer than the time computed at the mark without repeats."),
         "mis": tr(lang, "막대는 0에서 시작하므로 길이 차이가 작아 보인다. 1(이론 시간과 같음)에서 얼마나 떨어졌는지는 눈금으로 읽는다. 시간의 비율이지 템포의 비율이 아니다. 도돌이표를 지킨 연주, 페르마타·쉼·트랙 앞뒤의 무음도 값을 키우므로, 2배가 「템포가 절반」이라는 뜻은 아니다. 반복을 지켰다고 본 값은 아래 표의 다른 칸에 있다.",
                   "Bars start at 0, so differences look small; read the distance from 1 (equal to the theoretical time) on the scale. This is a ratio of times, not of tempos: repeats taken, fermatas, rests and silence at the ends of a track all make it larger, so 2 does not mean 'half the tempo'. The value assuming repeats are taken is in another column of the table below.")}
    return intro, p


def metric_asap(groups, m, lang, cap: str) -> tuple[str, dict]:
    name = m[lang]["name"]
    intro = tr(lang, f"{esc(name)}{axis.kp(name, '을', '를')} 피아노 곡마다 점 하나로 찍어, 바흐와 베토벤으로 한 줄씩 나눈 그림이다.",
               f"{esc(name)} for each piano piece, one dot each, with a row for Bach and a row for Beethoven.")
    p = strip_parts(groups, m["fmt"], lang, "곡", "piece", "작곡가 하나", "one composer", how_extra=cap,
                    mis_extra=tr(lang, "현대 피아노 연주를 MIDI 로 기록한 ASAP 자료에서 잰 값이다. MAESTRO 와 이어진 파일은 국제 피아노 e-콩쿠르 연주이고, 이어지지 않은 파일의 출처는 이 자료로 따로 확인하지 않았다.",
                                 "These values are measured on the ASAP set of MIDI records of modern-piano performances. Files linked to MAESTRO are International Piano-e-Competition performances; the source of the other files was not checked separately here."))
    return intro, p


def metric_trend(pts, lang, slope: str, n: int) -> tuple[str, dict]:
    """Scatter of conductor medians against the recording year. pts: (year, value, color, label)."""
    s = sorted(pts, key=lambda p: p[0])
    lo, hi = s[0], s[-1]
    intro = tr(lang, f"지휘자 {n}명마다 녹음 연도와, 악장 끝부분(코다)에서 잰 템포와 표기의 차(측정 − 표기)를 점 하나로 찍은 그림이다.",
               f"Recording year against the difference between the tempo measured at the end of each movement (the coda) and the mark (measured − mark), one dot for each of {n} conductors.")
    p = {"short": tr(lang, f"가장 이른 녹음은 {esc(lo[3].split(' (')[0])}({num(lo[0], '.0f')}년, {num(lo[1], '+.1f')} bpm), 가장 늦은 녹음은 {esc(hi[3].split(' (')[0])}({num(hi[0], '.0f')}년, {num(hi[1], '+.1f')} bpm)이다. 점선의 기울기는 10년당 {slope} bpm이다.",
                     f"The earliest recording is {esc(lo[3].split(' (')[0])} ({num(lo[0], '.0f')}, {num(lo[1], '+.1f')} bpm), the latest {esc(hi[3].split(' (')[0])} ({num(hi[0], '.0f')}, {num(hi[1], '+.1f')} bpm). The dashed line changes by {slope} bpm per decade."),
         "how": tr(lang, "점 하나가 지휘자(전집 녹음) 하나다. 가로는 녹음 기간의 가운데 해, 세로는 그 지휘자의 악장 값(측정한 템포 − 표기, bpm)의 중앙값이다. 0의 가로선이 표기대로이고 아래로 갈수록 느리다. 색은 연주 양식(위 범례). 점선은 같은 악장 안에서 잰 기울기를 지휘자 평균점에 맞춰 그은 것이다.",
                   "Each dot is one conductor (one complete cycle). Across: the middle year of the recording dates; up: the conductor's median over movements of measured tempo minus the mark, in bpm. The horizontal line at 0 is the mark; lower is slower. Color is the performance style (legend above). The dashed line has the slope measured within movements, drawn through the conductors' mean point."),
         "one": tr(lang, f"가장 왼쪽 점은 {esc(lo[3].split(" (")[0])}의 전집이다. {num(lo[0], '.0f')}년 무렵 녹음이고, 중앙값이 표기보다 1분에 {num(abs(lo[1]), '.1f')}박 {'느리다' if lo[1] < 0 else '빠르다'}.",
                   f"The leftmost dot is {esc(lo[3].split(' (')[0])}'s cycle: recorded around {num(lo[0], '.0f')}, with a median {num(abs(lo[1]), '.1f')} beats a minute {'slower' if lo[1] < 0 else 'faster'} than the mark."),
         "mis": tr(lang, "지휘자마다 녹음 시기가 하나뿐이라, 지휘자의 차이와 연도의 차이가 한 쌍으로 묶여 있다. 그래서 점선의 기울기를 연도의 영향으로 읽을 수 없다. 기울기의 불확실성(95% 구간)은 아래 표에 있다.",
                   "Each conductor comes with a single recording period, so differences between conductors and between years are bound together; the slope cannot be read as an influence of the year. Its uncertainty (95% interval) is in the table below."),
         "terms": BPM_TERM[lang]}
    return intro, p


def metric_pedal(groups, lang, cap: str) -> tuple[str, dict]:
    intro = tr(lang, "녹음마다 첫 음부터 마지막 음까지의 시간 가운데 댐퍼 페달이 일정 깊이 이상 눌려 있던 시간의 비율을 점 하나로 찍어, 바흐와 베토벤으로 나눈 그림이다.",
               "For each recording, the share of the time from first note to last with the damper pedal pressed beyond a set depth, one dot per recording, in a row for Bach and a row for Beethoven.")
    p = strip_parts(groups, ".3f", lang, "녹음", "recording", "작곡가 하나", "one composer", how_extra=cap,
                    mis_extra=tr(lang, "현대 피아노 연주를 MIDI 로 기록한 ASAP 자료에서 잰 값이다(MAESTRO 와 이어진 파일은 국제 피아노 e-콩쿠르 연주다). 바흐가 쓴 악기로 한 연주의 값이 아니다.",
                                 "These are measured on the ASAP set of MIDI records of modern-piano performances (files linked to MAESTRO are Piano-e-Competition performances), not on performances with the instruments Bach wrote for."))
    p["terms"] = (p.get("terms", "") + " " + tr(lang, "밟은 시간 — MIDI 기록에서 댐퍼 페달 신호(CC64, 0~127)가 64 이상인 시간이다. MIDI 관례대로 63 이하는 뗀 것, 64 이상은 밟은 것으로 본다. 0보다 크기만 하면 넣은 값(반 페달 포함)은 아래 표의 다른 칸에 있다. 분모는 파일마다 첫 음 시작부터 마지막 음 끝까지의 시간이다. 한 녹음에서 잘라 낸 여러 파일은 합쳐 녹음 하나로 세는데, 그때는 파일마다 낸 이 시간과 페달 시간을 각각 더한다(이어진 원녹음 전체의 첫 음부터 마지막 음까지와는 다를 수 있다).",
                                                    "Pedal down — time with the MIDI damper signal (CC64, 0 to 127) at 64 or more; by MIDI convention 63 or less is up and 64 or more is down. The value counting anything above 0 (half-pedalling included) is in another column of the table below. The denominator is, for each file, the time from the start of its first note to the end of its last. Files cut from one recording are merged into one recording by adding up these times and the pedal times file by file (which may differ from the span of the whole original recording).")).strip()
    return intro, p


def metric_soft(items, lang, ci) -> tuple[str, dict]:
    """ci: (name, share, n performances, low, high) of the first bar."""
    intro = tr(lang, "소프트 페달을 한 번이라도 일정 깊이 이상 밟은 녹음의 비율을 작곡가마다 막대 하나로 그린 그림이다.",
               "The share of recordings in which the soft pedal is pressed beyond a set depth at least once, one bar per composer.")
    p = {"short": bars_extremes(items, ".0%", lang),
         "how": tr(lang, "막대 하나가 작곡가 하나이고, 길이가 그 작곡가의 녹음 가운데 소프트 페달을 쓴 녹음의 비율이다. 「썼다」는 MIDI 기록의 소프트 페달 신호(CC67)가 한 순간이라도 64 이상이었다는 뜻이다. 여러 곡으로 잘린 녹음은 합쳐 하나로 센다. 밟은 시간의 길이는 세지 않고 썼는지만 센다.",
                   "Each bar is one composer; its length is the share of that composer's recordings in which the soft pedal is used. 'Used' means the MIDI soft-pedal signal (CC67) reaches 64 or more at some moment. A recording cut into several pieces counts once. How long it is held is not counted here."),
         "one": tr(lang, f"「{esc(ci[0])}」 막대는 {pct(ci[1], 0)}다. {ci[2]}녹음 가운데 그만큼이 소프트 페달을 썼고, 95% 구간은 {pct(ci[3])}~{pct(ci[4])}다.",
                   f"The '{esc(ci[0])}' bar is {pct(ci[1], 0)}: that share of its {ci[2]} recordings use the soft pedal; the 95% interval is {pct(ci[3])} to {pct(ci[4])}."),
         "mis": tr(lang, "녹음 수가 적은 작곡가는 막대가 보여 주는 것보다 불확실성이 크다(아래 표의 95% 구간). 모차르트는 녹음이 적어 구간이 넓다.",
                   "A composer with few recordings carries more uncertainty than the bar shows (the 95% intervals in the table below); Mozart has few recordings and a wide interval."),
         "terms": tr(lang, "95% 구간(윌슨 점수 구간) — 이 녹음들을 표본으로 보고, 같은 종류의 녹음 전체에서 소프트 페달을 쓰는 비율을 추정할 때 붙이는 구간. 이 방법으로 표본을 되풀이해 뽑아 구간을 만들면 약 95%가 실제 비율을 포함한다. 넓을수록 표본이 말해 주는 것이 적다. 악단 비교 면의 회색 막대(같은 수를 500번 다시 뽑은 값의 가운데 95%)와는 다른 계산이다.",
                     "95% interval (Wilson score interval) — treating these recordings as a sample, the interval attached to the estimate of how often the soft pedal is used in all such recordings. Built this way over repeated samples, about 95% of such intervals contain the true share. The wider it is, the less the sample says. It is a different calculation from the gray bars on the orchestra page (the middle 95% of 500 redraws of the same size).")}
    return intro, p


def metric_conductor(items, lang, n: int) -> tuple[str, dict]:
    intro = tr(lang, f"뉴욕 필하모닉에서 작품 연주를 1,000건 이상 지휘한 {n}명마다, 지휘한 작품 연주 가운데 연주 당시 살아 있던 작곡가의 작품이 차지한 몫을 그린 그림이다.",
               f"For the {n} conductors with 1,000 or more work performances at the New York Philharmonic, the share of the work performances each conducted that were by composers alive at the time.")
    p = {"short": bars_extremes(items, ".0%", lang),
         "how": tr(lang, "막대 하나가 지휘자 하나다(위에서 아래로 처음 지휘한 시즌 순). 길이는 그 지휘자가 지휘한 작품 연주 가운데 연주 당시 생존 작곡가의 작품이 차지한 비율이고, 분모는 생몰년을 확인한 작곡가의 작품 연주다. 괄호는 지휘한 첫 시즌과 마지막 시즌의 시작 연도다.",
                   "Each bar is one conductor, top to bottom in order of first season. Its length is the share of the work performances that conductor led that were by composers alive at the time; the denominator is the performances of works by composers with known dates. In brackets, the start years of the first and last seasons conducted."),
         "one": bars_one(items, ".0%", lang),
         "mis": tr(lang, "지휘자마다 활동한 시대가 다르다. 생존 작곡가의 몫은 시대에 따라 크게 달랐으므로(「생존 작곡가 점유율」 면), 막대의 차이에는 시대의 차이와 공연 종류의 차이가 섞여 있다. 곡을 지휘자가 골랐는지 악단이 기획해 맡겼는지는 기록에 없어서, 막대를 지휘자의 선택으로 읽을 수 없다. 생몰년을 모르는 작곡가를 어떻게 세느냐에 따른 하한·상한은 아래 표에 있다.",
                   "The conductors worked in different periods, and the living-composer share differed a great deal by period (see the living-composer share page), so differences between bars mix in the period and the kind of concert. The record does not say whether a conductor chose the works or was assigned them, so a bar cannot be read as the conductor's choice. Lower and upper bounds, depending on how composers without known dates are counted, are in the table below.")}
    return intro, p


def metric_survival(ser, lang) -> tuple[str, dict]:
    intro = tr(lang, "뉴욕 필이 살아 있는 작곡가의 작품을 처음 연주한 뒤 몇 년 안에 다른 시즌에 다시 연주했는지를, 첫 연주 시기별로 누적해 그린 선 그림이다.",
               "How soon works by living composers were played again in a later season after their first New York Philharmonic performance, as cumulative lines by period of first performance.")
    rows = []
    for name, pts, *_ in ser:
        v10 = [y for x, y in pts if x == 10]
        if v10:
            rows.append((name, v10[0]))
    short = (("10년째 값은 " + ", ".join(f"{esc(nm)} {pct(v, 0)}" for nm, v in rows) + "다.") if lang == "ko"
             else ("At ten years: " + ", ".join(f"{esc(nm)} {pct(v, 0)}" for nm, v in rows) + "."))
    one = ""
    if rows:
        nm, v = rows[0]
        one = tr(lang, f"「{esc(nm)}」 선의 10년 자리 값 {pct(v, 0)}는, 그 시기에 처음 연주된 생존 작곡가 작품 가운데 그만큼이 10년 안에 한 번 이상 다시 연주되었다고 추정한다는 뜻이다.",
                 f"The '{esc(nm)}' line at ten years, {pct(v, 0)}, is the estimated share of works by living composers first played in that period that were played again at least once within ten years.")
    p = {"short": short,
         "how": tr(lang, "선 하나가 첫 연주 시기 하나다(색은 위 범례). 가로는 첫 연주 시즌부터의 햇수(30년까지), 세로는 그때까지 다른 시즌에 다시 연주된 작품의 누적 비율이다. 그래서 선은 내려가지 않는다. 첫 연주와 같은 시즌의 다른 프로그램은 재연주로 세지 않는다.",
                   "Each line is one period of first performance (colors in the legend above). Across: years since the first season (up to 30); up: the cumulative share of works played again in a later season by then, so the lines never go down. Other programs in the season of the first performance do not count as playing it again."),
         "one": one,
         "mis": tr(lang, "2000년 이후 선은 지켜본 기간이 짧아, 뒤로 갈수록 그 값을 받치는 작품이 적다. 아직 다시 연주되지 않은 것과 끝내 다시 연주되지 않은 것은 다르다. 「신작」은 작곡 연도가 아니라 첫 연주 시즌에 작곡가가 살아 있었는지로 가렸다(작곡 연도는 기록에 없다). 기록의 첫 시즌(1842–43)에 처음 보이는 작품은 그 전 연주를 알 수 없어 뺐다.",
                   "The 2000-on line has short follow-up, so fewer works stand behind its later values. Not played again yet is not the same as never played again. A 'new' work here is one whose composer was alive in the season of the first performance, not one with a recent composition date (the record has none). Works first seen in the archive's first season (1842–43) are left out, since their earlier history is unknown."),
         "terms": tr(lang, "카플란–마이어(Kaplan–Meier) — 작품마다 지켜본 기간이 다를 때, 아직 결과가 나지 않은 작품도 지켜본 기간만큼은 계산에 넣어 누적 비율을 추정하는 방법. 세로값은 1 − (그때까지 다시 연주되지 않은 비율의 추정)이다.",
                     "Kaplan–Meier — a way to estimate a cumulative share when works have been followed for different lengths of time: a work still waiting counts for as long as it has been watched. The vertical value is 1 − (the estimated share not yet played again).")}
    return intro, p


def metric_women(ser, lang, last_label: str) -> tuple[str, dict]:
    intro = tr(lang, "뉴욕 필의 시즌마다 작품 연주 가운데 여성 작곡가의 작품이 차지한 비율을, 성별을 모르는 작곡가를 어떻게 세느냐에 따라 세 선으로 그린 그림이다.",
               "The share of each New York Philharmonic season's work performances that went to women composers, in three lines depending on how composers of unknown gender are counted.")
    lo = line_points(ser[0][1])
    hi = line_points(ser[2][1])
    p = {"short": line_short([ser[1]], ".1%", lang, season),
         "how": tr(lang, "가로는 시즌의 시작 해(1842 = 1842–43 시즌)다. 하한과 상한의 분모는 그 시즌에 사람 작곡가의 작품을 연주한 건수이고(전승곡·작곡가 미상 등은 뺀다), 가운데 값의 분모는 그 가운데 성별이 확인된 작곡가의 작품 연주 수다. 성별은 Wikidata 기록을 따르고, 서로 다른 값이 둘 이상 적힌 작곡가는 성별을 모르는 것으로 둔다. 「하한」은 성별을 모르는 작곡가를 모두 여성이 아닌 것으로, 「상한」은 모두 여성으로 둔 값이고, 「가운데 값」은 성별이 확인된 작곡가만으로 낸 값이다.",
                   "Across: the first year of the season (1842 = 1842–43). The lower and upper bounds divide by the season's performances of works by individual composers (traditional works, unknown composers and the like are left out); the middle value divides by those of them whose composer's gender is recorded. Gender follows Wikidata; a composer with two or more conflicting values counts as unknown. 'Lower bound' counts composers of unknown gender as not women, 'upper bound' as women, and 'middle value' uses only composers whose gender is recorded."),
         "one": tr(lang, f"{last_label} 시즌은 하한 {pct(lo[-1][1])}, 상한 {pct(hi[-1][1])}다. 두 값의 차이는 성별을 모르는 작곡가 쪽 연주의 몫이다.",
                   f"In {last_label} the lower bound is {pct(lo[-1][1])} and the upper bound {pct(hi[-1][1])}; the gap is the share that went to composers of unknown gender."),
         "mis": tr(lang, "상한과 하한이 많이 벌어진 시즌은 성별을 확인하지 못한 작곡가의 작품 연주가 그 시즌에서 큰 몫을 차지했다는 뜻이다. 그런 작곡가 한 사람의 작품이 여러 번 연주되어도 벌어지므로 작곡가 수를 말해 주지 않고, 상한이 높다고 여성 작곡가가 많았다는 뜻도 아니다.",
                   "A season where the upper and lower bounds lie far apart is one where works by composers of unknown gender took a large share of the performances. One such composer played many times widens the gap too, so it is not a count of composers, and a high upper bound does not mean many women.")}
    return intro, p


def metric_turnover(ser, lang, last_note: str = "") -> tuple[str, dict]:
    intro = tr(lang, "10년마다 가장 많이 연주된 작곡가 명단이 앞 10년의 명단과 얼마나 겹치는지 그린 선 그림이다.",
               "How much each decade's list of most-performed composers overlaps with the previous decade's list.")
    s10 = line_points(ser[0][1])
    lo = min(s10, key=lambda p: p[1])
    dl = (lambda x: f"{x}년대") if lang == "ko" else (lambda x: f"{x}s")
    lo_x = tied_names([dl(x) for x, y in s10 if y == lo[1]], lang)
    p = {"short": line_short(ser, ".2f", lang, dl),
         "how": tr(lang, "점 하나가 10년 하나이고, 값은 그 10년과 앞 10년의 상위 명단이 겹치는 정도(자카드 지수, 0~1)다. 1이면 명단이 그대로, 0이면 완전히 바뀌었다. 선은 상위 10명과 상위 25명 두 가지다.",
                   "Each point is one decade; its value is how much that decade's top list overlaps with the previous decade's (Jaccard index, 0 to 1): 1 means the same list, 0 an entirely new one. The two lines use the top 10 and the top 25."),
         "one": tr(lang, f"상위 10명 선이 가장 낮은 {lo_x}는 {num(lo[1], '.2f')}{axis.kp(num(lo[1], '.2f'), '이다', '다')}. 두 10년의 상위 10명을 합친 명단 가운데 양쪽에 다 든 사람의 비율이 그만큼이라는 뜻이다.",
                   f"The top-10 line is lowest in the {lo_x}, at {num(lo[1], '.2f')}: of everyone on either decade's top-10 list, that share is on both."),
         "mis": tr(lang, "자카드 지수 0.67은 「10명 중 6.7명이 남았다」가 아니다. 10명 중 8명이 남으면 두 명단을 합친 12명 가운데 8명이 겹쳐 0.67이 된다. 상위 10명에서 남은 사람이 k명이면 값은 k ÷ (20 − k)라, 0.54는 10명 중 7명쯤 남은 것이다(7 ÷ 13). 이 식은 두 명단이 늘 10명씩일 때 맞는다. 이름은 「회전율」이지만 값이 클수록 명단이 덜 바뀐다." + ((" " + last_note) if last_note else ""),
                   "A Jaccard index of 0.67 does not mean 6.7 of 10 stayed: if 8 of 10 stay, 8 of the 12 names on either list are shared, which gives 0.67. With k of the top 10 staying the value is k ÷ (20 − k), so 0.54 means about 7 of 10 stayed (7 ÷ 13). The formula holds because both lists always have ten names. Despite the name 'turnover', a larger value means the list changed less." + ((" " + last_note) if last_note else "")),
         "terms": tr(lang, "자카드 지수 — 두 명단에 모두 든 이름의 수 ÷ 어느 한쪽에라도 든 이름의 수.", "Jaccard index — the number of names on both lists ÷ the number on either list.")}
    return intro, p


def metric_season(ser, m, lang, n_first: int, first_label: str, band=False) -> tuple[str, dict]:
    # v1 3.06: each season line says how its value is computed (the registry formula, the same text as the definition box below)
    """A New York Philharmonic season line (shares, concentration, counts, ages)."""
    name = m[lang]["name"]
    intro = tr(lang, f"{esc(name)}{axis.kp(name, '을', '를')} 뉴욕 필하모닉의 완결 시즌마다 점 하나로 찍어 이은 선 그림이다.",
               f"{esc(name)} for every completed New York Philharmonic season, joined into a line.")
    how = tr(lang, f"가로는 시즌의 시작 해다(1842 = 1842–43 시즌). 세로는 위 축 이름에 적은 값이고, 선 위에 마우스를 대거나 누르면 그 시즌의 값이 뜬다. 값의 계산: {esc(m['ko']['formula'])}",
             f"Across: the first year of the season (1842 = 1842–43). Up: the value named in the axis title above; hover over or tap the line for a season's value. How the value is computed: {esc(m['en']['formula'])}")
    if band:
        how += tr(lang, " 「하한」과 「상한」은 생몰년을 확인하지 못한 작곡가를 모두 생존이 아닌 쪽으로, 모두 생존인 쪽으로 둔 값이다.",
                  " 'Lower' and 'upper' count every composer without known dates as not alive and as alive.")
    p = {"short": line_short(ser[:1], m["fmt"], lang, season, names=False),
         "how": how,
         "one": line_one(ser[:1], m["fmt"], lang, season),
         "mis": tr(lang, f"시즌마다 오르내림이 크다. 한 시즌의 높낮이보다 긴 흐름을 본다. 첫 시즌({first_label})은 프로그램이 {n_first}개뿐이라, 초기 값은 몇 곡에 크게 흔들린다.",
                   f"Values swing from season to season; look at the long run rather than one season. The first season ({first_label}) has only {n_first} programs, so early values move a lot with a few works.")}
    return intro, p


def composer_line(c_name: str, pts1, lang, peak_label: str, peak_share, peak_done: bool) -> tuple[str, dict]:
    """The line on each of the top-50 composer pages."""
    p1 = line_points(pts1)
    intro = tr(lang, f"{esc(c_name)}의 작품이 시즌마다 뉴욕 필하모닉의 작품 연주에서 차지한 몫을 그린 선 그림이다.",
               f"The share of each New York Philharmonic season's work performances that went to {esc(c_name)}.")
    zeros = sum(1 for _, y in p1 if y == 0)
    one = tr(lang, f"몫이 가장 컸던 시즌은 {esc(peak_label)}이고, 그 시즌 작품 연주의 {pct(peak_share)}였다.", f"The largest share came in {esc(peak_label)}: {pct(peak_share)} of that season's work performances.")
    if not peak_done:
        one += tr(lang, " 이 시즌은 아직 끝나지 않아 그림에는 없고, 값이 바뀔 수 있다.", " That season is still in progress, so it is not drawn and the value may change.")
    p = {"short": line_short([("", pts1)], ".1%", lang, season, names=False) + tr(lang, f" 그림에 실린 완결 시즌 {len(p1)}개 가운데 {zeros}개 시즌은 0이다.", f" {zeros} of the {len(p1)} completed seasons drawn are at 0."),
         "how": tr(lang, "완결 시즌만 그렸다. 가로는 시즌의 시작 해(1842 = 1842–43 시즌), 세로는 그 시즌 작품 연주 전체 가운데 이 작곡가의 몫이다. 위 선(작품 연주)은 발췌를 포함하고, 아래 선(전곡 연주)은 그중 악장 표시가 없는 연주만 같은 분모로 나눈 것이다. 두 선의 간격이 이 작곡가의 발췌 연주가 그 시즌 전체에서 차지한 몫이다.",
                   "Completed seasons only. Across: the first year of the season (1842 = 1842–43); up: this composer's share of the season's work performances. The upper line (work performances) includes excerpts; the lower line (complete performances) counts only performances without a movement named, over the same denominator. The gap between them is this composer's excerpts as a share of the whole season."),
         "one": one,
         "mis": tr(lang, "몫은 그 시즌 전체 연주에 대한 비율이다. 연주 횟수가 같아도 그 시즌의 연주가 많으면 몫은 작아진다. 초기 시즌은 연주회가 몇 번뿐이라 한 곡으로도 크게 튄다.",
                   "The share is out of the whole season: the same number of performances is a smaller share in a season with more performances, and early seasons with only a few concerts jump with a single work.")}
    return intro, p


def reading_shares(ser, lang, mz_seasons, bach_med) -> tuple[str, dict]:
    """Reading edition: Beethoven, Mozart and Bach shares per season."""
    intro = tr(lang, "뉴욕 필하모닉의 시즌마다 베토벤·모차르트·바흐의 작품이 작품 연주에서 차지한 몫을 세 선으로 그린 그림이다.",
               "The share of each New York Philharmonic season's work performances that went to Beethoven, Mozart and Bach, as three lines.")
    mz = "·".join(mz_seasons) if lang == "ko" else (", ".join(mz_seasons[:-1]) + " and " + mz_seasons[-1] if len(mz_seasons) > 1 else "".join(mz_seasons))
    p = {"short": line_short([ser[0]], ".1%", lang, season) + (tr(lang, f" 모차르트가 20%를 넘은 시즌은 {mz}{axis.kp(mz, '이다', '다')}.", f" Mozart passes 20% in {mz}.") if mz_seasons else "")
                  + tr(lang, f" 바흐는 시즌 중앙값이 {pct(bach_med)}다.", f" Bach's season median is {pct(bach_med)}."),
         "how": tr(lang, "가로는 시즌의 시작 해(1842 = 1842–43 시즌), 세로는 그 시즌 작품 연주 가운데 그 작곡가의 몫이다. 선 끝의 이름과 위 범례가 색을 알려 준다. 완결 시즌만 그렸다.",
                   "Across: the first year of the season (1842 = 1842–43); up: that composer's share of the season's work performances. The names at the line ends and the legend above give the colors. Completed seasons only."),
         "one": line_one([ser[1]], ".1%", lang, season),
         "mis": tr(lang, "세 선은 같은 시즌 전체를 분모로 한 몫이라, 한 작곡가의 몫이 줄어든 것이 연주 횟수가 줄었다는 뜻은 아니다. 시즌의 연주가 늘면 횟수가 같아도 몫은 줄어든다.",
                   "All three are shares of the same season total, so a falling share does not mean fewer performances: when a season has more performances, the same count is a smaller share.")}
    return intro, p


HHI_TERM = {"ko": "HHI(허핀달–허시만 지수) — 작곡가마다 점유율을 제곱해 더한 값. 한 작곡가뿐이면 1, 작곡가 N명이 똑같이 나눠 가지면 1/N이다. 그래서 1/HHI를 「몇 명이 고르게 나눠 가진 것과 같은가」로 읽을 수 있다. 전승곡·국가·작곡가 미상·공동 표기 같은 항목은 분류마다 한 덩어리로 넣는다.",
            "en": "HHI (Herfindahl–Hirschman index) — the sum of the squared shares of the composers: 1 for a single composer, 1/N for N composers with equal shares, so 1/HHI reads as 'as concentrated as that many equal composers'. Traditional works, anthems, unknown composers and joint credits each enter as one block per category."}


def reading_hhi(ser, lang, short_txt: str) -> tuple[str, dict]:
    intro = tr(lang, "시즌마다 작품 연주가 몇몇 작곡가에게 얼마나 몰려 있었는지(집중도)를 그린 선 그림이다.",
               "How much each season's work performances were concentrated on a few composers.")
    p = {"short": short_txt,
         "how": tr(lang, "가로는 시즌의 시작 해, 세로는 그 시즌의 작곡가 집중도(HHI, 0~1)다. 위로 갈수록 소수의 작곡가에게 몰려 있다.",
                   "Across: the first year of the season; up: that season's composer concentration (HHI, 0 to 1). Higher means more concentrated on a few composers."),
         "one": line_one(ser, ".3f", lang, season),
         "mis": tr(lang, "초기 시즌은 연주회가 몇 번뿐이라 몇 곡으로도 값이 크게 튄다. 값이 내려갔다는 것은 연주가 소수 작곡가에게 덜 몰렸다는 뜻이다. 작곡가 수가 같아도 연주가 더 고르게 나뉘면 값이 내려가므로, 연주된 작곡가 수를 센 값은 아니다.",
                   "Early seasons had only a few concerts, so a few works move the value a lot. A falling value means performances were less concentrated on a few composers; with the same number of composers, a more even split also lowers it, so it is not a count of composers."),
         "terms": HHI_TERM[lang]}
    return intro, p


def reading_living(ser, lang, how_txt: str) -> tuple[str, dict]:
    intro = tr(lang, "시즌마다 작품 연주 가운데 연주 당시 살아 있던 작곡가의 작품이 차지한 몫을 그린 선 그림이다.",
               "The share of each season's work performances that went to composers alive at the time.")
    p = {"short": line_short([ser[0]], ".0%", lang, season),
         "how": tr(lang, "가로는 시즌의 시작 해, 세로는 생존 작곡가의 몫이다. 생존은 시즌 시작 해에 살아 있었는지로 가렸고, 「생존 작곡가」 선의 분모는 생몰년을 확인한 작곡가의 작품 연주다. ",
                   "Across: the first year of the season; up: the living-composer share. Alive means alive in the first year of the season, and the denominator of the 'living composers' line is the performances of works by composers with known dates. ") + how_txt,
         "one": line_one([ser[0]], ".1%", lang, season),
         "mis": tr(lang, "최근 시즌은 생몰년을 확인하지 못한 작곡가가 많아 「상한」 선이 위로 벌어진다. 진짜 값은 하한(그림에는 없고 위 본문에 있다)과 상한 사이에 있다.",
                   "In recent seasons many composers have no known dates, so the upper-bound line moves away; the true value lies between the lower bound (not drawn; given in the text above) and the upper bound.")}
    return intro, p


# ----------------------------------------------------------------- pages whose figures carry a long caption already
_FIG = None


def retrofit(body: str, specs, lang: str) -> str:
    """Give each <figure> that has a <figcaption> but no line above (in page order) the line above and labelled
    paragraphs: the caption it had becomes 'how the chart works'. specs: [(intro, extra parts dict)], one per such
    figure; the count must match, so a figure added later cannot silently go without notes."""
    import re
    global _FIG
    if _FIG is None:
        _FIG = re.compile(r"<figure\b([^>]*)>(?!<p class=\"fi\">)(.*?)<figcaption>(.*?)</figcaption></figure>", re.S)
    found = list(_FIG.finditer(body))
    found = [m for m in found if 'class="cp"' not in m.group(3)]
    if len(found) != len(specs):
        raise SystemExit(f"fig_notes.retrofit: {len(found)} captioned figures, {len(specs)} notes")
    out, last = [], 0
    for m, (intro, extra) in zip(found, specs):
        parts = dict(extra)
        parts["how"] = (m.group(3).strip() + (" " + parts["how"] if parts.get("how") else ""))
        out.append(body[last:m.start()])
        out.append(f'<figure{m.group(1)}><p class="fi">{intro}</p>{m.group(2)}<figcaption>{parts_html(parts, lang)}</figcaption></figure>')
        last = m.end()
    out.append(body[last:])
    return "".join(out)
