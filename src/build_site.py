# -*- coding: utf-8 -*-
"""Static site builder: derived CSVs + registry -> site/ (ko + en).

No external dependencies beyond pandas. Charts are inline SVG written here.
Usage: python src/build_site.py --derived data/derived --out site
"""
from __future__ import annotations

import argparse
import html
import json
import math
import shutil
from pathlib import Path

import pandas as pd

from registry import LAYERS, METRICS, SOURCES

VERSION = "1.1"
BUILD_DATE = "2026-11-01"
REPO = "https://github.com/BowonKwon/Classical-Music-Metrics"
CHANGELOG = [
    ("1.0", "2026-10-31", "바흐·베토벤 악보 14지표, 연주 6지표, 뉴욕 필 레퍼토리 4지표.", "Bach and Beethoven: 14 score metrics, 6 performance metrics, 4 NY Phil repertoire metrics."),
    ("1.1", BUILD_DATE, "모차르트 피아노 소나타 54악장(악보 14지표)과 ASAP 모차르트 연주 16개를 더했다. 뉴욕 필 레퍼토리를 전 작곡가로 넓히고 지표 5개(모차르트 점유율·발췌 비율·생존 작곡가 점유율·레퍼토리 나이·정전 회전율)와 작곡가 면을 신설했다. 레퍼토리의 세는 단위를 「프로그램의 작품 항목」에서 「프로그램의 작품」으로 바꾸어 1.0 의 레퍼토리 수치가 달라졌다(옛 값은 표의 1.0 단위 열).",
     "Added Mozart's piano sonatas (54 movements, all 14 score metrics) and 16 ASAP Mozart performances. Widened the NY Phil repertoire layer to every composer, with five new metrics (Mozart share, excerpt share, living-composer share, repertoire age, canon turnover) and composer pages. The repertoire counting unit changed from 'work entry on a program' to 'work on a program', so 1.0 repertoire values changed (old values kept in a '1.0 unit' column)."),
]

# categorical palette (validated reference palette, slots 1-3), light/dark
PAL = {"light": ["#2a78d6", "#eb6834", "#1baf7a"], "dark": ["#3987e5", "#d95926", "#199e70"]}
COMPOSER_COLOR = {"Bach": 0, "Beethoven": 1, "Mozart": 2}
COMPOSERS = ["Bach", "Beethoven", "Mozart"]
PTYPE_COLOR = {"Romantic": 1, "HI influence": 2, "HI": 0}
# Korean forms (Korean orthography for loanwords) for the top-50 NY Phil composers; others stay in the archive's spelling
KO_NAME = {
    "Beethoven, Ludwig van": "베토벤", "Wagner, Richard": "바그너", "Mozart, Wolfgang Amadeus": "모차르트", "Tchaikovsky, Pyotr Ilyich": "차이콥스키",
    "Brahms, Johannes": "브람스", "Strauss, Richard": "리하르트 슈트라우스", "Bach, Johann Sebastian": "바흐", "Dvorak, Antonín": "드보르자크",
    "Mendelssohn, Felix": "멘델스존", "Ravel, Maurice": "라벨", "Schubert, Franz": "슈베르트", "Stravinsky, Igor": "스트라빈스키",
    "Berlioz, Hector": "베를리오즈", "Debussy, Claude": "드뷔시", "Schumann, Robert": "슈만", "Haydn, Franz Joseph": "하이든",
    "Prokofiev, Sergei": "프로코피예프", "Liszt, Franz": "리스트", "Weber, Carl Maria von": "베버", "Sibelius, Jean": "시벨리우스",
    "Mahler, Gustav": "말러", "Strauss, Johann, II": "요한 슈트라우스 2세", "Saint-Saens [Saint-Saëns], Camille": "생상스", "Gershwin, George": "거슈윈",
    "Copland, Aaron": "코플런드", "Bernstein, Leonard": "번스타인", "Rachmaninoff, Sergei": "라흐마니노프", "Handel, George Frideric": "헨델",
    "Shostakovich, Dmitri": "쇼스타코비치", "Rimsky-Korsakov, Nikolai": "림스키코르사코프", "Bartok [Bartók], Béla": "버르토크", "Rossini, Gioachino": "로시니",
    "Verdi, Giuseppe": "베르디", "Musorgsky, Modest": "무소륵스키", "Chopin, Frédéric": "쇼팽", "Bizet, Georges": "비제",
    "Bruckner, Anton": "브루크너", "Grieg, Edvard": "그리그", "Elgar, Sir Edward": "엘가", "Franck, César": "프랑크",
    "Barber, Samuel": "바버", "Falla, Manuel de": "파야", "Smetana, Bedrich": "스메타나", "Ives, Charles": "아이브스",
    "Respighi, Ottorino": "레스피기", "Vivaldi, Antonio": "비발디", "Sousa, John Philip": "수자", "Bruch, Max": "브루흐",
    "Hindemith, Paul": "힌데미트", "Britten, Benjamin": "브리튼",
}
FLAG_LABEL = {
    "ko": {"person": "작곡가", "traditional": "전승곡", "anthem": "국가(國歌)", "unattributed": "작곡가 미상", "non_work": "작품 아님", "multiple": "공동·복합 표기"},
    "en": {"person": "composer", "traditional": "traditional", "anthem": "anthem", "unattributed": "unattributed", "non_work": "not a work", "multiple": "joint credit"},
}


def ordinal(n: int) -> str:
    n = int(n)
    suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suf}"


def slug(name: str) -> str:
    import re
    import unicodedata
    s = unicodedata.normalize("NFKD", re.sub(r"\[.*?\]", "", name)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

T = {
    "ko": dict(
        site="서양 고전 음악 메트릭스", tagline="악보와 연주를 숫자로 읽는다 — 바흐·베토벤·모차르트와 뉴욕 필 180년",
        nav_home="홈", nav_metrics="지표", nav_composers="작곡가", nav_reading="읽기용 판", nav_data="데이터", nav_method="방법·출처", lang_other="English",
        season="시즌", all_concerts="전체", subscription="정기공연만", v10="1.0 단위", coverage="생몰년 확인", lower="하한", upper="상한",
        perf_u1="작품 연주", perf_u2="전곡 연주", excerpt="발췌 비율", first="첫 시즌", last="마지막 시즌", n_seasons="연주된 시즌 수", born="출생", died="사망",
        rank="순위", category="구분", peak="최고 점유 시즌", top_works="많이 연주된 작품", decade_rank="10년 단위 순위", programs="프로그램",
        layer="층", definition="정의", formula="공식", reading="읽는 법", caveat="한계", source="자료원", unit="단위",
        table="표", download="CSV 내려받기", n="표본", median="중앙값", q1="1사분위", q3="3사분위", min="최소", max="최대",
        collection="모음", composer="작곡가", movements="악장 수", by_collection="모음별 분포", top="상위", bottom="하위",
        all_rows="전체 행", ranking="순위표", license="라이선스", cite="인용", built="생성일", version="판", hub="공개 자료 전체",
        coll={"chorales": "코랄(371)", "english_french_suites": "영국·프랑스 모음곡", "solo_violin_cello_flute": "무반주 바이올린·첼로·플루트",
              "piano_sonatas": "피아노 소나타", "string_quartets": "현악4중주", "chorales_kern370": "코랄(Humdrum)"},
        ptype={"Romantic": "낭만파", "HI influence": "시대연주 영향", "HI": "시대연주"},
        dist_caption="점 하나가 악장 하나. 세로선은 모음의 중앙값.",
        metric_list="지표 목록", search="필터", work="작품", mvt="악장", year="연도", bars="마디", no_harm="(화성 주석 없는 모음은 비어 있다)",
    ),
    "en": dict(
        site="Classical Music Metrics", tagline="Reading scores and performances as numbers — Bach, Beethoven, Mozart and 180 years of the New York Philharmonic",
        nav_home="Home", nav_metrics="Metrics", nav_composers="Composers", nav_reading="Reading edition", nav_data="Data", nav_method="Method & sources", lang_other="한국어",
        season="Season", all_concerts="all", subscription="subscription only", v10="1.0 unit", coverage="dated", lower="lower", upper="upper",
        perf_u1="work perf.", perf_u2="complete perf.", excerpt="excerpt share", first="first season", last="last season", n_seasons="seasons played", born="born", died="died",
        rank="rank", category="type", peak="peak season", top_works="Most performed works", decade_rank="Rank by decade", programs="programs",
        layer="Layer", definition="Definition", formula="Formula", reading="How to read it", caveat="Caveats", source="Source", unit="Unit",
        table="Table", download="Download CSV", n="n", median="median", q1="Q1", q3="Q3", min="min", max="max",
        collection="Collection", composer="Composer", movements="movements", by_collection="Distribution by collection", top="Top", bottom="Bottom",
        all_rows="All rows", ranking="Ranking", license="License", cite="Citation", built="Built", version="Version", hub="All public materials",
        coll={"chorales": "Chorales (371)", "english_french_suites": "English & French Suites", "solo_violin_cello_flute": "Solo violin, cello, flute",
              "piano_sonatas": "Piano sonatas", "string_quartets": "String quartets", "chorales_kern370": "Chorales (Humdrum)"},
        ptype={"Romantic": "Romantic", "HI influence": "HIP-influenced", "HI": "Period (HIP)"},
        dist_caption="One dot per movement. Vertical bar = collection median.",
        metric_list="All metrics", search="Filter", work="Work", mvt="Movement", year="Year", bars="Bars", no_harm="(blank for collections without harmony annotations)",
    ),
}

CSS = """
/* layout: one quiet column, serif display over sans body; low-saturation slate accent with a sand secondary */
:root{color-scheme:light;
  --bg:#f8f7f4;--bg2:#efede8;--card:#ffffff;--line:#dedbd3;--line2:#ebe8e1;
  --fg:#1d1f24;--fg2:#5a5e68;--fg3:#8a8e98;
  --accent:#3f6a9e;--accent2:#b5833f;
  --s1:#3a6fb0;--s2:#b5833f;--s3:#7f63ad;--grid:#e6e3dc;
  --shadow:0 1px 2px rgba(30,32,40,.05),0 6px 18px rgba(30,32,40,.05);
  --display:"Noto Serif KR","Source Serif 4",Georgia,"Times New Roman",serif;
  --body:"Noto Sans KR",-apple-system,"Segoe UI","Apple SD Gothic Neo",Roboto,sans-serif}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;
  --bg:#1b1c1f;--bg2:#222326;--card:#232428;--line:#34363c;--line2:#2b2d32;
  --fg:#ebe9e4;--fg2:#b3b1aa;--fg3:#80827f;
  --accent:#7ea4d6;--accent2:#d1a35f;
  --s1:#5a8ccf;--s2:#b5863a;--s3:#9078c4;--grid:#2e3035;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 20px rgba(0,0,0,.25)}}
:root[data-theme="dark"]{color-scheme:dark;
  --bg:#1b1c1f;--bg2:#222326;--card:#232428;--line:#34363c;--line2:#2b2d32;
  --fg:#ebe9e4;--fg2:#b3b1aa;--fg3:#80827f;
  --accent:#7ea4d6;--accent2:#d1a35f;
  --s1:#5a8ccf;--s2:#b5863a;--s3:#9078c4;--grid:#2e3035;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 8px 20px rgba(0,0,0,.25)}
*{box-sizing:border-box}html,body{max-width:100%;overflow-x:hidden}
body{margin:0;font:16px/1.7 var(--body);background:var(--bg);color:var(--fg);overflow-wrap:anywhere;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline;text-underline-offset:3px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
header{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line);padding:.55rem 1.1rem;display:flex;gap:1.4rem;align-items:center;flex-wrap:wrap}
header .brand{font-family:var(--display);font-weight:600;font-size:1.05rem;color:var(--fg);letter-spacing:-.01em}
header nav{display:flex;gap:1rem;flex-wrap:wrap}header nav a{color:var(--fg2);font-size:.92rem;padding:.2rem 0;border-bottom:2px solid transparent}
header nav a:hover{text-decoration:none;color:var(--fg)}header nav a.on{color:var(--fg);border-bottom-color:var(--accent2)}
header .right{margin-left:auto;display:flex;gap:.6rem;align-items:center}
header .lang{font-size:.88rem;color:var(--fg2);border:1px solid var(--line);border-radius:999px;padding:.15rem .7rem}header .lang:hover{text-decoration:none;color:var(--fg);border-color:var(--fg3)}
.theme{border:1px solid var(--line);background:transparent;color:var(--fg2);border-radius:999px;width:30px;height:30px;cursor:pointer;font-size:.9rem;line-height:1;padding:0}.theme:hover{color:var(--fg);border-color:var(--fg3)}
main{max-width:1060px;margin:0 auto;padding:1.6rem 1.1rem 4rem;min-width:0}
h1{font-family:var(--display);font-weight:600;font-size:clamp(1.6rem,3.2vw,2.2rem);line-height:1.25;letter-spacing:-.015em;margin:.3rem 0 .5rem;text-wrap:balance}
h2{font-family:var(--display);font-weight:600;font-size:1.3rem;line-height:1.3;margin:2.4rem 0 .8rem;padding-bottom:.35rem;border-bottom:1px solid var(--line);text-wrap:balance}
h3{font-size:1.02rem;margin:1.4rem 0 .4rem}
.eyebrow{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:.4rem}
.tag{display:inline-block;font-size:.74rem;letter-spacing:.04em;padding:.1rem .55rem;border-radius:999px;color:var(--fg2);background:var(--bg2);border:1px solid var(--line2)}
.tag.layer{color:var(--accent);border-color:color-mix(in srgb,var(--accent) 35%,transparent);background:color-mix(in srgb,var(--accent) 9%,transparent)}
.lead{color:var(--fg2);font-size:1.05rem;max-width:70ch;margin:0 0 1.2rem}
.hero{padding:.6rem 0 1.4rem;border-bottom:1px solid var(--line);margin-bottom:1.4rem}
.hero h1{font-size:clamp(1.9rem,4vw,2.7rem)}.hero .lead{font-size:1.12rem}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(235px,1fr));gap:.8rem;margin:.9rem 0 1.4rem}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.85rem 1rem .9rem;box-shadow:var(--shadow);color:var(--fg);transition:transform .15s,border-color .15s}
a.card:hover{text-decoration:none;transform:translateY(-2px);border-color:var(--fg3)}
.card b{display:block;margin-bottom:.25rem;font-size:.98rem;color:var(--accent)}.card small{color:var(--fg2);font-size:.86rem;line-height:1.5;display:block}
.card.layer-A{border-top:3px solid var(--s1)}.card.layer-C{border-top:3px solid var(--s2)}.card.layer-D{border-top:3px solid var(--s3)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:.8rem;margin:1.2rem 0 1.6rem}
.stat{display:block;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem;box-shadow:var(--shadow);color:var(--fg)}
.stat .n{font-family:var(--display);font-size:2rem;font-weight:600;line-height:1.1;letter-spacing:-.02em;font-variant-numeric:tabular-nums}
.stat small{display:block;color:var(--fg2);margin-top:.35rem;font-size:.86rem;line-height:1.45}
a.stat:hover{text-decoration:none;border-color:var(--fg3)}
.spec{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1.2rem;margin:1rem 0 1.4rem;box-shadow:var(--shadow)}
dl{display:grid;grid-template-columns:max-content 1fr;gap:.55rem 1.4rem;margin:0}dt{color:var(--fg3);font-size:.82rem;letter-spacing:.04em;text-transform:uppercase;padding-top:.15rem}dd{margin:0;min-width:0}
dd.formula{font-family:ui-monospace,"SF Mono",Consolas,"Noto Sans KR",monospace;font-size:.9rem;background:var(--bg2);border-radius:6px;padding:.45rem .65rem;line-height:1.6}
@media(max-width:640px){dl{grid-template-columns:1fr}dt{margin-top:.5rem}}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}
th,td{border-bottom:1px solid var(--line2);padding:.42rem .6rem;text-align:left;vertical-align:top}
thead th{color:var(--fg2);font-weight:600;font-size:.82rem;letter-spacing:.02em;cursor:pointer;white-space:nowrap;border-bottom:1px solid var(--line)}
thead th:hover{color:var(--fg)}tbody tr:nth-child(even){background:color-mix(in srgb,var(--bg2) 55%,transparent)}tbody tr:hover{background:var(--bg2)}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}td:first-child{white-space:nowrap}
.wrap{overflow-x:auto;border:1px solid var(--line);border-radius:10px;background:var(--card);padding:0 .3rem;margin:.6rem 0 1rem}.wrap table{margin:0}
figure{margin:1.2rem 0;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1rem .8rem;box-shadow:var(--shadow)}
figcaption{font-size:.86rem;color:var(--fg2);margin-top:.5rem;line-height:1.5}
svg{max-width:100%;height:auto;display:block}svg text{font-family:var(--body);fill:var(--fg2);font-size:11px}svg .ax{stroke:var(--line)}svg .grid{stroke:var(--grid)}
.legend{display:flex;gap:1.1rem;font-size:.86rem;color:var(--fg2);flex-wrap:wrap;margin:.2rem 0 .4rem}.legend span::before{content:"";display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:.4rem;vertical-align:-1px;background:var(--c)}
.note{background:color-mix(in srgb,var(--accent) 7%,var(--card));border:1px solid color-mix(in srgb,var(--accent) 25%,var(--line));border-left:4px solid var(--accent);border-radius:8px;padding:.7rem 1rem;margin:1.2rem 0;font-size:.95rem}
.prose p,.prose ul,.prose .note,.prose .lead{max-width:72ch}.prose p{margin:.8rem 0}.prose ul{padding-left:1.2rem}.prose li{margin:.3rem 0}
.src{color:var(--fg2);font-size:.92rem}.files a{display:inline-block;font-size:.85rem;background:var(--bg2);border:1px solid var(--line2);border-radius:6px;padding:.15rem .55rem;margin:.2rem .3rem .2rem 0;color:var(--fg2)}.files a:hover{color:var(--fg);text-decoration:none;border-color:var(--fg3)}
footer{border-top:1px solid var(--line);color:var(--fg3);font-size:.82rem;padding:1.2rem;text-align:center}
.filter{margin:.5rem 0}.filter input{padding:.4rem .7rem;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--fg);width:min(100%,340px);font:inherit;font-size:.9rem}
.filter input:focus{border-color:var(--accent);outline:none;box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 20%,transparent)}
.links{display:flex;gap:1.2rem;flex-wrap:wrap;margin-top:2rem;font-size:.95rem}
@media(prefers-reduced-motion:reduce){.card,a.card:hover{transition:none;transform:none}}
"""

JS = """
(function(){var k="cmm-theme",r=document.documentElement,b=document.getElementById("theme");function ap(v){if(v)r.setAttribute("data-theme",v);else r.removeAttribute("data-theme");if(b)b.textContent=v==="dark"?"\u263E":v==="light"?"\u2600":"\u25D1"}var cur=localStorage.getItem(k)||"";ap(cur);if(b)b.addEventListener("click",function(){cur=cur===""?"light":cur==="light"?"dark":"";if(cur)localStorage.setItem(k,cur);else localStorage.removeItem(k);ap(cur)})})();
document.querySelectorAll('table.sort').forEach(function(t){
  var ths=t.querySelectorAll('th');ths.forEach(function(th,i){th.addEventListener('click',function(){
    var rows=Array.from(t.tBodies[0].rows),asc=th.dataset.asc!=='1';th.dataset.asc=asc?'1':'0';
    rows.sort(function(a,b){var x=a.cells[i].dataset.v||a.cells[i].textContent,y=b.cells[i].dataset.v||b.cells[i].textContent;
      var nx=parseFloat(x),ny=parseFloat(y);if(!isNaN(nx)&&!isNaN(ny))return asc?nx-ny:ny-nx;return asc?x.localeCompare(y):y.localeCompare(x)});
    rows.forEach(function(r){t.tBodies[0].appendChild(r)})})})});
document.querySelectorAll('.filter input').forEach(function(inp){inp.addEventListener('input',function(){
  var q=inp.value.toLowerCase(),t=document.getElementById(inp.dataset.target);
  Array.from(t.tBodies[0].rows).forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(q)>=0?'':'none'})})});
"""


def esc(s) -> str:
    return html.escape("" if s is None or (isinstance(s, float) and math.isnan(s)) else str(s))


def fmt(v, spec) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    try:
        return format(v, spec)
    except Exception:
        return str(v)


def page(lang: str, title: str, body: str, depth: int = 1, desc: str = "", active: str = "") -> str:
    t = T[lang]
    root = "../" * depth
    other = "en" if lang == "ko" else "ko"
    hub_path = "" if lang == "ko" else "en/"
    nav = [("home", f"{root}{lang}/index.html", t["nav_home"]), ("metrics", f"{root}{lang}/metrics/index.html", t["nav_metrics"]),
           ("composers", f"{root}{lang}/composers/index.html", t["nav_composers"]),
           ("reading", f"{root}{lang}/reading.html", t["nav_reading"]), ("data", f"{root}{lang}/data.html", t["nav_data"]), ("method", f"{root}{lang}/method.html", t["nav_method"])]
    navh = "".join(f'<a href="{h}"{" class=\"on\"" if k == active else ""}>{n}</a>' for k, h, n in nav)
    return f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} — {t['site']}</title><meta name="description" content="{esc(desc or t['tagline'])}">
