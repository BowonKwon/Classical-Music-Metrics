"""'At a glance' boxes for metric pages (1.2.1).

Every number is computed here from the same tables the page draws, so the box cannot drift from the data.
The caution line is taken from the metric's caveat in registry.py (explicit text where a shortened
caveat would drop a limit that bears on the comparison shown).
"""
from __future__ import annotations

import html
import re

import pandas as pd

KO = {"Bach": "바흐", "Beethoven": "베토벤", "Mozart": "모차르트"}


def minus(s: str) -> str:
    """Hyphen-minus in front of a number -> minus sign (U+2212), as on the rest of the site."""
    return re.sub(r"(?<![\w.])-(?=\d)", "\u2212", s)


def stat_spec(v, fmt: str) -> str:
    """Format spec for a median or quartile. Integer-valued metrics (fmt ".0f") keep whole numbers as integers,
    but a median of an even count (29.5) or an interpolated quartile (57.75 -> 57.8) is shown with one decimal place instead of rounded
    (rounding 29.5 to "30" made the box disagree with the table's definition of the median)."""
    x = float(v)
    if fmt != ".0f" or x != x or x.is_integer():
        return fmt
    return ".1f"   # 1.4 owner decision (2026-11-04): one decimal place (57.75 -> 57.8)


def _f(v, fmt):
    return minus(format(float(v), fmt))


def _fs(v, fmt):
    """A median/quartile: _f with stat_spec."""
    return _f(v, stat_spec(v, fmt))


def sentences(text: str, lang: str) -> list[str]:
    """Split into sentences, not inside parentheses or after e.g. / i.e. / etc."""
    out, start, depth = [], 0, 0
    for i, ch in enumerate(text):
        depth += (ch == "(") - (ch == ")")
        if depth or ch != "." or text[i + 1:i + 2] not in ("", " "):
            continue
        if lang == "ko" and text[i - 1:i] != "다":
            continue
        if lang != "ko" and re.search(r"(e\.g|i\.e|etc|cf|vs|No)$", text[:i]):
            continue
        out.append(text[start:i + 1].strip())
        start = i + 1
    if text[start:].strip():
        out.append(text[start:].strip())
    return out


def first_sentence(text: str, lang: str) -> str:
    return sentences(text, lang)[0]


def ties(series: pd.Series, value: float) -> list:
    """All index labels whose value equals `value` (exact ties in the raw data)."""
    return [k for k, v in series.items() if v == value]


_ARCH = ("한 아카이브의 기록이며 뉴욕 심포니·스타디움 콘서트 등 관련 단체의 프로그램이 섞여 있다.",
         "One archive's record, which mixes in programs of related bodies (New York Symphony, Stadium concerts).")
_EARLY = ("초기 시즌은 작품 연주 건수가 적어 비율이 거칠다(1842–43은 작품 연주 31건).",
          "Early seasons have few work performances, so shares are coarse (31 in 1842–43).")
_FORCES = ("모든 성부의 음을 합산하므로, 편성이 다른 묶음 사이의 높낮이는 편성 차이를 크게 반영한다.",
           "All voices are counted together, so differences between collections with different forces largely reflect the forces.")
