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
SCALE_FILES = ["scales.csv", "scales_cairo1932.csv"]


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
IN_KO = '인도의 22 슈루티는 바라타의 『나티야샤스트라』에 나온다. 사드자 그라마의 일곱 음이 각각 슈루티 4·3·2·4·4·3·2개를 차지한다(28장 24~26절, Ghosh 영역 2권 8쪽). 원전은 슈루티의 개수만 말하고 크기는 말하지 않으므로, 여기서는 같은 크기로 놓고 그렸다. 아래의 실측 연구가 견준 22 슈루티는 이 그림이 아니라, 옥타브를 크기가 다른 22개로 나눈 근대의 비율 체계다. 오늘날의 노래를 잰 Serrà 외(2011)는 카르나틱 233곡과 힌두스타니 133곡의 음정 히스토그램을 순정률·평균율과 견주었다. 카르나틱은 순정률 쪽(상관 0.552 대 0.448), 힌두스타니는 평균율 쪽(0.723 대 0.641)에 더 가까웠다. 그 22 슈루티 체계에만 있는 일곱 위치에서 힌두스타니는 정점이 없었고, 카르나틱은 세 곳에 작은 기여가 있었을 뿐이다. 저자들은 22 슈루티를 뒷받침하는 강한 정량 증거가 없지만 배제할 수도 없다고 결론지었다.'
IN_EN = "The 22 śrutis come from Bharata's Nāṭyaśāstra: the seven notes of the ṣaḍja-grāma take 4, 3, 2, 4, 4, 3 and 2 śrutis (28.24–26; tr. Ghosh, vol. II, p. 8). The text gives the number of śrutis, not their size, so they are drawn here as equal. The 22 śrutis tested in the measurement study below are not this drawing but a modern ratio system that divides the octave into 22 unequal steps. Measuring present-day singing, Serrà et al. (2011) compared interval histograms of 233 Carnatic and 133 Hindustani recordings with just intonation and equal temperament. Carnatic singing was closer to just intonation (correlation 0.552 vs 0.448), Hindustani closer to equal temperament (0.723 vs 0.641). At the seven positions found only in that 22-śruti system, Hindustani showed no peaks and Carnatic only small contributions at three. The authors concluded that the 22 śrutis lack strong quantitative support but cannot be ruled out."
CH_KO = '모잠비크 초피의 팀빌라는 옥타브를 일곱 개의 거의 같은 음정으로 나눈다. 트레이시는 212~424진동을 4진동 간격으로 나눈 소리굽쇠 54개로 그동안 악기 수백 대를 쟀고, 음높이를 ±2진동 안에서 정할 수 있었다고 적었다(『초피 음악가들』, 1948, 122쪽). 그는 1940년부터 해마다 초피 마을을 찾았고, 책에 실은 음계 대부분을 1943년 9월 26일 키시코(Quissico)에서 연 회의 전에 기록해 두었다. 그 회의에서 악기 제작자와 악단 지휘자들은, 기준음 홈베의 높이는 저마다 달라도 모두 「일곱 음정이 모두 같은 고른 음계」를 지향한다고 말했다(123~124쪽). 자발라 지구 다섯 악단의 음정은 141~207센트에 걸쳐 있고(7평균율이면 171센트), 홈베는 252~276진동이었다(125쪽 도표 IV). 다섯 악단 평균의 주황 막대는 악단 사이의 표준편차다. 한 악기 행은 트레이시(1958)가 실은 값으로, 1948년 도표의 자발라 악단과 같다.'
CH_EN = "The Chopi timbila of Mozambique divides the octave into seven nearly equal steps. Over his fieldwork Tracey measured several hundred instruments with 54 tuning forks spanning 212–424 vibrations in steps of four, and wrote that he could fix a pitch to within two vibrations (Chopi Musicians, 1948, p. 122). He visited Chopi villages every year from 1940 and had noted most of the scales in the book before a meeting at Quissico on 26 September 1943, where instrument makers and orchestra leaders said that, whatever their differences over the pitch of the tonic Hombe, each was aiming at 'an even scale of seven intervals, all alike' (pp. 123–124). In five orchestras of the Zavala District the steps range from 141 to 207 cents (171 for seven equal steps), and Hombe lay at 252–276 vibrations (p. 125, Diagram IV). The orange bars on the five-orchestra mean show the spread between orchestras. The single-instrument row gives the values Tracey printed in 1958, the same as the Zavala orchestra in the 1948 diagram."
NY_KO = "다음은 원문을 열지 못했거나, 열었지만 음계로 옮길 수 없어 넣지 않았다. ① 1932 카이로 회의 기록집(<i>Recueil des travaux du Congrès de musique arabe qui s'est tenu au Caire en 1932</i>, Le Caire: Imprimerie nationale, 1934)과 데를랑제(R. d'Erlanger) 『아랍 음악(<i>La musique arabe</i>)』 5권(Paris: Geuthner, 1949)의 음계표 — 출판본을 보지 못했다. ② 모크타르·모샤라파, 「Modes in Modern Egyptian Music」, <i>Nature</i> 140: 548–549 (1937) — 본문을 보지 못했다. ③ Serrà 외(2011)가 견준 22 슈루티의 비율 체계 — 그 비율을 정한 문헌을 원문으로 확인하지 못했다. ④ 다른 국악기 실측 — 박수홍·옥승호·서인화·김소리·정환희, 「국악관악기 품질평가를 위한 음고특성분석」, 『한국소음진동공학회 2011년 춘계학술대회논문집』 302–307쪽은 국립국악원 연주자 세 사람이 시판 대금·소금·퉁소·단소를 분 음높이를 쟀으나, 음별 값이 그림에만 있고 비교 기준인 「평균율 기준음고」를 정의하지 않아 음계로 옮기지 않았다. Nam, 「Pitch Distributions in Korean Court Music」, <i>Music Perception</i> 16(2): 243–247 (1998)은 본문을 보지 못했다. "
NY_EN = "Left out because the original could not be opened, or was opened but could not be turned into a scale: (1) the scale tables of the Cairo Congress proceedings (<i>Recueil des travaux du Congrès de musique arabe qui s'est tenu au Caire en 1932</i>, Cairo: Imprimerie nationale, 1934) and of R. d'Erlanger, <i>La musique arabe</i>, vol. 5 (Paris: Geuthner, 1949) — the printed books not seen; (2) M. Mokhtar & A. M. Mosharrafa, 'Modes in Modern Egyptian Music', <i>Nature</i> 140: 548–549 (1937) — full text not seen; (3) the 22-śruti ratio system compared by Serrà et al. (2011) — the publication that fixes its ratios was not checked in the original; (4) further measurements of Korean instruments — S.-H. Park, S.-H. Ock, I.-H. Seo, S.-R. Kim & H.-H. Jeong, 'Frequency characteristics analysis for quality assessment on Korean traditional wind instruments', Proceedings of the Korean Society for Noise and Vibration Engineering, Spring 2011, pp. 302–307, measured commercial daegeum, sogeum, tungso and danso played by three National Gugak Center players, but the per-note values are only in charts and the equal-tempered reference pitch is not defined, so they are not drawn; U. Nam, 'Pitch Distributions in Korean Court Music', <i>Music Perception</i> 16(2): 243–247 (1998), full text not seen; "