<script>(function(){{var q=new URLSearchParams(location.search).get("theme");if(q==="light"||q==="dark"){{localStorage.setItem("cmm-theme",q)}}else if(q==="auto"){{localStorage.removeItem("cmm-theme")}}var v=localStorage.getItem("cmm-theme");if(v)document.documentElement.setAttribute("data-theme",v)}})();</script>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700&family=Noto+Serif+KR:wght@600&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body>
<header><a class="brand" href="{root}{lang}/index.html">{t['site']}</a>
<nav>{navh}</nav>
<div class="right"><button id="theme" class="theme" type="button" aria-label="theme">\u25D1</button><a class="lang" href="{root}{other}/index.html">{t['lang_other']}</a></div></header>
<main>{body}</main>
<footer>{t['site']} · {t['version']} {VERSION} · {t['built']} {BUILD_DATE} · <a href="{REPO}">GitHub</a> · {t['hub']} <a href="https://bowonkwon.github.io/{hub_path}">bowonkwon.github.io</a></footer>
<script>{JS}</script></body></html>"""


# ----------------------------------------------------------------- SVG charts

def nice_ticks(lo: float, hi: float, n: int = 5) -> list[float]:
    span = hi - lo
    if span <= 0:
        return [lo]
    raw = span / n
    mag = 10 ** math.floor(math.log10(raw))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10)), key=lambda st: abs(st - raw))
    start = math.floor(lo / step) * step
    ticks, v = [], start
    while v <= hi + step * 1e-9:
        if v >= lo - step * 1e-9:
            ticks.append(round(v, 10))
        v += step
    return ticks

def svg_strip(groups: list[tuple[str, list[float], int]], spec: str, width=900, row_h=34, label_w=230, xlabel="") -> str:
    """Horizontal strip plot: one row per group, dots jittered vertically, median bar."""
    vals = [v for _, vs, _ in groups for v in vs if not math.isnan(v)]
    if not vals:
        return ""
    lo, hi = min(vals), max(vals)
    if hi == lo:
        hi = lo + 1
    pad = (hi - lo) * 0.04
    lo, hi = lo - pad, hi + pad
    pw = width - label_w - 30
    h = row_h * len(groups) + 40

    def x(v):
        return label_w + (v - lo) / (hi - lo) * pw

    out = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="strip plot">']
    # grid: 5 ticks
    for v in nice_ticks(lo, hi):
        out.append(f'<line class="grid" x1="{x(v):.1f}" y1="8" x2="{x(v):.1f}" y2="{h-30}"/>')
        out.append(f'<text x="{x(v):.1f}" y="{h-14}" text-anchor="middle">{fmt(v, spec)}</text>')
    if xlabel:
        out.append(f'<text x="{label_w+pw/2:.0f}" y="{h-2}" text-anchor="middle">{esc(xlabel)}</text>')
    import random
    rnd = random.Random(7)
    for gi, (name, vs, ci) in enumerate(groups):
        cy = 20 + gi * row_h
        out.append(f'<text x="{label_w-8}" y="{cy+4}" text-anchor="end">{esc(name)}</text>')
        col = f"var(--s{ci+1})"
        vs2 = [v for v in vs if not math.isnan(v)]
        for v in vs2:
            jy = cy + rnd.uniform(-row_h * 0.3, row_h * 0.3)
            out.append(f'<circle cx="{x(v):.1f}" cy="{jy:.1f}" r="3.4" fill="{col}" fill-opacity=".6" stroke="var(--card)" stroke-width="1"><title>{fmt(v, spec)}</title></circle>')
        if vs2:
            med = sorted(vs2)[len(vs2) // 2]
            out.append(f'<rect x="{x(med)-1.5:.1f}" y="{cy-row_h*0.42:.1f}" width="3" height="{row_h*0.84:.1f}" fill="var(--fg)" rx="1.5"><title>median {fmt(med, spec)}</title></rect>')
    out.append("</svg>")
    return "".join(out)


def svg_lines(series: list[tuple[str, list[tuple[float, float]], int]], spec: str, width=900, height=320, ylabel="", xfmt="d", end_labels=True) -> str:
    xs = [p[0] for _, pts, _ in series for p in pts]
    ys = [p[1] for _, pts, _ in series for p in pts if not math.isnan(p[1])]
    if not xs or not ys:
        return ""
    x0, x1, y0, y1 = min(xs), max(xs), 0.0, max(ys) * 1.05
    L, R, Tp, B = 60, (90 if len(series) > 1 else 20), 16, 36
    pw, ph = width - L - R, height - Tp - B

    def X(v):
        return L + (v - x0) / (x1 - x0) * pw

    def Y(v):
        return Tp + ph - (v - y0) / (y1 - y0) * ph

    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="line chart">']
    for v in nice_ticks(y0, y1):
        out.append(f'<line class="grid" x1="{L}" y1="{Y(v):.1f}" x2="{width-R}" y2="{Y(v):.1f}"/><text x="{L-6}" y="{Y(v)+4:.1f}" text-anchor="end">{fmt(v, spec)}</text>')
    step = max(1, int((x1 - x0) / 8 / 10) * 10)
    xv = int(math.ceil(x0 / step) * step)
    while xv <= x1:
        out.append(f'<text x="{X(xv):.1f}" y="{height-12}" text-anchor="middle">{xv}</text>')
        xv += step
    if ylabel:
        out.append(f'<text x="{L}" y="10">{esc(ylabel)}</text>')
    for name, pts, ci in series:
        pts = [p for p in pts if not math.isnan(p[1])]
        d = " ".join(f"{'M' if i == 0 else 'L'}{X(x):.1f},{Y(y):.1f}" for i, (x, y) in enumerate(pts))
        out.append(f'<path d="{d}" fill="none" stroke="var(--s{ci+1})" stroke-width="2" stroke-linejoin="round"/>')
        for x, y in pts:
            out.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="5" fill="transparent"><title>{esc(name)} · {x}: {fmt(y, spec)}</title></circle>')
        if len(series) > 1 and end_labels:
            lx, ly = pts[-1]
            out.append(f'<text x="{X(lx)+4:.1f}" y="{Y(ly)+4:.1f}">{esc(name)}</text>')
    out.append("</svg>")
    return "".join(out)


def svg_bars(items: list[tuple[str, float, int]], spec: str, width=900, row_h=22, label_w=240, xlabel="", zero_line=True) -> str:
    vals = [v for _, v, _ in items]
    lo, hi = min(min(vals), 0.0), max(max(vals), 0.0)
    pad = (hi - lo) * 0.05 or 1
    lo, hi = lo - pad, hi + pad
    pw = width - label_w - 30
    h = row_h * len(items) + 40

    def x(v):
        return label_w + (v - lo) / (hi - lo) * pw

    out = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="bar chart">']
    for v in nice_ticks(lo, hi):
        out.append(f'<line class="grid" x1="{x(v):.1f}" y1="6" x2="{x(v):.1f}" y2="{h-30}"/><text x="{x(v):.1f}" y="{h-14}" text-anchor="middle">{fmt(v, spec)}</text>')
    if zero_line:
        out.append(f'<line class="ax" x1="{x(0):.1f}" y1="6" x2="{x(0):.1f}" y2="{h-30}" stroke="var(--fg2)"/>')
    if xlabel:
        out.append(f'<text x="{label_w+pw/2:.0f}" y="{h-2}" text-anchor="middle">{esc(xlabel)}</text>')
    for i, (name, v, ci) in enumerate(items):
        y = 8 + i * row_h
        x0, x1 = sorted([x(0), x(v)])
        out.append(f'<text x="{label_w-8}" y="{y+row_h*0.68:.1f}" text-anchor="end">{esc(name)}</text>')
        out.append(f'<rect x="{x0:.1f}" y="{y+2}" width="{max(x1-x0,1):.1f}" height="{row_h-6}" fill="var(--s{ci+1})" rx="3"><title>{esc(name)}: {fmt(v, spec)}</title></rect>')
    out.append("</svg>")
    return "".join(out)


def legend(entries: list[tuple[str, int]]) -> str:
    return '<div class="legend">' + "".join(f'<span style="--c:var(--s{ci+1})">{esc(n)}</span>' for n, ci in entries) + "</div>"


# ----------------------------------------------------------------- tables
def table_html(df: pd.DataFrame, cols: list[tuple[str, str, str | None]], tid: str, lang: str, numeric_class=True, filt=True) -> str:
    """cols: (column, header, fmt spec or None)."""
    t = T[lang]
    out = []
    if filt:
        out.append(f'<div class="filter"><input placeholder="{t["search"]}…" data-target="{tid}"></div>')
    out.append(f'<div class="wrap"><table class="sort" id="{tid}"><thead><tr>')
    for c, hname, spec in cols:
        out.append(f'<th class="{"num" if spec else ""}">{esc(hname)}</th>')
    out.append("</tr></thead><tbody>")
    for _, r in df.iterrows():
        out.append("<tr>")
        for c, hname, spec in cols:
            v = r.get(c)
            if spec:
                out.append(f'<td class="num" data-v="{"" if pd.isna(v) else v}">{fmt(v, spec)}</td>')
            else:
                out.append(f"<td>{esc(v)}</td>")
        out.append("</tr>")
    out.append("</tbody></table></div>")
    return "".join(out)


# ----------------------------------------------------------------- data package
LICENSE_URL = {
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC-BY-NC-SA-4.0": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
}


def write_datapackage(data_dir: Path, data_files: dict) -> None:
    """Frictionless Data Package descriptor: one entry per published CSV with its
    licence, the licence of its sources and the sources themselves, so that a file
    taken on its own can be traced. Generated from DATA_FILES; nothing is typed twice."""
    resources = []
    for f, (sk, lay) in data_files.items():
        keys = sk.split("+")
        lic = "CC-BY-NC-SA-4.0" if any(k in ("dcml", "kern370", "asap") for k in keys) else "CC-BY-4.0"
        df = pd.read_csv(data_dir / f)
        res = {
            "name": f.replace("/", "-").removesuffix(".csv").lower(),
            "path": f,
            "format": "csv",
            "mediatype": "text/csv",
            "encoding": "utf-8",
            "layer": LAYERS[lay]["en"],
            "rows": int(len(df)),
            "licenses": [{"name": lic, "path": LICENSE_URL[lic]}],
            "sources": [{"title": SOURCES[k]["en"].split(". ")[0][:160], "path": SOURCES[k]["url"], "license": SOURCES[k]["license"]} for k in keys],
        }
        if f == "score_metrics_by_movement.csv":
            res["description"] = ("Mixed licence: rows with license=CC0-1.0 (DCML Bach chorales) carry no condition from the editor; "
                                  "all other rows are CC BY-NC-SA 4.0. See the per-row 'license' column.")
        resources.append(res)
    pkg = {
        "profile": "data-package",
        "name": "classical-music-metrics",
        "title": "Classical Music Metrics — derived data",
        "version": VERSION,
        "created": BUILD_DATE,
        "homepage": "https://bowonkwon.github.io/Classical-Music-Metrics/",
        "contributors": [{"title": "Bowon Kwon", "role": "author"}],
        "description": "Derived tables behind the Classical Music Metrics site. Each resource lists the licence of the table and the licences of its sources. "
                       "Original scores, MIDI and audio are not included.",
        "resources": resources,
    }
    (data_dir / "datapackage.json").write_text(json.dumps(pkg, ensure_ascii=False, indent=1), encoding="utf-8")


# ----------------------------------------------------------------- build
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--derived", default="data/derived")
    ap.add_argument("--out", default="site")
    ap.add_argument("--aliases", default="data/aliases")
    a = ap.parse_args()
    D, OUT = Path(a.derived), Path(a.out)
    for sub in ("ko", "en", "data"):  # clean children only (a local server may hold the root)
        if (OUT / sub).exists():
            shutil.rmtree(OUT / sub)
    (OUT / "data").mkdir(parents=True, exist_ok=True)

    score = pd.read_csv(D / "score_metrics_by_movement.csv")
    score = score[score["collection"] != "chorales_kern370"]
    cross = pd.read_csv(D / "chorale_crosscheck_dcml_vs_kern.csv")
    coda = pd.read_csv(D / "beethoven_symphony_coda_tempo.csv")
    cond = pd.read_csv(D / "beethoven_symphony_conductor_summary.csv")
    mvsum = pd.read_csv(D / "beethoven_symphony_movement_summary.csv")
    dur = pd.read_csv(D / "beethoven_symphony_duration_ratio.csv")
    asap_piece = pd.read_csv(D / "asap_piece_summary.csv")
    asap_perf = pd.read_csv(D / "asap_performance_metrics.csv")
    ny_season = pd.read_csv(D / "nyphil_season_summary.csv")
    ny_work = pd.read_csv(D / "nyphil_work_frequency.csv")
    ny_all = pd.read_csv(D / "nyphil_work_frequency_all_top300.csv")
    ny_comp = pd.read_csv(D / "nyphil_composer_summary.csv")
    ny_cs = pd.read_csv(D / "nyphil_composer_season.csv")
    ny_dec = pd.read_csv(D / "nyphil_decade_top.csv")
    ny_turn = pd.read_csv(D / "nyphil_canon_turnover.csv")
    ny_w50 = pd.read_csv(D / "nyphil_work_frequency_top50_composers.csv")
    AL = Path(a.aliases)
    ny_done = ny_season[ny_season["season_complete"]]

    # public CSV copies
    DATA_FILES = {
        "score_metrics_by_movement.csv": ("dcml", "A"),
        "score_metrics_kern370.csv": ("kern370", "A"),
        "chorale_crosscheck_dcml_vs_kern.csv": ("kern370", "A"),
        "beethoven_symphony_coda_tempo.csv": ("bmetr", "C"),
        "beethoven_symphony_duration_ratio.csv": ("bmetr", "C"),
        "beethoven_symphony_conductor_summary.csv": ("bmetr", "C"),
        "beethoven_symphony_movement_summary.csv": ("bmetr", "C"),
        "asap_performance_metrics.csv": ("asap", "C"),
        "asap_piece_summary.csv": ("asap", "C"),
        "nyphil_season_summary.csv": ("nyphil", "D"),
        "nyphil_composer_season.csv": ("nyphil", "D"),
        "nyphil_work_frequency.csv": ("nyphil", "D"),
        "nyphil_work_frequency_all_top300.csv": ("nyphil", "D"),
        "nyphil_orchestra_programs.csv": ("nyphil", "D"),
        "nyphil_composer_summary.csv": ("nyphil+wikidata", "D"),
        "nyphil_decade_top.csv": ("nyphil", "D"),
        "nyphil_canon_turnover.csv": ("nyphil", "D"),
        "nyphil_work_frequency_top50_composers.csv": ("nyphil", "D"),
        "aliases/nyphil_composers.csv": ("nyphil", "D"),
        "aliases/composer_wikidata.csv": ("wikidata", "D"),
    }
    (OUT / "data" / "aliases").mkdir(exist_ok=True)
    for f in DATA_FILES:
        src_f = AL / f.split("/", 1)[1] if f.startswith("aliases/") else D / f
        shutil.copy(src_f, OUT / "data" / f)
    write_datapackage(OUT / "data", DATA_FILES)

    # headline numbers (computed, used in both languages)
    med = score.groupby(["composer", "collection"]).median(numeric_only=True)
    cnt = score.groupby(["composer", "collection"]).size()
    coda_ok = coda[(~coda["unusable"]) & (coda["symphony"] != 9)]
    pt = coda_ok.groupby("ptype")["coda_tempo_diff_bpm"].agg(["median", "size", lambda x: x.quantile(.25), lambda x: x.quantile(.75)])
    pt.columns = ["median", "n", "q1", "q3"]
    ny_first, ny_last = ny_done.iloc[0], ny_done.iloc[-1]  # first and last complete season
    persons = ny_comp[ny_comp["flag"] == "person"]
    u2_top = ny_all.sort_values("complete_performances", ascending=False).iloc[0]
    wag = persons[persons["composer"] == "Wagner, Richard"].iloc[0]
    decade_med = ny_done.assign(dec=ny_done["season_start"] // 10 * 10).groupby("dec")[["living_share", "repertoire_age_median", "excerpt_share"]].median()
    asap_c = asap_piece.groupby("composer").agg(n_pieces=("title", "size"), n_perf=("n_performances", "sum"),
                                                 cv=("tempo_cv_across_performers", "median"), rub=("local_tempo_change_median", "median"),
                                                 vel=("velocity_sd_median", "median"))
    H = dict(
        n_movements=int(len(score)), n_bach=int((score.composer == "Bach").sum()), n_beet=int((score.composer == "Beethoven").sum()),
        n_notes=int(score["n_notes"].sum()),
        rom=pt.loc["Romantic", "median"], hii=pt.loc["HI influence", "median"], hi=pt.loc["HI", "median"],
        rom_n=int(pt.loc["Romantic", "n"]), hii_n=int(pt.loc["HI influence", "n"]), hi_n=int(pt.loc["HI", "n"]),
        rom_q1=pt.loc["Romantic", "q1"], rom_q3=pt.loc["Romantic", "q3"], hi_q1=pt.loc["HI", "q1"], hi_q3=pt.loc["HI", "q3"],
        n_cond=int(cond["conductor"].nunique()), n_tracks=int(len(coda)),
        asap_bach_perf=int(asap_c.loc["Bach", "n_perf"]), asap_beet_perf=int(asap_c.loc["Beethoven", "n_perf"]),
        asap_bach_pieces=int(asap_c.loc["Bach", "n_pieces"]), asap_beet_pieces=int(asap_c.loc["Beethoven", "n_pieces"]),
        asap_bach_cv=asap_c.loc["Bach", "cv"], asap_beet_cv=asap_c.loc["Beethoven", "cv"],
        asap_bach_rub=asap_c.loc["Bach", "rub"], asap_beet_rub=asap_c.loc["Beethoven", "rub"],
        asap_bach_vel=asap_c.loc["Bach", "vel"], asap_beet_vel=asap_c.loc["Beethoven", "vel"],
        ny_programs=int(ny_season["n_programs"].sum()), ny_seasons=int(len(ny_season)),
        ny_first_season=ny_first["season"], ny_last_season=ny_last["season"],
        ny_first_beet=ny_first["beethoven_share"], ny_last_beet=ny_last["beethoven_share"],
        ny_first_hhi=ny_first["hhi"], ny_last_hhi=ny_last["hhi"], ny_first_comp=int(ny_first["distinct_composers"]), ny_last_comp=int(ny_last["distinct_composers"]),
        ny_top_work=ny_work.iloc[0]["work_title"], ny_top_n=int(ny_work.iloc[0]["performances"]), ny_top_rank=int(ny_work.iloc[0]["rank_all_composers"]),
        ny_all_top=ny_all.iloc[0]["work_title"], ny_all_top_composer=ny_all.iloc[0]["composer"], ny_all_top_n=int(ny_all.iloc[0]["performances"]),
        ny_programs_complete=int(ny_done["n_programs"].sum()),
        faster_n=int((coda_ok["coda_tempo_diff_bpm"] > 0).sum()), faster_of=int(len(coda_ok)),
        cross_min_r=float(cross["pearson_r"].min()), cross_n=int(cross["n"].iloc[0]),
        n_moz=int((score.composer == "Mozart").sum()),
        asap_moz_perf=int(asap_c.loc["Mozart", "n_perf"]) if "Mozart" in asap_c.index else 0,
        asap_moz_pieces=int(asap_c.loc["Mozart", "n_pieces"]) if "Mozart" in asap_c.index else 0,
        ny_u1=int(ny_season["work_performances"].sum()), ny_u0=int(ny_season["work_performances_u0"].sum()),
        ny_u2=int(ny_season["complete_performances"].sum()),
        ny_persons=int(len(persons)), ny_strings=int(len(ny_comp)),
        ny_first_moz=ny_first["mozart_share"], ny_last_moz=ny_last["mozart_share"],
        ny_last_living=ny_last["living_share"], ny_last_living_lo=ny_last["living_share_low"], ny_last_living_hi=ny_last["living_share_high"],
        ny_first_age=ny_first["repertoire_age_median"], ny_last_age=ny_last["repertoire_age_median"],
        ny_u2_top=u2_top["work_title"], ny_u2_top_composer=u2_top["composer"], ny_u2_top_n=int(u2_top["complete_performances"]),
        ny_all_top_u2=int(ny_all.iloc[0]["complete_performances"]),
        wag_rank_u1=int(wag["rank_u1"]), wag_rank_u2=int(wag["rank_u2"]), wag_excerpt=wag["excerpt_share"],
        dec_living_1840=decade_med.loc[1840, "living_share"], dec_living_1990=decade_med.loc[1990, "living_share"], dec_living_2020=decade_med.loc[2020, "living_share"],
        dec_excerpt_1840=decade_med.loc[1840, "excerpt_share"], dec_excerpt_1990=decade_med.loc[1990, "excerpt_share"], dec_excerpt_2020=decade_med.loc[2020, "excerpt_share"],
        turn_med10=float(ny_turn["jaccard_top10"].median()),
        **{f"son_{c[:3].lower()}_{k}": med.loc[(c, "piano_sonatas"), k] for c in ("Beethoven", "Mozart")
           for k in ("chromatic_ratio", "applied_chord_ratio", "local_key_changes_per_100_measures", "top_leap_ratio", "chords_per_measure", "pitch_range_semitones")},
    )
    (OUT / "data" / "headline.json").write_text(json.dumps(H, ensure_ascii=False, indent=1, default=str), encoding="utf-8")

    for lang in ("ko", "en"):
        t = T[lang]
        base = OUT / lang
        (base / "metrics").mkdir(parents=True)
        L = lambda m: m[lang]  # noqa: E731

        # ---------------- metric pages
        for m in METRICS:
            ml = L(m)
            body = [f'<div class="eyebrow"><span class="tag layer">{LAYERS[m["layer"]][lang]}</span><span class="tag">{t["unit"]}: {esc(m["unit"])}</span></div>',
                    f"<h1>{esc(ml['name'])}</h1><p class='lead'>{esc(ml['definition'])}</p>",
                    f"<div class='spec'><dl><dt>{t['formula']}</dt><dd class='formula'>{esc(ml['formula'])}</dd><dt>{t['reading']}</dt><dd>{esc(ml['reading'])}</dd><dt>{t['caveat']}</dt><dd>{esc(ml['caveat'])}</dd></dl></div>"]
            if m["table"] == "score":
                groups, summ = [], []
                for (comp, coll), g in score.groupby(["composer", "collection"], sort=False):
                    vs = g[m["id"]].astype(float).tolist()
                    if all(math.isnan(v) for v in vs):
                        continue
                    name = f"{comp} · {t['coll'][coll]}"
                    groups.append((name, vs, COMPOSER_COLOR[comp]))
                    s = pd.Series([v for v in vs if not math.isnan(v)])
                    summ.append(dict(group=name, n=len(s), median=s.median(), q1=s.quantile(.25), q3=s.quantile(.75), mn=s.min(), mx=s.max()))
                order = ["chorales", "english_french_suites", "solo_violin_cello_flute", "string_quartets", "piano_sonatas"]
                groups.sort(key=lambda g: order.index(next(k for k in order if t["coll"][k] in g[0])))
                summ.sort(key=lambda s: order.index(next(k for k in order if t["coll"][k] in s["group"])))
                body.append(f"<h2>{t['by_collection']}</h2>{legend([(c, COMPOSER_COLOR[c]) for c in COMPOSERS])}<figure>{svg_strip(groups, m['fmt'], xlabel=m['unit'])}<figcaption>{t['dist_caption']} {t['no_harm'] if m['group']=='harmony' else ''}</figcaption></figure>")
                sdf = pd.DataFrame(summ)
                body.append(table_html(sdf, [("group", t["collection"], None), ("n", t["n"], "d"), ("median", t["median"], m["fmt"]), ("q1", t["q1"], m["fmt"]), ("q3", t["q3"], m["fmt"]), ("mn", t["min"], m["fmt"]), ("mx", t["max"], m["fmt"])], f"s_{m['id']}", lang, filt=False))
                rk = score.dropna(subset=[m["id"]]).sort_values(m["id"], ascending=False).copy()
                rk["work"] = rk["work"].where(rk["work"].notna() & (rk["work"] != ""), rk["piece_id"])
                rk["composed_start"] = rk["composed_start"].astype(str).where(rk["composed_start"].astype(str).str.match(r"^\d{4}"), "")
                body.append(f"<h2>{t['ranking']}</h2>" + table_html(rk, [("composer", t["composer"], None), ("work", t["work"], None), ("movement_title", t["mvt"], None), ("composed_start", t["year"], None), ("n_measures", t["bars"], "d"), (m["id"], ml["name"], m["fmt"])], f"r_{m['id']}", lang))
                src = "dcml"
            elif m["table"] == "coda":
                items = [(f"{r.conductor.split(',')[0]} ({t['ptype'][r.ptype]}, {str(r.date)[:4]})", r.median_diff_bpm, PTYPE_COLOR[r.ptype]) for r in cond.itertuples()]
                body.append(legend([(t["ptype"][k], v) for k, v in PTYPE_COLOR.items()]))
                body.append(f"<figure>{svg_bars(items, '+.1f', xlabel='bpm')}<figcaption>{'지휘자별 중앙값(교향곡 1~8번 33악장). 녹음 연도는 괄호 안.' if lang=='ko' else 'Median per conductor over 33 movements of Symphonies 1–8; recording years in parentheses.'}</figcaption></figure>")
                body.append(table_html(cond, [("conductor", "Conductor", None), ("ptype", "Style", None), ("date", "Rec.", None), ("n_movements", t["n"], "d"), ("median_diff_bpm", t["median"], "+.1f"), ("q1_diff_bpm", t["q1"], "+.1f"), ("q3_diff_bpm", t["q3"], "+.1f"), ("n_rectified", "rectified", "d")], "cond", lang))
                src = "bmetr"
            elif m["table"] == "duration":
                mv = mvsum.assign(label=mvsum["symphony"].astype(str) + "/" + mvsum["movement"].astype(str) + " " + mvsum["main_character"].fillna("") + " ♩=" + mvsum["main_mark"].astype(int).astype(str))
                body.append(f"<figure>{svg_bars([(r.label, r.ratio_no_rep_median, 1) for r in mv.itertuples()], '.2f', xlabel='×', zero_line=False)}<figcaption>{'악장별 중앙값(지휘자 36명), 반복 없음 가정.' if lang=='ko' else 'Median over 36 conductors per movement, assuming no repeats.'}</figcaption></figure>")
                body.append(table_html(mv, [("label", "Movement", None), ("n", t["n"], "d"), ("duration_median_s", "sec (median)", ".0f"), ("ratio_no_rep_median", "no repeats", ".2f"), ("ratio_with_rep_median", "with repeats", ".2f")], "mv", lang))
                src = "bmetr"
            elif m["table"] == "asap_piece":
                groups = [(c, asap_piece[asap_piece.composer == c][m["id"]].astype(float).tolist(), COMPOSER_COLOR[c]) for c in ("Bach", "Beethoven")]
                two = m["id"] == "tempo_cv_across_performers"
                cap_ko = "점 하나가 곡 하나" + ("(연주 2개 이상인 곡만)" if two else "(연주가 하나인 곡은 그 연주의 값)") + ". 모차르트(6곡·연주 16개)는 소표본이라 차트에서 빼고 아래 표에만 둔다."
                cap_en = "One dot per piece" + (" (pieces with two or more performances only)" if two else " (a single-performance piece shows that performance's value)") + ". Mozart (6 pieces, 16 performances) is too small a sample for the chart and appears only in the table below."
                body.append(f"<figure>{svg_strip(groups, m['fmt'], xlabel=m['unit'])}<figcaption>{cap_ko if lang=='ko' else cap_en}</figcaption></figure>")
                body.append(table_html(asap_piece.sort_values(m["id"], ascending=False), [("composer", t["composer"], None), ("title", "Piece", None), ("n_performances", "perf.", "d"), ("tempo_mean_bpm_median", "tempo (median)", ".0f"), (m["id"], ml["name"], m["fmt"])], "ap", lang))
                src = "asap"
            elif m["table"] == "nyphil_turnover":
                tt = ny_turn.dropna(subset=["jaccard_top10"])
                ser = [("상위 10" if lang == "ko" else "top 10", [(int(r.decade), float(r.jaccard_top10)) for r in tt.itertuples()], 0),
                       ("상위 25" if lang == "ko" else "top 25", [(int(r.decade), float(r.jaccard_top25)) for r in tt.itertuples()], 1)]
                body.append(f"<figure>{svg_lines(ser, m['fmt'], ylabel='Jaccard')}<figcaption>{'10년 단위. 점은 앞 10년과의 겹침.' if lang=='ko' else 'By decade; each point is the overlap with the previous decade.'}</figcaption></figure>")
                ko_ = lang == "ko"
                body.append(table_html(ny_turn, [("decade", "10년" if ko_ else "decade", None), ("n_seasons", "시즌 수" if ko_ else "seasons", "d"), ("jaccard_top10", "상위 10" if ko_ else "top 10", ".2f"), ("jaccard_top25", "상위 25" if ko_ else "top 25", ".2f"), ("new_in_top10", "상위 10 신규 진입" if ko_ else "new in top 10", None)], "turn", lang, filt=False))
                body.append(f"<h2>{t['decade_rank']}</h2>")
                piv = ny_dec[ny_dec["rank"] <= 10].assign(name=lambda d_: d_["composer"].map(lambda c: KO_NAME.get(c, c.split(',')[0]) if lang == "ko" else c.split(',')[0]))
                piv = piv.pivot(index="rank", columns="decade", values="name").reset_index()
                piv.columns = [str(c) for c in piv.columns]
                body.append(table_html(piv, [(c, c if c != "rank" else t["rank"], None) for c in piv.columns], "dec", lang, filt=False))
                src = "nyphil"
            else:  # nyphil season
                done = ny_done
                ci_main = COMPOSER_COLOR.get(next((c for c in COMPOSERS if c.lower() in m["id"]), ""), 0)
                ser = [(t["all_concerts"], [(int(r.season_start), float(r[m["id"]])) for _, r in done.iterrows()], ci_main)]
                if m.get("sub"):
                    ser.append((t["subscription"], [(int(r.season_start), float(r[m["id"] + "_sub"])) for _, r in done.iterrows() if not pd.isna(r[m["id"] + "_sub"])], (ci_main + 1) % 3))
                if m.get("band"):
                    lo, hi = m["band"]
                    ser = [(ml["name"], ser[0][1], 0), (t["lower"], [(int(r.season_start), float(r[lo])) for _, r in done.iterrows()], 2), (t["upper"], [(int(r.season_start), float(r[hi])) for _, r in done.iterrows()], 1)]
                if len(ser) > 1:
                    body.append(legend([(n, ci) for n, _, ci in ser]))
                cap = ('완결 시즌별(1842–43 ~ %s). 진행 중인 시즌은 표에만 있다.' % ny_last["season"]) if lang == "ko" else ('Completed seasons, 1842–43 to %s. The season in progress is in the table only.' % ny_last["season"])
                body.append(f"<figure>{svg_lines(ser, m['fmt'], ylabel=m['unit'], end_labels=False)}<figcaption>{cap}</figcaption></figure>")
                cols = [("season", t["season"], None), ("n_programs", t["programs"], "d"), ("work_performances", t["perf_u1"], "d"), (m["id"], ml["name"], m["fmt"])]
                if m.get("sub"):
                    cols.append((m["id"] + "_sub", t["subscription"], m["fmt"]))
                if m.get("v10"):
                    cols.append((m["v10"], t["v10"], m["fmt"]))
                if m.get("band"):
                    cols += [(m["band"][0], t["lower"], m["fmt"]), (m["band"][1], t["upper"], m["fmt"])]
                if m["id"] in ("living_share", "repertoire_age_median"):
                    cols.append(("dated_coverage", t["coverage"], ".0%"))
                body.append(table_html(ny_season.iloc[::-1], cols, "ny", lang))
                if m.get("composer_col"):
                    big = persons[persons["perf_u1"] >= 200].sort_values(m["composer_col"], ascending=False).copy()
                    big["name"] = big["composer"].map(lambda c: f"{KO_NAME[c]} ({c})" if lang == "ko" and c in KO_NAME else c)
                    body.append(f"<h2>{'작곡가별 (작품 연주 200회 이상)' if lang=='ko' else 'By composer (200+ work performances)'}</h2>")
                    body.append(table_html(big, [("name", t["composer"], None), ("perf_u1", t["perf_u1"], "d"), ("perf_u2", t["perf_u2"], "d"), (m["composer_col"], ml["name"], m["fmt"]), ("rank_u1", t["rank"] + " (U1)", ".0f"), ("rank_u2", t["rank"] + " (U2)", ".0f")], "bycomp", lang))
                src = "nyphil" if m["id"] not in ("living_share", "repertoire_age_median") else ["nyphil", "wikidata"]
            srcs = src if isinstance(src, list) else [src]
            body.append(f"<h2>{t['source']}</h2>")
            for sk in srcs:
                s = SOURCES[sk]
                body.append(f"<p class='src'>{esc(s[lang])} <a href='{s['url']}'>{s['url']}</a> · {t['license']}: {esc(s['license'])}</p>")
            files = [f for f, (sk, _) in DATA_FILES.items() if set(sk.split("+")) & set(srcs)]
            body.append("<p class='files'>" + "".join(f'<a href="../../data/{f}">{f}</a>' for f in files) + "</p>")
            (base / "metrics" / f"{m['id']}.html").write_text(page(lang, ml["name"], "".join(body), depth=2, desc=ml["definition"], active="metrics"), encoding="utf-8")

        # ---------------- metrics index
        body = [f"<h1>{t['metric_list']}</h1>"]
        for lay in ("A", "C", "D"):
            body.append(f"<h2>{LAYERS[lay][lang]}</h2><div class='cards'>")
            for m in METRICS:
                if m["layer"] == lay:
                    body.append(f"<a class='card layer-{lay}' href='{m['id']}.html'><b>{esc(L(m)['name'])}</b><small>{esc(L(m)['definition'])}</small></a>")
            body.append("</div>")
        (base / "metrics" / "index.html").write_text(page(lang, t["nav_metrics"], "".join(body), depth=2, active="metrics"), encoding="utf-8")

        # ---------------- composers: ranking of every name + top-50 profiles
        (base / "composers").mkdir()
        top50 = set(persons[persons["rank_u1"] <= 50]["composer"])
        cdf = ny_comp.copy()
        cdf["cat"] = cdf["flag"].map(FLAG_LABEL[lang])

        def disp(c):
            return f"{KO_NAME[c]} · {c}" if lang == "ko" and c in KO_NAME else c

        cdf["name_html"] = cdf["composer"].map(lambda c: f"<a href='{slug(c)}.html'>{esc(disp(c))}</a>" if c in top50 else esc(disp(c)))
        intro = ("뉴욕 필하모닉 공연 기록(1842–43 ~ %s)에 작품이 오른 모든 이름 %s개. 사람 작곡가 %s명과 전승곡·국가·작곡가 미상·공동 표기 등 사람이 아닌 표기를 구분했다. 순위는 사람 작곡가만 매긴다. 상위 50명은 이름을 누르면 프로필 면으로 간다. 작품 연주(U1)는 한 프로그램의 작품 하나 × 연주회 수, 전곡 연주(U2)는 그중 발췌가 아닌 것이다."
                 % (ny_season.iloc[-1]["season"], f"{H['ny_strings']:,}", f"{H['ny_persons']:,}")) if lang == "ko" else (
                 "Every name with a work in the New York Philharmonic Performance History (1842–43 to %s): %s names, of which %s are individual composers; traditional, anthem, unattributed and joint credits are labelled separately and not ranked. The top 50 link to profile pages. Work performances (U1) = one work on a program × its concerts; complete performances (U2) exclude excerpts."
                 % (ny_season.iloc[-1]["season"], f"{H['ny_strings']:,}", f"{H['ny_persons']:,}"))
        rows = []
        for r in cdf.itertuples():
            rows.append("<tr>" + "".join([
                f"<td class='num' data-v='{'' if pd.isna(r.rank_u1) else int(r.rank_u1)}'>{'' if pd.isna(r.rank_u1) else int(r.rank_u1)}</td>",
                f"<td>{r.name_html}</td><td>{esc(r.cat)}</td>",
                f"<td class='num' data-v='{r.perf_u1}'>{int(r.perf_u1):,}</td><td class='num' data-v='{r.perf_u2}'>{int(r.perf_u2):,}</td>",
                f"<td class='num' data-v='{r.excerpt_share}'>{r.excerpt_share:.0%}</td>",
                f"<td>{esc(r.first_season)}</td><td>{esc(r.last_season)}</td><td class='num' data-v='{r.n_seasons}'>{int(r.n_seasons)}</td>",
                f"<td class='num'>{'' if pd.isna(r.birth_year) else int(r.birth_year)}</td><td class='num'>{'' if pd.isna(r.death_year) else int(r.death_year)}</td>",
            ]) + "</tr>")
        heads = [(t["rank"], 1), (t["composer"], 0), (t["category"], 0), (t["perf_u1"], 1), (t["perf_u2"], 1), (t["excerpt"], 1), (t["first"], 0), (t["last"], 0), (t["n_seasons"], 1), (t["born"], 1), (t["died"], 1)]
        tab = (f'<div class="filter"><input placeholder="{t["search"]}…" data-target="allcomp"></div><div class="wrap"><table class="sort" id="allcomp"><thead><tr>'
               + "".join(f'<th class="{"num" if n else ""}">{esc(h)}</th>' for h, n in heads) + "</tr></thead><tbody>" + "".join(rows) + "</tbody></table></div>")
        n_dated = int(ny_comp["wikidata_status"].isin(["ok", "ok_manual"]).sum())
        note = (f"생몰년은 Wikidata(10회 이상 연주된 작곡가를 맞춰 검수, {n_dated}명 확정)에서 왔고 나머지는 비어 있다. 「P.D.Q. 바흐」는 피터 시켈리로 합쳤다. 한국어 표기는 상위 50명에만 붙였고, 국립국어원 외래어 표기 용례를 따랐다(용례에 없는 아이브스는 서울시립교향악단 표기)." if lang == "ko" else
                f"Birth and death years come from Wikidata (composers with 10+ performances, matched and reviewed; {n_dated} confirmed); the rest are blank. 'P.D.Q. Bach' is merged into Peter Schickele.")
        body = [f"<h1>{t['nav_composers']}</h1><p class='lead'>{esc(intro)}</p>", tab, f"<p class='src'>{esc(note)}</p>",
                "<p class='files'>" + "".join(f'<a href="../../data/{f}">{f}</a>' for f in ("nyphil_composer_summary.csv", "aliases/nyphil_composers.csv", "aliases/composer_wikidata.csv")) + "</p>"]
        (base / "composers" / "index.html").write_text(page(lang, t["nav_composers"], "".join(body), depth=2, active="composers"), encoding="utf-8")

        for c in sorted(top50):
            r = persons[persons["composer"] == c].iloc[0]
            g = ny_cs[(ny_cs["composer"] == c)].set_index("season")
            pts1 = [(int(s_.season_start), float(g["share_u1"].get(s_.season, 0.0))) for s_ in ny_done.itertuples()]
            pts2 = [(int(s_.season_start), float(g["perf_u2"].get(s_.season, 0.0)) / float(s_.work_performances)) for s_ in ny_done.itertuples()]
            title = disp(c)
            life = "" if pd.isna(r.birth_year) else f"{int(r.birth_year)}–{'' if pd.isna(r.death_year) else int(r.death_year)}"
            facts = [(t["rank"] + " (U1 / U2)", f"{int(r.rank_u1)} / {int(r.rank_u2)}"), (t["perf_u1"], f"{int(r.perf_u1):,}"), (t["perf_u2"], f"{int(r.perf_u2):,}"),
                     (t["excerpt"], f"{r.excerpt_share:.0%}"), (t["first"] + " – " + t["last"], f"{r.first_season} – {r.last_season}"), (t["n_seasons"], f"{int(r.n_seasons)}"),
                     (t["peak"], f"{r.peak_season} ({r.peak_share:.1%})"), (t["born"] + " – " + t["died"], life or "—")]
            body = [f"<div class='eyebrow'><span class='tag layer'>{LAYERS['D'][lang]}</span><span class='tag'>NY Phil</span></div><h1>{esc(title)}</h1>",
                    "<div class='spec'><dl>" + "".join(f"<dt>{esc(k)}</dt><dd>{esc(v)}</dd>" for k, v in facts) + "</dl></div>",
                    legend([(t["perf_u1"], 0), (t["perf_u2"] + (" (같은 분모)" if lang == "ko" else " (same denominator)"), 1)]),
                    f"<figure>{svg_lines([(t['perf_u1'], pts1, 0), (t['perf_u2'], pts2, 1)], '.1%', ylabel='share', end_labels=False)}<figcaption>{'완결 시즌별. 두 선 모두 그 시즌의 작품 연주 전체를 분모로 한다 — 위 선은 이 작곡가의 작품 연주, 아래 선은 그중 전곡 연주(악장 표시 없는 연주)의 몫이다. 두 선의 간격이 그 시즌 전체에서 이 작곡가의 발췌 연주가 차지한 몫이다.' if lang=='ko' else 'Completed seasons. Both lines use the season\'s total work performances as denominator: the upper line is this composer\'s work performances, the lower line the part of them that are complete (no movement named). The gap is this composer\'s excerpts as a share of the whole season.'}</figcaption></figure>"]
            dr = ny_dec[ny_dec["composer"] == c][["decade", "rank", "share"]].astype({"decade": int, "rank": int})
            dr["decade"] = dr["decade"].astype(str) + ("년대" if lang == "ko" else "s")
            if len(dr):
                body.append(f"<h2>{t['decade_rank']}</h2>" + table_html(dr, [("decade", "10년" if lang == "ko" else "decade", None), ("rank", t["rank"], "d"), ("share", "share", ".1%")], "dr", lang, filt=False))
            ww = ny_w50[ny_w50["composer"] == c]
            body.append(f"<h2>{t['top_works']}</h2>" + table_html(ww, [("work_title", t["work"], None), ("performances", t["perf_u1"], "d"), ("complete_performances", t["perf_u2"], "d"), ("first_season", t["first"], None), ("last_season", t["last"], None), ("rank", t["rank"] + " (all)", "d")], "ww", lang, filt=False))
            body.append(f"<p class='links'><a href='index.html'>← {t['nav_composers']}</a><a href='../metrics/excerpt_share.html'>{esc(next(L(m)['name'] for m in METRICS if m['id']=='excerpt_share'))} →</a></p>")
            (base / "composers" / f"{slug(c)}.html").write_text(page(lang, title, "".join(body), depth=2, desc=title, active="composers"), encoding="utf-8")

        # ---------------- data page
        body = [f"<h1>{t['nav_data']}</h1>"]
        rows = []
        for f, (sk, lay) in DATA_FILES.items():
            n = len(pd.read_csv(OUT / "data" / f))
            derived = "CC BY-NC-SA 4.0" if sk in ("dcml", "kern370", "asap") else "CC BY 4.0"
            src_lic = " + ".join(f"{esc(SOURCES[k]['license'])} ({'NY Phil' if k == 'nyphil' else k.capitalize()})" for k in sk.split("+")) if "+" in sk else esc(SOURCES[sk]["license"])
            rows.append(f"<tr><td><a href='../data/{f}'>{f}</a></td><td>{LAYERS[lay][lang]}</td><td class='num'>{n:,}</td><td>{src_lic}</td><td>{derived}</td></tr>")
        body.append(f"<div class='wrap'><table><thead><tr><th>File</th><th>{t['layer']}</th><th class='num'>rows</th><th>{'원자료 라이선스' if lang=='ko' else 'Source license'}</th><th>{'이 표의 라이선스' if lang=='ko' else 'This table'}</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>")
        body.append("<p>" + ("「이 표의 라이선스」는 엮은이가 파생 표에 붙인 조건이다. CC BY-NC-SA 원자료(DCML·Sapp·ASAP)에서 만든 표는 그 조건을 이어받아 CC BY-NC-SA 4.0 으로 둔다. DCML 코랄(CC0)에서 나온 행은 NC-SA 행과 한 파일(score_metrics_by_movement.csv)에 섞여 있어 파일 단위로는 NC-SA 로 표시하지만, 그 361행만 따로 쓰는 데에는 엮은이가 조건을 붙이지 않는다. 뉴욕 필·Wikidata 원자료는 CC0 이고, bmetr 는 MIT(코드나 자료를 복제할 때 저작권·허락 고지를 남기는 조건)다. 이 표들은 원자료를 복제한 것이 아니라 엮은이가 계산하거나 검수해 더한 수치이며(aliases/ 의 작곡가 분류표·Wikidata 매칭표 포함), 그 부분에 CC BY 4.0 을 붙인다. bmetr 에서 온 표를 쓸 때는 원저자(Martín-Castro & Ucar 2020)를 함께 밝혀 주기 바란다. 원본 악보·MIDI·음원은 이 저장소에 없다." if lang == "ko" else "'This table' is the licence the editor attaches to the derived table. Tables built from CC BY-NC-SA sources (DCML, Sapp, ASAP) carry that condition forward as CC BY-NC-SA 4.0. Rows from the DCML chorales (CC0) sit in the same file as NC-SA rows (score_metrics_by_movement.csv), so the file is marked NC-SA, but the editor attaches no condition to those 361 rows used on their own. The NY Phil and Wikidata sources are CC0; bmetr is MIT (copies of its code or data must keep the copyright and permission notice). These tables are not copies of the sources but numbers the editor computed or reviewed (including the composer classification and Wikidata matching tables under aliases/), and CC BY 4.0 applies to that part. When using tables derived from bmetr, please also credit its authors (Martín-Castro & Ucar 2020). No original scores, MIDI or audio are redistributed here.") + "</p>")
        body.append("<p>" + ("파일마다 이 표의 라이선스·원자료·원자료 라이선스를 기계가 읽을 수 있게 적은 목록: <a href='../data/datapackage.json'>datapackage.json</a>(Frictionless Data Package). CSV 만 따로 가져갈 때도 이 목록을 함께 두기 바란다." if lang == "ko" else
                            "A machine-readable list of each file's licence, sources and source licences: <a href='../data/datapackage.json'>datapackage.json</a> (Frictionless Data Package). Please keep it with any CSV you redistribute.") + "</p>")
        (base / "data.html").write_text(page(lang, t["nav_data"], "".join(body), active="data"), encoding="utf-8")

        # ---------------- method page
        body = [f"<h1>{t['nav_method']}</h1>"]
        if lang == "ko":
            body.append("""<h2>원칙</h2><ul>
