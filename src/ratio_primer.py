"""'Before you start — notes set by ratio' (1.21): a primer section on the Scales and tuning page.

Every number is computed here from definitions (ratios, 2^(k/12), harmonic n) — nothing is measured.
Sources quoted: Sima Qian, Shiji 25 'Lüshu' (律數 81·54·72·48·64), Lüshi chunqiu 6 'Yinlü' (order of the twelve lü,
益 = 上生, 去 = 下生), both zh.wikisource (rev 2687752, 2327717); Helmholtz, On the Sensations of Tone,
tr. Ellis, 3rd ed. 1895, ch. X, p. 194 (consonance as the absence or weakness of beats between partials).
Playback: simultaneous tones use a tone with harmonics 1-8 at amplitude 1/n (the page's other buttons use a
triangle wave, which has odd harmonics only, so the 4th harmonic behind the beats of a major third is missing).
"""
from __future__ import annotations

import html
import json
import math
from fractions import Fraction as F

BASE = 261.63  # middle C, the page's reference


def cents(r) -> float:
    return 1200 * math.log2(float(r))


def esc(s):
    return html.escape(str(s))


def frac(r: F) -> str:
    return f"{r.numerator}/{r.denominator}" if r.denominator != 1 else f"{r.numerator}"


# ---- A. ratios and cents -------------------------------------------------------------------------------------
# 1.22: the intervals are not chosen by hand. interval_rows() collects every interval between two notes of the just
# major scale below (C..B from three 4:5:6 triads, see JUST), one octave up at most; for each size in semitones the
# simplest ratio (smallest numerator + denominator) is the main row and the others are 'other ratio' rows. 7/4, from
# the 7th harmonic, is added as one more other-ratio row of the minor seventh.
SEMI_NAME = {1: ("단2도", "minor second"), 2: ("장2도", "major second"), 3: ("단3도", "minor third"), 4: ("장3도", "major third"),
             5: ("완전4도", "perfect fourth"), 6: ("증4도", "augmented fourth"), 7: ("완전5도", "perfect fifth"), 8: ("단6도", "minor sixth"),
             9: ("장6도", "major sixth"), 10: ("단7도", "minor seventh"), 11: ("장7도", "major seventh"), 12: ("옥타브", "octave")}
MAXH = 8  # harmonics in the playback tone


def et_beats(r: F, semis: int, f: float = BASE) -> float:
    """Beats per second when the interval is played in equal temperament above f: the p-th harmonic of the lower
    tone against the q-th of the upper (r = p/q). Whether the playback tone has those harmonics is audible(r)."""
    p, q = r.numerator, r.denominator
    g = f * 2 ** (semis / 12)
    return abs(p * f - q * g)


# ---- B. harmonics -------------------------------------------------------------------------------------------
HARM = list(range(1, 17))


def harm_dev(n: int) -> float:
    c = cents(n)
    return c - round(c / 100) * 100


# ---- C. three ways ------------------------------------------------------------------------------------------
MAJOR = ["C", "D", "E", "F", "G", "A", "B"]
MAJOR_KO = ["도", "레", "미", "파", "솔", "라", "시"]
PYTH_K = {"F": -1, "C": 0, "G": 1, "D": 2, "A": 3, "E": 4, "B": 5}  # fifths from C


def fold(r: F) -> F:
    while r >= 2:
        r /= 2
    while r < 1:
        r *= 2
    return r


def pyth(name: str) -> F:
    return fold(F(3, 2) ** PYTH_K[name])


JUST = {"C": F(1), "D": F(9, 8), "E": F(5, 4), "F": F(4, 3), "G": F(3, 2), "A": F(5, 3), "B": F(15, 8)}
ET_SEMI = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
COMMA = F(3, 2) ** 12 / 2 ** 7  # Pythagorean comma 531441/524288
SYNTONIC = F(81, 64) / F(5, 4)  # 81/80

# Twelve lü in the order of the Lüshi chunqiu, from a huangzhong pipe of 81 (Shiji). 'sun' = length x 2/3 (去 / 下生),
# 'yi' = length x 4/3 (益 / 上生). The step 蕤賓 -> 大呂 is yi, so two yi follow each other.
LU = [("黃鐘", "황종", None), ("林鐘", "임종", "sun"), ("太蔟", "태주", "yi"), ("南呂", "남려", "sun"), ("姑洗", "고선", "yi"),
      ("應鐘", "응종", "sun"), ("蕤賓", "유빈", "yi"), ("大呂", "대려", "yi"), ("夷則", "이칙", "sun"), ("夾鐘", "협종", "yi"),
      ("無射", "무역", "sun"), ("仲呂", "중려", "yi")]
LU_UP = {"黃鐘", "大呂", "太蔟", "夾鐘", "姑洗", "仲呂", "蕤賓"}  # 為上 in the Lüshi chunqiu
LU_PITCH = ["C", "G", "D", "A", "E", "B", "F♯", "C♯", "G♯", "D♯", "A♯", "E♯"]  # with huangzhong on C


def lu_table():
    rows, L = [], F(81)
    for i, (h, ko, op) in enumerate(LU):
        if op == "sun":
            L = L * F(2, 3)
        elif op == "yi":
            L = L * F(4, 3)
        rows.append(dict(hanja=h, ko=ko, op=op, length=L, ratio=F(81) / L, cents=cents(F(81) / L), pitch=LU_PITCH[i]))
    return rows


def lu_next():
    """One more sun after 仲呂: the pipe that should be half of huangzhong (40.5) but is not."""
    last = lu_table()[-1]["length"] * F(2, 3)
    return last, cents(F(81, 2) / last)


# ---- D. enharmonic pairs ------------------------------------------------------------------------------------
ENH = {  # system: (C sharp, D flat)
    "pyth": (fold(F(3, 2) ** 7), fold(F(2, 3) ** 5)),
    "just": (F(5, 3) * F(5, 4) / 2, F(4, 3) / F(5, 4)),  # C# a major third above A; Db a major third below F
    "et": (2 ** (1 / 12), 2 ** (1 / 12)),
}


def interval_rows():
    """[{semis, ratio, main, pairs_ko, pairs_en, name_ko, name_en}] from the just major scale, plus 7/4."""
    found = {}
    for i, a in enumerate(MAJOR):
        for step in range(1, 8):
            j = i + step
            b = MAJOR[j % 7]
            r = JUST[b] * (2 if j >= 7 else 1) / JUST[a]
            semis = ET_SEMI[b] + (12 if j >= 7 else 0) - ET_SEMI[a]
            ko = f"{MAJOR_KO[i]}–{MAJOR_KO[j % 7]}{'′' if j >= 7 else ''}"
            en = f"{a}–{b}{'′' if j >= 7 else ''}"
            found.setdefault((semis, r), ([], []))
            found[(semis, r)][0].append(ko)
            found[(semis, r)][1].append(en)
    rows = []
    for semis in sorted({k[0] for k in found}):
        rats = sorted((r for (s_, r) in found if s_ == semis), key=lambda r: (r.numerator + r.denominator, r))
        for n, r in enumerate(rats):
            ko, en = SEMI_NAME[semis]
            if semis == 6 and r == F(64, 45):
                ko, en = "감5도", "diminished fifth"
            rows.append(dict(semis=semis, ratio=r, main=(n == 0), pairs_ko=found[(semis, r)][0], pairs_en=found[(semis, r)][1], name_ko=ko, name_en=en))
    rows.append(dict(semis=10, ratio=F(7, 4), main=False, pairs_ko=["7배음 ÷ 4배음"], pairs_en=["harmonic 7 ÷ harmonic 4"],
                     name_ko="단7도", name_en="minor seventh"))
    return rows


