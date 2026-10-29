"""세종표기 공용 엔진 — 언어별 모듈(lang/{es,ru,zh}_hangul.py)이 함께 쓰는 부분.

- 배정 값은 대응표 하나(../data/mapping.csv)에서 읽는다. 공개 표와 엔진이 같은 원천이다.
  환경 변수 SEJONG_MAPPING 으로 다른 대응표를 고를 수 있다.
- 층: 2 = 옛한글(첫가끝 조합), 1 = 현대 한글 근사.
- 저장 규약(KS X 1026-1 5.2·5.3): 현대 자모만으로 된 음절은 완성형, 옛 자모가 든 음절만 첫가끝.
- 지표의 공통 계산도 여기 둔다.

「세종의 글자로 보는 외래어 표기」 판 2(2026. 10. 28.). MIT License(LICENSE).
"""
import csv, os, pathlib, re, unicodedata

MAPPING = pathlib.Path(os.environ.get("SEJONG_MAPPING") or (pathlib.Path(__file__).resolve().parents[1] / "data" / "mapping.csv"))

MOD_I = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
MOD_M = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
MOD_F = " ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
CJ_I = {c: chr(0x1100 + i) for i, c in enumerate(MOD_I)}
CJ_M = {c: chr(0x1161 + i) for i, c in enumerate(MOD_M)}
CJ_F = {"ㄱ": "ᆨ", "ㄴ": "ᆫ", "ㄹ": "ᆯ", "ㅁ": "ᆷ", "ㅂ": "ᆸ", "ㅅ": "ᆺ", "ㅇ": "ᆼ"}
FILLER_V = "ᅠ"                       # 중성 채움 — 초성 낱자(KS X 1026-1 5.1)
DOT1, DOT2 = "〮", "〯"           # 방점
COMPAT = {"ᄫ": "ㅸ", "ᅗ": "ㆄ", "ᅀ": "ㅿ", "ᅌ": "ㆁ", "ᅙ": "ㆆ"}   # 호환 자모가 있는 옛 초성


def load_mapping(path=MAPPING):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    return rows


class Glyphs:
    """lang 행이 공통(*) 행보다 앞선다. key = (ipa, context)."""

    def __init__(self, lang, layer=2, rows=None):
        self.lang, self.layer = lang, layer
        self.t = {}
        for r in rows or load_mapping():
            if r["lang"] == "*":
                self.t.setdefault((r["ipa"], r["context"]), r)
        for r in rows or load_mapping():
            if r["lang"] == lang:
                self.t[(r["ipa"], r["context"])] = r

    def row(self, ipa, context="*"):
        return self.t.get((ipa, context)) or self.t.get((ipa, "*"))

    def get(self, ipa, context="*", default=None):
        r = self.row(ipa, context)
        if not r:
            return default
        return r["l2"] if self.layer == 2 else r["l1"]


def is_modern(c):
    return c in MOD_I or c in MOD_M or c in MOD_F.strip()


def compose(i, m, f=""):
    """초·중·종(현대 자모 또는 첫가끝 초성) → 음절. 현대 자모만이면 완성형."""
    if i in MOD_I and m in MOD_M and (not f or f in MOD_F):
        return chr(0xAC00 + (MOD_I.index(i) * 21 + MOD_M.index(m)) * 28 + (MOD_F.index(f) if f else 0))
    L = CJ_I.get(i, i)
    return L + CJ_M.get(m, m) + (CJ_F[f] if f else "")


def small(c):
    """받침으로 나지 않는 자음 낱자. 현대 자모·호환 자모가 있으면 그것, 없으면 초성 + 중성 채움."""
    if c in MOD_I:
        return c
    if c in COMPAT:
        return COMPAT[c]
    return c + FILLER_V


# ── 지표용 평문화 ──
TAG_B = re.compile(r"<b>(.*?)</b>")
TAG_S = re.compile(r"<small>(.*?)</small>")


def flat(html):
    """굵게 → 그 음절 앞 ˈ, 작은 글자 → ₍…₎, NFC."""
    s = TAG_B.sub(lambda m: "ˈ" + m.group(1), html)
    s = TAG_S.sub(lambda m: "₍" + m.group(1) + "₎", s)
    s = re.sub(r"<[^>]+>", "", s)
    return unicodedata.normalize("NFC", s)


def count_syllables(html):
    """M1 표기 음절 수: 작은 글자 밖의 완성형 + 첫가끝(L V) 음절."""
    s = TAG_S.sub("", html)
    s = re.sub(r"<[^>]+>", "", s)
    s = unicodedata.normalize("NFC", s)
    n = sum(1 for c in s if 0xAC00 <= ord(c) <= 0xD7A3)
    n += len(re.findall(r"[ᄀ-ᅟꥠ-ꥼ][ᅠ-ᆧힰ-ퟆ]", s))
    return n
