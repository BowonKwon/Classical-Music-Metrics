"""Attach composers to Seoul Philharmonic programs (Seoul Open Data OA-22909 Korean / OA-22910 English, KOGL Type 1).

Both editions carry the same 곡목 field: English work titles only, no composer, several titles run together without a
separator. This script (1) splits the field into titles, (2) attributes a composer to each title from the title itself,
and (3) checks and supplements that with composer names mentioned in the concert's own text (공연명, 국문 프로그램소개).

Method 1 - title evidence, in this order:
  catalog   a catalogue marker that belongs to one composer (BWV, HWV, K./KV, D, Hob., WWV, TrV, RV, Sz/BB, FP, JW)
  exact     the normalized title appears in a reference title list (Carnegie Hall + NY Phil) with one composer
  feature   (genre, catalogue/opus number) or (genre, number, key) maps to one composer in the reference list
A key is used only if it occurs at least MIN_N times and the leading composer has at least MIN_SHARE of occurrences.

Method 2 - concert text: composers whose surname (English, 공연명) or Korean name (Wikidata ko labels + site table)
appears in the concert's text. Used (a) as an agreement check on method 1 and (b) to settle a title that method 1
left open when exactly one mentioned composer fits a relaxed key (genre + number, or genre + key) - method 'text+feature'.

Output data/derived/seoulphil_works.csv (one row per concert x title) and seoulphil_attrib_summary.json.
"""
import glob
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from orch_compare import invert, norm  # noqa: E402

RAW = ROOT / "data" / "raw"
ALI = ROOT / "data" / "aliases"
DER = ROOT / "data" / "derived"
MIN_N, MIN_SHARE = 2, 0.9
# Text-based assignment ('text+feature', 'text+genre') was audited on 2026-11-07 (stratified sample): about 5 of 15 and
# 8 of 9 correct. Concert notes name composers who are not on the program (comparisons, influences), so a mention does
# not identify the work. Off: concert text is used only as an agreement check on title-based attributions.
USE_TEXT_ASSIGN = False

CATALOG = [  # marker regex -> canonical composer (NY Phil form)
    (r"\bBWV\b", "Bach, Johann Sebastian"), (r"\bHWV\b", "Handel, George Frideric"),
    (r"\bK(?:V\.?\s?|\.\s?)\d{1,3}[a-z]?\b", "Mozart, Wolfgang Amadeus"), (r"\bD\.?\s?\d{2,3}\b", "Schubert, Franz"),
    (r"\bHob\.?", "Haydn, Franz Joseph"), (r"\bWWV\b", "Wagner, Richard"), (r"\bTrV\b", "Strauss, Richard"),
    (r"\bRV\s?\d", "Vivaldi, Antonio"), (r"\b(?:Sz|BB)\.?\s?\d", "Bartok [Bartók], Béla"), (r"\bFP\s?\d", "Poulenc, Francis"),
    (r"\bJW\s?[IVX]", "Janacek [Janácek], Leoš"), (r"\bWAB\s?\d", "Bruckner, Anton"),
    (r"(?:,|\s)L\.\s?\d{1,3}\b", "Debussy, Claude"), (r"(?:,|\s)M\.\s?\d{1,2}\b", "Ravel, Maurice"),
]
GENRES = ["symphony", "concerto", "overture", "suite", "quartet", "quintet", "sonata", "serenade", "rhapsody", "variations",
          "requiem", "mass", "prelude", "fantasy", "fantasia", "poem", "dances", "dance", "march", "waltz", "scherzo",
          "nocturne", "sinfonietta", "divertimento", "trio", "septet", "octet", "sextet", "concertino", "ballade", "symphonie"]
INSTR = ["piano", "violin", "cello", "viola", "flute", "oboe", "clarinet", "bassoon", "horn", "trumpet", "trombone", "harp",
         "organ", "guitar", "percussion", "timpani", "saxophone", "double bass", "tuba", "marimba"]


