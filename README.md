# Classical Music Metrics — 클래식 음악 세이버메트릭스

악보와 연주를 숫자로 읽는 공개 데이터 사이트입니다. 야구의 세이버메트릭스처럼 **지표마다 정의·공식·표본·한계**를 함께 두고, 공개 악보 코퍼스와 연주 데이터셋에서 뽑은 수치를 지표 하나에 한 면씩 보여 줍니다. 첫 판은 바흐와 베토벤입니다.

- **사이트:** https://bowonkwon.github.io/Classical-Music-Metrics/ ([한국어](https://bowonkwon.github.io/Classical-Music-Metrics/ko/) · [English](https://bowonkwon.github.io/Classical-Music-Metrics/en/))
- **읽기용 판:** 핵심 결과를 글로 읽는 판 — [한국어](https://bowonkwon.github.io/Classical-Music-Metrics/ko/reading.html) · [English](https://bowonkwon.github.io/Classical-Music-Metrics/en/reading.html)
- **판:** 1.0 (2026. 10. 31.)

## 무엇이 들어 있나

| 층 | 내용 | 원자료 |
|---|---|---|
| 악보 지표 | 바흐 518악장·베토벤 161악장(코랄, 영국·프랑스 모음곡, 무반주 독주곡, 현악4중주 전곡, 피아노 소나타 전곡)의 음역·반음계 비율·리듬 엔트로피·화성 리듬·전조 빈도 등 14개 | DCML 코퍼스(EPFL), Sapp Humdrum 코랄 |
| 연주 지표 | 지휘자 36명의 베토벤 교향곡 전집에서 메트로놈 표기 대비 템포; 바흐 평균율·베토벤 소나타 피아노 연주 428개의 템포 산포·루바토·강약 폭 | bmetr(Martín-Castro & Ucar 2020), ASAP |
| 레퍼토리 지표 | 뉴욕 필하모닉 1842~2026 시즌의 바흐·베토벤 점유율과 작곡가 집중도 | NY Phil Performance History |

## 저장소 구성

```
docs/   사이트(GitHub Pages). docs/data/ 에 파생 CSV
data/   파생 CSV와 원자료 커밋 해시(raw_manifest.json)
src/    지표 정의(registry.py)·추출 스크립트 4개·사이트 생성기
```

재현: 원자료 저장소들을 `data/raw/` 에 클론한 뒤 `src/` 의 스크립트를 순서대로 돌리면 `data/` 의 CSV 와 `docs/` 가 다시 만들어집니다(Python 3.11+, pandas, music21, mido, pyreadr). 원본 악보·MIDI·음원은 이 저장소에 없습니다.

## 이용 허락

- 사이트의 글과 지표 설명에서 엮은이에게 권리가 있는 부분은 [CC BY-NC 4.0](LICENSE.md)으로 공개합니다. 이 요약은 이해를 돕기 위한 것이고, 조건은 라이선스 원문을 따릅니다.
- 코드(`src/`)는 [PolyForm Noncommercial 1.0.0](LICENSE.md)으로 공개합니다. 상업적으로 이용하시려면 [Issues](https://github.com/BowonKwon/Classical-Music-Metrics/issues)로 연락해 주십시오.
- 파생 데이터(`data/`)는 원자료의 라이선스를 따릅니다. DCML·Sapp·ASAP(CC BY-NC-SA 4.0)에서 나온 표는 **CC BY-NC-SA 4.0**, bmetr(MIT)·뉴욕 필(CC0)에서 나온 표는 **CC BY 4.0** 입니다. 표마다 어느 쪽인지는 [데이터](https://bowonkwon.github.io/Classical-Music-Metrics/ko/data.html) 면에 적혀 있습니다.
- © 2026 권보원(Bowon Kwon)

## 일러두기

지표 설계·코드·본문 초고는 Claude(Anthropic)의 도움으로 작성했고, 엮은이가 원자료와 대조해 검증했습니다. 그래도 틀린 서술이나 계산이 남아 있을 수 있습니다. 찾으시면 [Issues](https://github.com/BowonKwon/Classical-Music-Metrics/issues)로 알려 주십시오. 이 저장소는 엮은이가 개인적으로 만든 것이며 엮은이가 속한 기관의 견해와 관계가 없습니다.

---

## English

An open data site that reads scores and performances as numbers. As in baseball's sabermetrics, **every metric carries its definition, formula, sample and caveats**, one page per metric, computed from open score corpora and performance datasets. The first edition covers Bach and Beethoven.

- **Site:** https://bowonkwon.github.io/Classical-Music-Metrics/en/ · **Reading edition:** [en/reading.html](https://bowonkwon.github.io/Classical-Music-Metrics/en/reading.html)
- **Version:** 1.0 (Oct 31, 2026)

| Layer | Contents | Sources |
|---|---|---|
| Score metrics | 14 metrics (pitch range, chromatic ratio, rhythm entropy, harmonic rhythm, modulation rate …) over 518 Bach and 161 Beethoven movements: chorales, English and French Suites, solo works, all string quartets, all piano sonatas | DCML corpora (EPFL), Sapp Humdrum chorales |
| Performance metrics | Tempo vs Beethoven's metronome marks for 36 conductors' symphony cycles; tempo spread, rubato and dynamic range over 428 piano performances of the Well-Tempered Clavier and Beethoven sonatas | bmetr (Martín-Castro & Ucar 2020), ASAP |
| Repertoire metrics | Bach and Beethoven shares and composer concentration at the New York Philharmonic, 1842–2026 | NY Phil Performance History |

`docs/` is the site (GitHub Pages), `data/` the derived CSVs with the input commit hashes, `src/` the metric registry, four extractors and the site builder. Clone the source repositories into `data/raw/` and run the scripts to rebuild everything. No scores, MIDI or audio are redistributed.

Text is licensed under [CC BY-NC 4.0](LICENSE.md) and code under [PolyForm Noncommercial 1.0.0](LICENSE.md) to the extent the editor holds rights; derived data inherits its source license (CC BY-NC-SA 4.0 for tables from DCML, Sapp and ASAP; CC BY 4.0 for tables from bmetr and the NY Phil). © 2026 Bowon Kwon. Metric design, code and draft text were produced with help from Claude (Anthropic) and verified by the editor against the source data; errors may remain — please report them via Issues. This is a personal project and does not represent any institution the editor belongs to.
