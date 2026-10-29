"""스페인어 한글 표기 — 「세종의 글자로 보는 외래어 표기」 판 2.

sejong(ipa) = render(ipa, layer=2): 음소 IPA → 2층(옛한글) 표기. layer=1 은 현대 한글 근사.
  결과는 HTML 조각이다 — 강세 음절 <b>, 받침으로 나지 않는 자음 <small>.
  배정 값은 ../data/mapping.csv, 음절 나누기·받침 조건 등 규칙은 ../data/rules.md 에 적었다.
loan(word): 철자 → 국립국어원 「외래어 표기법」 표 2 + 제3장 제4절(에스파냐어의 표기) 1~6항(0층).
  규범에 실린 보기 60개를 모두 규범대로 적는 것을 시험으로 확인했다.
"""
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import hangul_core as HC  # noqa: E402  — 배정 값은 mapping.csv 에서(2026-10-28 판 2 이관)

VOW = "aeiou"
CONS = ["tʃ", "p", "b", "t", "d", "k", "ɡ", "f", "θ", "s", "x", "ʝ", "m", "n", "ɲ", "l", "ʎ", "ɾ", "r"]
MOD_I = HC.MOD_I
CODA = {"n": "ㄴ", "l": "ㄹ", "m": "ㅁ", "k": "ㄱ", "p": "ㅂ"}           # 받침으로 그대로 나는 것
MED = {("", "a"): "ㅏ", ("", "e"): "ㅔ", ("", "i"): "ㅣ", ("", "o"): "ㅗ", ("", "u"): "ㅜ",
       ("j", "a"): "ㅑ", ("j", "e"): "ㅖ", ("j", "o"): "ㅛ", ("j", "u"): "ㅠ", ("j", "i"): "ㅣ",
       ("w", "a"): "ㅘ", ("w", "e"): "ㅞ", ("w", "i"): "ㅟ", ("w", "o"): "ㅝ", ("w", "u"): "ㅜ"}
_TAB = {}


def _tables(layer):
    """층별 첫소리·작은 낱자 표 — mapping.csv(공통 * + es)에서 읽는다."""
    if layer not in _TAB:
        G = HC.Glyphs("es", layer)
        on = {c: G.get(c) or G.get(c, "어두") for c in CONS}
        on[""] = "ㅇ"
        sm = {c: HC.small(v) for c, v in on.items() if c}
        _TAB[layer] = (on, sm)
    return _TAB[layer]


compose = HC.compose


def tokens(w):
    out, i = [], 0
    while i < len(w):
        if w[i] == "ˈ":
            out.append("ˈ"); i += 1; continue
        if w[i] in "ˌ.":                    # 부강세·음절점은 버린다(10장 eximente ˌeksiˈmente — 전권 빌드 2026-10-28)
            i += 1; continue
        if w.startswith("tʃ", i):
            out.append("tʃ"); i += 2; continue
        out.append(w[i]); i += 1
    return out


OBS = set("pbtdkɡf")


def syllables(toks):
    """음소 → [(stress, onset[], glide, vowel, coda[], offglide)]"""
    # 핵: 모음. 앞 j/w(+모음)는 활음, 모음 뒤 j/w(+자음·끝)는 뒤 활음
    seg, stress_next = [], False
    for t in toks:
        if t == "ˈ":
            stress_next = True; continue
        seg.append((t, stress_next)); stress_next = False if t in VOW else stress_next
    # 단순화: 모음 자리 찾고 그 사이 자음 나누기
    idx = [k for k, (t, _) in enumerate(seg) if t in VOW]
    syl = []
    for n, k in enumerate(idx):
        lo = 0 if n == 0 else None
        syl.append({"v": seg[k][0], "k": k})
    # 사이 자음 묶음
    bounds = []
    prev = -1
    for n, k in enumerate(idx):
        between = [seg[x][0] for x in range(prev + 1, k)]
        bounds.append(between); prev = k
    tail = [seg[x][0] for x in range(prev + 1, len(seg))]
    res = []
    for n, k in enumerate(idx):
        cl = bounds[n]
        glide = ""
        if cl and cl[-1] in "jw":
            glide = cl[-1]; cl = cl[:-1]
        if n == 0:
            onset, prev_coda = cl, []
        else:
            # 앞 음절 뒤 활음(lej, aj …): 앞 모음 바로 뒤 j/w 하나가 있고 그 뒤 자음이 있으면 offglide
            if len(cl) >= 2 and len(cl) == 2 and cl[0] + cl[1] and cl[1] in "lɾ" and cl[0] in OBS:
                onset, prev_coda = cl, []
            elif len(cl) >= 3 and cl[-1] in "lɾ" and cl[-2] in OBS:
                onset, prev_coda = cl[-2:], cl[:-2]
            elif cl:
                onset, prev_coda = cl[-1:], cl[:-1]
            else:
                onset, prev_coda = [], []
            res[-1]["coda"] = prev_coda
        stressed = any(seg[x][1] for x in range(k - len(bounds[n]), k + 1))
        res.append({"onset": onset, "glide": glide, "v": seg[k][0], "coda": [], "stress": stressed})
    if res:
        res[-1]["coda"] = tail
    return res


