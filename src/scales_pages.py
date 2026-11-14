"""Scales and tuning page (1.6; second edition 1.7): scales.html in each language — theory and measurement,
drawn on a 0-1200 cent ruler and playable in the browser (Web Audio; tones are synthesised, no recordings).

  python src/cairo1932_peaks.py   ->  data/derived/scales_cairo1932.csv (needs the ORD-CC32 zip in data/raw/ordcc32/)
  python src/scales_pages.py      ->  data/derived/scales.csv (one row per scale)

Only values that are exact arithmetic from a definition, or that were read in the cited source (directly or,
for the 1.6 rows marked so, through the DaMuSc compilation, CC BY 4.0), are included. From 1.7 every new row was
read in its primary source; sources that could not be opened are listed in section 4 of the page instead.
Rows computed from ORD-CC32 (CC BY-NC 4.0) carry license CC-BY-NC-4.0 in the per-row license column.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/derived"
SCALE_FILES = ["scales.csv", "scales_cairo1932.csv", "scales_places.csv"]


def cairo(maqam: str, region: str) -> tuple[list[float], int]:
    """Peaks (cents, rounded) and recording count for one maqam x region, from cairo1932_peaks.py."""
    t = pd.read_csv(D / "scales_cairo1932.csv")
    t = t[(t.maqam == maqam) & (t.region == region)]
    return [float(round(v)) for v in t.peak_cents], int(t.n_recordings.iloc[0])


SRUTI = [0, 3, 5, 9, 13, 16, 18]  # sa-grama: sa 4, ri 3, ga 2, ma 4, pa 4, dha 3, ni 2 srutis (Natyasastra 28.24-26)


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


RAST_EG, BAYATI_EG = cairo("rast", "Egypt"), cairo("bayati", "Egypt")

# 1.14 — Clements 1913, pp. 7-8: vibration numbers with sa = 240 for the srutis numbered 1-22 (Deval's measurements).
# 0 Kshobhini (213 1/3) is 22 an octave down; 1-3 (216, 225, 227 5/9) lie below sa and are doubled here.
# The two unnumbered septimal notes (ma atikomal 315, ni atikomal 420) are listed in the text, not drawn.
CLEMENTS_VIB = {4: 240, 5: 252, 6: 256, 7: 800 / 3, 8: 270, 9: 2560 / 9, 10: 288, 11: 300, 12: 1215 / 4, 13: 320, 14: 324,
                15: 675 / 2, 16: 1024 / 3, 17: 360, 18: 378, 19: 384, 20: 400, 21: 405, 22: 1280 / 3,
                1: 2 * 216, 2: 2 * 225, 3: 2 * 2048 / 9}
CLEMENTS_CENTS = sorted(round(1200 * math.log2(v / 240), 1) for v in CLEMENTS_VIB.values())

# 1.14 — Bel 1988 (HAL hal-00008280), p. 15: rag Todi, tonal positions in cents above sa.
# The mode is do reb mib fa# sol lab si (sa = do). lab = lower octave; (lab) = middle octave.
# Mansur's 1095 is printed in the (lab) column and '?' in the si column; read as si (Bel's own mean, 1107, includes it).
TODI_COLS = ["reb", "mib", "fa#", "sol", "lab", "(lab)", "si"]
TODI = [  # performer, instrument ko, instrument en, kind, values (None = not given)
    ("Mallikarjun Mansur", "노래", "voice", "perf", [88, 293, 625, 701, 794, None, 1095]),
    ("Z. M. Dagar", "루드라 비나", "rudra vīṇā", "perf", [93, 293, 600, 702, 785, None, 1108]),
    ("Faiyaz Khan", "노래", "voice", "perf", [90, 294, 606, 702, None, 810, 1104]),
    ("Bismillah Khan", "셰나이", "shahnāī", "perf", [99, 303, 617, 705, None, 805, 1116]),
    ("Kishori Amonkar", "노래", "voice", "perf", [96, 288, 594, 702, 792, 810, 1110]),
    ("Asad Ali Khan (1)", "루드라 비나", "rudra vīṇā", "perf", [99, 290, 593, 702, 795, 802, 1105]),
    ("Asad Ali Khan (2)", "슈루티 하모니움 조율", "śruti harmonium tuning", "tuning", [100, 294, 606, 702, 794, None, 1108]),
    ("Bor-Van der Meer", "슈루티 하모니움 조율", "śruti harmonium tuning", "tuning", [96, 294, 606, 702, 792, 804, 1110]),
]
TODI_PRINTED = [  # cells exactly as printed on p. 15, '' = blank
    ["88", "293", "625", "701", "794", "1095", "?"],
    ["93", "293", "600", "702", "785", "", "1108"],
    ["90", "294", "606", "702", "?", "(810)", "1104"],
    ["99", "303", "617", "705", "?", "(805)", "1116"],
    ["96", "288", "594", "702", "792", "(810)", "1110"],
    ["99", "290", "593", "702", "795", "(802)", "1105"],
    ["100", "294", "606", "702", "794", "", "1108"],
    ["96", "294", "606", "702", "792", "(804)", "1110"],
]


def todi_stats():
    """Mean and population SD over the six performances (harmonium tunings excluded), lower-octave lab."""
    out = []
    for j, col in enumerate(TODI_COLS):
        if col == "(lab)":
            continue
        xs = [r[4][j] for r in TODI if r[3] == "perf" and r[4][j] is not None]
        m = sum(xs) / len(xs)
        sd = (sum((x - m) ** 2 for x in xs) / len(xs)) ** .5
        out.append((col, round(m, 1), round(sd, 1), len(xs)))
    return out


TODI_STATS = todi_stats()

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
    ("east", "gy_lee1928", "가야금 경기민요 — 이일선 「이팔청춘가」 (1928 음반, 실측)", "Gayageum, Gyeonggi folk song: Lee Ilseon, 'Ipal cheongchunga' (1928 record, measured)", "고음반 측정, 고유동 2021", "Measured from an early record by Ko Yudong (2021)", "measured",
     [0, 149.0, 431.8, 687.1, 846.9, 1141.2], None, 1, "Ko Yudong 2021, MA thesis, Hanyang Univ., p. 183, Table 102: mean deviation from equal temperament per string, string 6 (Do) = 0; strings 6–11 Do Re Mi Sol La Do. String 8 is the open-string value (+31.75)"),
    ("east", "gy_kim1931", "가야금 경기민요 — 김죽파 「아리랑 잡곡」 (1931 음반, 실측)", "Gayageum, Gyeonggi folk song: Kim Jukpa, 'Arirang japgok' (1931 record, measured)", "고음반 측정, 고유동 2021", "Measured from an early record by Ko Yudong (2021)", "measured",
     [0, 131.3, 409.3, 708.3, 840.2, 1201.3], None, 1, "Ko Yudong 2021, MA thesis, Hanyang Univ., p. 183, Table 102: mean deviation from equal temperament per string, string 6 (Do) = 0; strings 6–11 Do Re Mi Sol La Do"),
    ("east", "gy_kim1932", "가야금 경기민요 — 김죽파 「아리랑」 (1932 음반, 실측)", "Gayageum, Gyeonggi folk song: Kim Jukpa, 'Arirang' (1932 record, measured)", "고음반 측정, 고유동 2021", "Measured from an early record by Ko Yudong (2021)", "measured",
     [0, 140.9, 435.8, 726.3, 870.0], None, 1, "Ko Yudong 2021, MA thesis, Hanyang Univ., p. 183, Table 102: mean deviation from equal temperament per string, string 6 (Do) = 0; strings 6–11 Do Re Mi Sol La Do. String 11 not measured"),
    ("east", "gy_seong1960", "가야금 경기민요 — 성금연 「아리랑」 (1960 음반, 실측)", "Gayageum, Gyeonggi folk song: Seong Geumyeon, 'Arirang' (1960 record, measured)", "고음반 측정, 고유동 2021", "Measured from an early record by Ko Yudong (2021)", "measured",
     [0, 134.8, 355.4, 648.2, 857.4], None, 1, "Ko Yudong 2021, MA thesis, Hanyang Univ., p. 183, Table 102: mean deviation from equal temperament per string, string 6 (Do) = 0; strings 6–11 Do Re Mi Sol La Do. String 11 not measured; the author notes fewer measurable notes in this record"),
    ("east", "sj_kimbh", "가야금산조 계면조의 청과 꺾는 음 — 김병호 (실측)", "Gayageum sanjo, gyemyeonjo: cheong and the bent notes, Kim Byeongho (measured)", "진양조 음원, 양수연 2013 측정", "Jinyangjo recording, measured by Yang Suyeon (2013)", "measured",
     [0, 111.4, 349.8, 1196.2], None, 1, "Yang Suyeon 2013, MA thesis, Seoul National Univ.: middle register, cheong c′ to the lower and upper notes of the bent figure (pp. 84, 87–88) and c′–c″ (p. 47)"),
    ("east", "sj_kimjp", "가야금산조 계면조의 청과 꺾는 음 — 김죽파 (실측)", "Gayageum sanjo, gyemyeonjo: cheong and the bent notes, Kim Jukpa (measured)", "진양조 음원, 양수연 2013 측정", "Jinyangjo recording, measured by Yang Suyeon (2013)", "measured",
     [0, 94.1, 351.4, 1206.2], None, 1, "Yang Suyeon 2013, MA thesis, Seoul National Univ.: middle register, cheong c′ to the lower and upper notes of the bent figure (pp. 84, 87–88) and c′–c″ (p. 47)"),
    ("east", "sj_seong", "가야금산조 계면조의 청과 꺾는 음 — 성금연 (실측)", "Gayageum sanjo, gyemyeonjo: cheong and the bent notes, Seong Geumyeon (measured)", "진양조 음원, 양수연 2013 측정", "Jinyangjo recording, measured by Yang Suyeon (2013)", "measured",
     [0, 67.8, 350.8, 1202.1], None, 1, "Yang Suyeon 2013, MA thesis, Seoul National Univ.: middle register, cheong c′ to the lower and upper notes of the bent figure (pp. 84, 87–88) and c′–c″ (p. 47)"),
    ("east", "sj_ham", "가야금산조 계면조의 청과 꺾는 음 — 함동정월 (실측)", "Gayageum sanjo, gyemyeonjo: cheong and the bent notes, Ham Dongjeongwol (measured)", "진양조 음원, 양수연 2013 측정", "Jinyangjo recording, measured by Yang Suyeon (2013)", "measured",
     [0, 80.4, 353.8, 1193.0], None, 1, "Yang Suyeon 2013, MA thesis, Seoul National Univ.: middle register, cheong c′ to the lower and upper notes of the bent figure (pp. 84, 87–88) and c′–c″ (p. 47). The upper note follows the table's cent value (353.8); the same table's frequencies (237.7 → 290.9 Hz) give 349.7 cents"),
    ("east", "piri_sang_pyeongjo", "피리 — 상령산(평조회상) (정재국 녹음, 실측)", "P'iri: Sangnyeongsan (in Pyeongjo hoesang), Chung Chaekook (measured)", "녹음 측정, 남운정 1998", "Measured from a recording by Unjung Nam (1998)", "measured",
     [0, 141, 458, 705, 881], None, 1, "Nam 1998, Music Perception 16(2), p. 244, Fig. 1: average intervals in cents between the scale tones of one solo p'iri recording by Chung Chaekook, about 10 samples per tone from stable (non-vibrato) portions, pitch classes from different octaves combined. Notes hwang tae jung im nam. The five printed intervals sum to 1,208 cents (141+317+247+176+327); the octave is not drawn"),
    ("east", "piri_sang_pyojung", "피리 — 상령산(표정만방지곡) (정재국 녹음, 실측)", "P'iri: Sangnyeongsan (in Pyojeong manbang jigok), Chung Chaekook (measured)", "녹음 측정, 남운정 1998", "Measured from a recording by Unjung Nam (1998)", "measured",
     [0, 114, 485, 727, 921], None, 1, "Nam 1998, Music Perception 16(2), p. 244, Fig. 1: average intervals in cents between the scale tones of one solo p'iri recording by Chung Chaekook, about 10 samples per tone from stable (non-vibrato) portions, pitch classes from different octaves combined. Notes jung im mu hwang tae. The five printed intervals sum to 1,288 cents (114+371+242+194+367); the octave is not drawn"),
    ("east", "piri_sujecheon", "피리 — 수제천 (정재국 녹음, 실측)", "P'iri: Sujecheon, Chung Chaekook (measured)", "녹음 측정, 남운정 1998", "Measured from a recording by Unjung Nam (1998)", "measured",
     [0, 204, 548, 692, 1023], None, 1, "Nam 1998, Music Perception 16(2), p. 244, Fig. 1: average intervals in cents between the scale tones of one solo p'iri recording by Chung Chaekook, about 10 samples per tone from stable (non-vibrato) portions, pitch classes from different octaves combined. Notes tae go im nam hwang. The five printed intervals sum to 1,177 cents (204+344+144+331+154); the octave is not drawn"),
    ("east", "in_uehara", "일본 음선(陰旋, 미야코부시) — 우에하라의 비율", "Japanese in scale (陰旋, miyako-bushi): Uehara's ratios", "우에하라 로쿠시로 『속악선율고』(1895)", "Uehara Rokushirō, Zokugaku senritsu kō (1895)", "theory",
     [0.0, c(16/15), c(4/3), c(3/2), c(7/4)], None, None, "Uehara 1895 (NDL pid 856052): monochord string lengths pp. 90–91; frequency ratios pp. 104–106: 1, 16/15, 4/3, 3/2, descending fifth note 8/5, ascending fifth note 12/7, 7/4 or 9/5 by school and shamisen tuning (7/4 used for playback), 2. The table on pp. 105–106 prints 15/16 and 4/8 for the second and third notes; read as 16/15 and 4/3 from its own interval column (16/15, 5/4) and the string lengths on p. 91 (15/16, 3/4). The name 陰旋, p. 79"),
    ("east", "yo_uehara", "일본 양선(陽旋, 이나카부시) — 우에하라의 비율", "Japanese yō scale (陽旋, inaka-bushi): Uehara's ratios", "우에하라 로쿠시로 『속악선율고』(1895)", "Uehara Rokushirō, Zokugaku senritsu kō (1895)", "theory",
     [0.0, c(10/9), c(4/3), c(3/2), c(9/5)], None, None, "Uehara 1895, p. 107: 1, 10/9, 4/3, 3/2, descending fifth note 5/3, ascending fifth note 9/5, 2 — 'from only a few trials, not to be called exact'; the name 陽旋, p. 79"),
    ("east", "koto_isawa", "고토 히라조시 조율 — 이사와 보고", "Koto, hira-jōshi tuning: Isawa's report", "이사와 슈지의 보고, 엘리스 1885가 인용", "Isawa Shūji's report, as quoted by Ellis (1885)", "theory",
     [0, 204, 316, 702, 814], None, None, "Ellis 1885, J. Soc. Arts 33, p. 522 (cents from string II)"),
    ("east", "koto_woman", "고토 히라조시 조율 — 여성 연주자 (실측 1대)", "Koto, hira-jōshi tuning: woman player (one instrument, measured)", "런던 나이츠브리지 일본촌, 엘리스·힙킨스 측정(엘리스 1885 보고)", "Japanese Village, Knightsbridge, London, measured by Ellis and Hipkins (reported by Ellis 1885)", "measured",
     [0, 193, 357, 719, 801, 1199], None, 1, "Ellis 1885, J. Soc. Arts 33, p. 522"),
    ("east", "koto_master", "고토 히라조시 조율 — 그 스승 (실측 1대)", "Koto, hira-jōshi tuning: her music master (one instrument, measured)", "런던 나이츠브리지 일본촌, 엘리스·힙킨스 측정(엘리스 1885 보고)", "Japanese Village, Knightsbridge, London, measured by Ellis and Hipkins (reported by Ellis 1885)", "measured",
     [0, 185, 337, 683, 790, 1200], None, 1, "Ellis 1885, J. Soc. Arts 33, p. 522"),
    # measured
    ("measured", "slendro", "자와 가믈란 슬렌드로 (28개 평균)", "Javanese gamelan sléndro (mean of 28)", "자와(인도네시아) 족자카르타·수라카르타", "Yogyakarta and Surakarta, Java", "measured",
     [0, 233, 474, 719, 961, 1214], [0, 10, 17, 13, 12, 12], 28, "Surjodiningrat, Sudarjana & Susanto 1972 (via DaMuSc, McBride et al. 2023, CC BY 4.0)"),
    ("measured", "pelog", "자와 가믈란 펠로그 (23개 평균)", "Javanese gamelan pélog (mean of 23)", "자와(인도네시아) 족자카르타·수라카르타", "Yogyakarta and Surakarta, Java", "measured",
     [0, 119, 256, 547, 672, 782, 947, 1215], [0, 19, 22, 22, 18, 23, 25, 13], 23, "Surjodiningrat, Sudarjana & Susanto 1972 (via DaMuSc, McBride et al. 2023, CC BY 4.0)"),
    ("measured", "thai_et", "타이 7평균율 (이론)", "Thai 7-tone equal division (theory)", "엘리스(1885) 이래의 통설", "The received view since Ellis (1885)", "theory",
     [round(1200 * k / 7, 1) for k in range(7)], None, None, "Seven equal steps of 171.4 cents (Ellis 1885, quoted in Garzoli 2015)"),
    ("measured", "thai_ranat", "타이 라나트 엑 (실측, 여러 대의 평균)", "Thai ranat ek (measured, mean of several instruments)", "모턴의 측정(1961~62), 가르촐리 2015 재수록", "Morton's measurement (1961–62), reprinted by Garzoli 2015", "measured",
     [0.0, 184.7, 351.6, 525.1, 682.7, 869.4, 1034.7, 1217.1], None, None, "Morton 1976, Table E (604–1220 Hz, bars 14–21): mean frequency over the ranat ek measured, in Garzoli 2015, AAWM 4(2), Table A and note 30"),
    ("measured", "chopi_avg", "모잠비크 초피 팀빌라 — 자발라 지구 다섯 악단 평균 (실측)", "Chopi timbila, Mozambique: mean of five orchestras in the Zavala District (measured)", "휴 트레이시의 소리굽쇠 측정(1948 보고, 악단별 측정일은 적혀 있지 않음)", "Measured by Hugh Tracey with tuning forks (reported 1948; dates per orchestra not given)", "measured",
     [0, 176, 345, 519, 680, 851, 1027, 1200], [0, 19.3, 14.4, 18.5, 16.2, 20.9, 18.7, 0], 5, "H. Tracey 1948, Chopi Musicians, p. 125, Diagram IV(b), column 'Average' (Zavala, Chisiko, Mavila, Banguza, Zandamela). Bars: population SD of the five printed columns, computed by the editor. The printed cents do not always match the printed frequencies: Mavila's sixth note is 424 vibrations in IV(a) but 830 cents in IV(b), which fits 420 (the average uses 830); a few other cells differ by about a cent"),
    ("measured", "chopi", "모잠비크 초피 팀빌라 (실측 1대)", "Chopi timbila, Mozambique (one instrument, measured)", "휴 트레이시의 소리굽쇠 측정", "Measured by Hugh Tracey with tuning forks", "measured",
     [0, 157, 325, 498, 655, 834, 1027, 1200], None, 1, "H. Tracey 1958, African Music 2(1), p. 19, 'Typical African scales' No. 1 (252–504 vibrations per second); the same values as the Zavala orchestra in Tracey 1948, p. 125, Diagram IV"),
    ("measured", "shur_vaziri", "페르시아 슈르: 바지리의 24음 표기", "Persian Shur: Vaziri's 24-quarter-tone notation", "20세기 전반 바지리의 이론(셰피이 2021은 1934년 『음악 이론』을 인용)", "Vaziri's theory, first half of the 20th century (Shafiei 2021 cites his Music Theory, 1934)", "theory",
     [0, 200, 350, 500, 700, 850, 1000], None, None, "Shafiei 2021, arXiv:2108.01283, Table 2"),
    ("measured", "shur_karimi", "페르시아 슈르: 카리미의 노래 (실측)", "Persian Shur: Karimi's singing (measured)", "마흐무드 카리미의 성악 라디프", "Mahmud Karimi's vocal radif", "measured",
     [0, 210, 347, 498, 696, 836, 985, 1190], None, 1, "Shafiei 2021, arXiv:2108.01283, Table 2 (pitch histogram, 15 gushe)"),
    ("measured", "rast_aeu", "터키 라스트: 아렐-에즈기-우즈딜렉 이론", "Turkish Rast: Arel–Ezgi–Uzdilek theory", "20세기 터키 이론", "20th-century Turkish theory", "theory",
     [0, 204.0, 384.5, 498.1, 701.9, 905.9, 1086.3], None, None, "Bozkurt et al. 2009, J. New Music Research 38(1), Table 1 (row YAEU)"),
    ("measured", "rast_meas", "터키 라스트: 명인 녹음 16개 (실측)", "Turkish Rast: 16 master recordings (measured)", "탄부리 제밀 베이 등", "Tanburi Cemil Bey and others", "measured",
     [0, 207.6, 376.8, 495.8, 702.3, 914.9, 1087.0], None, 16, "Bozkurt et al. 2009, Table 1 (AutoPeak-ave). The table's extra peak at 994.2 cents is left out to show seven degrees; the 1,200-cent point is added for playback, not measured"),
    ("measured", "rast_mushaqa", "아랍 라스트: 무샤카의 24 4분음 (4분음 = 50센트로 놓았을 때)", "Arabic Rast: Mushāqa's 24 quarter tones (quarter = 50 cents)", "미하일 무샤카(다마스쿠스, 19세기 중반), 엘리 스미스 영역 1847", "Mīkhāʾīl Mushāqa (Damascus, mid-19th century), tr. Eli Smith 1847", "theory",
     [0, 200, 350, 500, 700, 900, 1050], None, None, "Smith 1847, JAOS 1(3), p. 176: steps of 4, 3, 3, 4, 4, 3, 3 quarters from rast; 24 quarters to the octave. pp. 213–215: Mushāqa shortens the quarters along the string in a fixed ratio, aiming at equal intervals; a construction on the string, not an exact 50-cent grid. On p. 216 he judges, after comparing two tamburs, that the Arab division into quarters is in error and the Greek division right"),
    ("measured", "rast_cairo", "아랍 라스트: 1932 카이로 회의 녹음, 이집트 (실측)", "Arabic Rast: 1932 Cairo Congress recordings, Egypt (measured)", "카이로 아랍 음악 회의(1932) 녹음", "Recordings made at the Cairo Congress of Arab Music (1932)", "measured",
     RAST_EG[0], None, RAST_EG[1], "Computed by the editor from ORD-CC32 (Bozkurt 2025, CC BY-NC 4.0): peaks of the mean tonic-aligned histogram, 20-cent bins, the dataset's own peak method"),
    ("measured", "bayati_cairo", "아랍 바야티: 1932 카이로 회의 녹음, 이집트 (실측)", "Arabic Bayati: 1932 Cairo Congress recordings, Egypt (measured)", "카이로 아랍 음악 회의(1932) 녹음", "Recordings made at the Cairo Congress of Arab Music (1932)", "measured",
     BAYATI_EG[0], None, BAYATI_EG[1], "Computed by the editor from ORD-CC32 (Bozkurt 2025, CC BY-NC 4.0); the sixth degree forms no peak"),
    ("measured", "sruti", "인도 사드자 그라마의 22 슈루티 (슈루티를 같은 크기로 놓았을 때)", "Indian ṣaḍja-grāma on 22 śrutis (śrutis drawn as equal)", "바라타 『나티야샤스트라』", "Bharata, Nāṭyaśāstra", "theory",
     [round(1200 * k / 22, 1) for k in SRUTI], None, None, "Nāṭyaśāstra 28.24–26, tr. Ghosh 1961, vol. II, p. 8: sa 4, ri 3, ga 2, ma 4, pa 4, dha 3, ni 2 śrutis. The text gives counts, not sizes; equal śrutis are an assumption of this drawing"),
    ("measured", "sruti_clements", "근대의 22 슈루티 — 클레먼츠 1913 (데발의 측정)", "The modern 22 śrutis: Clements 1913 (after Deval's measurements)", "데발이 가수의 노래를 디아코드로 재어 정함, 클레먼츠 1913이 표로 실음", "Fixed by Deval from singers measured on a diachord; tabulated by Clements (1913)", "theory",
     CLEMENTS_CENTS, None, None, "Clements 1913, Introduction to the Study of Indian Music, pp. 7–8: vibration numbers with sa = 240 for srutis 1–22 (srutis 1–3 lie below sa and are raised an octave here). Unnumbered septimal ma atikomal (315) and ni atikomal (420) not drawn"),
    ("measured", "todi_bel", "라가 토디 — 연주 6계열 평균 (실측)", "Rāg Toḍī: mean of six performances (measured)", "벨 1988이 녹음에서 측정(가수 3, 루드라 비나 2, 셰나이 1)", "Measured from recordings by Bel (1988): three singers, two rudra vīṇā, one shahnāī", "measured",
     [0.0] + [m for _, m, _, _ in TODI_STATS], [0] + [sd for _, _, sd, _ in TODI_STATS], 6,
     "Bel 1988, 'Raga : approches conceptuelles et expérimentales', HAL hal-00008280, p. 15: tonal positions in cents above sa; mean and population SD over the six performances, editor's calculation (two śruti-harmonium tunings excluded). lab is the lower-octave value (n = 4); Mansur's 1095, printed in the middle-octave lab column, is read as si"),
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


# Scales whose descending form differs (Uehara 1895): the descending note set, low to high.
DOWN = {"in_uehara": [0.0, c(16/15), c(4/3), c(3/2), c(8/5)],
        "yo_uehara": [0.0, c(10/9), c(4/3), c(3/2), c(5/3)]}
NC = {"rast_cairo", "bayati_cairo",  # ORD-CC32, CC BY-NC 4.0
      "gy_lee1928", "gy_kim1931", "gy_kim1932", "gy_seong1960",  # Ko 2021 thesis, CC BY-NC-ND 2.0 KR
      "sj_kimbh", "sj_kimjp", "sj_seong", "sj_ham"}  # Yang 2013 thesis, CC BY-NC-SA 2.0 KR
OCTAVE_MEASURED = {"gy_lee1928"}  # last value is the measured upper Do (string 11), not a missing octave  # computed from ORD-CC32 (CC BY-NC 4.0)


def frame() -> pd.DataFrame:
    df = pd.DataFrame(SCALES, columns=COLS)
    df["cents_down"] = df["id"].map(lambda i: ";".join(f"{x:g}" for x in DOWN[i]) if i in DOWN else "")
    df["cents"] = df["cents"].map(lambda v: ";".join(f"{x:g}" for x in v))
    df["sd"] = df["sd"].map(lambda v: "" if v is None else ";".join(f"{x:g}" for x in v))
    df["license"] = df["id"].map(lambda i: "CC-BY-NC-4.0" if i in NC else "CC-BY-4.0")
    return df


def esc(s):
    return html.escape("" if s is None else str(s))


CSS = """.scale{border-top:1px solid var(--line);padding:.6rem 0 .3rem}.scale h3{margin:0;font-size:.95rem}.scale .meta{color:var(--fg3);font-size:.82rem;margin:.1rem 0 .2rem}
.scale .btns{display:flex;gap:.4rem;flex-wrap:wrap;margin:.2rem 0}.scale button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:.15rem .7rem;font-size:.82rem;cursor:pointer}
.scale button:hover{border-color:var(--fg3)}.scale .kind{font-size:.72rem;border-radius:4px;padding:0 .35rem;margin-left:.35rem;vertical-align:1px}
.kind.theory{background:color-mix(in srgb,var(--g1) 22%,transparent)}.kind.measured{background:color-mix(in srgb,var(--g2) 26%,transparent)}"""

JS = """<script>(function(){var ac=null;function ctx(){if(!ac){ac=new (window.AudioContext||window.webkitAudioContext)()}return ac}
function tone(f,t,d){var a=ctx(),o=a.createOscillator(),g=a.createGain();o.type='triangle';o.frequency.value=f;g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(.22,t+.02);g.gain.exponentialRampToValueAtTime(.001,t+d);o.connect(g);g.connect(a.destination);o.start(t);o.stop(t+d+.05)}
var BASE=261.63;function play(c,mode,d){var a=ctx(),t=a.currentTime+.05,seq=c.slice();if(mode==='updown'){var dn=(d||c).slice();seq=seq.concat(dn.slice(0,-1).reverse())}
if(mode==='compare'){c.forEach(function(x){tone(BASE*Math.pow(2,x/1200),t,.55);tone(BASE*Math.pow(2,Math.round(x/100)*100/1200),t+.6,.55);t+=1.3});return}
seq.forEach(function(x){tone(BASE*Math.pow(2,x/1200),t,.5);t+=.42})}
document.querySelectorAll('.scale button[data-c]').forEach(function(b){b.addEventListener('click',function(){var c=JSON.parse(b.getAttribute('data-c')),d=b.getAttribute('data-d');play(c,b.getAttribute('data-m'),d?JSON.parse(d):null)})})})();</script>"""


def ruler(cents, sd, width=900, height=58, lo=0, hi=1260, down=None, added=None):
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
        if added is not None and v == added and i == len(cents) - 1:
            o.append(f'<circle cx="{X(v):.1f}" cy="24" r="4" fill="none" stroke="var(--fg3)" stroke-width="1.5" stroke-dasharray="2 2"><title>{v:g} cents (added for playback, not in the source)</title></circle>')
            continue
        if sd and sd[i]:
            o.append(f'<line x1="{X(v - sd[i]):.1f}" x2="{X(v + sd[i]):.1f}" y1="24" y2="24" stroke="var(--g2)" stroke-width="7" stroke-opacity=".45" stroke-linecap="round"/>')
        o.append(f'<circle cx="{X(v):.1f}" cy="24" r="5.5" fill="var(--g1)" stroke="var(--card)" stroke-width="1.5"><title>{v:g} cents{f" ± {sd[i]:g}" if sd and sd[i] else ""}</title></circle>')
    for v in (down or []):
        if v not in cents:
            o.append(f'<circle cx="{X(v):.1f}" cy="24" r="4.5" fill="var(--card)" stroke="var(--g1)" stroke-width="2"><title>{v:g} cents (descending)</title></circle>')
    o.append("</svg>")
    return "".join(o)


GROUPS = {"west": ("1. 서양 조율의 역사 — 비율로 정의된 이론값", "1. Western tuning — values defined by ratios"),
          "east": ("2. 동아시아 — 삼분손익과 일본의 두 음계", "2. East Asia — sanfen sunyi (三分損益) and Japan's two scales"),
          "measured": ("3. 이론과 실측", "3. Theory and measurement")}


JP_KO = '일본의 두 5음 음계에 음선(陰旋)·양선(陽旋)이라는 이름을 붙인 사람은 우에하라 로쿠시로다(『속악선율고』, 1895, 79쪽). 그는 소쿄쿠·나가우타·지우타처럼 도시에서 연주하는 음악의 음계를 미야코부시, 뱃노래·마부 노래·모내기 노래 같은 시골 노래의 음계를 이나카부시로 나누고, 앞의 것을 음선, 뒤의 것을 양선이라 불렀다. 두 음계 모두 다섯째 음이 올라갈 때와 내려갈 때 다르다. 음선은 일현금의 현 길이로 재었고(90~91쪽), 두 음계의 음을 104~107쪽에 진동수 비로 정리했다. 음선이 올라갈 때 쓰는 다섯째 음은 유파와 샤미센 조율에 따라 12/7·7/4·9/5 가운데 하나라고 했는데, 여기서는 7/4로 들려준다. 105~106쪽 표는 둘째·셋째 음을 15/16·4/8로 찍었으나, 같은 표의 음정 칸과 91쪽 현 길이 비에 맞추어 16/15·4/3으로 읽었다. 양선의 비는 몇 번 시험해 얻은 값일 뿐이라 정확하다고 할 수 없다고 우에하라 스스로 밝혔다. 「올라갔다 내려오기」를 누르면 내려올 때 속이 빈 점의 음으로 바꿔 들려준다.'
JP_EN = "The names in (陰旋) and yō (陽旋) for Japan's two five-note scales come from Uehara Rokushirō (Zokugaku senritsu kō, 1895, p. 79). He separated the scale of urban music such as zokusō, nagauta and jiuta (miyako-bushi) from that of rural songs such as boat, packhorse and rice-planting songs (inaka-bushi), and called the first in and the second yō. In both, the fifth note differs going up and coming down. He measured the in scale by string lengths on a monochord (pp. 90–91) and gave both scales as frequency ratios on pp. 104–107. For the ascending fifth note of the in scale he gave 12/7, 7/4 or 9/5, depending on the school and the shamisen tuning; 7/4 is used here. The table on pp. 105–106 prints 15/16 and 4/8 for the second and third notes; they are read as 16/15 and 4/3 to match the table's own interval column and the string-length ratios on p. 91. Of the yō ratios Uehara wrote that they came from only a few trials and could not be called exact. 'Up and down' switches to the hollow-dot note on the way down."
KOTO_KO = '고토의 히라조시 조율은 엘리스(1885)가 런던 나이츠브리지의 일본촌에서 힙킨스와 함께 두 연주자의 조율을 잰 값을, 이사와 슈지가 보내온 보고의 값과 나란히 실었다(522쪽). 엘리스는 여성 연주자의 5도가 높고 스승의 5도가 낮아 둘이 36센트 어긋났다고 적었다. 넷째 줄과 다섯째 줄 사이는 보고에서 386센트였으나 두 사람은 362센트와 346센트로 조율했다.'
KOTO_EN = "For the koto's hira-jōshi tuning, Ellis (1885) printed the tunings of two players he measured with Hipkins at the Japanese Village in Knightsbridge, London, beside the values in a report sent by Isawa Shūji (p. 522). He noted that the woman's fifth was sharp and her master's flat, 36 cents apart. Between strings IV and V the report has 386 cents; the two players tuned 362 and 346."
ME_KO = '아랍 음악의 24 4분음은 19세기 다마스쿠스의 미하일 무샤카가 정리한 체계다. 그는 옥타브를 4분음 24개로 세고, 라스트에서 시작하는 일곱 음정을 4분음 4·3·3·4·4·3·3개로 나누었다(엘리 스미스 영역 1847, 176쪽). 그는 4분음이 같은 음정이 되도록 현 위의 길이를 일정한 비율로 줄여 가는 작도법을 제시했다(213~215쪽). 여기서는 그것을 50센트로 놓고 그렸고, 그러면 셋째 음은 350센트, 장3도와 단3도의 한가운데에 온다. 다만 무샤카는 두 탐부르를 견주어 본 뒤 아랍식 4분음 분할이 틀리고 그리스식 분할이 옳다고 적기도 했다(216쪽). 1932년 카이로 아랍 음악 회의는 음계를 정하려고 위원회를 두었으나 최종 합의안을 내지 못했다(Bozkurt 2025). 그 회의 때 녹음한 음반의 음높이 자료(ORD-CC32)로 엮은이가 녹음별 히스토그램을 평균해 정점을 다시 계산했다. 이집트 녹음 13곡의 라스트에서 셋째 음은 355센트, 이라크 녹음 3곡에서는 376센트였다. 이집트 녹음 17곡의 바야티에서 둘째 음은 150센트다. 히스토그램 칸이 20센트이므로 몇 센트의 차이는 읽지 않는 것이 좋다.'
ME_EN = 'The 24 quarter tones of Arabic music were set out by Mīkhāʾīl Mushāqa of Damascus in the 19th century. He counted 24 quarters to the octave and divided the seven steps from rast into 4, 3, 3, 4, 4, 3 and 3 quarters (tr. Eli Smith 1847, p. 176). He gave a construction that shortens the quarters along the string in a fixed ratio so that they come out as equal intervals (pp. 213–215). They are drawn here as 50 cents each, which puts the third degree at 350 cents, halfway between a major and a minor third. Yet after comparing two tamburs Mushāqa also wrote that the Arab division into quarters was in error and the Greek division right (p. 216). The 1932 Cairo Congress of Arab Music set up a committee to fix the scale, but it reached no final agreed proposal (Bozkurt 2025). From the pitch data of the Congress recordings (ORD-CC32), the editor averaged the per-recording histograms and recomputed the peaks. In 13 Egyptian recordings of Rast the third degree lies at 355 cents; in 3 Iraqi recordings, at 376. In 17 Egyptian recordings of Bayati the second degree lies at 150 cents. The histogram bins are 20 cents wide, so differences of a few cents should not be read into.'
IN_KO = '인도의 22 슈루티는 바라타의 『나티야샤스트라』에 나온다. 사드자 그라마의 일곱 음이 각각 슈루티 4·3·2·4·4·3·2개를 차지한다(28장 24~26절, Ghosh 영역 2권 8쪽). 원전은 슈루티의 개수만 말하고 크기는 말하지 않으므로, 여기서는 같은 크기로 놓고 그렸다. 라마나탄(1981)에 따르면 바라타에게 슈루티는 두 음의 높낮이를 가려낼 수 있는 가장 작은 음정이었고, 다틸라·샤른가데바에게는 먼저 그렇게 갈리는 음 위치였다(33쪽). 슈루티는 스바라의 크기를 재어 그라마를 나누는 단위이며, 분류를 위해 세운 개념이라 연주에는 존재하지 않았다고 했다(32쪽). 한 스바라 안의 슈루티는 「대략 같은」 크기이고 그 정확한 크기는 중요하지 않다고 했다. 22라는 총수를 신성하게 여길 까닭은 없고 중요한 것은 각 스바라가 차지하는 슈루티 수라고 했다(34~35쪽). 근대 분류의 특정 스바라 위치를 9/8이나 10/9 같은 비율로 나타내는 것은 이미 아는 사실을 다른 말로 바꾸는 데 지나지 않는다고 보았다(36~37쪽). 아래의 실측 연구가 견준 22 슈루티는 이 그림이 아니라, 옥타브를 크기가 다른 22개로 나눈 근대의 비율 체계다. 오늘날의 노래를 잰 Serrà 외(2011)는 카르나틱 233곡과 힌두스타니 133곡의 음정 히스토그램을 순정률·평균율과 견주었다. 카르나틱은 순정률 쪽(상관 0.552 대 0.448), 힌두스타니는 평균율 쪽(0.723 대 0.641)에 더 가까웠다. 그 22 슈루티 체계에만 있는 일곱 위치에서 힌두스타니는 정점이 없었고, 카르나틱은 세 곳에 작은 기여가 있었을 뿐이다. 저자들은 22 슈루티를 뒷받침하는 강한 정량 증거가 없지만 배제할 수도 없다고 결론지었다.'
IN_EN = "The 22 śrutis come from Bharata's Nāṭyaśāstra: the seven notes of the ṣaḍja-grāma take 4, 3, 2, 4, 4, 3 and 2 śrutis (28.24–26; tr. Ghosh, vol. II, p. 8). The text gives the number of śrutis, not their size, so they are drawn here as equal. According to Ramanathan (1981), for Bharata the śruti was the least perceptible difference in pitch between two sounds, while for Dattila and Śārṅgadeva it was first the pitch position so distinguished (p. 33). It is a unit for measuring the size of svaras and sorting them into the two grāmas; formulated for classification, it 'had no existence in performance' (p. 32). The śrutis within a svara are 'roughly equal' and their exact size is of no importance; the total of 22 has no sanctity, what matters being the number of śrutis in each svara (pp. 34–35). Expressing the position of a particular svara of the modern classification as a ratio such as 9/8 or 10/9 only puts known facts in a different language (pp. 36–37). The 22 śrutis tested in the measurement study below are not this drawing but a modern ratio system that divides the octave into 22 unequal steps. Measuring present-day singing, Serrà et al. (2011) compared interval histograms of 233 Carnatic and 133 Hindustani recordings with just intonation and equal temperament. Carnatic singing was closer to just intonation (correlation 0.552 vs 0.448), Hindustani closer to equal temperament (0.723 vs 0.641). At the seven positions found only in that 22-śruti system, Hindustani showed no peaks and Carnatic only small contributions at three. The authors concluded that the 22 śrutis lack strong quantitative support but cannot be ruled out."
CH_KO = '모잠비크 초피의 팀빌라는 옥타브를 일곱 개의 거의 같은 음정으로 나눈다. 트레이시는 212~424진동을 4진동 간격으로 나눈 소리굽쇠 54개로 그동안 악기 수백 대를 쟀고, 음높이를 ±2진동 안에서 정할 수 있었다고 적었다(『초피 음악가들』, 1948, 122쪽). 그는 1940년부터 해마다 초피 마을을 찾았고, 책에 실은 음계 대부분을 1943년 9월 26일 키시코(Quissico)에서 연 회의 전에 기록해 두었다. 그 회의에서 악기 제작자와 악단 지휘자들은, 기준음 홈베의 높이는 저마다 달라도 모두 「일곱 음정이 모두 같은 고른 음계」를 지향한다고 말했다(123~124쪽). 자발라 지구 다섯 악단의 음정은 141~207센트에 걸쳐 있고(7평균율이면 171센트), 홈베는 252~276진동이었다(125쪽 도표 IV). 다섯 악단 평균의 주황 막대는 악단 사이의 표준편차다. 한 악기 행은 트레이시(1958)가 실은 값으로, 1948년 도표의 자발라 악단과 같다. 앤드루 트레이시는 『뉴 그로브』 2판(2001)의 「모잠비크」 항목에서 이 조율을 음정마다 약 170센트인 7음 등분이라 하고, 홈베의 절대 높이는 마을마다 약 100센트 넘게 다르지 않다고 적었다. 1948년 도표의 다섯 악단 홈베(252~276진동)는 약 157센트에 걸쳐 있지만, 도표 머리에는 가장 높은 잔다멜라(276)가 그 뒤 자발라처럼 홈베 252로 다시 조율했다는 주가 붙어 있다. 나머지 네 악단(252~260진동)만 보면 약 54센트다.'
CH_EN = "The Chopi timbila of Mozambique divides the octave into seven nearly equal steps. Over his fieldwork Tracey measured several hundred instruments with 54 tuning forks spanning 212–424 vibrations in steps of four, and wrote that he could fix a pitch to within two vibrations (Chopi Musicians, 1948, p. 122). He visited Chopi villages every year from 1940 and had noted most of the scales in the book before a meeting at Quissico on 26 September 1943, where instrument makers and orchestra leaders said that, whatever their differences over the pitch of the tonic Hombe, each was aiming at 'an even scale of seven intervals, all alike' (pp. 123–124). In five orchestras of the Zavala District the steps range from 141 to 207 cents (171 for seven equal steps), and Hombe lay at 252–276 vibrations (p. 125, Diagram IV). The orange bars on the five-orchestra mean show the spread between orchestras. The single-instrument row gives the values Tracey printed in 1958, the same as the Zavala orchestra in the 1948 diagram. In the 'Mozambique' article of the New Grove, second edition (2001), Andrew Tracey calls the tuning equiheptatonic, each step about 170 cents, and says the absolute pitch of the tonic does not vary from village to village by more than about 100 cents; the Hombe of the five orchestras in the 1948 diagram (252–276 vibrations) spans about 157 cents, but a note under the diagram's title says that Zandamela, the highest (276), has since retuned to Zavala's Hombe of 252; the other four (252–260 vibrations) span about 54 cents."
NY_KO = "다음은 원문을 열지 못했거나, 열었지만 음계로 옮길 수 없어 넣지 않았다. ① 1932 카이로 회의 기록집(<i>Recueil des travaux du Congrès de musique arabe qui s'est tenu au Caire en 1932</i>, Le Caire: Imprimerie nationale, 1934)과 데를랑제(R. d'Erlanger) 『아랍 음악(<i>La musique arabe</i>)』 5권(Paris: Geuthner, 1949)의 음계표 — 출판본을 보지 못했다. ② 모크타르·모샤라파, 「Modes in Modern Egyptian Music」, <i>Nature</i> 140: 548–549 (1937) — 본문을 보지 못했다. ③ Serrà 외(2011)가 견준 22 슈루티의 비율 — 그들이 따른 2차 문헌(Shankar 1999, Schmidt-Jones 2011)을 보지 못했다. 근대 비율 체계 가운데 클레먼츠 1913의 표(데발의 측정)는 3절에 실었다. ④ 다른 국악기 실측 — 박수홍·옥승호·서인화·김소리·정환희, 「국악관악기 품질평가를 위한 음고특성분석」, 『한국소음진동공학회 2011년 춘계학술대회논문집』 302–307쪽은 국립국악원 연주자 세 사람이 시판 대금·소금·퉁소·단소를 분 음높이를 쟀으나, 음별 값이 그림에만 있고 비교 기준인 「평균율 기준음고」를 정의하지 않아 음계로 옮기지 않았다. ⑤ 실제 곡에서 각 선법이 얼마나 쓰였는지 — 이 사이트가 쓰는 DCML 곡집의 조 표기(annotated_key)는 값이 있는 1,283악장이 모두 장조나 단조이고 43악장은 비어 있어, 이 열로는 선법별로 셀 수 없다. "
NY_EN = "Left out because the original could not be opened, or was opened but could not be turned into a scale: (1) the scale tables of the Cairo Congress proceedings (<i>Recueil des travaux du Congrès de musique arabe qui s'est tenu au Caire en 1932</i>, Cairo: Imprimerie nationale, 1934) and of R. d'Erlanger, <i>La musique arabe</i>, vol. 5 (Paris: Geuthner, 1949) — the printed books not seen; (2) M. Mokhtar & A. M. Mosharrafa, 'Modes in Modern Egyptian Music', <i>Nature</i> 140: 548–549 (1937) — full text not seen; (3) the 22-śruti ratios compared by Serrà et al. (2011) — the secondary sources they followed (Shankar 1999, Schmidt-Jones 2011) were not seen; of the modern ratio systems, Clements's 1913 table (after Deval's measurements) is drawn in section 3; (4) further measurements of Korean instruments — S.-H. Park, S.-H. Ock, I.-H. Seo, S.-R. Kim & H.-H. Jeong, 'Frequency characteristics analysis for quality assessment on Korean traditional wind instruments', Proceedings of the Korean Society for Noise and Vibration Engineering, Spring 2011, pp. 302–307, measured commercial daegeum, sogeum, tungso and danso played by three National Gugak Center players, but the per-note values are only in charts and the equal-tempered reference pitch is not defined, so they are not drawn; (5) how often each mode was used in actual pieces — in the DCML collections used on this site the key label (annotated_key) is major or minor in all 1,283 movements that have one, and empty in 43, so modes cannot be counted from it. "


KR_KO = '한국 악기를 직접 잰 값으로 가야금 연구 두 편을 실었다. 고유동(2021)은 1928~1960년 고음반에서 이일선·김죽파·성금연이 연주한 경기민요의 가야금 음높이를 praat로 재어, 줄마다 평균율과의 차이를 6번 줄(도)의 평균에 맞추어 정리했다(183쪽 표 102). 네 녹음 모두 레를 평균율보다 51~69센트 낮게, 라를 30센트 이상 낮게 탔고, 레–미 음정은 장2도보다 넓었다. 이일선 녹음의 11번 줄(높은 도)은 6번 줄보다 1141센트 위에 있어 옥타브보다 59센트 좁다. 양수연(2013)은 김병호·김죽파·성금연·함동정월의 가야금산조 진양조 음원에서 계면조의 중심음인 청과, 꺾는 음을 이루는 두 음을 쟀다. 여기에는 표본이 가장 많은 중간 음역의 값을 실었다(84·87·88쪽). 청에서 꺾는 아래음까지는 68~111센트로 채보에 쓰는 장2도(200센트)보다 훨씬 좁고, 꺾는 윗음까지는 350~354센트로 단3도(300센트)보다 넓다. 다만 함동정월의 윗음은 표에 적힌 센트값(353.8)을 따른 것이고, 같은 표의 주파수로 다시 계산하면 349.7센트다. 청의 옥타브는 1193~1206센트였다(47쪽). 고유동은 세 연주자의 녹음 넷(김죽파는 두 곡), 양수연은 네 연주자의 녹음 하나씩을 쟀다. 이 값이 연주자나 유파 전체를 대표한다고 볼 수는 없다. 관악기로는 남운정(Nam 1998)이 정재국의 피리 독주 녹음 세 곡(상령산 두 곡과 수제천)에서 음마다 떨림 없는 구간 열 곳 안팎을 재어, 음 사이의 평균 음정을 그림으로 실었다(244쪽 그림 1). 평조회상의 상령산에서 황–태는 141센트, 수제천의 태–고는 204센트였다. 다만 인쇄된 다섯 음정을 더하면 1208·1288·1177센트로 옥타브(1200)와 맞지 않고, 원문은 그 까닭을 적지 않았다. 그래서 다섯 음만 그리고 옥타브는 재생용 점선 고리로 두었다. 남운정은 피리의 음높이 굽힘이 커서 이 평균만으로 음계를 단정할 수 없다고 적었다.'
KR_EN = "Two gayageum studies supply measured values for a Korean instrument. Ko (2021) measured with Praat the gayageum pitches of Gyeonggi folk songs played by Lee Ilseon, Kim Jukpa and Seong Geumyeon on records from 1928 to 1960, and gave each string's deviation from equal temperament with the mean of string 6 (Do) set to zero (p. 183, Table 102). In all four records Re is 51–69 cents below equal temperament and La at least 30 cents below, and the Re–Mi step is wider than a major second. In Lee Ilseon's record string 11 (upper Do) lies 1,141 cents above string 6, 59 cents short of an octave. Yang (2013) measured, in jinyangjo recordings of gayageum sanjo by Kim Byeongho, Kim Jukpa, Seong Geumyeon and Ham Dongjeongwol, cheong, the central note of gyemyeonjo, and the two notes of the bent figure (kkeongneun eum). The values shown are for the middle register, which has the most samples (pp. 84, 87–88). From cheong to the lower bent note is 68–111 cents, far narrower than the major second (200 cents) used in transcription; to the upper bent note, 350–354 cents, wider than a minor third (300). Ham Dongjeongwol's upper note follows the cent value printed in the table (353.8); the table's own frequencies give 349.7 cents. Cheong's octave measured 1,193–1,206 cents (p. 47). Ko measured four records by three players (two songs by Kim Jukpa), Yang one recording each by four players. The values do not stand for a player or school as a whole. For a wind instrument, Unjung Nam (1998) measured about ten stable (non-vibrato) samples per tone in three solo p'iri recordings by Chung Chaekook (two Sangnyeongsan and Sujecheon) and drew the average intervals between tones (p. 244, Fig. 1). In the Sangnyeongsan of Pyeongjo hoesang hwang–tae is 141 cents; in Sujecheon tae–go is 204. The five printed intervals of each work, however, sum to 1,208, 1,288 and 1,177 cents rather than an octave, and the article does not say why, so only the five tones are drawn and the octave is the dashed playback ring. Nam notes that the wide pitch bends of the p'iri keep these averages from settling the scale on their own."


LIM = [  # Lim Gyeongmi 2013, MA thesis, Seoul National Univ., p. 114, Table 140: mean interval jing (c') - ttang (d'), cents
    ("김죽파류", "Kim Jukpa school", "157.89", "184.51", "156.76", "155.17", "185.76"),
    ("김병호류", "Kim Byeongho school", "155.01", "–", "156.09", "169.00", "154.82"),
    ("강태홍류", "Kang Taehong school", "155.37", "164.51", "118.76", "86.04", "143.23"),
]
LIM_KO = ("임경미(2013)는 김죽파·김병호·강태홍류 가야금산조의 진양조와 중모리에서 악조마다 징(c′)과 땅(d′) 사이의 음정을 쟀다(114쪽 표 140). 오선보에는 장2도(200센트)로 적는 음정인데, 열네 값 모두 그보다 좁았고 강태홍류 경드름(86센트)을 빼면 모두 단2도와 장2도 사이였다. 음계 전체가 아니라 음정 하나라서 자 위에 그리지 않고 표로 둔다.")
LIM_EN = ("Lim (2013) measured, in the jinyangjo and jungmori of the Kim Jukpa, Kim Byeongho and Kang Taehong schools of gayageum sanjo, the interval between jing (c′) and ttang (d′) in each mode (p. 114, Table 140). Staff notation writes it as a major second (200 cents); all fourteen values are narrower, and all but Kang Taehong's gyeongdeureum (86 cents) lie between a minor and a major second. It is one interval rather than a scale, so it is shown as a table rather than on the ruler.")


# ---- 1.13: modes (section 4). Everything here is arithmetic on the white keys; the names come from
# Cleonides, Harmonic Introduction 9-10 (tr. Strunk, Source Readings, 1950, pp. 34-46) and Glarean, Dodecachordon (1547),
# title-page table, I.21 and II.5 (tr. Bohn 1888, pp. 49, 65).
WK = "CDEFGAB"
TUNINGS = {  # cents of the white keys C D E F G A B above C
    "et": [0.0, 200.0, 400.0, 500.0, 700.0, 900.0, 1100.0],
    "pyth": [c(r) for r in (1, 9/8, 81/64, 4/3, 3/2, 27/16, 243/128)],
    "mean": [meantone12()[i] for i in (0, 2, 4, 5, 7, 9, 11)],
}
TUN_LABEL = {"et": ("12평균율", "12-tone equal"), "pyth": ("피타고라스 음률", "Pythagorean"), "mean": ("4분의 1 쉼표 중전음률", "Quarter-comma meantone")}
MODES = [  # white key the mode starts on (index into WK), id, ko, en
    (0, "ionian", "이오니아", "Ionian"), (1, "dorian", "도리아", "Dorian"), (2, "phrygian", "프리지아", "Phrygian"),
    (3, "lydian", "리디아", "Lydian"), (4, "mixolydian", "믹솔리디아", "Mixolydian"), (5, "aeolian", "에올리아", "Aeolian"),
    (6, "locrian", "로크리아", "Locrian")]
FIFTHS_ORDER = [3, 0, 4, 1, 5, 2, 6]  # starting keys F C G D A E B: each mode lowers one degree of the one before
GREEK = {6: ("믹솔리디아", "Mixolydian"), 0: ("리디아", "Lydian"), 1: ("프리지아", "Phrygian"), 2: ("도리아", "Dorian"),
         3: ("하이포리디아", "Hypolydian"), 4: ("하이포프리지아", "Hypophrygian"), 5: ("하이포도리아 (공통·로크리아)", "Hypodorian (common, Locrian)")}
GLAREAN = {0: ("Ionicus", "Ionicus"), 1: ("Dorius", "Dorius"), 2: ("Phrygius", "Phrygius"), 3: ("Lydius", "Lydius"),  # Latin as printed
           4: ("Mixolydius", "Mixolydius"), 5: ("Aeolius", "Aeolius"), 6: ("Hyperaeolius (뺌)", "Hyperaeolius (rejected)")}
SHARED = {"Dorian": "var(--g1)", "Phrygian": "var(--g2)", "Lydian": "var(--g3)", "Mixolydian": "var(--g4)"}


def mode_cents(s: int, tun: str = "et") -> list[float]:
    """Cents above the starting note of the eight white keys s .. s+7 (s = 0 for C) in a tuning."""
    T = TUNINGS[tun]
    a = [T[i % 7] + 1200 * (i // 7) for i in range(s, s + 8)]
    return [round(v - a[0], 1) for v in a]


def is_semitone(i: int) -> bool:
    """True if white key i to i+1 is a semitone (E-F or B-C)."""
    return WK[i % 7] in "EB"


def keyboard(s: int, k: bool) -> str:
    """Fourteen white keys C..b with the octave s .. s+7 shaded and each step marked tone or semitone."""
    W, H, n = 900, 92, 14
    kw = (W - 20) / n
    o = [f'<svg viewBox="0 0 {W} {H}" role="img">']
    for i in range(n):
        x = 10 + i * kw
        on = s <= i <= s + 7
        fill = "#c4d7ee" if on else "#f6f4ef"
        o.append(f'<rect x="{x:.1f}" y="26" width="{kw - 2:.1f}" height="50" rx="3" fill="{fill}" stroke="#8a8780"/>')
        o.append(f'<text x="{x + kw / 2 - 1:.1f}" y="70" text-anchor="middle" style="fill:#2a2a2a"{" font-weight=" + chr(34) + "700" + chr(34) if i == s or i == s + 7 else ""}>{WK[i % 7]}</text>')
    for i in range(n - 1):  # black keys sit between white keys except E|F and B|C
        if not is_semitone(i):
            x = 10 + (i + 1) * kw - kw * .28
            o.append(f'<rect x="{x:.1f}" y="26" width="{kw * .54:.1f}" height="28" rx="2" fill="#26262a"/>')
    for i in range(s, s + 7):
        x = 10 + (i + 1) * kw - 1
        semi = is_semitone(i)
        lab = ("반" if semi else "온") if k else ("S" if semi else "T")
        col = "var(--g2)" if semi else "var(--fg3)"
        o.append(f'<text x="{x:.1f}" y="17" text-anchor="middle" style="fill:{col}"{" font-weight=" + chr(34) + "700" + chr(34) if semi else ""}>{lab}</text>')
    o.append("</svg>")
    return "".join(o)


def ruler_changed(cents: list[float], changed: int | None) -> str:
    """The cent ruler of ruler(), with the degree lowered from the previous mode in orange and its old place hollow."""
    s = ruler(cents, None, added=None)
    if changed is None:
        return s
    X = lambda v: 10 + v / 1260 * 880  # noqa: E731  same scale as ruler()
    v = cents[changed]
    extra = (f'<circle cx="{X(v + 100):.1f}" cy="24" r="4.5" fill="var(--card)" stroke="var(--g2)" stroke-width="2"/>'
             f'<circle cx="{X(v):.1f}" cy="24" r="6" fill="var(--g2)" stroke="var(--card)" stroke-width="1.5"/>')
    return s.replace("</svg>", extra + "</svg>")


def names_map(k: bool) -> str:
    """Rows C..B: Cleonides' octave species starting on that key, Glarean's authentic mode on that final, today's name."""
    W, top, rh = 900, 34, 30
    H = top + 7 * rh + 6
    xg, xl, xm = 360, 520, 760  # right edge of the Greek column, left edge of Glarean's, today's
    o = [f'<svg viewBox="0 0 {W} {H}" role="img">']
    heads = (("시작 건반", "클레오니데스: 옥타브 종", "글라레안 1547: 정격", "오늘의 이름") if k else
             ("Starts on", "Cleonides: octave species", "Glarean 1547: authentic", "Today"))
    o.append(f'<text x="30" y="18" font-weight="700">{heads[0]}</text><text x="{xg}" y="18" text-anchor="end" font-weight="700">{heads[1]}</text>'
             f'<text x="{xl}" y="18" font-weight="700">{heads[2]}</text><text x="{xm}" y="18" font-weight="700">{heads[3]}</text>')
    y = lambda i: top + i * rh + rh / 2  # noqa: E731
    for i in range(7):
        g, gl, md = GREEK[i], GLAREAN[i], MODES[i]
        gc = SHARED.get(g[1].split(" ")[0], "var(--fg)")
        lc = SHARED.get(md[3] if md[3] in SHARED else "", "var(--fg)")
        o.append(f'<text x="40" y="{y(i) + 5:.0f}" text-anchor="middle" font-weight="700">{WK[i]}</text>'
                 f'<text x="{xg}" y="{y(i) + 5:.0f}" text-anchor="end" style="fill:{gc}">{esc(g[0] if k else g[1])}</text>'
                 f'<text x="{xl}" y="{y(i) + 5:.0f}" style="fill:{lc}">{esc(gl[0] if k else gl[1])}</text>'
                 f'<text x="{xm}" y="{y(i) + 5:.0f}">{esc(md[2] if k else md[3])}</text>')
    for nm, col in SHARED.items():  # join the same name in the two columns
        a = next(i for i in range(7) if GREEK[i][1] == nm)
        b = next(i for i in range(7) if MODES[i][3] == nm)
        o.append(f'<path d="M{xg + 8},{y(a):.0f} C{xg + 80},{y(a):.0f} {xl - 80},{y(b):.0f} {xl - 8},{y(b):.0f}" fill="none" stroke="{col}" stroke-width="2"/>')
    o.append("</svg>")
    return "".join(o)


