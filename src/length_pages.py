"""Reading page, section 2.1 (1.18): conductors added through track lengths.

Every number in the text is computed here from data/derived/beethoven_length_*.csv.
"""
from __future__ import annotations

import html

import pandas as pd

esc = html.escape

# Korean labels (surnames; initials where two people could be confused). bmetr keys are "Surname, Given".
KO = {
    "Abbado": "아바도", "Barenboim": "바렌보임", "Bernstein": "번스타인", "Böhm": "뵘", "Brüggen": "브뤼헨", "Chailly": "샤이",
    "Cluytens": "클뤼탕스", "Davis": "콜린 데이비스", "Ferencsik": "페렌치크", "Furtwängler": "푸르트뱅글러", "Gardiner": "가디너",
    "Gielen": "길렌", "Haitink": "하이팅크", "Harnoncourt": "아르농쿠르", "Hickox": "히콕스", "Hogwood": "호그우드", "Hugget": "허깃·굿맨",
    "Immerseel": "반 이메르세일", "Jochum": "요훔", "Karajan": "카라얀", "Kegel": "케겔", "Klemperer": "클렘페러",
    "Leinsdorf": "라인스도르프", "Masur": "마주어", "Mengelberg": "멩엘베르흐", "Muti": "무티", "Norrington": "노링턴",
    "Pletnev": "플레트뇨프", "Polizzi": "폴리치", "Rattle": "래틀", "Solti": "솔티", "Szell": "셀", "Toscanini": "토스카니니",
    "Tremblay": "트랑블레", "Walter": "발터", "Wand": "반트",
    # added in 1.18
    "Maazel": "마젤", "Celibidache": "첼리비다케", "Thielemann": "틸레만", "Sawallisch": "자발리슈", "Järvi": "파보 예르비",
    "Jordan": "필리프 조르당", "Ansermet": "앙세르메", "Vänskä": "벤스케", "Jansons": "얀손스", "Dudamel": "두다멜",
    "Herreweghe": "헤레베허", "Steinberg": "스타인버그", "Schuricht": "슈리히트", "Fischer": "아담 피셔", "Kletzki": "클레츠키",
    "Blomstedt": "블롬슈테트", "Ozawa": "오자와", "Savall": "사발", "Mackerras": "매케러스", "Ormandy": "오먼디",
    "Doráti": "도라티", "Giulini": "줄리니", "Nelsons": "넬손스", "Janowski": "야노프스키", "Kempe": "켐페",
    "Dohnányi": "도흐나니", "Scherchen": "셰르헨", "Sanderling": "잔덜링", "Konwitschny": "콘비츠니", "Suitner": "주이트너",
    "Krips": "크립스", "Nézet-Séguin": "네제세갱", "Kubelík": "쿠벨리크", "Weingartner": "바인가르트너", "Monteux": "몽퇴", "Thomas": "틸슨 토머스",
}
EN_INITIAL = {"Davis": "C. Davis", "Järvi": "P. Järvi", "Jordan": "P. Jordan", "Fischer": "Á. Fischer", "Hugget": "Huggett & Goodman", "Thomas": "Tilson Thomas"}
ORCH_KO = {"London Symphony Orchestra": "런던 교향악단", "Royal Philharmonic Orchestra": "로열 필하모닉 관현악단",
           "Koninklijk Concertgebouworkest": "로열 콘세르트헤바우 관현악단", "Wiener Philharmoniker": "빈 필하모닉",
           "Bayerisches Staatsorchester": "바이에른 국립 관현악단", "Philharmonisches Staatsorchester Bremen": "브레멘 필하모닉 국립 관현악단",
           "Münchner Philharmoniker": "뮌헨 필하모닉", "hr‐Sinfonieorchester": "헤센 방송 교향악단", "hr-Sinfonieorchester": "헤센 방송 교향악단",
           "Berliner Philharmoniker": "베를린 필하모닉", "London Philharmonic Orchestra": "런던 필하모닉 관현악단",
           "Staatskapelle Dresden": "드레스덴 슈타츠카펠레", "Seoul Philharmonic Orchestra": "서울시립교향악단",
           "New York Philharmonic": "뉴욕 필하모닉", "Symphonieorchester des Bayerischen Rundfunks": "바이에른 방송 교향악단", "Chicago Symphony Orchestra": "시카고 교향악단", "NDR Elbphilharmonie Orchester": "NDR 엘프필하모니 관현악단", "התזמורת הפילהרמונית הישראלית": "이스라엘 필하모닉 관현악단"}
ORCH_EN = {"התזמורת הפילהרמונית הישראלית": "Israel Philharmonic Orchestra", "hr‐Sinfonieorchester": "hr-Sinfonieorchester"}
# rows of the partial table whose official issue could not be confirmed from a primary source (Codex 117 T3.8)
UNCONFIRMED_ISSUE = {("Q160706", 5, 2, "Chicago Symphony Orchestra")}
INNER_KO = {(2, 2): "2번 2악장", (3, 2): "3번 2악장", (4, 2): "4번 2악장", (5, 2): "5번 2악장", (6, 2): "6번 2악장", (7, 2): "7번 2악장", (8, 2): "8번 2악장"}


def josa(word: str, pair=("은", "는")) -> str:
    """Attach the Korean particle that fits the last syllable (은/는, 이/가, 을/를, 과/와, 으로/로)."""
    ch = word.rstrip(" ○")[-1:]
    if "가" <= ch <= "힣":
        has = (ord(ch) - 0xAC00) % 28
        if pair == ("으로", "로"):
            return word + ("로" if has in (0, 8) else "으로")
        return word + (pair[0] if has else pair[1])
    return word + pair[1]


