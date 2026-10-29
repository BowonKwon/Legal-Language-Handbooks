"""러시아어 한글 표기 — 「세종의 글자로 보는 외래어 표기」 판 2.

sejong(ipa, layer=2): 음소 IPA → 2층(옛한글) 표기. layer=1 은 현대 한글 근사.
  결과는 HTML 조각이다 — 강세 음절 <b>, 모음 없이 나는 자음 <small>.
  배정 값은 ../data/mapping.csv, 경·연자음과 모음의 결합 등 규칙은 ../data/rules.md 에 적었다.
loan(word): 키릴 철자 → 국립국어원 「외래어 표기법」 표 19 + 제3장 제21절(러시아어의 표기) 1~10항(0층).
  규범에 실린 보기 121개를 모두 규범대로 적는 것을 시험으로 확인했다. ъ 는 규범에 규정이 없어서
  앞 자음을 「자음 앞」으로 다룬다.
"""
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import hangul_core as HC  # noqa: E402  — 배정 값은 mapping.csv 에서(2026-10-28 판 2 이관)

# ── 세종의 글자로 ──

MOD_I, MOD_M, MOD_F = HC.MOD_I, HC.MOD_M, HC.MOD_F
FILLER = HC.FILLER_V
# 엔진이 읽는 분절음 목록과 mapping.csv 에 행이 없을 때의 값(괄호 안 별칭은 mapping 의 어느 행을 따르는지)
BASE = {"p": "ㅃ", "b": "ㅂ", "t": "ㄸ", "d": "ㄷ", "k": "ㄲ", "ɡ": "ㄱ", "g": "ㄱ", "s": "ㅅ", "x": "ㅎ", "ɣ": "ㅎ",
        "m": "ㅁ", "n": "ㄴ", "ɲ": "ㄴ", "ɫ": "ㄹ", "l": "ㄹ", "j": "ㅇ",
        "t͡ɕ": "ㅉ", "ɕ": "ㅆ",
        "f": "ᅗ", "v": "ᄫ", "z": "ᅀ", "ʑ": "ᅀ", "d͡z": "ᅀ", "d͡ʑ": "ᅀ", "ʂ": "ᄾ", "ʐ": "ᄿ", "d͡ʐ": "ᄿ",
        "t͡s": "ᅎ", "r": "ᄙ", "ɾ": "ᄙ"}
ALIAS = {"g": "ɡ", "ɣ": "x", "ʑ": "z", "d͡z": "z", "d͡ʑ": "z", "d͡ʐ": "ʐ", "ɾ": "r"}
CONS = sorted(BASE, key=len, reverse=True)
ALWAYS_SOFT = {"ɕ", "ʑ", "t͡ɕ", "d͡ʑ"}           # ч·щ — 뒤 모음을 ㅑ계열로(ㅉ 은 이미 구개음이라 예외)
NO_Y = {"t͡ɕ", "ʂ", "ʐ", "d͡ʐ", "t͡s"}            # ㅑ계열로 바꾸지 않는다
V_BASE = {"a": "ㅏ", "ɐ": "ㅏ", "ə": "ㅓ", "ɪ": "ㅣ", "i": "ㅣ", "ɨ": "ㅡ", "e": "ㅔ", "ɛ": "ㅔ", "o": "ㅗ", "ɵ": "ㅗ",
          "u": "ㅜ", "ʊ": "ㅜ", "ʉ": "ㅜ", "æ": "ㅐ"}
V = V_BASE                                        # _tokens 가 모음 판정에 쓴다(값은 _tables 에서)
Y = {"ㅏ": "ㅑ", "ㅓ": "ㅕ", "ㅗ": "ㅛ", "ㅜ": "ㅠ", "ㅔ": "ㅖ", "ㅐ": "ㅒ", "ㅣ": "ㅣ", "ㅡ": "ㅣ"}
_TAB = {}


def _tables(layer):
    """층별 첫소리·모음 표 — mapping.csv(공통 * + ru)에서. 행이 없으면 BASE 값."""
    if layer not in _TAB:
        G = HC.Glyphs("ru", layer)
        on = {}
        for c, v in BASE.items():
            k = ALIAS.get(c, c)
            on[c] = G.get(k) or G.get(k, "어두") or v
        vw = {c: (G.get(c) or v) for c, v in V_BASE.items()}
        _TAB[layer] = (on, vw)
    return _TAB[layer]


