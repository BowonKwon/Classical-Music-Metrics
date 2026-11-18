# -*- coding: utf-8 -*-
"""Ids of the second-level headings, one table per kind of page (1.19).

The key of SECTIONS is the `active` argument that the page is built with (the menu entry it belongs to).
A heading written in the code without an id gets its id here, looked up by its text: the number in front
("3. ") is dropped and every run of digits is read as N, so a section keeps its id when the sections are
renumbered or a count in the title changes. One id serves Korean and English.

A heading that is not in the table stops the build. When a section is added or its title is rewritten,
add or change the line here; do not reuse an id for a different section, since the id is part of the address
(page.html#id) that readers may have saved. Headings that carry an id in the code (history s1-s7,
orchestras kr) are left as they are.
"""
import html
import re
from pathlib import Path

SECTIONS = {
    "home": [
        ("score", "악보 지표", "Score metrics"),
        ("performance", "연주 지표", "Performance metrics"),
        ("repertoire", "레퍼토리 지표", "Repertoire metrics"),
        ("works-history", "작품 활동·역사", "Works & history"),
        ("orchestra-comparison", "악단 비교", "Orchestra comparison"),
    ],
    "metrics": [  # the metric list and every metric page
        ("score", "악보 지표", "Score metrics"),
        ("performance", "연주 지표", "Performance metrics"),
        ("repertoire", "레퍼토리 지표", "Repertoire metrics"),
        ("works-history", "작품 활동·역사", "Works & history"),
        ("orchestra-comparison", "악단 비교", "Orchestra comparison"),
        ("distribution", "모음별 분포", "Distribution by collection"),
        ("classical-sonatas", "고전기 건반 소나타", "Classical-era keyboard sonatas"),
        ("keyboard", "건반 음악 1740~1925", "Keyboard music, 1740–1925"),
        ("quartets", "현악 4중주", "String quartets"),
        ("ranking", "순위표", "Ranking"),
        ("decade-rank", "10년 단위 순위", "Rank by decade"),
        ("by-conductor", "지휘자별 (작품 연주 200건 이상)", "By conductor (200+ work performances)"),
        ("by-composer", "작곡가별 (작품 연주 200회 이상)", "By composer (200+ work performances)"),
        ("sources", "자료원", "Source"),
    ],
    "composers": [
        ("decade-rank", "10년 단위 순위", "Rank by decade"),
        ("top-works", "많이 연주된 작품", "Most performed works"),
    ],
    "history": [
        ("sources", "자료와 이용 허락", "Sources and licenses"),
    ],
    "genres": [
        ("life", "1. 생애의 장르 흐름", "1. Genres across a life"),
        ("period", "2. 시대와 세부 장르", "2. Period and sub-genre"),
        ("dating", "3. 연도 근거와 연주 시간", "3. Dating and duration"),
        ("method", "4. 분류 방법과 한계", "4. Method and limits"),
    ],
    "orchestras": [
        ("no-ranking", "1. 순위를 매기지 않는 이유", "1. Why there is no ranking"),
        ("sources", "2. 자료", "2. Sources"),
        ("carnegie-check", "3. 카네기홀 기록은 믿을 만한가", "3. Can the Carnegie Hall records be trusted?"),
        ("carnegie-touring", "4. 카네기홀 투어 프로그램의 쏠림", "4. How narrow are touring programs at Carnegie Hall?"),
        ("leipzig-new-york", "5. 19세기 라이프치히와 뉴욕", "5. Leipzig and New York in the nineteenth century"),
        ("seoul-new-york", "6. 서울시향과 뉴욕 필 — 정기공연 2009–2025년", "6. Seoul and New York — subscription concerts 2009–2025"),
        ("limits", "8. 한계", "8. Limits"),
    ],
    "scales": [
        ("by-region", "지역으로 보기", "By region"),
        ("western-tuning", "1. 서양 조율의 역사 — 비율로 정의된 이론값", "1. Western tuning — values defined by ratios"),
        ("east-asia", "2. 동아시아 — 삼분손익과 일본의 두 음계", "2. East Asia — sanfen sunyi (三分損益) and Japan's two scales"),
        ("theory-and-measurement", "3. 이론과 실측", "3. Theory and measurement"),
        ("modes", "4. 선법 — 같은 일곱 음, 다른 시작", "4. Modes — the same seven notes, a different start"),
        ("not-yet", "5. 아직 넣지 않은 것", "5. Not yet included"),
    ],
    "harmony": [
        ("data", "1. 자료", "1. The data"),
        ("periods", "2. 시대에 따라", "2. Across the periods"),
        ("annotation", "3. 주석이 만드는 차이", "3. What the annotation adds"),
        ("schumann", "4. 클라라 슈만과 로베르트 슈만", "4. Clara and Robert Schumann"),
        ("by-collection", "5. 곡집별 값", "5. By collection"),
    ],
    "sonatas": [
        ("collections", "1. 곡집", "1. The collections"),
        ("eight-metrics", "2. 지표 여덟 개", "2. Eight metrics"),
        ("findings", "3. 데이터가 보여 주는 것, 주의할 점", "3. What the data show, and what to watch for"),
        ("cpe-bach", "4. C. P. E. 바흐 — 소나타와 다른 곡", "4. C. P. E. Bach: sonatas and the other pieces"),
        ("medians", "5. 지표 47개의 중앙값", "5. Medians of all 47 metrics"),
    ],
    "romantic": [
        ("collections", "1. 곡집", "1. The collections"),
        ("keyboard", "2. 건반 음악 1740~1925", "2. Keyboard music, 1740–1925"),
        ("findings", "3. 데이터가 보여 주는 것, 주의할 점", "3. What the data show, and what to watch for"),
        ("key-maps", "4. 조성 지도", "4. Key maps"),
        ("quartets", "5. 현악 4중주", "5. String quartets"),
        ("medians", "6. 지표 47개의 중앙값", "6. Medians of all 47 metrics"),
    ],
    "map": [
        ("how-made", "1. 만든 방법", "1. How it is made"),
        ("harmony-map", "2. 화음 지도 — 음표 지표와 화음 지표", "2. Harmony map: note and chord metrics"),
        ("note-map", "3. 음표 지도 — 음표 지표만", "3. Note map: note metrics only"),
        ("fingerprint", "4. 악장의 지문", "4. A movement's fingerprint"),
        ("departure", "5. 으뜸조에서 얼마나 멀리, 얼마나 오래", "5. How far from home, and for how long"),
    ],
    "profiles": [
        ("pitch-classes", "1. 음고류 분포와 푸리에 계수", "1. Pitch-class distribution and its Fourier coefficients"),
        ("root-transitions", "2. 근음 전이 행렬", "2. Root-transition matrices"),
        ("one-movement", "3. 악장 하나 들여다보기", "3. One movement at a time"),
        ("which-metrics", "4. 어느 것을 지표로 냈나", "4. Which summaries became metrics"),
    ],
    "reading": [
        ("scores", "1. 악보 — 바흐 518악장, 베토벤 161악장, 모차르트 54악장", "1. Scores — 518 Bach, 161 Beethoven and 54 Mozart movements"),
        ("metronome", "2. 베토벤의 메트로놈 — 지휘자 36명은 표기보다 얼마나 느린가", "2. Beethoven's metronome — how far below the marks do 36 conductors play?"),
        ("pianists", "3. 피아니스트들은 같은 곡을 얼마나 다르게 치는가", "3. How differently do pianists play the same piece?"),
        ("repertoire", "4. 180년의 레퍼토리 — 뉴욕 필하모닉", "4. 180 years of repertoire — the New York Philharmonic"),
        ("limits", "5. 한계와 다음", "5. Limits and next steps"),
    ],
    "data": [
        ("columns-recordings", "열 설명: 베토벤 교향곡 녹음 표", "Columns: Beethoven symphony recordings"),
    ],
    "method": [
        ("principles", "원칙", "Principles"),
        ("sources", "자료원", "Source"),
        ("counting-unit", "레퍼토리를 세는 단위 (1.1)", "Counting unit for repertoire (1.1)"),
        ("composer-names", "작곡가 이름 정리", "Composer names"),
        ("composer-dates", "작곡가 생몰년 (Wikidata)", "Composer dates (Wikidata)"),
        ("cross-check", "교차 검증", "Cross-check"),
        ("source-paper", "선행 연구와의 대조", "Comparison with the source paper"),
        ("ai-disclosure", "AI 사용 고지", "AI disclosure"),
        ("not-yet", "아직 없는 것 (장기 과제)", "Not yet here (long-term)"),
        ("changelog", "변경 이력", "Changelog"),
    ],
}