MODE_INTRO_KO = ("이 절에서는 선법을 한 옥타브 안에서 온음과 반음이 놓이는 순서로 구별하고, 같은 일곱 음을 서로 다른 음에서 시작해 한 옥타브로 늘어놓아 견준다(선법을 끝음과 음역으로 더 나누는 이론도 있다. 아래 「이름의 역사」 참조). "
                 "피아노의 흰 건반 일곱 개만 써도 시작음을 바꾸면 온음과 반음의 자리가 달라진다. 흰 건반 사이의 반음은 E–F와 B–C 두 곳뿐이고(검은 건반이 없는 자리), 시작음이 한 칸 오를 때마다 두 반음이 옥타브 안에서 한 칸씩 앞으로 온다. 맨 앞에 있던 반음은 맨 뒤로 돌아간다(E에서 F로 넘어갈 때). "
                 "이름은 오늘 쓰는 것을 붙였고, 한국어 표기는 교육부 편수자료(2023)의 음악 용어를 따랐다. 로크리아와 하이포도리아는 그 표에 없어 같은 방식으로 옮겼다.")
MODE_INTRO_EN = ("Here modes are told apart by the order of tones and semitones within an octave, and the same seven notes are laid out an octave from different starting notes for comparison (some theories divide modes further by final and range; see 'Where the names came from' below). "
                 "The seven white keys of a piano alone give different arrangements: change the starting key and the tones and semitones fall in different places. Between white keys there are only two semitones, E–F and B–C (where there is no black key); each time the starting key moves up one, the two semitones move one step earlier in the octave, and a semitone in first place wraps round to last (from E to F). "
                 "The names are today's.")