_compose = HC.compose


def _small(c, soft, ONSET):
    i = ONSET[c]
    if soft:
        return _compose(i, "ㅣ")
    return HC.small(i)


def _tokens(ipa):
    s = re.sub(r"\(ː\)|⁽[^⁾]*⁾|[\[\]/.‿ˌ]", "", str(ipa))
    s = s.replace("ɪ̯", "J").replace("i̯", "J").replace("-", " ")
    out, i, stress = [], 0, False
    while i < len(s):
        ch = s[i]
        if ch == "ˈ":
            stress = True; i += 1; continue
        if ch == " ":
            out.append(("sep",)); i += 1; continue
        if ch in V:
            out.append(("V", ch, stress)); stress = False; i += 1; continue
        if ch in "jJ":
            out.append(("J",)); i += 1; continue
        c = next((x for x in CONS if s.startswith(x, i)), None)
        if c is None:
            i += 1; continue                     # ː 등 — 근사라 버린다
        i += len(c)
        soft = False
        while i < len(s) and s[i] in "ʲː":
            soft = soft or s[i] == "ʲ"; i += 1
        out.append(("C", c, soft or c in ALWAYS_SOFT))
    return out


def sejong(ipa, layer=2):
    ONSET, V = _tables(layer)
    t = _tokens(ipa)
    out = []                                  # {"k": "syl"|"small"|"sep", ...}
    k = 0
    while k < len(t):
        x = t[k]
        nx = t[k + 1] if k + 1 < len(t) else None
        if x[0] == "sep":
            out.append({"k": "sep"}); k += 1; continue
        if x[0] == "V":
            out.append({"k": "syl", "i": "ㅇ", "m": V[x[1]], "f": "", "st": x[2]}); k += 1; continue
        if x[0] == "J":
            if nx and nx[0] == "V":
                out.append({"k": "syl", "i": "ㅇ", "m": Y[V[nx[1]]], "f": "", "st": nx[2]}); k += 2; continue
            out.append({"k": "syl", "i": "ㅇ", "m": "ㅣ", "f": "", "st": False}); k += 1; continue   # 뒤 활음 ɪ̯ → 이
        c, soft = x[1], x[2]
        prev = out[-1] if out and out[-1]["k"] == "syl" and not out[-1]["f"] else None
        if nx and nx[0] == "V":
            m = V[nx[1]]
            if soft and c not in NO_Y:
                m = Y[m]
            if c in ("ɫ", "l") and prev:          # 모음 사이 l → 받침 ㄹ + ㄹ (es_hangul 과 같음)
                prev["f"] = "ㄹ"
            out.append({"k": "syl", "i": ONSET[c], "m": m, "f": "", "st": nx[2]}); k += 2; continue
        if not soft and c in ("n", "m", "ɫ") and prev:
            prev["f"] = {"n": "ㄴ", "m": "ㅁ", "ɫ": "ㄹ"}[c]; k += 1; continue
        out.append({"k": "small", "s": _small(c, soft, ONSET)}); k += 1
    html = []
    for o in out:
        if o["k"] == "sep":
            html.append(" ")
        elif o["k"] == "small":
            html.append(f"<small>{o['s']}</small>")
        else:
            s = _compose(o["i"], o["m"], o["f"])
            html.append(f"<b>{s}</b>" if o["st"] else s)
    return "".join(html).strip()


# ── 외래어 표기법(표 19 + 제3장 제21절) ──

VOICED = set("бвгджзлмнр")
VOICELESS = set("пфктсшщхцч")
CONS_RU = VOICED | VOICELESS
VOW_RU = set("аеёиоуыэюя")
C_MOD = {"б": "ㅂ", "в": "ㅂ", "г": "ㄱ", "д": "ㄷ", "ж": "ㅈ", "з": "ㅈ", "к": "ㅋ", "л": "ㄹ", "м": "ㅁ", "н": "ㄴ",
         "п": "ㅍ", "р": "ㄹ", "с": "ㅅ", "т": "ㅌ", "ф": "ㅍ", "х": "ㅎ", "ц": "ㅊ", "ч": "ㅊ", "ш": "ㅅ", "щ": "ㅅ", "тч": "ㅊ"}