_H2 = re.compile(r"<h2\b([^>]*)>(.*?)</h2>", re.S)
_HAS_ID = re.compile(r"\bid\s*=")
_ID = re.compile(r"""<h2\b[^>]*?\bid=(["']?)([^"'\s>]+)\1""")


def norm(s: str) -> str:
    """Heading text without tags, without the number in front, and with every run of digits read as N."""
    s = html.unescape(re.sub(r"<[^>]+>", "", s)).strip()
    s = re.sub(r"^\d+\.\s+", "", s)
    return re.sub(r"\d+(?:[.,]\d+)*", "N", s)


def _table(kind: str, lang: str) -> dict:
    col = 1 if lang == "ko" else 2
    out = {}
    for row in SECTIONS.get(kind, []):
        key = norm(row[col])
        if key in out and out[key] != row[0]:
            raise ValueError(f"section_ids.SECTIONS[{kind!r}]: two ids for the heading {key!r}")
        out[key] = row[0]
    return out


def add_ids(body: str, lang: str, kind: str, where: str = "") -> str:
    """Give every second-level heading that has no id the id set in SECTIONS[kind]."""
    table = _table(kind, lang)

    def sub(m):
        attrs, inner = m.group(1), m.group(2)
        if _HAS_ID.search(attrs):
            return m.group(0)
        key = norm(inner)
        if key not in table:
            raise ValueError(f"{where or kind} ({lang}): no id for the second-level heading {key!r} — "
                             f"add it to SECTIONS[{kind!r}] in src/section_ids.py")
        return f'<h2{attrs} id="{table[key]}">{inner}</h2>'

    return _H2.sub(sub, body)


def check_pairs(site: Path) -> int:
    """Every page must have the same section ids, in the same order, in Korean and in English.
    Returns the number of pages compared; raises on the first page that differs."""
    n = 0
    for ko in sorted((site / "ko").rglob("*.html")):
        en = site / "en" / ko.relative_to(site / "ko")
        if not en.exists():
            continue
        a = [m.group(2) for m in _ID.finditer(ko.read_text(encoding="utf-8"))]
        b = [m.group(2) for m in _ID.finditer(en.read_text(encoding="utf-8"))]
        if a != b:
            raise ValueError(f"{ko.relative_to(site / 'ko').as_posix()}: section ids differ between ko {a} and en {b}")
        if len(set(a)) != len(a):
            raise ValueError(f"{ko.relative_to(site / 'ko').as_posix()}: a section id is used twice: {a}")
        n += 1
    return n
