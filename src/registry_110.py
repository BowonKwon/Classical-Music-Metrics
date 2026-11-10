"""1.10: three metrics of departure from the home key (score_metrics_110.py, design 63).
Readings quote numbers from data/derived/score_metrics_110_by_movement.csv; tests/test_piecemap.py checks them."""

_KEY = ("국소 조는 DCML 주석자가 정한 것이다. 조표 차는 국소 조의 조표(단조는 나란한조의 조표)에서 으뜸조의 조표를 뺀 뒤 이명동음으로 접어 0~6으로 센다(「전조 거리」와 같은 척도). "
        "으뜸조와 그 나란한조는 0이다. 국소 조의 로마 숫자는 DCML 표준대로 읽는다: 단조 맥락의 III·VI·VII는 자연단음계의 3·6·7음이고, vi/V처럼 겹친 표기는 V조의 vi다. 국소 조 주석이 없는 악장은 빈칸이다.")
_KEY_EN = ("Local keys are the DCML annotators'. The signature difference is the local key's signature (a minor key takes its relative major's) minus the home key's, folded enharmonically to 0–6 "
           "(the scale of the key-change distance). The home key and its relative are 0. Local-key numerals are read as in the DCML standard: in a minor context III, VI and VII are degrees of the natural minor; a nested label such as vi/V is vi of the key of V. Blank for movements without local-key labels.")
_CAV = ("주석자의 판단을 함께 잰다. 음표만으로 조를 추정해 같은 값을 낸 대조판은 「곡 지도」 면에 있다. Herremans·Chew(2016)의 tensile strain 과 착상(국소 조성과 전체 조성의 거리)은 같다. 다만 그쪽은 음 묶음의 중심과 곡 전체 조의 중심 사이 거리를 나선 배열 위에서 재고, 여기서는 주석된 두 조의 조표 차를 재며 나란한조를 0으로 둔다. 두 값은 같은 척도가 아니다.")
_CAV_EN = ("Measures the annotators' judgment as well. A note-only version that finds keys without annotation is compared on the 'Piece map' page. The idea matches Herremans & Chew's (2016) tensile strain (distance between local and global tonal context), but they measure the distance in the spiral array between the centre of a cluster of notes and that of the global key, while here it is the signature difference between two annotated keys, with the relative key set to 0. The two are not on the same scale.")

METRICS_110 = [
    dict(id="departure_mean", layer="A", group="harmony", table="score", unit="steps", fmt=".2f", higher="further from home, longer",
         ko=dict(name="으뜸조 이탈도", definition="악장이 으뜸조에서 얼마나 멀리, 얼마나 오래 떠나 있는가(1.10 신설).",
                 formula="국소 조가 이어지는 구간마다 으뜸조와의 조표 차를 내고, 구간 길이(4분음표 수)로 가중 평균한다. " + _KEY,
                 reading="0이면 악장 내내 으뜸조(또는 그 나란한조)에 머문다. 화성 주석이 있는 793악장의 중앙값은 0.308이고, 20%는 0이다. 곡집별 중앙값은 그리그 「서정 소품」 0(곡의 절반 남짓이 으뜸조를 떠나지 않는다)에서 베토벤 현악 4중주 0.772까지다.", caveat=_CAV),
         en=dict(name="Departure from the home key", definition="How far and for how long the movement leaves its home key (new in 1.10).",
                 formula="For each stretch in one local key, the signature difference from the home key, averaged with the stretch lengths (in quarter notes) as weights. " + _KEY_EN,
                 reading="0 means the movement stays in the home key (or its relative) throughout. Over the 793 movements with harmony labels the median is 0.308, and 20% are 0. Collection medians run from 0 for Grieg's Lyric Pieces (just over half the pieces never leave home) to 0.772 for Beethoven's string quartets.", caveat=_CAV_EN)),
    dict(id="off_tonic_share", layer="A", group="harmony", table="score", unit="ratio", fmt=".3f", higher="more time away",
         ko=dict(name="으뜸조 밖 시간 비율", definition="악장 길이 가운데 으뜸조(와 그 나란한조) 밖에 있는 비율(1.10 신설).",
                 formula="조표 차가 0보다 큰 구간의 길이 합 / 악장 길이. " + _KEY,
                 reading="0.3이면 악장 길이의 30%를 으뜸조 밖에서 보낸다. 793악장의 중앙값은 0.261이고, 곡집별 중앙값은 그리그 0에서 베토벤 현악 4중주 0.391까지다.", caveat=_CAV),
         en=dict(name="Time away from the home key", definition="Share of the movement spent outside the home key and its relative (new in 1.10).",
                 formula="Total length of stretches with a signature difference above 0 / length of the movement. " + _KEY_EN,
                 reading="0.3 means 30% of the movement is spent away from the home key. The median over 793 movements is 0.261; collection medians run from 0 (Grieg) to 0.391 (Beethoven's string quartets).", caveat=_CAV_EN)),
    dict(id="departure_max", layer="A", group="harmony", table="score", unit="steps", fmt=".0f", higher="further",
         ko=dict(name="최대 이탈", definition="악장이 다녀간 가장 먼 조의 조표 차(1.10 신설).",
                 formula="구간별 조표 차의 최댓값. " + _KEY,
                 reading="1이면 가장 먼 조가 5도 옆 조다. 793악장의 중앙값은 1이고, 18%는 4 이상까지 간다. 곡집별 중앙값이 4인 곳은 베토벤 현악 4중주, 리스트 「순례의 해」, 차이콥스키 「사계」다.", caveat=_CAV + " 짧게 한 번만 다녀가도 잡힌다."),
         en=dict(name="Furthest key", definition="Signature difference of the most distant key the movement visits (new in 1.10).",
                 formula="The largest signature difference over the stretches. " + _KEY_EN,
                 reading="1 means the furthest key is a neighbor on the circle of fifths. The median over 793 movements is 1, and 18% go 4 or more steps away. Collection medians of 4: Beethoven's string quartets, Liszt's Années de pèlerinage and Tchaikovsky's The Seasons.", caveat=_CAV_EN + " A single brief visit counts.")),
]
