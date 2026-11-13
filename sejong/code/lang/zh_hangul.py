"""중국어 한글 표기 — 「세종의 글자로 보는 외래어 표기」 판 3.

loan(pinyin): 숫자 병음 → 국립국어원 「외래어 표기법」 표 5(중국어의 발음 부호와 한글 대조표) + 제3장 제7절(0층).
sejong(ipa, layer=2, tone=None): zh_ipa.to_ipa() 형식 IPA → 2층(옛한글) 표기. layer=1 은 현대 한글 근사(성조 없음).
  성모는 ../data/mapping.csv, 운모는 아래 FIN 표. 성조는 방점(1성 1점 · 2성 2점 · 3성 무점 · 4성 1점 · 경성 무점,
  3성 + 3성은 앞 글자 2점). tone 인자의 다른 변형은 지표 비교용이다(../data/rules.md 3-3).
tone_side(ipa): 표의 「성조」 칸 — 음절마다 사전형 성조 번호. 2층 문자열의 일부가 아니다.
"""
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import hangul_core as HC  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import zh_ipa  # noqa: E402

# ── 0층: 외래어 표기법 표 5 ──
L_INIT = {"b": "ㅂ", "p": "ㅍ", "m": "ㅁ", "f": "ㅍ", "d": "ㄷ", "t": "ㅌ", "n": "ㄴ", "l": "ㄹ", "g": "ㄱ", "k": "ㅋ", "h": "ㅎ",
          "j": "ㅈ", "q": "ㅊ", "x": "ㅅ", "zh": "ㅈ", "ch": "ㅊ", "sh": "ㅅ", "r": "ㄹ", "z": "ㅉ", "c": "ㅊ", "s": "ㅆ"}
L_APICAL = {"zhi": "즈", "chi": "츠", "shi": "스", "ri": "르", "zi": "쯔", "ci": "츠", "si": "쓰"}   # [ ] 단독 표기
# 운모 → 한글(표의 단독 표기). 자음이 앞설 때 ( ) 표기가 따로 있는 것은 L_FIN_C.
L_FIN = {"a": "아", "o": "오", "e": "어", "ê": "에", "i": "이", "u": "우", "ü": "위",
         "ai": "아이", "ei": "에이", "ao": "아오", "ou": "어우", "an": "안", "en": "언", "ang": "앙", "eng": "엉", "er": "얼",
         "ia": "야", "io": "요", "ie": "예", "iai": "야이", "iao": "야오", "iu": "유", "ian": "옌", "in": "인", "iang": "양", "ing": "잉",
         "ua": "와", "uo": "워", "uai": "와이", "ui": "웨이", "uan": "완", "un": "원", "uang": "왕", "ong": "웡",
         "üe": "웨", "üan": "위안", "ün": "윈", "iong": "융"}
L_FIN_C = {"ui": "우이", "un": "운", "ong": "웅"}
YW = dict(zh_ipa.YW, yai="iai", yo="io")   # 표 5 의 yai·yo 는 zh_ipa 에 없다
TONE_RE = re.compile(r"([a-zü:v]+)([1-5])$")


def _parts(syl):
    s = syl.lower().replace("u:", "ü").replace("v", "ü")
    m = TONE_RE.match(s)
    if not m:
        raise ValueError(syl)
    body = m.group(1)
    if body in YW:
        f = YW[body]
        return "", ("ong" if f == "ueng" else f), body
    ini = next((i for i in ("zh", "ch", "sh") if body.startswith(i)), None) or (body[0] if body[0] in L_INIT else "")
    fin = body[len(ini):]
    if ini in ("j", "q", "x") and fin.startswith("u"):
        fin = "ü" + fin[1:]
    if fin == "ueng":
        fin = "ong"
    return ini, fin, body


