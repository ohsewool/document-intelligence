"""샘플 PDF를 어디서 가져오는가 — **한 곳.**

`conftest.py`가 이미 이 일을 하고 있었고, 그 파일에는 왜 한 곳이어야 하는지도
적혀 있었다.

    한 모듈이 가진 부수효과에 다른 모듈이 기대는 구조였다. 여기로 옮기면
    누가 먼저 돌든 상관이 없다.

그런데 `test_rejections_that_were_never_fired.py`는 그 픽스처를 안 쓰고
**경로를 직접 적고 있었다.** `unittest.TestCase`라 pytest 픽스처를 인자로 받을 수
없어서다. 파일이 없으면 그 검사는 skip이 아니라 `FileNotFoundError`로 죽는다.

    캐시 없음 + 네트워크 없음
        픽스처를 쓰는 32개   → skip
        경로를 직접 쓴 1개   → FileNotFoundError

**규칙을 옮기지 않고 꺼내 놓는다.** pytest 픽스처는 pytest만 쓸 수 있지만 평범한
함수는 누구나 쓴다. `conftest.py`의 픽스처도 이것을 부른다 — 두 벌이 되면 한쪽만
낡는다.
"""

from __future__ import annotations

import os
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# arXiv:1706.03762. 저자들이 바로 이런 재사용을 위해 배포한 것이다.
#
# 주소를 환경변수로 덮을 수 있게 둔다. **대조를 위해서다** — CI가 "샘플 PDF를 못
# 받는 상태"를 한 번 만들어 보고 그때 skip 집합 훅이 실제로 빨간불을 내는지
# 확인한다. 그 확인이 없으면 훅이 죽어도 아무도 모른다.
PDF_URL = os.getenv("SAMPLE_PDF_URL", "").strip() or "https://arxiv.org/pdf/1706.03762v7"
CACHE = Path(__file__).parent / "fixtures" / "sample.pdf"


def ensure_sample_pdf() -> Path:
    """캐시된 샘플 PDF. 없으면 한 번 받고, 못 받으면 **skip한다.**

    네트워크가 없다는 것과 코드가 틀렸다는 것은 다르다. 다만 *조용히* 다르면
    안 된다 — 무엇이 왜 빠졌는지는 `conftest.py`의 세션 훅이 지킨다.
    """
    if CACHE.exists():
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    try:
        request = urllib.request.Request(
            PDF_URL, headers={"User-Agent": "document-intelligence"})
        with urllib.request.urlopen(request, timeout=60) as response:
            CACHE.write_bytes(response.read())
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        pytest.skip(f"샘플 PDF를 받지 못했다: {error}")
    return CACHE
