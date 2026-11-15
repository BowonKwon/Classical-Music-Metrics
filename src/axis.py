"""Axis titles and unit names for charts (1.17).

Before 1.17 the axis of a chart carried the unit symbol only ("r", "ratio", "bits"), in English on both
language versions, and nothing said which way was "more". A chart title now reads
    metric name (unit) · further right = <what a larger value means>
with the unit and the direction in the page language. The English direction phrases are the registry's
`higher` field, except for the seven in HIGHER_EN below, where that short field says more than the formula
measures; the Korean ones are in HIGHER_KO, one per metric.
"""

UNIT_KO = {
    "ratio": "비율, 0~1", "share": "점유율", "semitones": "반음", "steps": "5도권 걸음", "bits": "비트", "quarter notes": "4분음표",
    "CV": "변동계수", "notes/♩": "4분음표당 음표 수", "notes": "음", "labels/bar": "마디당 화음 기호 수", "types/100": "기호 100개당 종류",
    "changes/100 bars": "100마디당 횟수", "changes/note": "음표당 횟수", "MIDI": "MIDI 음높이 번호", "pitch names": "음이름 수",
    "durations": "음가 종류 수", "keys": "조의 수", "cadences/100 bars": "100마디당 종지 수", "nPVI": "nPVI", "bars": "마디", "r": "상관계수 r",
    "bpm": "분당 박 수(bpm)", "×": "배", "log₂ ratio": "log₂ 비", "MIDI velocity": "MIDI 세기", "bpm/10y": "10년당 bpm",
    "share of time": "시간 비율", "share of recordings": "녹음 비율", "index": "지수, 0~1", "composers": "명", "years": "년",
    "Jaccard": "자카드 지수, 0~1", "share of works": "작품 비율",
}

# 1.17: where the registry's short `higher` says more than the formula measures, the axis uses these instead
HIGHER_EN = {
    "mean_simultaneity": "more notes starting together", "chords_per_measure": "more chord labels per bar",
    "minor_local_key_ratio": "larger share of chord labels in minor local keys", "npvi_top": "more contrast between neighboring onset intervals",
    "off_tonic_share": "more time outside the home key and its relative",
    "tempo_trend_bpm_per_decade": "the (measured − marked) difference grows more with later recordings",
    "repertoire_age_median": "more works by composers long dead",
}