OPEN_OK = re.compile(r"(?:^|\s)[lLdD]$")  # l'Oye, d'Indy: elision, not a closing quote


def split_titles(s: str) -> list[str]:
    """'…Op. 37Symphony No. 9…' -> two titles. A new title starts (a) where a capital + lowercase letter directly
    follows a lowercase letter, digit, bracket or a closing quote (a quote preceded by a non-space that is not an
    elision like l'), or (b) after an opus/catalogue number followed by a space and a capitalized word other than No."""
    s = html.unescape(html.unescape(str(s))).replace(" ", " ")
    cuts = []
    for m in re.finditer(r"(?=[A-Z][a-z])", s):
        i = m.start()
        if i == 0:
            continue
        prev = s[i - 1]
        if re.match(r"[a-z0-9)\]]", prev):
            cuts.append(i)
        elif prev in "'’”\"" and i >= 2 and not s[i - 2].isspace() and not OPEN_OK.search(s[:i - 1]):
            cuts.append(i)
    for m in re.finditer(r"\b(?:Op\.?|K\.|BWV|HWV|D\.?|Hob\.?\s?[IVX]+:|WAB|TrV|Sz\.?|L\.|M\.)\s?\d+[a-z]?(?:,? No\. \d+)? (?=(?!Nos?\b)[A-Z][a-z])", s):
        cuts.append(m.end())
    # 'Op. 84, Hob.I:105, Symphony No. 9 …': a catalogue number, a comma, then a genre word starts a new title
    for m in re.finditer(r"(?:Op\.?|K\.|BWV|HWV|D\.?|Hob\.?\s?[IVX]+:|WAB|TrV|Sz\.?|L\.|M\.)\s?\d+[a-z]?, (?=(?:Symphony|Concerto|Piano|Violin|Cello|Viola|String|Overture|Suite|Serenade|Requiem|Mass)\b)", s):
        cuts.append(m.end())
    parts, last = [], 0
    for c in sorted(set(cuts)):
        parts.append(s[last:c]); last = c
    parts.append(s[last:])
    return [p.strip(" ,;") for p in parts if p.strip(" ,;'’")]


def key_name(t: str) -> str | None:
    t = t.lower().replace("♭", " flat").replace("♯", " sharp")
    m = re.search(r"\b([a-g])(?:[\s-]*(flat|sharp|b(?=\s)))?\s*-?\s*(major|minor|dur|moll)\b", t)
    if not m:
        return None
    acc = {"flat": "b", "b": "b", "sharp": "#"}.get(m.group(2) or "", "")
    mode = {"dur": "major", "moll": "minor"}.get(m.group(3), m.group(3))
    return f"{m.group(1)}{acc} {mode}"


def features(t: str) -> dict:
    low = t.lower()
    genre = next((g for g in GENRES if re.search(rf"\b{g}\b", low)), None)
    if genre == "symphonie":
        genre = "symphony"
    inst = next((i for i in INSTR if i in low), None) if genre in ("concerto", "sonata", "concertino") else None
    num = re.search(r"\bno\.?\s*(\d+)", low)
    op = re.search(r"\b(?:op(?:us)?\.?)\s*(\d+[a-z]?)(?:[,\s]*no\.?\s*(\d+))?", low)
    cat = re.search(r"\b(bwv|hwv|kv|k|d|hob\.?\s*[ivx]+:?|wwv|trv|rv|sz|bb|fp|woo|s|m|h|b|l)\.?\s*(\d+[a-z]?)\b", low)
    g = f"{genre}:{inst}" if inst else genre
    return {"genre": g, "num": num.group(1) if num else None, "key": key_name(t),
            "opus": f"op{op.group(1)}" + (f"/{op.group(2)}" if op and op.group(2) else "") if op else None,
            "cat": f"{cat.group(1).replace(' ', '')}{cat.group(2)}" if cat and not op else None}