<li><b>지표 하나에 정의·공식·표본·한계를 함께 둔다.</b> 야구의 세이버메트릭스가 설득력을 갖는 이유가 그것이라서다.</li>
<li><b>기술 통계와 해석을 가른다.</b> 「반음계 비율이 높다」는 측정이고, 「그래서 더 혁신적이다」는 해석이다. 이 사이트는 앞의 것만 한다.</li>
<li><b>같은 코드가 모든 작곡가를 잰다.</b> 바흐·베토벤·모차르트를 다른 식으로 재면 비교가 아니다.</li>
<li><b>원자료는 공개 코퍼스만 쓴다.</b> 악보·MIDI·음원은 재배포하지 않고 수치만 낸다.</li></ul>""")
        else:
            body.append("""<h2>Principles</h2><ul>
<li><b>Every metric carries its definition, formula, sample and caveats.</b> That is what makes baseball's sabermetrics persuasive.</li>
<li><b>Measurement is kept apart from interpretation.</b> "The chromatic ratio is higher" is a measurement; "so it is more innovative" is a reading. This site does only the former.</li>
<li><b>One codebase measures every composer.</b> Measuring Bach, Beethoven and Mozart differently would not be a comparison.</li>
<li><b>Only open corpora.</b> Scores, MIDI and audio are not redistributed; only the numbers are.</li></ul>""")
        body.append(f"<h2>{t['source']}</h2>")
        for k, s in SOURCES.items():
            body.append(f"<p><b>{k}</b> — {esc(s[lang])} <a href='{s['url']}'>{s['url']}</a> · {t['license']}: {esc(s['license'])}</p>")
        if lang == "ko":
            body.append(f"""<h2>레퍼토리를 세는 단위 (1.1)</h2>