HIGHER_KO = {
    "pitch_range_semitones": "음역이 넓다", "chromatic_ratio": "조표 밖 음이 많다", "pitch_class_entropy": "열두 음을 고르게 쓴다",
    "rhythm_entropy": "음가가 다양하다", "offbeat_onset_ratio": "박 사이에서 시작하는 음이 많다", "notes_per_quarter": "음표가 촘촘하다",
    "mean_simultaneity": "같은 시점에 함께 시작하는 음이 많다", "top_leap_ratio": "도약이 많다", "top_mean_interval_semitones": "선율이 크게 움직인다",
    "chords_per_measure": "마디당 화음 기호가 많다", "chord_vocabulary_per_100_labels": "화음 종류가 다양하다", "applied_chord_ratio": "부속화음이 많다",
    "seventh_chord_ratio": "7화음이 많다", "local_key_changes_per_100_measures": "조가 자주 바뀐다", "top_step_ratio": "순차 진행이 많다",
    "top_repeat_ratio": "같은 음 반복이 많다", "top_range_semitones": "선율의 음역이 넓다", "top_direction_changes_per_note": "선율 방향이 자주 꺾인다",
    "pitch_mean_midi": "음역대가 높다", "pitch_sd_midi": "음높이가 넓게 퍼져 있다", "tpc_vocabulary": "쓰는 음이름이 많다",
    "duration_vocabulary": "음가 종류가 많다", "mean_duration_qb": "음이 길다", "mean_chord_duration_qb": "화음이 오래 머문다",
    "chromatic_numeral_ratio": "반음계 화음이 많다", "inversion_ratio": "전위 화음이 많다", "local_key_vocabulary": "거치는 조가 많다",
    "minor_local_key_ratio": "단조 국소 조에 붙은 화음 기호의 비율이 높다", "cadences_per_100_measures": "종지가 잦다", "pac_ratio_of_cadences": "완전 정격 종지가 많다",
    "npvi_top": "이웃한 음 시작 간격의 대비가 크다", "post_leap_reversal": "도약 뒤 반대 방향으로 움직이는 일이 많다",
    "beat_crossing_ratio": "박을 넘기는 당김음이 많다", "motif_repeat_ratio": "같은 음형이 많이 되풀이된다", "dim7_ratio": "감7화음이 많다",
    "predominant_chromatic_ratio": "나폴리·증6화음이 많다", "pedal_ratio": "페달 포인트가 많다", "phrase_len_median": "악구가 길다",
    "phrase_4_8_ratio": "4·8마디 악구가 많다", "key_clarity": "한 조의 전형적인 음 분포와 닮았다", "outside_5oct_ratio": "5옥타브 밖 음이 많다",
    "fifth_root_motion_ratio": "5도 하행 근음 진행이 많다", "key_change_distance_median": "먼 조로 옮겨 간다",
    "departure_mean": "으뜸조에서 멀리, 오래 벗어난다", "off_tonic_share": "으뜸조·나란한조 밖에서 보내는 시간이 길다", "departure_max": "가장 멀리 간 조가 멀다",
    "root_motion_entropy": "근음이 여러 음정으로 고르게 움직인다", "coda_tempo_diff_bpm": "메트로놈 표기보다 빠르다(0은 표기대로)",
    "ratio_no_repeats": "표기보다 느리다(1은 표기대로)", "tempo_cv_across_performers": "연주마다 템포가 많이 다르다",
    "local_tempo_change_median": "박마다 템포가 많이 흔들린다", "ibi_cv_median": "한 연주 안에서 템포가 많이 바뀐다",
    "velocity_sd_median": "셈여림 폭이 넓다", "tempo_trend_bpm_per_decade": "늦은 녹음일수록 (측정 − 표기) 차이가 더 커진다",
    "sustain_ratio": "댐퍼 페달을 오래 밟는다", "soft_used_share": "소프트 페달을 쓴 연주가 많다", "beethoven_share": "베토벤 작품 연주가 많다",
    "mozart_share": "모차르트 작품 연주가 많다", "bach_share": "바흐 작품 연주가 많다", "hhi": "소수 작곡가에게 연주가 몰려 있다",
    "distinct_composers": "연주된 작곡가가 많다", "excerpt_share": "발췌 연주가 많다", "living_share": "생존 작곡가 작품이 많다",
    "repertoire_age_median": "세상을 떠난 지 오래된 작곡가의 작품이 많다", "canon_turnover": "상위 작곡가 명단이 덜 바뀐다",
    "conductor_repertoire": "생존 작곡가 작품이 많다", "reperf_10y_km": "다시 연주된 작품이 많다", "women_share": "여성 작곡가 작품이 많다",
}

COMPOSER_KO = {"Bach": "바흐", "Beethoven": "베토벤", "Mozart": "모차르트"}


def unit(m: dict, lang: str) -> str:
    """Unit name in the page language."""
    return UNIT_KO.get(m["unit"], m["unit"]) if lang == "ko" else m["unit"]


def axis(m: dict, lang: str, where: str = "x") -> str:
    """Axis title: metric name, unit, and what a larger value means. where: 'x' (value runs left to right) or 'y' (bottom to top)."""
    if lang == "ko":
        side = "오른쪽일수록" if where == "x" else "위일수록"
        return f"{m['ko']['name']} ({unit(m, lang)}) · {side} {HIGHER_KO[m['id']]}"
    side = "further right" if where == "x" else "higher up"
    return f"{m['en']['name']} ({m['unit']}) · {side} = {HIGHER_EN.get(m['id'], m['higher'])}"