def tnorm(t: str) -> str:
    t = html.unescape(t).lower().replace("♭", " flat").replace("♯", " sharp").replace("-", " ")
    t = re.sub(r"[‘’“”'\"?]", "", t)
    return re.sub(r"[^a-z0-9 ]+", " ", re.sub(r"\s+", " ", t)).strip()


GENERIC = set(GENRES) | {w for i in INSTR for w in i.split()} | {
    "in", "no", "nos", "op", "opus", "major", "minor", "flat", "sharp", "a", "b", "c", "d", "e", "f", "g", "for", "and", "the", "of",
    "from", "orchestra", "string", "strings", "suite", "excerpts", "selections", "arr", "by", "with", "symphonic", "orchestral",
    "dur", "moll", "en", "et", "la", "le", "de", "des", "to", "act", "movement", "mvt", "version", "rev", "two", "three", "four",
    "chamber", "small", "grand", "sinfonia", "concert", "solo", "piece", "pieces", "work", "k", "kv", "bwv", "hwv", "hob", "wab", "trv"}


QUOTED = re.compile(r"[‘'“\"(][^’'”\")]{2,40}[’'”\")]")


def stem(w: str) -> str:
    return w[:-1] if len(w) > 4 and w.endswith("s") and not w.endswith("ss") else w  # winds -> wind, violins -> violin


GENERIC_STEM = {stem(g) for g in GENERIC} | {"wind", "brass", "voice", "soprano", "tenor", "ensemble", "instrument", "player"}


def distinct(t: str, keep_quoted: bool = False) -> frozenset:
    """Distinctive title words, plural-folded. For the title being attributed, nicknames in quotes or brackets
    ('Choral', (Eroica)) are dropped: reference lists often omit them. Reference titles keep them (keep_quoted=True),
    so an unquoted nickname in a Seoul title ('…Op. 90, Italian') can still meet the reference's '(ITALIAN)'."""
    t = html.unescape(t) if keep_quoted else QUOTED.sub(" ", html.unescape(t))
    ws = (stem(w) for w in tnorm(t).split() if not w.isdigit() and len(w) > 2)
    return frozenset(w for w in ws if w not in GENERIC and w not in GENERIC_STEM)


def feature_keys(f: dict) -> list[tuple]:
    """Most specific first: (genre, number, opus) before (genre, opus)."""
    keys = []
    if f["genre"] and f["num"] and (f["opus"] or f["cat"]):
        keys.append(("g+n+op", f["genre"], f["num"], f["opus"] or f["cat"]))
    if f["genre"] and (f["opus"] or f["cat"]):
        keys.append(("g+op", f["genre"], f["opus"] or f["cat"]))
    if f["genre"] and f["num"] and f["key"] and not (f["opus"] or f["cat"]):
        keys.append(("g+n+k", f["genre"], f["num"], f["key"]))
    return keys


def reference() -> tuple[dict, dict, dict, dict]:
    """Reference title lists. Carnegie titles are in the same English style as Seoul's; NY Phil's are upper-case
    inverted ('SYMPHONY NO. 5, E MINOR, OP. 64') and enter only through feature keys."""
    xw = pd.read_csv(ALI / "orch_composer_xwalk.csv")
    xmap = dict(zip(xw.composer_raw, xw.composer))
    exact, feat = defaultdict(Counter), defaultdict(Counter)
    words = defaultdict(set)  # (key, composer) -> distinctive words seen in reference titles
    keys = defaultdict(set)  # (key, composer) -> tonalities named in reference titles
    for f in glob.glob(str(RAW / "carnegiehall" / "works" / "page-*.json")):
        for b in json.loads(Path(f).read_text(encoding="utf-8"))["results"]["bindings"]:
            t, c = b.get("workLabel", {}).get("value"), b.get("compLabel", {}).get("value")
            if not t or not c:
                continue
            comp = xmap.get(invert(c), invert(c))
            exact[tnorm(t)][comp] += 1
            for k in feature_keys(features(t)):
                feat[k][comp] += 1
                words[(k, comp)] |= distinct(t, keep_quoted=True)
                if key_name(t):
                    keys[(k, comp)].add(key_name(t))
    import repertoire_metrics as rm
    ny = rm.apply_aliases(rm.load_entries(RAW), ALI / "nyphil_composers.csv")
    for t, c in ny.loc[ny["flag"] == "person", ["work_title", "composer"]].itertuples(index=False):
        for k in feature_keys(features(t)):
            feat[k][c] += 1
            words[(k, c)] |= distinct(t, keep_quoted=True)
            if key_name(t):
                keys[(k, c)].add(key_name(t))
    return exact, feat, words, keys