# 무성 자음 앞 받침(제1항) · 유성 자음 앞 · 어말
BEFORE_VL = {"б": "ㅂ", "в": "ㅂ", "п": "ㅂ", "ф": "ㅂ", "к": "ㄱ", "г": "ㄱ", "т": "ㅅ", "д": "ㅅ"}
SYL = {"б": ("브", "프"), "в": ("브", "프"), "п": ("프", "프"), "ф": ("프", "프"), "к": ("크", "크"), "г": ("그", "크"),
       "т": ("트", "트"), "д": ("드", "트"), "з": ("즈", "스"), "ж": ("즈", "시"), "х": ("흐", "흐"), "р": ("르", "르"),
       "с": ("스", "스"), "ш": ("시", "시"), "щ": ("시", "시"), "ч": ("치", "치"), "ц": ("츠", "츠"), "тч": ("치", "치")}
VSOLO = {"а": "ㅏ", "о": "ㅗ", "у": "ㅜ", "и": "ㅣ", "ы": "ㅣ", "е": "ㅖ", "э": "ㅖ", "я": "ㅑ", "ё": "ㅛ", "ю": "ㅠ"}
VAFTER = {"а": "ㅏ", "о": "ㅗ", "у": "ㅜ", "и": "ㅣ", "ы": "ㅣ", "е": "ㅔ", "э": "ㅔ", "я": "ㅑ", "ё": "ㅛ", "ю": "ㅠ"}
DEY = {"ㅑ": "ㅏ", "ㅖ": "ㅔ", "ㅛ": "ㅗ", "ㅠ": "ㅜ"}            # ㅈ·ㅊ 뒤 이중 모음 → 단모음(고르바초프)
SHY = {"ㅏ": "ㅑ", "ㅔ": "ㅖ", "ㅗ": "ㅛ", "ㅜ": "ㅠ"}            # ш·щ 의 「시」가 모음과 합친다(표 19 주)


def _syl(i, m, f=" "):
    return [i, m, f]


def _render(S):
    return "".join(chr(0xAC00 + (MOD_I.index(i) * 21 + MOD_M.index(m)) * 28 + MOD_F.index(f)) for i, m, f in S)