CAUTION = {
    "beethoven_share": (_ARCH[0] + " " + _EARLY[0], _ARCH[1] + " " + _EARLY[1]),
    "mozart_share": ("「Mozart, Wolfgang Amadeus」 표기만 세고(레오폴트 모차르트는 별개) 편곡도 넣는다. " + _ARCH[0],
                     "Counts the name 'Mozart, Wolfgang Amadeus' only (Leopold Mozart is separate), arrangements included. " + _ARCH[1]),
    "bach_share": ("작곡가 칸이 「Bach, Johann Sebastian」인 항목만 세고(「Vivaldi-Bach」 같은 복합 표기는 제외) 편곡도 넣는다. " + _ARCH[0],
                   "Counts entries credited to 'Bach, Johann Sebastian' only (joint credits such as 'Vivaldi-Bach' are not), arrangements included. " + _ARCH[1]),
    "excerpt_share": ("옛 프로그램에서 협주곡 한 악장을 악장 표시 없이 적었으면 전곡으로 잡힌다. 초기 시즌은 작품 연주 건수가 적다.",
                      "An old program that listed one concerto movement without marking it counts as complete. Early seasons have few work performances."),
    "hhi": ("정기공연만 세면 표본과 곡목 구성이 달라져 값도 달라진다(2025–26 정기공연만 0.016, 전체 0.011). 초기 시즌은 작품 연주 건수가 적다.",
            "Restricting the count to subscription concerts changes the sample and the program mix, and therefore the value (2025–26: 0.016 vs 0.011). Early seasons have few work performances."),
    "distinct_composers": ("연주회 수가 늘면 함께 늘어나므로 점유율·HHI와 같이 본다.", "Grows with the number of concerts, so read it with shares and HHI."),
    "living_share": ("생몰년 확인 비율이 2020년대 시즌에 72~81%로 떨어지고 미확인 작곡가는 대부분 생존해 있을 것이므로, 최근 값은 실제보다 낮을 가능성이 크다 — 상한과 함께 읽는다. 「시즌 시작 연도에 생존」은 연 단위 근사다.",
                     "Date coverage falls to 72–81% in the 2020s and most composers without dates are presumably alive, so recent values are likely too low — read them with the upper bound. 'Alive in the start year' is a year-level approximation."),
    "repertoire_age_median": ("작품의 작곡 연도가 아니라 작곡가의 사망 연도를 쓴다. 생몰년 미확인 작곡가는 빠지므로 최근 시즌은 값이 높게 나올 수 있다.",
                              "Uses the composer's death year, not the work's date. Composers without dates drop out, which may push recent values up."),
    "canon_turnover": ("1840년대는 8시즌, 2020년대는 진행 중 시즌까지 7시즌으로 짧다(1840년대는 앞 10년이 없어 값이 없다). 순위 경계의 동률은 이름순으로 끊으므로 경계의 한 명이 바뀌면 지수가 크게 움직인다.",
                       "The 1840s have 8 seasons and the 2020s 7 including the one in progress (the 1840s have no earlier decade to compare). Ties at the cut-off are broken alphabetically, so one name changing at the boundary moves the index a lot."),
    "chords_per_measure": ("주석이 있는 코퍼스에만 있다(코랄 제외). 주석자의 분석 단위가 코퍼스마다 조금 다르고, 마디의 길이·박자도 묶음마다 다르다.",
                           "Only for annotated corpora (not chorales). Annotation granularity differs slightly between corpora, and bar length and meter differ between collections."),
    "chromatic_ratio": ("조표 기준이라, 조표를 바꾸지 않은 채 전조한 구간에서는 새 조의 음이라도 원래 조표 밖이면 「반음계」로 잡힌다. 코랄은 DCML 판본에 임시표 오류 경고가 있어 Humdrum 판본과 대조했다(상관 0.98).",
                        "Keyed to the signature, so in a modulation without a signature change, notes of the new key outside the original signature count as chromatic. The DCML chorales carry a warning about accidental errors and were cross-checked against the Humdrum encoding (r = 0.98)."),
    "local_key_changes_per_100_measures": ("주석자의 조 판단에 좌우된다. 짧은 토니시제이션은 부속화음으로 처리되어 여기 들어가지 않는다.",
                                           "Depends on the annotators' key reading. Brief tonicizations are labeled as applied chords and are not counted here."),
    "mean_simultaneity": ("울리고 있는 음이 아니라 시작하는 음만 센다. " + _FORCES[0], "Counts starting notes, not sounding ones. " + _FORCES[1]),
    "notes_per_quarter": ("템포를 모르므로 「초당 음표 수」가 아니다. " + _FORCES[0], "Tempo is unknown, so this is not notes per second. " + _FORCES[1]),
    "coda_tempo_diff_bpm": ("템포는 원저자가 Marsyas 템포 추정기로 뽑은 값이고 코다 구간 하나만 표본했다. 교향곡 9번은 뺐다(1~8번). 지휘자 중앙값이 모두 음수여도 모든 악장이 느리다는 뜻은 아니다.",
                            "Tempi are the original authors' Marsyas estimates from a single coda sample. Symphony 9 is excluded (Symphonies 1–8 only). All conductor medians being negative does not mean every movement is slower."),
    "ratio_no_repeats": ("악장 전체 평균이라 템포 변화·루바토·페르마타가 섞인다. 반복 여부는 녹음마다 다르고 데이터에 없으므로, 2배가 곧 템포 절반을 뜻하지는 않는다.",
                         "A whole-movement average, so tempo changes, rubato and fermatas are folded in. Repeat choices vary by recording and are not in the data, so 2× does not mean half the tempo."),
    "tempo_cv_across_performers": ("연주자는 국제 피아노 e-콩쿠르 참가자(MAESTRO)라 상업 음반 연주자 표본이 아니다. 곡당 연주 수가 1~25개로 고르지 않고, 연주가 하나뿐인 곡은 이 지표에서 빠진다.",
                                   "Performers are International Piano-e-Competition entrants (MAESTRO), not commercial recording artists. Performances per piece range from 1 to 25, and pieces with a single performance drop out of this metric."),
    "pitch_mean_midi": ("편성과 악기 음역에 크게 좌우되어 같은 편성 안에서만 비교한다. 바흐 무반주 묶음은 바이올린(높음)과 첼로(낮음)가 섞여 분포가 둘로 갈린다.",
                        "Driven by forces and instrument ranges; compare within the same forces only. Bach's solo works mix violin (high) and cello (low), so their distribution splits in two."),
    "pitch_sd_midi": ("편성에 따라 달라지므로 같은 편성 안에서만 비교한다.", "Depends on the forces; compare within the same forces only."),
    "mean_chord_duration_qb": ("주석이 있는 코퍼스에만 있다(코랄 제외). 주석자의 분석 단위가 코퍼스마다 조금 다르다.",
                               "Only for annotated corpora (not chorales). Annotation granularity differs slightly between corpora."),
    "motif_repeat_ratio": ("이 사이트가 정한 정의다. 음정 열로 세므로 조옮김한 반복도 잡히지만 리듬은 보지 않고, 반복 기호는 펼치지 않는다.",
                           "This site's own definition. Built on intervals, so transposed repeats count, but rhythm is ignored and repeat signs are not expanded."),
    "dim7_ratio": ("주석이 있는 코퍼스에만 있다(코랄 제외). 이끈음 위 감7과 부속화음으로 쓰인 감7을 가리지 않는다.",
                   "Only for annotated corpora (not chorales). Leading-tone and applied diminished sevenths are not separated."),
    "cadences_per_100_measures": ("종지를 주석한 코퍼스·작품에만 있다: 베토벤 현악4중주는 주석이 없고, 바흐 무반주는 BWV 1009~1013만 주석이 있다(바이올린 작품·첼로 모음곡 1·2번은 비워 둔다). 마디 길이가 다른 묶음끼리는 차이를 덜어 읽는다.",
                                  "Only where cadences are annotated: the Beethoven quartets have none, and among Bach's solo works only BWV 1009–1013 are annotated (the violin works and Cello Suites 1–2 are left blank). Treat differences between collections with different bar lengths with caution."),
    "chromatic_numeral_ratio": ("DCML 표기는 단조의 로마 숫자를 자연 단음계 기준으로 적어, 단조의 이끈음 화음(화성 단음계로는 온음계 화음)이 ♯vii 로 적혀 여기에 들어간다(모차르트 단조 구간 화음 2,304개 중 206개). 단조 비중이 큰 묶음은 값이 높게 나온다.",
                                "DCML writes minor-key numerals against the natural minor scale, so minor-key leading-tone chords (diatonic in harmonic minor) appear as ♯vii and count here (206 of 2,304 minor-key chords in Mozart). Groups with more minor music score higher."),
    "pac_ratio_of_cadences": ("종지 주석이 있는 악장에만 있다(종지 밀도와 같은 범위). 종지가 몇 개 안 되는 악장은 값이 거칠다.",
                              "Only for movements with cadence annotation (same scope as cadence density). Movements with few cadences give coarse values."),
    "phrase_4_8_ratio": ("악구 길이와 같은 한계(주석자 판단·못갖춘마디·옛 표기). 끝에서 끝까지의 간격이라 악구 안의 대칭성까지 보여 주지는 않는다.",
                         "Same limits as phrase length (annotators' judgment, pickups, older convention). End-to-end gaps do not show symmetry within a phrase."),
    "predominant_chromatic_ratio": ("주석이 있는 코퍼스에만 있다(코랄 제외). 나폴리 화음의 전위·부속 용법을 가리지 않는다.",
                                    "Only for annotated corpora (not chorales). Inversions and applied uses of the Neapolitan are not separated."),
    "velocity_sd_median": ("MIDI velocity는 음량의 대리 지표이며 악기·녹음 환경에 따라 눈금이 다르다. 같은 데이터셋 안의 상대 비교에만 쓴다.",
                           "MIDI velocity is a proxy for loudness and its scale depends on instrument and setup. Use it only for relative comparison within this dataset."),
}