TUN_KO = ("「조율」 단추로 이 일곱 줄을 12평균율, 피타고라스 음률(순정 5도를 쌓은 값), 4분의 1 쉼표 중전음률로 바꿔 들을 수 있다. 흰 건반의 높이만 바뀌고 온음·반음의 순서는 그대로다. "
          "장3도 C–E는 12평균율에서 400센트, 피타고라스 음률에서 408센트, 중전음률에서 386센트다. 소리는 가온 다(261.63 Hz)를 C로 놓고, 선법마다 그 시작 건반의 높이에서 시작한다.")
TUN_EN = ("The 'Tuning' buttons play these seven rows in 12-tone equal temperament, Pythagorean tuning (stacked pure fifths) or quarter-comma meantone. Only the pitches of the white keys change; the order of tones and semitones does not. "
          "The major third C–E is 400 cents in equal temperament, 408 in Pythagorean tuning and 386 in meantone. Middle C (261.63 Hz) is C, and each mode starts at the pitch of its own starting key.")
ONE_KO = ("같은 으뜸음 D 위에 일곱 선법을 5도 순서(흰 건반의 시작음 F C G D A E B)로 놓으면, 한 줄 내려갈 때마다 음 하나가 반음 내려간다. 리디아에서 이오니아로 4음, 믹솔리디아로 7음, 도리아로 3음, 에올리아로 6음, 프리지아로 2음, 로크리아로 5음이다. "
          "주황 점은 바로 위 줄에서 반음 내려간 음이고, 속 빈 주황 고리는 그 음이 있던 자리다. 「위 줄과 이어서」는 위 줄의 선법과 이 줄의 선법을 차례로 들려준다. 에올리아 줄에서 누르면 도리아와 에올리아의 차이, 곧 6음 하나(B와 B♭)가 들린다. 이 부분은 12평균율로만 들려준다.")
