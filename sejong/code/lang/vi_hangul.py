"""베트남어 한글 표기 — 「세종의 글자로 보는 외래어 표기」 판 3.

loan(word): 꾸옥응으 철자 → 국립국어원 「외래어 표기법」 표 16(베트남어 자모와 한글 대조표) + 제3장 제18절 제1~4항(0층).
  성조는 적지 않는다. 규범에 실린 보기 113개를 모두 규범대로 적는 것을 시험으로 확인했다.
  규범에 정함이 없는 nh + ư 는 「니」 + 「으」로 푼다.
sejong(ipa, layer=2, tone=None): 하노이 IPA(vi_ipa.to_canon() 의 정규 꼴 또는 원천 꼴) → 2층(옛한글) 표기. layer=1 은 현대 한글 근사(성조 없음).
  첫소리 · 모음은 ../data/mapping.csv. 받침은 ㅁ ㄴ ㅇ ㅂ ㅅ ㄱ. 뒤 활음과 이중모음 둘째 요소는 덧글자(작은 글자)이고
  그 뒤 끝소리는 덧글자의 받침이다. 성조는 방점과 음절 끝 작은 ㆆ(ngang 1점 · huyền 무점 · sắc 2점 · hỏi 1점 + ㆆ ·
  ngã 2점 + ㆆ · nặng 무점 + ㆆ, 막는 끝소리 음절에서는 ㆆ 을 쓰지 않는다). 음절 사이는 띄운다.
  tone 인자의 다른 변형과 kh 인자는 지표 비교용이다(../data/rules.md 4-5).
tone_side(ipa): 표의 「성조 · 길이」 칸 — 음절마다 성조 번호, 긴 a · ơ 음절은 ':'. 2층 문자열의 일부가 아니다.
"""
import pathlib
import re
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import hangul_core as HC  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import vi_ipa  # noqa: E402

# ══ 0층: 외래어 표기법 표 16 + 제18절 ══
L_ONSET = {"b": "ㅂ", "c": "ㄲ", "k": "ㄲ", "q": "ㄲ", "ch": "ㅉ", "d": "ㅈ", "gi": "ㅈ", "đ": "ㄷ", "g": "ㄱ", "gh": "ㄱ", "h": "ㅎ",
           "kh": "ㅋ", "l": "ㄹ", "m": "ㅁ", "n": "ㄴ", "ng": "응", "ngh": "응", "nh": "니", "p": "ㅃ", "ph": "ㅍ", "r": "ㄹ",
           "s": "ㅅ", "t": "ㄸ", "th": "ㅌ", "tr": "ㅉ", "v": "ㅂ", "x": "ㅆ"}
L_CODA = {"c": "ㄱ", "k": "ㄱ", "ch": "ㄱ", "m": "ㅁ", "n": "ㄴ", "ng": "ㅇ", "nh": "ㄴ", "p": "ㅂ", "t": "ㅅ"}
L_VOWEL = {"a": "ㅏ", "ă": "ㅏ", "â": "ㅓ", "e": "ㅐ", "ê": "ㅔ", "i": "ㅣ", "y": "ㅣ", "o": "ㅗ", "ô": "ㅗ", "ơ": "ㅓ", "u": "ㅜ", "ư": "ㅡ"}
L_Y = {"ㅏ": "ㅑ", "ㅓ": "ㅕ", "ㅐ": "ㅒ", "ㅔ": "ㅖ", "ㅗ": "ㅛ", "ㅜ": "ㅠ", "ㅣ": "ㅣ"}   # ㅡ 는 미규정 — 「니으」로 푼다
_ON = sorted(L_ONSET, key=len, reverse=True)
_CO = sorted(L_CODA, key=len, reverse=True)
_VL = "aăâeêiyoôơuư"
_TONE_MARKS = {"̀", "́", "̉", "̃", "̣"}


def _strip_tone(w):
    """성조 부호 다섯만 뗀다. 모음을 바꾸는 부호(ă â ê ô ơ ư)와 đ 는 남긴다."""
    s = unicodedata.normalize("NFD", w.lower().replace("Đ", "đ"))
    return unicodedata.normalize("NFC", "".join(c for c in s if c not in _TONE_MARKS))


def _syl(i, m, f=""):
    return [i, m, f]


