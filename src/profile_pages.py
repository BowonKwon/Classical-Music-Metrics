"""1.12: 'Pitch classes and chord progressions' page (profiles.html), design 72.

Sections: 1 pitch-class distribution and its Fourier magnitudes; 2 root-transition matrices and transition
entropy; 3 one movement at a time (key stretches, self-similarity matrix, 4-bar window series); 4 which
candidates became metrics (rules fixed beforehand) and the variation inside a movement; 5 sources.
Every number in the prose is computed here from the 1.12 tables. Heat-map colour: the validated six-step
one-hue ramp of the piece map (piecemap_pages.YEAR_RAMPS), light and dark.
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
import colour_19 as col19  # noqa: E402
import gates_112  # noqa: E402
import piecemap_pages as pmp  # noqa: E402
from registry import METRICS  # noqa: E402
from registry_112 import PAGE, PC_KO  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "data/derived"
FILES = ["score_metrics_112_by_movement.csv", "root_transitions_112.csv", "root_transition_entropy_112.csv",
         "metrics_112_gates.csv", "ssm_112_index.csv"]
MET = {m["id"]: m for m in METRICS}
ORDER = ["bach_chorales", "bach_en_fr_suites", "bach_solo", "scarlatti_sonatas", "wf_bach_sonatas", "cpe_bach_keyboard",
         "jc_bach_sonatas", "mozart_piano_sonatas", "kozeluh_sonatas", "pleyel_quartets", "beethoven_piano_sonatas", "ABC",
         "mendelssohn_quartets", "chopin_mazurkas", "schumann_kinderszenen", "liszt_pelerinage", "tchaikovsky_seasons",
         "dvorak_silhouettes", "grieg_lyric_pieces", "medtner_tales"]
DEGREE = ["♭2", "♭6", "♭3", "♭7", "4", "1", "5", "2", "6", "3", "7", "♯4"]  # line of fifths -5..+6 from the local tonic
DFT_BINS = [0.05, 0.1, 0.2, 0.3, 0.4]
ROW_BINS = [2, 5, 10, 20, 40]  # per cent of the row
DEFAULT_PIECE = ("mozart_piano_sonatas", "K279-1")
MIN_ROW = 30  # rows with fewer transitions are drawn faint, without numbers
CAND = {"dft_mag_5": ("5도권 집중도 |X₅|/X₀", "Fifths concentration |X₅|/X₀"), "dft_mag_1": ("반음 군집도 |X₁|/X₀", "Semitone clustering |X₁|/X₀"),
        "root_motion_entropy": ("근음 진행 다양도", "Root-motion variety"), "chromatic_window_sd": ("반음계 비율의 출렁임", "Variation of the chromatic ratio"),
        "density_window_cv": ("음표 밀도의 출렁임", "Variation of note density")}
PROTO = [(1, list(range(7)), ("반음 이웃 일곱 음", "seven semitone neighbors")), (2, [0, 6], ("셋온음", "a tritone")),
         (3, [0, 4, 8], ("증3화음", "an augmented triad")), (4, [0, 3, 6, 9], ("감7화음", "a diminished seventh")),
         (5, [0, 2, 4, 5, 7, 9, 11], ("온음계", "a diatonic scale")), (6, [0, 2, 4, 6, 8, 10], ("온음음계", "a whole-tone scale"))]


def esc(s):
    return html.escape("" if s is None else str(s))


def mn(v, spec=".2f") -> str:
    return format(v, spec).replace("-", "−")


def css() -> str:
    def block(mode):
        return "".join(f"--q{i + 1}:{c};" for i, c in enumerate(pmp.YEAR_RAMPS[mode]))
    rules = "".join(f".pf .q{i + 1}{{fill:var(--q{i + 1})}}" for i in range(6))
    return ("<style>:root{" + block("light") + "}@media(prefers-color-scheme:dark){:root:not([data-theme=\"light\"]){" + block("dark") + "}}"
            ":root[data-theme=\"dark\"]{" + block("dark") + "}" + rules
            + ".pf .q0{fill:none;stroke:var(--line2)}.pf text{font-size:11px;fill:var(--fg)}.pf .pfa{fill:var(--fg2)}.pf .faint{opacity:.3}.pf .in{fill:var(--card);font-size:10px}"
            ".pf-ctl{display:flex;gap:.6rem;align-items:center;flex-wrap:wrap;margin:.5rem 0}.pf-ctl select{font:inherit;font-size:.9rem;padding:.2rem .4rem;background:var(--card);color:var(--fg);border:1px solid var(--line);border-radius:6px;max-width:100%}"
            ".pf-two{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1rem}"
            "#pf-one{max-width:640px}#pf-ssm{width:100%;image-rendering:pixelated;image-rendering:crisp-edges;border:1px solid var(--line);display:block}"
            "#pf-keys{display:block;width:100%;height:14px;margin-bottom:2px}#pf-lines{display:block;width:100%}"
            ".pf-l1{stroke:var(--s1);fill:none;stroke-width:1.6}.pf-l2{stroke:var(--s2);fill:none;stroke-width:1.6}</style>")


def binq(v: float, bins) -> int:
    return 1 + int(np.searchsorted(bins, v, side="right"))


def legend(bins, lang: str, pct: bool) -> str:
    k = lang == "ko"
    labs = [f"< {bins[0]}"] + [f"{a}–{b}" for a, b in zip(bins, bins[1:])] + [f"≥ {bins[-1]}"]
    if pct:
        labs = [x + "%" for x in labs]
    cells = "".join(f"<rect x='{120 + i * 120}' y='3' width='18' height='14' rx='2' class='q{i + 1}'/><text x='{143 + i * 120}' y='15'>{esc(labs[i])}</text>" for i in range(6))
    lab = ("행 안 비율" if k else "Share of the row") if pct else ("값" if k else "Value")
    return f"<svg class='pf' viewBox='0 0 860 22' width='100%' role='img' aria-label='{'범례' if k else 'Legend'}'><text x='108' y='15' text-anchor='end'>{lab}</text>{cells}</svg>"


def proto_figure(lang: str) -> str:
    k = lang == "ko"
    out = []
    for i, (kk, pcs, lab) in enumerate(PROTO):
        cx, cy, r = 70 + i * 145, 62, 40
        w = np.zeros(12)
        w[pcs] = 1
        mag = abs((w * np.exp(-2j * np.pi * kk * np.arange(12) / 12)).sum()) / w.sum()
        dots = "".join(f"<circle cx='{cx + r * np.sin(2 * np.pi * n / 12):.1f}' cy='{cy - r * np.cos(2 * np.pi * n / 12):.1f}' r='{5 if n in pcs else 2.2}' "
                       f"fill='{'var(--s1)' if n in pcs else 'var(--fg3)'}'/>" for n in range(12))
        out.append(f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='none' stroke='var(--grid)'/>{dots}"
                   f"<text x='{cx}' y='126' text-anchor='middle'>k = {kk}: {lab[0 if k else 1]}</text><text x='{cx}' y='142' text-anchor='middle' class='pfa'>|X{'₁₂₃₄₅₆'[kk - 1]}|/X₀ = {mag:.2f}</text>")
    return f"<svg class='pf' viewBox='0 0 880 150' width='100%' role='img' aria-label='{'계수별 원형 계열' if k else 'A prototype for each coefficient'}'>{''.join(out)}</svg>"


def dft_heatmap(df: pd.DataFrame, lang: str) -> str:
    k = lang == "ko"
    cw, rh, x0, y0 = 78, 24, 300, 26
    cols = [f"dft_mag_{i}" for i in range(1, 7)]
    med = df.groupby("corpus")[cols].median()
    cnt = df.groupby("corpus").size()
    comp = df.drop_duplicates("corpus").set_index("corpus")["composer"]
    out = [f"<text x='{x0 + i * cw + cw / 2}' y='16' text-anchor='middle'>|X{'₁₂₃₄₅₆'[i]}|/X₀</text>" for i in range(6)]
    for r, c in enumerate(ORDER):
        y = y0 + r * rh
        out.append(f"<text x='{x0 - 8}' y='{y + 16}' text-anchor='end'>{esc(pmp.coll_name(c, comp[c], lang))} ({cnt[c]})</text>")
        for i, col in enumerate(cols):
            v = float(med.loc[c, col])
            out.append(f"<rect x='{x0 + i * cw + 1}' y='{y + 1}' width='{cw - 2}' height='{rh - 2}' rx='2' class='q{binq(v, DFT_BINS)}'/>"
                       f"<text x='{x0 + i * cw + cw / 2}' y='{y + 16}' text-anchor='middle' class='km-lab'>{v:.2f}</text>")
    h = y0 + len(ORDER) * rh + 4
    return f"<svg class='pf' viewBox='0 0 {x0 + 6 * cw + 4} {h}' width='100%' role='img' aria-label='{'곡집별 푸리에 계수 크기' if k else 'Fourier magnitudes by collection'}'>{''.join(out)}</svg>"


def year_scatter(df: pd.DataFrame, lang: str) -> tuple[str, float, int]:
    k = lang == "ko"
    d = df.dropna(subset=["year", "dft_mag_5"])
    w, h, m = 900, 380, 46
    x0, x1 = 1680, 1940
    px = lambda v: m + (v - x0) / (x1 - x0) * (w - 2 * m)  # noqa: E731
    py = lambda v: h - m - v * (h - 2 * m)  # noqa: E731
    dots = "".join(f"<circle cx='{px(r.year):.1f}' cy='{py(r.dft_mag_5):.1f}' r='2.4' fill='var(--s1)' fill-opacity='.4'><title>{esc(pmp.coll_name(r.corpus, r.composer, lang))} · {esc(r.piece_id)} · {int(r.year)}</title></circle>" for r in d.itertuples())
    ticks = "".join(f"<text x='{px(t):.1f}' y='{h - m + 16}' text-anchor='middle' class='pfa'>{t}</text>" for t in range(1700, 1941, 40))
    ticks += "".join(f"<text x='{m - 8}' y='{py(t) + 4:.1f}' text-anchor='end' class='pfa'>{t:.1f}</text><line x1='{m}' y1='{py(t):.1f}' x2='{w - m}' y2='{py(t):.1f}' stroke='var(--grid)'/>" for t in (0, 0.2, 0.4, 0.6, 0.8, 1.0))
    lab = (f"<text x='{w / 2}' y='{h - 6}' text-anchor='middle' class='pfa'>{'작곡 연도' if k else 'Year composed'}</text>"
           f"<text x='14' y='{h / 2}' text-anchor='middle' transform='rotate(-90 14 {h / 2})' class='pfa'>|X₅|/X₀</text>")
    rho = float(spearmanr(d["year"], d["dft_mag_5"]).statistic)
    return f"<svg class='pf' viewBox='0 0 {w} {h}' width='100%' role='img' aria-label='{'작곡 연도와 다섯째 계수' if k else 'Year composed and the fifth coefficient'}'>{ticks}{lab}{dots}</svg>", rho, len(d)


def matrices_block(lang: str, comp: pd.Series) -> str:
    k = lang == "ko"
    mat = pd.read_csv(D / "root_transitions_112.csv")
    data = {}
    for (c, mode), g in mat.groupby(["corpus", "mode"]):
        m = np.zeros((12, 12), dtype=int)
        m[g["from_fifths"].to_numpy() + 5, g["to_fifths"].to_numpy() + 5] = g["count"].to_numpy()
        data.setdefault(c, {})[mode] = m.tolist()
    corpora = [c for c in ORDER if c in data]
    opts = "".join(f"<option value='{esc(c)}'>{esc(pmp.coll_name(c, comp[c], lang))}</option>" for c in corpora)
    js = ("<script>(function(){var M=" + json.dumps(data, separators=(",", ":")) + ",DG=" + json.dumps(DEGREE, ensure_ascii=False) + ",MINROW=" + str(MIN_ROW) + ",B=" + json.dumps(ROW_BINS)
          + ",L=" + json.dumps({"major": "장조 국소 조" if k else "Major local keys", "minor": "단조 국소 조" if k else "Minor local keys",
                               "n": "전이" if k else "transitions", "from": "앞 근음" if k else "from", "to": "뒤 근음" if k else "to"}, ensure_ascii=False) + ";"
          "function q(p){for(var i=0;i<B.length;i++){if(p<B[i])return i+1}return 6}"
          "function one(m,mode){var c=26,x0=40,y0=40,s='',tot=0,i,j;for(i=0;i<12;i++)for(j=0;j<12;j++)tot+=m[i][j];"
          "s+='<text x=\"'+(x0+6*c)+'\" y=\"12\" text-anchor=\"middle\">'+L[mode]+' · '+L.n+' '+tot.toLocaleString()+'</text>';"
          "for(j=0;j<12;j++)s+='<text x=\"'+(x0+j*c+c/2)+'\" y=\"34\" text-anchor=\"middle\" class=\"pfa\">'+DG[j]+'</text>';"
          "s+='<text x=\"'+(x0+12*c+6)+'\" y=\"34\" class=\"pfa\">n</text>';"
          "for(i=0;i<12;i++){var rs=0;for(j=0;j<12;j++)rs+=m[i][j];var ft=rs<MINROW?' faint':'';s+='<text x=\"'+(x0-6)+'\" y=\"'+(y0+i*c+17)+'\" text-anchor=\"end\" class=\"pfa\">'+DG[i]+'</text>'"
          "+'<text x=\"'+(x0+12*c+6)+'\" y=\"'+(y0+i*c+17)+'\" class=\"pfa\">'+rs.toLocaleString()+'</text>';"
          "for(j=0;j<12;j++){var v=m[i][j],p=rs?100*v/rs:0,cl=(v?('q'+q(p)):'q0')+ft;"
          "s+='<rect x=\"'+(x0+j*c+1)+'\" y=\"'+(y0+i*c+1)+'\" width=\"'+(c-2)+'\" height=\"'+(c-2)+'\" rx=\"2\" class=\"'+cl+'\"><title>'+DG[i]+' → '+DG[j]+': '+v+' ('+p.toFixed(1)+'%)</title></rect>';"
          "if(p>=10&&!ft)s+='<text x=\"'+(x0+j*c+c/2)+'\" y=\"'+(y0+i*c+17)+'\" text-anchor=\"middle\" class=\"'+(p>=20?'in':'km-lab')+'\">'+Math.round(p)+'</text>'}}"
          "return '<svg class=\"pf\" viewBox=\"0 0 '+(x0+12*c+48)+' '+(y0+12*c+4)+'\" width=\"100%\" role=\"img\" aria-label=\"'+L[mode]+'\">'+s+'</svg>'}"
          "var sel=document.getElementById('pf-coll'),box=document.getElementById('pf-mats');"
          "function show(){var d=M[sel.value];box.innerHTML='<div>'+one(d.major,'major')+'</div><div>'+one(d.minor,'minor')+'</div>'}"
          "sel.addEventListener('change',show);show()})();</script>")
    return (f"<div class='pf-ctl'><label>{'곡집' if k else 'Collection'} <select id='pf-coll'>{opts}</select></label></div>"
            f"<div id='pf-mats' class='pf-two'></div>" + legend(ROW_BINS, lang, True) + js)


def entropy_table(lang: str, comp: pd.Series, table_html) -> tuple[str, pd.DataFrame]:
    k = lang == "ko"
    e = pd.read_csv(D / "root_transition_entropy_112.csv")
    full = e["n_boot"] == gates_boot()
    rows = []
    for c in ORDER:
        g = e[e.corpus == c].set_index("mode")
        if g.empty:
            continue
        r = dict(name=pmp.coll_name(c, comp[c], lang))
        for mode in ("major", "minor"):
            x = g.loc[mode]
            r[f"n_{mode}"] = int(x.n_transitions)
            r[f"h_{mode}"] = x.entropy_rarefied
            ok = pd.notna(x.entropy_rarefied) and bool(full[(e.corpus == c) & (e["mode"] == mode)].iloc[0])
            r[f"ci_{mode}"] = f"{x.ci_low:.2f}–{x.ci_high:.2f}" if ok else "—"
        rows.append(r)
    t = pd.DataFrame(rows)
    cols = [("name", "곡집" if k else "Collection", None),
            ("n_major", "장조: 전이 수" if k else "major: n", ",d"), ("h_major", "장조: 엔트로피" if k else "major: entropy", ".3f"), ("ci_major", "95% 구간" if k else "95% interval", None),
            ("n_minor", "단조: 전이 수" if k else "minor: n", ",d"), ("h_minor", "단조: 엔트로피" if k else "minor: entropy", ".3f"), ("ci_minor", "95% 구간 " if k else "95% interval ", None)]
    return table_html(t, cols, "pf_ent", lang, filt=False), e


def gates_boot() -> int:
    import score_metrics_112 as s112
    return s112.BOOT_REPS


def one_block(lang: str, comp: pd.Series) -> str:
    k = lang == "ko"
    idx = pd.read_csv(D / "ssm_112_index.csv")
    idx["o"] = idx["corpus"].map({c: i for i, c in enumerate(ORDER)})
    idx = idx.sort_values(["o", "piece_id"])
    opts = "".join(f"<option value='{esc(r.corpus)}__{esc(r.piece_id)}'{' selected' if (r.corpus, r.piece_id) == DEFAULT_PIECE else ''}>{esc(pmp.coll_name(r.corpus, comp[r.corpus], lang))} · {esc(r.piece_id)} "
                   f"({r.n_measures} {'마디' if k else 'measures'}; {col19.ROLE[r.role][0 if k else 1]})</option>" for r in idx.itertuples())
    t = {"dens": "음표 밀도(4분음표당 음 수)" if k else "note density (notes per quarter)", "chrom": "반음계 비율" if k else "chromatic ratio",
         "max": "최대" if k else "max", "bar": "마디" if k else "measure", "err": "자료를 읽지 못했다." if k else "Could not load the data.",
         "nokey": "화성 주석 없음" if k else "no harmony labels"}
    js = ("<script>(function(){var T=" + json.dumps(t, ensure_ascii=False) + ",sel=document.getElementById('pf-piece'),cv=document.getElementById('pf-ssm'),"
          "ks=document.getElementById('pf-keys'),ln=document.getElementById('pf-lines'),cur=null;"
          "function ink(){var c=getComputedStyle(document.documentElement).getPropertyValue('--q6').trim();return [parseInt(c.substr(1,2),16),parseInt(c.substr(3,2),16),parseInt(c.substr(5,2),16)]}"
          "function step(v){v=Math.max(-6,Math.min(6,Math.round(v)));return v===0?'z':(v>0?'p'+v:'m'+(-v))}"
          "function draw(d){cur=d;var n=d.n,c=ink(),ctx=cv.getContext('2d'),i,j,p=0;cv.width=n;cv.height=n;var im=ctx.createImageData(n,n),a=new Uint8Array(n*n);"
          "for(i=0;i<n;i++)a[i*n+i]=255;for(i=0;i<n-1;i++)for(j=i+1;j<n;j++){var v=parseInt(d.upper.substr(p,2),16);p+=2;a[i*n+j]=v;a[j*n+i]=v}"
          "for(i=0;i<d.empty.length;i++){var e=d.empty[i];for(j=0;j<n;j++){a[e*n+j]=0;a[j*n+e]=0}}"
          "for(i=0;i<n*n;i++){im.data[4*i]=c[0];im.data[4*i+1]=c[1];im.data[4*i+2]=c[2];im.data[4*i+3]=Math.max(0,Math.round((a[i]-127.5)*2))}ctx.putImageData(im,0,0);"
          "var s='';if(d.keys.length){for(i=0;i<d.keys.length;i++){var g=d.keys[i],x=0,x2=n;for(j=0;j<n;j++){if(d.mn[j]>=g[0]){x=j;break}}for(j=n-1;j>=0;j--){if(d.mn[j]<=g[1]){x2=j+1;break}}"
          "s+='<rect x=\"'+x+'\" y=\"0\" width=\"'+Math.max(x2-x,0.5)+'\" height=\"1\" class=\"kh-'+step(g[2])+'\"><title>'+g[4]+' ('+T.bar+' '+g[0]+'–'+g[1]+')</title></rect>'}}"
          "else s='<title>'+T.nokey+'</title>';ks.setAttribute('viewBox','0 0 '+n+' 1');ks.innerHTML=s;"
          "var W=640,H=120,w=d.windows,md=0,mc=0;for(i=0;i<w.length;i++){md=Math.max(md,w[i][1]);if(w[i][2]!==null)mc=Math.max(mc,w[i][2])}"
          "function path(ix,mx,cl){var pts=[];for(var q=0;q<w.length;q++){if(w[q][ix]===null)continue;pts.push(((w[q][0]+1)/n*W).toFixed(1)+','+(H-18-(mx?w[q][ix]/mx:0)*(H-36)).toFixed(1))}"
          "return '<polyline class=\"'+cl+'\" points=\"'+pts.join(' ')+'\"/>'}"
          "ln.setAttribute('viewBox','0 0 '+W+' '+H);ln.innerHTML='<line x1=\"0\" y1=\"'+(H-18)+'\" x2=\"'+W+'\" y2=\"'+(H-18)+'\" stroke=\"var(--grid)\"/>'+path(1,md,'pf-l1')+path(2,mc,'pf-l2')"
          "+'<text x=\"2\" y=\"11\" style=\"fill:var(--s1)\">'+T.dens+' · '+T.max+' '+md.toFixed(2)+'</text><text x=\"'+W+'\" y=\"11\" text-anchor=\"end\" style=\"fill:var(--s2)\">'+T.chrom+' · '+T.max+' '+mc.toFixed(2)+'</text>'"
          "+'<text x=\"0\" y=\"'+(H-4)+'\" class=\"pfa\">'+T.bar+' '+d.mn[0]+'</text><text x=\"'+W+'\" y=\"'+(H-4)+'\" text-anchor=\"end\" class=\"pfa\">'+d.mn[n-1]+'</text>'}"
          "function load(){fetch('../data/profiles/ssm_112/'+sel.value+'.json').then(function(r){return r.json()}).then(draw).catch(function(){ln.innerHTML='<text x=\"2\" y=\"12\">'+T.err+'</text>'})}"
          "sel.addEventListener('change',load);new MutationObserver(function(){if(cur)draw(cur)}).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});load()})();</script>")
    return (f"<div class='pf-ctl'><label>{'악장' if k else 'Movement'} <select id='pf-piece'>{opts}</select></label></div>"
            f"<div id='pf-one'><svg id='pf-keys' class='pf' preserveAspectRatio='none' role='img' aria-label='{'국소 조' if k else 'Local keys'}'></svg>"
            f"<canvas id='pf-ssm' role='img' aria-label='{'자기 유사 행렬' if k else 'Self-similarity matrix'}'></canvas>"
            f"<svg id='pf-lines' class='pf' role='img' aria-label='{'4마디 창별 값' if k else 'Values by 4-bar window'}'></svg></div>" + js), len(idx)


def gates_table(lang: str, table_html) -> tuple[str, dict, list]:
    k = lang == "ko"
    g = pd.read_csv(D / "metrics_112_gates.csv")
    v = gates_112.verdicts(g)
    pub = gates_112.published(g)
    rows = []
    for c in gates_112.CANDIDATES:
        x = g[g.candidate == c]
        ln_ = x[x.check == "length"]
        ov = x[x.check == "overlap"]
        top = ov.reindex(ov["value"].abs().sort_values(ascending=False).index).iloc[0]
        rel = MET[top.against][lang]["name"] if top.against in MET else CAND[top.against][0 if k else 1]
        rows.append(dict(name=CAND[c][0 if k else 1], miss=f"{float(x[x.check == 'missing']['value'].iloc[0]) * 100:.1f}%",
                         length=", ".join(mn(r) for r in ln_["value"]), overlap=f"{mn(top['value'])} ({rel})",
                         verdict=(("지표" if k else "metric") if c in pub else ("조건 통과, 지표로는 내지 않음" if k else "passed; not published")) if v[c]
                         else ("CSV에만(길이)" if k else "CSV only (length)")))
    cols = [("name", "후보" if k else "Candidate", None), ("miss", "빈칸" if k else "Blank", None),
            ("length", "길이와의 순위 상관" if k else "Rank correlation with length", None),
            ("overlap", "겹침이 가장 큰 기존 지표와의 상관" if k else "Largest correlation with an existing metric", None), ("verdict", "판정" if k else "Verdict", None)]
    return table_html(pd.DataFrame(rows), cols, "pf_gate", lang, filt=False), v, pub


def window_table(df: pd.DataFrame, lang: str, comp: pd.Series, table_html) -> str:
    k = lang == "ko"
    rows = []
    for c in ORDER:
        g = df[df.corpus == c]
        n = int(g["chromatic_window_sd"].notna().sum())
        rows.append(dict(name=pmp.coll_name(c, comp[c], lang), n=len(g), nv=n,
                         cs=g["chromatic_window_sd"].median() if n >= 5 else float("nan"), dc=g["density_window_cv"].median() if n >= 5 else float("nan")))
    cols = [("name", "곡집" if k else "Collection", None), ("n", "악장" if k else "movements", "d"), ("nv", "값이 있는 악장" if k else "with a value", "d"),
            ("cs", CAND["chromatic_window_sd"][0 if k else 1], ".3f"), ("dc", CAND["density_window_cv"][0 if k else 1], ".3f")]
    return table_html(pd.DataFrame(rows), cols, "pf_win", lang, filt=False)


def render(lang, table_html):
    k = lang == "ko"
    df = gates_112.table()
    comp = df.drop_duplicates("corpus").set_index("corpus")["composer"]
    g = pd.read_csv(D / "metrics_112_gates.csv")
    rho5 = float(g[(g.candidate == "dft_mag_5") & (g.check == "length")]["value"].iloc[0])
    med5 = df.groupby("corpus")["dft_mag_5"].median()
    lo5, hi5 = med5.idxmin(), med5.idxmax()
    med1 = df.groupby("corpus")["dft_mag_1"].median()
    sc, rho_y, n_y = year_scatter(df, lang)
    name = lambda c: pmp.coll_name(c, comp[c], lang)  # noqa: E731
    b = [col19.css() + css(), f"<h1>{PAGE[0 if k else 1]}</h1><p class='lead'>"
         + (f"악장 하나를 숫자 하나가 아니라 벡터와 행렬로 요약해 본다. 벡터는 열두 {PC_KO}의 분포와 그 푸리에 계수이고, 행렬은 화음의 근음이 어디서 어디로 가는지를 센 표와, 마디끼리 얼마나 닮았는지를 그린 그림이다. "
            f"{PC_KO}(pitch class)는 옥타브를 무시한 음이름 열두 가지를 말한다. 가온 도와 높은 도는 같은 {PC_KO}다." if k else
            "A movement summarized not by one number but by vectors and matrices. The vector is the distribution over the twelve pitch classes and its Fourier coefficients; the matrices count where chord roots go from where, and picture how alike the measures of a movement are. "
            "A pitch class is a note name regardless of octave: middle C and the C above it are the same pitch class.") + "</p>"]
    # 1
    b.append((f"<h2>1. {PC_KO} 분포와 푸리에 계수</h2>"
              f"<p>악장마다 열두 {PC_KO}가 울린 길이의 비율을 내면 숫자 열두 개가 된다. 이 열두 숫자에 이산 푸리에 변환을 하면 「원 위에 k번 되풀이되는 무늬가 얼마나 강한가」를 k = 1~6에 대해 하나씩 얻는다. "
              "크기는 0과 1 사이이고, 조옮김해도 변하지 않는다. 아래 그림은 계수마다 값이 커지는 음 묶음의 예다.</p>" if k else
              "<h2>1. Pitch-class distribution and its Fourier coefficients</h2>"
              "<p>For each movement, the share of sounding time on each of the twelve pitch classes gives twelve numbers. Their discrete Fourier transform gives, for k = 1 to 6, how strong a pattern repeating k times around the circle is. "
              "The magnitudes lie between 0 and 1 and do not change under transposition. The figure shows, for each coefficient, a set of notes that makes it large.</p>")
             + f"<figure>{proto_figure(lang)}<figcaption>"
             + ("열두 점은 반음 순서로 놓은 열두 음, 큰 점은 쓰인 음이다. 다섯째 계수는 5도권에서 이웃한 음들(온음계)에, 첫째 계수는 반음으로 이웃한 음들에 반응한다. 음 하나만 쓰면 여섯 계수가 모두 1이고, 열두 음을 고르게 쓰면 모두 0이다."
                if k else "The twelve dots are the twelve notes in semitone order; large dots are the notes used. The fifth coefficient responds to neighbors on the circle of fifths (a diatonic scale), the first to neighbors by semitone. A single note gives 1 for all six; twelve notes used equally give 0 for all.")
             + "</figcaption></figure>"
             + (f"<p>아래는 곡집별 중앙값이다(괄호는 악장 수). 다섯째 계수의 중앙값은 {name(lo5)} {med5[lo5]:.2f}에서 {name(hi5)} {med5[hi5]:.2f}까지다. "
                f"다만 이 값은 긴 악장일수록 낮다(악장 길이와의 순위 상관 {mn(rho5)}). 그래서 지표로 내지 않고 이 면과 CSV에만 싣는다(4절). 첫째 계수는 곡집별 중앙값이 {med1.min():.2f}~{med1.max():.2f}로 작고 서로 비슷하다. 온음계 일곱 음이 반음계 원에 고르게 퍼져 있다는 점(일곱 음을 고르게 쓰면 0.04)과 맞는 결과다.</p>" if k else
                f"<p>Collection medians follow (number of movements in parentheses). The median of the fifth coefficient runs from {med5[lo5]:.2f} ({name(lo5)}) to {med5[hi5]:.2f} ({name(hi5)}). "
                f"It is lower for longer movements, though (rank correlation with movement length {mn(rho5)}), so it is not published as a metric, only here and in the CSV (section 4). The first coefficient is small and much the same everywhere (collection medians {med1.min():.2f} to {med1.max():.2f}), which fits the fact that the seven notes of a diatonic scale are spread evenly around the chromatic circle (0.04 when used equally).</p>")
             + f"<figure>{dft_heatmap(df, lang)}{legend(DFT_BINS, lang, False)}</figure>"
             + f"<figure>{sc}<figcaption>"
             + (f"점 하나가 악장 하나({n_y:,}악장, 작곡 연도가 확인된 것). 세로는 다섯째 계수의 크기. 작곡 연도와의 순위 상관은 {mn(rho_y)}다. 곡집마다 장르와 악장 길이가 달라서, 이 기울기를 시대의 변화로만 읽을 수는 없다."
                if k else f"One dot per movement ({n_y:,} movements with a confirmed year). Vertical: magnitude of the fifth coefficient. Rank correlation with the year composed: {mn(rho_y)}. Collections differ in genre and movement length, so the slope cannot be read as change over time alone.")
             + "</figcaption></figure>")
    # 2
    ent_html, e = entropy_table(lang, comp, table_html)
    ok = e.dropna(subset=["entropy_rarefied"])
    lo, hi = ok.loc[ok.entropy_rarefied.idxmin()], ok.loc[ok.entropy_rarefied.idxmax()]
    mode_name = lambda m: ("장조" if m == "major" else "단조") if k else m  # noqa: E731
    tot = int(e.n_transitions.sum())
    drop = int(e.n_dropped_enharmonic.sum())
    blank = e[e.entropy_rarefied.isna()]
    diff = (ok.entropy_all - ok.entropy_rarefied)
    both = e.pivot(index="corpus", columns="mode", values="entropy_rarefied").dropna()
    higher_minor = int((both["minor"] > both["major"]).sum())
    b.append((f"<h2>2. 근음 전이 행렬</h2><p>화성 주석이 있는 19곡집에서, 같은 국소 조 안에서 근음이 바뀌는 연속 화음 {tot:,}쌍을 셌다. 행은 앞 화음의 근음, 열은 뒤 화음의 근음이고, 국소 조 으뜸음에서 본 음도를 5도권 순서로 놓았다(가운데가 으뜸음 1, 오른쪽으로 5·2·6…, 왼쪽으로 4·♭7·♭3…). "
              "칸의 색과 숫자는 그 행 안에서의 비율(%)이고, 오른쪽 끝의 n은 그 행의 전이 수다. 전이가 30쌍 미만인 행은 흐리게 그렸다. 대각선 바로 왼쪽 칸이 5도 하행이다. 단조에서 자연단음계의 3·6·7음은 ♭3·♭6·♭7 자리다. "
              f"5도권을 열두 칸으로 접었으므로 ♯1과 ♭2 같은 이명동음은 한 칸이 되고, 접으면 같은 칸이 되는 전이 {drop}쌍은 뺐다.</p>" if k else
              f"<h2>2. Root-transition matrices</h2><p>In the 19 collections with harmony labels, {tot:,} pairs of successive chords in the same local key whose root changes were counted. Rows are the root of the first chord, columns that of the second, as scale degrees from the local tonic in circle-of-fifths order (the tonic, 1, in the middle; 5, 2, 6 … to the right; 4, ♭7, ♭3 … to the left). "
              "Colour and number give the share within the row (%); n at the right is the number of transitions in the row. Rows with fewer than 30 transitions are drawn faint. The cell just left of the diagonal is a falling fifth. In minor keys the natural 3rd, 6th and 7th degrees are at ♭3, ♭6, ♭7. "
              f"The line of fifths is folded to twelve cells, so enharmonic roots such as ♯1 and ♭2 share a cell; {drop} transitions whose two roots fold onto one cell were left out.</p>")
             + matrices_block(lang, comp)
             + (f"<h3>전이 엔트로피</h3><p>행렬 하나를 수치 하나로 줄인 값이다. 앞 근음이 정해졌을 때 뒤 근음이 얼마나 예측하기 어려운지를 행마다 엔트로피로 재고 log₂11로 나눈 뒤(Moss 외 2019가 화음 기호에 쓴 정규화 조건부 엔트로피의 방식을 근음에 적용했다), 행의 빈도로 가중 평균했다(가중 평균은 이 사이트가 더한 것이다). "
                "0이면 뒤 근음이 늘 정해져 있고, 1이면 나머지 열한 음이 고르게 나온다. 같은 자료에서도 전이를 적게 뽑으면 엔트로피 추정값이 낮게 나오므로, 곡집·모드마다 전이 400쌍을 뽑아 계산하기를 200번 되풀이한 평균을 실었다. "
                f"전체 표본으로 계산한 값보다 {diff.min():.3f}~{diff.max():.3f} 낮다. 전이가 400쌍에 못 미치는 {len(blank)}칸은 비웠다. "
                f"값은 {name(lo.corpus)} {mode_name(lo['mode'])} {lo.entropy_rarefied:.3f}에서 {name(hi.corpus)} {mode_name(hi['mode'])} {hi.entropy_rarefied:.3f}까지다. 장·단조 값이 모두 있는 {len(both)}곡집 가운데 {higher_minor}곳에서 단조 쪽이 높다. "
                "구간은 악장을 다시 뽑는 부트스트랩 200회의 95% 구간이고(작품·주석자 단위의 묶임은 반영하지 않았다), 다시 뽑은 표본이 400쌍에 못 미친 회차가 있는 칸은 구간을 싣지 않았다. 구간은 값 하나하나가 얼마나 흔들리는지를 보인 것이고, 두 곡집의 차이를 검정한 것은 아니다. 구간이 넓게 겹치는 곡집끼리는 순서를 단정하지 않는다.</p>" if k else
                f"<h3>Transition entropy</h3><p>One number for each matrix. For each row, the entropy of the next root given the first, divided by log₂11 (the normalization Moss et al. 2019 apply to chord symbols, applied here to roots); the rows are then averaged with their frequencies as weights (the weighted mean is this site's addition). "
                "0 means the next root is always determined; 1 means the other eleven are equally likely. Even from the same data, entropy estimates come out lower when fewer transitions are drawn, so each value is the mean of 200 draws of 400 transitions per collection and mode. "
                f"These are {diff.min():.3f} to {diff.max():.3f} below the values from all transitions. The {len(blank)} cells with fewer than 400 transitions are blank. "
                f"Values run from {lo.entropy_rarefied:.3f} ({name(lo.corpus)}, {mode_name(lo['mode'])}) to {hi.entropy_rarefied:.3f} ({name(hi.corpus)}, {mode_name(hi['mode'])}). Of the {len(both)} collections with both values, minor is higher in {higher_minor}. "
                "Intervals are 95% intervals from 200 bootstrap resamples of movements (clustering by work or annotator is not taken into account); where some resamples had fewer than 400 transitions the interval is not given. The intervals show how much each value varies; they are not a test of the difference between two collections. Collections whose intervals overlap widely are not ranked here.</p>")
             + ent_html
             + ("<p>악장 단위로는 12×12 행렬을 채우기에 전이가 모자라서(악장당 중앙값 122쌍), 근음이 움직인 음정 11가지의 분포만으로 <a href='metrics/root_motion_entropy.html'>근음 진행 다양도</a>라는 지표를 냈다.</p>" if k else
                "<p>A single movement has too few transitions to fill a 12 × 12 matrix (median 122 per movement), so the movement-level metric <a href='metrics/root_motion_entropy.html'>root-motion variety</a> uses only the distribution over the eleven intervals by which the root moves.</p>"))
    # 3
    one, n_one = one_block(lang, comp)
    b.append((f"<h2>3. 악장 하나 들여다보기</h2><p>표본 {n_one}악장을 하나씩 볼 수 있다. 곡집마다 전조 횟수가 중앙값에 가장 가까운 곡, 가장 많은 곡, 가장 적은 곡이다(「낭만기 소품」 면 조성 지도와 같은 규칙. 코랄은 짧아서 뺐다).</p>"
              f"<ul><li><b>위 띠</b>는 주석된 국소 조다. 회색이 으뜸조(와 나란한조), 주황은 ♯ 쪽, 파랑은 ♭ 쪽으로 간 조이고 색이 강할수록 멀다.</li>"
              f"<li><b>가운데 정사각형</b>은 자기 유사 행렬이다. 가로·세로가 모두 마디이고, 칸이 진할수록 두 마디의 {PC_KO} 분포가 닮았다(코사인 유사도. 0.5 이하는 바탕색이고 1에서 가장 진하다). 음이 있는 마디의 대각선은 자기 자신이라 가장 진하다. 대각선과 나란한 진한 줄은 대목이 되풀이된다는 단서이고, 진한 네모는 비슷한 음들을 쓰는 구간이다. 분포가 같아도 마디 안의 음 순서와 리듬은 다를 수 있으므로, 실제로 같은 대목인지는 악보로 확인해야 한다. 쉼표뿐인 마디는 대각선까지 빈 줄이다.</li>"
              "<li><b>아래 꺾은선</b>은 4마디 창마다의 음표 밀도와 반음계 비율이다. 두 선은 각자의 최댓값에 맞춰 그렸다.</li></ul>"
              f"<p>행렬은 조에 맞춰 옮기지 않은 음고류 분포로 만든다(옥타브는 무시한다). 같은 주제가 다른 조로 돌아오면 대개 덜 닮게 나오므로 위 띠와 함께 읽어야 한다. 도돌이표는 펴지 않았다. 마디 안의 음 순서와 리듬, 음역은 반영하지 않는다(음 길이는 분포의 가중치로만 쓴다).</p>" if k else
              f"<h2>3. One movement at a time</h2><p>{n_one} sample movements: for each collection, the one whose number of key changes is closest to the collection median, the one with the most, and the one with the fewest (the rule of the key maps on the 'Romantic pieces' page; the chorales are too short and are left out).</p>"
              "<ul><li>The <b>strip on top</b> shows the annotated local keys: grey for the home key (and its relative), orange for keys on the sharp side, blue for the flat side, stronger the further away.</li>"
              "<li>The <b>square</b> is the self-similarity matrix. Both axes are measures; the stronger a cell's colour, the more alike the pitch-class distributions of the two measures (cosine similarity; 0.5 or less is left blank, 1 is strongest). On the diagonal each measure with notes is compared with itself, so it is strongest. Strong lines parallel to the diagonal suggest passages that repeat; strong squares are stretches that use similar notes. Two measures with the same distribution can still differ in the order of notes and in rhythm, so whether a passage really repeats has to be checked in the score. A measure with only rests is an empty line, diagonal included.</li>"
              "<li>The <b>lines below</b> give note density and the chromatic ratio for each 4-bar window, each scaled to its own maximum.</li></ul>"
              "<p>The matrix uses pitch-class distributions that are not transposed to the local key (octaves are ignored). A theme that returns in another key usually looks less alike, so read it with the strip. Repeats are not unfolded. The order of notes within a measure, rhythm and register are not taken into account (note lengths serve only as weights).</p>")
             + one)
    # 4
    gate_html, v, pub = gates_table(lang, table_html)
    n_pass = sum(v.values())
    assert pub == ["root_motion_entropy"] and n_pass == 2  # the sentences below say so
    rc = float(g[(g.candidate == "chromatic_window_sd") & (g.check == "length")]["value"].iloc[0])
    rd = float(g[(g.candidate == "density_window_cv") & (g.check == "length")]["value"].iloc[0])
    nwin = int(df["chromatic_window_sd"].notna().sum())
    b.append((f"<h2>4. 어느 것을 지표로 냈나</h2><p>이 면의 요약 가운데 악장 단위 수치 다섯을 지표 후보로 두고, 계산하기 전에 조건 셋을 정했다. "
              "(가) 악장 길이(로그)와의 스피어먼 순위 상관 절댓값이 0.5 이하일 것(근음 진행 다양도는 근음 변화 수와도). (나) 관련된 기존 지표와의 피어슨 상관 절댓값이 0.9 이하일 것. (다) 빈칸이 30% 이하일 것. "
              f"다섯 가운데 {n_pass}개가 조건을 지났다. 나머지 셋은 긴 악장일수록 값이 한쪽으로 가서 떨어졌다. 조건을 지난 둘 가운데 <a href='metrics/root_motion_entropy.html'>근음 진행 다양도</a>만 지표로 냈다. "
              f"반음 군집도는 계산한 뒤에 빼기로 했다. 조성 음악에서 이 값(곡집별 중앙값 {med1.min():.2f}~{med1.max():.2f})이 무엇을 뜻하는지 읽는 법을 쓸 수 없고, 기존 지표나 작곡 연도와도 거의 상관이 없어서 새 정보인지 잡음인지 이 자료로는 가를 수 없기 때문이다. "
              "지표로 내지 않은 넷은 이 면과 CSV에만 싣는다.</p>" if k else
              "<h2>4. Which summaries became metrics</h2><p>Five movement-level numbers from this page were candidates for metrics, with three conditions fixed before computing: "
              "(a) |Spearman rank correlation| with log movement length at most 0.5 (for root-motion variety, also with the number of root changes); (b) |Pearson correlation| with each related existing metric at most 0.9; (c) blank for at most 30% of movements. "
              f"{n_pass} of the five met the conditions; the other three move one way as movements get longer. Of the two that passed, only <a href='metrics/root_motion_entropy.html'>root-motion variety</a> is published as a metric. "
              f"Semitone clustering was withheld after computing: no reading can be given for its values in tonal music (collection medians {med1.min():.2f} to {med1.max():.2f}), and it hardly correlates with any existing metric or with the year composed, so these data cannot tell new information from noise. "
              "The four that are not metrics appear only here and in the CSV.</p>")
             + gate_html
             + (f"<h3>곡 안의 출렁임</h3><p>악장을 4마디 창으로 나누고(겹침 없음, 마지막 짧은 창은 버림) 창마다 반음계 비율과 음표 밀도를 낸 뒤, 반음계 비율은 창들의 표준편차를, 음표 밀도는 변동계수(표준편차 ÷ 평균)를 냈다. 온전한 창이 넷 미만인 악장은 빈칸이다({nwin:,}악장에 값이 있다. 코랄은 대부분 16마디가 안 된다). "
                f"두 값 모두 긴 악장일수록 크다(순위 상관 {mn(rc)}, {mn(rd)}). 그래서 아래 곡집별 중앙값에는 곡집마다 다른 악장 길이가 섞여 있다. 값이 있는 악장이 다섯 미만인 곡집은 비웠다.</p>" if k else
                f"<h3>Variation inside a movement</h3><p>Each movement is cut into 4-bar windows (no overlap; an incomplete last window is dropped). For each window the chromatic ratio and note density are computed; then the standard deviation of the windows' chromatic ratio and the coefficient of variation (SD ÷ mean) of their density. Movements with fewer than four complete windows are blank ({nwin:,} movements have a value; most chorales are under 16 measures). "
                f"Both grow with movement length (rank correlations {mn(rc)} and {mn(rd)}), so the collection medians below also reflect how long each collection's movements are. Collections with fewer than five movements with a value are blank.</p>")
             + window_table(df, lang, comp, table_html))
    # 5
    b.append("<p class='src'>" + ("자료·출처: " if k else "Data and sources: ")
             + "DCMLab corpora (CC BY-NC-SA 4.0); Hentschel, J., Rammos, Y., Neuwirth, M. & Rohrmeier, M. (2025), <i>Scientific Data</i> 12:685; "
             "Moss, F. C., Neuwirth, M., Harasim, D. & Rohrmeier, M. (2019), 'Statistical characteristics of tonal harmony: a corpus study of Beethoven's string quartets', <i>PLoS ONE</i> 14(6): e0217242"
             + (" — 정규화 조건부 엔트로피(식 3). 그 논문은 화음 기호 전체의 전이를 세고 근음 유지도 포함한다. 여기서는 근음만 보고 근음이 바뀌는 전이만 센다; " if k else " — normalized conditional entropy (eq. 3). That study counts transitions between full chord symbols, repetitions of a root included; here only roots are compared and only root changes counted; ")
             + "Viaccoz, C., Harasim, D., Moss, F. C. & Rohrmeier, M. (2023; online 2022), 'Wavescapes: a visual hierarchical analysis of tonality using the discrete Fourier transform', <i>Musicae Scientiae</i> 27(2): 390–427"
             + (" — 계수 크기를 영째 계수로 나누는 정규화; " if k else " — normalizing magnitudes by the zeroth coefficient; ")
             + "Yust, J. (2015), 'Schubert's harmonic language and Fourier phase space', <i>Journal of Music Theory</i> 59(1): 121–181"
             + (f" — {PC_KO} 분포의 푸리에 변환을 화성 분석에 쓴 연구(이 면은 위상을 해석하지 않는다); " if k else " — the Fourier transform of pitch-class distributions in harmonic analysis (phases are not interpreted here); ")
             + "Foote, J. (1999), 'Visualizing music and audio using self-similarity', ACM Multimedia '99"
             + (" — 자기 유사 행렬의 착상. 원 논문은 주로 음향 신호에서 뽑은 특징 벡터를 코사인으로 견주고, MIDI 음높이가 같은지로 만든 그림도 하나 싣는다. 여기서는 악보의 마디별 음고류 분포를 코사인으로 견주었다. " if k else " — the idea of the self-similarity matrix. The paper mostly compares feature vectors of the audio signal by their cosine and includes one image built from MIDI notes by whether two pitches match; here, measure-by-measure pitch-class distributions from the score are compared by cosine. ")
             + (" 데이터: <a href='../data/profiles/score_metrics_112_by_movement.csv'>악장별 분포·계수·창별 값</a>, <a href='../data/profiles/root_transitions_112.csv'>전이 행렬</a>, <a href='../data/profiles/root_transition_entropy_112.csv'>전이 엔트로피</a>, <a href='../data/profiles/metrics_112_gates.csv'>지표 판정</a>, <a href='../data/profiles/ssm_112_index.csv'>표본 악장 목록</a>(CSV)."
                if k else " Data: <a href='../data/profiles/score_metrics_112_by_movement.csv'>distributions, coefficients and window values by movement</a>, <a href='../data/profiles/root_transitions_112.csv'>transition matrices</a>, <a href='../data/profiles/root_transition_entropy_112.csv'>transition entropy</a>, <a href='../data/profiles/metrics_112_gates.csv'>metric checks</a>, <a href='../data/profiles/ssm_112_index.csv'>sample movements</a> (CSV).") + "</p>")
    return "".join(b)


def build(lang, path, page_fn, table_html):
    k = lang == "ko"
    desc = (f"악장마다의 {PC_KO} 분포와 푸리에 계수, 근음 전이 행렬, 자기 유사 행렬, 곡 안의 변동" if k
            else "Pitch-class distributions and Fourier magnitudes by movement, root-transition matrices, self-similarity matrices, variation inside a movement")
    path.write_text(page_fn(lang, PAGE[0 if k else 1], render(lang, table_html), desc=desc, active="profiles"), encoding="utf-8")
