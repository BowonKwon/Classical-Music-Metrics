"""1.12: one metric from the vector and matrix summaries (score_metrics_112.py, design 72).
Five candidates were tested against conditions fixed beforehand (gates_112.py). Two passed; of those, root-motion
variety is published. The first Fourier magnitude (semitone clustering) passed too but is withheld: its values
in tonal music cannot be given a reading (gates_112.WITHHELD). The reading quotes numbers from
data/derived/score_metrics_112_by_movement.csv; tests/test_score_112.py checks them."""

PC_KO = "음고류"  # Korean term for pitch class (the term used in Korean music-theory journals)
PAGE = ("음 분포와 화음 진행", "Pitch classes and chord progressions")
PAGE_FILE = "profiles.html"

METRICS_112 = [
    dict(id="root_motion_entropy", layer="A", group="harmony", table="score", unit="ratio", fmt=".3f", higher="more varied root motion",
         ko=dict(name="근음 진행 다양도",
                 definition="화음의 근음이 움직이는 음정이 몇 가지에 몰려 있는가, 여러 가지에 고르게 퍼져 있는가(1.12 신설).",
                 formula="같은 국소 조 안에서 근음이 바뀌는 연속 화음마다, 근음이 5도권에서 움직인 걸음 수를 낸다(5도 아래 −1, 5도 위 +1, 장2도 위 +2 …; 이명동음으로 접어 −5~+6, 0을 뺀 11가지). "
                         "그 11가지 분포의 엔트로피를 log₂11로 나눈다. 근음 변화가 30번 미만인 악장은 빈칸이다. 세는 단위는 「5도 하행 근음 진행 비율」과 같다.",
                 reading="0이면 근음이 늘 같은 음정으로 움직이고, 1이면 11가지 음정을 고르게 쓴다. 값이 있는 769악장의 중앙값은 0.765이고, 곡집별 중앙값은 0.608(슈만 「어린이 정경」)~0.866(멘델스존 현악 4중주)이다. "
                         "「5도 하행 근음 진행 비율」과의 상관계수는 −0.82다.",
                 caveat="주석자의 화음 판단을 함께 잰다. 근음 변화가 적은 악장일수록 값이 조금 낮게 나온다(근음 변화 수와의 순위 상관 0.24). 근음만 보므로 전위나 7화음 같은 화음의 종류는 구별하지 않는다. "
                        f"곡집 단위의 근음 전이 행렬과 전이 엔트로피는 「{PAGE[0]}」 면에 있다."),
         en=dict(name="Root-motion variety",
                 definition="Whether chord roots move by a few intervals or by many, evenly (new in 1.12).",
                 formula="For each pair of successive chords in the same local key whose root changes, the number of steps the root moves on the line of fifths (a fifth down −1, a fifth up +1, a major second up +2, …; folded enharmonically to −5…+6, eleven values without 0). "
                         "The entropy of the distribution over those eleven values, divided by log₂11. Blank for movements with fewer than 30 root changes. The unit counted is that of the 'falling-fifth root motion' metric.",
                 reading="0 means the root always moves by the same interval; 1 means all eleven intervals are used equally. The median over the 769 movements with a value is 0.765; collection medians run from 0.608 (Schumann's Kinderszenen) to 0.866 (Mendelssohn's string quartets). "
                         "Its correlation with the share of falling-fifth root motion is −0.82.",
                 caveat="Measures the annotators' chord judgments as well. Movements with fewer root changes come out slightly lower (rank correlation with the number of root changes 0.24). Only roots are compared, so inversions and chord types such as sevenths are not distinguished. "
                        f"Root-transition matrices and transition entropy by collection are on the '{PAGE[1]}' page.")),
]