ONE_EN = ("Put the seven modes on the same final, D, in the order of fifths (starting white keys F C G D A E B), and each row lowers one note of the row above by a semitone: Lydian to Ionian the 4th, then the 7th (Mixolydian), the 3rd (Dorian), the 6th (Aeolian), the 2nd (Phrygian) and the 5th (Locrian). "
          "The orange dot is the note lowered from the row above, and the hollow orange ring is where it was. 'After the row above' plays the mode of the row above and then this one; on the Aeolian row it lets you hear the one note, the 6th (B against B♭), that separates Dorian from Aeolian. This part plays in equal temperament only.")
HIST_KO = ("오늘의 이름과 고대 그리스의 이름은 같은 말이지만 가리키는 배열이 다르다. 연대가 확실하지 않은 클레오니데스의 『화성학 입문』은 옥타브에 일곱 종(種)이 있다고 하고, 옛사람들이 그것을 믹솔리디아·리디아·프리지아·도리아·하이포리디아·하이포프리지아라 불렀고, 일곱째를 「공통」 또는 「로크리아」 또는 「하이포도리아」라 불렀다고 적었다(9~10절, Strunk 영역). "
           "그는 각 종을 그리스 음 이름으로 경계 짓고, 온음계에서 반음이 아래·위에서 몇째에 오는지도 적었다. 그 반음 자리를 흰 건반에 맞추면 그리스의 도리아는 E에서 E까지, 곧 오늘의 프리지아 배열이다. 같은 방식으로 그리스의 프리지아는 D(오늘의 도리아), 리디아는 C(오늘의 이오니아), 믹솔리디아는 B(오늘의 로크리아)에서 시작한다. 이 대응은 온음과 반음의 순서가 같다는 뜻일 뿐, 그리스 음악의 실제 음높이나 조율이 흰 건반과 같았다는 뜻은 아니다.")
HIST_EN = ("Today's names and the ancient Greek names are the same words for different arrangements. Cleonides' Harmonic Introduction, of uncertain date, says the octave has seven species and that the ancients called them Mixolydian, Lydian, Phrygian, Dorian, Hypolydian and Hypophrygian, the seventh 'common or Locrian or Hypodorian' (sections 9–10, tr. Strunk). "
           "He bounds each species by Greek note names and says where the semitones fall, counted from the bottom and the top, in the diatonic genus. Matched to the white keys by those semitones, the Greek Dorian runs from E to E, which is today's Phrygian. In the same way the Greek Phrygian starts on D (today's Dorian), the Lydian on C (today's Ionian) and the Mixolydian on B (today's Locrian). The match is only in the order of tones and semitones; it does not mean that the pitches or tunings of Greek music were those of the white keys.")