KR_KO = '한국 악기를 직접 잰 값으로 가야금 연구 두 편을 실었다. 고유동(2021)은 1928~1960년 고음반에서 이일선·김죽파·성금연이 연주한 경기민요의 가야금 음높이를 praat로 재어, 줄마다 평균율과의 차이를 6번 줄(도)의 평균에 맞추어 정리했다(183쪽 표 102). 네 녹음 모두 레를 평균율보다 51~69센트 낮게, 라를 30센트 이상 낮게 탔고, 레–미 음정은 장2도보다 넓었다. 이일선 녹음의 11번 줄(높은 도)은 6번 줄보다 1141센트 위에 있어 옥타브보다 59센트 좁다. 양수연(2013)은 김병호·김죽파·성금연·함동정월의 가야금산조 진양조 음원에서 계면조의 중심음인 청과, 꺾는 음을 이루는 두 음을 쟀다. 여기에는 표본이 가장 많은 중간 음역의 값을 실었다(84·87·88쪽). 청에서 꺾는 아래음까지는 68~111센트로 채보에 쓰는 장2도(200센트)보다 훨씬 좁고, 꺾는 윗음까지는 350~354센트로 단3도(300센트)보다 넓다. 다만 함동정월의 윗음은 표에 적힌 센트값(353.8)을 따른 것이고, 같은 표의 주파수로 다시 계산하면 349.7센트다. 청의 옥타브는 1193~1206센트였다(47쪽). 고유동은 세 연주자의 녹음 넷(김죽파는 두 곡), 양수연은 네 연주자의 녹음 하나씩을 쟀다. 이 값이 연주자나 유파 전체를 대표한다고 볼 수는 없다.'
KR_EN = "Two gayageum studies supply measured values for a Korean instrument. Ko (2021) measured with Praat the gayageum pitches of Gyeonggi folk songs played by Lee Ilseon, Kim Jukpa and Seong Geumyeon on records from 1928 to 1960, and gave each string's deviation from equal temperament with the mean of string 6 (Do) set to zero (p. 183, Table 102). In all four records Re is 51–69 cents below equal temperament and La at least 30 cents below, and the Re–Mi step is wider than a major second. In Lee Ilseon's record string 11 (upper Do) lies 1,141 cents above string 6, 59 cents short of an octave. Yang (2013) measured, in jinyangjo recordings of gayageum sanjo by Kim Byeongho, Kim Jukpa, Seong Geumyeon and Ham Dongjeongwol, cheong, the central note of gyemyeonjo, and the two notes of the bent figure (kkeongneun eum). The values shown are for the middle register, which has the most samples (pp. 84, 87–88). From cheong to the lower bent note is 68–111 cents, far narrower than the major second (200 cents) used in transcription; to the upper bent note, 350–354 cents, wider than a minor third (300). Ham Dongjeongwol's upper note follows the cent value printed in the table (353.8); the table's own frequencies give 349.7 cents. Cheong's octave measured 1,193–1,206 cents (p. 47). Ko measured four records by three players (two songs by Kim Jukpa), Yang one recording each by four players. The values do not stand for a player or school as a whole."