def _vowel_units(v, after_q):
    """모음 글자 묶음 → 중성 목록. 표 16 의 이중모음 칸(ia 이어 · ua 우어 · ưa 으어)과 제3항(y + 모음)을 적용한다."""
    out, i = [], 0
    while i < len(v):
        c, nx = v[i], v[i + 1:i + 2]
        if c == "y" and nx:                               # 제3항: y 는 뒤따르는 모음과 한 음절(yên 옌)
            out.append(L_Y.get(L_VOWEL[nx], L_VOWEL[nx])); i += 2; continue
        if c in "iuư" and nx == "a" and i + 2 == len(v) and not (c == "u" and after_q):
            out += [L_VOWEL[c], "ㅓ"]; i += 2; continue   # ia 이어 · ua 우어 · ưa 으어
        out.append(L_VOWEL[c]); i += 1
    return out


def _starts_syllable(s):
    on = next((o for o in _ON if s.startswith(o)), "")
    return bool(on) and len(s) > len(on) and s[len(on)] in _VL


def _loan_word(s):
    """띄어 쓴 덩어리 하나 → (음절 목록 — 음절마다 초 · 중 · 종, 첫 글자가 l 인가). 보통은 한 음절이고, 표기법 보기의
    Pleiku 처럼 붙여 쓴 여러 음절·자음 + l 무리도 받는다. 모르는 꼴이면 ValueError."""
    S, pos, l_initial = [], 0, s.startswith("l")
    while pos < len(s):
        # 자음 + l 무리(klông · Pleiku — 표기법 보기에만 나온다): 「으」 음절에 ㄹ 받침
        if len(s) - pos > 2 and s[pos] in "kpb" and s[pos + 1] == "l":
            S.append(_syl(L_ONSET[s[pos]], "ㅡ", "ㄹ"))
            pos += 1
        on = next((o for o in _ON if s.startswith(o, pos)), "")
        pos += len(on)
        if on == "q" and s.startswith("u", pos):          # qu
            on, pos = "qu", pos + 1
        k = pos
        while k < len(s) and s[k] in _VL:
            k += 1
        v = s[pos:k]
        if on == "gi" and not v:                          # gì·gìn: i 가 모음
            v = "i"
        rest = s[k:]
        if rest in L_CODA or not rest:
            coda, pos = rest, len(s)
        else:                                             # 붙여 쓴 다음 음절이 있다 — 다음 음절의 첫소리를 먼저 채운다
            coda = next((c for c in [""] + sorted(L_CODA, key=len) if rest.startswith(c) and _starts_syllable(rest[len(c):])), None)
            if coda is None:
                raise ValueError(s)
            pos = k + len(coda)
        if not v:
            raise ValueError(s)
        if on == "qu":
            if v[0] in "aă":                              # 제2항: qu + a → 꽈
                S.append(_syl("ㄲ", "ㅘ")); units = _vowel_units(v, True)[1:]
            else:
                S.append(_syl("ㄲ", "ㅜ")); units = _vowel_units(v, True)
            S += [_syl("ㅇ", u) for u in units]
        else:
            units = _vowel_units(v, False)
            if on in ("ng", "ngh"):
                S.append(_syl("ㅇ", "ㅡ", "ㅇ")); S.append(_syl("ㅇ", units[0]))
            elif on == "nh":                              # 제1항: nh 는 이어지는 모음과 한 음절
                if units[0] in L_Y:
                    S.append(_syl("ㄴ", L_Y[units[0]]))
                else:                                     # 미규정(nh + ư): 「니」 + 「으」
                    S.append(_syl("ㄴ", "ㅣ")); S.append(_syl("ㅇ", units[0]))
            else:
                S.append(_syl(L_ONSET[on] if on else "ㅇ", units[0]))
            S += [_syl("ㅇ", u) for u in units[1:]]
        if coda:
            if coda == "nh" and v[-1] == "a":             # 제1항: a + nh → 아인
                S.append(_syl("ㅇ", "ㅣ", "ㄴ"))
            else:
                S[-1][2] = L_CODA[coda]
    return S, l_initial


def loan(word, names=False):
    """'Hạ Long' → '할롱'. 음절을 붙여 적는다. 제4항: 어중의 l 이 모음 앞에 오면 ㄹㄹ(앞 음절에 받침이 없을 때 ㄹ 받침을 더한다).
    names=True 면 성과 이름 사이로 보아 제4항을 적용하지 않는다(Thế Lữ 테르)."""
    S = []
    for w in re.findall(r"[^\W\d_]+", unicodedata.normalize("NFC", str(word))):
        blocks, l_initial = _loan_word(_strip_tone(w))
        if l_initial and S and not names and not S[-1][2]:
            S[-1][2] = "ㄹ"
        S += blocks
    return "".join(HC.compose(i, m, f) for i, m, f in S)