GLAR_KO = ("1547년 바젤에서 나온 글라레안의 『도데카코르돈』 표제면에는 정격 선법 여섯이 끝음과 함께 실려 있다. Dorius D, Phrygius E, Lydius F, Mixolydius G, Aeolius A, Ionicus C다(라틴어 표기 그대로). 같은 표에 B의 Hyperaeolius와 그 변격인 Hyperphrygius가 따로 적혀 있는데(변격 쪽의 F는 음역의 아래 끝이다), 글라레안은 이 둘을 빼고 정격 여섯·변격 여섯의 12선법을 세웠다(1권 21장, 독일어 역 49쪽). "
           "그는 당대 사람들이 「8개 선법 또는 톤」을 들어 왔다고 적고, 선법은 본질상 옥타브 종의 수대로 일곱뿐이지만 정격과 변격으로 나누면 열둘이라고 했다(2권 5장, 독일어 역 65쪽 — 56쪽 자리에 65로 잘못 찍힌 쪽이다). 같은 쪽에서 그는 반음 하나만 바꿔도 선법의 성격이 완전히 달라진다고 하고, 당시 음악가들이 옛 여섯째·일곱째 선법을 뒤집어 새 다섯째·여섯째 선법, 곧 이오니아 선법 둘을 만들었으며 그것이 지금 리디아 선법보다 더 많이 쓰인다고 적었다(번호는 글라레안이 쓴 옛 번호와 새 번호다). "
           "두 자료를 흰 건반 위에 놓으면 네 이름(도리아·프리지아·리디아·믹솔리디아)은 서로 다른 배열에 붙어 있다. 에올리아와 이오니아는 글라레안의 표에서 A와 C에 붙었고, 오늘 B에서 시작하는 선법을 부르는 「로크리아」는 클레오니데스에게는 A에서 시작하는 종의 다른 이름이었다.")
GLAR_EN = ("The title page of Glarean's Dodecachordon (Basel, 1547) lists six authentic modes with their finals: Dorius D, Phrygius E, Lydius F, Mixolydius G, Aeolius A and Ionicus C. The same table names, apart, a Hyperaeolius on B and its plagal, a Hyperphrygius (the F on the plagal side is the bottom of its range); Glarean set these two aside and built twelve modes, six authentic and six plagal (book I, ch. 21; German tr. p. 49). "
           "He wrote that his contemporaries had counted 'eight modes or tones', and that by nature there are only seven modes, as there are only seven species of the octave, but twelve if they are divided into authentic and plagal (book II, ch. 5; German tr. p. 65, a misprint for p. 56). On the same page he wrote that changing a single semitone can alter a mode's character entirely, and that musicians of his day, by inverting the old sixth and seventh modes, had made two Ionian modes, the new fifth and sixth, now more used than the Lydian (the numbers are Glarean's old and new numbering). "
           "Set on the white keys, the two sources attach four names (Dorian, Phrygian, Lydian, Mixolydian) to different arrangements. Aeolian and Ionian were attached to A and C in Glarean's table, and 'Locrian', today the name of the mode on B, was for Cleonides another name for the species starting on A.")
MODE_SRC = ("Cleonides, <i>Harmonic Introduction</i>, sections 9–10, tr. O. Strunk, <i>Source Readings in Music History</i> (New York: Norton, 1950), pp. 34–46; "
            "H. Glareanus, <i>Dodecachordon</i> (Basel: Henricus Petri, 1547), title-page table; German tr. P. Bohn, <i>Glareani Dodecachordon</i>, Publikation älterer praktischer und theoretischer Musikwerke 16 (Leipzig: Breitkopf &amp; Härtel, 1888), pp. 49, 65 "
            "(<a href='https://archive.org/details/bub_gb_lpX2AAAAMAAJ'>Internet Archive</a>). Korean mode names: Ministry of Education, <i>Pyeonsu jaryo II</i> for textbooks under the 2022 revised curriculum (2023), music terms, pp. 329–345. Cents are computed from the definitions of the tunings.")

MODE_JS = """<script>(function(){var ac=null,TUN=__TUN__,cur='et';function ctx(){if(!ac){ac=new (window.AudioContext||window.webkitAudioContext)()}return ac}
function tone(f,t,d){var a=ctx(),o=a.createOscillator(),g=a.createGain();o.type='triangle';o.frequency.value=f;g.gain.setValueAtTime(0,t);g.gain.linearRampToValueAtTime(.22,t+.02);g.gain.exponentialRampToValueAtTime(.001,t+d);o.connect(g);g.connect(a.destination);o.start(t);o.stop(t+d+.05)}
function wc(i){var T=TUN[cur];return T[i%7]+1200*Math.floor(i/7)}
function seq(c,m){return m==='updown'?c.concat(c.slice(0,-1).reverse()):c}
function run(lists){var a=ctx(),t=a.currentTime+.05;lists.forEach(function(c){c.forEach(function(x){tone(261.63*Math.pow(2,x/1200),t,.5);t+=.42});t+=.5})}
document.querySelectorAll('.mode button[data-w]').forEach(function(b){b.addEventListener('click',function(){var w=JSON.parse(b.getAttribute('data-w')).map(wc);run([seq(w,b.getAttribute('data-m'))])})});
document.querySelectorAll('.mode button[data-c]').forEach(function(b){b.addEventListener('click',function(){var c=JSON.parse(b.getAttribute('data-c')),p=b.getAttribute('data-p');run(p?[JSON.parse(p),c]:[seq(c,b.getAttribute('data-m'))])})});
document.querySelectorAll('button[data-tun]').forEach(function(b){b.addEventListener('click',function(){cur=b.getAttribute('data-tun');document.querySelectorAll('button[data-tun]').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false')})})})})();</script>"""
MODE_CSS = (".mode{border-top:1px solid var(--line);padding:.5rem 0 .3rem}.mode h3{margin:0;font-size:.95rem}.mode .btns{display:flex;gap:.4rem;flex-wrap:wrap;margin:.2rem 0}"
            ".mode button,.tunsel button{border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:999px;padding:.15rem .7rem;font-size:.82rem;cursor:pointer}"
            ".tunsel{display:flex;gap:.4rem;flex-wrap:wrap;align-items:center;margin:.4rem 0}.tunsel button[aria-pressed=true]{border-color:var(--g1);background:color-mix(in srgb,var(--g1) 18%,var(--card))}")


def modes_section(k: bool) -> str:
    b = ["<h2>" + ("4. 선법 — 같은 일곱 음, 다른 시작" if k else "4. Modes — the same seven notes, a different start") + "</h2>",
         f"<p>{MODE_INTRO_KO if k else MODE_INTRO_EN}</p><p>{TUN_KO if k else TUN_EN}</p>",
         "<div class='tunsel'><span>" + ("조율:" if k else "Tuning:") + "</span>"
         + "".join(f"<button type='button' data-tun='{t}' aria-pressed='{'true' if t == 'et' else 'false'}'>{TUN_LABEL[t][0 if k else 1]}</button>" for t in TUNINGS) + "</div>"]
    for s, mid, ko, en in MODES:
        steps = "".join(("반" if k else "S") if is_semitone(i) else ("온" if k else "T") for i in range(s, s + 7))
        w = esc(json.dumps(list(range(s, s + 8))))
        b.append(f"<div class='mode' id='mode-{mid}'><h3>{esc(ko if k else en)} — {WK[s]}{'에서 시작' if k else ' to ' + WK[s]}"
                 f"<span class='meta'> · {steps}</span></h3>{keyboard(s, k)}"
                 f"<div class='btns'><button type='button' data-w='{w}' data-m='up'>▶ {'올라가기' if k else 'Up'}</button>"
                 f"<button type='button' data-w='{w}' data-m='updown'>▶ {'올라갔다 내려오기' if k else 'Up and down'}</button></div></div>")
    b.append("<h3 style='margin-top:1rem'>" + ("같은 으뜸음 D 위의 일곱 선법" if k else "The seven modes on one final, D") + f"</h3><p>{ONE_KO if k else ONE_EN}</p>")
    prev = None
    for n, s in enumerate(FIFTHS_ORDER):
        _, mid, ko, en = MODES[s]
        cents = mode_cents(s)
        changed = None if prev is None else next(j for j in range(8) if cents[j] != prev[j])
        absc = esc(json.dumps([v + 200 for v in cents]))
        pair = f"<button type='button' data-c='{absc}' data-p='{esc(json.dumps([v + 200 for v in prev]))}'>▶ {'위 줄과 이어서' if k else 'After the row above'}</button>" if prev else ""
        lowered = "" if changed is None else (f" · {changed + 1}음을 반음 내림" if k else f" · degree {changed + 1} lowered a semitone")
        b.append(f"<div class='mode'><h3>D {esc(ko if k else en)}<span class='meta'>{lowered}</span></h3>{ruler_changed(cents, changed)}"
                 f"<div class='btns'><button type='button' data-c='{absc}' data-m='updown'>▶ {'올라갔다 내려오기' if k else 'Up and down'}</button>{pair}</div></div>")
        prev = cents
    b.append("<h3 style='margin-top:1rem'>" + ("이름의 역사" if k else "Where the names came from") + f"</h3><p>{HIST_KO if k else HIST_EN}</p>{names_map(k)}"
             + "<p class='src'>" + ("같은 색 선은 같은 이름이다. 행은 그 종·선법의 옥타브 배열이 시작하는 흰 건반이다(글라레안의 정격에서는 그 음이 끝음이다)." if k else "Lines of one color join the same name. Each row is the white key on which the octave arrangement of the species or mode starts (for Glarean's authentic modes this note is the final).") + "</p>"
             + "<div class='mode'><div class='btns'>"
             + f"<button type='button' data-w='{esc(json.dumps(list(range(2, 10))))}' data-m='updown'>▶ {'클레오니데스의 도리아 (E–E)' if k else 'Cleonides’ Dorian (E–E)'}</button>"
             + f"<button type='button' data-w='{esc(json.dumps(list(range(1, 9))))}' data-m='updown'>▶ {'글라레안의 도리우스 (D–D)' if k else 'Glarean’s Dorius (D–D)'}</button></div></div>"
             + f"<p>{GLAR_KO if k else GLAR_EN}</p><p class='src'>{MODE_SRC}</p>")
    b.append(MODE_JS.replace("__TUN__", json.dumps(TUNINGS)))
    return "".join(b)


IN2_KO = ("22 슈루티에 비율을 붙인 근대 체계의 출처로는 데발(1910)과 클레먼츠(1913)를 실었다. 클레먼츠의 설명에 따르면 데발은 줄 두 개를 같은 높이로 맞춘 디아코드에서 한 줄의 줄받이를 움직여 가수가 부른 음에 맞추고, 눈금에서 사(Sa)에 대한 진동수 비를 계산했다(6~7쪽). 클레먼츠는 그 결과를 사 = 240으로 놓은 진동수 표로 실었고(7~8쪽), 대부분의 음에서 슈루티 둘이 순정 반음, 셋이 단온음(10/9), 넷이 장온음(9/8)이 된다고 요약했다. "
          "여기에는 클레먼츠 표에서 번호가 붙은 슈루티 1~22를 그렸다. 데발 1910의 표 D와는 두 곳이 다르다. 데발은 마 아티코말 315(21/16)를 넣고 마 카이시크 324(27/20)를 넣지 않았으며, 높은 니를 455⅝(243/128)로 적었다. 클레먼츠는 455 1/9(256/135)이다. 21/20, 63/40 같은 7의 비도 들어 있다. 번호 없이 따로 적힌 두 음(마 아티코말 315 = 21/16, 니 아티코말 420 = 7/4)은 그리지 않았다. Serrà 외(2011)가 견준 22 슈루티는 다른 2차 문헌에서 가져온 것이고, 이 표와 같은 체계인지는 확인하지 못했다. "
          "실제 연주로는 벨(1988)이 라가 토디의 녹음 여섯 계열에서 음마다 잰 위치를 실었다. 평균과 표준편차(모집단)는 엮은이가 여섯 계열로 다시 계산했다. 벨 자신의 평균표는 하모니움 조율 실험 두 건까지 넣은 것이다. 레♭·미♭·라♭은 평균율보다 낮고 파#·시는 높으며, 가장 흩어진 음은 파#다(593~625센트). 라♭은 낮은 옥타브와 가운데 옥타브에서 따로 쟀는데, 가운데 옥타브 쪽이 802~810센트로 더 높다. 토디의 미♭(가♭)을 두고는 말이 갈렸다. 자이라즈보이(1971)는 이 음이 흔히 「매우 낮다」고 말해진다고 하면서, 고스와미(1960)는 사–가♭을 315센트로, 다니엘루(1954)는 275센트에 해당하는 값으로 주었다고 적었다(167쪽 주 2). 벨이 잰 여섯 계열의 미♭은 288~303센트였다. 표 머리의 「sib」는 본문의 선법(do réb mib fa# sol lab si)과 맞지 않아 si로 읽었다. 만수르 줄의 1095는 가운데 옥타브 라♭ 칸에 찍혀 있으나 si 값으로 읽었다(벨의 평균 1107이 이 값을 si에 넣어 계산되어 있다).")
IN2_EN = ("For the modern system that gives the 22 śrutis ratios, the sources shown are Deval (1910) and Clements (1913). As Clements describes it, Deval tuned the two wires of a diachord to the same pitch, moved the fret of one to the note a singer sang, and computed its vibration ratio to sa from the scale (pp. 6–7). Clements printed the results as vibration numbers with sa = 240 (pp. 7–8) and summed them up for most notes as two śrutis making a just semitone, three a minor tone (10/9) and four a major tone (9/8). "
          "The śrutis numbered 1–22 in Clements's table are drawn here. Deval's Table D (1910) differs in two places: it includes ma atikomal 315 (21/16) but not ma kaishik 324 (27/20), and gives the high ni as 455⅝ (243/128) where Clements has 455 1/9 (256/135). Clements's śrutis include septimal ratios such as 21/20 and 63/40. Two notes listed apart without numbers (ma atikomal 315 = 21/16, ni atikomal 420 = 7/4) are not drawn. The 22 śrutis compared by Serrà et al. (2011) were taken from other secondary sources; whether they form the same system as this table was not checked. "
          "Performance is shown by Bel's (1988) measurements of rāg Toḍī: the position of each note in six recorded performances. The mean and standard deviation (population) were recomputed by the editor over the six; Bel's own table of means also includes two harmonium-tuning experiments. Re♭, mi♭ and la♭ lie below equal temperament and fa♯ and si above; fa♯ is the most scattered (593–625 cents). La♭ was measured separately in the lower and middle octaves, the middle-octave value being higher (802–810 cents). Accounts of Toḍī's mi♭ (ga♭) disagreed. Jairazbhoy (1971) notes that it is generally said to be very flat, and that Goswami (1960) gave the minor third sa–ga♭ as 315 cents while Daniélou (1954) gave a value equivalent to 275 cents (p. 167, n. 2). In Bel's six performances mi♭ lay at 288–303 cents. The column head 'sib' does not match the mode in the text (do réb mib fa# sol lab si) and is read as si. Mansur's 1095 is printed in the middle-octave la♭ column but read as si (Bel's mean, 1107, counts it there).")
GAMAKA_KO = ("벨의 토디 값은 선율선에서 머무는 부분만 골라 평균한 음 위치다. 0.1초·0.4초·0.2초 창으로 불규칙한 곡선, 높이 80센트 띠를 벗어나는 구간, 기울기가 큰 구간을 걸러 냈다(14쪽). 벨은 파#가 선율 움직임 속에서 겨우 암시될 뿐이라 위치를 잡기 매우 어렵다고 적었다(15쪽). "
             "라가의 음이 고정된 점이 아니라는 것은 카르나틱 노래의 측정에서도 보인다. 가수 19명의 녹음을 잰 비라라가반 외(2018)에 따르면, 한 음높이에 머무는 음의 정밀도는 길이가 길수록 좋아져 0.5초를 넘으면 약 10센트에 머물렀다. 가마카(꾸밈 움직임)에서 음높이 곡선이 방향을 바꾸는 점은 오차의 표준편차가 약 60센트였다. 이 두 값은 카르나틱 음악에서 잰 음별 오차라서, 힌두스타니 토디 행의 연주자 사이 표준편차와 바로 견줄 수 없다. 같은 스바라가 라가마다 다르게 불린다는 것은 코두리 외(2014)가 보였다. 젊은 전문 가수 5명이 드론만 두고 부른 바르남 28곡(라가 7개)에서 스바라마다 음높이 분포를 그렸다. 가(Ga)는 베가다에서 약 400센트의 날카로운 봉우리 하나였다. 모하남에서는 약 400센트와 700센트에 봉우리가 있고 그 사이가 이어졌으며, 아보기에서는 약 200~500센트에 퍼져 200·500센트 부근(리와 마의 자리)에 봉우리가 섰다. 슈리에서는 가의 봉우리가 리의 자리(약 200센트) 쪽으로 번졌다(투고판 4~7쪽, 그림 4). 이론 행의 점(클레먼츠 등)은 측정값이 아니다.")