def season(label) -> str:
    return str(label).replace("-", "–")


def coll_label(name: str) -> str:
    return re.sub(r" ?\(\d+\)$", "", name)


def _join(items, lang):
    if lang == "ko":
        return (", " if any("·" in x for x in items) else "·").join(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _score(m, lang, d, coll_names):
    s = d["score"]
    meds = []
    for (comp, coll), g in s.groupby(["composer", "collection"], sort=False):
        v = g[m["id"]].astype(float).dropna()
        if len(v):
            cl = coll_label(coll_names[coll])
            name = f"{KO[comp]} {cl}" if lang == "ko" else (f"{comp}'s solo works (violin, cello, flute)" if coll == "solo_violin_cello_flute" else f"{comp}'s {cl if cl.startswith('English') else cl[0].lower() + cl[1:]}")
            meds.append((name, v.median(), len(v), comp, coll))
    meds.sort(key=lambda x: x[1], reverse=True)
    hi, lo = meds[0], meds[-1]
    fmt = m["fmt"]
    hi_n = _join([x[0] for x in meds if x[1] == hi[1]], lang)  # exact ties are all named
    lo_n = _join([x[0] for x in meds if x[1] == lo[1]], lang)
    if lang == "ko":
        out = f"악장 중앙값이 가장 높은 묶음은 {hi_n}({_fs(hi[1], fmt)}), 가장 낮은 묶음은 {lo_n}({_fs(lo[1], fmt)})."
    else:
        out = f"Among the collections, {hi_n} have the highest median ({_fs(hi[1], fmt)}) and {lo_n} the lowest ({_fs(lo[1], fmt)})."
    son = {c: v for _, v, _, c, coll in meds if coll == "piano_sonatas"}
    if {"Beethoven", "Mozart"} <= son.keys():
        if lang == "ko":
            out += f" 같은 피아노 소나타끼리는 베토벤 {_fs(son['Beethoven'], fmt)}, 모차르트 {_fs(son['Mozart'], fmt)}."
        else:
            out += f" Within the piano sonatas: Beethoven {_fs(son['Beethoven'], fmt)}, Mozart {_fs(son['Mozart'], fmt)}."
    return out


def _season(m, lang, d):
    done = d["ny_done"].set_index("season", drop=False)
    col, fmt = m["id"], m["fmt"]
    a, b = done.iloc[0], done.iloc[-1]
    vals = done[col].astype(float)
    peaks = ties(vals, vals.max())
    pk = done.loc[peaks[0]]
    sa, sb = season(a["season"]), season(b["season"])
    sp = _join([season(x) for x in peaks], lang)
    npr, nwp = int(pk["n_programs"]), int(pk["work_performances"])
    if col == "living_share":
        base = round(nwp * float(pk["dated_coverage"]))
        size_ko, size_en = f"생몰년 확인 작품 연주 {base:,}건 기준", f"base: {base:,} work performances with known dates"
    else:
        size_ko, size_en = f"연주회 {npr:,}회·작품 연주 {nwp:,}건", f"{npr:,} concerts, {nwp:,} work performances"
    if lang == "ko":
        out = (f"{sa} {_f(a[col], fmt)} → {sb} {_f(b[col], fmt)}(완결 시즌 기준). "
               f"가장 높았던 시즌은 {sp}({_f(pk[col], fmt)}, {size_ko}).")
    else:
        out = (f"{sa} {_f(a[col], fmt)} → {sb} {_f(b[col], fmt)} (completed seasons). "
               f"The peak was {sp} ({_f(pk[col], fmt)}; {size_en}).")
    if m.get("band"):
        lo, hi = m["band"]
        out += (f" {sb}의 범위는 {_f(b[lo], fmt)}~{_f(b[hi], fmt)}(생몰년 미확인 작곡가를 어느 쪽으로 넣느냐에 따라)." if lang == "ko"
                else f" For {sb} the range is {_f(b[lo], fmt)}–{_f(b[hi], fmt)}, depending on how composers with unknown dates are counted.")
    return out


def _turnover(m, lang, d):
    tt = d["ny_turn"].dropna(subset=["jaccard_top10"]).set_index("decade")
    v = tt["jaccard_top10"].astype(float)
    med = v.median()
    lo_d, hi_d = ties(v, v.min()), ties(v, v.max())
    if lang == "ko":
        return (f"10년마다 상위 10명이 앞 10년과 겹치는 정도의 중앙값은 {med:.2f}. 가장 많이 바뀐 때는 {_join([f'{int(x)}년대' for x in lo_d], lang)}({v.min():.2f}), "
                f"가장 적게 바뀐 때는 {_join([f'{int(x)}년대' for x in hi_d], lang)}({v.max():.2f}).")
    return (f"Median overlap of the top 10 with the previous decade: {med:.2f}. Most change in the {_join([f'{int(x)}s' for x in lo_d], lang)} ({v.min():.2f}), "
            f"least in the {_join([f'{int(x)}s' for x in hi_d], lang)} ({v.max():.2f}).")


def _coda(m, lang, d):
    c = d["cond"]
    n, slow = len(c), int((c["median_diff_bpm"] < 0).sum())
    diffs = c["median_diff_bpm"].astype(float)
    top = diffs.loc[diffs.abs().idxmin()]  # closest to the marks = smallest |difference|
    med = c["median_diff_bpm"].median()
    if lang == "ko":
        who = f"지휘자 {n}명 모두" if slow == n else f"지휘자 {n}명 가운데 {slow}명의"
        return (f"교향곡 1~8번에서 {who} 중앙값이 메트로놈 표시보다 느리다. 지휘자별 중앙값의 중앙값은 {_f(med, '+.1f')} bpm이고, "
                f"표시와의 차이가 가장 작은 지휘자도 {_f(top, '+.1f')} bpm.")
    who = f"all {n} conductors have" if slow == n else f"{slow} of {n} conductors have"
    return (f"In Symphonies 1–8, {who} a median slower than the metronome mark. The median of conductor medians is {_f(med, '+.1f')} bpm; "
            f"the conductor closest to the marks is still {_f(top, '+.1f')} bpm.")


def _duration(m, lang, d):
    mv = d["mvsum"]
    v = mv["ratio_no_rep_median"].astype(float)
    lo, hi = mv.loc[v.idxmin()], mv.loc[v.idxmax()]
    if lang == "ko":
        return (f"이론 시간을 반복 없이 계산하면 악장별 중앙값은 {v.min():.2f}~{v.max():.2f}배"
                f"(최소 {int(lo.symphony)}번 {int(lo.movement)}악장, 최대 {int(hi.symphony)}번 {int(hi.movement)}악장).")
    return (f"With the theoretical time computed without repeats, movement medians run {v.min():.2f}–{v.max():.2f}×"
            f" (lowest: Symphony {int(lo.symphony)}/{int(lo.movement)}; highest: {int(hi.symphony)}/{int(hi.movement)}).")


def _asap(m, lang, d):
    a = d["asap_piece"]
    fmt = m["fmt"]
    parts = []
    for c in ("Bach", "Beethoven"):
        v = a.loc[a.composer == c, m["id"]].astype(float).dropna()
        parts.append((KO[c] if lang == "ko" else c, v.median(), len(v)))
    nm = int((a.composer == "Mozart").sum())
    nv = int(a.loc[a.composer == "Mozart", m["id"]].notna().sum())
    if lang == "ko":
        tail = f"모차르트는 {nm}곡" + (f"(이 지표가 있는 곡은 {nv}곡)" if nv != nm else "") + "이라 표에만 둔다."
        return "곡별 값의 중앙값은 " + ", ".join(f"{n} {_f(v, fmt)}({k}곡)" for n, v, k in parts) + ". " + tail
    tail = f"Mozart ({nm} pieces" + (f", {nv} with this metric" if nv != nm else "") + ") is in the table only."
    return "Median over pieces: " + ", ".join(f"{n} {_f(v, fmt)} ({k} pieces)" for n, v, k in parts) + ". " + tail


def _trend(m, lang, d):
    tr = d["trend"].set_index("model")
    fe, pt = tr.loc["movement_fe"], tr.loc["movement_fe_ptype"]
    f = lambda v: _f(v, "+.2f")  # noqa: E731
    if lang == "ko":
        return (f"같은 악장 안에서 녹음이 10년 늦을수록 표기와의 차이는 {f(fe['slope_bpm_per_decade'])} bpm(95% 구간 {f(fe['ci95_low'])}~{f(fe['ci95_high'])}; "
                f"{int(fe['n_obs']):,}행·지휘자 {int(fe['n_conductors'])}명) — 늦은 녹음과 덜 느린 템포가 함께 관찰된다. "
                f"연주 양식을 함께 고려하면 {f(pt['slope_bpm_per_decade'])}({f(pt['ci95_low'])}~{f(pt['ci95_high'])})로 줄어 0과 구별되지 않는다.")
    return (f"Within movements, each decade later in recording goes with {f(fe['slope_bpm_per_decade'])} bpm relative to the marks (95% interval {f(fe['ci95_low'])} to {f(fe['ci95_high'])}; "
            f"{int(fe['n_obs']):,} rows, {int(fe['n_conductors'])} conductors): later recordings and less slow tempi are observed together. "
            f"With performance style included it falls to {f(pt['slope_bpm_per_decade'])} ({f(pt['ci95_low'])} to {f(pt['ci95_high'])}), which cannot be told apart from 0.")


def _pedal(m, lang, d):
    ps = d["pedal_sum"].set_index("composer")
    parts = [(KO[c] if lang == "ko" else c, ps.loc[c]) for c in ("Bach", "Beethoven", "Mozart") if c in ps.index]
    if m["id"] == "sustain_ratio":
        if lang == "ko":
            return "연주별 중앙값은 " + ", ".join(f"{n} {_f(r['sustain_ratio_median'], '.2f')}({int(r['n_performances'])}연주)" for n, r in parts) + "."
        return "Median over performances: " + ", ".join(f"{n} {_f(r['sustain_ratio_median'], '.2f')} ({int(r['n_performances'])} performances)" for n, r in parts) + "."
    if lang == "ko":
        return "소프트 페달을 쓴 연주는 " + ", ".join(f"{n} {_f(r['soft_used_share'], '.1%')}({int(r['soft_used_n'])}/{int(r['n_performances'])})" for n, r in parts) + "."
    return "Performances using the soft pedal: " + ", ".join(f"{n} {_f(r['soft_used_share'], '.1%')} ({int(r['soft_used_n'])}/{int(r['n_performances'])})" for n, r in parts) + "."


# 1.4 owner decision (2026-11-04): Korean spelling beside the archive name in the Korean box (conductors with 1,000+ work performances)
KO_CONDUCTOR = {'Damrosch': '담로시', 'Stransky': '스트란스키', 'Bernstein': '번스타인', 'Mehta': '메타', 'Kostelanetz': '코스텔라네츠', 'Mitropoulos': '미트로풀로스', 'Masur': '마주어', 'Hoogstraten': '호흐스트라턴', 'Gilbert': '길버트', 'Maazel': '마젤', 'Barbirolli': '바비롤리', 'Toscanini': '토스카니니', 'Mengelberg': '멩엘베르크', 'Boulez': '불레즈', 'Leinsdorf': '라인스도르프', 'Rodzinski': '로진스키', 'Walter': '발터', 'Smallens': '스몰렌스', 'Schelling': '셸링', 'Slatkin': '슬래트킨'}


def _conductor(m, lang, d):
    c = d["ny_cond"]
    big = c[(c["conductor_flag"] == "person") & (c["perf_u1"] >= 1000)]
    hi, lo = big.loc[big["living_share"].idxmax()], big.loc[big["living_share"].idxmin()]
    none = int(c.loc[c["conductor_flag"] == "none_recorded", "perf_u1"].sum())
    nm = lambda r: r["conductor"].split(",")[0]  # noqa: E731
    if lang == "ko":
        nm = lambda r: (lambda sur: f"{KO_CONDUCTOR[sur]}({sur})" if sur in KO_CONDUCTOR else sur)(r["conductor"].split(",")[0])  # noqa: E731
        return (f"작품 연주 1,000건 이상인 지휘자 {len(big)}명 가운데 생존 작곡가 점유율이 가장 높은 지휘자는 {nm(hi)}({_f(hi['living_share'], '.1%')}), "
                f"가장 낮은 지휘자는 {nm(lo)}({_f(lo['living_share'], '.1%')}). 지휘자가 기록되지 않은 작품 연주는 {none:,}건.")
    return (f"Among {len(big)} conductors with 1,000+ work performances, the living-composer share is highest for {nm(hi)} ({_f(hi['living_share'], '.1%')}) "
            f"and lowest for {nm(lo)} ({_f(lo['living_share'], '.1%')}). {none:,} work performances have no conductor recorded.")


def _survival(m, lang, d):
    s = d["surv_sum"].set_index(["set", "cohort"])
    a = s.loc[("living_composer", "all")]
    e, l_ = s.loc[("living_composer", "1843-1899")], s.loc[("living_composer", "2000-")]
    p = lambda v: _f(v, ".1%")  # noqa: E731
    if lang == "ko":
        return (f"작곡가가 살아 있던 작품 {int(a['n_used']):,}개 가운데 10년 안에 다른 시즌에 다시 연주된 비율은 {p(a['reperf_10y_km'])}"
                f"({p(a['reperf_10y_ci95_low'])}~{p(a['reperf_10y_ci95_high'])}). 1843~1899년에 처음 연주된 작품은 {p(e['reperf_10y_km'])}, 2000년 이후는 {p(l_['reperf_10y_km'])}.")
    return (f"Of {int(a['n_used']):,} works by living composers, {p(a['reperf_10y_km'])} were played again in another season within 10 years "
            f"({p(a['reperf_10y_ci95_low'])}–{p(a['reperf_10y_ci95_high'])}). First performed 1843–1899: {p(e['reperf_10y_km'])}; since 2000: {p(l_['reperf_10y_km'])}.")



def _women(m, lang, d):
    w = d["women"]
    w = w[w["season_start"] <= 2025].assign(dec=lambda x: (x["season_start"] // 10) * 10)
    def dec(y):
        g = w[w["dec"] == y]; u = g["person_u1"].astype(float); k = u * g["gender_coverage"]
        return ((g["women_share_low"] * u).sum() / u.sum(), (g["women_share"].fillna(0) * k).sum() / k.sum(), (g["women_share_high"] * u).sum() / u.sum())
    lo, mid, hi = dec(2020)
    p = lambda v: _f(v, ".1%")  # noqa: E731
    if lang == "ko":
        return f"2000년대까지는 10년 단위 가운데 값이 1% 아래였다. 2020년대 완결 시즌은 {p(mid)}(하한 {p(lo)}~상한 {p(hi)}) — 성별 미상 작곡가가 늘어 폭이 넓다."
    return f"Up to the 2000s the decade middle value stays below 1%. Completed seasons of the 2020s: {p(mid)} (lower bound {p(lo)}, upper bound {p(hi)}) — the range is wide, as more composers have no recorded gender."


def caution_for(m, lang, by_id) -> str:
    if m["id"] in CAUTION:
        return CAUTION[m["id"]][0 if lang == "ko" else 1]
    return first_sentence(m[lang]["caveat"], lang)


def box(m, lang, d, coll_names, by_id=None) -> str:
    kind = m["table"]
    if kind == "score":
        seen = _score(m, lang, d, coll_names)
    elif kind == "nyphil_season":
        seen = _season(m, lang, d)
    elif kind == "nyphil_turnover":
        seen = _turnover(m, lang, d)
    elif kind == "coda":
        seen = _coda(m, lang, d)
    elif kind == "duration":
        seen = _duration(m, lang, d)
    elif kind == "asap_piece":
        seen = _asap(m, lang, d)
    elif kind == "tempo_trend":
        seen = _trend(m, lang, d)
    elif kind in ("asap_pedal", "asap_soft"):
        seen = _pedal(m, lang, d)
    elif kind == "nyphil_conductor":
        seen = _conductor(m, lang, d)
    elif kind == "nyphil_survival":
        seen = _survival(m, lang, d)
    elif kind == "nyphil_women":
        seen = _women(m, lang, d)
    else:
        return ""
    caution = caution_for(m, lang, by_id or {})
    h, s_lbl, c_lbl = (("한눈에 보기", "데이터가 보여 주는 것", "주의할 점") if lang == "ko" else ("At a glance", "What the data show", "Watch for"))
    return (f"<aside class='glance'><p class='glance-h'>{h}</p><dl><dt>{s_lbl}</dt><dd>{html.escape(seen)}</dd>"
            f"<dt>{c_lbl}</dt><dd>{html.escape(caution)}</dd></dl></aside>")