# ══ 2층·1층: 세종의 글자로 ══
ONSETS = sorted(["ɓ", "ɗ", "t", "tʰ", "k", "x", "ɣ", "h", "m", "n", "ɲ", "ŋ", "f", "v", "s", "z", "l", "tɕ", "p"], key=len, reverse=True)
VOWELS = ["a", "ə", "ɨ", "i", "e", "ɛ", "o", "ɔ", "u"]
CODA = {"m": "ㅁ", "n": "ㄴ", "ŋ": "ㅇ", "p": "ㅂ", "t": "ㅅ", "k": "ㄱ"}
STOPS = ("p", "t", "k")
MED_W = {"ㅏ": "ㅘ", "ㅓ": "ㅝ", "ㅔ": "ㅞ", "ㅐ": "ㅙ", "ㅣ": "ㅟ"}                 # 가운데 w + 모음
PAL = {"ㅏ": "ㅑ", "ㅓ": "ㅕ", "ㅗ": "ㅛ", "ㅜ": "ㅠ", "ㅔ": "ㅖ", "ㅐ": "ㅒ", "ㅣ": "ㅣ"}   # ɲ 뒤 ㅣ계(ㅡ · ㆍ 는 mapping 의 「ɲ 뒤」 행)
GLIDE = {"ə": "ㅓ", "j": "ㅣ", "w": "ㅜ"}                                         # 덧글자의 중성
_RIME = re.compile(r"^(w?)(aː|a|əː|ə|ɨ|i|e|ɛ|o|ɔ|u)(ə?)([jw]?)([mnŋptk]?)$")
_SYL = re.compile(r"^(.*?)([˥˦˧˨˩ˀ]+)$")

D1, D2 = HC.DOT1, HC.DOT2
SMALL_H, SMALL_Q = "ㅎ", "ㆆ"            # 작은 낱자: ㅎ(U+314E) · ㆆ(U+3186)
# 성조 표기 변형 — 기본은 Va. 나머지는 지표 비교용. 값 = (방점, 음절 끝 작은 낱자, 번호 태그)
TONE_VARIANTS = {
    "Va": {"ngang": (D1, "", ""), "huyền": ("", "", ""), "sắc": (D2, "", ""), "hỏi": (D1, SMALL_Q, ""), "ngã": (D2, SMALL_Q, ""), "nặng": ("", SMALL_Q, "")},
    "P1": {"ngang": (D1, "", ""), "huyền": ("", SMALL_H, ""), "sắc": (D2, "", ""), "hỏi": ("", "", ""), "ngã": (D2, SMALL_Q, ""), "nặng": ("", SMALL_Q, "")},
    "Vn": {"ngang": ("", "", "[1]"), "huyền": ("", "", "[2]"), "sắc": ("", "", "[3]"), "hỏi": ("", "", "[4]"), "ngã": ("", "", "[5]"), "nặng": ("", "", "[6]")},
}
TONE_VARIANTS["Va2"] = TONE_VARIANTS["Va"]          # 막는 끝소리 음절에도 ㆆ
TONE_VARIANTS["Vd"] = TONE_VARIANTS["Va"]           # ㆆ 을 핵 덩이의 받침 ᇹ 으로
TONE_VARIANTS["V0"] = {k: (v[0], "", "") for k, v in TONE_VARIANTS["Va"].items()}   # 방점만
TONE_VARIANTS["VnL"] = TONE_VARIANTS["Vn"]          # 번호 + 길이 표지 ':'
TONE_DEFAULT = "Va"                                 # 2층은 한글 자모 · 방점 · 작은 ㆆ 만 쓴다
TONE_NO = {"ngang": 1, "huyền": 2, "sắc": 3, "hỏi": 4, "ngã": 5, "nặng": 6}
KH_VARIANTS = {"Xb": None, "Xa": "ㅋ", "Xe": "ㅎ"}  # x 의 2층 값 — None 이면 대응표(판 3: ᅘ)
_TAB = HC.register_cache({})


def _tables(layer):
    if layer not in _TAB:
        G = HC.Glyphs("vi", layer)
        on = {c: G.get(c) or G.get(c, "음절 첫") or G.get(c, "어두") for c in ONSETS}
        on[""] = "ㅇ"
        vw = {v: G.get(v) for v in VOWELS}
        pal = dict(PAL)
        for v in ("ɨ", "ɔ"):                         # ㅡ · ㆍ 의 ㅣ계(합자해의 합용 중성)
            r = G.row(v, "ɲ 뒤")
            if r and r["context"] == "ɲ 뒤":
                pal[vw[v]] = r["l2"] if layer == 2 else r["l1"]
        if any(x is None for x in list(on.values()) + list(vw.values())):
            raise KeyError("베트남어 행이 대응표에 없다")
        _TAB[layer] = (on, vw, pal)
    return _TAB[layer]