def decide(counter: Counter | None) -> str | None:
    if not counter:
        return None
    n = sum(counter.values())
    top, k = counter.most_common(1)[0]
    return top if n >= MIN_N and k / n >= MIN_SHARE else None


def name_lexicon() -> list[tuple[str, str]]:
    """(pattern, canonical composer). Korean: Wikidata ko label's last word and alt labels; English: surname."""
    pats = []
    ko = pd.read_csv(ALI / "composer_ko_labels_wikidata.csv")
    for r in ko.itertuples(index=False):
        for lab in (r.ko_label, r.ko_alt):
            if isinstance(lab, str) and lab.strip():
                last = lab.split()[-1]
                if len(last) >= 2:
                    pats.append((last, r.composer))
    for c in ko.composer.unique():
        sur = c.split(",")[0].split("[")[0].strip()
        if len(sur) >= 4:
            pats.append((sur, c))
    seen, out = set(), []
    for p, c in pats:
        if (p, c) not in seen:
            seen.add((p, c)); out.append((p, c))
    return out


def mentioned(text: str, lex: list[tuple[str, str]]) -> set[str]:
    hits = set()
    for p, c in lex:
        if re.search(r"[가-힣]", p):
            if re.search(rf"(?<![가-힣]){re.escape(p)}(?:의|는|은|이|가|를|을|와|과|에|도|로|,|\s|$|’|'|”|\")", text):
                hits.add(c)
        elif re.search(rf"\b{re.escape(p)}\b", text):
            hits.add(c)
    return hits