def josa_num(num: str, pair=("은", "는")) -> str:
    """Particle after a number read in Korean (0 영, 1 일, 3 삼, 6 육, 7 칠, 8 팔 end in a consonant)."""
    return num + (pair[0] if num[-1:] in "013678" else pair[1])


def neg(x: float, spec: str = ".1f") -> str:
    return format(x, spec).replace("-", "−")


def join(names, lang: str) -> str:
    names = list(names)
    if lang == "ko":
        return " · ".join(names)
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def surname(c: str) -> str:
    if "," in c:
        return c.split(",")[0].strip()
    return c.replace("von ", "").split()[-1]


def label(c: str, lang: str) -> str:
    s = surname(c)
    if lang == "ko":
        return KO.get(s, s)
    return EN_INITIAL.get(s, s)


def load(D):
    I = pd.read_csv(D / "beethoven_length_index.csv", keep_default_na=False)
    for c in ("k_median", "k_q1", "k_q3"):
        I[c] = I[c].astype(float)
    S = pd.read_csv(D / "beethoven_length_candidates.csv", keep_default_na=False)
    M = pd.read_csv(D / "beethoven_length_movements.csv", keep_default_na=False)
    V = pd.read_csv(D / "beethoven_length_checks.csv", keep_default_na=False).set_index(["check", "movements"])
    P = pd.read_csv(D / "beethoven_length_pipeline.csv")
    return I, S, M, V, P


def numbers(D) -> dict:
    I, S, M, V, P = load(D)
    new, old = I[I.source == "musicbrainz"], I[I.source == "bmetr"]
    v = lambda k, m, col="value": float(V.loc[(k, m), col])  # noqa: E731
    slow, fast = I.iloc[0], I.iloc[-1]
    return dict(
        n_all=len(I), n_new=len(new), n_old=len(old), n_req=int(new.requested.astype(str).eq("True").sum()),
        n_gen=int((~new.requested.astype(str).eq("True")).sum()), all_below_1=bool((I.k_median < 1).all()),
        med_new=new.k_median.median(), med_old=old.k_median.median(),
        slow=slow.conductor, slow_k=slow.k_median, fast=fast.conductor, fast_k=fast.k_median,
        rho7=v("audio_vs_length", "inner7"), lo7=v("audio_vs_length", "inner7", "lo"), hi7=v("audio_vs_length", "inner7", "hi"),
        rho11=v("audio_vs_length", "repeat_free11"), rho33a=v("audio_vs_length", "all33_no_repeats"), rho33b=v("audio_vs_length", "all33_with_repeats"),
        gap_mean=v("rank_gap_inner7", "inner7"), gap_max=v("rank_gap_inner7", "inner7", "hi"),
        bc_n=int(v("barcode_same_recording", "inner7", "n")), bc_tracks=int(v("barcode_same_recording", "inner7", "n_tracks")),
        bc_med=v("barcode_same_recording", "inner7"), bc_q1=v("barcode_same_recording", "inner7", "lo"), bc_q3=v("barcode_same_recording", "inner7", "hi"),
        bc_10=v("barcode_same_recording", "inner7", "share_within_10s"), bc_max=v("barcode_same_recording", "inner7", "max_abs_rel"),
        bc_off=V.loc[("barcode_same_recording", "inner7"), "excluded"], bc_found=int(v("barcode_all", "inner7", "n")),
        pipe_n=len(P), pipe_ok=int((P["diff"].abs() < 0.02).sum()), pipe_off=list(P[P["diff"].abs() >= 0.02].bmetr_conductor),
        n_dropped=int(v("dropped_implausible", "inner7", "n")),
        bc_short=short_barcode(D, V.loc[("barcode_same_recording", "inner7"), "excluded"]),
        thiel=float(I[I.conductor == "Christian Thielemann"].k_median.iloc[0]),
        **repeat_growth(D), **mv_medians(M),
    )


def short_barcode(D, excluded: str) -> list:
    """Conductors whose matched release carries fewer than seven of the movements: (conductor, n)."""
    B = pd.read_csv(D / "beethoven_length_barcode.csv")
    B = B[~B.conductor.isin([c for c in str(excluded).split(";") if c])]
    n = B.groupby("conductor").size()
    return [(c, int(k)) for c, k in n.items() if k < 7]


def repeat_growth(D) -> dict:
    """How much taking every repeat lengthens a movement that has repeat signs (theoretical durations, bmetr marks)."""
    m = pd.read_csv(D / "beethoven_symphony_marks.csv")
    m = m[m.symphony <= 8]
    g = m.groupby(["symphony", "movement"])[["theo_no_rep_s", "theo_with_rep_s"]].sum()
    r = (g.theo_with_rep_s / g.theo_no_rep_s - 1)
    r = r[r > 0]
    return dict(rep_n=len(r), rep_min=r.min(), rep_max=r.max(), rep_med=r.median(), rep_q1=r.quantile(.25), rep_q3=r.quantile(.75))


def mv_medians(M) -> dict:
    b = M[M.source == "bmetr"].copy()
    b["k"] = b.k.astype(float)
    med = b.groupby(["symphony", "movement"]).k.median()
    return dict(med_4_2=med[(4, 2)], med_8_2=med[(8, 2)])


