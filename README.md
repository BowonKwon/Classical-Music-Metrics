# Classical Music Metrics — 서양 고전 음악 메트릭스

악보와 연주를 숫자로 읽는 공개 데이터 사이트입니다. 야구의 세이버메트릭스처럼 **지표마다 정의·공식·표본·한계**를 함께 두고, 공개 악보 코퍼스와 연주 데이터셋에서 뽑은 수치를 지표 하나에 한 면씩 보여 줍니다. 바흐와 베토벤으로 시작해 1.1에서 모차르트와 뉴욕 필하모닉의 전 작곡가 레퍼토리를, 1.2에서 작곡가 작품 활동·교향곡 편성·템포 지시어·악기 사용 변천·A음 높이의 역사를 담은 「작품·역사」 면을 더했습니다.

- **사이트:** https://bowonkwon.github.io/Classical-Music-Metrics/ ([한국어](https://bowonkwon.github.io/Classical-Music-Metrics/ko/) · [English](https://bowonkwon.github.io/Classical-Music-Metrics/en/))
- **읽기용 판:** 핵심 결과를 글로 읽는 판 — [한국어](https://bowonkwon.github.io/Classical-Music-Metrics/ko/reading.html) · [English](https://bowonkwon.github.io/Classical-Music-Metrics/en/reading.html)
- **판:** 1.3 (2026. 11. 2.) — 1.0 은 2026. 10. 31., 1.1·1.2 는 2026. 11. 1., 1.2.1 은 2026. 11. 2.
- **다른 공개 자료:** https://bowonkwon.github.io/ — 법률 외국어 자습서·AI 자습서와 함께 한곳에 모았습니다.

## 무엇이 들어 있나

| 층 | 내용 | 원자료 |
|---|---|---|
| 악보 지표 | 바흐 518악장·베토벤 161악장·모차르트 54악장(코랄, 영국·프랑스 모음곡, 무반주 독주곡, 베토벤 현악4중주 전곡·피아노 소나타 28곡(22·25·27·28번은 코퍼스에 없다), 모차르트 피아노 소나타 18곡)의 음역·반음계 비율·리듬 엔트로피·화성 리듬·전조 빈도·악구 길이·nPVI 등 39개 | DCML 코퍼스(EPFL), Sapp Humdrum 코랄 |
| 연주 지표 | 지휘자 36명의 베토벤 교향곡 전집에서 메트로놈 표기 대비 템포; 바흐 평균율·베토벤 소나타 피아노 연주 428개의 템포 산포·루바토·강약 폭(모차르트 연주 16개는 소표본이라 표에만) | bmetr(Martín-Castro & Ucar 2020), ASAP |
| 레퍼토리 지표 | 뉴욕 필하모닉 1842~2026 시즌, 작곡가 3,126명 전체의 점유율·발췌 비율·생존 작곡가 점유율·레퍼토리 나이·정전 회전율·작곡가 집중도. 전 작곡가 순위표와 상위 50명 프로필 면 | NY Phil Performance History, Wikidata(작곡가 생몰년) |
| 작품 활동·역사 (1.2) | 작곡가 10명의 경력 띠·나이별 작품면·쓴 시기와 연주되는 시기, 교향곡 편성, 템포 지시어 구성, 교향곡 편성란의 악기 사용 변천(25년 구간), A음 높이의 역사(1361~1885년 측정 242건) | IMSLP 작품면, NY Phil, Ellis 『On the Sensations of Tone』 부록(1885·1895, 퍼블릭 도메인) |

## 1.3에서 바뀐 것

- 악보 지표를 14개에서 39개로 늘렸습니다. 이미 계산해 두었던 16개를 공개하고, 리듬 대비 지수(nPVI)·도약 후 반진행·박 넘김 당김음·동기 반복률·감7화음·나폴리·증6화음·페달 포인트·악구 길이·4·8마디 악구 비율 9개를 새로 계산했습니다(`src/score_metrics_13.py`, `data/score_metrics_13_by_movement.csv`).
- 종지 기호는 화음 기호가 없는 행에 붙은 것까지 세도록 고쳤고, 종지를 주석하지 않은 작품(바흐 무반주 바이올린 작품·첼로 모음곡 1·2번)의 종지 밀도는 0이 아니라 빈칸으로 둡니다.
- 같은 값의 행은 늘 같은 순서로 나오도록 정렬을 고정했습니다.
- 바흐 Humdrum 코랄 표(`score_metrics_kern370.csv`)를 따로 쓰는 단계와 코랄 두 인코딩 대조표를 만드는 스크립트(`chorale_crosscheck.py`)를 공개해, 공개 코드만으로 모든 표가 다시 만들어지게 했습니다.

## 1.2.1에서 바뀐 것

- 지표 면 29개와 「작품·역사」 면 7개 절 맨 위에 「한눈에 보기」 상자를 두었습니다. 수치는 그 면의 표에서 계산하고, 주의할 점은 각 지표의 한계 설명에서 가져왔습니다.
- 반음계 비율과 레퍼토리 집중도(HHI)의 한계 설명을 더 정확하게 고쳤습니다.

## 1.2에서 더한 것

- **「작품·역사」 면.** IMSLP 작품면(작곡가 10명 4,589면, 교향곡 범주 3,140면)의 작곡 연도·장르 태그·편성·악장 칸을 파싱했습니다. 단위는 IMSLP 작품면이라 「작곡한 작품 수」와 같지 않고, 교향곡 범주는 전체 교향곡의 확률 표본이 아닙니다 — 면에 그 한계를 적었습니다.
- **A음 높이의 역사.** Ellis 의 역사적 음고 표를 1895년판 쪽 이미지에서 옮겨 적고 1885년판과 전부 대조했습니다(`data/ellis/`).
- **라이선스가 다른 표.** IMSLP 에서 온 표(`data/imslp/`)와 그 차트는 **CC BY-SA 4.0** 입니다.

## 1.1에서 바뀐 것

- **레퍼토리를 세는 단위.** 1.0 은 프로그램의 작품 *항목* 하나를 한 번으로 셌습니다. 그러면 같은 작품의 서곡과 아리아를 따로 연주했을 때 두 번이 됩니다. 1.1 은 프로그램에 오른 *작품* 하나를 한 번으로 세고, 그중 발췌가 아닌 전곡 연주를 따로 셉니다. 이 때문에 1.0 의 레퍼토리 지표 네 개(바흐·베토벤 점유율, 집중도, 작곡가 수)의 값이 달라졌습니다. 옛 값은 표의 「1.0 단위」 열에 그대로 남겼습니다.
- **작곡가 이름.** 전승곡·국가(國歌)·작곡가 미상·공동 또는 편곡 복합 표기 91개를 사람 작곡가와 구분하고, 필명 「P.D.Q. 바흐」를 피터 시켈리로 합쳤습니다. 분류표는 `data/aliases/nyphil_composers.csv` 입니다.
- **작곡가 생몰년.** 10회 이상 연주된 529명을 Wikidata 와 맞추고 엮은이가 검수했습니다(518명 확정, 10명 미확정, 필명 1건 통합). 매칭표는 `data/aliases/composer_wikidata.csv` 입니다.
- **「전곡 연주」의 뜻.** 아카이브가 악장·부분을 적지 않은 연주를 전곡으로 셉니다. 실제 공연 내용을 확인한 값이 아니라 기재에서 나온 대리 지표입니다.

## 저장소 구성

```
docs/   사이트(GitHub Pages). docs/data/ 에 파생 CSV
data/   파생 CSV, 작곡가 분류·Wikidata 매칭표(data/aliases/), IMSLP 표(data/imslp/), Ellis 전사본(data/ellis/), 파일별 라이선스(datapackage.json), 원자료 커밋 해시(raw_manifest.json)
src/    지표 정의(registry.py)·추출 스크립트·Wikidata 매칭 스크립트·사이트 생성기
```

재현: 원자료 저장소들을 `data/raw/` 에 클론한 뒤 `src/` 의 스크립트를 순서대로 돌리면 `data/` 의 CSV 와 `docs/` 가 다시 만들어집니다(Python 3.11+, pandas, music21, mido, pyreadr, requests). 악보 지표는 `score_metrics.py`(바흐 Humdrum 코랄은 `score_metrics_kern370.csv` 로 따로 씀) → `score_metrics_13.py` 순서이고, 코랄 두 인코딩 대조표는 `chorale_crosscheck.py` 가 만듭니다. Wikidata 매칭 스크립트는 후보표만 만들고, 레퍼토리 지표는 검수를 마친 `data/aliases/composer_wikidata.csv` 를 읽습니다. 원본 악보·MIDI·음원은 이 저장소에 없습니다.

## 이용 허락

- 사이트의 글과 지표 설명에서 엮은이에게 권리가 있는 부분은 [CC BY-NC 4.0](LICENSE.md)으로 공개합니다. 이 요약은 이해를 돕기 위한 것이고, 조건은 라이선스 원문을 따릅니다.
- 코드(`src/`)는 [PolyForm Noncommercial 1.0.0](LICENSE.md)으로 공개합니다. 상업적으로 이용하시려면 [Issues](https://github.com/BowonKwon/Classical-Music-Metrics/issues)로 연락해 주십시오.
- 파생 데이터(`data/`): DCML·Sapp·ASAP(CC BY-NC-SA 4.0)에서 만든 표는 그 조건을 이어받아 **CC BY-NC-SA 4.0**, 뉴욕 필·Wikidata(CC0)와 bmetr(MIT)에서 엮은이가 계산하거나 검수해 더한 표는 **CC BY 4.0** 입니다. bmetr 의 MIT 허락은 코드·자료를 복제할 때 저작권·허락 고지를 남기라는 조건을 두므로, bmetr 에서 온 표를 쓸 때는 원저자(Martín-Castro & Ucar 2020)도 함께 밝혀 주십시오. IMSLP 작품면(CC BY-SA 4.0)을 가공한 `data/imslp/` 의 표와 「작품·역사」 면 1~6절의 차트는 **CC BY-SA 4.0** 이고(사이트 글의 비영리 조건은 적용하지 않습니다), 퍼블릭 도메인 원본을 옮겨 적은 `data/ellis/` 는 CC BY 4.0 입니다. 표마다 원자료 라이선스와 표의 라이선스를 [데이터](https://bowonkwon.github.io/Classical-Music-Metrics/ko/data.html) 면과 `data/datapackage.json` 에 적었습니다.
- © 2026 권보원(Bowon Kwon)

## 일러두기

지표 설계·코드·본문 초고는 Claude(Anthropic)의 도움으로 작성했고, 엮은이가 원자료와 대조해 검증했습니다. 그래도 틀린 서술이나 계산이 남아 있을 수 있습니다. 찾으시면 [Issues](https://github.com/BowonKwon/Classical-Music-Metrics/issues)로 알려 주십시오. 이 저장소는 엮은이가 개인적으로 만든 것이며 엮은이가 속한 기관의 견해와 관계가 없습니다.

---

## English

An open data site that reads scores and performances as numbers. As in baseball's sabermetrics, **every metric carries its definition, formula, sample and caveats**, one page per metric, computed from open score corpora and performance datasets. It began with Bach and Beethoven; version 1.1 added Mozart and the New York Philharmonic's repertoire across every composer, and 1.2 adds a 'Works & history' page on composers' work activity, symphonic orchestration, tempo markings, instrument use and the history of the pitch of a′.

- **Site:** https://bowonkwon.github.io/Classical-Music-Metrics/en/ · **Reading edition:** [en/reading.html](https://bowonkwon.github.io/Classical-Music-Metrics/en/reading.html)
- **Version:** 1.3 (Nov 2, 2026) — 1.0 was Oct 31, 2026; 1.1 and 1.2 Nov 1, 2026; 1.2.1 Nov 2, 2026
- **Other public materials:** https://bowonkwon.github.io/en/ — the legal-language and AI handbooks, listed alongside this site.

| Layer | Contents | Sources |
|---|---|---|
| Score metrics | 39 metrics (pitch range, chromatic ratio, rhythm entropy, harmonic rhythm, modulation rate, phrase length, nPVI …) over 518 Bach, 161 Beethoven and 54 Mozart movements: chorales, English and French Suites, solo works, Beethoven's string quartets and piano sonatas, Mozart's 18 piano sonatas (Beethoven: 28 sonatas; Nos. 22, 25, 27, 28 are not in the corpus) | DCML corpora (EPFL), Sapp Humdrum chorales |
| Performance metrics | Tempo vs Beethoven's metronome marks for 36 conductors' symphony cycles; tempo spread, rubato and dynamic range over 428 piano performances of the Well-Tempered Clavier and Beethoven sonatas (16 Mozart performances, too few for charts, appear in tables) | bmetr (Martín-Castro & Ucar 2020), ASAP |
| Repertoire metrics | New York Philharmonic, 1842–2026, all 3,126 composers: shares, excerpt share, living-composer share, repertoire age, canon turnover, concentration; a full composer ranking and profiles of the top 50 | NY Phil Performance History, Wikidata (composer dates) |
| Works & history (1.2) | Career ribbons, work pages by age and composed-vs-performed for ten composers; symphony orchestration; tempo markings; instruments named in symphony instrumentation by 25-year period; the pitch of a′ 1361–1885 (242 measurements) | IMSLP work pages, NY Phil, Ellis's appendix to *On the Sensations of Tone* (1885/1895, public domain) |

**What changed in 1.3.** Score metrics grow from 14 to 39: sixteen already computed are now published, and nine are new — nPVI rhythmic contrast, post-leap reversal, beat-crossing syncopation, motif repetition, diminished sevenths, Neapolitan and augmented sixths, pedal points, phrase length and the 4- and 8-bar phrase share (`src/score_metrics_13.py`, `data/score_metrics_13_by_movement.csv`). Cadence labels on rows without a chord symbol are now counted, and works without cadence annotation (Bach's solo violin works and Cello Suites 1–2) are left blank rather than 0. Tied rows are now always listed in the same order. The step that writes the Humdrum chorales to their own table and the chorale cross-check script (`chorale_crosscheck.py`) are now public, so every table can be rebuilt from the published code.

**What changed in 1.2.1.** An 'At a glance' box now opens the 29 metric pages and the seven sections of the Works & history page: numbers computed from the page's own tables, and the main limit from each metric's caveats. The caveats for the chromatic ratio and repertoire concentration (HHI) were made more precise.

**What 1.2 adds.** A 'Works & history' page built from IMSLP work pages (4,589 pages for ten composers, 3,140 in the Symphonies category). The unit is the IMSLP work page, not the number of works composed, and the Symphonies category is not a probability sample of all symphonies; the page states these limits. Ellis's table of historical pitches was transcribed from the 1895 page images and checked line by line against 1885 (`data/ellis/`). Tables derived from IMSLP (`data/imslp/`) and their charts are **CC BY-SA 4.0**.

**What changed in 1.1.** Repertoire is now counted per *work* on a program rather than per work *entry* (an overture and an aria from one opera used to count twice), with complete performances counted separately; the four 1.0 repertoire metrics therefore changed, and their old values are kept in a '1.0 unit' column. 91 non-person credits (traditional, anthem, unattributed, joint or arrangement credits) are separated from composers, and the pen name 'P.D.Q. Bach' is merged into Peter Schickele (`data/aliases/nyphil_composers.csv`). Birth and death years for the 529 composers with 10+ performances were matched in Wikidata and reviewed by the editor: 518 confirmed, 10 unresolved, one pen name merged (`data/aliases/composer_wikidata.csv`). A 'complete performance' is one where the archive names no movement or part — a proxy from the record, not a verified performance.

`docs/` is the site (GitHub Pages), `data/` the derived CSVs, lookup tables, IMSLP tables (`data/imslp/`), the Ellis transcription (`data/ellis/`), per-file licences (`datapackage.json`) and input commit hashes, `src/` the metric registry, extractors, Wikidata matcher and site builder. Clone the source repositories into `data/raw/` and run the scripts to rebuild everything (score metrics: `score_metrics.py`, which writes the Humdrum chorales to `score_metrics_kern370.csv` separately, then `score_metrics_13.py`; the two-encoding chorale cross-check comes from `chorale_crosscheck.py`); the repertoire metrics read the reviewed Wikidata table, not the matcher's raw candidates. No scores, MIDI or audio are redistributed.

Text is licensed under [CC BY-NC 4.0](LICENSE.md) and code under [PolyForm Noncommercial 1.0.0](LICENSE.md) to the extent the editor holds rights; derived tables from DCML, Sapp and ASAP carry their sources' CC BY-NC-SA 4.0 forward, while the editor's computations and reviews from the NY Phil and Wikidata (CC0) and bmetr (MIT) are released under CC BY 4.0 (bmetr's MIT licence asks that copies keep its copyright and permission notice, so please also credit Martín-Castro & Ucar 2020 when using tables derived from it); tables derived from IMSLP work pages (`data/imslp/`) and the charts in sections 1–6 of the Works & history page are CC BY-SA 4.0 (the non-commercial condition on the site's text does not apply to them), and the Ellis transcription (`data/ellis/`) is CC BY 4.0; the Data page and `data/datapackage.json` list both licences for every table. © 2026 Bowon Kwon. Metric design, code and draft text were produced with help from Claude (Anthropic) and verified by the editor against the source data; errors may remain — please report them via Issues. This is a personal project and does not represent any institution the editor belongs to.