GAMAKA_EN = ("Bel's Toḍī values are note positions averaged over the stable parts of the melodic line only: windows of 0.1, 0.4 and 0.2 seconds removed irregular curve segments, segments leaving an 80-cent band, and segments with a steep slope (p. 14). Bel wrote that fa♯ is very hard to locate, being barely suggested in the melodic movement (p. 15). "
             "That the notes of a rāga are not fixed points also shows in measurements of Carnatic singing. Measuring the recordings of nineteen singers, Viraraghavan et al. (2018) found that the precision of notes held at one pitch improves with duration and settles at about 10 cents beyond 0.5 seconds, while the points where the pitch curve turns within a gamaka (ornamental movement) have errors with a standard deviation of about 60 cents. These are per-note errors measured in Carnatic music, so they cannot be compared directly with the spread between performers in the Hindustani Toḍī row. That one svara is sung differently in different rāgas was shown by Koduri et al. (2014), who drew the pitch distribution of each svara in 28 varṇams in seven rāgas sung by five young professional singers with only the drone. Ga in Bēgaḍa was one sharp peak at about 400 cents; in Mōhanaṁ there were peaks at about 400 and 700 cents with a continuum between them; in Ābhōgi it spread over about 200–500 cents with peaks near 200 and 500 (the places of ri and ma); in Śrī its peak was smeared towards ri at about 200 cents (preprint, pp. 4–7, Fig. 4). The dots of the theory rows (Clements and others) are not measurements.")


# 1.15 — Jairazbhoy & Stone 1963, BSOAS 26(1): 123–124. Rag Yaman. Frequencies (c.p.s.) and printed cents.
# (performer, instrument ko, instrument en, film marking, sa_hz, re_hz or None, ga_hz or range, sa-re, re-ga, sa-ga printed)
YAMAN = [
    ("Pannalal Ghosh", "플루트", "flute", "1-1-A (사·sa) / 1-1-B (가·ga)", 314.4, None, 402.6, None, None, "429"),
    ("Pannalal Ghosh", "플루트", "flute", "3-4-B (사·sa) / 3-4-A (레·re, 가·ga)", 325.5, 371.2, 416.0, 228, 197, "425"),
    ("Pannalal Ghosh", "플루트", "flute", "4-6-A", 325.5, 372.5, 413.0, 234, 178, "412"),
    ("Pannalal Ghosh", "플루트", "flute", "6-1 (사·sa) / 6-2-A (가·ga)", 314.3, None, "399.2–403.4", None, None, "414–433"),
    ("Pannalal Ghosh", "플루트", "flute", "6-2-C", 314.3, None, 405.0, None, None, "439"),
    ("Pannalal Ghosh", "플루트", "flute", "6-2-E", 314.3, None, 402.4, None, None, "428"),
    ("Bundu Khan", "사랑기", "sārangī", "3-2-C", 288.3, 324.0, 365.1, 202, 207, "409"),
    ("Bundu Khan", "사랑기", "sārangī", "5-3-A / -B / -C (사·레·가)", 296.8, 330.6, 370.0, 187, 195, "382"),
    ("Umrao Khan", "노래", "voice", "2-2-A", 261.6, None, 327.6, None, None, "389"),
    ("Umrao Khan", "노래", "voice", "3-3-A", 258.0, 284.8, 322.8, 171, 216, "387"),
    ("Umrao Khan", "노래", "voice", "4-3-B (가·ga만 표시)", 266.5, 296.0, 331.0, 182, 193, "375"),
    ("Umrao Khan", "노래", "voice", "5-2", 269.6, 299.0, 334.9, 180, 196, "376"),
    ("Ravi Shankar", "시타르", "sitār", "2-3-A (사·sa) / 2-3-B (가·ga)", 269.0, None, "337.0–339.0", None, None, "390–400"),
    ("Ravi Shankar", "시타르", "sitār", "4-4", 270.0, 305.2, 338.5, 212, 180, "392"),
    ("Ravi Shankar", "시타르", "sitār", "5-1", 270.5, 307.7, 341.2, 223, 180, "403"),
    ("Gangoobai Hangal", "노래", "voice", "1-2-A", 205.8, None, 260.0, None, None, "405"),
    ("W. S. Deshpande", "노래", "voice", "3-1-A / -B / -C (사·레·가)", 283.5, 317.8, 356.0, 197, 197, "394"),
]
YAMAN_KO = ("자이라즈보이와 스톤(1963)은 라가 야만(야만 칼리안)을 연주자 여섯이 연주한 녹음에서 사·레·가의 음을 골라 오실로스코프로 찍고 진동수를 셌다(119~124쪽). 음마다 가장 안정된 부분을 1/10초 단위로 나누어 보고 0.5초 이상에 걸쳐 평균했다(124쪽). 저자들은 어느 부분이 안정된지 고르는 데 분석자의 해석이 크게 개입한다고 밝혔다(124~125쪽). 사–가 장3도는 판날랄 고시의 플루트에서 412~439센트, 움라오 칸의 노래에서 375~389센트였다. 저자들은 가장 큰 차이를 고시의 439센트와 움라오 칸의 375센트 사이의 64센트로 들고, 그래도 선율의 흐름으로 보아 둘 다 같은 라가라고 했다(130쪽). 고시와 라비 샹카르는 사–레를 레–가보다 넓게, 분두 칸과 그 아들 움라오 칸은 좁게 연주하는 것으로 보였다. 결론은 평균율의 위아래로 아마 25~30센트 안쪽이면 받아들여질 수 있고, 22 슈루티든 다른 정밀한 음률이든 북인도 고전음악에 적용하는 것은 의미가 없어 보인다는 것이었다(131쪽). 다만 저자들도 이것이 한 라가의 음정 두 개만 본 결과라고 밝혔다(131쪽 주 1). "
            "아래 점 하나는 원표의 측정 묶음 하나에서 나온 사–가다. 막대 둘은 성격이 다르다. 고시(6-2-A)의 막대는 약 3초 동안 이어진 가 하나가 세게 불수록 399.2에서 403 Hz로 올라간 변화이고(126쪽), 샹카르(2-3)의 막대는 짧게 세 번 친 가의 차이로, 저자들은 너무 짧아 결정적이지 않다고 적었다(124쪽). 표의 센트는 원문에 찍힌 값이며, 찍힌 진동수로 다시 계산하면 1센트 안팎 다른 곳이 있다(예: 샹카르 5-1의 레–가 180은 178.9, 고시 6-2-A의 상한 433은 432.1 — 126쪽 본문도 약 432라고 적는다). 세로선은 순정 장3도(386)·평균율(400)·피타고라스 장3도(408)다.")
YAMAN_EN = ("Jairazbhoy and Stone (1963) took sa, re and ga from recordings of rāg Yaman (Yaman Kalyān) by six performers, filmed them on an oscilloscope and counted the frequencies (pp. 119–124). For each note they found the steadiest part by dividing the film into tenths of a second and averaged over half a second or more (p. 124); they add that choosing that part is very largely subjective (pp. 124–125). The major third sa–ga ranged from 412 to 439 cents in Pannalal Ghosh's flute and from 375 to 389 cents in Umrao Khan's singing. The authors give the largest difference as the 64 cents between Ghosh's 439 and Umrao Khan's 375, yet the melodic sequences show both to be playing the same rāga (p. 130). Ghosh and Ravi Shankar seemed to play sa–re wider than re–ga, Bundu Khan and his son Umrao Khan narrower. They concluded that any intonation within perhaps 25 or 30 cents on either side of equal temperament can be acceptable and that applying the 22 śrutis, or any system of exact intonation, to North Indian classical music seems pointless (p. 131), while noting that the result rests on two intervals in one rāga (p. 131, n. 1). "
            "Each dot below is the sa–ga of one measurement group in the original table. The two bars are of different kinds: Ghosh's (6-2-A) is one ga held for about three seconds that rose from 399.2 to 403 Hz as he blew harder (p. 126); Shankar's (2-3) is the spread of a ga plucked three times, too short, the authors say, to be conclusive (p. 124). The cents in the table are as printed; recomputed from the printed frequencies some differ by about a cent (e.g. Shankar 5-1 re–ga 180 gives 178.9, and the upper end 433 of Ghosh 6-2-A gives 432.1, which p. 126 itself gives as about 432). The vertical lines are the just major third (386), equal temperament (400) and the Pythagorean major third (408).")


def yaman_block(k):
    head = (["연주자", "악기", "기록 표시", "사(Hz)", "레(Hz)", "가(Hz)", "사–레", "레–가", "사–가(센트)"] if k else
            ["Performer", "Instrument", "Film marking", "sa (Hz)", "re (Hz)", "ga (Hz)", "sa–re", "re–ga", "sa–ga (cents)"])
    th = "".join(f"<th{'' if i < 3 else chr(32) + 'class=' + chr(39) + 'num' + chr(39)}>{h}</th>" for i, h in enumerate(head))
    def mark(f):
        pairs = (("사·sa", "사", "sa"), ("레·re", "레", "re"), ("가·ga", "가", "ga"), ("사·레·가", "사·레·가", "sa, re, ga"), ("만 표시", "만 표시", " only"))
        for src, ko_, en_ in pairs:
            f = f.replace(src, ko_ if k else en_)
        return f
    rows = "".join(f"<tr><td>{esc(n)}</td><td>{esc(a if k else e)}</td><td>{esc(mark(f))}</td>"
                   + "".join(f"<td class='num'>{'' if v is None else esc(v)}</td>" for v in (sa, re_, ga, sr, rg, sg)) + "</tr>"
                   for n, a, e, f, sa, re_, ga, sr, rg, sg in YAMAN)
    cap = ("라가 야만의 사·레·가 측정(자이라즈보이·스톤 1963, 123~124쪽). 센트는 원문에 찍힌 값(정수까지만 정확하다고 저자가 밝힘)"
           if k else "Rāg Yaman: measured sa, re, ga (Jairazbhoy & Stone 1963, pp. 123–124). Cents as printed (accurate to the nearest whole figure, the authors say)")
    # dot strip of sa-ga
    W, H, lo, hi = 900, 92, 360, 450
    X = lambda v: 20 + (v - lo) / (hi - lo) * (W - 40)  # noqa: E731
    o = [f'<svg viewBox="0 0 {W} {H}" role="img">']
    for ref, lab in ((386.3, "5/4"), (400, "12평균율" if k else "equal"), (407.8, "81/64")):
        o.append(f'<line x1="{X(ref):.1f}" x2="{X(ref):.1f}" y1="10" y2="62" stroke="var(--fg3)" stroke-dasharray="3 3"/>'
                 f'<text x="{X(ref):.1f}" y="88" text-anchor="middle">{ref:g} {lab}</text>')
    for v in range(lo, hi + 1, 10):
        o.append(f'<line x1="{X(v):.1f}" x2="{X(v):.1f}" y1="62" y2="67" stroke="var(--fg3)"/>' + (f'<text x="{X(v):.1f}" y="76" text-anchor="middle" style="font-size:10px">{v}</text>' if v % 20 == 0 else ""))
    perf = sorted({r[0] for r in YAMAN}, key=[r[0] for r in YAMAN].index)
    col = {n: f"var(--g{i + 1})" for i, n in enumerate(perf)}
    for n, _, _, _, _, _, _, _, _, sg in YAMAN:
        yy = 14 + perf.index(n) * 8
        if "–" in sg:
            a, b = (float(x) for x in sg.split("–"))
            o.append(f'<line x1="{X(a):.1f}" x2="{X(b):.1f}" y1="{yy}" y2="{yy}" stroke="{col[n]}" stroke-width="5" stroke-linecap="round"><title>{esc(n)}: {sg}</title></line>')
        else:
            o.append(f'<circle cx="{X(float(sg)):.1f}" cy="{yy}" r="4.5" fill="{col[n]}"><title>{esc(n)}: {sg}</title></circle>')
    o.append("</svg>")
    legend = " · ".join(f"<span style='color:{col[n]}'>●</span> {esc(n)}" for n in perf)
    btn = lambda c, t: f"<button type='button' data-c='{esc(json.dumps(c))}' data-m='up'>▶ {t}</button>"  # noqa: E731
    btns = ("<div class='scale'><div class='btns'>" + btn([0, 439.0], "고시 6-2-C: 사–가 439센트" if k else "Ghosh 6-2-C: sa–ga 439 cents")
            + btn([0, 375.0], "움라오 칸 4-3-B: 사–가 375센트" if k else "Umrao Khan 4-3-B: sa–ga 375 cents")
            + btn([0, 400.0], "평균율 400센트" if k else "Equal temperament, 400 cents") + "</div></div>")
    return (f"<h3 style='margin-top:1rem'>{'라가 야만 — 같은 라가, 다른 3도' if k else 'Rāg Yaman: one rāga, different thirds'}</h3><p>{YAMAN_KO if k else YAMAN_EN}</p>"
            + "".join(o) + f"<p class='src'>{legend}</p>" + btns
            + f"<div class='wrap'><table><caption>{cap}</caption><thead><tr>{th}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")


def todi_table(k):
    head = ["연주자" if k else "Performer", "악기" if k else "Instrument"] + ["레♭", "미♭", "파#", "솔", "라♭", "(라♭)", "시"]
    if not k:
        head[2:] = ["re♭", "mi♭", "fa♯", "sol", "la♭", "(la♭)", "si"]
    th = "".join(f"<th{'' if i < 2 else chr(32) + 'class=' + chr(39) + 'num' + chr(39)}>{h}</th>" for i, h in enumerate(head))
    rows = "".join(f"<tr><td>{esc(n)}</td><td>{esc(a if k else e)}</td>" + "".join(f"<td class='num'>{esc(v)}</td>" for v in pr) + "</tr>"
                   for (n, a, e, _, _), pr in zip(TODI, TODI_PRINTED))
    cap = ("라가 토디의 음 위치(센트, 사 = 0). 라♭은 낮은 옥타브, (라♭)은 가운데 옥타브. 아래 두 줄은 하모니움 조율 실험이다. 칸은 원문에 찍힌 그대로다(? 와 괄호 포함, 만수르 줄은 인쇄 위치 그대로 — 평균 계산에서는 1095를 시로 읽었다). 벨 1988, 15쪽"
           if k else "Rāg Toḍī, note positions (cents, sa = 0). la♭ lower octave, (la♭) middle octave. The last two rows are harmonium-tuning experiments. Cells are as printed, with ? and brackets (Mansur's row is left where it was printed; for the means 1095 is read as si). Bel 1988, p. 15")
    return f"<div class='wrap'><table><caption>{cap}</caption><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table></div>"


# ---- 1.16: regions and places -------------------------------------------------------------------------------
# Regions, not states: music belongs to communities, and no state borders are drawn. A row is put on the map only
# when its source names a city or a site; rows that name only a region, or no place, are listed beside the map.
REGIONS = [("europe", "유럽·지중해", "Europe and the Mediterranean", 60, 20), ("wasia", "서아시아·북아프리카", "West Asia and North Africa", 21, 46),
           ("sasia", "남아시아", "South Asia", 24, 82), ("seasia", "동남아시아", "Southeast Asia", 14, 101),
           ("easia", "동아시아", "East Asia", 40, 118), ("africa", "사하라 이남 아프리카", "Sub-Saharan Africa", 3, 22)]
REGION_OF = {"pyth": "europe", "arch_enh": "europe", "arch_chr": "europe", "arch_dia": "europe", "just": "europe", "mean": "europe",
             "werck": "europe", "vallotti": "europe",
             "lu12": "easia", "wuyin": "easia", "pyeongjo": "easia", "gyemyeon": "easia", "gy_lee1928": "easia", "gy_kim1931": "easia",
             "gy_kim1932": "easia", "gy_seong1960": "easia", "sj_kimbh": "easia", "sj_kimjp": "easia", "sj_seong": "easia", "sj_ham": "easia",
             "piri_sang_pyeongjo": "easia", "piri_sang_pyojung": "easia", "piri_sujecheon": "easia", "in_uehara": "easia", "yo_uehara": "easia",
             "koto_isawa": "easia", "koto_woman": "easia", "koto_master": "easia",
             "slendro": "seasia", "pelog": "seasia", "thai_et": "seasia", "thai_ranat": "seasia",
             "chopi_avg": "africa", "chopi": "africa", "ganda": "africa", "malinke": "africa",
             "shur_vaziri": "wasia", "shur_karimi": "wasia", "rast_aeu": "wasia", "rast_meas": "wasia", "rast_mushaqa": "wasia",
             "rast_cairo": "wasia", "bayati_cairo": "wasia",
             "sruti": "sasia", "sruti_clements": "sasia", "todi_bel": "sasia"}  # et12: no region