def svg_dots(items, width=900, row_h=19, lo=0.6, hi=1.02, xlabel="", mark_label=""):
    """items: (label, median, q1, q3, slot or None). slot None = hollow (track length only, added in 1.18)."""
    label_w = max(150, int(max(len(n) for n, *_ in items) * 7.6) + 16)
    pw = width - label_w - 24
    h = row_h * len(items) + 50
    X = lambda v: label_w + (v - lo) / (hi - lo) * pw  # noqa: E731
    out = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="dot chart">']
    t = lo
    while t <= hi + 1e-9:
        out.append(f'<line class="grid" x1="{X(t):.1f}" y1="6" x2="{X(t):.1f}" y2="{h-40}"/><text x="{X(t):.1f}" y="{h-26}" text-anchor="middle">{t:.1f}</text>')
        t = round(t + 0.1, 10)
    out.append(f'<line class="ax" x1="{X(1):.1f}" y1="6" x2="{X(1):.1f}" y2="{h-40}" stroke="var(--fg2)" stroke-dasharray="4 3"/>')
    if mark_label:
        out.append(f'<text x="{X(1)-4:.1f}" y="14" text-anchor="end">{esc(mark_label)}</text>')   # top right: the slowest rows sit far left
    if xlabel:
        out.append(f'<text x="{label_w+pw/2:.0f}" y="{h-8}" text-anchor="middle">{esc(xlabel)}</text>')
    for i, (name, med, q1, q3, slot, tip) in enumerate(items):
        y = 8 + i * row_h + row_h / 2
        col = "var(--fg2)" if slot is None else f"var(--s{slot+1})"
        out.append(f'<text x="{label_w-8}" y="{y+4:.1f}" text-anchor="end">{esc(name)}</text>')
        out.append(f'<line x1="{X(q1):.1f}" y1="{y:.1f}" x2="{X(q3):.1f}" y2="{y:.1f}" stroke="{col}" stroke-width="2" stroke-opacity=".55"/>')
        fill = "var(--card)" if slot is None else col
        out.append(f'<circle cx="{X(med):.1f}" cy="{y:.1f}" r="4.6" fill="{fill}" stroke="{col}" stroke-width="1.8"><title>{esc(tip)}</title></circle>')
    out.append("</svg>")
    return "".join(out)