def render(ipa, layer=2):
    ONSET, SMALL = _tables(layer)
    words = []
    for w in ipa.split():
        sy = syllables(tokens(w))
        html = []
        for n, s in enumerate(sy):
            on = s["onset"]
            pre = "".join(f"<small>{SMALL.get(c, c)}</small>" for c in on[:-1])
            c0 = on[-1] if on else ""
            g = s["glide"]
            if c0 in ("ɲ", "ʝ", "ʎ") and not g:
                g = "j"
            m = MED[(g, s["v"])]
            init = ONSET[c0]
            coda = list(s["coda"])
            fin = ""
            off = ""
            if coda and coda[0] in "jw":
                off = "이" if coda[0] == "j" else "우"; coda = coda[1:]
            nxt = sy[n + 1] if n + 1 < len(sy) else None
            # 모음 사이 l → 받침 ㄹ + ㄹ (우리말 ㄹㄹ = 혀옆소리)
            if nxt and not coda and not off and nxt["onset"] == ["l"]:
                fin = "ㄹ"
            elif coda and coda[0] in CODA and not off:
                fin = CODA[coda[0]]; coda = coda[1:]
            body = compose(init, m, fin) + off
            tail = "".join(f"<small>{SMALL.get(c, c)}</small>" for c in coda)
            body = pre + (f"<b>{body}</b>" if s["stress"] else body) + tail
            html.append(body)
        words.append("".join(html))
    return " ".join(words)



# ── 외래어 표기법 ──

I = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
M = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
F = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
V = {"a": "ㅏ", "e": "ㅔ", "i": "ㅣ", "o": "ㅗ", "u": "ㅜ"}
YV = {"a": "ㅑ", "e": "ㅖ", "i": "ㅣ", "o": "ㅛ", "u": "ㅠ"}      # ll·y·ñ + 모음은 한 음절(표 2 주)
WV = {"a": "ㅘ", "e": "ㅞ", "i": "ㅟ", "o": "ㅝ"}


def syl(i, m, f=" "):
    return [i, m, f]


def strip(w):
    w = w.lower().replace("ñ", "\0")
    w = "".join(c for c in unicodedata.normalize("NFD", w) if unicodedata.category(c) != "Mn")
    return w.replace("\0", "ñ")


def units(w):
    """철자 → (종류, 값) 단위. 모음 앞 활음·이중 글자를 묶는다."""
    out, i = [], 0
    while i < len(w):
        c, n2 = w[i], w[i:i + 2]
        nx = w[i + 2:i + 3]
        if n2 in ("gu", "qu") and nx in ("e", "i"):          # 제1항
            out.append(("C", "ㄱ" if c == "g" else "ㅋ")); i += 2; continue
        if n2 == "qu" and nx in ("o", "a"):
            out.append(("C", "ㅋ")); out.append(("W", "")); i += 2; continue
        if n2 == "gu" and nx == "a":
            out.append(("C", "ㄱ")); out.append(("W", "")); i += 2; continue
        if n2 == "ch":
            out.append(("C", "ㅊ")); i += 2; continue
        if n2 == "ll":
            out.append(("Y", "")); i += 2; continue
        if n2 == "rr":
            out.append(("C", "ㄹ", "r")); i += 2; continue
        if n2 == "cc":                                      # 제2항 -cc- → ㄱㅅ
            out.append(("K", "ㄱ")); out.append(("C", "ㅅ")); i += 2; continue
        if c in "aeiou":
            out.append(("V", c)); i += 1; continue
        if c == "y":
            if w[i + 1:i + 2] and w[i + 1] in "aeiou":
                out.append(("Y", "")); i += 1; continue
            out.append(("V", "i")); i += 1; continue           # 어말 y(ley) → 이
        if c == "w":
            out.append(("W", "")); i += 1; continue
        if c == "ñ":
            out.append(("C", "ㄴ")); out.append(("Y", "")); i += 1; continue
        if c == "h":
            i += 1; continue
        if c == "c":
            out.append(("C", "ㅅ" if nx_vowel(w, i, "ei") else "ㅋ", "c")); i += 1; continue
        if c == "g":
            out.append(("C", "ㅎ" if nx_vowel(w, i, "ei") else "ㄱ", "g")); i += 1; continue
        if c == "x":
            if i == 0 and nx_vowel(w, i):
                out.append(("C", "ㅅ")); i += 1; continue      # 제4항 어두
            out.append(("K", "ㄱ")); out.append(("C", "ㅅ", "s")); i += 1; continue
        m = {"b": "ㅂ", "v": "ㅂ", "d": "ㄷ", "f": "ㅍ", "j": "ㅎ", "k": "ㅋ", "l": "ㄹ", "m": "ㅁ", "n": "ㄴ",
             "p": "ㅍ", "q": "ㅋ", "r": "ㄹ", "s": "ㅅ", "t": "ㅌ", "z": "ㅅ"}
        out.append(("C", m[c], c)); i += 1
    return out