def main():
    base = RAW / "seoulphil_datagokr"
    ko = pd.read_csv(base / "seoulphil_ko_OA-22909.csv", encoding="cp949", encoding_errors="replace")
    en = pd.read_csv(base / "seoulphil_en_OA-22910.csv", encoding="cp949", encoding_errors="replace")
    m = ko.merge(en[["공연일련번호", "공연명", "공연구분1"]], on="공연일련번호", suffixes=("", "_en"))
    exact, feat, words, keys = reference()
    lex = name_lexicon()
    # Hand-made title table (data/aliases/seoulphil_title_manual.csv): titles the rules cannot settle or split.
    # 'composers' may list several composers separated by ';' when two works were run together; an empty part
    # means that work's composer is not established. Source 'editor' = assigned by the editing session, to be checked.
    mpath = ALI / "seoulphil_title_manual.csv"
    manual = dict(pd.read_csv(mpath, dtype=str, keep_default_na=False)[["title", "composers"]].values) if mpath.exists() else {}
    rows = []
    for r in m.itertuples(index=False):
        if not isinstance(r.곡목, str):
            continue
        intro = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", html.unescape(str(r.프로그램소개 or "")))))
        text = " ".join(str(x) for x in (r.공연명, r.공연명_en, intro) if isinstance(x, str))
        ment = mentioned(text, lex)
        for t in split_titles(r.곡목):
            if t in manual:
                for i, c in enumerate(manual[t].split(";")):
                    c = c.strip() or None
                    rows.append({"concert_id": r.공연일련번호, "date": str(r.공연일시)[:10].replace(".", "-"), "type_ko": r.공연구분1,
                                 "type_en": r.공연구분1_en, "series": r.공연구분2, "title": t + (f" [part {i + 1}]" if ";" in manual[t] else ""),
                                 "genre": features(t)["genre"], "composer": c, "method": "manual" if c else "none",
                                 "text_mentions": "; ".join(sorted(ment)), "agrees_with_text": (c in ment) if (c and ment) else None})
                continue
            f = features(t)
            comp, how = None, None
            for pat, c in CATALOG:
                if re.search(pat, t):
                    comp, how = c, "catalog"
                    break
            if not comp:
                comp = decide(exact.get(tnorm(t)))
                how = "exact" if comp else None
            if not comp:
                dt = distinct(t)
                for k in feature_keys(f):
                    c = decide(feat.get(k))
                    # a title with its own distinctive words must share one with the reference titles of that key
                    # reject only when the title carries two or more distinctive words and none occurs in the
                    # reference titles of that key ('Pelleas et Melisande Suite, Op. 46' is not 'Peer Gynt Suite, Op. 46')
                    # 2026-11-07 Codex check: 'Romanian Rhapsody No. 1, Op. 11' had gone to Dohnanyi's Rhapsody Op. 11 and
                    # 'Piano Quintet in E-flat, Op. 87' (Hummel) to Mendelssohn's Op. 87 (B-flat). Now: any distinctive word
                    # must recur in the reference titles (nicknames are already removed), and a stated key must match.
                    key_ok = not f["key"] or not keys[(k, c)] or f["key"] in keys[(k, c)]
                    if c and key_ok and (not dt or not words[(k, c)] or dt & words[(k, c)]):
                        comp, how = c, "feature"
                        break
            if USE_TEXT_ASSIGN and not comp and ment and f["genre"]:
                fits = set()
                for c in ment:
                    for k, cnt in feat.items():
                        if k[1] == f["genre"] and cnt.get(c) and (
                                (f["num"] and k[0] == "g+n+k" and k[2] == f["num"]) or (f["key"] and k[0] == "g+n+k" and k[3] == f["key"])):
                            fits.add(c)
                if len(fits) == 1:
                    comp, how = fits.pop(), "text+feature"
            if USE_TEXT_ASSIGN and not comp and ment and f["genre"] and not (f["num"] or f["key"] or f["opus"] or f["cat"]) and not distinct(t):
                # bare title ('Violin Concerto'): only if exactly one mentioned composer has that genre in the references
                fits = {c for c in ment if any(k[1] == f["genre"] and cnt.get(c) for k, cnt in feat.items())}
                if len(fits) == 1:
                    comp, how = fits.pop(), "text+genre"
            rows.append({"concert_id": r.공연일련번호, "date": str(r.공연일시)[:10].replace(".", "-"), "type_ko": r.공연구분1,
                         "type_en": r.공연구분1_en, "series": r.공연구분2, "title": t, "genre": f["genre"], "composer": comp,
                         "method": how or "none", "text_mentions": "; ".join(sorted(ment)),
                         "agrees_with_text": (comp in ment) if (comp and ment) else None})
    w = pd.DataFrame(rows)
    w.to_csv(DER / "seoulphil_works.csv", index=False, encoding="utf-8", lineterminator="\n")
    sub = w[w.type_ko == "정기공연"]
    att = sub[sub.composer.notna()]
    summ = {
        "concerts_with_programme": int(w.concert_id.nunique()), "titles": len(w),
        "subscription_titles": len(sub), "subscription_attributed": round(float(sub.composer.notna().mean()), 4),
        "by_method_subscription": sub.method.value_counts().to_dict(),
        "text_check_n": int(att.agrees_with_text.notna().sum()),
        "text_check_agree": round(float(att.agrees_with_text.dropna().mean()), 4) if att.agrees_with_text.notna().any() else None,
        "text_check_by_method": att.dropna(subset=["agrees_with_text"]).groupby("method").agrees_with_text.agg(["size", "mean"]).round(3).to_dict("index"),
    }
    (DER / "seoulphil_attrib_summary.json").write_text(json.dumps(summ, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