def section(lang: str, D, ptype_color: dict, ptype_name: dict) -> str:
    ko = lang == "ko"
    I, S, M, V, P = load(D)
    n = numbers(D)
    f2 = lambda x: f"{x:.2f}"  # noqa: E731
    items = []
    for r in I.itertuples():
        nm = label(r.conductor, lang)
        if r.source == "bmetr":
            slot = ptype_color[r.ptype]
            tip = f"{nm} ({ptype_name[r.ptype]}) — {f2(r.k_median)} [{f2(r.k_q1)}, {f2(r.k_q3)}]"
        else:
            slot = None
            tip = (f"{nm} (길이만) — {f2(r.k_median)} [{f2(r.k_q1)}, {f2(r.k_q3)}]" if ko else f"{nm} (length only) — {f2(r.k_median)} [{f2(r.k_q1)}, {f2(r.k_q3)}]")
            nm = nm + " ○"
        items.append((nm, r.k_median, r.k_q1, r.k_q3, slot, tip))
    xlabel = ("길이로 잰 속도 (표기 = 1) · 오른쪽일수록 빠름" if ko else "speed from track length (marks = 1) · further right is faster")
    fig = svg_dots(items, xlabel=xlabel, mark_label=("점선 = 표기대로" if ko else "dashed = as marked"))
    lg = '<div class="legend">' + "".join(f'<span style="--c:var(--s{v+1})">{esc(ptype_name[k])} (bmetr)</span>' for k, v in ptype_color.items())
    lg += ('<span class="hollow">' + ("○ 이번에 더한 지휘자 — 트랙 길이만(MusicBrainz)" if ko else "○ added in 1.18 — track length only (MusicBrainz)") + "</span></div>")
    sl, fa = label(n["slow"], lang), label(n["fast"], lang)
    import fig_notes  # noqa: E402  (1.22.3: chart notes)
    _top = items[0]
    fnote = dict(
        intro=("지휘자마다 교향곡 2~8번 2악장 일곱을 메트로놈 표기 속도의 몇 배로 연주했는지, 트랙 길이로 재서 한 줄씩 그린 그림이다." if ko else
               "For each conductor, the speed of the seven second movements of Symphonies 2–8 as a fraction of the marked speed, measured from track lengths, one row each."),
        one=(f"맨 위 줄 {esc(_top[0])}의 점은 {f2(_top[1])}에 있다. 일곱 악장의 가운데 값이 표기 속도의 {_top[1]:.0%}, 곧 표기대로라면 걸릴 시간의 {1 / _top[1]:.2f}배가 걸렸다는 뜻이다. 가로선은 {f2(_top[2])}에서 {f2(_top[3])}까지다." if ko else
             f"The top row, {esc(_top[0])}, has its dot at {f2(_top[1])}: the middle of its seven movements runs at {_top[1]:.0%} of the marked speed, taking {1 / _top[1]:.2f} times as long as the marks imply. Its line runs from {f2(_top[2])} to {f2(_top[3])}."),
        mis=(f"트랙 길이에는 쉼·페르마타·앞뒤 무음이 들어 있어 박 하나하나의 속도와 같지 않다. 같은 지휘자 {n['n_old']}명을 음원 템포로 잰 순서와 순위 상관 {f2(n['rho7'])}이라, 순위 몇 자리 차이는 읽지 않는다(음원 템포 쪽은 교향곡 1~8번 전 악장의 끝부분에서 잰 값이라 견주는 악장이 같지 않다). 막대처럼 보이는 가로선은 일곱 악장 가운데 절반이 놓인 범위이지 오차 막대가 아니다." if ko else
             f"Track lengths include rests, fermatas and silence at the ends, so this is not the beat-by-beat tempo. For the same {n['n_old']} conductors its order matches the audio tempo with a rank correlation of {f2(n['rho7'])}, so do not read differences of a few places (the audio tempo is measured at the ends of all movements of Symphonies 1–8, so the movements compared are not the same). The horizontal line is the range of the middle half of the seven movements, not an error bar."))

    # partial table: every distinct performance in MusicBrainz (owner decision 11-16)
    PA = pd.read_csv(D / "beethoven_length_partial.csv", keep_default_na=False)
    for c in ("k", "median_k_36", "rel_to_36", "length_s", "length_min_s", "length_max_s"):
        PA[c] = PA[c].astype(float)
    rows = []
    order = PA.drop_duplicates("wikidata_q").sort_values("name_ko" if ko else "name_en").wikidata_q
    for q in order:
        g = PA[PA.wikidata_q == q]
        nm = g.name_ko.iloc[0] if ko else g.name_en.iloc[0]
        first_c = True
        for (sy, mv), gm in g.groupby(["symphony", "movement"], sort=True):
            first_m = True
            for x in gm.itertuples():
                mvs = (INNER_KO[(sy, mv)] if ko else f"No. {sy}, II") if first_m else ""
                yr = str(int(float(x.year))) if x.year != "" else ("연도 미상" if ko else "year n/a")
                parts = [o for o in x.orchestra.split("; ") if o]
                orch = esc(" / ".join((ORCH_KO if ko else ORCH_EN).get(o, o) for o in parts)) + (" ※" if len(parts) > 1 else "")
                if (x.wikidata_q, x.symphony, x.movement, x.orchestra) in UNCONFIRMED_ISSUE:
                    orch += " ‡"
                dis = str(x.records_disagree) == "True"
                kcell = f2(x.k) + (f" †({x.length_min_s:.0f}~{x.length_max_s:.0f}초)" if ko else f" †({x.length_min_s:.0f}–{x.length_max_s:.0f} s)") if dis else f2(x.k)
                rows.append(f"<tr><td>{esc(nm) if first_c else ''}</td><td>{mvs}</td><td>{orch}, {yr}</td><td class='num'>{kcell}</td><td class='num'>{f2(x.median_k_36) if first_m else ''}</td><td class='num'>{f2(x.rel_to_36)}</td></tr>")
                first_c = first_m = False
    th = (("지휘자", "악장", "관현악단 · 녹음 해", "길이로 잰 속도", f"같은 악장 {n['n_old']}명 중앙값", f"{n['n_old']}명 대비") if ko else
          ("Conductor", "Movement", "Orchestra · year", "Speed from length", f"Median of the {n['n_old']}, same movement", f"vs the {n['n_old']}"))
    table = "<div class='wrap'><table><thead><tr>" + "".join(f"<th{' class=num' if i >= 3 else ''}>{h}</th>" for i, h in enumerate(th)) + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>"
    notes = []
    if "※" in "".join(rows):
        notes.append("※ MusicBrainz에 한 녹음이 두 악단에 함께 이어져 있다. 자료 그대로 옮겼다." if ko else "※ MusicBrainz links this one recording to two orchestras; shown as recorded there.")
    if "†" in "".join(rows):
        notes.append("† 같은 악단 · 같은 해의 기록이 MusicBrainz에 둘 이상 있고 길이가 2% 넘게 다르다. 값은 기록 길이의 중앙값으로 냈고, 괄호는 기록 길이의 범위다." if ko else
                     "† MusicBrainz has more than one record for this orchestra and year, and their lengths differ by more than 2%. The value uses the median length; the range of the records is in parentheses.")
    if "‡" in "".join(rows):
        notes.append("‡ MusicBrainz에는 실려 있으나 정식 발매 녹음인지 1차 자료로 확인하지 못했다." if ko else
                     "‡ Listed in MusicBrainz, but we could not confirm from a primary source that this recording was officially issued.")
    table += "".join(f"<p class='src'>{esc(t)}</p>" for t in notes)
    n_perf, n_cond_p = len(PA), PA.wikidata_q.nunique()
    none_req = S[S.requested.astype(str).eq("True") & S.bmetr_conductor.eq("") & S.status.eq("none")]
    none_names = join((none_req.name_ko if ko else none_req.name_en).tolist(), lang)

    on_fig = set(S[S.on_figure.astype(str).eq("True")].wikidata_q)
    new_rows = M[(M.source == "musicbrainz") & M.wikidata_q.isin(on_fig)]
    fb = new_rows[new_rows.release_group == ""]
    fb_names = [label(c, lang) for c in sorted(set(fb.name_en))]
    fb_wide = []
    for c, g in fb.groupby("name_en"):
        ys = sorted({int(float(y)) for y in g.link_year if y != ""})
        if ys and ys[-1] - ys[0] > 10:
            fb_wide.append((label(c, lang), ys[0], ys[-1]))
    several = S[(S.status == "several_orchestras") & S.bmetr_conductor.eq("")]
    several_names = join([label(c, lang) for c in several.name_en], lang)
    missing = S[(S.status == "orchestra_missing") & S.bmetr_conductor.eq("")]
    missing_names = join([label(c, lang) for c in missing.name_en], lang)
    fb_ko = (f" 묶음 없이 악장마다 모은 {josa(join(fb_names, 'ko'))} 한 악단 조건은 맞지만 한 번의 전집 녹음이라는 보장은 없다"
             + ("(" + ", ".join(f"{josa(nm)} {a}~{b}년 녹음이 섞여 있다" for nm, a, b in fb_wide) + ")" if fb_wide else "") + ".") if fb_names else ""
    fb_en = (f" {join(fb_names, 'en')}, whose movements were gathered one by one without a boxed set, meet the one-orchestra condition but are not guaranteed to be a single cycle"
             + (" (" + ", ".join(f"{nm}'s recordings span {a}–{b}" for nm, a, b in fb_wide) + ")" if fb_wide else "") + ".") if fb_names else ""
    same = f2(n["med_new"]) == f2(n["med_old"])
    medline_ko = (f"새로 더한 {n['n_new']}명과 기존 {n['n_old']}명의 중앙값은 둘 다 {f2(n['med_new'])}이다." if same else
                  f"새로 더한 {n['n_new']}명의 중앙값은 {f2(n['med_new'])}, 기존 {n['n_old']}명은 {f2(n['med_old'])}이다.")
    medline_en = (f"The median is {f2(n['med_new'])} for both the {n['n_new']} added conductors and the original {n['n_old']}." if same else
                  f"The median is {f2(n['med_new'])} for the {n['n_new']} added conductors and {f2(n['med_old'])} for the original {n['n_old']}.")
    glance = ("<aside class='glance'><p class='glance-h'>" + ("한눈에 보기" if ko else "At a glance") + "</p><dl>"
              + (f"<dt>무엇을 보나</dt><dd>교향곡 2~8번의 2악장 일곱을 지휘자가 메트로놈 표기대로라면 걸릴 시간보다 얼마나 오래 연주했는지를, 녹음 트랙의 길이로 잰다. 지휘자 {n['n_old']}명(음원 측정 자료가 있는 bmetr)에 {n['n_new']}명을 더했다.</dd>"
                 f"<dt>데이터가 보여 주는 것</dt><dd>{n['n_all']}명의 지휘자별 중앙값이 {'모두' if n['all_below_1'] else '대부분'} 1보다 작다 — 표기보다 오래 걸렸다. 가장 느린 {josa(sl)} {f2(n['slow_k'])}(표기대로라면 걸릴 시간의 {1/n['slow_k']:.2f}배), 가장 빠른 {josa(fa)} {josa_num(f2(n['fast_k']), ('이다', '다'))}. {medline_ko}</dd>"
                 f"<dt>주의할 점</dt><dd>길이로 잰 값은 음원에서 잰 템포와 지휘자 순서가 대체로 같지만(순위 상관 {f2(n['rho7'])}) 순위 몇 자리 차이는 읽지 않는다. 새 지휘자는 길이로만 쟀다. 악장 하나하나는 1을 넘을 수도 있다.</dd>"
                 if ko else
                 f"<dt>What this shows</dt><dd>How much longer than the time implied by Beethoven's metronome marks conductors take the seven second movements of Symphonies 2–8, measured from track lengths. To the {n['n_old']} conductors with audio measurements (bmetr) it adds {n['n_new']}.</dd>"
                 f"<dt>What the data show</dt><dd>{'All' if n['all_below_1'] else 'Most'} {n['n_all']} conductor medians are below 1 — longer than the marks imply. The slowest, {sl}, is at {f2(n['slow_k'])} ({1/n['slow_k']:.2f} times the marked time); the fastest, {fa}, at {f2(n['fast_k'])}. {medline_en}</dd>"
                 f"<dt>Watch for</dt><dd>The length measure orders conductors much as the audio tempo does (rank correlation {f2(n['rho7'])}), but not exactly; do not read differences of a few places. The added conductors are measured by length only. Single movements can be above 1.</dd>")
              + "</dl></aside>")

    if ko:
        body = f"""<h3 id="s2-1">2-1. 트랙 길이로 더한 지휘자 — {n['n_old']}명에 {n['n_new']}명</h3>
{glance}
<p>위 그림은 Martín-Castro와 Ucar가 논문과 함께 공개한 자료 꾸러미 bmetr(이하 bmetr)의 템포, 곧 저자들이 음원에서 잰 값이라서, 그 자료에 없는 지휘자는 같은 방법으로 더할 수 없다. 대신 <b>트랙 길이</b>는 음원 없이도 알 수 있다. 악장을 메트로놈 표기대로 연주했을 때 걸릴 시간(악보의 마디 수 × 박 수 ÷ 메트로놈 숫자)을 실제 트랙 길이로 나누면, 그 녹음이 표기 속도의 몇 배에 해당하는지가 나온다. 쉼 · 페르마타 · 트랙 앞뒤의 무음까지 들어간 실효 값이라 박자 하나하나의 속도와는 다르다. <b>1이면 표기대로, 0.80이면 표기 속도의 80%</b>로, 같은 악장을 1.25배(1 ÷ 0.80) 시간 동안 연주했다는 뜻이다. 1보다 크면 표기보다 빠르다는 뜻인데, 이 절의 지휘자 가운데 중앙값이 1을 넘는 사람은 없다.</p>
<p>모든 악장을 쓰지 않는다. 반복 기호가 있는 악장은 반복을 모두 하면 메트로놈 이론 길이가 악장에 따라 {n['rep_min']:.0%}에서 {n['rep_max']:.0%}까지(중앙값 {n['rep_med']:.0%}) 늘어나는데, 지휘자가 반복을 했는지는 자료에 없다. 그래서 bmetr 악보 자료에서 반복 기호가 없는 악장 열하나만 고르고, 그 가운데 피날레(마지막 악장) 셋(실황 녹음 끝의 박수, 음반 마지막 트랙 뒤의 긴 무음을 피하려고)과 피날레로 쉬지 않고 이어지는 6번 4악장(폭풍, 트랙을 어디서 끊는지가 음반마다 다를 수 있다)을 뺐다. 남는 일곱은 공교롭게 모두 2악장이다(교향곡 2~8번에 하나씩). 1번은 네 악장 모두 반복 기호가 있어 빠진다.</p>
<p><b>36명으로 먼저 시험했다.</b> 같은 36명을 이 길이 지수로 줄 세운 순서와 음원 템포로 줄 세운 순서의 스피어먼 순위 상관(두 줄 세우기가 얼마나 같은 순서인지를 −1~1로 나타낸 값, 1이면 순서가 완전히 같다)은 {f2(n['rho7'])}이다. 지휘자 36명을 무작위로 다시 뽑아 2,000번 다시 계산하면(부트스트랩) 가운데 95%가 {f2(n['lo7'])}~{f2(n['hi7'])} 사이에 든다. 표본이 달랐다면 이 정도 범위에서 움직였으리라는 뜻이다. 이 구간은 지휘자를 달리 뽑았을 때의 흔들림만 담고, 트랙을 잘못 이었거나 다른 녹음을 고른 오류는 담지 않는다. 반복 기호가 있는 악장까지 33악장을 다 쓰면 {f2(n['rho33a'])}(반복을 하지 않았다고 볼 때)~{f2(n['rho33b'])}(했다고 볼 때)로 떨어진다. 순위 차이는 평균 {n['gap_mean']:.1f}자리, 가장 큰 경우 {n['gap_max']:.0f}자리였다. 두 값은 같은 것을 재지 않는다 — 음원 템포는 악장 끝 한 구간의 박자 속도이고, 길이 지수는 리타르단도(점점 느리게)와 페르마타(늘임표)까지 들어간 악장 전체의 시간이다.</p>
<p><b>새 지휘자의 트랙 길이</b>는 MusicBrainz(공동 편집 음반 데이터베이스, 핵심 자료는 저작권 조건 없이 쓸 수 있는 CC0)의 데이터 덤프에서 가져왔다. 자료원이 같은 자로 재는지 보려고, bmetr 음반의 바코드로 MusicBrainz에서 같은 음반을 찾았다({n['bc_found']}명. 바코드가 같은 음반이 여럿이면 일곱 악장이 가장 많이 실린 음반, 같으면 식별자가 앞선 음반 하나로 견줬고, 한 음반에 같은 악장 녹음이 둘이면 식별자가 앞선 녹음을 썼다). 일곱 악장의 상대 길이 차이(절댓값)의 중앙값이 2%를 넘어 같은 바코드에 다른 녹음이 걸려 있는 것으로 보이는 {esc(josa(', '.join(label(c, 'ko') for c in n['bc_off'].split(';') if c), ('을', '를')))} 빼면 {n['bc_n']}명의 그 일곱 악장 {n['bc_tracks']}트랙({join([f'{label(c, "ko")} {k}' for c, k in n['bc_short']], 'ko')}악장만 실린 음반이 있어 {n['bc_n']} × 7보다 적다)에서 두 자료의 길이 차이는 중앙값 {neg(n['bc_med'], '.2f')}초(가운데 절반이 {neg(n['bc_q1'])}~{neg(n['bc_q3'])}초)이고 {n['bc_10']:.1%}가 10초 안이다. 녹음을 고르는 규칙(아래)도 36명 가운데 MusicBrainz에 한 악단 전집이 있는 {n['pipe_n']}명에 그대로 적용해 보았다. {n['pipe_ok']}명은 bmetr 값과 0.02 안에서 같았고, 어긋난 {esc(josa(join((label(c, 'ko') for c in n['pipe_off']), 'ko')))} 규칙이 bmetr 저자들과 다른 전집을 고른 경우다.</p>
<p><b>그림 읽는 법.</b> 한 줄이 지휘자 한 명의 녹음 일곱이다. 색 점은 bmetr 저자들이 쓴 전집 음반, 빈 점은 아래 규칙으로 고른 녹음이다. 점은 일곱 악장 값의 중앙값, 가로선은 일곱 값을 줄 세워 느린 쪽 4분의 1과 빠른 쪽 4분의 1을 뺀 가운데 절반의 범위(1사분위~3사분위)다. 점선이 표기대로(1.0)다. 색 점은 bmetr의 {n['n_old']}명으로, 색은 bmetr가 붙인 연주 양식이다. <b>속이 빈 점(○)은 이번에 더한 {n['n_new']}명</b>으로, 트랙 길이로만 쟀고 연주 양식은 원자료가 분류하지 않아 회색으로 두었다. 예를 들어 틸레만(빈 필, 2008~2010)의 {josa_num(f2(n['thiel']))} 일곱 악장 값의 중앙값으로, 표기대로라면 걸릴 시간의 {1/n['thiel']:.2f}배 동안 연주했다는 뜻이다.</p>
{lg}{fig_notes.fx(fig, fnote['intro'], dict(short=f"가장 느린 {sl}({f2(n['slow_k'])})부터 가장 빠른 {fa}({f2(n['fast_k'])})까지, {n['n_all']}명의 중앙값이 {'모두' if n['all_below_1'] else '대부분'} 1보다 작다.", how="한 줄이 지휘자 한 명이고 위에서부터 느린 순서다. 점은 일곱 악장 값의 중앙값, 가로선은 1사분위~3사분위다. 점선(1.0)이 표기대로이고 왼쪽일수록 느리다. 색 점은 bmetr의 지휘자(색은 연주 양식), 속이 빈 점(○)은 트랙 길이로만 잰 지휘자다. 자세한 읽는 법은 바로 위 단락에 있다.", one=fnote['one'], mis=fnote['mis']), lang)}
<p><b>녹음 고르기.</b> 후보는 엮은이가 이름을 든 세 사람(정명훈 · 틸레만 · 카를로스 클라이버)을 포함한 요청 명단과 「지휘의 계보」 명단이다. 그 가운데 <b>한 악단과 일곱 악장을 모두 녹음했다고 MusicBrainz에 올라 있는 {n['n_new']}명</b>을 그림에 넣었다(요청 명단 {n['n_req']}명, 계보 명단 {n['n_gen']}명). 트랙 길이가 적힌 음반 묶음(전집 상자) 하나에 일곱 악장이 모두 실려 있으면 그 묶음의 녹음을 쓴다. 그런 묶음이 여럿이면 일곱 녹음이 모두 같은 악단으로 적힌 묶음, 그 지휘자의 교향곡이 더 많이 실린 묶음, 음반이 더 많은 묶음, 첫 발매가 이른 묶음, MusicBrainz 식별자가 앞선 묶음 순서로 고른다. 묶음 안이든 묶음이 없을 때든 악장마다 서로 다른 음반에 가장 많이 실린 녹음을 쓰고(같으면 관계에 적힌 해가 이른 것, 그다음 식별자가 앞선 것), 묶음이 없을 때는 일곱 녹음 모두 같은 한 악단으로 적혀 있어야 그림에 넣는다(악단이 적히지 않은 녹음이 하나라도 있으면 넣지 않는다). 녹음 하나의 길이는 음반마다 한 값씩 세어 중앙값을 낸다. 같은 악장 36명 중앙값의 1.5배보다 크거나 1.5분의 1보다 작은 값은 잘못 이어진 트랙으로 보고 뺐다(녹음 {n['n_dropped']}개). 이 거름은 36명을 기준으로 삼으므로 정말로 아주 느리거나 빠른 연주를 지웠을 수도 있다.{fb_ko} 녹음 해는 MusicBrainz 관계에 적힌 해다. 녹음 기간의 첫해일 수 있고 음반사 자료와 다른 경우도 있다(워너 뮤직 재팬 음반 면은 자발리슈 3번을 1991년, 첼리비다케 5번을 1992년으로 적는다. 자발리슈 8번은 같은 회사의 두 면이 1983년과 「1991~1993년 실황」으로 엇갈린다). MusicBrainz에 없다고 녹음이 없는 것은 아니다.</p>
<p><b>일부 교향곡만 있는 지휘자</b>는 그림에 넣지 않았다. 악장마다 표기보다 느린 정도가 달라서({n['n_old']}명 중앙값이 4번 2악장은 {f2(n['med_4_2'])}, 8번 2악장은 {f2(n['med_8_2'])}), 다른 악장끼리는 견줄 수 없기 때문이다. 대신 MusicBrainz에 있는 이 지휘자들의 녹음 기록을 악장마다 모두 묶어 적고, 같은 악장의 36명 중앙값과 나란히 둔다({n_cond_p}명, 묶음 {n_perf}개). 같은 악단 · 같은 해의 기록은 한 묶음으로 둔다 — 같은 공연이라는 뜻은 아니다(같은 해에 같은 악단과 두 번 공연했을 수 있다). 해가 적히지 않은 기록은 같은 악단의 묶음 가운데 길이가 가장 가까운 묶음과 길이 차이가 2% 이내이면(그 묶음의 중앙값 기준) 거기에 넣고, 아니면 해 없는 기록끼리 2% 안의 것을 모아 「연도 미상」 묶음으로 따로 적는다. 여기서는 대표 녹음을 고르지 않으며 지휘자별 요약값도 내지 않는다. 「36명 대비」가 1보다 작으면 그 악장을 36명의 가운데보다 느리게 연주했다는 뜻이다.</p>
{table}
<p class="src">요청 명단 가운데 {esc(josa(none_names))} MusicBrainz에 베토벤 교향곡 녹음이 올라 있지 않았고, 성시연은 위키데이터 번호로 MusicBrainz 인물을 찾지 못했고, 김예훈은 계보 명단에 위키데이터 번호가 없어 맞추지 못했다(2026-11-14 덤프). MusicBrainz 자료로는 한 악단으로 일곱 악장이 갖춰지지 않는 {esc(several_names)}, 한 악장의 악단 기록이 빠진 {esc(josa(missing_names))} 「한 악단」 조건에 맞지 않아 넣지 않았다.</p>"""
    else:
        body = f"""<h3 id="s2-1">2.1 Conductors added through track lengths — {n['n_new']} more to the {n['n_old']}</h3>
{glance}
<p>The chart above uses the tempi in bmetr, the data package Martín-Castro and Ucar published with their paper, which they measured from the audio, so a conductor missing from their data cannot be added the same way. <b>Track lengths</b>, however, are known without the audio. Divide the time a movement would take at Beethoven's marks (bars × beats per bar ÷ metronome number) by the actual track length, and you get the recording's effective speed as a fraction of the marked speed. Because pauses, fermatas and silence at the ends of the track are included, it is not the beat-by-beat tempo. <b>1 means as marked; 0.80 means 80% of the marked speed</b> — the movement took 1.25 times (1 ÷ 0.80) as long. Above 1 would mean faster than marked; no conductor in this section has a median above 1.</p>
<p>Not every movement is used. Where a movement has repeat signs, taking every repeat lengthens its theoretical duration by {n['rep_min']:.0%} to {n['rep_max']:.0%} depending on the movement (median {n['rep_med']:.0%}), and whether a conductor took the repeats is not in the data. So only the eleven movements without repeat signs in bmetr's score data are kept, and of those the three finales are dropped (to avoid applause at the end of live recordings and the long silence after a disc's last track), as is No. 6/IV (the storm), which runs into the finale without a break, so discs may place the track boundary differently. The seven that remain happen to be all second movements (one each in Symphonies 2–8). Symphony 1 drops out because all four of its movements have repeat signs.</p>
<p><b>The measure was tested on the 36 first.</b> Ranking those 36 conductors by this length index and by the audio tempo gives a Spearman rank correlation (how alike two orderings are, on a scale from −1 to 1; 1 means the same order) of {f2(n['rho7'])}. Redrawing the 36 conductors at random and recomputing 2,000 times (a bootstrap), the middle 95% of the results lie between {f2(n['lo7'])} and {f2(n['hi7'])} — roughly how far the value could move with a different sample. The interval covers only that sampling variation, not errors from wrongly linked tracks or a different choice of recording. Using all 33 movements, repeats included, it falls to {f2(n['rho33a'])} (assuming no repeats) to {f2(n['rho33b'])} (assuming all repeats). Ranks differ by {n['gap_mean']:.1f} places on average and by {n['gap_max']:.0f} at most. The two do not measure the same thing: the audio tempo is the beat rate in one passage near the end of a movement; the length index is the time for the whole movement, ritardandos and fermatas included.</p>
<p><b>Track lengths for the added conductors</b> come from a data dump of MusicBrainz (a collaboratively edited music database; core data released under CC0, free of copyright conditions). To check that this source measures on the same scale, the bmetr albums were looked up in MusicBrainz by barcode ({n['bc_found']} conductors found; where several releases share the barcode, the one carrying the most of the seven movements, then the smaller identifier, is used; where a release has two recordings of a movement, the one with the smaller identifier). Leaving out {esc(', '.join(label(c, 'en') for c in n['bc_off'].split(';') if c))}, whose barcode appears to lead to a different recording (median absolute relative length difference over the seven movements above 2%), the {n['bc_tracks']} tracks of the seven movements for {n['bc_n']} conductors (fewer than {n['bc_n']} × 7 because the matched releases of {join([f'{label(c, "en")} ({k})' for c, k in n['bc_short']], 'en')} carry fewer movements) differ between the two sources by a median of {neg(n['bc_med'], '.2f')} s (middle half {neg(n['bc_q1'])} to {neg(n['bc_q3'])} s), and {n['bc_10']:.1%} are within 10 s. The rule for choosing recordings (below) was also run on the {n['pipe_n']} of the 36 who have a one-orchestra cycle in MusicBrainz: {n['pipe_ok']} match the bmetr value within 0.02; for {esc(join((label(c, 'en') for c in n['pipe_off']), 'en'))} the rule picked a different cycle from the one the bmetr authors used.</p>
<p><b>How to read the chart.</b> Each row summarizes seven recordings of one conductor: for colored dots, the cycle the bmetr authors used; for hollow dots, recordings selected by the rules below. The dot is the median of the seven movements; the line spans the middle half of the seven values, without the slowest and fastest quarter (first to third quartile). The dashed line is the marked speed (1.0). Colored dots are bmetr's {n['n_old']}, colored by the performance style bmetr assigns. <b>Hollow dots (○) are the {n['n_new']} added in 1.18</b>, measured from track length only and shown in gray because the source gives no style for them. For example, Thielemann's {f2(n['thiel'])} (Vienna Philharmonic, 2008–2010) is the median of his seven movements: {1/n['thiel']:.2f} times as long as the marks imply.</p>
{lg}{fig_notes.fx(fig, fnote['intro'], dict(short=f"From the slowest, {sl} ({f2(n['slow_k'])}), to the fastest, {fa} ({f2(n['fast_k'])}), {'all' if n['all_below_1'] else 'most'} {n['n_all']} conductor medians are below 1.", how="Each row is one conductor, slowest at the top. The dot is the median of the seven movements; the line spans the first to third quartile. The dashed line (1.0) is the marked speed; further left is slower. Colored dots are bmetr's conductors (color = performance style); hollow dots (○) are conductors measured from track length only. The paragraph just above explains more.", one=fnote['one'], mis=fnote['mis']), lang)}
<p><b>Choosing recordings.</b> Candidates came from the editor's requested names, which include the three named at the start (Myung-whun Chung, Christian Thielemann, Carlos Kleiber), and the conductor-genealogy list. The chart adds the <b>{n['n_new']} whom MusicBrainz lists as having recorded all seven movements with one orchestra</b> ({n['n_req']} from the requested names, {n['n_gen']} from the genealogy list). If one release group (a boxed cycle) with track lengths carries all seven, its recordings are used. If several do, the order of preference is: all seven credited to one orchestra; more of the conductor's symphonies; more releases; the earlier first release; the smaller MusicBrainz identifier. Within a group, or without one, each movement takes the recording found on the most distinct releases (ties: the earlier year on the relationship, then the smaller identifier); without a group, the conductor is charted only if all seven recordings are credited to one and the same orchestra (a recording with no orchestra credit rules the conductor out). A recording's length is the median over releases, one value per release. Values more than 1.5 times above, or below 1/1.5 of, the 36-conductor median of the same movement were treated as wrongly linked tracks and dropped ({n['n_dropped']} recordings); because the filter uses the 36 as its reference, it may also have removed some genuinely extreme performances.{fb_en} Recording years are those on the MusicBrainz relationships; they may be the first year of a longer period and sometimes differ from the label's information (Warner Music Japan's release pages give 1991 for Sawallisch No. 3 and 1992 for Celibidache No. 5; for Sawallisch No. 8 two pages of the same label disagree, 1983 and "live 1991–1993"). Absence from MusicBrainz does not mean a recording does not exist.</p>
<p><b>Conductors with only some of the symphonies</b> are not on the chart: movements differ in how far below the marks they are usually taken (the median of the {n['n_old']} is {f2(n['med_4_2'])} in No. 4/II and {f2(n['med_8_2'])} in No. 8/II), so values for different movements cannot be compared. Instead all of these conductors' MusicBrainz records are grouped and listed movement by movement, next to the median of the 36 for the same movement ({n_cond_p} conductors, {n_perf} groups). Records with the same orchestra and year form one group — which does not mean one concert (the same orchestra may have played the work twice that year). A record without a year joins the same-orchestra group whose length is closest, if the difference is within 2% (of that group's median); otherwise undated records within 2% of each other form their own "year n/a" group. No representative recording is chosen here and no per-conductor summary is given. A "vs the 36" value below 1 means slower than the middle of the 36 in that movement.</p>
{table}
<p class="src">Of the requested names, {esc(none_names)} have no Beethoven symphony recording in MusicBrainz, Shi-Yeon Sung could not be matched to a MusicBrainz artist through the Wikidata ID, and Kim Ye-hun has no Wikidata ID on the genealogy list to match (dump of 2026-11-14). {esc(several_names)}, whose seven movements do not come from one orchestra in the MusicBrainz data, and {esc(missing_names)}, one of whose movements has no orchestra credit, do not meet the one-orchestra condition and are not included.</p>"""
    return body