def ratio_axes_svg(k: bool) -> str:
    """Two rulers for one octave: frequency ratio on a plain scale (top) and cents (bottom), joined at the 13 equal-
    tempered notes; the main just ratios as dots on both, clickable."""
    width, L, R = 900, 24, 24
    W = width - L - R
    yt, yb, height = 70, 160, 214
    X1 = lambda r: L + (float(r) - 1) * W  # noqa: E731
    X2 = lambda c: L + c / 1200 * W  # noqa: E731
    o = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{"한 옥타브를 진동수 비와 센트로 견준 그림" if k else "One octave as frequency ratio and as cents"}">']
    o.append(f'<text x="{L}" y="12" style="fill:var(--fg3)">{"위: 진동수 비를 같은 간격으로 · 아래: 센트를 같은 간격으로(진동수로는 로그 눈금) · 회색 선: 평균율 반음 12개 · 색 점: 순정 비(누르면 소리)" if k else "Top: frequency ratio, evenly spaced · bottom: cents, evenly spaced (a log scale of frequency) · gray lines: the 12 equal-tempered semitones · colored dots: just ratios (click to hear)"}</text>')
    for kk in range(13):
        r = 2 ** (kk / 12)
        o.append(f'<line x1="{X1(r):.1f}" y1="{yt}" x2="{X2(100 * kk):.1f}" y2="{yb}" stroke="var(--fg3)" stroke-opacity=".55" stroke-width="1"><title>{esc(f"2^({kk}/12) = {r:.4f} → {100 * kk}" + ("센트" if k else " cents"))}</title></line>')
    for y in (yt, yb):
        o.append(f'<line x1="{L}" x2="{L + W}" y1="{y}" y2="{y}" stroke="var(--fg3)" stroke-opacity=".7"/>')
    for t in range(11):
        r = 1 + t / 10
        o.append(f'<line x1="{X1(r):.1f}" x2="{X1(r):.1f}" y1="{yt}" y2="{yt + 5}" stroke="var(--fg3)"/>'
                 f'<text x="{X1(r):.1f}" y="{yt + 17}" text-anchor="middle" style="fill:var(--fg3)">{r:.1f}</text>')
    for c in range(0, 1201, 100):
        o.append(f'<line x1="{X2(c):.1f}" x2="{X2(c):.1f}" y1="{yb}" y2="{yb + 5}" stroke="var(--fg3)"/>')
        if c % 200 == 0:
            o.append(f'<text x="{X2(c):.1f}" y="{yb + 18}" text-anchor="middle" style="fill:var(--fg3)">{c}</text>')
    o.append(f'<text x="{L + W}" y="{yb + 34}" text-anchor="end" style="fill:var(--fg3)">{"센트" if k else "cents"}</text>')
    o.append(f'<text x="{L + W}" y="{yt + 31}" text-anchor="end" style="fill:var(--fg3)">{"진동수 비" if k else "frequency ratio"}</text>')
    mains = [row for row in interval_rows() if row["main"]]
    for n, row in enumerate(mains):
        r, c = row["ratio"], cents(row["ratio"])
        nm = row["name_ko"] if k else row["name_en"]
        tip = esc(f"{nm} {frac(r)} = {float(r):.4f} → {c:.1f}" + ("센트" if k else " cents"))
        dp = esc(json.dumps([[0, round(c, 3)]]))
        o.append(f'<line x1="{X1(r):.1f}" y1="{yt}" x2="{X2(c):.1f}" y2="{yb}" stroke="var(--g2)" stroke-dasharray="3 3" stroke-opacity=".8"/>')
        for x, y in ((X1(r), yt), (X2(c), yb)):
            o.append(f'<circle cx="{x:.1f}" cy="{y}" r="5.5" fill="var(--g2)" stroke="var(--card)" stroke-width="1.2" style="cursor:pointer" data-p="{dp}" data-t="rich" data-d="2.4"><title>{tip}</title></circle>')
        o.append(f'<text x="{X1(r):.1f}" y="{yt - (12 if n % 2 == 0 else 28)}" text-anchor="middle">{frac(r)}</text>')
    o.append("</svg>")
    return "".join(o)


def interval_table(k: bool) -> str:
    T = (lambda ko, en: ko if k else en)  # noqa: E731
    sorts = [("size", T("크기 순", "by size")), ("simple", T("단순한 비 순(분자+분모)", "simplest ratio first (numerator + denominator)")),
             ("dev", T("평균율과의 차이가 큰 순", "furthest from equal temperament")), ("beat", T("맥놀이가 많은 순", "most beats"))]
    o = ["<div class='sortbar' role='group' aria-label='" + T("표 정렬", "Sort the table") + "'>" + T("정렬: ", "Sort: ")
         + "".join(f"<button type='button' class='sort' data-sort='{key}' aria-pressed='{'true' if key == 'size' else 'false'}'>{esc(lab)}</button>" for key, lab in sorts) + "</div>"]
    head = [T("음정", "Interval"), T("순정 비", "Just ratio"), T("반음", "Semitones"), T("소수", "Decimal"), T("순정 센트", "Just, cents"),
            T("평균율 비", "Equal ratio"), T("소수", "Decimal"), T("평균율 센트", "Equal, cents"), T("평균율 − 순정", "Equal − just"),
            T("평균율로 함께 울릴 때 맥놀이(1초에)", "Beats per second, equal-tempered, together"), T("순정률 장음계에서 나오는 곳", "Where it occurs in the just major scale"), T("듣기", "Listen")]
    num = (2, 3, 4, 6, 7, 8, 9)
    th = "".join(f"<th{' class=num' if i in num else ''}>{h}</th>" for i, h in enumerate(head))
    trs = []
    for order, row in enumerate(sorted(interval_rows(), key=lambda x: (x["semis"], cents(x["ratio"])))):
        r, sm = row["ratio"], row["semis"]
        c, e = cents(r), 100 * sm
        bt = et_beats(r, sm)
        audible = r.numerator <= MAXH
        beats = f"{bt:.1f}" if audible else f"({bt:.1f})"
        tag = "" if row["main"] else f" <span class='alt-tag'>{T('다른 비', 'other ratio')}</span>"
        name = T(row["name_ko"], row["name_en"]) + tag
        where = ", ".join(row["pairs_ko"] if k else row["pairs_en"])
        btns = ("<div class='btns'>" + btn(T("순정 차례로", "just, in turn"), [[0], [c]], dur=0.7)
                + btn(T("순정 함께", "just, together"), [[0, c]], dur=2.6)
                + btn(T("평균율 함께", "equal, together"), [[0, e]], dur=2.6) + "</div>")
        cells = [name, f"<span class='ratio'>{frac(r)}</span>", str(sm), f"{float(r):.4f}", f"{c:.1f}",
                 f"2^({sm}/12)", f"{2 ** (sm / 12):.4f}", f"{e}", f"{e - c:+.1f}", beats, where, btns]
        attrs = (f" data-order='{order}' data-size='{sm * 2000 + c:.3f}' data-simple='{r.numerator + r.denominator}' data-dev='{abs(e - c):.3f}'"
                 f" data-beat='{bt if audible else -1:.3f}'" + ("" if row["main"] else " class='alt'"))
        trs.append(f"<tr{attrs}>" + "".join(f"<td{' class=num' if i in num else ''}>{x}</td>" for i, x in enumerate(cells)) + "</tr>")
    o.append(f"<div class='wrap ivlwrap'><table class='ivl'><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div>")
    o.append("<p class='src sortnote'>" + T("지금 순서: 크기 순(반음 수, 같은 반음이면 센트가 작은 쪽부터).", "Current order: by size (semitones, then cents).") + "</p>")
    return "".join(o)


SORT_JS = """<script>(function(){var t=document.querySelector('.primer table.ivl');if(!t)return;var tb=t.tBodies[0],note=document.querySelector('.primer .sortnote');
var NOTE=%s;function fix(){t.classList.remove('fix1','fix2');var c=tb.rows[0].cells,w=t.parentElement.clientWidth,a=c[0].getBoundingClientRect().width,b=c[1].getBoundingClientRect().width;
t.style.setProperty('--c1',a+'px');t.classList.toggle('fix1',a<=.45*w);t.classList.toggle('fix2',a+b<=.6*w)}fix();addEventListener('resize',fix);addEventListener('load',fix);function key(tr,k){return parseFloat(tr.getAttribute('data-'+k))}
function sortBy(k){var rows=Array.prototype.slice.call(tb.rows);rows.sort(function(a,b){var d;
if(k==='size')d=key(a,'size')-key(b,'size');else if(k==='simple')d=key(a,'simple')-key(b,'simple');else if(k==='dev')d=key(b,'dev')-key(a,'dev');else d=key(b,'beat')-key(a,'beat');
return d||key(a,'order')-key(b,'order')});rows.forEach(function(r){tb.appendChild(r)});
document.querySelectorAll('.primer .sortbar button').forEach(function(b){b.setAttribute('aria-pressed',b.getAttribute('data-sort')===k?'true':'false')});if(note)note.textContent=NOTE[k]}
document.querySelectorAll('.primer .sortbar button').forEach(function(b){b.addEventListener('click',function(){sortBy(b.getAttribute('data-sort'))})})})();</script>"""