def nx_vowel(w, i, only="aeiou"):
    return i + 1 < len(w) and w[i + 1] in only


CODA_OK = {"ㄴ": "ㄴ", "ㄹ": "ㄹ", "ㅁ": "ㅁ"}
SCHWA = {"b": "ㅂ", "v": "ㅂ", "d": "ㄷ", "f": "ㅍ", "g": "ㄱ", "k": "ㅋ", "r": "ㄹ", "s": "ㅅ", "t": "ㅌ", "z": "ㅅ",
         "c": "ㅋ", "p": "ㅍ", "q": "ㅋ", "ch": "ㅊ"}


def loan(word):
    out = []
    word = re.sub(r"[¿?¡!.,;:«»\"()]", "", word.replace("-", " "))   # 하이픈은 낱말 경계, 문장부호는 버린다(13장 contencioso-administrativo, 20장 ¿podría repetir?)
    for w in word.split():
        out.append(loan1(strip(w)))
    return " ".join(out)


def loan1(w):
    U = units(w)
    S = []                       # 음절 [초, 중, 종]
    i = 0
    while i < len(U):
        k = U[i]
        nxt = U[i + 1] if i + 1 < len(U) else None
        if k[0] == "V":
            init = "ㅇ"
            S.append(syl(init, V[k[1]])); i += 1; continue
        if k[0] in ("Y", "W"):
            # 앞 자음 없이 활음 + 모음
            if nxt and nxt[0] == "V":
                m = (YV if k[0] == "Y" else WV).get(nxt[1]) if not (k[0] == "W" and nxt[1] == "u") else "ㅜ"
                if k[0] == "W" and S and False:
                    pass
                S.append(syl("ㅇ", m or V[nxt[1]])); i += 2; continue
            i += 1; continue
        if k[0] == "K":          # 받침 ㄱ(cc·x)
            if S and S[-1][2] == " ":
                S[-1][2] = "ㄱ"
            else:
                S.append(syl("ㅇ", "ㅡ", "ㄱ"))
            i += 1; continue
        # 자음
        ch = k[1]; src = k[2] if len(k) > 2 else ""
        if nxt and nxt[0] == "V":
            # 어중 l → ㄹㄹ(제5항): 앞 음절에 받침이 없으면 ㄹ 받침을 더한다
            if src == "l" and S and S[-1][2] == " ":
                S[-1][2] = "ㄹ"
            S.append(syl(ch, V[nxt[1]])); i += 2; continue
        if nxt and nxt[0] in ("Y", "W") and i + 2 < len(U) and U[i + 2][0] == "V":
            v = U[i + 2][1]
            if nxt[0] == "Y":
                m = YV[v]
            else:                 # qu·gu + a → 과·콰(제1항), + o → 구오·쿠오
                m = WV.get(v) if v == "a" else None
            if src == "l" and S and S[-1][2] == " ":
                S[-1][2] = "ㄹ"
            if m:
                S.append(syl(ch, m)); i += 3; continue
            S.append(syl(ch, "ㅜ")); i += 2; continue      # 구오·쿠오: 활음을 우로
        # 자음 앞·어말
        if src == "n" and nxt and nxt[0] == "C" and len(nxt) > 2 and nxt[2] in ("c", "g") and nxt[1] in ("ㅋ", "ㄱ"):
            ch = "ㅇ"                                      # 제6항
        if ch in ("ㄴ", "ㄹ", "ㅁ", "ㅇ") and src in ("n", "l", "m"):
            if S and S[-1][2] == " ":
                S[-1][2] = ch if ch != "ㅇ" else "ㅇ"; i += 1; continue
        liq = nxt and nxt[0] == "C" and len(nxt) > 2 and nxt[2] in ("l", "r")
        if src in ("c", "p") and not liq and nxt is not None and S and S[-1][2] == " ":
            S[-1][2] = "ㄱ" if src == "c" else "ㅂ"; i += 1; continue
        if src == "c" and nxt is None and S and S[-1][2] == " ":
            S[-1][2] = "ㄱ"; i += 1; continue                 # bistec 비스텍
        if src == "j" and nxt is None:
            i += 1; continue                                  # reloj 렐로
        if src == "l" and (nxt is None or nxt[0] == "C") and S and S[-1][2] == " ":
            S[-1][2] = "ㄹ"; i += 1; continue
        S.append(syl(SCHWA.get(src, ch) if src else ch, "ㅡ"))
        # 자음 + l 무리: 「으」 음절에 ㄹ 받침(블·플·글)
        if nxt and len(nxt) > 2 and nxt[2] == "l" and i + 2 < len(U) and U[i + 2][0] in ("V", "Y"):
            S[-1][2] = "ㄹ"
        i += 1
    return "".join(chr(0xAC00 + (I.index(a) * 21 + M.index(b)) * 28 + F.index(c)) for a, b, c in S)



sejong = render