# City- or site-level places named in the row text or its source. Coordinates: Wikidata P625 (CC0), rounded to 0.001°.
PLACES = {
    "slendro": ("족자카르타·수라카르타", "Yogyakarta and Surakarta", [(-7.800, 110.391), (-7.567, 110.817)], "Q7568, Q4803"),
    "pelog": ("족자카르타·수라카르타", "Yogyakarta and Surakarta", [(-7.800, 110.391), (-7.567, 110.817)], "Q7568, Q4803"),
    "koto_woman": ("런던 나이츠브리지 일본촌 — 잰 곳", "Japanese Village, Knightsbridge, London (where measured)", [(51.507, -0.128)], "Q84"),
    "koto_master": ("런던 나이츠브리지 일본촌 — 잰 곳", "Japanese Village, Knightsbridge, London (where measured)", [(51.507, -0.128)], "Q84"),
    "chopi_avg": ("자발라 지구 (키시코 좌표로 표시)", "Zavala District (shown at Quissico)", [(-24.683, 34.667)], "Q166838"),
    "chopi": ("자발라 지구 (키시코 좌표로 표시)", "Zavala District (shown at Quissico)", [(-24.683, 34.667)], "Q166838"),
    "rast_mushaqa": ("다마스쿠스 — 무샤카", "Damascus (Mushāqa)", [(33.513, 36.292)], "Q3766"),
    "rast_cairo": ("카이로 — 1932 회의 녹음", "Cairo (1932 Congress recordings)", [(30.044, 31.236)], "Q85"),
    "bayati_cairo": ("카이로 — 1932 회의 녹음", "Cairo (1932 Congress recordings)", [(30.044, 31.236)], "Q85"),
}
AWAY = {"koto_woman", "koto_master"}  # measured outside the region the music belongs to
LABEL_AT = {"Q3766": (-14, -10, "end"), "Q85": (-14, 16, "end"), "Q84": (14, 16, "start")}  # place-label offsets (dx, dy, anchor); default right of the mark


def et_distance(cents):
    """Mean distance (cents) from the nearest 12-TET note, measured from the first listed note, over the ascending notes
    above it and below 1,150 cents (a rule of thumb that leaves out the octave; a narrow measured octave such as 1,141 stays in).
    Unweighted: every listed note counts once."""
    c0 = cents[0]
    xs = [v - c0 for v in cents[1:] if 0 < v - c0 < 1150]
    return round(sum(abs(v - round(v / 100) * 100) for v in xs) / len(xs), 1)


def places_frame() -> pd.DataFrame:
    rows = []
    for g, i, nko, nen, wko, wen, kind, cents, *_ in SCALES:
        reg = REGION_OF.get(i, "")
        pl = PLACES.get(i)
        level = "site" if pl else ("region" if reg else "none")
        rows.append({"id": i, "region": reg, "place_level": level, "place_ko": pl[0] if pl else "", "place_en": pl[1] if pl else "",
                     "coords": ";".join(f"{a:.3f},{o:.3f}" for a, o in pl[2]) if pl else "", "wikidata": pl[3] if pl else "",
                     "measured_away": i in AWAY, "kind": kind, "et_distance_cents": et_distance(cents)})
    return pd.DataFrame(rows)


def equal_earth(lat, lon):
    import math as m
    A1, A2, A3, A4 = 1.340264, -0.081106, 0.000893, 0.003796
    phi, lam = m.radians(lat), m.radians(lon)
    th = m.asin(m.sqrt(3) / 2 * m.sin(phi))
    x = 2 * m.sqrt(3) * lam * m.cos(th) / (3 * (9 * A4 * th ** 8 + 7 * A3 * th ** 6 + 3 * A2 * th ** 2 + A1))
    y = A4 * th ** 9 + A3 * th ** 7 + A2 * th ** 3 + A1 * th
    return x, y


LAND = D / "scales_land_equalearth.json"  # projected Natural Earth 1:110m land (public domain), built from data/raw/naturalearth/


def build_land():
    src = ROOT / "data/raw/naturalearth/ne_110m_land.geojson"
    gj = json.loads(src.read_text(encoding="utf-8"))
    rings = []
    for f in gj["features"]:
        geom = f["geometry"]
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        for poly in polys:
            ring = poly[0]
            if max(pt[1] for pt in ring) < -58:  # Antarctica left out
                continue
            rings.append([[round(c, 4) for c in equal_earth(max(pt[1], -58), pt[0])] for pt in ring])
    LAND.write_text(json.dumps({"source": "Natural Earth 1:110m land (public domain), Equal Earth projection, unit sphere", "rings": rings}), encoding="utf-8")


MAP_W, MAP_H = 900, 400


def map_xy(lat, lon):
    x, y = equal_earth(lat, lon)
    X0, X1 = equal_earth(0, -180)[0], equal_earth(0, 180)[0]
    Y1, Y0 = equal_earth(80, 0)[1], equal_earth(-58, 0)[1]
    return 10 + (x - X0) / (X1 - X0) * (MAP_W - 20), 10 + (Y1 - y) / (Y1 - Y0) * (MAP_H - 20)


def tone(d):
    """Sequential color for an et_distance of 0-50 cents (one hue, light to dark)."""
    pct = 25 + min(d, 50) / 50 * 75
    return f"color-mix(in srgb,var(--g5) {pct:.0f}%,var(--card))"


def region_overview(k):
    pf = places_frame()
    names = {r[0]: (r[1] if k else r[2]) for r in REGIONS}
    nm = {r[1]: (r[2] if k else r[3]) for r in SCALES}
    land = json.loads(LAND.read_text(encoding="utf-8"))["rings"]
    X0, X1 = equal_earth(0, -180)[0], equal_earth(0, 180)[0]
    Y1, Y0 = equal_earth(80, 0)[1], equal_earth(-58, 0)[1]
    px = lambda x, y: (10 + (x - X0) / (X1 - X0) * (MAP_W - 20), 10 + (Y1 - y) / (Y1 - Y0) * (MAP_H - 20))  # noqa: E731
    o = [f'<svg viewBox="0 0 {MAP_W} {MAP_H}" role="img" aria-label="{"국경선 없는 지도" if k else "Map without borders"}">']
    for ring in land:
        pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in (px(*q) for q in ring))
        o.append(f'<polygon points="{pts}" fill="var(--line)" fill-opacity=".55" stroke="none"/>')
    for code, ko, en, la, lo in REGIONS:  # region labels (no points)
        x, y = map_xy(la, lo)
        n_reg = int(((pf.region == code) & (pf.place_level == "region")).sum())
        o.append(f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="middle" style="font-style:italic;fill:var(--fg3)">{esc(ko if k else en)}</text>'
                 f'<text x="{x:.0f}" y="{y + 13:.0f}" text-anchor="middle" style="font-size:10px;fill:var(--fg3)">{("지도 밖 " + str(n_reg)) if k else (str(n_reg) + " off the map")}</text>')
    ea = next(r for r in REGIONS if r[0] == "easia")
    exy = map_xy(ea[3] - 3, ea[4])
    seen = {}
    count = pf[pf.place_level == "site"].coords.value_counts().to_dict()
    for r in pf[pf.place_level == "site"].itertuples():
        coords = [tuple(map(float, c.split(","))) for c in r.coords.split(";")]
        key = r.coords
        j = seen.get(key, 0)
        seen[key] = j + 1
        x0, y0 = map_xy(*coords[0])
        for la, lo in (coords[1:] if j == 0 else []):
            x1, y1 = map_xy(la, lo)
            o.append(f'<circle cx="{x1:.1f}" cy="{y1:.1f}" r="2.5" fill="none" stroke="var(--fg3)"/>')
        if r.measured_away and j == 0:
            o.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{exy[0]:.1f}" y2="{exy[1]:.1f}" stroke="var(--fg3)" stroke-dasharray="4 4" stroke-opacity=".7"/>')
        cx = x0 + (j - (count[key] - 1) / 2) * 9  # side by side when one place holds several rows
        shape = (f'<circle cx="{cx:.1f}" cy="{y0:.1f}" r="5.5" fill="{tone(r.et_distance_cents)}" stroke="var(--fg)" stroke-width="1"/>' if r.kind == "measured"
                 else f'<rect x="{cx - 5:.1f}" y="{y0 - 5:.1f}" width="10" height="10" fill="{tone(r.et_distance_cents)}" stroke="var(--fg)" stroke-width="1"/>')
        o.append(f'<a href="#scale-{r.id}"><title>{esc(nm[r.id])} — {esc(r.place_ko if k else r.place_en)} · {r.et_distance_cents:g}</title>{shape}</a>')
    for key in seen:  # one place label per place
        r = pf[pf.coords == key].iloc[0]
        x0, y0 = map_xy(*map(float, key.split(";")[0].split(",")))
        dx, dy, anc = LABEL_AT.get(r.wikidata, (14, 4, "start"))
        o.append(f'<text x="{x0 + dx:.0f}" y="{y0 + dy:.0f}" text-anchor="{anc}" style="font-size:11px">{esc(r.place_ko if k else r.place_en)}</text>')
    o.append("</svg>")
    # dot plot: et distance by region
    groups = [(c, names[c]) for c, *_ in REGIONS] + [("", "장소 없음" if k else "No place")]
    W, rh, L = 900, 30, 190
    H = 40 + rh * len(groups)
    Xd = lambda v: L + v / 50 * (W - L - 20)  # noqa: E731
    d = [f'<svg viewBox="0 0 {W} {H}" role="img">']
    for v in range(0, 51, 10):
        d.append(f'<line x1="{Xd(v):.1f}" x2="{Xd(v):.1f}" y1="14" y2="{H - 22}" stroke="var(--line)"/><text x="{Xd(v):.1f}" y="{H - 6}" text-anchor="middle">{v}</text>')
    d.append(f'<line x1="{Xd(25):.1f}" x2="{Xd(25):.1f}" y1="14" y2="{H - 22}" stroke="var(--fg3)" stroke-dasharray="4 3"/>'
             f'<text x="{Xd(25) + 4:.1f}" y="12" style="font-size:10px;fill:var(--fg3)">{"무작위 기댓값 25" if k else "random expectation 25"}</text>')
    for gi, (code, lab) in enumerate(groups):
        y = 30 + gi * rh
        d.append(f'<text x="{L - 10}" y="{y + 4}" text-anchor="end">{esc(lab)}</text>')
        sub = pf[pf.region == code].sort_values("et_distance_cents")
        last, stack = None, 0
        for r in sub.itertuples():
            stack = stack + 1 if last is not None and abs(r.et_distance_cents - last) < 1.2 else 0
            last = r.et_distance_cents
            yy = y + (0, -8, 8, -16, 16)[stack % 5]
            x = Xd(r.et_distance_cents)
            mark = (f'<circle cx="{x:.1f}" cy="{yy}" r="4.5" fill="var(--g5)" fill-opacity=".85"/>' if r.kind == "measured"
                    else f'<circle cx="{x:.1f}" cy="{yy}" r="4" fill="var(--card)" stroke="var(--g5)" stroke-width="1.6"/>')
            d.append(f'<a href="#scale-{r.id}"><title>{esc(nm[r.id])} · {r.et_distance_cents:g}</title>{mark}</a>')
    d.append("</svg>")
    off_reg = "".join(f"<li><b>{esc(names[c])}</b>: " + ", ".join(f"<a href='#scale-{i}'>{esc(nm[i])}</a>" for i in pf[(pf.region == c) & (pf.place_level == 'region')].id) + "</li>"
                      for c, *_ in REGIONS if ((pf.region == c) & (pf.place_level == "region")).any())
    off_none = ", ".join(f"<a href='#scale-{i}'>{esc(nm[i])}</a>" for i in pf[pf.place_level == "none"].id)
    med = pf.groupby("region").et_distance_cents.median()
    intro = (("지도에는 국경선을 그리지 않았다. 음악은 나라보다 그것을 연주하고 듣는 지역 공동체의 것이라는 쪽에 서서, 음계를 여섯 문화권(유럽·지중해, 서아시아·북아프리카, 남아시아, 동남아시아, 동아시아, 사하라 이남 아프리카)으로 묶었다. "
              "점은 줄의 서술이 도시나 장소를 밝힌 경우만 찍었다 — 잰 곳이거나(카이로·족자카르타·수라카르타·자발라 지구·런던), 이론을 정리한 사람의 도시다(다마스쿠스의 무샤카). 도시 수준 표시이고 좌표는 위키데이터(CC0)다. 한 곳에 줄이 여럿이면 표시를 옆으로 나란히 놓았다. 족자카르타와 수라카르타는 이 축척에서 거의 겹쳐 이름표 하나로 묶었다(작은 고리가 수라카르타). 동그라미는 실측, 네모는 이론값이다. 도시·장소를 특정하지 못한 줄은 지도 아래 목록에 모았다. 문화권 배정은 엮은이의 판단이고(예: 터키 라스트를 서아시아·북아프리카에), 지도 위 문화권 이름표의 자리는 편의상 정한 것이다. "
              "고토의 두 줄은 1885년 런던에서 쟀다. 음악이 속한 곳과 잰 곳이 달라서 점선으로 동아시아에 이었다. 점을 누르면 그 음계로 간다.")
             if k else
             ("The map draws no state borders. Taking music to belong to the communities that play and hear it rather than to states, the scales are grouped into six cultural regions (Europe and the Mediterranean, West Asia and North Africa, South Asia, Southeast Asia, East Asia, Sub-Saharan Africa). "
              "A row is plotted only when its description names a city or a site — where it was measured (Cairo, Yogyakarta, Surakarta, the Zavala District, London) or the city of the person who set out the theory (Mushāqa of Damascus). Placement is city-level, with coordinates from Wikidata (CC0); where one place holds several rows, the marks sit side by side. Yogyakarta and Surakarta nearly coincide at this scale and share one label (the small ring is Surakarta). Circles are measurements, squares theory. Rows for which no city or site can be named are listed below the map. The cultural regions were assigned by the editor (for instance Turkish Rast to West Asia and North Africa), and the region labels on the map are placed for convenience. "
              "The two koto rows were measured in London in 1885; since the music belongs elsewhere, a dashed line joins them to East Asia. Click a mark to go to its scale."))
    metric = (("색과 아래 그림의 가로축은 평균율에서 떨어진 정도다. 각 음계의 첫 음을 0으로 놓고, 그 위 1150센트 아래의 음(올라갈 때의 음만, 옥타브를 빼려는 어림 규칙이라 1141센트처럼 좁게 잰 옥타브는 들어간다)마다 가장 가까운 12평균율 음과의 차이(센트)를 가중치 없이 평균했다. 0이면 평균율과 같고, 음을 아무렇게나 놓으면 평균 25센트가 된다(0~50센트 사이 균등분포의 평균). "
               f"지역별 중앙값은 유럽·지중해 {med['europe']:.1f}, 서아시아·북아프리카 {med['wasia']:.1f}, 남아시아 {med['sasia']:.1f}, 동남아시아 {med['seasia']:.1f}, 동아시아 {med['easia']:.1f}, 사하라 이남 아프리카 {med['africa']:.1f}센트다. "
               "이 값은 음계의 좋고 나쁨이 아니라 평균율이라는 한 자와의 거리일 뿐이다. 이론값과 실측이 섞여 있고(속 빈 점이 이론), 지역마다 실린 음계의 수와 종류가 달라 지역을 서로 견주는 근거로 쓰기 어렵다. 첫 음을 다른 음으로 잡으면 값이 달라지고, 첫 음 말고 평균에 들어가는 음이 둘뿐인 줄(산조의 꺾는 음)도 있다.")
              if k else
              ("The color and the horizontal axis below show distance from equal temperament: with each scale's first note at 0, the unweighted mean difference (cents) from the nearest equal-tempered note of each ascending note above it and below 1,150 cents (a rule of thumb to leave out the octave, so a narrowly measured octave such as 1,141 stays in). 0 is equal temperament; notes placed at random would average 25 cents (the mean of a uniform distribution over 0–50). "
               f"Regional medians are {med['europe']:.1f} (Europe and the Mediterranean), {med['wasia']:.1f} (West Asia and North Africa), {med['sasia']:.1f} (South Asia), {med['seasia']:.1f} (Southeast Asia), {med['easia']:.1f} (East Asia) and {med['africa']:.1f} cents (Sub-Saharan Africa). "
               "The value says nothing about a scale's merit, only its distance from one yardstick, equal temperament. Theory and measurement are mixed (hollow dots are theory), and the number and kind of scales differ from region to region, so it is a poor basis for comparing regions. Taking another note as the first changes the value, and in some rows only two notes besides the first enter the mean (the bent notes of sanjo)."))
    return (f"<h2>{'지역으로 보기' if k else 'By region'}</h2><p>{intro}</p>" + "".join(o)
            + "<p class='src'>" + ("바탕: Natural Earth 1:110m 육지(퍼블릭 도메인), 이퀄 어스 도법, 남위 58도 아래는 뺐다. 색: 평균율과의 거리 — 강조색이 짙을수록 크다(0 → 50센트)." if k else
                                   "Base: Natural Earth 1:110m land (public domain), Equal Earth projection, south of 58°S left out. Color: distance from equal temperament — the stronger the accent color, the larger (0 → 50 cents).") + "</p>"
            + f"<p>{metric}</p>" + "".join(d)
            + f"<h3>{'도시·장소를 특정하지 못한 줄 (문화권별)' if k else 'Rows with no city or site named (by region)'}</h3><ul>{off_reg}</ul>"
            + f"<h3>{'장소 없는 이론' if k else 'Theory with no place'}</h3><p>{off_none}</p>")


