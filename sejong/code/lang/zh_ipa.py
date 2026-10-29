"""중국어 숫자 병음(CC-CEDICT 형식) → 음소 IPA — 세종표기 지표 사전 등록(2026-10-28)용으로 얼린 규칙.

broad 표기: 성모·운모를 음소로, 성조는 사전형(기저 성조)을 Chao 성조 글자로 음절 끝에 붙인다.
3성 변조·一/不 변조는 IPA 에 적지 않는다(표층 값은 세종표기 층이 범례 규칙으로 처리).
음절 사이는 "." 로 가른다. 경성(5)은 성조 글자 없음.
"""
import re

INIT = {"b": "p", "p": "pʰ", "m": "m", "f": "f", "d": "t", "t": "tʰ", "n": "n", "l": "l",
        "g": "k", "k": "kʰ", "h": "x", "j": "tɕ", "q": "tɕʰ", "x": "ɕ",
        "zh": "tʂ", "ch": "tʂʰ", "sh": "ʂ", "r": "ʐ", "z": "ts", "c": "tsʰ", "s": "s"}
FINAL = {"a": "a", "o": "o", "e": "ɤ", "ê": "ɛ", "er": "ɚ", "i": "i", "u": "u", "ü": "y",
         "ai": "ai", "ei": "ei", "ao": "au", "ou": "ou", "an": "an", "en": "ən", "ang": "aŋ", "eng": "əŋ", "ong": "ʊŋ",
         "ia": "ja", "ie": "jɛ", "iao": "jau", "iu": "jou", "ian": "jɛn", "in": "in", "iang": "jaŋ", "ing": "iŋ", "iong": "jʊŋ",
         "ua": "wa", "uo": "wo", "uai": "wai", "ui": "wei", "uan": "wan", "un": "wən", "uang": "waŋ", "ueng": "wəŋ",
         "üe": "ɥɛ", "üan": "ɥɛn", "ün": "yn"}
# y·w 로 시작하는 표기 → 운모
YW = {"yi": "i", "ya": "ia", "ye": "ie", "yao": "iao", "you": "iu", "yan": "ian", "yin": "in", "yang": "iang",
      "ying": "ing", "yong": "iong", "yu": "ü", "yue": "üe", "yuan": "üan", "yun": "ün",
      "wu": "u", "wa": "ua", "wo": "uo", "wai": "uai", "wei": "ui", "wan": "uan", "wen": "un", "wang": "uang", "weng": "ueng"}
TONE = {"1": "˥", "2": "˧˥", "3": "˨˩˦", "4": "˥˩", "5": ""}
SYL = re.compile(r"([a-zü:v]+)([1-5])$")


def syllable(s):
    """'fa3' → 'fa˨˩˦'. 모르는 꼴이면 ValueError."""
    s = s.lower().replace("u:", "ü").replace("v", "ü")
    m = SYL.match(s)
    if not m:
        raise ValueError(s)
    body, tone = m.groups()
    if body == "r":                       # 儿化 음절(r5)
        return "ɻ"
    if body in YW:
        ini, fin = "", YW[body]
    else:
        ini = next((i for i in ("zh", "ch", "sh") if body.startswith(i)), None) or (body[0] if body[0] in INIT else "")
        fin = body[len(ini):]
        if ini in ("j", "q", "x") and fin.startswith("u"):
            fin = "ü" + fin[1:]
    if fin == "i" and ini in ("z", "c", "s"):
        v = "ɹ̩"
    elif fin == "i" and ini in ("zh", "ch", "sh", "r"):
        v = "ɻ̩"
    elif fin == "o" and ini in ("b", "p", "m", "f"):
        v = "wo"
    elif fin in FINAL:
        v = FINAL[fin]
    else:
        raise ValueError(s)
    return INIT.get(ini, "") + v + TONE[tone]


def to_ipa(pinyin):
    """'fa3lü4' 또는 'fa3 lü4' → 'fa˨˩˦.ly˥˩'"""
    parts = re.findall(r"[a-zA-Zü:]+[1-5]", pinyin)
    return ".".join(syllable(p) for p in parts)


def n_syllables(pinyin):
    return len(re.findall(r"[a-zA-Zü:]+[1-5]", pinyin))


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for t in ("fa3lü4", "zheng4ju4", "yin2hang2", "si1fa3", "shi4", "ri4", "zi4", "quan2", "nü3", "lüe4", "bo2", "yue1", "er2", "de5"):
        print(t, to_ipa(t))