<p>뉴욕 필 기록은 프로그램마다 작품 항목을 적는다. 같은 작품에서 서곡과 아리아를 따로 연주하면 항목이 둘이 된다. 1.0 은 항목 하나를 한 번으로 셌고(U0, 전체 {H['ny_u0']:,}건), 1.1 은 <b>한 프로그램에서 아카이브가 같은 작품 번호로 적은 항목을 한 번</b>으로 센다(U1, {H['ny_u1']:,}건). 같은 원작이라도 다른 작품 번호를 받은 편곡은 따로 센다. 어느 쪽이든 그 프로그램의 연주회 수를 곱한다. 그 가운데 악장·부분 표시가 하나도 없는 것을 전곡 연주(U2, {H['ny_u2']:,}건)로 따로 센다. U2는 기재에서 나온 대리 지표다 — 작품 번호 뒷부분이 부분을 가리키는데 악장 칸이 빈 73쌍은 전곡으로, 표시 없는 항목과 발췌 항목이 섞인 105쌍은 발췌로 잡힌다. 대상은 작곡가가 적힌 작품이 하나라도 있는 프로그램 {H['ny_programs']:,}개다(원자료의 프로그램 기록은 15,074개).</p>
<p>단위에 따라 순위가 달라진다. 바그너는 작품 연주(U1)로 {H['wag_rank_u1']}위지만 발췌가 {H['wag_excerpt']:.0%}여서 전곡 연주(U2)로는 {H['wag_rank_u2']}위다. 그래서 점유율·집중도는 U1 로 내고, 발췌 비율을 따로 지표로 둔다. 1.0 의 네 지표는 표의 「1.0 단위」 열에 옛 정의 그대로 다시 계산해 두었다(완결 시즌 전부에서 1.0 공개값과 일치).</p>
<p>「정기공연만」 계열은 행사 유형이 Subscription Season 인 연주회만 센다. 스타디움·공원·투어·청소년 음악회를 뺀 값이다.</p>
<h2>작곡가 이름 정리</h2>
<p>아카이브의 작곡가 표기는 이미 표준형이어서 악센트·대소문자 변이로 갈리는 이름은 없었다. 대신 사람이 아닌 표기 91개를 분류하고, 한 사람의 필명 1건(P.D.Q. 바흐 → 피터 시켈리)을 합쳤다 — 전승곡(Traditional 등)·국가(Anthem)·작곡가 미상·작품 아님(해설·시연·즉흥)·공동 또는 편곡 복합 표기(「Vivaldi-Bach」, 「Lennon-McCartney」, 사선으로 이은 여러 이름, 밴드·단체명). 이 표기는 모든 분모에 남기되 작곡가로 세지 않는다. 복합 표기를 원작곡가에게 돌리지 않는 것은, 돌리면 편곡자의 몫이 원작곡가 점유율로 들어가기 때문이다. 분류표는 <a href="../data/aliases/nyphil_composers.csv">aliases/nyphil_composers.csv</a>.</p>
<h2>작곡가 생몰년 (Wikidata)</h2>
<p>10회 이상 연주된 작곡가 529명을 Wikidata 에서 이름으로 찾아, 음악 직업을 가진 사람 항목만 후보로 남기고 첫 연주 시즌보다 5년 이상 앞서 태어났는지 대조했다. 후보가 하나뿐이고 대조를 통과한 478명은 자동 확정, 동명이인 후보가 여럿이거나 대조에 걸린 40명은 엮은이가 연주된 작품과 날짜로 하나씩 골랐다(예: 훔퍼딩크는 1936년생 가수가 아니라 1854년생 작곡가). 10명은 확정하지 못해 비워 두었다. 「P.D.Q. 바흐」는 피터 시켈리의 필명이라 작곡가 표에서 시켈리로 합쳤다. 한 항목에 날짜가 여럿이면 선호(preferred) 순위 값을, 없으면 정상 순위 값 가운데 가장 이른 연도를 쓰고, 명백한 오류 1건(과르니에리 몰년 1933 → 1993)은 손으로 고쳤다. 연도는 날짜 값의 연도를 그대로 쓰므로 율리우스력으로 적힌 날짜는 한 해 어긋날 수 있다. 레퍼토리 지표에는 몰년만 쓰이고, 몰년이 없으면 생존으로 본다. 매칭표는 <a href="../data/aliases/composer_wikidata.csv">aliases/composer_wikidata.csv</a>.</p>""")
        else:
            body.append(f"""<h2>Counting unit for repertoire (1.1)</h2>