def lim_table(k):
    head = ("유파", "계면조", "우조", "평조", "경드름", "강산제") if k else ("School", "gyemyeonjo", "ujo", "pyeongjo", "gyeongdeureum", "gangsanje")
    rows = "".join(f"<tr><td>{a if k else e}</td>" + "".join(f"<td class='num'>{v}</td>" for v in vals) + "</tr>" for a, e, *vals in LIM)
    th = "".join(f"<th{'' if i == 0 else chr(32) + 'class=' + chr(39) + 'num' + chr(39)}>{h}</th>" for i, h in enumerate(head))
    cap = "징(c′)–땅(d′) 평균 음정(센트)" if k else "Mean interval jing (c′) – ttang (d′), cents"
    return f"<p>{LIM_KO if k else LIM_EN}</p><div class='wrap'><table><caption>{cap}</caption><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table></div>"


def render(lang: str) -> str:
    k = lang == "ko"
    df = pd.DataFrame(SCALES, columns=COLS)
    from history_pages import GCSS  # noqa: E402
    b = [f"<style>{GCSS}{CSS}{MODE_CSS}</style><div class='hero'><h1>{'음계와 조율' if k else 'Scales and tuning'}</h1><p class='lead'>"
         + ("한 옥타브(1200센트)를 어떻게 나누어 왔는지, 시대와 지역에 따라 견준다. 점 하나가 음 하나이고, 회색 눈금은 피아노의 12평균율(100센트 간격)이다. 단추를 누르면 브라우저가 그 자리에서 음을 합성해 들려준다."
            if k else "How the octave (1,200 cents) has been divided, compared across periods and regions. Each dot is a note; the grey ticks are piano equal temperament (100 cents apart). The buttons play the scale, synthesised by your browser on the spot.")
         + "</p></div>"]
    b.append("<p class='src'>" + ("모든 음계를 같은 기준음(가온 다, 261.63 Hz) 위에 옮겨 들려준다. 실제 악기의 음높이는 다르다. 「평균율과 번갈아」는 각 음 다음에 가장 가까운 12평균율 음을 들려준다. 소리는 삼각파 합성음이라 악기 음색이 아니다. 「이론」은 비율이나 규칙으로 정한 값, 「실측」은 악기나 연주를 잰 값이다. 속이 빈 점은 내려갈 때만 쓰는 음이고, 점선 고리는 원자료에 없는 옥타브(1200센트)를 재생을 위해 붙인 자리다."
                                 if k else "Every scale is played on the same reference, middle C (261.63 Hz); the instruments themselves sit at other pitches. 'Against equal temperament' follows each note with the nearest equal-tempered note. The sound is a synthesised triangle wave, not the instrument's timbre. 'Theory' marks values set by ratios or rules; 'measured' marks values taken from instruments or performances. A hollow dot is a note used only when descending; a dashed ring marks an octave (1,200 cents) that the source does not give and that is added only for playback.") + "</p>")
    b.append(region_overview(k))
    for g, (tko, ten) in GROUPS.items():
        b.append(f"<h2>{tko if k else ten}</h2>")
        if g == "east":
            b.append("<p>" + ("삼분손익은 율관 길이를 3분의 1씩 줄이고 늘려 음을 얻는 방법으로, 순정 5도를 쌓는 것과 같다. 12번째 음인 중려는 4/3(498센트)이 아니라 521.5센트에 놓인다. 5도 12개를 쌓으면 옥타브보다 피타고라스 쉼표(23.5센트)만큼 넘치기 때문이다. 한국 아악의 12율도 같은 계열이다. 유준희 외(2011)가 정리한 비율표에서 중려는 1.35다. 평조·계면조의 음 구성은 관례를 따랐고, 실제 연주에서 중려가 521센트 부근에 놓였는지는 이 값만으로는 알 수 없다."
                              if k else "Sanfen sunyi (三分損益) shortens and lengthens a pipe by a third in turn, which amounts to stacking pure fifths. The twelfth note, 仲呂, lands at 521.5 cents rather than 4/3 (498 cents), because twelve fifths overshoot the octave by the Pythagorean comma (23.5 cents). The twelve yul of Korean court music follow the same series; in the ratio table of Yoo et al. (2011), jungnyeo (仲呂) is 1.35. The note sets of pyeongjo and gyemyeonjo follow convention, and whether performers actually placed jungnyeo near 521 cents cannot be told from these values.") + "</p>")
            b.append("<p>" + (JP_KO if k else JP_EN) + "</p><p>" + (KOTO_KO if k else KOTO_EN) + "</p><p>" + (KR_KO if k else KR_EN) + "</p>" + lim_table(k))
        if g == "measured":
            b.append("<p>" + ("이론이 정한 음과 실제로 조율하거나 연주한 음은 다르다. 같은 곡조의 이론값과 실측값을 나란히 놓았다. 가믈란은 악기 세트 수십 개의 평균이고, 주황 막대는 ±1 표준편차(수록 세트 전체의 모집단 표준편차)다. 여기 실은 가믈란 평균과 라나트 엑 평균에서는 옥타브가 1200센트보다 넓다(1214~1217센트). 원자료에 옥타브 음이 없는 음계는 재생을 위해 1200센트를 붙였다."
                              if k else "The notes a theory prescribes and the notes actually tuned or sung differ. Theory and measurement for the same scale sit side by side. The gamelan rows average dozens of sets; the orange bars show ±1 standard deviation (population SD over the sets included). In the gamelan and ranat ek means shown here the octave is wider than 1,200 cents (1,214–1,217). Where the source gives no octave note, 1,200 cents is added for playback.") + "</p>")
            b.append("".join(f"<p>{x}</p>" for x in ((ME_KO, IN_KO, IN2_KO) if k else (ME_EN, IN_EN, IN2_EN))) + todi_table(k) + yaman_block(k) + f"<p>{GAMAKA_KO if k else GAMAKA_EN}</p><p>{CH_KO if k else CH_EN}</p>")
        for r in df[df.group == g].itertuples():
            add = not (r.cents[-1] > 1150 or r.id in OCTAVE_MEASURED)
            cents = list(r.cents) + ([1200.0] if add else [])
            sd = list(r.sd) + ([0] * (len(cents) - len(r.sd))) if r.sd else None
            kind = ("이론" if r.kind == "theory" else "실측") if k else r.kind
            n = f" · n = {int(r.n)}" if r.n and r.n > 1 else ""
            data = esc(json.dumps(cents))
            down = DOWN.get(r.id)
            dattr = f" data-d='{esc(json.dumps(down + [1200.0]))}'" if down else ""
            b.append(f"<div class='scale' id='scale-{r.id}'><h3>{esc(r.name_ko if k else r.name_en)}<span class='kind {r.kind}'>{kind}</span></h3>"
                     f"<div class='meta'>{esc(r.when_ko if k else r.when_en)}{n} · {esc(r.source)}</div>{ruler(cents, sd, down=down, added=1200.0 if add else None)}"
                     f"<div class='btns'><button type='button' data-c='{data}' data-m='up'>▶ {'올라가기' if k else 'Up'}</button>"
                     f"<button type='button' data-c='{data}' data-m='updown'{dattr}>▶ {'올라갔다 내려오기' if k else 'Up and down'}</button>"
                     f"<button type='button' data-c='{data}' data-m='compare'>▶ {'평균율과 번갈아' if k else 'Against equal temperament'}</button></div></div>")
        if g == "east":
            rows = "".join(f"<tr><td>{esc(a if k else e)}</td><td class='num'>{hz}</td></tr>" for a, e, hz in HZ)
            b.append(f"<h3 style='margin-top:1rem'>{'황종의 높이는 시대마다 달랐다' if k else 'The pitch of hwangjong changed over time'}</h3><p>"
                     + ("음계는 비율이고, 실제 음높이는 기준음 황종이 정한다. 국립고궁박물관·국립국악원 등에 남은 편경·특경의 경석 241매를 잰 연구는, 경석에 새긴 간지나 개수(改修) 시기가 같은 것끼리 묶어 황종의 높이를 거꾸로 추정했다. 간지는 60년마다 돌아오므로 정유년·갑자년은 제작 연도가 하나로 정해지지 않는다."
                        if k else "A scale is a set of ratios; the actual pitch is fixed by the reference note hwangjong (黃鍾). A study of 241 surviving stone-chime slabs (pyeongyeong and teukgyeong) in Korean collections grouped the stones by the cyclical year or the re-tuning date inscribed on them and estimated hwangjong from each group. A cyclical year recurs every 60 years, so the jeongyu and gapja groups do not fix a single year of manufacture.")
                     + f"</p><div class='wrap'><table><thead><tr><th>{'경석 묶음' if k else 'Stone group'}</th><th class='num'>{'황종 추정(Hz)' if k else 'hwangjong estimate (Hz)'}</th></tr></thead><tbody>{rows}</tbody></table></div>"
                     "<p class='src'>유준희·박정우·배대성 외, 「유물 편경의 음향 분석을 통한 아악 황종음고의 추정」, 『한국음향학회지』 30(8): 421–427, 2011.</p>")
    b.append(modes_section(k))
    b.append("<h2>" + ("5. 아직 넣지 않은 것" if k else "5. Not yet included") + "</h2><p>" + (NY_KO if k else NY_EN) + "</p>")
    b.append("<p class='src'>" + ("자료: " if k else "Data: ") + "McBride, Passmore & Tlusty (2023), 'Convergent evolution in a large cross-cultural database of musical scales', <i>PLoS ONE</i> 18(12): e0284851 — <a href='https://github.com/jomimc/DaMuSc'>DaMuSc</a> (CC BY 4.0); "
             "Garzoli (2015), 'The myth of equidistance in Thai tuning', <i>Analytical Approaches to World Music</i> 4(2); Bozkurt et al. (2009), <i>Journal of New Music Research</i> 38(1): 45–70; Shafiei (2021), arXiv:2108.01283; "
             "Smith (1847), 'A treatise on Arab music, chiefly from a work by Mikhâil Meshâkah, of Damascus', <i>Journal of the American Oriental Society</i> 1(3): 173–217; "
             "Bozkurt (2025), 'An open research dataset of the 1932 Cairo Congress of Arab Music', arXiv:2506.14503 — <a href='https://doi.org/10.5281/zenodo.15682346'>ORD-CC32</a> (CC BY-NC 4.0; the Rast and Bayati rows and scales_cairo1932.csv carry this license); "
             "Ghosh (tr., 1961), <i>The Nāṭyaśāstra</i>, vol. II (Asiatic Society, Calcutta); Serrà, Koduri, Miron & Serra (2011), ISMIR 2011: 157–162; Ramanathan (1981), 'Shruti according to ancient texts', <i>Journal of the Indian Musicological Society</i> 12(3): 31–37; K. B. Deval (1910), <i>The Hindu Musical Scale and the Twenty-two Shrutees</i> (Poona: Arya Bhushan Press); E. Clements (1913), <i>Introduction to the Study of Indian Music</i> (London: Longmans, Green; <a href='https://archive.org/details/cu31924018413900'>Internet Archive</a>); B. Bel (1988), 'Raga : approches conceptuelles et expérimentales', <i>Actes du colloque Structures musicales et assistance informatique</i>, Marseille (<a href='https://hal.science/hal-00008280'>HAL hal-00008280</a>); V. S. Viraraghavan, H. A. Murthy & R. Aravind (2018), 'Precision of sung notes in Carnatic music', ISMIR 2018: 499–505; G. K. Koduri, V. Ishwar, J. Serrà & X. Serra (2014), 'Intonation analysis of rāgas in Carnatic music', <i>Journal of New Music Research</i> 43(1): 72–93, <a href='https://doi.org/10.1080/09298215.2013.866145'>doi:10.1080/09298215.2013.866145</a> (read in the submitted version, <a href='https://repositori.upf.edu/items/7240fd78-c671-4ea0-9e1d-489141e481ca'>UPF repository</a>, which also lists H. Murthy as an author; page references on this page are to that version); N. A. Jairazbhoy (1971), <i>The Rāgs of North Indian Music: Their Structure and Evolution</i> (London: Faber and Faber); N. A. Jairazbhoy & A. W. Stone (1963), 'Intonation in present-day North Indian classical music', <i>Bulletin of the School of Oriental and African Studies</i> 26(1): 119–132, doi:10.1017/S0041977X00074309; "
             "上原六四郎 (Uehara 1895), 『俗楽旋律考』 (金港堂; <a href='https://dl.ndl.go.jp/pid/856052'>NDL Digital Collections</a>); "
             "Ellis (1885), 'On the musical scales of various nations', <i>Journal of the Society of Arts</i> 33: 485–527; Tracey (1958), 'Towards an assessment of African scales', <i>African Music</i> 2(1): 15–20; Tracey (1948), <i>Chopi Musicians: Their Music, Poetry, and Instruments</i> (London: Oxford University Press for the International African Institute); A. Tracey (2001), 'Mozambique', <i>Grove Music Online</i> (= <i>The New Grove Dictionary of Music and Musicians</i>, 2nd ed.), doi:10.1093/gmo/9781561592630.article.19268; Nam (1998), 'Pitch distributions in Korean court music: evidence consistent with tonal hierarchies', <i>Music Perception</i> 16(2): 243–247; "
             "고유동 (Ko Yudong 2021. 2.), 「가야금 경기민요 음률 분석: 이일선, 김죽파, 성금연의 연주를 중심으로」, 한양대학교 대학원 국악학과 음악학 석사학위논문 (CC BY-NC-ND 2.0 KR); 양수연 (Yang Suyeon 2013. 2.), 「가야금산조의 음고 및 음정분석연구」, 서울대학교 대학원 음악과 국악기악전공 음악학석사학위논문 (CC BY-NC-SA 2.0 KR); 임경미 (Lim Gyeongmi 2013. 8.), 「가야금산조의 조에 따른 음고 및 음정분석연구」, 서울대학교 대학원 음악과 국악기악전공 음악학석사학위논문 (CC BY-NC-ND 2.0 KR) — the gayageum rows give only the editor's transcription of their numbers and carry license CC-BY-NC-4.0; "
             + ("유준희 외(2011). 비율로 정의된 음률은 정의에서 계산했고 Scala 아카이브(Huygens-Fokker 재단)의 파일과 대조했다." if k else "Yoo et al. (2011). Ratio-defined tunings were computed from their definitions and checked against the Scala archive (Huygens-Fokker Foundation).")
             + "</p>" + JS)
    return "".join(b)


def build(lang, path, page_fn):
    path.write_text(page_fn(lang, "음계와 조율" if lang == "ko" else "Scales and tuning", render(lang),
                            desc="Scales and tuning compared across periods and regions", active="scales"), encoding="utf-8")


if __name__ == "__main__":
    frame().to_csv(D / "scales.csv", index=False, encoding="utf-8", lineterminator="\n")
    places_frame().to_csv(D / "scales_places.csv", index=False, encoding="utf-8", lineterminator="\n")
    if (ROOT / "data/raw/naturalearth/ne_110m_land.geojson").exists():
        build_land()
    print("wrote data/derived/scales.csv")