# ---- rendering ----------------------------------------------------------------------------------------------
CSS = """.primer h3{margin:1.1rem 0 .3rem;font-size:1rem}.primer .btns{display:flex;gap:.35rem;flex-wrap:wrap;margin:.25rem 0 .5rem}
.primer button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:.12rem .6rem;font-size:.8rem;cursor:pointer;white-space:nowrap}
.primer button:hover{border-color:var(--fg3)}.primer td .btns{margin:0;flex-wrap:nowrap}.primer .formula{font-size:.92rem;line-height:1.7;background:color-mix(in srgb,var(--fg3) 8%,transparent);border-radius:8px;padding:.45rem .8rem}
.primer blockquote{margin:.5rem 0;padding:.4rem .8rem;border-left:3px solid var(--line)}.primer blockquote p{margin:.2rem 0}
.primer .ratio{font-size:1.08rem;font-weight:700}.primer tr.alt td{color:var(--fg3)}.primer tr.alt .ratio{font-weight:600}.primer .alt-tag{font-size:.7rem;border:1px solid var(--line);border-radius:4px;padding:0 .3rem;margin-left:.25rem;white-space:nowrap}
.primer table.ivl.fix1 th:first-child,.primer table.ivl.fix1 td:first-child,.primer table.ivl.fix2 th:nth-child(2),.primer table.ivl.fix2 td:nth-child(2){position:sticky;left:0;z-index:1;background:var(--card)}
.primer table.ivl.fix2 th:nth-child(2),.primer table.ivl.fix2 td:nth-child(2){left:var(--c1,0px)}.primer .ivlwrap{padding-left:0}.primer table.ivl.fix1:not(.fix2) th:first-child,.primer table.ivl.fix1:not(.fix2) td:first-child{box-shadow:inset -1px 0 0 var(--line)}.primer table.ivl.fix2 th:nth-child(2),.primer table.ivl.fix2 td:nth-child(2){box-shadow:inset -1px 0 0 var(--line)}
@media(max-width:640px){.primer table.ivl td:first-child,.primer table.ivl th:first-child{max-width:6.5em;min-width:5em;white-space:normal}.primer table.ivl td:first-child .alt-tag{display:inline-block;margin:.15rem 0 0}}
.primer .sortbar{display:flex;gap:.35rem;flex-wrap:wrap;align-items:center;margin:.6rem 0 .2rem;font-size:.85rem}.primer .sortbar button[aria-pressed=true]{border-color:var(--g1);background:color-mix(in srgb,var(--g1) 18%,var(--card))}"""

JS = """<script>(function(){var ac=null,W=null;function ctx(){if(!ac){ac=new (window.AudioContext||window.webkitAudioContext)()}return ac}
function wave(a){if(!W){var re=new Float32Array(9),im=new Float32Array(9);for(var i=1;i<9;i++)im[i]=1/i;W=a.createPeriodicWave(re,im)}return W}
function voice(f,t,d,kind,amp){var a=ctx(),o=a.createOscillator(),g=a.createGain();if(kind==='rich')o.setPeriodicWave(wave(a));else o.type=kind;o.frequency.value=f;
g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(amp,t+.03);g.gain.setValueAtTime(amp,t+Math.max(.05,d-.2));g.gain.linearRampToValueAtTime(.0001,t+d);o.connect(g);g.connect(a.destination);o.start(t);o.stop(t+d+.05)}
var BASE=261.63;document.querySelectorAll('.primer [data-p]').forEach(function(b){b.addEventListener('click',function(){
var steps=JSON.parse(b.getAttribute('data-p')),kind=b.getAttribute('data-t')||'rich',d=parseFloat(b.getAttribute('data-d')||'.6'),am=b.getAttribute('data-a');am=am?JSON.parse(am):null;
var a=ctx(),t=a.currentTime+.05;steps.forEach(function(st){var n=st.length;st.forEach(function(c,i){voice(BASE*Math.pow(2,c/1200),t,d,kind,(am?am[i]:1)*.2/Math.max(1,n*.75))});t+=d+.08})})})})();</script>"""


def btn(label, steps, kind="rich", dur=0.6, amps=None):
    a = f" data-a='{esc(json.dumps(amps))}'" if amps else ""
    s = [[round(c, 3) for c in st] for st in steps]
    return f"<button type='button' data-p='{esc(json.dumps(s))}' data-t='{kind}' data-d='{dur}'{a}>▶ {esc(label)}</button>"


def harmonics_svg(k: bool) -> str:
    width, height, L, R = 900, 96, 14, 14
    hi = 4900
    X = lambda v: L + v / hi * (width - L - R)  # noqa: E731
    o = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{"배음 1~16의 높이" if k else "Heights of harmonics 1-16"}">']
    for s in range(0, 49):
        x = X(s * 100)
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="40" y2="{56 if s % 12 == 0 else 50}" stroke="var(--fg3)" stroke-opacity=".45" stroke-width="{1.4 if s % 12 == 0 else .7}"/>')
        if s % 12 == 0:
            o.append(f'<text x="{x:.1f}" y="{height - 22}" text-anchor="middle">{s * 100}</text>')
    o.append(f'<text x="{X(4800) + 12:.1f}" y="{height - 22}">{"센트" if k else "cents"}</text>')
    o.append(f'<text x="{X(0):.1f}" y="{height - 4}" style="fill:var(--fg3)">{"가로: 바탕음(1배음)에서 잰 높이. 회색 눈금은 12평균율(100센트 간격), 굵은 눈금은 옥타브." if k else "Across: height above the fundamental (harmonic 1). Gray ticks: equal temperament (100 cents apart); bold ticks: octaves."}</text>')
    o.append(f'<line x1="{X(0):.1f}" x2="{X(4800):.1f}" y1="45" y2="45" stroke="var(--fg3)" stroke-opacity=".5"/>')
    for n in HARM:
        c, dv = cents(n), harm_dev(n)
        tip = (f"{n}배음 · 바탕음에서 {c:.1f}센트 · 가장 가까운 평균율 음과 {dv:+.1f}센트" if k
               else f"harmonic {n} · {c:.1f} cents above the fundamental · {dv:+.1f} cents from the nearest equal-tempered note")
        o.append(f'<circle cx="{X(c):.1f}" cy="45" r="5" fill="var(--g1)" stroke="var(--card)" stroke-width="1.2"><title>{esc(tip)}</title></circle>')
        o.append(f'<text x="{X(c):.1f}" y="{30 if n % 2 else 20}" text-anchor="middle">{n}</text>')
    o.append("</svg>")
    return "".join(o)


def table(head, rows, num_cols=()):
    th = "".join(f"<th{' class=num' if i in num_cols else ''}>{h}</th>" for i, h in enumerate(head))
    tr = "".join("<tr>" + "".join(f"<td{' class=num' if i in num_cols else ''}>{c}</td>" for i, c in enumerate(r)) + "</tr>" for r in rows)
    return f"<div class='wrap'><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>"