<p>The NY Phil archive lists work entries per program; an overture and an aria from the same opera are two entries. Version 1.0 counted each entry once (U0, {H['ny_u0']:,} in all); 1.1 counts <b>the entries the archive files under one work number on a program once</b> (U1, {H['ny_u1']:,}). Arrangements given a different work number are counted separately. Either way the count is multiplied by the program's number of concerts. Those with no movement or part named are counted separately as complete performances (U2, {H['ny_u2']:,}). U2 is a proxy from the record: 73 pairs with a part number but an empty movement field count as complete, and 105 pairs mixing unmarked and excerpt entries count as excerpts. The population is the {H['ny_programs']:,} programs with at least one credited work (the source has 15,074 program records).</p>
<p>The unit changes rankings. Wagner is {ordinal(H['wag_rank_u1'])} by work performances (U1) but, with {H['wag_excerpt']:.0%} excerpts, {ordinal(H['wag_rank_u2'])} by complete performances (U2). Shares and concentration therefore use U1, and the excerpt share is its own metric. The four 1.0 metrics are recomputed under the old definition in a '1.0 unit' column (identical to the published 1.0 values for every completed season).</p>
<p>The 'subscription only' series counts only concerts whose event type is Subscription Season, leaving out Stadium, parks, tour and young people's concerts.</p>
<h2>Composer names</h2>
<p>The archive already uses authority forms, so no composer is split by accents or capitalisation. Instead, 91 non-person credits are classified and one pen name is merged (P.D.Q. Bach → Peter Schickele): traditional, anthem, unattributed, not a work (talks, demonstrations, improvisation), and joint or arrangement credits ('Vivaldi-Bach', 'Lennon-McCartney', slash-joined names, bands and ensembles). They stay in every denominator but are not counted as composers; joint credits are not assigned to the original composer, which would move an arranger's share into the composer's. Table: <a href="../data/aliases/nyphil_composers.csv">aliases/nyphil_composers.csv</a>.</p>
<h2>Composer dates (Wikidata)</h2>
<p>The 529 composers with 10+ performances were searched by name in Wikidata; only human items with a music occupation were kept and checked against the first NY Phil season (born at least five years earlier). 478 with a single candidate passing the check were accepted automatically; 40 with several same-name candidates or a failed check were resolved by the editor from the works performed and the dates (e.g. Humperdinck the composer, born 1854, not the singer born 1936); 10 remain unresolved and blank. 'P.D.Q. Bach' is Peter Schickele's pen name and is merged into Schickele in the composer tables. Where an item holds several dates the preferred-rank value is used, otherwise the earliest normal-rank year; one clear error (Guarnieri's death, 1933 → 1993) was corrected by hand. Years are taken as written, so a date recorded in the Julian calendar can be one year off. Only death years enter the repertoire metrics; a composer without a death year is treated as living. Table: <a href="../data/aliases/composer_wikidata.csv">aliases/composer_wikidata.csv</a>.</p>""")
        body.append("<h2>" + ("교차 검증" if lang == "ko" else "Cross-check") + "</h2>")
        body.append(("바흐 코랄은 두 개의 독립된 인코딩(DCML MuseScore 판, Sapp Humdrum 판)으로 같은 지표를 계산해 대조했다. 음표 수가 2%% 안에서 일치하는 %d곡에서 아홉 지표의 피어슨 상관은 최소 %.2f 였다." % (H["cross_n"], H["cross_min_r"])) if lang == "ko" else
                    ("The Bach chorales were measured from two independent encodings (DCML MuseScore and Sapp Humdrum). On the %d chorales whose note counts agree within 2%%, the nine metrics correlate at r ≥ %.2f." % (H["cross_n"], H["cross_min_r"])))
        body.append(table_html(cross, [("metric", "metric", None), ("n", t["n"], "d"), ("dcml_median", "DCML", ".3f"), ("kern_median", "Humdrum", ".3f"), ("pearson_r", "r", ".3f"), ("median_abs_diff", "|diff| median", ".4f")], "cross", lang, filt=False))
        body.append("<h2>" + ("선행 연구와의 대조" if lang == "ko" else "Comparison with the source paper") + "</h2>")
        body.append(("Martín-Castro & Ucar (2020)는 혼합효과 회귀로 시대연주·시대연주 영향·낭만파 지휘자가 표기보다 각각 6(2)·8(2)·13(2) bpm 느리다고 보고했다. 이 사이트의 단순 중앙값은 %.0f·%.0f·%.1f bpm 으로, 방법이 달라도 같은 그림이다." % (H["hi"], H["hii"], H["rom"])) if lang == "ko" else
                    ("Martín-Castro & Ucar (2020) report, from a mixed-effects regression, that HIP, HIP-influenced and Romantic conductors fall below the marks by 6(2), 8(2) and 13(2) bpm. The plain medians here are %.0f, %.0f and %.1f bpm — the same picture by a simpler route." % (H["hi"], H["hii"], H["rom"])))
        body.append("<h2>" + ("AI 사용 고지" if lang == "ko" else "AI disclosure") + "</h2><p>" + ("지표 설계·코드·본문 초고는 Claude(Anthropic)의 도움으로 작성했고, 엮은이가 원자료와 대조해 검증했다. 수치는 공개 코드로 재현할 수 있다." if lang == "ko" else "Metric design, code and draft text were produced with help from Claude (Anthropic) and verified by the editor against the source data. All numbers are reproducible from the published code.") + "</p>")
        body.append("<h2>" + ("아직 없는 것 (장기 과제)" if lang == "ko" else "Not yet here (long-term)") + "</h2><ul>" + ("".join(f"<li>{x}</li>" for x in ([
            "베토벤 교향곡의 악보 지표 — 기계 판독 총보가 공개돼 있지 않아 악보 인식(OMR)과 사람 교정이 필요하다.",
            "바흐 녹음의 연주 시간 추이(시대연주 운동 전후) — 음반 메타데이터에서 재발매 중복을 걸러야 한다.",
            "지휘자별 템포 통계의 확장 — 베토벤 이외 작곡가.",
            "뉴욕 필 이외 오케스트라의 레퍼토리 — 일괄 공개 데이터가 드물다.",
            "종지 지표(종지 밀도·정격 종지 비율) — 모차르트·베토벤 소나타 코퍼스에 종지 주석이 있으나, 두 코퍼스의 주석 체계가 같은지 확인한 뒤 낸다."] if lang == "ko" else [
            "Score metrics for the Beethoven symphonies — no open machine-readable full scores; needs OMR plus human correction.",
            "Bach recording durations over time (before/after the period-instrument movement) — requires de-duplicating reissues in release metadata.",
            "Conductor tempo statistics beyond Beethoven.",
            "Repertoire of orchestras other than the New York Philharmonic — bulk open data is rare.",
            "Cadence metrics (cadence density, PAC ratio) — the Mozart and Beethoven sonata corpora carry cadence labels, to be published once the two annotation schemes are confirmed comparable."]))) + "</ul>")
        body.append("<h2>" + ("변경 이력" if lang == "ko" else "Changelog") + "</h2><ul>" + "".join(f"<li><b>{v}</b> ({d}) — {esc(ko if lang == 'ko' else en)}</li>" for v, d, ko, en in CHANGELOG) + "</ul>")
        (base / "method.html").write_text(page(lang, t["nav_method"], "<div class='prose'>" + "".join(body) + "</div>", active="method"), encoding="utf-8")

        # ---------------- reading edition
        body = [f"<h1>{t['nav_reading']}</h1>"]
        medtab = []
        order = [("Bach", "chorales"), ("Bach", "english_french_suites"), ("Bach", "solo_violin_cello_flute"), ("Beethoven", "string_quartets"), ("Beethoven", "piano_sonatas"), ("Mozart", "piano_sonatas")]
        for comp, coll in order:
            r = {"group": f"{comp} · {t['coll'][coll]}", "n": int(cnt[(comp, coll)])}
            for mid in ["chromatic_ratio", "rhythm_entropy", "offbeat_onset_ratio", "notes_per_quarter", "top_leap_ratio", "chords_per_measure", "seventh_chord_ratio", "local_key_changes_per_100_measures"]:
                r[mid] = med.loc[(comp, coll), mid]
            medtab.append(r)
        medtab = pd.DataFrame(medtab)
        mt_cols = [("group", t["collection"], None), ("n", t["movements"], "d")] + [(mid, L(next(m for m in METRICS if m["id"] == mid))["name"], next(m for m in METRICS if m["id"] == mid)["fmt"]) for mid in medtab.columns[2:]]
        ptype_rows = "".join(f"<tr><td>{t['ptype'][k]}</td><td class='num'>{int(pt.loc[k,'n'])}</td><td class='num'>{pt.loc[k,'median']:+.1f}</td><td class='num'>{pt.loc[k,'q1']:+.1f}</td><td class='num'>{pt.loc[k,'q3']:+.1f}</td></tr>" for k in ("HI", "HI influence", "Romantic"))
        ny_pts_b = [(int(r.season_start), float(r.beethoven_share)) for _, r in ny_done.iterrows()]
        ny_pts_j = [(int(r.season_start), float(r.bach_share)) for _, r in ny_done.iterrows()]
        ny_pts_m = [(int(r.season_start), float(r.mozart_share)) for _, r in ny_done.iterrows()]
        ny_pts_h = [(int(r.season_start), float(r.hhi)) for _, r in ny_done.iterrows()]
        ny_pts_l = [(int(r.season_start), float(r.living_share)) for _, r in ny_done.iterrows()]
        ny_pts_lh = [(int(r.season_start), float(r.living_share_high)) for _, r in ny_done.iterrows()]
        cond_items = [(f"{r.conductor.split(',')[0]} ({t['ptype'][r.ptype]})", r.median_diff_bpm, PTYPE_COLOR[r.ptype]) for r in cond.itertuples()]
        if lang == "ko":
            body.append(f"""<p class="lead">야구는 타율과 OPS로 선수를 읽는다. 서양 고전 음악도 악보와 녹음이 데이터로 공개된 만큼은 같은 일을 할 수 있다. 이 판은 수치 사이트의 핵심 결과를 글로 읽는 판이다. 지표 하나하나의 정의와 전체 표는 <a href="metrics/index.html">지표</a> 면에 있다.</p>
