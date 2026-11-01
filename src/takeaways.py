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


def _f(v, fmt):
    return format(float(v), fmt)


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
           "All voices are counted together, so differences between groups with different forces largely reflect the forces.")
CAUTION = {
    "beethoven_share": (_ARCH[0] + " " + _EARLY[0], _ARCH[1] + " " + _EARLY[1]),
    "mozart_share": ("「Mozart, Wolfgang Amadeus」 표기만 세고(레오폴트 모차르트는 별개) 편곡도 넣는다. " + _ARCH[0],
                     "Counts the name 'Mozart, Wolfgang Amadeus' only (Leopold Mozart is separate), arrangements included. " + _ARCH[1]),
    "bach_share": ("작곡가 칸이 「Bach, Johann Sebastian」인 항목만 세고(「Vivaldi-Bach」 같은 복합 표기는 제외) 편곡도 넣는다. " + _ARCH[0],
                   "Counts entries credited to 'Bach, Johann Sebastian' only (joint credits such as 'Vivaldi-Bach' are not), arrangements included. " + _ARCH[1]),
    "excerpt_share": ("옛 프로그램에서 협주곡 한 악장을 악장 표시 없이 적었으면 전곡으로 잡힌다. 초기 시즌은 작품 연주 건수가 적다.",
                      "An old program that listed one concerto movement without marking it counts as complete. Early seasons have few work performances."),
    "hhi": ("정기공연만 세면 표본과 곡목 구성이 달라져 값도 달라진다(2025–26 정기공연만 0.016, 전체 0.011). 초기 시즌은 작품 연주 건수가 적다.",
            "Counting subscription concerts only changes the sample and the programme mix, and so the value (2025–26: 0.016 vs 0.011). Early seasons have few work performances."),
    "distinct_composers": ("연주회 수가 늘면 함께 는다. 점유율·HHI와 같이 본다.", "Grows with the number of concerts; read with shares and HHI."),
    "living_share": ("생몰년 확인 비율이 2020년대 시즌에 72~81%로 떨어지고 미확인 작곡가는 대부분 생존해 있을 것이므로, 최근 값은 실제보다 낮을 가능성이 크다 — 상한과 함께 읽는다. 「시즌 시작 연도에 생존」은 연 단위 근사다.",
                     "Date coverage falls to 72–81% in the 2020s and most composers without dates are presumably alive, so recent values are likely too low — read them with the upper bound. 'Alive in the start year' is a year-level approximation."),
    "repertoire_age_median": ("작품의 작곡 연도가 아니라 작곡가의 사망 연도를 쓴다. 생몰년 미확인 작곡가는 빠지므로 최근 시즌은 값이 높게 나올 수 있다.",
                              "Uses the composer's death year, not the work's date. Composers without dates drop out, which may push recent values up."),
    "canon_turnover": ("1840년대는 8시즌, 2020년대는 진행 중 시즌까지 7시즌으로 짧다(1840년대는 앞 10년이 없어 값이 없다). 순위 경계의 동률은 이름순으로 끊으므로 경계의 한 명이 바뀌면 지수가 크게 움직인다.",
                       "The 1840s have 8 seasons and the 2020s 7 including the one in progress (the 1840s have no earlier decade to compare). Ties at the cut-off are broken alphabetically, so one name changing at the boundary moves the index a lot."),
    "chords_per_measure": ("주석이 있는 코퍼스에만 있다(코랄 제외). 주석자의 분석 단위가 코퍼스마다 조금 다르고, 마디의 길이·박자도 묶음마다 다르다.",
                           "Only for annotated corpora (not chorales). Annotation granularity differs slightly between corpora, and bar length and metre differ between groups."),
    "chromatic_ratio": ("조표 기준이라, 조표를 바꾸지 않은 채 전조한 구간에서는 새 조의 음이라도 원래 조표 밖이면 「반음계」로 잡힌다. 코랄은 DCML 판본에 임시표 오류 경고가 있어 Humdrum 판본과 대조했다(상관 0.98).",
                        "Keyed to the signature, so in a modulation without a signature change, notes of the new key outside the original signature count as chromatic. The DCML chorales carry a warning about accidental errors and were cross-checked against the Humdrum encoding (r = 0.98)."),
    "local_key_changes_per_100_measures": ("주석자의 조 판단에 좌우된다. 짧은 토니시제이션은 부속화음으로 처리되어 여기 들어가지 않는다.",
                                           "Depends on the annotator's key reading. Brief tonicizations are labelled as applied chords and are not counted here."),
    "mean_simultaneity": ("울리고 있는 음이 아니라 시작하는 음만 센다. " + _FORCES[0], "Counts starting notes, not sounding ones. " + _FORCES[1]),
    "notes_per_quarter": ("템포를 모르므로 「초당 음표 수」가 아니다. " + _FORCES[0], "Tempo is unknown, so this is not notes per second. " + _FORCES[1]),
    "coda_tempo_diff_bpm": ("템포는 원저자가 Marsyas 템포 추정기로 뽑은 값이고 코다 구간 하나만 표본했다. 교향곡 9번은 뺐다(1~8번). 지휘자 중앙값이 모두 음수여도 모든 악장이 느리다는 뜻은 아니다.",
                            "Tempi are the original authors' Marsyas estimates from a single coda sample. Symphony 9 is excluded (Symphonies 1–8 only). All conductor medians being negative does not mean every movement is slower."),
    "ratio_no_repeats": ("악장 전체 평균이라 템포 변화·루바토·페르마타가 섞인다. 반복 여부는 녹음마다 다르고 데이터에 없으므로, 2배가 곧 템포 절반을 뜻하지는 않는다.",
                         "A whole-movement average, so tempo changes, rubato and fermatas are folded in. Repeat choices vary by recording and are not in the data, so 2× does not mean half the tempo."),
    "tempo_cv_across_performers": ("연주자는 국제 피아노 e-콩쿠르 참가자(MAESTRO)라 상업 음반 연주자 표본이 아니다. 곡당 연주 수가 1~25개로 고르지 않고, 연주가 하나뿐인 곡은 이 지표에서 빠진다.",
                                   "Performers are International Piano-e-Competition entrants (MAESTRO), not commercial recording artists. Performances per piece range from 1 to 25, and pieces with a single performance drop out of this metric."),
    "velocity_sd_median": ("MIDI velocity는 음량의 대리 지표이며 악기·녹음 환경에 따라 눈금이 다르다. 같은 데이터셋 안의 상대 비교에만 쓴다.",
                           "MIDI velocity is a proxy for loudness and its scale depends on instrument and setup. Use it only for relative comparison within this dataset."),
}