def composer(name: str, lang: str) -> str:
    """Composer name for legends and row labels (the three whose scores the metric pages chart)."""
    return COMPOSER_KO.get(name, name) if lang == "ko" else name


def _median(vs) -> float:
    """Median as the strip plot draws it (NaN left out; mean of the two middle values for an even count)."""
    sv = sorted(v for v in (float(x) for x in vs) if v == v)
    if not sv:
        return float("nan")
    mid = len(sv) // 2
    return sv[mid] if len(sv) % 2 else (sv[mid - 1] + sv[mid]) / 2


def num(v: float, fmt: str) -> str:
    """A median in the metric's format (one more decimal when an integer metric lands on a half), with a real minus sign."""
    from takeaways import stat_spec
    return format(float(v), stat_spec(v, fmt)).replace("-", "−")


def kp(word: str, with_final: str, without: str) -> str:
    """Korean particle after a word or a number: `with_final` when the last syllable (or the last digit as read aloud) ends in a consonant."""
    ch = str(word).strip()[-1:]
    if "가" <= ch <= "힣":
        final = (ord(ch) - 0xAC00) % 28 != 0
    else:
        final = ch in "013678"   # 영 일 삼 육 칠 팔 end in a consonant; 이 사 오 구 do not
    return with_final if final else without


def ro(word: str) -> str:
    """The particle (으)로 after a word or a number: 로 after a vowel or ㄹ (일, 칠, 팔), 으로 after any other final consonant."""
    ch = str(word).strip()[-1:]
    if "가" <= ch <= "힣":
        j = (ord(ch) - 0xAC00) % 28
        return "로" if j in (0, 8) else "으로"
    return "으로" if ch in "036" else "로"


def strip_note(groups, fmt: str, lang: str, unit_ko: str = "곡집", unit_en: str = "collection", scope: bool = False) -> str:
    """One sentence for the caption of a strip plot (1.17), computed from the rows that are drawn:
    with up to three rows, every median; otherwise the rows with the highest and the lowest median
    (rows exactly tied at an extreme are named together; more than three tied rows are counted, not named).
    scope=True opens with the number of rows drawn, for charts that leave a collection out."""
    k = lang == "ko"
    med = [(n, _median(vs)) for n, vs, *_ in groups]
    med = [(n, x) for n, x in med if x == x]
    if len(med) < 2:
        return ""
    if len(med) <= 3:
        body = ", ".join(f"{n} {num(x, fmt)}" for n, x in med)
        return f"중앙값은 {body}{kp(body, '이다', '다')}." if k else f"Medians: {body}."
    hi, lo = max(x for _, x in med), min(x for _, x in med)
    if hi == lo:
        return f"{unit_ko} 중앙값이 모두 {num(hi, fmt)}{ro(num(hi, fmt))} 같다." if k else f"All {unit_en} medians are {num(hi, fmt)}."
    sep = "·" if k else ", "

    def who(v):
        ns = [n for n, x in med if x == v]
        return sep.join(ns) if len(ns) <= 3 else (f"{unit_ko} {len(ns)}개" if k else f"{len(ns)} {unit_en}s")
    hn, ln = who(hi), who(lo)
    pre = (f"그림에 실린 {unit_ko} {len(med)}개 가운데 " if k else f"Among the {len(med)} {unit_en}s drawn: ") if scope else ""
    if not k and pre:
        return f"{pre}highest median {hn} ({num(hi, fmt)}); lowest {ln} ({num(lo, fmt)})."
    return (pre + f"중앙값이 가장 큰 {unit_ko}은 {hn}({num(hi, fmt)}), 가장 작은 {unit_ko}은 {ln}({num(lo, fmt)}){kp(ln, '이다', '다')}." if k
            else f"Highest {unit_en} median: {hn} ({num(hi, fmt)}); lowest: {ln} ({num(lo, fmt)}).")