LIM = [  # Lim Gyeongmi 2013, MA thesis, Seoul National Univ., p. 114, Table 140: mean interval jing (c') - ttang (d'), cents
    ("김죽파류", "Kim Jukpa school", "157.89", "184.51", "156.76", "155.17", "185.76"),
    ("김병호류", "Kim Byeongho school", "155.01", "–", "156.09", "169.00", "154.82"),
    ("강태홍류", "Kang Taehong school", "155.37", "164.51", "118.76", "86.04", "143.23"),
]
LIM_KO = ("임경미(2013)는 김죽파·김병호·강태홍류 가야금산조의 진양조와 중모리에서 악조마다 징(c′)과 땅(d′) 사이의 음정을 쟀다(114쪽 표 140). 오선보에는 장2도(200센트)로 적는 음정인데, 열네 값 모두 그보다 좁았고 강태홍류 경드름(86센트)을 빼면 모두 단2도와 장2도 사이였다. 음계 전체가 아니라 음정 하나라서 자 위에 그리지 않고 표로 둔다.")
LIM_EN = ("Lim (2013) measured, in the jinyangjo and jungmori of the Kim Jukpa, Kim Byeongho and Kang Taehong schools of gayageum sanjo, the interval between jing (c′) and ttang (d′) in each mode (p. 114, Table 140). Staff notation writes it as a major second (200 cents); all fourteen values are narrower, and all but Kang Taehong's gyeongdeureum (86 cents) lie between a minor and a major second. It is one interval rather than a scale, so it is shown as a table rather than on the ruler.")


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
    b = [f"<style>{GCSS}{CSS}</style><div class='hero'><h1>{'음계와 조율' if k else 'Scales and tuning'}</h1><p class='lead'>"
         + ("한 옥타브(1200센트)를 어떻게 나누어 왔는지, 시대와 지역에 따라 견준다. 점 하나가 음 하나이고, 회색 눈금은 피아노의 12평균율(100센트 간격)이다. 단추를 누르면 브라우저가 그 자리에서 음을 합성해 들려준다."
            if k else "How the octave (1,200 cents) has been divided, compared across periods and regions. Each dot is a note; the grey ticks are piano equal temperament (100 cents apart). The buttons play the scale, synthesised by your browser on the spot.")
         + "</p></div>"]
    b.append("<p class='src'>" + ("모든 음계를 같은 기준음(가온 다, 261.63 Hz) 위에 옮겨 들려준다. 실제 악기의 음높이는 다르다. 「평균율과 번갈아」는 각 음 다음에 가장 가까운 12평균율 음을 들려준다. 소리는 삼각파 합성음이라 악기 음색이 아니다. 「이론」은 비율이나 규칙으로 정한 값, 「실측」은 악기나 연주를 잰 값이다. 속이 빈 점은 내려갈 때만 쓰는 음이고, 점선 고리는 원자료에 없는 옥타브(1200센트)를 재생을 위해 붙인 자리다."
                                 if k else "Every scale is played on the same reference, middle C (261.63 Hz); the instruments themselves sit at other pitches. 'Against equal temperament' follows each note with the nearest equal-tempered note. The sound is a synthesised triangle wave, not the instrument's timbre. 'Theory' marks values set by ratios or rules; 'measured' marks values taken from instruments or performances. A hollow dot is a note used only when descending; a dashed ring marks an octave (1,200 cents) that the source does not give and that is added only for playback.") + "</p>")
    for g, (tko, ten) in GROUPS.items():
        b.append(f"<h2>{tko if k else ten}</h2>")
        if g == "east":
            b.append("<p>" + ("삼분손익은 율관 길이를 3분의 1씩 줄이고 늘려 음을 얻는 방법으로, 순정 5도를 쌓는 것과 같다. 12번째 음인 중려는 4/3(498센트)이 아니라 521.5센트에 놓인다. 5도 12개를 쌓으면 옥타브보다 피타고라스 쉼표(23.5센트)만큼 넘치기 때문이다. 한국 아악의 12율도 같은 계열이다. 유준희 외(2011)가 정리한 비율표에서 중려는 1.35다. 평조·계면조의 음 구성은 관례를 따랐고, 실제 연주에서 중려가 521센트 부근에 놓였는지는 이 값만으로는 알 수 없다."
                              if k else "Sanfen sunyi (三分損益) shortens and lengthens a pipe by a third in turn, which amounts to stacking pure fifths. The twelfth note, 仲呂, lands at 521.5 cents rather than 4/3 (498 cents), because twelve fifths overshoot the octave by the Pythagorean comma (23.5 cents). The twelve yul of Korean court music follow the same series; in the ratio table of Yoo et al. (2011), jungnyeo (仲呂) is 1.35. The note sets of pyeongjo and gyemyeonjo follow convention, and whether performers actually placed jungnyeo near 521 cents cannot be told from these values.") + "</p>")
            b.append("<p>" + (JP_KO if k else JP_EN) + "</p><p>" + (KOTO_KO if k else KOTO_EN) + "</p><p>" + (KR_KO if k else KR_EN) + "</p>" + lim_table(k))
        if g == "measured":
            b.append("<p>" + ("이론이 정한 음과 실제로 조율하거나 연주한 음은 다르다. 같은 곡조의 이론값과 실측값을 나란히 놓았다. 가믈란은 악기 세트 수십 개의 평균이고, 주황 막대는 ±1 표준편차(수록 세트 전체의 모집단 표준편차)다. 여기 실은 가믈란 평균과 라나트 엑 평균에서는 옥타브가 1200센트보다 넓다(1214~1217센트). 원자료에 옥타브 음이 없는 음계는 재생을 위해 1200센트를 붙였다."
                              if k else "The notes a theory prescribes and the notes actually tuned or sung differ. Theory and measurement for the same scale sit side by side. The gamelan rows average dozens of sets; the orange bars show ±1 standard deviation (population SD over the sets included). In the gamelan and ranat ek means shown here the octave is wider than 1,200 cents (1,214–1,217). Where the source gives no octave note, 1,200 cents is added for playback.") + "</p>")
            b.append("".join(f"<p>{x}</p>" for x in ((ME_KO, IN_KO, CH_KO) if k else (ME_EN, IN_EN, CH_EN))))
        for r in df[df.group == g].itertuples():
            add = not (r.cents[-1] > 1150 or r.id in OCTAVE_MEASURED)
            cents = list(r.cents) + ([1200.0] if add else [])
            sd = list(r.sd) + ([0] * (len(cents) - len(r.sd))) if r.sd else None
            kind = ("이론" if r.kind == "theory" else "실측") if k else r.kind
            n = f" · n = {int(r.n)}" if r.n and r.n > 1 else ""
            data = esc(json.dumps(cents))
            down = DOWN.get(r.id)
            dattr = f" data-d='{esc(json.dumps(down + [1200.0]))}'" if down else ""
            b.append(f"<div class='scale'><h3>{esc(r.name_ko if k else r.name_en)}<span class='kind {r.kind}'>{kind}</span></h3>"
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
    b.append("<h2>" + ("4. 아직 넣지 않은 것" if k else "4. Not yet included") + "</h2><p>" + (NY_KO if k else NY_EN) + "</p>")
    b.append("<p class='src'>" + ("자료: " if k else "Data: ") + "McBride, Passmore & Tlusty (2023), 'Convergent evolution in a large cross-cultural database of musical scales', <i>PLoS ONE</i> 18(12): e0284851 — <a href='https://github.com/jomimc/DaMuSc'>DaMuSc</a> (CC BY 4.0); "
             "Garzoli (2015), 'The myth of equidistance in Thai tuning', <i>Analytical Approaches to World Music</i> 4(2); Bozkurt et al. (2009), <i>Journal of New Music Research</i> 38(1): 45–70; Shafiei (2021), arXiv:2108.01283; "
             "Smith (1847), 'A treatise on Arab music, chiefly from a work by Mikhâil Meshâkah, of Damascus', <i>Journal of the American Oriental Society</i> 1(3): 173–217; "
             "Bozkurt (2025), 'An open research dataset of the 1932 Cairo Congress of Arab Music', arXiv:2506.14503 — <a href='https://doi.org/10.5281/zenodo.15682346'>ORD-CC32</a> (CC BY-NC 4.0; the Rast and Bayati rows and scales_cairo1932.csv carry this license); "
             "Ghosh (tr., 1961), <i>The Nāṭyaśāstra</i>, vol. II (Asiatic Society, Calcutta); Serrà, Koduri, Miron & Serra (2011), ISMIR 2011: 157–162; "
             "上原六四郎 (Uehara 1895), 『俗楽旋律考』 (金港堂; <a href='https://dl.ndl.go.jp/pid/856052'>NDL Digital Collections</a>); "
             "Ellis (1885), 'On the musical scales of various nations', <i>Journal of the Society of Arts</i> 33: 485–527; Tracey (1958), 'Towards an assessment of African scales', <i>African Music</i> 2(1): 15–20; Tracey (1948), <i>Chopi Musicians: Their Music, Poetry, and Instruments</i> (London: Oxford University Press for the International African Institute); "
             "고유동 (Ko Yudong 2021. 2.), 「가야금 경기민요 음률 분석: 이일선, 김죽파, 성금연의 연주를 중심으로」, 한양대학교 대학원 국악학과 음악학 석사학위논문 (CC BY-NC-ND 2.0 KR); 양수연 (Yang Suyeon 2013. 2.), 「가야금산조의 음고 및 음정분석연구」, 서울대학교 대학원 음악과 국악기악전공 음악학석사학위논문 (CC BY-NC-SA 2.0 KR); 임경미 (Lim Gyeongmi 2013. 8.), 「가야금산조의 조에 따른 음고 및 음정분석연구」, 서울대학교 대학원 음악과 국악기악전공 음악학석사학위논문 (CC BY-NC-ND 2.0 KR) — the gayageum rows give only the editor's transcription of their numbers and carry license CC-BY-NC-4.0; "
             + ("유준희 외(2011). 비율로 정의된 음률은 정의에서 계산했고 Scala 아카이브(Huygens-Fokker 재단)의 파일과 대조했다." if k else "Yoo et al. (2011). Ratio-defined tunings were computed from their definitions and checked against the Scala archive (Huygens-Fokker Foundation).")
             + "</p>" + JS)
    return "".join(b)


def build(lang, path, page_fn):
    path.write_text(page_fn(lang, "음계와 조율" if lang == "ko" else "Scales and tuning", render(lang),
                            desc="Scales and tuning compared across periods and regions", active="scales"), encoding="utf-8")


if __name__ == "__main__":
    frame().to_csv(D / "scales.csv", index=False, encoding="utf-8", lineterminator="\n")
    print("wrote data/derived/scales.csv")