def season(label) -> str:
    return str(label).replace("-", "–")


def coll_label(name: str) -> str:
    return re.sub(r" ?\(\d+\)$", "", name)


def _join(items, lang):
    if lang == "ko":
        return "·".join(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _score(m, lang, d, coll_names):
    s = d["score"]
    meds = []
    for (comp, coll), g in s.groupby(["composer", "collection"], sort=False):
        v = g[m["id"]].astype(float).dropna()
        if len(v):
            cl = coll_label(coll_names[coll])
            name = f"{KO[comp]} {cl}" if lang == "ko" else f"{comp}'s {cl if cl.startswith('English') else cl[0].lower() + cl[1:]}"
            meds.append((name, v.median(), len(v), comp, coll))
    meds.sort(key=lambda x: x[1], reverse=True)
    hi, lo = meds[0], meds[-1]
    fmt = m["fmt"]
    if lang == "ko":
        out = f"악장 중앙값이 가장 높은 묶음은 {hi[0]}({_f(hi[1], fmt)}), 가장 낮은 묶음은 {lo[0]}({_f(lo[1], fmt)})."
    else:
        out = f"Across movements, {hi[0]} have the highest median ({_f(hi[1], fmt)}) and {lo[0]} the lowest ({_f(lo[1], fmt)})."
    son = {c: v for _, v, _, c, coll in meds if coll == "piano_sonatas"}
    if {"Beethoven", "Mozart"} <= son.keys():
        if lang == "ko":
            out += f" 같은 피아노 소나타끼리는 베토벤 {_f(son['Beethoven'], fmt)}, 모차르트 {_f(son['Mozart'], fmt)}."
        else:
            out += f" Within the piano sonatas: Beethoven {_f(son['Beethoven'], fmt)}, Mozart {_f(son['Mozart'], fmt)}."
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
    top = c["median_diff_bpm"].max()
    med = c["median_diff_bpm"].median()
    if lang == "ko":
        who = f"지휘자 {n}명 모두" if slow == n else f"지휘자 {n}명 가운데 {slow}명의"
        return (f"교향곡 1~8번에서 {who} 중앙값이 메트로놈 표시보다 느리다. 지휘자별 중앙값의 중앙값은 {med:+.1f} bpm이고, "
                f"표시와의 차이가 가장 작은 지휘자도 {top:+.1f} bpm.")
    who = f"all {n} conductors have" if slow == n else f"{slow} of {n} conductors have"
    return (f"In Symphonies 1–8, {who} a median slower than the metronome mark. The median of conductor medians is {med:+.1f} bpm; "
            f"the conductor closest to the marks is still {top:+.1f} bpm.")


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
    else:
        return ""
    caution = caution_for(m, lang, by_id or {})
    h, s_lbl, c_lbl = (("한눈에 보기", "데이터가 보여 주는 것", "주의할 점") if lang == "ko" else ("At a glance", "What the data show", "Watch for"))
    return (f"<aside class='glance'><p class='glance-h'>{h}</p><dl><dt>{s_lbl}</dt><dd>{html.escape(seen)}</dd>"
            f"<dt>{c_lbl}</dt><dd>{html.escape(caution)}</dd></dl></aside>")