<h2>1. 악보 — 바흐 {H['n_bach']}악장, 베토벤 {H['n_beet']}악장, 모차르트 {H['n_moz']}악장</h2>
<p>공개 주석 코퍼스에서 바흐의 코랄·영국 및 프랑스 모음곡·무반주 독주곡, 베토벤의 현악4중주 전곡과 피아노 소나타 28곡(22·25·27·28번은 코퍼스에 없다), 모차르트의 피아노 소나타 18곡을 가져와 같은 코드로 쟀다. 음표 {H['n_notes']:,}개다. 아래는 모음별 중앙값이다.</p>
{table_html(medtab, mt_cols, 'medtab', lang, filt=False)}
<p>세 가지가 눈에 띈다. 첫째, <b>반음계 비율</b>은 코랄(0.06)에서 베토벤 소나타(0.15)까지 두 배 넘게 벌어지지만, 바흐 무반주 독주곡(0.11)과 베토벤 4중주(0.13)는 가깝다 — 작곡가 사이의 간격이 편성 사이의 간격보다 작을 수 있다는 뜻이고, 「바로크는 온음계, 고전은 반음계」라는 통념을 이 표만으로 세울 수는 없다(장르를 통제한 비교는 아니다). 둘째, <b>화성 리듬</b>은 반대 방향이다. 바흐 모음곡은 마디당 세 화음, 베토벤은 두 화음 미만으로, 베토벤이 한 화음을 더 오래 끈다. 셋째, <b>최상성부 도약 비율</b>은 코랄 소프라노(0.14)가 가장 낮고 베토벤 소나타(0.50)가 가장 높다. 성악적 선율과 기악적 분산화음의 차이가 숫자로 그대로 나온다.</p>
<p>모차르트와 베토벤의 피아노 소나타는 편성과 장르가 같아 이 사이트에서 가장 통제된 비교다(베토벤은 28곡 91악장, 화성 지표는 화성 주석이 있는 64악장). 반음계 비율은 모차르트 {H['son_moz_chromatic_ratio']:.3f}·베토벤 {H['son_bee_chromatic_ratio']:.3f}, 부속화음 비율은 {H['son_moz_applied_chord_ratio']:.3f}·{H['son_bee_applied_chord_ratio']:.3f}, 최상성부 도약 비율은 {H['son_moz_top_leap_ratio']:.2f}·{H['son_bee_top_leap_ratio']:.2f}로 모두 베토벤이 높다. 그런데 100마디당 국지 조성 전환은 모차르트가 {H['son_moz_local_key_changes_per_100_measures']:.1f}회로 베토벤({H['son_bee_local_key_changes_per_100_measures']:.1f}회)보다 많다. 조를 더 자주 옮기면서 조표 밖 음은 덜 쓰는 셈이다. 짧은 거리의 전조를 자주 하는 쪽과 한 조 안에서 반음계를 더 쓰는 쪽의 차이로 읽을 수도 있지만, 이 표만으로 그 해석을 세우지는 않는다.</p>
<div class="note">이 숫자는 「무엇이 다른가」를 말하지 「왜」나 「누가 낫나」를 말하지 않는다. 편성·장르·주석자가 모두 다르다는 점을 표의 한계 칸에 적어 두었다.</div>
<h2>2. 베토벤의 메트로놈 — 지휘자 {H['n_cond']}명은 표기보다 얼마나 느린가</h2>
<p>베토벤은 교향곡 1~8번에 메트로놈 숫자를 남겼고, 그것이 너무 빠르다는 논란이 두 세기째다. Martín-Castro와 Ucar(2020)는 지휘자 36명의 전집 녹음 {H['n_tracks']:,}트랙에서 템포를 추출했다. 그 공개 데이터를 다시 집계하면 다음과 같다(교향곡 9번은 원저자처럼 제외).</p>
<div class="wrap"><table><thead><tr><th>연주 양식</th><th class="num">악장·지휘자 조합</th><th class="num">중앙값 (bpm)</th><th class="num">1사분위</th><th class="num">3사분위</th></tr></thead><tbody>{ptype_rows}</tbody></table></div>
<p>낭만파 지휘자는 중앙값으로 분당 {abs(H['rom']):.1f}박 느리고, 시대악기 지휘자도 {abs(H['hi']):.0f}박 느리다. <b>지휘자별 중앙값이 표기보다 빠른 사람은 36명 중 한 명도 없다.</b> 다만 악장 하나하나로 보면 {H['faster_n']}건({H['faster_n']/H['faster_of']:.1%})은 표기보다 빠르다 — 느린 쪽으로 치우친 것이지 모든 연주가 느린 것은 아니다. 원저자는 이 13 bpm 가량의 간격이 그 시대 멜첼 메트로놈 추의 높이(눈금에서 15 mm = 12 bpm)와 맞아떨어진다는 점에서 베토벤이 눈금을 잘못 읽었을 가능성을 제기했다. 그 해석의 옳고 그름과 무관하게, 「지휘자 36명이 모두 평균적으로 느리다」는 사실 자체는 데이터에서 확인된다.</p>
{legend([(t['ptype'][k], v) for k, v in PTYPE_COLOR.items()])}<figure>{svg_bars(cond_items, '+.1f', xlabel='bpm')}<figcaption>지휘자별 중앙값(33악장). 가장 느린 뵘(−17.5)부터 가장 가까운 샤이(−1.0)까지.</figcaption></figure>
<h2>3. 피아니스트들은 같은 곡을 얼마나 다르게 치는가</h2>
<p>ASAP 데이터셋에서 악보와 박 수가 맞는 연주는 바흐 평균율 {H['asap_bach_pieces']}곡({H['asap_bach_perf']}연주)과 베토벤 소나타 {H['asap_beet_pieces']}악장({H['asap_beet_perf']}연주, 원자료 271개 중 12개 제외)이다. 연주자는 국제 피아노 e-콩쿠르 참가자다. 1.1에서 더한 모차르트는 {H['asap_moz_pieces']}곡·{H['asap_moz_perf']}연주뿐이라 아래 비교에서 빼고 지표 면의 표에만 실었다.</p>
<ul><li><b>연주자 간 템포 산포</b>(연주가 2개 이상인 바흐 40곡·베토벤 33악장) 중앙값: 바흐 {H['asap_bach_cv']:.3f}, 베토벤 {H['asap_beet_cv']:.3f}. 같은 곡의 평균 템포 표준편차가 평균의 5~6% — 콩쿠르 참가자들은 템포 선택에서 생각보다 비슷하다.</li>
<li><b>박 단위 템포 흔들림</b>(루바토) 중앙값: 바흐 {H['asap_bach_rub']:.3f}, 베토벤 {H['asap_beet_rub']:.3f}. 베토벤에서 박마다 더 많이 늘고 준다.</li>
<li><b>강약 폭</b>(velocity 표준편차) 중앙값: 바흐 {H['asap_bach_vel']:.1f}, 베토벤 {H['asap_beet_vel']:.1f}. 셈여림 대비는 베토벤이 뚜렷이 크다.</li></ul>
<h2>4. 180년의 레퍼토리 — 뉴욕 필하모닉</h2>
<p>1842년 12월 7일 첫 연주회(베토벤 5번으로 시작했다)부터 {H['ny_last_season']} 시즌까지 {H['ny_programs_complete']:,}개 프로그램이 공개돼 있다(진행 중인 시즌까지 {H['ny_programs']:,}개; 뉴욕 심포니·스타디움 콘서트 등 아카이브가 함께 보존한 관련 단체의 프로그램 포함). 작품이 오른 이름은 {H['ny_strings']:,}개, 그중 사람 작곡가가 {H['ny_persons']:,}명이다. 전 작곡가 순위는 <a href="composers/index.html">작곡가</a> 면에 있다.</p>
<p><b>무엇을 한 번으로 세느냐가 먼저다.</b> 기록의 작품 항목 가운데 3분의 1 이상이 서곡·전주곡·아리아 같은 발췌다. 1.1은 한 프로그램에 오른 작품 하나를 한 번으로 세고(작품 연주 {H['ny_u1']:,}건), 그중 발췌가 아닌 것을 전곡 연주({H['ny_u2']:,}건)로 따로 센다. 작품 연주로 가장 많이 오른 것은 {esc(H['ny_all_top_composer'])}의 {esc(H['ny_all_top'])}({H['ny_all_top_n']:,}회)인데 전곡은 {H['ny_all_top_u2']}회뿐이고 나머지는 1막 전주곡 등 발췌다. 전곡 연주로는 {esc(H['ny_u2_top_composer'])}의 {esc(H['ny_u2_top'])}({H['ny_u2_top_n']:,}회)가 1위다. 바그너는 작품 연주로 {H['wag_rank_u1']}위, 전곡 연주로 {H['wag_rank_u2']}위다. 발췌 비율 자체도 1840년대 {H['dec_excerpt_1840']:.0%}(10년 중앙값)에서 1990년대 {H['dec_excerpt_1990']:.0%}까지 내려갔다가 2020년대 {H['dec_excerpt_2020']:.0%}로 올랐다.</p>
{legend([('Beethoven', 1), ('Mozart', 2), ('Bach', 0)])}<figure>{svg_lines([('Beethoven', ny_pts_b, 1), ('Mozart', ny_pts_m, 2), ('Bach', ny_pts_j, 0)], '.0%', ylabel='시즌 작품 연주 점유율')}<figcaption>베토벤 점유율은 {H['ny_first_season']} 시즌 {H['ny_first_beet']:.1%}에서 {H['ny_last_season']} 시즌 {H['ny_last_beet']:.1%}로. 모차르트는 서거 200주년 전후(1990–91·1991–92)에 20%를 넘었다. 바흐는 시즌 중앙값 1.7%.</figcaption></figure>
<figure>{svg_lines([('HHI', ny_pts_h, 2)], '.3f', ylabel='작곡가 집중도 (HHI)')}<figcaption>집중도는 {H['ny_first_hhi']:.3f}(작곡가 {H['ny_first_comp']}명)에서 {H['ny_last_hhi']:.3f}(작곡가 {H['ny_last_comp']}명)로. 해마다 오르내리지만 첫 시즌과 최근 시즌을 비교하면 레퍼토리는 크게 넓어졌다.</figcaption></figure>
<p><b>넓어졌지만 오래된 쪽으로 넓어졌다.</b> 연주 시점에 살아 있던 작곡가의 몫은 1840년대 {H['dec_living_1840']:.0%}(10년 중앙값)에서 1990년대 {H['dec_living_1990']:.0%}까지 떨어졌다가 2020년대 {H['dec_living_2020']:.0%}로 올랐다. 연주된 음악의 작곡가가 사망한 지 몇 년 되었는지(작품 연주로 가중한 중앙값)는 {H['ny_first_season']} 시즌 {H['ny_first_age']:.0f}년에서 {H['ny_last_season']} 시즌 {H['ny_last_age']:.0f}년이다. 다만 최근 시즌은 생몰년을 확인하지 못한 신진 작곡가가 많아, {H['ny_last_season']} 시즌의 생존 작곡가 점유율 {H['ny_last_living']:.1%}는 하한 {H['ny_last_living_lo']:.1%}와 상한 {H['ny_last_living_hi']:.1%} 사이에 있다고 읽어야 한다.</p>
<figure>{svg_lines([('생존 작곡가', ny_pts_l, 0), ('상한', ny_pts_lh, 1)], '.0%', ylabel='생존 작곡가 점유율')}<figcaption>완결 시즌별. 상한은 생몰년 미확인 작곡가를 모두 생존으로 둔 값이다.</figcaption></figure>
<p>최다 연주 작곡가 명단은 생각보다 자주 바뀐다. 10년 단위 상위 10명이 앞 10년과 겹치는 정도(자카드 지수)의 중앙값은 {H['turn_med10']:.2f}로, 10명 중 7명 남짓이 남고 서너 명이 바뀐다(<a href="metrics/canon_turnover.html">정전 회전율</a>).</p>
<h2>5. 한계와 다음</h2>
<p>이 판에 없는 것이 무엇인지가 있는 것만큼 중요하다. 베토벤 교향곡은 연주 지표만 있고 악보 지표가 없다(기계 판독 총보가 없어서다). 바흐의 녹음 데이터는 피아노 연주뿐이고, 시대악기 운동 전후의 연주 시간 변화는 아직 재지 못했다. 레퍼토리는 한 오케스트라의 기록이다. 각 지표의 한계 칸과 <a href="method.html">방법·출처</a> 면의 장기 과제 목록이 그 빈자리를 적어 둔다.</p>""")
        else:
            body.append(f"""<p class="lead">Baseball reads its players through batting average and OPS. Classical music can do the same, as far as scores and recordings are open as data. This is the prose edition of the site's main results; definitions and full tables live under <a href="metrics/index.html">Metrics</a>.</p>
