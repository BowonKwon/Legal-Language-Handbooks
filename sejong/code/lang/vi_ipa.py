"""베트남어 표제어 IPA(위키낱말사전 하노이 값) → 정규 IPA.

원천 IPA 는 위키낱말사전의 모듈이 철자에서 만든 하노이 값이고 성조 · 발성 표기 꼴이 섞여 있다.
이 모듈은 분절음은 그대로 두고 성조 표기만 여섯 성조로 접는다. 음절 사이는 "." 로 가르고 성조 글자는 음절 끝에 붙인다.
규칙은 ../data/rules.md 4-1 과 같다. 지표의 표본을 이 규칙으로 만들었으므로 규칙을 고치면 표본도 다시 만들어야 한다.
"""
import re
import unicodedata

TONE_CHARS = "˥˦˧˨˩"
NAME = {"˧˧": "ngang", "˨˩": "huyền", "˧˥": "sắc", "˧˩˧": "hỏi", "˧ˀ˥": "ngã", "˨˩ˀ": "nặng"}
CANON = {v: k for k, v in NAME.items()}
VOWELS = "aeiouɨəɛɔ"
_SYL = re.compile(r"^(.*?)([" + TONE_CHARS + r"]+)(ʔ?)$")


def syllable(s):
    """원천 음절 하나 → (정규 음절, 성조 이름). 모르는 꼴이면 ValueError."""
    s = unicodedata.normalize("NFD", s)
    m = _SYL.match(s)
    if not m:
        raise ValueError(s)
    body, tone, tail = m.groups()
    body = body.replace("̚", "")
    if body.startswith("ʔ"):                       # 음절 첫 ʔ(en 판 값) — 모음으로 시작하는 음절의 성문 시작
        body = body[1:]
    creaky = "̰" in body
    body = body.replace("̤", "").replace("̰", "").replace("̈", "").replace("ʨ", "tɕ")
    glottal = "ʔ" in body or bool(tail)
    if tone == "˧˧" and not glottal and not creaky:
        name = "ngang"
    elif tone == "˨˩" and not glottal and not creaky:
        name = "huyền"
    elif tone in ("˧˥", "˧˦") and not glottal and not creaky:
        name = "sắc"
    elif tone in ("˧˩˧", "˧˩") and not glottal:
        name = "hỏi"
    elif tone == "˧˥" and "ʔ" in body and not tail:
        k = body.index("ʔ")
        if not (0 < k < len(body) - 1 and body[k - 1] in VOWELS and body[k + 1] == body[k - 1]):
            raise ValueError(s)
        body = body[:k] + body[k + 2:]            # V ʔ V → V
        name = "ngã"
    elif tone in ("˨˩", "˧˨") and glottal:
        body = body.replace("ʔ", "")
        name = "nặng"
    else:
        raise ValueError(s)
    if "ʔ" in body or not body:
        raise ValueError(s)
    return unicodedata.normalize("NFC", body) + CANON[name], name


def to_canon(ipa):
    """'/twa̤ː˨˩ aːn˧˥/' → 'twaː˨˩.aːn˧˥'"""
    parts = str(ipa).strip().strip("/").split()
    return ".".join(syllable(p)[0] for p in parts)


def tones(ipa):
    return [syllable(p)[1] for p in str(ipa).strip().strip("/").split()]


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for t in ("/twa̤ː˨˩ aːn˧˥/", "/lwə̰ʔt˨˩/", "/fa̰ːʔm˨˩/", "/xwa̰ːn˧˩˧/", "/ɓa̰ːw˧˩˧ laʔajŋ˧˥/", "/kwiət̚˧˦ ʔɗïŋ˧˨ʔ/", "/tʰəm˧˩/"):
        print(t, to_canon(t), tones(t))