def section(k: bool) -> str:
    b = [f"<style>{CSS}</style><div class='primer'>"]
    T = (lambda ko, en: ko if k else en)  # noqa: E731
    b.append("<p>" + T("이 절은 아래 띠 그림들을 읽는 데 필요한 계산을 모았다. 음정을 진동수의 비로 나타내는 법, 비가 작은 정수일 때 무엇이 다른지, 피타고라스 음률·삼분손익·순정률·평균율이 각각 어떤 식으로 음을 정하는지, 그 차이가 딴이름 한소리(이명동음)에서 어떻게 드러나는지를 차례로 다룬다. 값은 모두 정의에서 계산한 것이고 잰 값이 아니다. 단추는 가온 다(261.63 Hz) 위에서 소리를 낸다.",
                       "This section gathers the arithmetic behind the rulers below: how an interval is written as a ratio of frequencies, what changes when the ratio is one of small whole numbers, how Pythagorean tuning, sanfen sunyi, just intonation and equal temperament each fix their notes, and how the difference shows in enharmonic pairs. Every value is computed from a definition, not measured. The buttons sound above middle C (261.63 Hz).") + "</p>")

    # A
    b.append(f"<h3 id='ratios-cents'>{T('진동수의 비와 센트', 'Frequency ratios and cents')}</h3>")
    b.append("<p>" + T("음의 높이는 1초에 몇 번 떠는가(진동수, 단위 Hz — 헤르츠, 1초에 떠는 횟수)로 잰다. 두 음의 음정은 진동수의 차가 아니라 비로 정해진다(아래 식에서 f₁·f₂는 두 음의 진동수). 가온 다(피아노 건반 가운데의 다, C4 — 261.63 Hz)에서 옥타브 위 다(523.26 Hz)까지는 261.63 Hz, 그 옥타브 위 다(1046.52 Hz)까지는 523.26 Hz로 차는 두 배가 되지만 비는 둘 다 2:1이다. 센트는 이 비를 로그로 바꾼 단위다. log₂ x는 2를 몇 제곱해야 x가 되는가를 나타내는 수다(log₂ 2 = 1, log₂ 4 = 2).",
                       "Pitch is measured by how many times a second a sound vibrates (frequency, in hertz, Hz: vibrations per second). The interval between two notes is fixed by the ratio of their frequencies, not the difference (f₁ and f₂ below are the two frequencies). From middle C (the C near the middle of the piano keyboard, C4: 261.63 Hz) to the C an octave up (523.26 Hz) the difference is 261.63 Hz, and to the next C (1046.52 Hz) it is 523.26 Hz, twice as much; the ratio is 2:1 both times. The cent turns the ratio into a logarithm: log₂ x is the power to which 2 must be raised to give x (log₂ 2 = 1, log₂ 4 = 2).") + "</p>")
    b.append("<p class='formula'>" + T("센트 = 1200 × log₂(f₂ ÷ f₁)", "cents = 1200 × log₂(f₂ ÷ f₁)") + "<br>"
             + T(f"예: 3:2 → 1200 × log₂ 1.5 = 1200 × 0.58496 = {cents(F(3, 2)):.2f}센트 · 비 2 → 1200센트 · 비 2^(1/12) = 1.05946 → 100센트",
                 f"e.g. 3:2 → 1200 × log₂ 1.5 = 1200 × 0.58496 = {cents(F(3, 2)):.2f} cents · ratio 2 → 1,200 cents · ratio 2^(1/12) = 1.05946 → 100 cents") + "<br>"
             + T(f"비를 곱하면 센트는 더해진다. 완전5도(3/2) 위에 완전4도(4/3)를 쌓으면 옥타브다: 3/2 × 4/3 = 2 → {cents(F(3, 2)):.2f} + {cents(F(4, 3)):.2f} = 1200",
                 f"Ratios multiply, cents add. A perfect fifth (3/2) with a perfect fourth (4/3) on top makes an octave: 3/2 × 4/3 = 2 → {cents(F(3, 2)):.2f} + {cents(F(4, 3)):.2f} = 1,200") + "</p>")
    b.append(ratio_axes_svg(k))
    st1, st11 = 2 ** (1 / 12) - 1, 2 - 2 ** (11 / 12)
    b.append("<p class='src'>" + T(f"평균율 반음 하나는 진동수에 2^(1/12) = 1.0595를 곱하는 것이다. 그래서 위의 비 눈금에서는 반음 간격이 오른쪽으로 갈수록 넓어지고(첫 반음 1 → 1.0595는 {st1:.4f}, 마지막 반음 1.8877 → 2는 {st11:.4f}), 아래 센트 눈금에서는 모두 100센트로 같다. 센트는 비를 곱하는 일을 더하는 일로 바꾼 눈금이다. 색 점과 점선은 아래 표의 기본 순정 비 열두 개다. 아래 센트 눈금에서 색 점이 가장 가까운 회색 선 끝에서 떨어진 가로 거리가 평균율과의 차이다.",
                                   f"An equal-tempered semitone multiplies the frequency by 2^(1/12) = 1.0595. On the ratio ruler above, the semitones therefore widen toward the right (the first, 1 → 1.0595, spans {st1:.4f}; the last, 1.8877 → 2, spans {st11:.4f}), while on the cent ruler below each is 100 cents. Cents turn multiplying ratios into adding. The colored dots and dashed lines are the twelve main just ratios of the table below. On the cent ruler, the horizontal distance from a colored dot to the end of the nearest gray line is its difference from equal temperament.") + "</p>")
    b.append("<p>" + T("아래 표의 줄은 한 줄을 빼고 손으로 고르지 않았다. 「네 가지 계산법」의 순정률 장음계(도~시) 안에서 두 음 사이(한 옥타브까지)에 나오는 음정을 모두 모아, 같은 크기(반음 수)끼리 가장 단순한 비(분자+분모가 작은 것)를 기본 줄로, 나머지를 「다른 비」 줄로 두었다. 순정률에서는 이름이 같은 음정도 어느 두 음 사이냐에 따라 비가 다르다. 예를 들어 도–솔은 3/2인데 레–라는 40/27로 신토닉 쉼표(81/80)만큼 좁다. 빼놓은 한 줄은 7/4다. 장음계에는 없고 7배음과 4배음 사이의 비(배음은 다음 소절)라서, 배음 소절과 잇기 위해 일부러 더했다. 증4도는 완전4도보다 반음 넓고 감5도는 완전5도보다 반음 좁은 음정이다. 「나오는 곳」 칸의 ′는 한 옥타브 위 음이다(도′는 위 도). 괄호 안의 맥놀이 값은 계산으로만 나오는 값이고 이 단추 소리로는 들리지 않는다(아래 문단). 표 위 단추로 순서를 바꿀 수 있다.",
                       "The rows of the table below are not chosen by hand, with one exception. They are every interval between two notes (up to an octave) of the just major scale of 'Four ways of computing the notes'; for each size (in semitones) the simplest ratio (smallest numerator + denominator) is the main row and the others are 'other ratio' rows. In just intonation an interval of the same name can have different ratios depending on which two notes it joins: C–G is 3/2, but D–A is 40/27, narrower by the syntonic comma (81/80). The exception is 7/4: it is not in the major scale but is the ratio between the 7th and 4th harmonics (harmonics are the next subsection), added on purpose to connect with that subsection. An augmented fourth is a semitone wider than a perfect fourth, a diminished fifth a semitone narrower than a perfect fifth. In the 'Where it occurs' column ′ marks the octave above (C′ is the upper C). Beats in parentheses come from the arithmetic only and cannot be heard with these buttons (see the paragraph below). The buttons above the table change the order.") + "</p>")
    b.append(interval_table(k) + SORT_JS % json.dumps({"size": T("지금 순서: 크기 순(반음 수, 같은 반음이면 센트가 작은 쪽부터).", "Current order: by size (semitones, then cents)."),
                                                       "simple": T("지금 순서: 단순한 비 순(분자+분모가 작은 쪽부터).", "Current order: simplest ratio first (smallest numerator + denominator)."),
                                                       "dev": T("지금 순서: 평균율과의 차이(센트, 부호 무시)가 큰 쪽부터.", "Current order: furthest from equal temperament first (cents, either direction)."),
                                                       "beat": T("지금 순서: 맥놀이가 많은 쪽부터(괄호 값은 이 단추 소리로 들리지 않아 맨 뒤).", "Current order: most beats first (values in parentheses, inaudible with these buttons, last).")}, ensure_ascii=False))
    t3, t5 = et_beats(F(5, 4), 4), et_beats(F(3, 2), 7)
    b.append("<p>" + T(f"진동수가 조금 다른 두 음이 함께 울리면 소리가 1초에 그 진동수 차만큼 커졌다 작아진다. 이것이 맥놀이다. 비 p/q(p는 분자, q는 분모)인 음정에서는 아래 음의 p번째 배음과 위 음의 q번째 배음이 같은 높이에 온다(배음은 다음 소절). 순정으로 맞추면 이 두 배음이 꼭 겹쳐 그 사이에는 맥놀이가 없고(다른 배음끼리 가까우면 거칠음은 남을 수 있다), 평균율로 맞추면 조금 어긋나 표의 횟수만큼 맥놀이가 생긴다. 가온 다 위 평균율 장3도에서는 아래 음의 5배음(5 × 261.63 = 1308.2 Hz)과 위 음의 4배음(4 × 329.63 = 1318.5 Hz)이 1초에 {t3:.1f}번, 평균율 5도에서는 {t5:.1f}번 맥놀이를 낸다. 헬름홀츠는 2·3배음이 세고 4·5배음은 중간쯤이며 그보다 높은 배음은 빨리 약해지는 음색을 가정하고, 두 음을 함께 울릴 때 배음 사이의 맥놀이가 생기지 않거나 아주 약하게만 생기는 진동수 비를 협화(두 음이 함께 울릴 때 거칠지 않고 어울리는 것)라 불렀다(『음감각론』 엘리스 영역 3판, 1895, 10장, 194쪽). 표에서 괄호 안의 값은 겹치는 배음이 8번째보다 위(비 p/q의 p가 8보다 큼)라서, 이 단추의 소리(1~8배음)로는 들리지 않는 맥놀이다. 계산으로는 생긴다.",
                       f"When two tones of slightly different frequency sound together, the sound swells and fades as many times a second as their frequencies differ: these are beats. In an interval of ratio p/q (p the numerator, q the denominator) the p-th harmonic of the lower tone and the q-th harmonic of the upper tone fall at the same height (harmonics are the next subsection). Tuned just, these two harmonics coincide and do not beat against each other (other harmonics that lie close may still leave some roughness); tuned equal, they miss slightly and beat as often as the table says. In an equal-tempered major third above middle C, the lower tone's 5th harmonic (5 × 261.63 = 1308.2 Hz) and the upper tone's 4th (4 × 329.63 = 1318.5 Hz) beat {t3:.1f} times a second; in an equal-tempered fifth, {t5:.1f} times. Assuming a quality of tone whose 2nd and 3rd partials are strong, 4th and 5th moderate and higher ones rapidly weaker, Helmholtz called consonances those ratios at which two tones sounded together form no beats between their partials, or only very weak ones (On the Sensations of Tone, tr. Ellis, 3rd ed., 1895, ch. X, p. 194). Values in parentheses are beats between harmonics above the 8th (p greater than 8 in the ratio p/q); they exist in the arithmetic but cannot be heard with these buttons, whose tone stops at the 8th harmonic.") + "</p>")

    # B
    b.append(f"<h3 id='ratios-harmonics'>{T('배음', 'Harmonics')}</h3>")
    b.append("<p>" + T("현이나 관의 음은 진동수 f인 순음(배음 없이 진동수가 하나뿐인 소리) 하나가 아니라, 대개 f, 2f, 3f, 4f …의 순음이 겹친 것으로 나타낼 수 있다. 이 성분 하나하나를 배음(倍音)이라 하고, 늘어선 것을 배음렬이라 한다. 이상적인 경우 양끝을 고정한 고르고 유연한 현과 양끝이 열린 고른 원통 관은 정수배 진동을 모두 낼 수 있고, 한끝이 막힌 고른 원통 관은 홀수배(f, 3f, 5f …)만 낼 수 있다. 낼 수 있는 진동이 모두 실제로 울리는 것은 아니다. 실제 악기는 재질과 모양 때문에 이 값에서 조금씩 벗어나고 배음마다 세기도 다르다. 이 면에는 실제 악기의 배음을 잰 값은 아직 싣지 않았다.",
                       "A note from a string or a pipe is usually not one pure tone (a sound with a single frequency and no harmonics) of frequency f but can be written as pure tones at f, 2f, 3f, 4f … sounding together. Each component is a harmonic, and the row of them is the harmonic series. In the ideal case a uniform flexible string fixed at both ends and a uniform cylindrical pipe open at both ends can vibrate at every whole multiple, and a uniform cylindrical pipe closed at one end at odd multiples only (f, 3f, 5f …); not every possible mode actually sounds. Real instruments depart a little from these values because of their material and shape, and their harmonics differ in strength. Measured harmonics of real instruments are not on this page yet.") + "</p>")
    b.append(harmonics_svg(k))
    b.append("<p class='src'>" + T(f"점 하나가 배음 하나다(위의 숫자가 n). 2·4·8·16배음은 바탕음의 옥타브들이고, 3배음은 옥타브와 5도 위({cents(3):.1f}센트), 5배음은 두 옥타브와 장3도 위({cents(5):.1f}센트)다. 이웃한 배음 사이 음정이 2:1, 3:2, 4:3, 5:4, 6:5 — 앞의 표의 작은 정수비 음정이 배음렬 앞쪽에 차례로 나온다. 7배음({cents(7):.1f}센트)은 가장 가까운 평균율 음보다 {abs(harm_dev(7)):.1f}센트 낮고, 11배음은 {abs(harm_dev(11)):.1f}센트 어긋나 평균율 두 음의 거의 한가운데에 온다. 점에 마우스를 올리면 값이 나온다.",
                                   f"Each dot is a harmonic (n above it). Harmonics 2, 4, 8 and 16 are octaves of the fundamental; the 3rd lies an octave and a fifth up ({cents(3):.1f} cents), the 5th two octaves and a major third up ({cents(5):.1f}). The intervals between neighboring harmonics are 2:1, 3:2, 4:3, 5:4, 6:5: the small-number intervals of the table above appear in order at the start of the series. The 7th harmonic ({cents(7):.1f} cents) lies {abs(harm_dev(7)):.1f} cents below the nearest equal-tempered note, and the 11th is {abs(harm_dev(11)):.1f} cents off, nearly halfway between two. Hover over a dot for its values.") + "</p>")
    hs = [cents(n) for n in range(1, 9)]
    b.append("<div class='btns'>" + btn(T("배음 1~8을 차례로(순음)", "harmonics 1-8 in turn (pure tones)"), [[c] for c in hs], kind="sine", dur=0.55)
             + btn(T("1~8을 함께(진폭 1/n)", "1-8 together (amplitude 1/n)"), [hs], kind="sine", dur=2.4, amps=[1 / n * 2.2 for n in range(1, 9)])
             + btn(T("바탕음만(순음)", "fundamental alone (pure tone)"), [[0]], kind="sine", dur=1.6)
             + btn(T("삼각파(이 면의 다른 단추 소리)", "triangle wave (the other buttons on this page)"), [[0]], kind="triangle", dur=1.6) + "</div>")
    b.append("<p class='src'>" + T("이 면의 다른 단추는 삼각파로 소리를 낸다. 삼각파는 홀수 배음만 있고 n번째 배음의 진폭이 1/n²로 줄어든다. 장3도(5:4)의 맥놀이를 만드는 것은 위 음의 4배음인데 삼각파에는 이것이 없어서, 위 표의 장3도 맥놀이는 삼각파로 함께 울려서는 생기지 않는다(다른 홀수 배음끼리의 약한 거칠음은 남을 수 있다). 그래서 이 절에서 두 음 이상을 함께 비교하는 단추는 1~8배음을 진폭 1/n으로 합친 소리를 쓴다(배음을 하나씩 들려주는 위의 단추는 순음을 쓴다).",
                                   "The other buttons on this page use a triangle wave, which has odd harmonics only, the n-th at amplitude 1/n². The beats of the major third (5:4) come from the upper tone's 4th harmonic, which a triangle wave lacks, so the major-third beats in the table above do not arise in a triangle wave (some faint roughness between other odd harmonics may remain). The buttons in this section that compare two or more notes together therefore use harmonics 1-8 at amplitude 1/n (the buttons above that play harmonics one by one use pure tones).") + "</p>")

    # C
    b.append(f"<h3 id='ratios-three'>{T('네 가지 계산법', 'Four ways of computing the notes')}</h3>")
    b.append("<p><b>" + T("피타고라스 음률", "Pythagorean tuning") + "</b> — " + T("순정 5도(3:2)만 쌓고, 1과 2 사이에 들도록 옥타브(2)로 나눈다.", "stack pure fifths (3:2) only, and divide by octaves (2) to bring each into the range 1 to 2.") + "</p>")
    b.append("<p class='formula'>" + T("음 = (3/2)ᵏ ÷ 2ᵐ (k: 쌓은 5도 수, m: 내린 옥타브 수)", "note = (3/2)ᵏ ÷ 2ᵐ (k fifths stacked, m octaves taken off)") + "<br>"
             + T(f"예: 미(E) = (3/2)⁴ ÷ 2² = 81/16 ÷ 4 = 81/64 → {cents(F(81, 64)):.1f}센트 · 파(F) = (3/2)⁻¹ × 2 = 4/3",
                 f"e.g. E = (3/2)⁴ ÷ 2² = 81/16 ÷ 4 = 81/64 → {cents(F(81, 64)):.1f} cents · F = (3/2)⁻¹ × 2 = 4/3") + "<br>"
             + T(f"5도 12개 = (3/2)¹² = 129.746, 옥타브 7개 = 2⁷ = 128 → 둘의 비 531441/524288 = {float(COMMA):.5f} → {cents(COMMA):.2f}센트(피타고라스 쉼표 — 「쉼표」는 악보의 쉼표가 아니라 두 음정의 작은 차이를 가리키는 「콤마」를 옮긴 말이다). 3을 한 번 이상 곱한 수는 홀수이고 2를 한 번 이상 곱한 수는 짝수라 둘은 같아질 수 없으므로, 5도를 몇 번 쌓아도 옥타브 몇 개와 꼭 맞지 않는다.",
                 f"12 fifths = (3/2)¹² = 129.746, 7 octaves = 2⁷ = 128 → their ratio 531441/524288 = {float(COMMA):.5f} → {cents(COMMA):.2f} cents (the Pythagorean comma). A positive power of 3 is odd and a positive power of 2 even, so they can never be equal: no number of stacked fifths ever matches a whole number of octaves.") + "</p>")

    b.append("<p><b>" + T("삼분손익", "Sanfen sunyi (三分損益)") + "</b> — " + T("율관(율의 기준 음을 내는 관)의 길이를 셋으로 나누어 한 몫을 덜거나(손, 損) 더해(익, 益) 다음 율을 얻는다. 『사기』 「율서」는 81에서 시작한다.",
                                                                    "divide the length of a pitch pipe (the pipe that sounds a lü's reference note) into three and take away one part (sun, 損) or add one (yi, 益) to get the next pipe. The Shiji 'Lüshu' starts from 81.") + "</p>")
    b.append("<blockquote><p lang='zh-Hant'>律數：九九八十一以爲宮。三分去一，五十四以爲徴。三分益一，七十二以爲商。三分去一，四十八以爲羽。三分益一，六十四以爲角。</p>"
             + (("<p>(독음) 율수: 구구팔십일 이위궁. 삼분거일, 오십사 이위치. 삼분익일, 칠십이 이위상. 삼분거일, 사십팔 이위우. 삼분익일, 육십사 이위각.</p>"
                 "<p>(해석) 율의 수: 9×9=81을 궁으로 삼는다. 셋으로 나누어 하나를 덜어 54를 치로 삼는다. 셋으로 나누어 하나를 더해 72를 상으로 삼는다. 셋으로 나누어 하나를 덜어 48을 우로 삼는다. 셋으로 나누어 하나를 더해 64를 각으로 삼는다.</p>") if k else
                "<p>(Translation) The lü numbers: nine times nine, 81, is taken as gong. Divide into three and take away one: 54 is zhi. Divide into three and add one: 72 is shang. Take away one: 48 is yu. Add one: 64 is jue.</p>")
             + "<p class='src'>" + T("사마천, 『사기』 권25 「율서」(위키문헌 판 2687752)", "Sima Qian, Shiji 25, 'Lüshu' (zh.wikisource revision 2687752)") + "</p></blockquote>")
    b.append("<p>" + T("열두 율은 『여씨춘추』 「음률」이 적은 차례로 이렇게 이어진다.", "The Lüshi chunqiu, 'Yinlü', gives the order in which the twelve pipes follow one another:") + "</p>")
    b.append("<blockquote><p lang='zh-Hant'>黃鐘生林鐘，林鐘生太蔟，太蔟生南呂，南呂生姑洗，姑洗生應鐘，應鐘生蕤賓，蕤賓生大呂，大呂生夷則，夷則生夾鐘，夾鐘生無射，無射生仲呂。三分所生，益之一分以上生；三分所生，去其一分以下生。黃鐘、（太）〔大〕呂、太蔟、夾鐘、姑洗、仲呂、蕤賓為上，林鐘、夷則、南呂、無射、應鐘為下。</p>"
             + (("<p>(독음) 황종생임종, 임종생태주, 태주생남려, 남려생고선, 고선생응종, 응종생유빈, 유빈생대려, 대려생이칙, 이칙생협종, 협종생무역, 무역생중려. 삼분소생, 익지일분이상생; 삼분소생, 거기일분이하생. 황종·대려·태주·협종·고선·중려·유빈위상, 임종·이칙·남려·무역·응종위하.</p>"
                 "<p>(해석) 황종이 임종을 낳고, 임종이 태주를, 태주가 남려를, 남려가 고선을, 고선이 응종을, 응종이 유빈을, 유빈이 대려를, 대려가 이칙을, 이칙이 협종을, 협종이 무역을, 무역이 중려를 낳는다. 셋으로 나누어 낳을 때 한 몫을 더하면 위로 낳고(상생), 한 몫을 덜면 아래로 낳는다(하생). 황종·대려·태주·협종·고선·중려·유빈은 위(上)이고, 임종·이칙·남려·무역·응종은 아래(下)이다.</p>") if k else
                "<p>(Translation) Huangzhong begets linzhong, linzhong taicou, taicou nanlü, nanlü guxian, guxian yingzhong, yingzhong ruibin, ruibin dalü, dalü yize, yize jiazhong, jiazhong wuyi, wuyi zhonglü. In begetting by thirds, adding one part begets upward (shangsheng); taking away one part begets downward (xiasheng). Huangzhong, dalü, taicou, jiazhong, guxian, zhonglü and ruibin are upper; linzhong, yize, nanlü, wuyi and yingzhong are lower.</p>")
             + "<p class='src'>" + T("『여씨춘추』 권6 「계하기」 「음률」(위키문헌 판 2327717). 괄호는 위키문헌 판의 교감 표시로, 太를 大로 고쳐 읽은 것이다.", "Lüshi chunqiu 6, 'Jixia ji', 'Yinlü' (zh.wikisource revision 2327717). The brackets are the edition's emendation of 太 to 大.") + "</p></blockquote>")
    lt = lu_table()
    long_up = min(float(r["length"]) for r in lt if r["hanja"] in LU_UP)
    long_dn = max(float(r["length"]) for r in lt if r["hanja"] not in LU_UP)
    b.append("<p class='formula'>" + T("손(덜기): 길이 × 2/3 → 진동수 × 3/2(5도 위) · 익(더하기): 길이 × 4/3 → 진동수 × 3/4(4도 아래, 곧 5도 위에서 옥타브 아래)",
                                       "sun (take away): length × 2/3 → frequency × 3/2 (a fifth up) · yi (add): length × 4/3 → frequency × 3/4 (a fourth down: a fifth up, then an octave down)") + "</p>")
    rows = []
    for i, r in enumerate(lt):
        op = {"sun": T("손 ×2/3", "sun ×2/3"), "yi": T("익 ×4/3", "yi ×4/3"), None: "—"}[r["op"]]
        rows.append([str(i + 1), f"{r['hanja']} {r['ko'] if k else ''}".strip(), op, frac(r["length"]), f"{float(r['length']):.3f}",
                     frac(r["ratio"]), f"{r['cents']:.1f}", r["pitch"], T("위" if r["hanja"] in LU_UP else "아래", "upper" if r["hanja"] in LU_UP else "lower")])
    b.append(table([T("차례", "Order"), T("율", "Pipe"), T("셈", "Step"), T("길이(분수)", "Length (fraction)"), T("길이", "Length"),
                    T("진동수 비(81 ÷ 길이)", "Frequency ratio (81 ÷ length)"), T("센트", "Cents"), T("황종을 C로 놓을 때", "With huangzhong on C"), T("상·하", "Upper/lower")],
                   rows, num_cols=(0, 4, 6)))
    nxt, gap = lu_next()
    b.append("<p>" + T(f"원문의 「위로 낳는다(상생)」·「아래로 낳는다(하생)」를 음높이로 읽으면 계산과 반대가 된다. 상생(익)은 율관을 길게 해 음을 4도 낮추고, 하생(손)은 짧게 해 음을 5도 높인다. 이 계산에서는 원문이 「위」로 꼽은 일곱 율이 모두 「아래」 다섯보다 긴 율관이다. 원문이 위·아래로 무엇을 가리켰는지를 원문만으로 정할 수는 없고, 여기서는 계산이 율관의 길이와 맞는다는 것만 적는다. 율관의 길이와 진동수는 반비례한다고 놓았다(같은 종류·같은 조건의 고른 원통 관이고 관 끝의 보정을 무시한 이상적인 경우). 그러면 손은 5도 위, 익은 4도 아래가 되어 삼분손익은 피타고라스 음률과 같은 값을 낸다(임종 702.0, 태주 203.9 …). 손과 익이 늘 번갈아 오지는 않는다. 원문은 대려를 「위」에 넣었으므로 유빈에서 대려를 낳는 것은 상생, 곧 익이다. 그래서 응종→유빈에 이어 익이 두 번 이어지고, 열두 율관의 길이가 모두 황종(81)과 그 반(40.5) 사이에 든다(유빈에서 손을 썼다면 37.9로 그 밖에 나간다). 길이로 보면 「위」 일곱은 {long_up:.1f} 이상, 「아래」 다섯은 {long_dn:.1f} 이하다. 중려에서 한 번 더 덜면 길이 {float(nxt):.3f}이 나오는데, 황종의 반(40.5)보다 짧아 청황종(한 옥타브 위 황종)보다 {gap:.2f}센트 높다. 피타고라스 쉼표만큼 열두 율이 닫히지 않는 것이다. 12번째 율 중려가 4/3(498.0센트)이 아니라 {lt[-1]['cents']:.1f}센트에 오는 까닭도 같다.",
                       f"Read as pitch, the text's \"begets upward\" (shangsheng) and \"begets downward\" (xiasheng) run against the arithmetic: shangsheng (yi) lengthens the pipe and lowers the note by a fourth, xiasheng (sun) shortens it and raises the note by a fifth. In this arithmetic the seven pipes the text calls upper are all longer than the five it calls lower. What the text meant by upper and lower cannot be settled from the text alone; the page only notes that the arithmetic matches pipe length. Pipe length is taken as inversely proportional to frequency (ideal uniform cylindrical pipes of the same kind and conditions, without the end correction). Sun is then a fifth up and yi a fourth down, so sanfen sunyi gives the same values as Pythagorean tuning (linzhong 702.0, taicou 203.9, …). Sun and yi do not always alternate. The text puts dalü among the upper pipes, so ruibin begets dalü by shangsheng, that is by yi; yi thus comes twice in a row (yingzhong to ruibin, ruibin to dalü), and every one of the twelve pipes stays between huangzhong (81) and half of it (40.5) (sun at ruibin would give 37.9, outside that range). By length the seven 'upper' pipes are {long_up:.1f} or longer and the five 'lower' ones {long_dn:.1f} or shorter. One more sun after zhonglü gives a length of {float(nxt):.3f}, shorter than half of huangzhong (40.5), so {gap:.2f} cents above huangzhong an octave up: by the Pythagorean comma the twelve pipes fail to close. The same is why the twelfth pipe, zhonglü, lies at {lt[-1]['cents']:.1f} cents rather than at 4/3 (498.0 cents).") + "</p>")

    b.append("<p><b>" + T("순정률", "Just intonation") + "</b> — " + T("장3화음 도·미·솔을 진동수 4:5:6으로 맞추고, 같은 화음을 파와 솔 위에도 세워 일곱 음을 얻는다.", "tune the major triad C–E–G to frequencies 4:5:6 and build the same triad on F and G to get seven notes.") + "</p>")
    b.append("<p class='formula'>" + T("도:미:솔 = 4:5:6 → 미 5/4, 솔 3/2 · 파:라:도′ = 4:5:6, 파 4/3 → 라 = 4/3 × 5/4 = 5/3 · 솔:시:레′ = 4:5:6 → 시 = 3/2 × 5/4 = 15/8, 레 = 3/2 × 3/2 ÷ 2 = 9/8",
                                       "C:E:G = 4:5:6 → E 5/4, G 3/2 · F:A:C′ = 4:5:6, F 4/3 → A = 4/3 × 5/4 = 5/3 · G:B:D′ = 4:5:6 → B = 3/2 × 5/4 = 15/8, D = 3/2 × 3/2 ÷ 2 = 9/8") + "<br>"
             + T(f"이웃한 음 사이: 9/8({cents(F(9, 8)):.1f}센트), 10/9({cents(F(10, 9)):.1f}센트), 16/15({cents(F(16, 15)):.1f}센트) — 온음이 두 가지 크기다. 피타고라스의 장3도 81/64와 순정 5/4의 비 81/80 = {cents(SYNTONIC):.2f}센트(신토닉 쉼표).",
                 f"Between neighbors: 9/8 ({cents(F(9, 8)):.1f} cents), 10/9 ({cents(F(10, 9)):.1f}), 16/15 ({cents(F(16, 15)):.1f}): whole tones come in two sizes. The Pythagorean third 81/64 and the just 5/4 differ by 81/80 = {cents(SYNTONIC):.2f} cents (the syntonic comma).") + "</p>")
    b.append("<p><b>" + T("12평균율", "Twelve-tone equal temperament") + "</b> — " + T("옥타브를 같은 비의 반음 열둘로 나눈다.", "divide the octave into twelve semitones of the same ratio.") + "</p>")
    b.append("<p class='formula'>" + T(f"반음 = 2^(1/12) = {2 ** (1 / 12):.6f} · k번째 음 = 2^(k/12) · 5도 = 2^(7/12) = {2 ** (7 / 12):.5f}(3/2 = 1.5보다 {cents(F(3, 2)) - 700:.2f}센트 좁다) · 장3도 = 2^(4/12) = {2 ** (4 / 12):.5f}(5/4 = 1.25보다 {400 - cents(F(5, 4)):.2f}센트 넓다)",
                                       f"semitone = 2^(1/12) = {2 ** (1 / 12):.6f} · k-th note = 2^(k/12) · fifth = 2^(7/12) = {2 ** (7 / 12):.5f} ({cents(F(3, 2)) - 700:.2f} cents narrower than 3/2) · major third = 2^(4/12) = {2 ** (4 / 12):.5f} ({400 - cents(F(5, 4)):.2f} cents wider than 5/4)") + "<br>"
             + T("한 옥타브 안에서 동음과 옥타브를 뺀 모든 음정의 비가 무리수다. 어느 조로 옮겨도 음정의 크기가 같은 대신, 동음과 옥타브 말고는 순정 비와 꼭 맞는 음정이 없다.",
                 "Within an octave every ratio except the unison and the octave is irrational. Intervals keep their size in every key, but apart from the unison and the octave none matches a whole-number ratio exactly.") + "</p>")
    rows = []
    for nm, nk in zip(MAJOR, MAJOR_KO):
        p, j, e = pyth(nm), JUST[nm], ET_SEMI[nm] * 100
        rows.append([f"{nk} ({nm})" if k else nm, frac(p), f"{cents(p):.1f}", frac(j), f"{cents(j):.1f}", f"2^({ET_SEMI[nm]}/12)", f"{e}",
                     f"{cents(p) - e:+.1f}", f"{cents(j) - e:+.1f}"])
    b.append(table([T("음", "Note"), T("피타고라스 비", "Pythagorean ratio"), T("센트", "Cents"), T("순정률 비", "Just ratio"), T("센트", "Cents"),
                    T("평균율 비", "Equal ratio"), T("센트", "Cents"), T("피타고라스 − 평균율", "Pythagorean − equal"), T("순정 − 평균율", "Just − equal")],
                   rows, num_cols=(2, 4, 6, 7, 8)))
    sys3 = [("pyth", T("피타고라스", "Pythagorean"), [cents(pyth(n)) for n in MAJOR] + [1200]),
            ("just", T("순정률", "just"), [cents(JUST[n]) for n in MAJOR] + [1200]),
            ("et", T("평균율", "equal"), [ET_SEMI[n] * 100 for n in MAJOR] + [1200])]
    b.append("<div class='btns'>" + "".join(btn(T(f"{lab} 음계", f"{lab} scale"), [[c] for c in cs], dur=0.45) for _, lab, cs in sys3)
             + "".join(btn(T(f"{lab} 도·미·솔 함께", f"{lab} C–E–G together"), [[cs[0], cs[2], cs[4]]], dur=2.8) for _, lab, cs in sys3) + "</div>")
    b.append("<p class='src'>" + T("도·미·솔을 함께 울리면 미가 순정률보다 피타고라스는 21.5센트, 평균율은 13.7센트 높아 맥놀이가 들린다. 이 표의 피타고라스 칸은 파를 5도 아래(4/3, 498.0센트)에서 얻었다. 황종에서 위로만 쌓는 삼분손익 열두 율에는 4/3이 없고, 그 자리에 중려(521.5센트)가 온다. 나머지 여섯 음(도·레·미·솔·라·시)은 두 계산이 같다. 아래 <a href='#western-tuning'>1절</a>의 피타고라스 줄은 이 표의 값을, <a href='#east-asia'>2절</a>의 삼분손익 12율 줄은 중려를 그린다.",
                                   "Played together, C–E–G beats in the Pythagorean and equal versions, whose E lies 21.5 and 13.7 cents above the just E. The Pythagorean column takes F from a fifth below (4/3, 498.0 cents). The twelve pipes of sanfen sunyi, stacked upward only from huangzhong, have no 4/3; zhonglü (521.5 cents) takes its place. The other six notes (C, D, E, G, A, B) are the same in both. Below, the Pythagorean row of <a href='#western-tuning'>section 1</a> draws this table's values, and the sanfen sunyi row of <a href='#east-asia'>section 2</a> draws zhonglü.") + "</p>")

    # D
    b.append(f"<h3 id='ratios-enharmonic'>{T('딴이름 한소리(이명동음)', 'Enharmonic notes')}</h3>")
    pc, pd = ENH["pyth"]
    jc, jd = ENH["just"]
    b.append("<p>" + T("C♯과 D♭(우리말 음이름으로 올림다·내림라. 음이름 다·라·마·바·사·가·나가 C·D·E·F·G·A·B다)은 피아노에서 같은 건반이고, 12평균율에서는 둘 다 가온 다보다 100센트 높아 이름은 다르고 소리는 같은 딴이름 한소리다. 아래 두 비율 계산에서는 두 음을 따로 계산하면 값이 갈린다.",
                       "C♯ and D♭ share a key on the piano, and in equal temperament both lie 100 cents above middle C. There the two names give one sound. In the two ratio calculations below, computing the two notes separately gives different values.") + "</p>")
    b.append("<p class='formula'>"
             + T(f"피타고라스: C♯ = 5도 7개 위 = 3⁷/2¹¹ = {frac(pc)} → {cents(pc):.1f}센트 · D♭ = 5도 5개 아래 = 2⁸/3⁵ = {frac(pd)} → {cents(pd):.1f}센트 · C♯이 D♭보다 {cents(pc) - cents(pd):.1f}센트 높다(두 음의 비 3¹²/2¹⁹ = 피타고라스 쉼표)",
                 f"Pythagorean: C♯ = 7 fifths up = 3⁷/2¹¹ = {frac(pc)} → {cents(pc):.1f} cents · D♭ = 5 fifths down = 2⁸/3⁵ = {frac(pd)} → {cents(pd):.1f} cents · C♯ is {cents(pc) - cents(pd):.1f} cents above D♭ (their ratio 3¹²/2¹⁹, the Pythagorean comma)") + "<br>"
             + T(f"순정률(한 가지 예): C♯ = 라(5/3) 위 장3도 = 5/3 × 5/4 ÷ 2 = {frac(jc)} → {cents(jc):.1f}센트 · D♭ = 파(4/3) 아래 장3도 = 4/3 ÷ 5/4 = {frac(jd)} → {cents(jd):.1f}센트 · 이번에는 C♯이 D♭보다 {cents(jd) - cents(jc):.1f}센트 낮다(두 음의 비 D♭ ÷ C♯ = 16/15 ÷ 25/24 = 128/125)",
                 f"Just (one example): C♯ = a major third above A (5/3) = 5/3 × 5/4 ÷ 2 = {frac(jc)} → {cents(jc):.1f} cents · D♭ = a major third below F (4/3) = 4/3 ÷ 5/4 = {frac(jd)} → {cents(jd):.1f} cents · here C♯ is {cents(jd) - cents(jc):.1f} cents below D♭ (their ratio D♭ ÷ C♯ = 16/15 ÷ 25/24 = 128/125)") + "<br>"
             + T("12평균율: C♯ = D♭ = 2^(1/12) → 100센트", "Equal temperament: C♯ = D♭ = 2^(1/12) → 100 cents") + "</p>")
    b.append("<p>" + T(f"순정률의 C♯·D♭은 어느 음에서 어떤 음정으로 만드느냐에 따라 값이 달라서 하나로 정해지지 않는다. 위는 그 가운데 한 예다. 삼분손익의 열두 율에는 한 자리에 값이 하나뿐이다. 황종을 C로 놓으면 대려가 그 자리에 오고, 대려는 5도 7개 위에서 왔으므로 C♯ 쪽 값({cents(pc):.1f}센트)을 갖는다. 열두 율의 목록은 중려에서 끝나므로 D♭ 쪽 값은 나오지 않는다.",
                       f"In just intonation C♯ and D♭ depend on the note and the interval they are built from, so neither has a single value; the line above is one example. The twelve pipes of sanfen sunyi have one value per place. With huangzhong on C, dalü takes that place, and since it comes seven fifths up it has the C♯ value ({cents(pc):.1f} cents). The list of twelve ends at zhonglü, so the D♭ value never appears.") + "</p>")
    eb = []
    for key, lab, (c1, c2) in (("pyth", T("피타고라스", "Pythagorean"), (cents(pc), cents(pd))), ("just", T("순정률", "just"), (cents(jc), cents(jd))), ("et", T("평균율", "equal"), (100.0, 100.0))):
        eb.append(btn(T(f"{lab}: C♯ → D♭", f"{lab}: C♯ → D♭"), [[c1], [c2]], dur=0.9) + btn(T(f"{lab}: 함께", f"{lab}: together"), [[c1, c2]], dur=2.6))
    b.append("<div class='btns'>" + "".join(eb) + "</div>")
    b.append("<p class='src'>" + T("두 음을 함께 울리면 피타고라스에서는 약 23센트, 순정률 예에서는 약 41센트 떨어진 두 음이 빠르게 맥놀이 치고, 평균율에서는 같은 음이라 맥놀이가 없다.",
                                   "Together, the Pythagorean pair (about 23 cents apart) and the just pair (about 41 cents apart) beat quickly; the equal-tempered pair is one note and does not beat.") + "</p>")
    b.append("</div>" + JS)
    out = "".join(b)
    # one formula per line: the separators " · " inside formula paragraphs become line breaks
    import re
    return re.sub(r"<p class='formula'>(.*?)</p>", lambda m: "<p class='formula'>" + m.group(1).replace(" · ", "<br>") + "</p>", out, flags=re.S)