<h2>1. Scores — {H['n_bach']} Bach, {H['n_beet']} Beethoven and {H['n_moz']} Mozart movements</h2>
<p>From open annotated corpora: Bach's chorales, English and French Suites and solo works; Beethoven's complete string quartets and 28 piano sonatas (Nos. 22, 25, 27 and 28 are not in the corpus); Mozart's 18 piano sonatas — {H['n_notes']:,} notes, measured by one codebase. Medians by collection:</p>
{table_html(medtab, mt_cols, 'medtab', lang, filt=False)}
<p>Three things stand out. First, the <b>chromatic ratio</b> more than doubles from the chorales (0.06) to Beethoven's sonatas (0.15), yet Bach's unaccompanied solo works (0.11) and Beethoven's quartets (0.13) sit close together — the gap between composers can be smaller than the gap between forces, so this table alone cannot establish the cliché "Baroque diatonic, Classical chromatic" (it is not a genre-controlled comparison). Second, <b>harmonic rhythm</b> runs the other way: Bach's suites change chord about three times a bar, Beethoven fewer than twice. Third, the <b>top-line leap ratio</b> is lowest in chorale sopranos (0.14) and highest in Beethoven's sonatas (0.50): vocal line versus instrumental figuration, in one number.</p>
<p>Mozart's and Beethoven's piano sonatas share instrument and genre, which makes them the most controlled comparison on this site (Beethoven: 28 sonatas, 91 movements; harmony metrics on the 64 movements with harmony annotations). The chromatic ratio (Mozart {H['son_moz_chromatic_ratio']:.3f}, Beethoven {H['son_bee_chromatic_ratio']:.3f}), the applied-chord ratio ({H['son_moz_applied_chord_ratio']:.3f}, {H['son_bee_applied_chord_ratio']:.3f}) and the top-line leap ratio ({H['son_moz_top_leap_ratio']:.2f}, {H['son_bee_top_leap_ratio']:.2f}) are all higher in Beethoven. Yet Mozart changes local key more often: {H['son_moz_local_key_changes_per_100_measures']:.1f} times per 100 bars against {H['son_bee_local_key_changes_per_100_measures']:.1f}. He moves key more often while using fewer notes outside the signature. One could read this as frequent short-range modulation versus more chromaticism within a key, but the table alone does not establish that reading.</p>
<div class="note">These numbers say what differs, not why or which is better. Instrumentation, genre and annotators all differ; the caveats column on each metric page says so.</div>
<h2>2. Beethoven's metronome — how far below the marks do {H['n_cond']} conductors play?</h2>
<p>Beethoven left metronome numbers for Symphonies 1–8, and for two centuries they have been called too fast. Martín-Castro and Ucar (2020) extracted tempi from {H['n_tracks']:,} tracks by 36 conductors. Re-aggregating their open data (Symphony 9 excluded, as in the paper):</p>
<div class="wrap"><table><thead><tr><th>Performance style</th><th class="num">movement × conductor</th><th class="num">median (bpm)</th><th class="num">Q1</th><th class="num">Q3</th></tr></thead><tbody>{ptype_rows}</tbody></table></div>
<p>Romantic conductors sit {abs(H['rom']):.1f} beats a minute below the marks at the median; even period-instrument conductors are {abs(H['hi']):.0f} below. <b>No conductor's median is faster than the marks.</b> Movement by movement, though, {H['faster_n']} of {H['faster_of']:,} readings ({H['faster_n']/H['faster_of']:.1%}) run faster — the distribution leans slow; not every performance is slow. The authors note that this gap of about 13 bpm matches the height of the weight on a Maelzel metronome of the period (15 mm on its scale = 12 bpm) and suggest Beethoven misread the scale. Whatever one makes of that reading, the fact that all 36 conductors are slower on average is in the data.</p>
{legend([(t['ptype'][k], v) for k, v in PTYPE_COLOR.items()])}<figure>{svg_bars(cond_items, '+.1f', xlabel='bpm')}<figcaption>Median per conductor over 33 movements, from the slowest (Böhm, −17.5) to the closest (Chailly, −1.0).</figcaption></figure>
<h2>3. How differently do pianists play the same piece?</h2>
<p>ASAP aligns {H['asap_bach_perf']} performances of {H['asap_bach_pieces']} Well-Tempered Clavier pieces and {H['asap_beet_perf']} performances of {H['asap_beet_pieces']} Beethoven sonata movements to their scores, beat by beat (12 of the 271 Beethoven performances whose beat counts do not match the score are left out). The performers are International Piano-e-Competition entrants. Mozart, added in 1.1, has only {H['asap_moz_pieces']} pieces and {H['asap_moz_perf']} performances, so it is left out of the comparison below and shown only in the metric tables.</p>
<ul><li><b>Across-performer tempo spread</b> (median CV over pieces with two or more performances: 40 Bach, 33 Beethoven): Bach {H['asap_bach_cv']:.3f}, Beethoven {H['asap_beet_cv']:.3f}. The SD of a piece's mean tempi is 5–6% of the mean — competition pianists agree on tempo more than one might expect.</li>
<li><b>Beat-to-beat tempo change</b> (rubato): Bach {H['asap_bach_rub']:.3f}, Beethoven {H['asap_beet_rub']:.3f}. More stretching per beat in Beethoven.</li>
<li><b>Dynamic spread</b> (velocity SD): Bach {H['asap_bach_vel']:.1f}, Beethoven {H['asap_beet_vel']:.1f}. Markedly wider dynamics in Beethoven.</li></ul>
<h2>4. 180 years of repertoire — the New York Philharmonic</h2>
<p>{H['ny_programs_complete']:,} programs are open from the first concert on 7 December 1842 (it opened with Beethoven's Fifth) to the {H['ny_last_season']} season ({H['ny_programs']:,} including the season in progress; the archive also holds programs of related bodies such as the New York Symphony and the Stadium concerts, which are included). {H['ny_strings']:,} names appear, {H['ny_persons']:,} of them individual composers; the full ranking is on the <a href="composers/index.html">Composers</a> page.</p>
<p><b>What counts as one comes first.</b> More than a third of the archive's work entries are excerpts — overtures, preludes, arias. Version 1.1 counts each work on a program once ({H['ny_u1']:,} work performances) and, separately, those that are not excerpts ({H['ny_u2']:,} complete performances). The most performed work is {esc(H['ny_all_top_composer'])}'s {esc(H['ny_all_top'])} ({H['ny_all_top_n']:,} times), but only {H['ny_all_top_u2']} of those were complete; the rest are excerpts such as the Act I prelude. By complete performances the leader is {esc(H['ny_u2_top_composer'])}'s {esc(H['ny_u2_top'])} ({H['ny_u2_top_n']:,}). Wagner ranks {ordinal(H['wag_rank_u1'])} by work performances and {ordinal(H['wag_rank_u2'])} by complete performances. The excerpt share itself fell from {H['dec_excerpt_1840']:.0%} in the 1840s (decade median) to {H['dec_excerpt_1990']:.0%} in the 1990s and rose to {H['dec_excerpt_2020']:.0%} in the 2020s.</p>
{legend([('Beethoven', 1), ('Mozart', 2), ('Bach', 0)])}<figure>{svg_lines([('Beethoven', ny_pts_b, 1), ('Mozart', ny_pts_m, 2), ('Bach', ny_pts_j, 0)], '.0%', ylabel='share of work performances per season')}<figcaption>Beethoven's share falls from {H['ny_first_beet']:.1%} in {H['ny_first_season']} to {H['ny_last_beet']:.1%} in {H['ny_last_season']}. Mozart passed 20% around the bicentenary of his death (1990–91, 1991–92). Bach's season median is 1.7%.</figcaption></figure>
<figure>{svg_lines([('HHI', ny_pts_h, 2)], '.3f', ylabel='composer concentration (HHI)')}<figcaption>Concentration falls from {H['ny_first_hhi']:.3f} ({H['ny_first_comp']} composers) to {H['ny_last_hhi']:.3f} ({H['ny_last_comp']} composers). It swings from season to season, but first and latest seasons compared, the repertoire has widened a great deal.</figcaption></figure>
<p><b>Wider, but wider toward the past.</b> The share of composers alive at the time fell from {H['dec_living_1840']:.0%} in the 1840s (decade median) to {H['dec_living_1990']:.0%} in the 1990s and rose to {H['dec_living_2020']:.0%} in the 2020s. How long dead the composers are (median weighted by work performances) went from {H['ny_first_age']:.0f} years in {H['ny_first_season']} to {H['ny_last_age']:.0f} in {H['ny_last_season']}. Recent seasons include many emerging composers without dates, so the {H['ny_last_season']} living share of {H['ny_last_living']:.1%} should be read as lying between {H['ny_last_living_lo']:.1%} and {H['ny_last_living_hi']:.1%}.</p>
<figure>{svg_lines([('living composers', ny_pts_l, 0), ('upper bound', ny_pts_lh, 1)], '.0%', ylabel='living-composer share')}<figcaption>Completed seasons. The upper bound treats composers without dates as living.</figcaption></figure>
<p>The list of most-performed composers changes more than one might think. The median overlap (Jaccard) of each decade's top 10 with the previous decade's is {H['turn_med10']:.2f}: roughly seven of ten stay and three or four change (<a href="metrics/canon_turnover.html">canon turnover</a>).</p>
<h2>5. Limits and next steps</h2>
<p>What is missing matters as much as what is here. The Beethoven symphonies have performance metrics but no score metrics (no open machine-readable full scores). Bach's performance data is piano only; the change in recorded durations around the period-instrument movement is not yet measured. The repertoire series is one orchestra. The caveats on each metric page and the long-term list under <a href="method.html">Method & sources</a> record those gaps.</p>""")
        (base / "reading.html").write_text(page(lang, t["nav_reading"], "<div class='prose'>" + "".join(body) + "</div>", active="reading"), encoding="utf-8")

        # ---------------- home
        cards = [
            (f"{H['n_movements']}", "악장 측정 (바흐 %d · 베토벤 %d · 모차르트 %d)" % (H['n_bach'], H['n_beet'], H['n_moz']) if lang == "ko" else "movements measured (Bach %d · Beethoven %d · Mozart %d)" % (H['n_bach'], H['n_beet'], H['n_moz']), "metrics/chromatic_ratio.html"),
            (f"{H['ny_persons']:,}", "뉴욕 필 1842~2026에 연주된 작곡가" if lang == "ko" else "composers performed by the NY Phil, 1842–2026", "composers/index.html"),
            (f"{H['rom']:+.1f} bpm", "낭만파 지휘자의 베토벤 표기 대비 중앙값" if lang == "ko" else "Romantic conductors vs Beethoven's marks (median)", "metrics/coda_tempo_diff_bpm.html"),
            (f"{H['asap_bach_perf']+H['asap_beet_perf']}", "박 단위 정렬된 피아노 연주" if lang == "ko" else "beat-aligned piano performances", "metrics/tempo_cv_across_performers.html"),
            (f"{H['ny_first_beet']:.0%} → {H['ny_last_beet']:.0%}", f"뉴욕 필 베토벤 점유율, {H['ny_first_season']} → {H['ny_last_season']}" if lang == "ko" else f"NY Phil Beethoven share, {H['ny_first_season']} → {H['ny_last_season']}", "metrics/beethoven_share.html"),
        ]
        body = [f"<div class='hero'><h1>{t['site']}</h1><p class='lead'>{t['tagline']}</p></div><div class='stats'>" + "".join(f"<a class='stat' href='{h}'><span class='n'>{esc(v)}</span><small>{esc(d)}</small></a>" for v, d, h in cards) + "</div>"]
        body.append(("<p class='lead' style='margin-top:.4rem'>세이버메트릭스가 야구를 바꾼 것은 통계 그 자체가 아니라 <b>지표마다 정의·공식·표본·한계를 공개한 것</b>이었다. 이 사이트는 서양 고전 음악에 같은 틀을 적용한다. 공개 악보 코퍼스와 연주 데이터셋에서 수치를 뽑고, 지표 하나에 페이지 하나를 둔다. 바흐와 베토벤으로 시작해 1.1에서 모차르트와 뉴욕 필의 전 작곡가 레퍼토리를 더했다.</p>" if lang == "ko" else
                     "<p class='lead' style='margin-top:.4rem'>What sabermetrics changed in baseball was not the statistics themselves but <b>publishing each metric's definition, formula, sample and caveats</b>. This site applies that frame to Western classical music: numbers extracted from open score corpora and performance datasets, one page per metric. It began with Bach and Beethoven; version 1.1 adds Mozart and the New York Philharmonic's repertoire across every composer.</p>"))
        for lay in ("A", "C", "D"):
            body.append(f"<h2>{LAYERS[lay][lang]}</h2><div class='cards'>")
            for m in METRICS:
                if m["layer"] == lay:
                    body.append(f"<a class='card layer-{lay}' href='metrics/{m['id']}.html'><b>{esc(L(m)['name'])}</b><small>{esc(L(m)['definition'])}</small></a>")
            body.append("</div>")
        body.append(f"<p class='links'><a href='reading.html'>{t['nav_reading']} →</a><a href='data.html'>{t['nav_data']} →</a><a href='method.html'>{t['nav_method']} →</a></p>")
        (base / "index.html").write_text(page(lang, t["nav_home"], "".join(body), active="home"), encoding="utf-8")

    # root redirect by browser language
    (OUT / "index.html").write_text("""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Classical Music Metrics</title>
<script>var l=(navigator.language||'').toLowerCase().indexOf('ko')==0?'ko':'en';location.replace(l+'/index.html');</script>
<meta http-equiv="refresh" content="1;url=en/index.html"></head><body><p><a href="ko/index.html">한국어</a> · <a href="en/index.html">English</a></p></body></html>""", encoding="utf-8")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    print("built", OUT, "metrics", len(METRICS))


if __name__ == "__main__":
    main()