def parse(syl):
    """정규 음절 → dict(onset, w, v, long, second, glide, coda, tone). 모르는 꼴이면 ValueError."""
    m = _SYL.match(syl)
    if not m or m.group(2) not in vi_ipa.NAME:
        raise ValueError(syl)
    body, tone = m.group(1), vi_ipa.NAME[m.group(2)]
    ini = next((c for c in ONSETS if body.startswith(c)), "")
    r = _RIME.match(body[len(ini):])
    if not r:
        raise ValueError(syl)
    w, v, second, gl, coda = r.groups()
    return {"onset": ini, "w": bool(w), "v": v.rstrip("ː"), "long": v.endswith("ː"), "second": second, "glide": gl, "coda": coda, "tone": tone}


def render_syllable(p, layer=2, tone=None, kh="Xb"):
    on, vw, pal = _tables(layer)
    i = on[p["onset"]]
    if p["onset"] == "x" and layer == 2 and KH_VARIANTS[kh]:
        i = KH_VARIANTS[kh]
    m = vw[p["v"]]
    if p["w"]:
        if m not in MED_W:
            raise ValueError("w + " + p["v"])
        m = MED_W[m]
    elif p["onset"] == "ɲ":
        m = pal.get(m, m)
    extras = [GLIDE[x] for x in (p["second"], p["glide"]) if x]
    f = CODA.get(p["coda"], "")
    variant = tone or TONE_DEFAULT
    dot, tailc, tag = TONE_VARIANTS[variant][p["tone"]] if layer == 2 else ("", "", "")
    checked = p["coda"] in STOPS
    if tailc == SMALL_Q and checked and variant in ("Va", "P1", "Vd"):
        tailc = ""                                   # 막는 끝소리 음절에는 ㆆ 을 쓰지 않는다
    nf = "" if extras else f
    if variant == "Vd" and layer == 2 and tailc == SMALL_Q:
        if not nf:
            nf = "ᇹ"                                 # 덩이 받침(비교용 — 이 꼴은 NFC 뒤 잘못된 형식이 된다)
        tailc = ""
    out = HC.compose(i, m, nf) + dot
    if extras:
        blocks = [HC.compose("ㅇ", e) for e in extras[:-1]] + [HC.compose("ㅇ", extras[-1], f)]
        out += HC.glide("".join(blocks))
    if tailc:
        out += f"<small>{tailc}</small>"
    if layer == 2 and variant == "VnL" and p["long"]:
        out += ":"
    return out + tag


def sejong(ipa, layer=2, tone=None, kh="Xb"):
    """'twaː˨˩.aːn˧˥' → '똬 안〯'. 원천 꼴(/…/, 띄어쓰기)이 오면 먼저 정규화한다."""
    s = str(ipa)
    if "/" in s or " " in s.strip() or "ʔ" in s:
        s = vi_ipa.to_canon(s)
    return " ".join(render_syllable(parse(x), layer, tone, kh) for x in s.split(".") if x)


def tone_side(ipa):
    """옆 칸 — 음절마다 성조 번호(1 ngang · 2 huyền · 3 sắc · 4 hỏi · 5 ngã · 6 nặng), 긴 a · ơ 음절은 번호 뒤에 ':'.
    'xwaːn˧˩˧' → '4:' / 'ɓaːw˧˩˧.lajŋ˧ˀ˥' → '4: · 5'. 2층 문자열 밖에 두는 정보다."""
    s = str(ipa)
    if "/" in s or " " in s.strip() or "ʔ" in s:
        s = vi_ipa.to_canon(s)
    out = []
    for x in s.split("."):
        if x:
            pr = parse(x)
            out.append(str(TONE_NO[pr["tone"]]) + (":" if pr["long"] else ""))
    return " · ".join(out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    HC.configure(edition=3)
    for hw, ipa in (("luật", "/lwə̰ʔt˨˩/"), ("pháp", "/faːp˧˥/"), ("phạm", "/fa̰ːʔm˨˩/"), ("khoản", "/xwa̰ːn˧˩˧/"), ("Tòa án", "/twa̤ː˨˩ aːn˧˥/"),
                    ("bảo lãnh", "/ɓa̰ːw˧˩˧ laʔajŋ˧˥/"), ("người", "/ŋɨəj˨˩/"), ("quyết định", "/kwiət̚˧˦ ʔɗïŋ˧˨ʔ/")):
        print(hw, loan(hw), *(sejong(ipa, tone=t) for t in ("Va", "P1", "Vn", "VnL")), sejong(ipa, 1), sep=" | ")
