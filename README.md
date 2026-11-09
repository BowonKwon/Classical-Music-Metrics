# Classical Music Metrics — 서양 고전 음악 메트릭스

악보와 연주를 숫자로 읽는 공개 데이터 사이트입니다. 야구의 세이버메트릭스처럼 **지표마다 정의·공식·표본·한계**를 함께 두고, 공개 악보 코퍼스와 연주 데이터셋에서 뽑은 수치를 지표 하나에 한 면씩 보여 줍니다. 바흐와 베토벤으로 시작해 1.1에서 모차르트와 뉴욕 필하모닉의 전 작곡가 레퍼토리를, 1.2에서 작곡가 작품 활동·교향곡 편성·템포 지시어·악기 사용 변천·A음 높이의 역사를 담은 「작품·역사」 면을, 1.5에서 뉴욕 필·카네기홀 초청 악단·게반트하우스·서울시향의 레퍼토리를 견주는 「악단 비교」 면을, 1.6에서 곡집 40개로 본 「화성의 역사」 면과 시대·지역별 음계를 보고 듣는 「음계와 조율」 면을, 1.8에서 같은 시대의 건반 소나타 곡집 일곱 개를 견주는 「고전기 건반 소나타」 면을 더했습니다.

- **사이트:** https://bowonkwon.github.io/Classical-Music-Metrics/ ([한국어](https://bowonkwon.github.io/Classical-Music-Metrics/ko/) · [English](https://bowonkwon.github.io/Classical-Music-Metrics/en/))
- **읽기용 판:** 핵심 결과를 글로 읽는 판 — [한국어](https://bowonkwon.github.io/Classical-Music-Metrics/ko/reading.html) · [English](https://bowonkwon.github.io/Classical-Music-Metrics/en/reading.html)
- **판:** 1.8.1 (2026. 11. 9.) — 1.0 은 2026. 10. 31., 1.1·1.2 는 2026. 11. 1., 1.2.1·1.3·1.3.1 은 2026. 11. 2., 1.4 는 2026. 11. 4., 1.5 는 2026. 11. 7., 1.6 은 2026. 11. 8., 1.7 은 2026. 11. 8., 1.7.1·1.8 은 2026. 11. 9.
- **다른 공개 자료:** https://bowonkwon.github.io/ — 법률 외국어 자습서·AI 자습서와 함께 한곳에 모았습니다.

## 무엇이 들어 있나

| 층 | 내용 | 원자료 |
|---|---|---|
| 악보 지표 | 바흐 518악장·베토벤 161악장·모차르트 54악장(코랄, 영국·프랑스 모음곡, 무반주 독주곡, 베토벤 현악4중주 전곡·피아노 소나타 28곡(22·25·27·28번은 코퍼스에 없다), 모차르트 피아노 소나타 18곡)의 음역·반음계 비율·리듬 엔트로피·화성 리듬·전조 빈도·악구 길이·nPVI 등 39개 | DCML 코퍼스(EPFL), Sapp Humdrum 코랄 |
| 연주 지표 | 지휘자 36명의 베토벤 교향곡 전집에서 메트로놈 표기 대비 템포; 바흐 평균율·베토벤 소나타 피아노 연주 428개의 템포 산포·루바토·강약 폭(모차르트 연주 16개는 소표본이라 표에만) | bmetr(Martín-Castro & Ucar 2020), ASAP |
| 레퍼토리 지표 | 뉴욕 필하모닉 1842~2026 시즌, 작곡가 3,126명 전체의 점유율·발췌 비율·생존 작곡가 점유율·레퍼토리 나이·정전 회전율·작곡가 집중도. 전 작곡가 순위표와 상위 50명 프로필 면 | NY Phil Performance History, Wikidata(작곡가 생몰년) |
| 작품 활동·역사 (1.2) | 작곡가 10명의 경력 띠·나이별 작품면·쓴 시기와 연주 비율, 교향곡 편성, 템포 지시어 구성, 교향곡 편성란의 악기 사용 변천(25년 구간), A음 높이의 역사(1361~1885년 측정 242건) | IMSLP 작품면, NY Phil, Ellis 『On the Sensations of Tone』 부록(1885·1895, 퍼블릭 도메인) |
| 악단 비교 (1.5) | 뉴욕 필 자체 기록과 카네기홀 기록의 대조, 카네기홀 초청 악단(빈 필·베를린 필·콘세르트헤바우 등)의 투어 프로그램 쏠림, 게반트하우스 × 뉴욕 필(1840~1890년대), 서울시향 × 뉴욕 필 정기공연(2009~2025). 순위·합성 점수 없음 | NY Phil, 카네기홀 공연 기록(CC0), Hartmann-Enke 게반트하우스 자료(CC BY 4.0), 서울시 열린데이터광장(공공누리 제1유형), Wikidata |
| 화성의 역사 (1.6) | DCML Distant Listening Corpus 곡집 40개(1,326곡, 화성 주석 1,283곡, 1590~1931)의 7화음·반음계·부속화음·화음 어휘를 50년 구간으로(곡집마다 한 표, 건반만의 선 따로). 클라라 슈만 × 로베르트 슈만 | DCML Distant Listening Corpus(Hentschel 외 2025, CC BY-NC-SA 4.0) |
| 고전기 건반 소나타 (1.8) | D. 스카를라티·W. F. 바흐·C. P. E. 바흐·J. C. 바흐·코젤루흐의 건반 소나타 곡집을 모차르트·베토벤과 함께(소나타 351악장) 악보 지표 39개로. C. P. E. 바흐의 판타지아·론도는 따로, 출판 연도만 있는 J. C. 바흐는 표에만 | DCML 코퍼스(Hentschel 외 2025, CC BY-NC-SA 4.0) |
| 음계와 조율 (1.6, 2판 1.7) | 음계 45개를 센트 자 위에 그리고 브라우저 합성음으로 재생. 서양 조율사(피타고라스~평균율), 삼분손익 12율·평조·계면조와 편경으로 추정한 황종 높이, 일본 음선·양선(우에하라 1895)과 고토 조율(엘리스 1885), 가야금 실측(경기민요 고음반·산조 계면조)과 피리 녹음 실측(남운정 1998), 아랍 라스트·바야티(무샤카의 24 4분음과 1932 카이로 회의 녹음), 인도 22 슈루티, 가믈란·타이·페르시아·터키·우간다·기니·모잠비크 초피의 이론과 실측 | DaMuSc(McBride 외 2023, CC BY 4.0), ORD-CC32(Bozkurt 2025, CC BY-NC 4.0), 각 행의 1차 문헌 |

## 1.8.1에서 바뀐 것

- **음표 처리 규칙 명시.** 악보 지표 중 음표에서 세는 21개의 공식에 「꾸밈음은 빼고, 붙임줄로 이어진 뒷음은 앞 음에 합쳐 한 음으로 센다. 이어지는 앞 음을 찾지 못한 뒷음은 새 음으로 세지 않는다」를 적었습니다(리듬 엔트로피는 원래 적혀 있었습니다). 계산은 처음부터 그렇게 했으므로 수치는 바뀌지 않습니다.
- **「고전기 건반 소나타」 출처.** 스카를라티 소나타의 형식·악기 서술에 미 의회도서관 NLS(Rodda 2020)를 달고, 근거를 확인하지 못한 베토벤 후기 피아노 음역 서술은 「피아노를 위한 여러 악장짜리 곡」으로 줄였습니다. J. C. 바흐 곡집의 작곡 연도는 공개 자료로 확인되지 않아 지금처럼 표에만 둡니다.

## 1.8에서 바뀐 것

- **「고전기 건반 소나타」 면 신설.** DCML이 같은 화성 주석 규칙으로 분석한 건반 소나타 곡집 일곱 개를 나란히 봅니다. 새로 더한 곡집은 D. 스카를라티 69악장, W. F. 바흐 9악장, C. P. E. 바흐 소나타 50악장, J. C. 바흐 29악장, 코젤루흐 49악장이고, 모차르트 54악장과 베토벤 91악장은 기존 그대로입니다(기존 수치는 바뀌지 않습니다).
- **비교의 기준.** C. P. E. 바흐 곡집의 판타지아 10악장·론도 6악장은 비교에서 빼고 따로 보입니다. J. C. 바흐 곡집은 원자료에 출판 연도만 있어 작곡 연도순 그림에서 빼고 표에만 둡니다. 코젤루흐 곡집에는 종지 표지가 없어 종지 지표 두 개를 빈칸으로 둡니다(0이 아닙니다). 화음 지표는 곡집마다 다른 주석자가 붙인 기호를 세므로 주석자의 차이가 섞여 있다는 점을 면에 적었습니다.
- **지표 면.** 악보 지표 면마다 「고전기 건반 소나타」 절을 더했습니다. 데이터는 `data/sonatas/sonata_metrics_by_movement.csv`(CC BY-NC-SA 4.0)입니다.
- 면의 수치와 사실 서술은 블라인드 교차 검증을 거쳤습니다. 표본 5악장의 수치 20개를 원자료에서 다시 계산해 모두 일치했습니다.

## 1.7.1에서 바뀐 것

- **「음계와 조율」 보충.** 남운정(1998)이 정재국의 피리 독주 녹음 세 곡에서 잰 평균 음정을 3행으로 더해 45개가 되었습니다. 인쇄된 다섯 음정의 합이 1200센트와 맞지 않아 옥타브는 그리지 않고 그 사실을 면에 적었습니다. 인도 슈루티 문단에 라마나탄(1981)의 고대 문헌 해석을, 초피 문단에 『뉴 그로브』 2판(2001) 「모잠비크」 항목의 서술과 1948년 실측의 비교를 더했습니다.

## 1.7에서 바뀐 것

- **「음계와 조율」 2판.** 음계를 23개에서 42개로 늘렸습니다. 새 값은 모두 1차 문헌의 해당 쪽에서 읽었습니다: 우에하라 『속악선율고』(1895)의 음선·양선 비율, 엘리스(1885)의 고토 히라조시 실측, 스미스 영역(1847)의 무샤카 24 4분음, 1932 카이로 아랍 음악 회의 녹음(ORD-CC32)에서 다시 계산한 라스트·바야티, 『나티야샤스트라』의 슈루티 배분, 트레이시(1948·1958)의 초피 팀빌라, 고유동(2021)의 경기민요 고음반 4개와 양수연(2013)의 산조 계면조 청·꺾는 음 4명, 임경미(2013)의 유파·악조별 징–땅 음정 표. 원문을 열지 못한 자료는 면의 「아직 넣지 않은 것」에 이유와 함께 적었습니다.
- **표시.** 올라갈 때와 내려갈 때 다른 음은 속이 빈 점, 원자료에 없는 옥타브를 재생을 위해 붙인 자리는 점선 고리로 그립니다(1.6의 옥타브 없는 음계에도 적용).
- **라이선스.** `data/scales/scales.csv` 에 행별 `license` 열이 생겼습니다. ORD-CC32에서 계산한 두 행과 석사학위논문 세 편에서 수치를 옮긴 가야금 8행은 CC BY-NC 4.0, 나머지는 CC BY 4.0입니다. 카이로 녹음의 정점 표 `data/scales/scales_cairo1932.csv`(CC BY-NC 4.0)와 그것을 만드는 `src/cairo1932_peaks.py` 를 더했습니다.
- **검증.** 새 값과 서술을 원자료만 받은 별도 모델(Codex)이 세 번 블라인드로 대조했습니다. 원문을 다시 확인한 뒤 우에하라 표의 인쇄 오식, 카이로 정점의 반올림, 원전 안의 수치 불일치(함동정월 윗음, 트레이시 도표 IV)를 면에 밝혔습니다.

## 1.6에서 바뀐 것

- **「화성의 역사」 면.** DCML Distant Listening Corpus의 곡집 40개(기존 5개 + 새 35개, 1,326곡·117,831마디)를 작곡 연대순으로 놓았습니다. 화음 지표는 화성 기호가 붙은 1,283곡에서, 음표 지표는 전체에서 셉니다. 곡집마다 악장 값의 중앙값을 내고, 곡집의 작곡 연도로 50년 구간을 나눠 그 중앙값들의 중앙값을 잇습니다(곡집 하나가 한 표). 7화음 비율은 1600년대 구간 0.045에서 1900년대 구간 0.426으로 오르고, 선에 오른 구간끼리 앞뒤로 견주면 5번 모두 올랐습니다(건반만으로는 4번 중 4번). 표본은 시대를 대표하도록 뽑힌 것이 아니고 건반 음악이 많으므로 「이 곡집들에서 이렇게 달라진다」로 읽어야 합니다. 1650년 이전 선법 음악의 로마 숫자 화음 지표는 따로 읽으라는 경고를 두었습니다.
- **「음계와 조율」 면.** 음계 23개를 0~1200센트 자 위에 그리고, 회색 눈금으로 12평균율을 겹쳤습니다. 단추를 누르면 브라우저가 삼각파로 합성해 들려줍니다(녹음 파일 없음). 비율로 정의된 음률은 정의에서 계산해 Scala 아카이브와 대조했고, 실측값은 DaMuSc 원자료(가믈란 28·23세트의 평균과 표준편차)와 원논문 표에서 옮겼습니다. 아랍 마캄·인도 슈루티·일본 음계·국악기 실측은 원문을 확인한 뒤 더합니다.
- **검증.** 화성 지표(곡집 4개를 원자료에서 다시 계산), 곡집 40개의 작곡 연도·장르, 음계 23개의 값과 연대, 두 면의 사실 서술을 원자료만 받은 별도 모델(Codex)이 블라인드로 대조했습니다. 그 결과 연대 막대가 곡집의 작곡 범위를 좁게 그리던 것(16개)과 음계 설명 몇 곳을, 원문을 다시 확인한 뒤 고쳤습니다.
- **새 스크립트·표.** `src/dlc_metrics.py`(곡집 40개 계산 → `data/dlc_movement_metrics.csv`·`dlc_corpus_metrics.csv`·`dlc_period_metrics.csv`), `src/harmony_pages.py`, `src/scales_pages.py`(→ `data/scales.csv`), 곡집 정보표 `data/aliases/dlc_corpora.csv`(장르·표기는 엮은이가 정함).

## 1.5에서 바뀐 것

- **「악단 비교」 면.** 공연 기록이 공개된 악단들의 작곡가 점유율을 같은 단위로 견줍니다. 합성 점수에는 가중치를 정당화할 외부 기준이 없어서 순위는 매기지 않습니다.
- **카네기홀 기록.** 카네기홀 공연 기록(SPARQL, 작품 129,338행)으로 초청 악단의 뉴욕 공연을 봅니다. 같은 뉴욕 필을 두 출처로 재면 카네기홀이 본거지였던 1890~1960년대에는 코사인 0.92~0.99로 거의 같습니다. 그래서 이 표본은 「그 악단이 카네기홀에서 한 공연」으로만 읽습니다.
- **서울시향.** 공연 정보의 곡목에 작곡가가 없어 곡명·작품번호·공연 페이지로 붙였습니다(정기공연 2009~2025년 1,586곡 중 85.9%, `data/orch/seoulphil_works.csv`, 수동표 `data/aliases/seoulphil_title_manual.csv`). 뉴욕 필 정기공연과의 작곡가 점유율 코사인은 0.930입니다. 상위 10명 점유율은 미귀속 곡을 모두 상위 10명 밖으로 셈한 하한 39.7%가 뉴욕 필 같은 곡 수 기준의 95% 상한 38.6%보다 높습니다. 공연 정보는 예정 프로그램이라 취소·변경 공연이 섞여 있는데, 2020·2021년을 빼도 판정은 같습니다.
- **검증.** 작곡가 귀속과 면의 사실 서술은 원자료만 받은 별도 모델(Codex)의 블라인드 교차 검증을 세 번 거쳤고, 지적은 원문을 다시 확인한 뒤 반영했습니다.
- **새 스크립트.** `src/carnegie_fetch.py`(카네기홀 SPARQL, 요청 간격 11초), `src/orch_compare.py`(악단 대조·투어 표), `src/seoulphil_attrib.py`(서울시향 작곡가 귀속), `src/proto_orchestras.py`(서울시향 × 뉴욕 필 계산), `src/orchestra_pages.py`(면).
- **분류표 수정.** 뉴욕 필 작곡가 분류표에서 무대 공연의 막 표시 「ACT,」를 작품 아님으로 옮겼습니다. 공개 지표 값은 바뀌지 않습니다.

## 1.4에서 바뀐 것

- **연주 지표 3개.** 녹음 연도별 템포 추이(베토벤 교향곡 36개 전집, 같은 악장 안 기울기 10년당 +0.85 bpm, 95% 구간 +0.16~+1.72 — 연주 양식을 함께 넣으면 +0.26 으로 줄어 0과 구별되지 않는다), 댐퍼 페달 사용 시간 비율과 소프트 페달 사용 녹음 비율(ASAP 의 국제 피아노 e-콩쿠르 녹음, 야마하 디스클라비어; 한 녹음에서 잘린 여러 곡은 녹음 하나로 센다 — ASAP 파일 456개 → 녹음 359개).
- **레퍼토리 지표 3개.** 뉴욕 필 지휘자별 레퍼토리 구성(지휘자 이름 정규화표 `data/aliases/nyphil_conductors.csv`, 규칙 R1~R5), 신작 10년 재연주율(Kaplan–Meier), 여성 작곡가 점유율(Wikidata 성별 P21, `data/aliases/composer_gender.csv` — 성별 미상 작곡가를 어떻게 셀지에 따라 하한·가운데 값·상한).
- **새 스크립트.** `src/tempo_metrics.py`(템포 추이), `src/performance_metrics.py`(페달), `src/repertoire_metrics.py`(지휘자·재연주·여성 점유율), `src/wikidata_gender.py`(P21 받기 — 요청에는 프로젝트 주소만 담는다), `src/registry_14.py`(지표 정의).
- **새 CSV.** `beethoven_symphony_tempo_trend.csv`·`beethoven_symphony_conductor_year.csv`·`asap_pedal.csv`·`asap_pedal_summary.csv`·`asap_pedal_recordings.csv`·`nyphil_conductor_repertoire.csv`·`nyphil_new_work_survival.csv`·`nyphil_new_work_survival_summary.csv`·`nyphil_women_share.csv`.
- **표시.** 음수는 −, 생성 문장의 시즌은 1842–43, 한국어 면의 연도 범위는 물결표. 정수 지표의 중앙값·사분위가 정수가 아니면 소수 첫째 자리까지. 지표·작곡가 면에 위치 표시줄·같은 묶음 목록·이전/다음, 언어 전환 링크는 같은 면으로. 「열다섯 마디」를 「열네 마디」(100 ÷ 7)로 바로잡았다.

## 1.3.1에서 바뀐 것

- **띠 그림의 중앙값.** 지표 면 띠 그림의 중앙값 막대가 값이 짝수 개일 때 가운데 두 값의 평균이 아니라 위쪽 값을 그리고 있었습니다. 고친 뒤 지표 38개 면의 띠 111줄에서 중앙값이 바뀌어 같은 면 표의 중앙값과 맞습니다(반올림 뒤 막대 위치나 툴팁 값이 달라진 것은 109줄. 예: 종지 밀도의 바흐 무반주 묶음 16.7 → 15.8). 표·요약 상자·CSV 의 수치는 그대로입니다.
- **영어 면.** 문장·용어(마디는 bar, 비교 단위는 collection 등)·철자(미국식)·표 머리글과 범례의 대소문자를 손봤습니다. 한국어 면은 지표 이름 「연주 안 템포 변동」(옛 「악장 안 템포 변동」 — 정의대로 연주 하나 안의 변동이다)과 「작품·역사」 3절 제목 「쓴 시기와 연주 비율」이 바뀌었습니다.
- **원자료 커밋 기록.** `raw_manifest.json` 에 커밋이 없는 IMSLP 항목 자리에 빌드 저장소 자신의 커밋이 잘못 적혀 있어 뺐습니다. 이제 `src/raw_manifest.py` 가 git 클론인 원자료의 커밋만 적습니다.
- **재현.** 저장소 루트가 아닌 곳에서도 빌드되고, Python 3.11 에서도 돌도록 고쳤습니다. 패키지 판은 `requirements.txt` 에 적었습니다. 지금 자료에서는 수치가 바뀌지 않는 경계 처리 세 가지(지휘자 요약의 「표시에 가장 가까운」 판정, 작품 ID 가 빈 뉴욕 필 항목, 음표가 없는 악장)도 고쳤습니다.

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
data/   파생 CSV, 작곡가 분류·Wikidata 매칭표·악단 대조표(data/aliases/), IMSLP 표(data/imslp/), Ellis 전사본(data/ellis/), 악단 비교 표(data/orch/), 화성사·음계 표(data/dlc_*.csv·scales.csv), 파일별 라이선스(datapackage.json), 원자료 커밋 해시(raw_manifest.json)
src/    지표 정의(registry.py)·추출 스크립트·Wikidata 매칭 스크립트·사이트 생성기
```

재현: 원자료 저장소들을 `data/raw/` 에 클론한 뒤 `src/` 의 스크립트를 순서대로 돌리면 `data/` 의 CSV 와 `docs/` 가 다시 만들어집니다(Python 3.11 이상, 패키지 판은 `requirements.txt`). 악보 지표는 `score_metrics.py`(바흐 Humdrum 코랄은 `score_metrics_kern370.csv` 로 따로 씀) → `score_metrics_13.py` 순서이고, 코랄 두 인코딩 대조표는 `chorale_crosscheck.py` 가 만듭니다. 원자료 커밋은 `raw_manifest.py` 가 `data/raw_manifest.json` 에 적습니다. Wikidata 매칭 스크립트는 후보표만 만들고, 레퍼토리 지표는 검수를 마친 `data/aliases/composer_wikidata.csv` 를 읽습니다. 악단 비교는 `carnegie_fetch.py` → `orch_compare.py` → `seoulphil_attrib.py` → `proto_orchestras.py` 순서입니다(게반트하우스 CSV와 서울시향 CSV 두 판은 내려받아 `data/raw/` 에 둡니다). 원본 악보·MIDI·음원은 이 저장소에 없습니다.

## 이용 허락

- 사이트의 글과 지표 설명에서 엮은이에게 권리가 있는 부분은 [CC BY-NC 4.0](LICENSE.md)으로 공개합니다. 이 요약은 이해를 돕기 위한 것이고, 조건은 라이선스 원문을 따릅니다.
- 코드(`src/`)는 [PolyForm Noncommercial 1.0.0](LICENSE.md)으로 공개합니다. 상업적으로 이용하시려면 [Issues](https://github.com/BowonKwon/Classical-Music-Metrics/issues)로 연락해 주십시오.
- 파생 데이터(`data/`): DCML·Sapp·ASAP(CC BY-NC-SA 4.0)에서 만든 표는 그 조건을 이어받아 **CC BY-NC-SA 4.0**, 뉴욕 필·Wikidata(CC0)와 bmetr(MIT)에서 엮은이가 계산하거나 검수해 더한 표는 **CC BY 4.0** 입니다. bmetr 의 MIT 허락은 코드·자료를 복제할 때 저작권·허락 고지를 남기라는 조건을 두므로, bmetr 에서 온 표를 쓸 때는 원저자(Martín-Castro & Ucar 2020)도 함께 밝혀 주십시오. IMSLP 작품면(CC BY-SA 4.0)을 가공한 `data/imslp/` 의 표와 「작품·역사」 면 1~6절의 차트는 **CC BY-SA 4.0** 이고(사이트 글의 비영리 조건은 적용하지 않습니다), 퍼블릭 도메인 원본을 옮겨 적은 `data/ellis/` 는 CC BY 4.0 입니다. 악단 비교 표(`data/orch/`)와 악단 대조표는 CC BY 4.0 이며, 서울시향에서 온 표를 쓸 때는 「출처: 서울특별시(서울 열린데이터광장)」를, 게반트하우스에서 온 표를 쓸 때는 원저자(Hartmann-Enke)를 함께 밝혀 주십시오. DCML Distant Listening Corpus에서 만든 `dlc_*.csv` 는 **CC BY-NC-SA 4.0**, DaMuSc(CC BY 4.0)와 논문 표에서 옮기거나 정의에서 계산한 `scales.csv` 는 **CC BY 4.0** 입니다. 표마다 원자료 라이선스와 표의 라이선스를 [데이터](https://bowonkwon.github.io/Classical-Music-Metrics/ko/data.html) 면과 `data/datapackage.json` 에 적었습니다.
- © 2026 권보원(Bowon Kwon)

## 일러두기

지표 설계·코드·본문 초고는 Claude(Anthropic)의 도움으로 작성했고, 엮은이가 원자료와 대조해 검증했습니다. 그래도 틀린 서술이나 계산이 남아 있을 수 있습니다. 찾으시면 [Issues](https://github.com/BowonKwon/Classical-Music-Metrics/issues)로 알려 주십시오. 이 저장소는 엮은이가 개인적으로 만든 것이며 엮은이가 속한 기관의 견해와 관계가 없습니다.

---

## English

An open data site that reads scores and performances as numbers. As in baseball's sabermetrics, **every metric carries its definition, formula, sample and caveats**, one page per metric, computed from open score corpora and performance datasets. It began with Bach and Beethoven; version 1.1 added Mozart and the New York Philharmonic's repertoire covering every composer, 1.2 added a 'Works & history' page on composers' work activity, symphonic orchestration, tempo markings, instrument use and the history of the pitch of a′, and 1.5 added an 'Orchestras' page comparing the repertoire of the New York Philharmonic, visiting orchestras at Carnegie Hall, the Leipzig Gewandhaus and the Seoul Philharmonic, and 1.6 added a 'History of harmony' page over 40 annotated collections and a 'Scales and tuning' page where scales from different periods and regions can be seen and heard, and 1.8 added a 'Classical-era keyboard sonatas' page comparing seven keyboard-sonata collections of the period.

- **Site:** https://bowonkwon.github.io/Classical-Music-Metrics/en/ · **Reading edition:** [en/reading.html](https://bowonkwon.github.io/Classical-Music-Metrics/en/reading.html)
- **Version:** 1.8.1 (Nov 9, 2026) — 1.0 was Oct 31, 2026; 1.1 and 1.2 Nov 1, 2026; 1.2.1, 1.3 and 1.3.1 Nov 2, 2026; 1.4 Nov 4, 2026; 1.5 Nov 7, 2026; 1.6 Nov 8, 2026; 1.7 Nov 8, 2026; 1.7.1 and 1.8 Nov 9, 2026
- **Other public materials:** https://bowonkwon.github.io/en/ — the legal-language and AI handbooks, listed alongside this site.

| Layer | Contents | Sources |
|---|---|---|
| Score metrics | 39 metrics (pitch range, chromatic ratio, rhythm entropy, harmonic rhythm, modulation rate, phrase length, nPVI …) over 518 Bach, 161 Beethoven and 54 Mozart movements: chorales, English and French Suites, solo works, Beethoven's string quartets and piano sonatas, Mozart's 18 piano sonatas (Beethoven: 28 sonatas; Nos. 22, 25, 27, 28 are not in the corpus) | DCML corpora (EPFL), Sapp Humdrum chorales |
| Performance metrics | Tempo vs Beethoven's metronome marks for 36 conductors' symphony cycles; tempo spread, rubato and dynamic range over 428 piano performances of the Well-Tempered Clavier and Beethoven sonatas (16 Mozart performances, too few for charts, appear in tables) | bmetr (Martín-Castro & Ucar 2020), ASAP |
| Repertoire metrics | New York Philharmonic, 1842–2026, all 3,126 composers: shares, excerpt share, living-composer share, repertoire age, canon turnover, concentration; a full composer ranking and profiles of the top 50 | NY Phil Performance History, Wikidata (composer dates) |
| Works & history (1.2) | Career ribbons, work pages by age, and when works were written vs how much they are played, for ten composers; symphony orchestration; tempo markings; instruments named in symphony instrumentation by 25-year period; the pitch of a′ 1361–1885 (242 measurements) | IMSLP work pages, NY Phil, Ellis's appendix to *On the Sensations of Tone* (1885/1895, public domain) |
| Orchestras (1.5) | The NY Phil's own records checked against Carnegie Hall's; how narrow visiting orchestras' Carnegie Hall programmes are (Vienna and Berlin Philharmonics, Concertgebouw and others); Gewandhaus × NY Phil (1840s–1890s); Seoul Philharmonic × NY Phil subscription concerts (2009–2025). No ranking and no composite score | NY Phil, Carnegie Hall performance history (CC0), Hartmann-Enke's Gewandhaus data (CC BY 4.0), Seoul Open Data Plaza (KOGL Type 1), Wikidata |
| History of harmony (1.6) | Seventh chords, chromaticism, applied chords and chord vocabulary by 50-year period over the 40 collections of the DCML Distant Listening Corpus (1,326 pieces, 1,283 with harmony labels, 1590–1931), one vote per collection, with a keyboard-only line; Clara × Robert Schumann | DCML Distant Listening Corpus (Hentschel et al. 2025, CC BY-NC-SA 4.0) |
| Classical-era keyboard sonatas (1.8) | Keyboard-sonata collections by D. Scarlatti, W. F. Bach, C. P. E. Bach, J. C. Bach and Koželuh beside Mozart and Beethoven (351 sonata movements) on the 39 score metrics. C. P. E. Bach's fantasias and rondos shown separately; J. C. Bach, with publication years only, in the tables only | DCML corpora (Hentschel et al. 2025, CC BY-NC-SA 4.0) |
| Scales and tuning (1.6, second edition 1.7) | 45 scales on a cent ruler with browser playback: Western tuning history, sanfen sunyi, pyeongjo and gyemyeonjo with the pitch of hwangjong from stone chimes, the Japanese in and yō scales (Uehara 1895) and koto tuning (Ellis 1885), measured gayageum scales (Gyeonggi folk-song records, sanjo gyemyeonjo) and p'iri recordings (Nam 1998), Arabic Rast and Bayati (Mushāqa's 24 quarter tones and the 1932 Cairo Congress recordings), the Indian 22 śrutis, and theory and measurement for gamelan, Thai, Persian, Turkish, Ganda, Malinke and Chopi scales | DaMuSc (McBride et al. 2023, CC BY 4.0), ORD-CC32 (Bozkurt 2025, CC BY-NC 4.0), the primary source of each row |

**What changed in 1.8.1.** The formulas of 21 score metrics counted from the notes now state the common rule: grace notes are left out, a tied continuation is merged into the note it continues, and a continuation whose preceding note cannot be found is not counted as a new note (rhythm entropy already said so). The computation always worked this way, so no values change. On the 'Classical-era keyboard sonatas' page the form and instrument of Scarlatti's sonatas now cite the Library of Congress NLS (Rodda 2020), and an unsupported statement about the compass of Beethoven's late-sonata pianos is reduced to 'multi-movement sonatas for the piano'. Composition years for the J. C. Bach collection could not be confirmed from open sources, so it stays in the tables only.

**What changed in 1.8.** New 'Classical-era keyboard sonatas' page: seven keyboard-sonata collections that DCML analysed under one harmony annotation standard. New collections: D. Scarlatti (69 movements), W. F. Bach (9), C. P. E. Bach (50 sonata movements), J. C. Bach (29) and Koželuh (49); Mozart (54) and Beethoven (91) are unchanged, as are their existing values. The 10 fantasia and 6 rondo movements in the C. P. E. Bach collection are shown separately, not in the comparison. The J. C. Bach source data give only publication years, so that collection is left out of the date-ordered charts and shown in the tables. The Koželuh collection has no cadence labels, so its two cadence metrics are blank (not zero). Chord metrics count labels added by different annotators in each collection, and the page says so. Each score-metric page gets a 'Classical-era keyboard sonatas' section; the data are in `data/sonatas/sonata_metrics_by_movement.csv` (CC BY-NC-SA 4.0). The page's numbers and statements of fact went through blind cross-checking: 20 values from five sample movements were recomputed from the source data and all matched.

**What changed in 1.7.1.** Supplement to the 'Scales and tuning' page: three rows of average intervals that Unjung Nam (1998) measured in three solo p'iri recordings by Chung Chaekook, 45 scales in all. The five printed intervals do not sum to 1,200 cents, so the octave is not drawn and the page says so. Added Ramanathan's (1981) reading of the ancient texts to the śruti paragraph, and to the Chopi paragraph the New Grove (2001) 'Mozambique' article and how it compares with the 1948 measurements.

**What changed in 1.7.** Second edition of the 'Scales and tuning' page: 42 scales instead of 23, every new value read on the cited page of its primary source — Uehara's in and yō ratios (1895), Ellis's koto hira-jōshi measurements (1885), Mushāqa's 24 quarter tones (tr. Smith 1847), Rast and Bayati recomputed from the 1932 Cairo Congress recordings (ORD-CC32), the śruti counts of the Nāṭyaśāstra, Tracey's Chopi timbila (1948, 1958), four Gyeonggi folk-song records measured by Ko (2021), cheong and the bent notes of sanjo gyemyeonjo for four players from Yang (2013), and a table of jing–ttang intervals by school and mode from Lim (2013). Sources that could not be opened are listed on the page with the reason. Notes used only when descending are hollow dots; an octave added only for playback is a dashed ring (also on the 1.6 scales without an octave). `data/scales/scales.csv` now has a per-row `license` column: the two rows computed from ORD-CC32 and the eight gayageum rows transcribed from three master's theses are CC BY-NC 4.0, the rest CC BY 4.0. New: `data/scales/scales_cairo1932.csv` (CC BY-NC 4.0) and `src/cairo1932_peaks.py`. The new values and statements were cross-checked blind three times by a separate model (Codex); after rechecking the sources, a misprint in Uehara's table, the rounding of the Cairo peaks and inconsistencies inside the sources (Ham Dongjeongwol's upper note, Tracey's Diagram IV) are stated on the page.

**What changed in 1.6.** A new 'History of harmony' page sets the 40 collections of the DCML Distant Listening Corpus (5 already used here plus 35 new; 1,326 pieces, 117,831 bars) in order of composition. Chord metrics are counted on the 1,283 pieces with harmony labels, note metrics on all pieces. Each collection's median over its pieces is one vote, and the line joins the medians of those votes by 50-year period: the seventh-chord ratio rises from 0.045 in the 1600s period to 0.426 in the 1900s and goes up between all 5 pairs of neighbouring periods on the line (4 of 4 on the keyboard-only line). The collections were not drawn to represent their periods and keyboard music dominates, so the charts show how these collections change; chord metrics for modal music before 1650 carry a warning. A new 'Scales and tuning' page draws 23 scales on a 0–1,200 cent ruler against equal temperament and plays them with a triangle-wave synthesiser in the browser (no recordings). Ratio-defined tunings were computed from their definitions and checked against the Scala archive; measured values come from the DaMuSc data (means and standard deviations over 28 and 23 gamelan sets) and the source papers' tables. Arabic maqam, Indian śruti, Japanese scales and measurements of Korean instruments will be added once their sources are checked in the original. The harmony metrics (recomputed for four collections from the source data), the composition years and genres of all 40 collections, the 23 scales' values and dates, and both pages' statements of fact were cross-checked blind by a separate model (Codex); after rechecking the sources, the composition-range bars (drawn too narrow for 16 collections) and several scale notes were corrected. New scripts and tables: `src/dlc_metrics.py` (→ `data/dlc_movement_metrics.csv`, `dlc_corpus_metrics.csv`, `dlc_period_metrics.csv`), `src/harmony_pages.py`, `src/scales_pages.py` (→ `data/scales.csv`), and the collection table `data/aliases/dlc_corpora.csv` (genres and display names set by the editor).

**What changed in 1.5.** A new 'Orchestras' page compares composer shares in one unit across orchestras with public performance records; there is no ranking, because a composite score has no outside standard for its weights. Visiting orchestras are seen through Carnegie Hall's performance history (SPARQL, 129,338 work rows); measured from both sources, the NY Phil agrees closely while Carnegie Hall was its home (cosine 0.92–0.99 in the 1890s–1960s), so these samples are read only as what an orchestra played at Carnegie Hall. The Seoul Philharmonic's programme field has no composers, so they were attached from titles, opus numbers and concert pages (85.9% of 1,586 subscription works, 2009–2025; `data/orch/seoulphil_works.csv`, hand-made table `data/aliases/seoulphil_title_manual.csv`). Against NY Phil subscription concerts the cosine is 0.930, and Seoul's top-10 composer share, counting every unattributed work outside the top ten, is at least 39.7%, above the 95% upper bound of the size-matched NY baseline (38.6%); the Seoul data list planned programmes, including cancelled or changed concerts, but leaving out 2020 and 2021 gives the same result. The attributions and the page's statements of fact went through three rounds of blind cross-checking by a separate model (Codex) given only the source data, and each point was rechecked against the source before it was applied. New scripts: `src/carnegie_fetch.py` (eleven seconds between requests), `src/orch_compare.py`, `src/seoulphil_attrib.py`, `src/proto_orchestras.py`, `src/orchestra_pages.py`. In the NY Phil composer table the act marker 'ACT,' is now classed as not a work; no published metric value changes.

**What changed in 1.4.** Three performance metrics: tempo trend by recording year (36 Beethoven symphony cycles; within-movement slope +0.85 bpm per decade, 95% interval +0.16 to +1.72 — with performance style included it falls to +0.26 and cannot be told apart from 0), damper pedal time share and soft pedal use (ASAP's International Piano-e-Competition recordings on Yamaha Disklaviers; a recording cut into several pieces counts once, 456 ASAP files → 359 recordings). Three repertoire metrics: repertoire by NY Phil conductor (conductor-name table `data/aliases/nyphil_conductors.csv`, rules R1–R5), ten-year re-performance of new works (Kaplan–Meier), and women composers' share (Wikidata P21 in `data/aliases/composer_gender.csv`; lower bound, middle value and upper bound depending on how composers of unknown gender are counted). New scripts: `src/tempo_metrics.py`, `src/performance_metrics.py`, `src/repertoire_metrics.py`, `src/wikidata_gender.py` (requests carry only the project address), `src/registry_14.py`. Display: minus signs, en-dash seasons, one decimal place for non-integer medians of integer metrics, breadcrumb, same-group list and previous/next on metric and composer pages, a language link to the same page, and 'every 14 bars' (100 ÷ 7) instead of fifteen.

**What changed in 1.3.1.** The median bar in the metric pages' strip charts showed the upper middle value when the number of values was even, instead of the mean of the two middle values. After the fix the median changes in 111 strip rows on 38 metric pages and now matches the table on the same page (after rounding, the bar position or tooltip value differs in 109 rows; e.g. cadence density, Bach's solo works: 16.7 → 15.8). Numbers in tables, summary boxes and CSVs are unchanged. The English pages were revised for wording, terms (bar for measure, collection for group), American spelling and sentence-case table headers and legends. `raw_manifest.json` no longer lists IMSLP, which has no commit (the build repository's own commit had been recorded in its place); `src/raw_manifest.py` now records only inputs that are git clones. The build now runs from any directory and on Python 3.11; package versions are in `requirements.txt`. Three edge cases that do not change any current number were also fixed (the 'closest to the marks' conductor in the summary box, NY Phil entries with an empty work ID, movements without notes).

**What changed in 1.3.** Score metrics grew from 14 to 39: sixteen that had already been computed were published, and nine were new — nPVI rhythmic contrast, post-leap reversal, beat-crossing syncopation, motif repetition, diminished sevenths, Neapolitan and augmented sixths, pedal points, phrase length and the 4- and 8-bar phrase share (`src/score_metrics_13.py`, `data/score_metrics_13_by_movement.csv`). Cadence labels on rows without a chord symbol are now counted, and works without cadence annotation (Bach's solo violin works and Cello Suites 1–2) are left blank rather than 0. Tied rows are now always listed in the same order. The step that writes the Humdrum chorales to their own table and the chorale cross-check script (`chorale_crosscheck.py`) are now public, so every table can be rebuilt from the published code.

**What changed in 1.2.1.** An 'At a glance' box now opens the 29 metric pages and the seven sections of the Works & history page: numbers computed from the page's own tables, and the main limit from each metric's caveats. The caveats for the chromatic ratio and repertoire concentration (HHI) were made more precise.

**What 1.2 adds.** A 'Works & history' page built from IMSLP work pages (4,589 pages for ten composers, 3,140 in the Symphonies category). The unit is the IMSLP work page, not the number of works composed, and the Symphonies category is not a probability sample of all symphonies; the page states these limits. Ellis's table of historical pitches was transcribed from the 1895 page images and checked line by line against 1885 (`data/ellis/`). Tables derived from IMSLP (`data/imslp/`) and their charts are **CC BY-SA 4.0**.

**What changed in 1.1.** Repertoire is now counted per *work* on a program rather than per work *entry* (an overture and an aria from one opera used to count twice), with complete performances counted separately; the four 1.0 repertoire metrics therefore changed, and their old values are kept in a '1.0 unit' column. 91 non-person credits (traditional, anthem, unattributed, joint or arrangement credits) are separated from composers, and the pen name 'P.D.Q. Bach' is merged into Peter Schickele (`data/aliases/nyphil_composers.csv`). Birth and death years for the 529 composers with 10+ performances were matched in Wikidata and reviewed by the editor: 518 confirmed, 10 unresolved, one pen name merged (`data/aliases/composer_wikidata.csv`). A 'complete performance' is one where the archive names no movement or part — a proxy from the record, not a verified performance.

`docs/` is the site (GitHub Pages), `data/` the derived CSVs, lookup tables, IMSLP tables (`data/imslp/`), the Ellis transcription (`data/ellis/`), orchestra tables (`data/orch/`), harmony and scale tables (`data/dlc_*.csv`, `scales.csv`), per-file licenses (`datapackage.json`) and input commit hashes (`raw_manifest.json`, written by `raw_manifest.py`), `src/` the metric registry, extractors, Wikidata matcher and site builder. Clone the source repositories into `data/raw/` and run the scripts to rebuild everything (Python 3.11 or later; package versions in `requirements.txt`; score metrics: `score_metrics.py`, which writes the Humdrum chorales to `score_metrics_kern370.csv` separately, then `score_metrics_13.py`; the two-encoding chorale cross-check comes from `chorale_crosscheck.py`); the repertoire metrics read the reviewed Wikidata table, not the matcher's raw candidates. No scores, MIDI or audio are redistributed.

Text is licensed under [CC BY-NC 4.0](LICENSE.md) and code under [PolyForm Noncommercial 1.0.0](LICENSE.md) to the extent the editor holds rights; derived tables from DCML, Sapp and ASAP carry their sources' CC BY-NC-SA 4.0 forward, while the editor's computations and reviews from the NY Phil and Wikidata (CC0) and bmetr (MIT) are released under CC BY 4.0 (bmetr's MIT license asks that copies keep its copyright and permission notice, so please also credit Martín-Castro & Ucar 2020 when using tables derived from it); tables derived from IMSLP work pages (`data/imslp/`) and the charts in sections 1–6 of the Works & history page are CC BY-SA 4.0 (the non-commercial condition on the site's text does not apply to them), the Ellis transcription (`data/ellis/`) is CC BY 4.0, and the orchestra tables (`data/orch/`) and matching tables are CC BY 4.0 (please credit "Source: Seoul Metropolitan Government (Seoul Open Data Plaza)" for tables from the Seoul data and Hartmann-Enke for tables from the Gewandhaus data); the `dlc_*.csv` tables from the DCML Distant Listening Corpus are CC BY-NC-SA 4.0, and `scales.csv` (from DaMuSc, CC BY 4.0, the source papers' tables and the tunings' definitions) is CC BY 4.0; the Data page and `data/datapackage.json` list both licenses for every table. © 2026 Bowon Kwon. Metric design, code and draft text were produced with help from Claude (Anthropic) and verified by the editor against the source data; errors may remain — please report them via Issues. This is a personal project and does not represent any institution the editor belongs to.
