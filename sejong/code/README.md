# 세종표기 엔진(판 2)

「세종의 글자로 보는 외래어 표기」 판 2의 표기를 내는 파이썬 모듈이다. 표준 라이브러리만 쓴다(파이썬 3.10 이상).
배정 값은 `../data/mapping.csv` 에서 읽고, 대응표만으로 정해지지 않는 규칙은 `../data/rules.md` 에 적었다.

```python
import sys; sys.path.insert(0, "sejong/code")
from lang import es_hangul, ru_hangul, zh_hangul, zh_ipa
es_hangul.render("ˈxweθ", layer=2)      # 2층(옛한글) — HTML 조각
es_hangul.render("ˈxweθ", layer=1)      # 1층(현대 한글 근사)
es_hangul.loan("juez")                  # 0층(외래어 표기법)
zh_hangul.sejong(zh_ipa.to_ipa("fa3 yuan4"))
```

라이선스: MIT(`LICENSE`). 데이터(`../data/`)는 CC BY 4.0.