def _hangul(text):
    """「브」 같은 완성 음절을 [초, 중, 종] 으로."""
    out = []
    for ch in text:
        n = ord(ch) - 0xAC00
        out.append([MOD_I[n // 588], MOD_M[(n % 588) // 28], MOD_F[n % 28]])
    return out


def _units(w):
    """철자 → 단위 목록. 이중 글자·겹자음(제7항)·дс(제4항)·дз/дж(제10항)·тс 를 먼저 묶는다."""
    out, i = [], 0
    while i < len(w):
        c, two, nx = w[i], w[i:i + 2], w[i + 2:i + 3]
        if two in ("дз", "дж"):
            out.append(("C", two[1])); i += 2; continue
        if two == "дс" and nx and nx in CONS_RU:
            out.append(("C", "ц")); i += 2; continue
        if two == "тс":
            out.append(("C", "ц")); i += 2; continue
        if two == "тч":
            out.append(("C", "тч")); i += 2; continue
        if c in CONS_RU and i + 1 < len(w) and w[i + 1] == c:
            if c in "мн" and nx and nx in VOW_RU:   # mm·nn 은 모음 앞에서 ㅁㅁ·ㄴㄴ
                out.append(("C", c)); i += 1; continue
            i += 1; continue                          # 같은 자음 겹침은 하나로
        if c in CONS_RU:
            out.append(("C", c)); i += 1; continue
        if c in VOW_RU:
            out.append(("V", c)); i += 1; continue
        if c == "й":
            out.append(("J",)); i += 1; continue
        if c == "ь":
            out.append(("SOFT",)); i += 1; continue
        if c == "ъ":
            out.append(("HARD",)); i += 1; continue
        i += 1
    return out


def _strip(word):
    w = unicodedata.normalize("NFD", word.lower())
    w = w.replace("́", "").replace("̀", "")
    w = unicodedata.normalize("NFC", w)
    return w.replace("a", "а").replace("e", "е").replace("o", "о")   # 규범 보기에 섞인 로마자(Ростопчинa)


def loan(word):
    if re.search(r"(?<![а-яё])[А-ЯЁ]{2,}(?![а-яё])", word):   # ГК РФ 같은 약어 — 표기법 대상이 아니다
        return ""
    return " ".join(_loan1(_strip(w)) for w in re.split(r"[\s\-]+", word) if _strip(w))


def _loan1(w):
    U = _units(w)
    S = []

    def host():
        return S[-1] if S and S[-1][2] == " " else None

    def nxt_kind(j):
        """j 번째 단위 뒤를 본다 — 'V'(모음) · 'VC'(유성 자음) · 'VLC'(무성 자음) · 'END'."""
        while j < len(U) and U[j][0] in ("HARD",):
            j += 1
        if j >= len(U):
            return "END"
        u = U[j]
        if u[0] == "V" or u[0] == "J" and j + 1 < len(U) and U[j + 1][0] == "V":
            return "V"
        if u[0] == "C":
            return "VC" if u[1][0] in VOICED and u[1] != "тч" else "VLC"
        if u[0] == "J":
            return "VC"
        return "END"

    k = 0
    while k < len(U):
        u = U[k]
        prev = U[k - 1] if k else None
        if u[0] == "V":
            after_c = prev is not None and prev[0] == "C"
            if after_c:                                # 앞 자음 처리에서 이미 합쳤다
                k += 1; continue
            S.append(_syl("ㅇ", VSOLO[u[1]])); k += 1; continue
        if u[0] == "J":
            nx = U[k + 1] if k + 1 < len(U) else None
            if nx and nx[0] == "V":                    # й + 모음 → 요·야
                S.append(_syl("ㅇ", VSOLO[nx[1]])); k += 2; continue
            if prev and prev[0] == "V" and prev[1] in "иы":   # -ий·-ый → 이(유리·벨리)
                k += 1; continue
            S.append(_syl("ㅇ", "ㅣ")); k += 1; continue
        if u[0] in ("SOFT", "HARD"):
            k += 1; continue
        c = u[1]
        nx = U[k + 1] if k + 1 < len(U) else None
        first = not S
        # 모음 앞
        if nx and nx[0] == "V":
            m = VAFTER[nx[1]]
            ini = C_MOD[c]
            if c in "шщ":
                m = SHY.get(m, m)
            if ini in ("ㅈ", "ㅊ"):
                m = DEY.get(m, m)
            if c == "л" and not first and host():      # 제5항 어중 모음 앞 l → ㄹㄹ
                host()[2] = "ㄹ"
            S.append(_syl(ini, m)); k += 2; continue
        # ь 앞(제9항)
        if nx and nx[0] == "SOFT":
            after = nxt_kind(k + 2)
            if c in "лмн" and after in ("VC", "VLC", "END"):
                if c == "л" and first:                 # 제6항 어두 자음 앞 ль → 리
                    S.append(_syl("ㄹ", "ㅣ")); k += 2; continue
                U[k + 1] = ("HARD",)                   # ь 를 적지 않는다 — 아래 자음 앞·어말 처리로
                nx = U[k + 1]
            else:
                if c == "л" and not first and host():
                    host()[2] = "ㄹ"
                m = "ㅣ"
                S.append(_syl(C_MOD[c], m)); k += 2; continue
        # 자음 앞·어말
        kind = nxt_kind(k + 1)
        if kind == "V":                               # ъ 뒤 모음 — 미규정, 자음 앞처럼
            kind = "VC"
        h = host()
        if c in BEFORE_VL and kind == "VLC" and h:
            h[2] = BEFORE_VL[c]; k += 1; continue
        if c == "л":
            if h:
                h[2] = "ㄹ"
            else:
                S.append(_syl("ㄹ", "ㅡ"))
            k += 1; continue
        if c == "н":
            if h:
                h[2] = "ㄴ"
            else:
                S.append(_syl("ㄴ", "ㅡ"))
            k += 1; continue
        if c == "м":
            nxu = U[k + 1] if k + 1 < len(U) else None
            if not h or kind != "END" and (first or (nxu and nxu[0] == "C" and nxu[1] == "л")):
                S.append(_syl("ㅁ", "ㅡ"))            # 제6항 어두 므 · 믈랴(제믈랴)
            else:
                h[2] = "ㅁ"
            k += 1; continue
        voiced_or_end = 0 if kind == "VC" else 1
        S.extend(_hangul(SYL[c][voiced_or_end]))
        k += 1
    out = _render(S)
    if re.search(r"(град|город)$", w) and out.endswith("트"):   # 제3항
        out = out[:-1] + "드"
    return out
