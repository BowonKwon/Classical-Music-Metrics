"""'At a glance' boxes for the seven sections of the Works & history page (1.2.1).

Every number is computed from the same tables the section draws. Callers pass the page module (hp) so
names, filters and the language switch are the page's own.
"""
from __future__ import annotations

import html
import re

import pandas as pd


def josa(word: str, pair: str) -> str:
    """Korean particle by final consonant: pair is '이가', '과와', '은는' or '을를'."""
    ch = word.strip()[-1:]
    if "가" <= ch <= "힣":
        return word + (pair[0] if (ord(ch) - 0xAC00) % 28 else pair[1])
    return word + pair[1]


def _box(lang, seen, caution):
    h, s_lbl, c_lbl = (("한눈에 보기", "데이터가 보여 주는 것", "주의할 점") if lang == "ko" else ("At a glance", "What the data show", "Watch for"))
    return (f"<aside class='glance'><p class='glance-h'>{h}</p><dl><dt>{s_lbl}</dt><dd>{html.escape(seen)}</dd>"
            f"<dt>{c_lbl}</dt><dd>{html.escape(caution)}</dd></dl></aside>")


def boxes(hp, lang, W, AC, RP, MR, SY, TP, TL, IU, EP, okb, okb2) -> dict[int, str]:
    ko = lang == "ko"
    name, gname, tname, iname = hp.name, hp.gname, hp.tname, hp.iname
    G = {}

    # 1 — career ribbons: pages per composer, genre mix
    per = W.groupby("composer").size().reindex(hp.ORDER).dropna()
    gen = W["genre"].value_counts(normalize=True)
    top_g = gen.index[0]
    hi_c, lo_c = per.idxmax(), per.idxmin()
    G[1] = _box(lang,
                (f"작품면은 {name(hi_c)} {int(per[hi_c]):,}면이 가장 많고 {name(lo_c)} {int(per[lo_c]):,}면이 가장 적다. 장르별로는 {josa(gname(top_g), '이가')} 전체의 {gen[top_g]:.0%}로 가장 많다." if ko else
                 f"{name(hi_c)} has the most work pages ({int(per[hi_c]):,}) and {name(lo_c)} the fewest ({int(per[lo_c]):,}). By genre, {gname(top_g).lower()} makes up the largest share, {gen[top_g]:.0%} of all pages."),
                ("단위는 IMSLP 작품면이라 작곡한 작품 수와 같지 않다." if ko else "The unit is the IMSLP work page, not the number of works composed."))

    # 2 — age profile: earliest and latest peak band
    pk = AC.loc[AC.groupby("composer")["share"].idxmax()].set_index("composer").reindex(hp.ORDER).dropna(subset=["age_bin"])
    e, l = pk["age_bin"].idxmin(), pk["age_bin"].idxmax()
    ea, la = int(pk.loc[e, "age_bin"]), int(pk.loc[l, "age_bin"])
    G[2] = _box(lang,
                (f"연도가 확인된 작품면 가운데, 작품면이 가장 많은 5년 구간이 가장 이른 작곡가는 {name(e)}({ea}~{ea + 4}세, {pk.loc[e, 'share']:.0%}), 가장 늦은 작곡가는 {name(l)}({la}~{la + 4}세, {pk.loc[l, 'share']:.0%})." if ko else
                 f"Among dated work pages, the five-year band with the most pages comes earliest for {name(e)} ({ea}–{ea + 4}, {pk.loc[e, 'share']:.0%}) and latest for {name(l)} ({la}–{la + 4}, {pk.loc[l, 'share']:.0%})."),
                ("나이는 작곡 연도에서 출생 연도를 뺀 값이고, 곡의 길이·규모를 통제하지 않아 「노동량」 비교가 아니다." if ko else
                 "Age is composition year minus birth year, and length and scale are not controlled, so this is not a comparison of workload."))

    # 3 — composed vs performed: biggest over-representation among the composers shown
    shown = [c for c in hp.ORDER if not RP[RP.composer == c].empty and not MR[MR.composer == c].empty
             and MR[MR.composer == c].iloc[0].dated_u1_share >= 0.5]
    best = None
    for c in shown:
        r = RP[RP.composer == c].copy()
        r["gap"] = r["nyphil_share"] - r["works_share"]
        top = r.loc[r["gap"].idxmax()]
        if best is None or top.gap > best[1].gap:
            best = (c, top)
    c, top = best
    b0 = int(top.bin_start)
    G[3] = _box(lang,
                (f"작곡가 {len(shown)}명 가운데 연주와 작품면의 차이가 가장 큰 곳은 {name(c)}의 {b0}~{b0 + 4}년 작품이다. 그 시기 작품이 작품면의 {top.works_share:.0%}인데 뉴욕 필 연주(연도까지 매칭된 것)의 {top.nyphil_share:.0%}를 차지한다." if ko else
                 f"Among the {len(shown)} composers shown, the largest gap is {name(c)}'s works of {b0}–{b0 + 4}: {top.works_share:.0%} of the work pages but {top.nyphil_share:.0%} of NY Phil performances matched to a dated page."),
                ("한 오케스트라의 기록이고, 작곡 연도까지 매칭된 연주만 센다." if ko else "One orchestra's record, counting only performances matched to a dated page."))

    # 4 — orchestration: decade medians (decades with at least five symphonies)
    dec = SY.assign(dec=(SY.year_start // 10) * 10).groupby("dec")["orch_parts"].agg(["median", "size"])
    dec = dec[dec["size"] >= 5]
    d0, d1 = dec.index[0], dec.index[-1]
    mx = SY.loc[SY.orch_parts.idxmax()]
    mx_title = re.sub(r"No\.(?=\d)", "No. ", str(mx.work_title))  # 'Symphony No.2' -> 'Symphony No. 2' in running text
    last = SY[(SY.year_start // 10) * 10 == d1]
    vc = last.composer.value_counts()
    lead_c, lead_n = vc.index[0], int(vc.iloc[0])
    heavy = lead_n / len(last) >= 0.75  # one composer dominates the decade
    note_ko = f"({int(d1)}년대 {len(last)}곡 가운데 {lead_n}곡이 {name(lead_c)})" if heavy else ""
    note_en = f" ({lead_n} of the {len(last)} in the {int(d1)}s are by {name(lead_c)})" if heavy else ""
    G[4] = _box(lang,
                (f"교향곡이 5곡 이상인 10년 구간의 중앙값은 {int(d0)}년대 {dec.loc[d0, 'median']:.0f}파트에서 {int(d1)}년대 {dec.loc[d1, 'median']:.0f}파트로{note_ko}. 가장 많은 곡은 {name(mx.composer)} 「{mx_title}」({int(mx.orch_parts)}파트)." if ko else
                 f"In decades with at least five symphonies, the median goes from {dec.loc[d0, 'median']:.0f} parts in the {int(d0)}s to {dec.loc[d1, 'median']:.0f} in the {int(d1)}s{note_en}. The largest is {name(mx.composer)}'s {mx_title} ({int(mx.orch_parts)} parts)."),
                ("편성란에 적힌 비현악 파트 수라 연주자 수나 악보의 실제 파트 수와 같다는 보장은 없다." if ko else
                 "Non-string parts as listed on the page; this need not equal the number of players or parts in the score."))

    # 5 — tempo markings: fast+very fast share, first vs last shown bin; non-Italian share
    fastish = TP[TP.tempo_class.isin(["fast", "very fast"])].groupby("bin")["share"].sum()
    slowish = TP[TP.tempo_class.isin(["slow", "moderately slow"])].groupby("bin")["share"].sum()
    a, z = okb[0], okb[-1]
    tl = TL.set_index("bin")
    ni_pk = tl.loc[okb, "non_italian_share"].idxmax()
    G[5] = _box(lang,
                (f"템포어가 인식된 줄 가운데(인식 20줄·인식률 60% 이상인 첫 구간과 마지막 구간) 「빠름·매우 빠름」의 비율은 {a}~{a + 24}년 {fastish.get(a, 0):.0%}, {z}~{z + 24}년 {fastish.get(z, 0):.0%}이고, 「느림·보통 느림」은 {slowish.get(a, 0):.0%}, {slowish.get(z, 0):.0%}다. 이탈리아어가 아닌 템포어는 {int(ni_pk)}~{int(ni_pk) + 24}년에 {tl.loc[ni_pk, 'non_italian_share']:.0%}로 가장 많다." if ko else
                 f"Among lines with a recognized tempo word (first and last bins with at least 20 recognized lines and 60% recognition), fast or very fast: {fastish.get(a, 0):.0%} in {a}–{a + 24}, {fastish.get(z, 0):.0%} in {z}–{z + 24}; slow or moderately slow: {slowish.get(a, 0):.0%} and {slowish.get(z, 0):.0%}. Non-Italian tempo words peak at {tl.loc[ni_pk, 'non_italian_share']:.0%} in {int(ni_pk)}–{int(ni_pk) + 24}."),
                ("적힌 지시어의 구성이지 연주 속도(BPM)가 아니다. 느린 서주가 있는 악장은 서주의 템포어로 잡힌다." if ko else
                 "The make-up of written markings, not performed speed (BPM). A movement with a slow introduction is classed by the introduction."))

    # 6 — instrument use: instruments named in at least half of the symphonies, first vs last bin; biggest rise
    iu = IU[IU.bin.isin(okb2)].pivot(index="instrument", columns="bin", values="share")
    a, z = okb2[0], okb2[-1]
    na, nz = int((iu[a] >= 0.5).sum()), int((iu[z] >= 0.5).sum())
    rise = (iu[z] - iu[a]).sort_values(ascending=False)
    r1, r2 = rise.index[0], rise.index[1]
    G[6] = _box(lang,
                (f"교향곡의 절반 이상에 이름이 오른 악기는 {a}~{a + 24}년 {na}개, {z}~{z + 24}년 {nz}개. 비율이 가장 크게 늘어난 악기는 {josa(iname(r1), '과와')} {josa(iname(r2), ('이', ''))}다({iu.loc[r1, a]:.0%} → {iu.loc[r1, z]:.0%}, {iu.loc[r2, a]:.0%} → {iu.loc[r2, z]:.0%})." if ko else
                 f"Instruments named in at least half the symphonies: {na} in {a}–{a + 24}, {nz} in {z}–{z + 24}. The biggest rises are {iname(r1)} ({iu.loc[r1, a]:.0%} → {iu.loc[r1, z]:.0%}) and {iname(r2)} ({iu.loc[r2, a]:.0%} → {iu.loc[r2, z]:.0%})."),
                ("편성 상세가 있는 면만 들어가 전체 교향곡의 확률 표본이 아니고, 선택·겸용 악기도 「적힘」으로 셌다." if ko else
                 "Only pages with instrumentation details are included, so this is not a probability sample, and optional or doubling instruments count as named."))

    # 7 — pitch of a': 25-year medians (bins with five or more points)
    ed = EP.dropna(subset=["year"])
    med = ed.groupby((ed.year // 25) * 25)["vib"].agg(["median", "size"])
    med = med[med["size"] >= 5]
    lo_b, hi_b = med["median"].idxmin(), med["median"].idxmax()
    G[7] = _box(lang,
                (f"25년 구간 중앙값(5점 이상)은 {int(lo_b)}~{int(lo_b) + 24}년 {med.loc[lo_b, 'median']:.1f} Hz가 가장 낮고 {int(hi_b)}~{int(hi_b) + 24}년 {med.loc[hi_b, 'median']:.1f} Hz가 가장 높다. 연도가 있는 기록은 {len(ed)}건." if ko else
                 f"Among 25-year medians (five or more points), the lowest is {med.loc[lo_b, 'median']:.1f} Hz in {int(lo_b)}–{int(lo_b) + 24} and the highest {med.loc[hi_b, 'median']:.1f} Hz in {int(hi_b)}–{int(hi_b) + 24}. {len(ed)} records carry a date."),
                ("Ellis가 모은 기록의 분포이지 각 시대의 「표준」이 아니고, 같은 시기에도 장소와 용도에 따라 100 Hz 넘게 벌어진다." if ko else
                 "The spread of the records Ellis collected, not each era's 'standard'; pitches of the same period differ by more than 100 Hz depending on place and use."))
    return G
