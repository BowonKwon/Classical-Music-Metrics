"""Scales and tuning page (1.6): scales.html in each language — theory and measurement, drawn on a 0-1200 cent
ruler and playable in the browser (Web Audio; tones are synthesised, no recordings).

  python src/scales_pages.py   ->  data/derived/scales.csv (one row per scale)

Only values that are exact arithmetic from a definition, or that were read in the cited source (directly or
through the DaMuSc compilation, CC BY 4.0), are included. Scales whose numbers rest on memory or secondary
web pages (Arabic 24-tone, Indian sruti, Japanese modes, Chopi timbila) are left for a later edition.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/derived"
SCALE_FILES = ["scales.csv"]


def c(r: float) -> float:
    return round(1200 * math.log2(r), 1)


def chain(n_up: int) -> list[float]:
    """Pitch classes of a chain of pure fifths (3/2) from the tonic, folded into one octave (sanfen sunyi)."""
    out = []
    for k in range(n_up):
        v = (1200 * math.log2(1.5) * k) % 1200
        out.append(round(v, 1))
    return sorted(out)


QC = 1200 * math.log2(5) / 4  # quarter-comma meantone fifth, 696.58 cents


def meantone12():
    # fifths from Eb (-3) to G# (+8) around C
    return sorted(round((QC * k) % 1200, 1) for k in range(-3, 9))


SCALES = [
    # group, id, ko name, en name, ko when/where, en when/where, kind, cents, sd, n, source
    ("west", "pyth", "피타고라스 음률 (장음계 배열)", "Pythagorean tuning (major order)", "고대 그리스~중세 유럽", "Ancient Greece to medieval Europe", "theory",
     [c(r) for r in (1, 9/8, 81/64, 4/3, 3/2, 27/16, 243/128)], None, None, "Pure fifths 3/2 folded into the octave (definition); cf. Scala archive pyth_12.scl"),
    ("west", "arch_enh", "아르키타스 이명 음계 (E선법)", "Archytas, enharmonic genus (E mode)", "기원전 4세기 무렵, 프톨레마이오스가 전함", "c. 4th century BCE, reported by Ptolemy", "theory",
     [0.0, c(28/27), c(28/27 * 36/35), c(4/3), c(3/2), c(3/2 * 28/27), c(3/2 * 28/27 * 36/35)], None, None, "Tetrachord 28/27, 36/35, 5/4 (Ptolemy, Harmonics, book I); cf. Scala arch_enh.scl"),
    ("west", "arch_chr", "아르키타스 반음계 음계 (E선법)", "Archytas, chromatic genus (E mode)", "기원전 4세기 무렵, 프톨레마이오스가 전함", "c. 4th century BCE, reported by Ptolemy", "theory",
     [0.0, c(28/27), c(28/27 * 243/224), c(4/3), c(3/2), c(3/2 * 28/27), c(3/2 * 28/27 * 243/224)], None, None, "Tetrachord 28/27, 243/224, 32/27 (Ptolemy, Harmonics, book I); cf. Scala arch_chrom.scl"),
    ("west", "arch_dia", "아르키타스 온음계 음계 (E선법)", "Archytas, diatonic genus (E mode)", "기원전 4세기 무렵, 프톨레마이오스가 전함", "c. 4th century BCE, reported by Ptolemy", "theory",
     [0.0, c(28/27), c(28/27 * 8/7), c(4/3), c(3/2), c(3/2 * 28/27), c(3/2 * 28/27 * 8/7)], None, None, "Tetrachord 28/27, 8/7, 9/8 (Ptolemy, Harmonics, book I)"),
    ("west", "just", "순정률 장음계", "Just-intonation major scale", "프톨레마이오스의 신토논 온음계를 차를리노(1558)가 장음계로 배열", "Ptolemy's syntonic diatonic, arranged as a major scale by Zarlino (1558)", "theory",
     [c(r) for r in (1, 9/8, 5/4, 4/3, 3/2, 5/3, 15/8)], None, None, "Ratios 9/8, 5/4, 4/3, 3/2, 5/3, 15/8 (definition); cf. Scala ptolemy.scl"),
    ("west", "mean", "4분의 1 쉼표 중전음률 (12음)", "Quarter-comma meantone (12 notes)", "16~17세기 유럽(아론 1523)", "16th–17th-century Europe (Aron 1523)", "theory",
     meantone12(), None, None, "Fifths narrowed by 1/4 syntonic comma, major thirds pure 5/4 (definition); cf. Scala meanquar.scl"),
    ("west", "werck", "베르크마이스터 III (12음)", "Werckmeister III (12 notes)", "1691년 『음률』", "Musicalische Temperatur, 1691", "theory",
     [0.0, 90.2, 192.2, 294.1, 390.2, 498.0, 588.3, 696.1, 792.2, 888.3, 996.1, 1092.2], None, None, "C–G, G–D, D–A, B–F♯ narrowed by 1/4 Pythagorean comma, other fifths pure; cf. Scala werck3.scl"),
    ("west", "vallotti", "발로티 (12음)", "Vallotti (12 notes)", "18세기 중반. 조율을 다룬 제2권은 1950년 출판(1779년에는 제1권만)", "Mid-18th century; the book on tuning (book 2) was printed only in 1950, book 1 in 1779", "theory",
     [0.0, 94.1, 196.1, 298.0, 392.2, 502.0, 592.2, 698.0, 796.1, 894.1, 1000.0, 1090.2], None, None, "F–C–G–D–A–E–B narrowed by 1/6 Pythagorean comma, other fifths pure; cf. Scala vallotti.scl"),
    ("west", "et12", "12평균율", "12-tone equal temperament", "오늘날 피아노의 표준", "The standard of the modern piano", "theory",
     [100.0 * k for k in range(12)], None, None, "Step 2^(1/12) = 100 cents (definition)"),
    # East Asia
    ("east", "lu12", "삼분손익 12율", "Twelve lü by sanfen sunyi (三分損益)", "고대 중국·조선 아악", "Ancient China; Korean court music (aak)", "theory",
     chain(12), None, None, "Chain of pure fifths from 黃鍾; ratio table confirmed by Yoo et al. 2011 (J. Acoust. Soc. Korea 30(8), Table 4: jungnyeo 1.35)"),
    ("east", "wuyin", "오음 궁상각치우", "Five tones gong–shang–jue–zhi–yu (宮商角徵羽)", "고대 중국", "Ancient China", "theory",
     chain(5), None, None, "First five notes of the fifths chain (definition)"),
    ("east", "pyeongjo", "평조 (황 태 중 림 남, 삼분손익값)", "Pyeongjo (黃 太 仲 林 南, sanfen sunyi values)", "한국 궁중음악", "Korean court music", "theory",
     [0.0, 203.9, 521.5, 702.0, 905.9], None, None, "Note set of pyeongjo on hwangjong; 仲呂 at 521.5 cents by strict sanfen sunyi (eleven fifths above 黃鍾)"),
    ("east", "gyemyeon", "계면조 (황 협 중 림 무, 삼분손익값)", "Gyemyeonjo (黃 夾 仲 林 無, sanfen sunyi values)", "한국 궁중음악, 옛 5음 계면조(뒤에 3~4음으로 줄어든 형태 이전)", "Korean court music, the older five-note gyemyeonjo (before it narrowed to three or four notes)", "theory",
     [0.0, 317.6, 521.5, 702.0, 1019.6], None, None, "Note set of gyemyeonjo on hwangjong; strict sanfen sunyi values"),
    # measured
    ("measured", "slendro", "자와 가믈란 슬렌드로 (28개 평균)", "Javanese gamelan sléndro (mean of 28)", "자와(인도네시아) 족자카르타·수라카르타", "Yogyakarta and Surakarta, Java", "measured",
     [0, 233, 474, 719, 961, 1214], [0, 10, 17, 13, 12, 12], 28, "Surjodiningrat, Sudarjana & Susanto 1972 (via DaMuSc, McBride et al. 2023, CC BY 4.0)"),
    ("measured", "pelog", "자와 가믈란 펠로그 (23개 평균)", "Javanese gamelan pélog (mean of 23)", "자와(인도네시아) 족자카르타·수라카르타", "Yogyakarta and Surakarta, Java", "measured",
     [0, 119, 256, 547, 672, 782, 947, 1215], [0, 19, 22, 22, 18, 23, 25, 13], 23, "Surjodiningrat, Sudarjana & Susanto 1972 (via DaMuSc, McBride et al. 2023, CC BY 4.0)"),
    ("measured", "thai_et", "타이 7평균율 (이론)", "Thai 7-tone equal division (theory)", "엘리스(1885) 이래의 통설", "The received view since Ellis (1885)", "theory",
     [round(1200 * k / 7, 1) for k in range(7)], None, None, "Seven equal steps of 171.4 cents (Ellis 1885, quoted in Garzoli 2015)"),
    ("measured", "thai_ranat", "타이 라나트 엑 (실측, 여러 대의 평균)", "Thai ranat ek (measured, mean of several instruments)", "모턴의 측정(1961~62), 가르촐리 2015 재수록", "Morton's measurement (1961–62), reprinted by Garzoli 2015", "measured",
     [0.0, 184.7, 351.6, 525.1, 682.7, 869.4, 1034.7, 1217.1], None, None, "Morton 1976, Table E (604–1220 Hz, bars 14–21): mean frequency over the ranat ek measured, in Garzoli 2015, AAWM 4(2), Table A and note 30"),
    ("measured", "shur_vaziri", "페르시아 슈르: 바지리의 24음 표기", "Persian Shur: Vaziri's 24-quarter-tone notation", "20세기 전반 바지리의 이론(셰피이 2021은 1934년 『음악 이론』을 인용)", "Vaziri's theory, first half of the 20th century (Shafiei 2021 cites his Music Theory, 1934)", "theory",
     [0, 200, 350, 500, 700, 850, 1000], None, None, "Shafiei 2021, arXiv:2108.01283, Table 2"),
    ("measured", "shur_karimi", "페르시아 슈르: 카리미의 노래 (실측)", "Persian Shur: Karimi's singing (measured)", "마흐무드 카리미의 성악 라디프", "Mahmud Karimi's vocal radif", "measured",
     [0, 210, 347, 498, 696, 836, 985, 1190], None, 1, "Shafiei 2021, arXiv:2108.01283, Table 2 (pitch histogram, 15 gushe)"),
    ("measured", "rast_aeu", "터키 라스트: 아렐-에즈기-우즈딜렉 이론", "Turkish Rast: Arel–Ezgi–Uzdilek theory", "20세기 터키 이론", "20th-century Turkish theory", "theory",
     [0, 204.0, 384.5, 498.1, 701.9, 905.9, 1086.3], None, None, "Bozkurt et al. 2009, J. New Music Research 38(1), Table 1 (row YAEU)"),
    ("measured", "rast_meas", "터키 라스트: 명인 녹음 16개 (실측)", "Turkish Rast: 16 master recordings (measured)", "탄부리 제밀 베이 등", "Tanburi Cemil Bey and others", "measured",
     [0, 207.6, 376.8, 495.8, 702.3, 914.9, 1087.0], None, 16, "Bozkurt et al. 2009, Table 1 (AutoPeak-ave). The table's extra peak at 994.2 cents is left out to show seven degrees; the 1,200-cent point is added for playback, not measured"),
    ("measured", "ganda", "우간다 간다 하프 (실측 1대)", "Ganda harp, Uganda (one instrument, measured)", "와크스만 1950", "Wachsmann 1950", "measured",
     [0, 239, 475, 713, 948, 1192], None, 1, "Wachsmann 1950, Nature 165: 40–41 (via DaMuSc M0187, CC BY 4.0)"),
    ("measured", "malinke", "기니 말링케 실로폰 (실측 1대)", "Malinke xylophone, Guinea (one instrument, measured)", "루제·슈바르츠 1969", "Rouget & Schwarz 1969", "measured",
     [0, 174, 356, 533, 692, 866, 1034, 1203], None, 1, "Rouget & Schwarz 1969 (via DaMuSc M0131, first octave; CC BY 4.0)"),
]
COLS = ["group", "id", "name_ko", "name_en", "when_ko", "when_en", "kind", "cents", "sd", "n", "source"]
HZ = [  # Yoo et al. 2011, J. Acoust. Soc. Korea 30(8): 421–427 — 황종 estimated from dated stone-chime groups
    ("계축년(1433) 경석 22매", "Stones dated 1433 (22)", "266.9"),
    ("정유년·갑자년 경석", "Stones dated in the jeongyu and gapja years", "262.4–262.5"),
    ("20세기 경석(갑진년, 소화 12·13년)", "20th-century stones (1904, 1937, 1938)", "258.7–259.3"),
]


def frame() -> pd.DataFrame:
    df = pd.DataFrame(SCALES, columns=COLS)
    df["cents"] = df["cents"].map(lambda v: ";".join(f"{x:g}" for x in v))
    df["sd"] = df["sd"].map(lambda v: "" if v is None else ";".join(f"{x:g}" for x in v))
    return df


def esc(s):
    return html.escape("" if s is None else str(s))


CSS = """.scale{border-top:1px solid var(--line);padding:.6rem 0 .3rem}.scale h3{margin:0;font-size:.95rem}.scale .meta{color:var(--fg3);font-size:.82rem;margin:.1rem 0 .2rem}
.scale .btns{display:flex;gap:.4rem;flex-wrap:wrap;margin:.2rem 0}.scale button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:.15rem .7rem;font-size:.82rem;cursor:pointer}
.scale button:hover{border-color:var(--fg3)}.scale .kind{font-size:.72rem;border-radius:4px;padding:0 .35rem;margin-left:.35rem;vertical-align:1px}
.kind.theory{background:color-mix(in srgb,var(--g1) 22%,transparent)}.kind.measured{background:color-mix(in srgb,var(--g2) 26%,transparent)}"""

JS = """<script>(function(){var ac=null;function ctx(){if(!ac){ac=new (window.AudioContext||window.webkitAudioContext)()}return ac}
function tone(f,t,d){var a=ctx(),o=a.createOscillator(),g=a.createGain();o.type='triangle';o.frequency.value=f;g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(.22,t+.02);g.gain.exponentialRampToValueAtTime(.001,t+d);o.connect(g);g.connect(a.destination);o.start(t);o.stop(t+d+.05)}
var BASE=261.63;function play(c,mode){var a=ctx(),t=a.currentTime+.05,seq=c.slice();if(mode==='updown'){seq=seq.concat(seq.slice(0,-1).reverse())}
if(mode==='compare'){c.forEach(function(x){tone(BASE*Math.pow(2,x/1200),t,.55);tone(BASE*Math.pow(2,Math.round(x/100)*100/1200),t+.6,.55);t+=1.3});return}
seq.forEach(function(x){tone(BASE*Math.pow(2,x/1200),t,.5);t+=.42})}
document.querySelectorAll('.scale button[data-c]').forEach(function(b){b.addEventListener('click',function(){var c=JSON.parse(b.getAttribute('data-c'));play(c,b.getAttribute('data-m'))})})})();</script>"""


def ruler(cents, sd, width=900, height=58, lo=0, hi=1260):
    L, R = 10, 10
    pw = width - L - R
    X = lambda v: L + (v - lo) / (hi - lo) * pw  # noqa: E731
    o = [f'<svg viewBox="0 0 {width} {height}" role="img">']
    for k in range(0, 13):
        x = X(k * 100)
        o.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="14" y2="34" stroke="var(--fg3)" stroke-opacity=".45" stroke-width="{1.4 if k % 12 == 0 else .8}"/>')
        if k % 2 == 0:
            o.append(f'<text x="{x:.1f}" y="{height - 4}" text-anchor="middle">{k * 100}</text>')
    o.append(f'<line x1="{X(0):.1f}" x2="{X(1200):.1f}" y1="24" y2="24" stroke="var(--fg3)" stroke-opacity=".5"/>')
    for i, v in enumerate(cents):
        if sd and sd[i]:
            o.append(f'<line x1="{X(v - sd[i]):.1f}" x2="{X(v + sd[i]):.1f}" y1="24" y2="24" stroke="var(--g2)" stroke-width="7" stroke-opacity=".45" stroke-linecap="round"/>')
        o.append(f'<circle cx="{X(v):.1f}" cy="24" r="5.5" fill="var(--g1)" stroke="var(--card)" stroke-width="1.5"><title>{v:g} cents{f" ± {sd[i]:g}" if sd and sd[i] else ""}</title></circle>')
    o.append("</svg>")
    return "".join(o)


GROUPS = {"west": ("1. 서양 조율의 역사 — 비율로 정의된 이론값", "1. Western tuning — values defined by ratios"),
          "east": ("2. 동아시아 — 삼분손익", "2. East Asia — sanfen sunyi (三分損益)"),
          "measured": ("3. 이론과 실측", "3. Theory and measurement")}


def render(lang: str) -> str:
    k = lang == "ko"
    df = pd.DataFrame(SCALES, columns=COLS)
    from history_pages import GCSS  # noqa: E402
    b = [f"<style>{GCSS}{CSS}</style><div class='hero'><h1>{'음계와 조율' if k else 'Scales and tuning'}</h1><p class='lead'>"
         + ("한 옥타브(1200센트)를 어떻게 나누어 왔는지, 시대와 지역에 따라 견준다. 점 하나가 음 하나이고, 회색 눈금은 피아노의 12평균율(100센트 간격)이다. 단추를 누르면 브라우저가 그 자리에서 음을 합성해 들려준다."
            if k else "How the octave (1,200 cents) has been divided, compared across periods and regions. Each dot is a note; the grey ticks are piano equal temperament (100 cents apart). The buttons play the scale, synthesised by your browser on the spot.")
         + "</p></div>"]
    b.append("<p class='src'>" + ("모든 음계를 같은 기준음(가온 다, 261.63 Hz) 위에 옮겨 들려준다. 실제 악기의 음높이는 다르다. 「평균율과 번갈아」는 각 음 다음에 가장 가까운 12평균율 음을 들려준다. 소리는 삼각파 합성음이라 악기 음색이 아니다. 「이론」은 비율이나 규칙으로 정한 값, 「실측」은 악기나 연주를 잰 값이다."
                                 if k else "Every scale is played on the same reference, middle C (261.63 Hz); the instruments themselves sit at other pitches. 'Against equal temperament' follows each note with the nearest equal-tempered note. The sound is a synthesised triangle wave, not the instrument's timbre. 'Theory' marks values set by ratios or rules; 'measured' marks values taken from instruments or performances.") + "</p>")
    for g, (tko, ten) in GROUPS.items():
        b.append(f"<h2>{tko if k else ten}</h2>")
        if g == "east":
            b.append("<p>" + ("삼분손익은 율관 길이를 3분의 1씩 줄이고 늘려 음을 얻는 방법으로, 순정 5도를 쌓는 것과 같다. 12번째 음인 중려는 4/3(498센트)이 아니라 521.5센트에 놓인다. 5도 12개를 쌓으면 옥타브보다 피타고라스 쉼표(23.5센트)만큼 넘치기 때문이다. 한국 아악의 12율도 같은 계열이다. 유준희 외(2011)가 정리한 비율표에서 중려는 1.35다. 평조·계면조의 음 구성은 관례를 따랐고, 실제 연주에서 중려가 521센트 부근에 놓였는지는 이 값만으로는 알 수 없다."
                              if k else "Sanfen sunyi (三分損益) shortens and lengthens a pipe by a third in turn, which amounts to stacking pure fifths. The twelfth note, 仲呂, lands at 521.5 cents rather than 4/3 (498 cents), because twelve fifths overshoot the octave by the Pythagorean comma (23.5 cents). The twelve yul of Korean court music follow the same series; in the ratio table of Yoo et al. (2011), jungnyeo (仲呂) is 1.35. The note sets of pyeongjo and gyemyeonjo follow convention, and whether performers actually placed jungnyeo near 521 cents cannot be told from these values.") + "</p>")
        if g == "measured":
            b.append("<p>" + ("이론이 정한 음과 실제로 조율하거나 연주한 음은 다르다. 같은 곡조의 이론값과 실측값을 나란히 놓았다. 가믈란은 악기 세트 수십 개의 평균이고, 주황 막대는 ±1 표준편차(수록 세트 전체의 모집단 표준편차)다. 여기 실은 가믈란 평균과 라나트 엑 평균에서는 옥타브가 1200센트보다 넓다(1214~1217센트). 원자료에 옥타브 음이 없는 음계는 재생을 위해 1200센트를 붙였다."
                              if k else "The notes a theory prescribes and the notes actually tuned or sung differ. Theory and measurement for the same scale sit side by side. The gamelan rows average dozens of sets; the orange bars show ±1 standard deviation (population SD over the sets included). In the gamelan and ranat ek means shown here the octave is wider than 1,200 cents (1,214–1,217). Where the source gives no octave note, 1,200 cents is added for playback.") + "</p>")
        for r in df[df.group == g].itertuples():
            cents = list(r.cents) + ([] if r.cents[-1] > 1150 else [1200.0])
            sd = list(r.sd) + ([0] * (len(cents) - len(r.sd))) if r.sd else None
            kind = ("이론" if r.kind == "theory" else "실측") if k else r.kind
            n = f" · n = {int(r.n)}" if r.n and r.n > 1 else ""
            data = esc(json.dumps(cents))
            b.append(f"<div class='scale'><h3>{esc(r.name_ko if k else r.name_en)}<span class='kind {r.kind}'>{kind}</span></h3>"
                     f"<div class='meta'>{esc(r.when_ko if k else r.when_en)}{n} · {esc(r.source)}</div>{ruler(cents, sd)}"
                     f"<div class='btns'><button type='button' data-c='{data}' data-m='up'>▶ {'올라가기' if k else 'Up'}</button>"
                     f"<button type='button' data-c='{data}' data-m='updown'>▶ {'올라갔다 내려오기' if k else 'Up and down'}</button>"
                     f"<button type='button' data-c='{data}' data-m='compare'>▶ {'평균율과 번갈아' if k else 'Against equal temperament'}</button></div></div>")
        if g == "east":
            rows = "".join(f"<tr><td>{esc(a if k else e)}</td><td class='num'>{hz}</td></tr>" for a, e, hz in HZ)
            b.append(f"<h3 style='margin-top:1rem'>{'황종의 높이는 시대마다 달랐다' if k else 'The pitch of hwangjong changed over time'}</h3><p>"
                     + ("음계는 비율이고, 실제 음높이는 기준음 황종이 정한다. 국립고궁박물관·국립국악원 등에 남은 편경·특경의 경석 241매를 잰 연구는, 경석에 새긴 간지나 개수(改修) 시기가 같은 것끼리 묶어 황종의 높이를 거꾸로 추정했다. 간지는 60년마다 돌아오므로 정유년·갑자년은 제작 연도가 하나로 정해지지 않는다."
                        if k else "A scale is a set of ratios; the actual pitch is fixed by the reference note hwangjong (黃鍾). A study of 241 surviving stone-chime slabs (pyeongyeong and teukgyeong) in Korean collections grouped the stones by the cyclical year or the re-tuning date inscribed on them and estimated hwangjong from each group. A cyclical year recurs every 60 years, so the jeongyu and gapja groups do not fix a single year of manufacture.")
                     + f"</p><div class='wrap'><table><thead><tr><th>{'경석 묶음' if k else 'Stone group'}</th><th class='num'>{'황종 추정(Hz)' if k else 'hwangjong estimate (Hz)'}</th></tr></thead><tbody>{rows}</tbody></table></div>"
                     "<p class='src'>유준희·박정우·배대성 외, 「유물 편경의 음향 분석을 통한 아악 황종음고의 추정」, 『한국음향학회지』 30(8): 421–427, 2011.</p>")
    b.append("<h2>" + ("4. 아직 넣지 않은 것" if k else "4. Not yet included") + "</h2><p>" + (
        "아랍 마캄의 24음 이론(1932 카이로 회의)과 실측, 인도의 22 슈루티, 일본의 요·인 음계, 모잠비크 초피 팀빌라, 한국 국악기 실측은 출처의 원문을 아직 확인하지 못해 넣지 않았다. 확인되는 대로 더한다."
        if k else "Arabic maqam (the 24-tone theory of the 1932 Cairo Congress and its measurement), the Indian 22 śruti, the Japanese yō and in scales, the Chopi timbila of Mozambique and measurements of Korean instruments are left out until their sources have been checked in the original.") + "</p>")
    b.append("<p class='src'>" + ("자료: " if k else "Data: ") + "McBride, Passmore & Tlusty (2023), 'Convergent evolution in a large cross-cultural database of musical scales', <i>PLoS ONE</i> 18(12): e0284851 — <a href='https://github.com/jomimc/DaMuSc'>DaMuSc</a> (CC BY 4.0); "
             "Garzoli (2015), 'The myth of equidistance in Thai tuning', <i>Analytical Approaches to World Music</i> 4(2); Bozkurt et al. (2009), <i>Journal of New Music Research</i> 38(1): 45–70; Shafiei (2021), arXiv:2108.01283; "
             + ("유준희 외(2011). 비율로 정의된 음률은 정의에서 계산했고 Scala 아카이브(Huygens-Fokker 재단)의 파일과 대조했다." if k else "Yoo et al. (2011). Ratio-defined tunings were computed from their definitions and checked against the Scala archive (Huygens-Fokker Foundation).")
             + "</p>" + JS)
    return "".join(b)


def build(lang, path, page_fn):
    path.write_text(page_fn(lang, "음계와 조율" if lang == "ko" else "Scales and tuning", render(lang),
                            desc="Scales and tuning compared across periods and regions", active="scales"), encoding="utf-8")


if __name__ == "__main__":
    frame().to_csv(D / "scales.csv", index=False, encoding="utf-8", lineterminator="\n")
    print("wrote data/derived/scales.csv")