def _decomp(h):
    """완성형 음절 하나 → (초, 중, 종) 현대 자모."""
    k = ord(h) - 0xAC00
    return HC.MOD_I[k // 588], HC.MOD_M[(k % 588) // 28], HC.MOD_F[k % 28].strip()


DEY = {"ㅑ": "ㅏ", "ㅖ": "ㅔ", "ㅛ": "ㅗ", "ㅠ": "ㅜ"}


def loan_syllable(syl):
    ini, fin, body = _parts(syl)
    if body in L_APICAL:
        return L_APICAL[body]
    if ini == "" and body in YW:
        h = L_FIN[fin]
        return h
    h = (L_FIN_C.get(fin) if ini else None) or L_FIN[fin]
    first, rest = h[0], h[1:]
    _, m, f = _decomp(first)
    i = L_INIT[ini] if ini else "ㅇ"
    if i in ("ㅈ", "ㅉ", "ㅊ") and m in DEY:          # 제7절 제2항
        m = DEY[m]
    return HC.compose(i, m, f) + rest


def loan(pinyin):
    """'fa3lü4' → '파뤼'. 공백은 낱말 경계로 둔다."""
    out = []
    for w in str(pinyin).split():
        out.append("".join(loan_syllable(p) for p in re.findall(r"[a-zA-Zü:]+[1-5]", w)))
    return " ".join(x for x in out if x)


# ── 2층·1층: 세종의 글자로 ──
INITS = sorted(["p", "pʰ", "m", "f", "t", "tʰ", "n", "l", "k", "kʰ", "x", "tɕ", "tɕʰ", "ɕ", "tʂ", "tʂʰ", "ʂ", "ʐ", "ts", "tsʰ", "s"],
               key=len, reverse=True)
# 운모 IPA → (중성, 종성, 덧붙는 글자). 덧붙는 글자는 판 1 스페인어 엔진처럼 보통 크기로 붙인다(뒤 활음).
FIN = {"a": ("ㅏ", "", ""), "o": ("ㅗ", "", ""), "wo": ("ㅝ", "", ""), "ɤ": ("ㅓ", "", ""), "ɛ": ("ㅔ", "", ""),
       "ɚ": ("ㅓ", "ㄹ", ""), "i": ("ㅣ", "", ""), "u": ("ㅜ", "", ""), "y": ("ㅟ", "", ""), "ɹ̩": ("ㅡ", "", ""), "ɻ̩": ("ㅡ", "", ""),
       "ai": ("ㅏ", "", "이"), "ei": ("ㅔ", "", "이"), "au": ("ㅏ", "", "오"), "ou": ("ㅓ", "", "우"),
       "an": ("ㅏ", "ㄴ", ""), "ən": ("ㅓ", "ㄴ", ""), "aŋ": ("ㅏ", "ㅇ", ""), "əŋ": ("ㅓ", "ㅇ", ""), "ʊŋ": ("ㅜ", "ㅇ", ""),
       "ja": ("ㅑ", "", ""), "jɛ": ("ㅖ", "", ""), "jau": ("ㅑ", "", "오"), "jou": ("ㅠ", "", ""), "jɛn": ("ㅖ", "ㄴ", ""),
       "in": ("ㅣ", "ㄴ", ""), "jaŋ": ("ㅑ", "ㅇ", ""), "iŋ": ("ㅣ", "ㅇ", ""), "jʊŋ": ("ㅠ", "ㅇ", ""),
       "wa": ("ㅘ", "", ""), "wai": ("ㅘ", "", "이"), "wei": ("ㅞ", "", "이"), "wan": ("ㅘ", "ㄴ", ""), "wən": ("ㅝ", "ㄴ", ""),
       "waŋ": ("ㅘ", "ㅇ", ""), "wəŋ": ("ㅝ", "ㅇ", ""), "ɥɛ": ("ㅞ", "", ""), "ɥɛn": ("ㅞ", "ㄴ", ""), "yn": ("ㅟ", "ㄴ", ""),
       "ɻ": ("ㅡ", "", "")}
TONES = {"˥": "1", "˧˥": "2", "˨˩˦": "3", "˥˩": "4", "": "5"}
DOT = {"1": HC.DOT1, "2": HC.DOT2, "3": "", "4": HC.DOT1, "5": ""}
# 성조 표기 변형 — 기본은 Zb(조치형). 나머지는 지표 비교용. 값 = (방점 표, 3성+3성 변조 여부, 음절 끝 작은 낱자, 음절 끝 태그)
TONE_DEFAULT = "Zb"
TONE_VARIANTS = {
    "Za": ({"1": "", "2": "", "3": HC.DOT2, "4": HC.DOT1, "5": ""}, False, {}, {}),      # 조류형(비교용)
    "Zb": (DOT, True, {}, {}),                                                            # 조치형(판 2)
    "Zc": (DOT, True, {"4": "ㆆ"}, {}),                                                   # Zb + 4성에 작은 ㆆ
    "Zb4": (DOT, True, {}, {"4": "[4]"}),                                                 # Zb + 4성 뒤 [4]
    "Zn": ({}, False, {}, {"1": "[1]", "2": "[2]", "3": "[3]", "4": "[4]", "5": "[0]"}),  # 방점 없이 번호(사전형)
}
_TAB = HC.register_cache({})


def _inits(layer):
    if layer not in _TAB:
        G = HC.Glyphs("zh", layer)
        _TAB[layer] = {c: G.get(c) or G.get(c, "어두") for c in INITS}
    return _TAB[layer]


def _split(syl):
    m = re.match(r"^(.*?)([˥˦˧˨˩]*)$", syl)
    body, tone = m.group(1), m.group(2)
    ini = next((i for i in INITS if body.startswith(i)), "")
    return ini, body[len(ini):], TONES.get(tone, "5")


def sejong(ipa, layer=2, tone=None):
    """'fa˨˩˦.ly˥˩' → '파뤼〮'(2층, 방점은 음절 뒤 결합 부호로 저장 — 표시는 글꼴이 왼쪽에).
    음절 하나의 순서: 초 + 중 + 종 + 방점 + 덧붙는 글자 + (작은 낱자) + (태그)."""
    I = _inits(layer)
    dots, sandhi, tailc, tag = TONE_VARIANTS[tone or TONE_DEFAULT]
    words = []
    for w in str(ipa).split():
        sy = [_split(s) for s in w.split(".") if s]
        tones = [t for _, _, t in sy]
        marks = list(tones)
        if sandhi:
            for k in range(len(marks) - 1):         # 3성+3성 → 앞 글자 2점(표층 값)
                if marks[k] == "3" and marks[k + 1] == "3":
                    marks[k] = "2"
        out = []
        for (ini, fin, _), t0, t in zip(sy, tones, marks):
            m, f, add = FIN[fin]
            i = I[ini] if ini else "ㅇ"
            body = HC.compose(i, m, f)
            if layer == 2:
                body += dots.get(t, "")
            body += HC.glide(add)
            if layer == 2:
                if tailc.get(t0):
                    body += f"<small>{tailc[t0]}</small>"
                body += tag.get(t0, "")
            out.append(body)
        words.append("".join(out))
    return " ".join(words)


def tone_side(ipa):
    """옆 칸 — 음절마다 사전형 성조 번호(1~4, 경성 0). 'fa˨˩˦.ly˥˩' → '3 · 4'. 2층은 1성과 4성이 같은 점이라 이 칸과 병음이 가른다."""
    out = []
    for w in str(ipa).split():
        for syl in w.split("."):
            if syl:
                t = _split(syl)[2]
                out.append("0" if t == "5" else t)
    return " · ".join(out)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for py in ("fa3lü4", "fa3yuan4", "zheng4ju4", "si1fa3", "shang4su4", "gui4", "zhong1guo2", "jia1", "jie2", "xiong1", "fa3guan1"):
        ipa = zh_ipa.to_ipa(py)
        print(py, ipa, loan(py), sejong(ipa), sejong(ipa, 1))
