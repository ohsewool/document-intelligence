"""샘플 PDF를 한 곳에서만 가져온다.

`tests/fixtures/`는 gitignore돼 있다 - 2.2MB짜리 논문을 저장소에 넣지 않는다.
그래서 각 모듈이 필요할 때 내려받는데, 그 로직이 `test_pdfplumber_adapter.py`
안에만 있었다.

교차 검증 모듈을 추가하고 나서야 문제가 드러났다. pytest는 파일을 알파벳 순으로
도는데 `test_cross_parser_agreement`가 `test_pdfplumber_adapter`보다 앞이라,
**CI에서는 파일이 아직 없어 새 테스트 10개가 조용히 skip됐다.** 로컬에서는 이미
받아둔 파일이 있어 전부 돌았고, 그래서 로컬만 보면 알 수 없었다.

한 모듈이 가진 부수효과에 다른 모듈이 기대는 구조였다. 여기로 옮기면 누가 먼저
돌든 상관이 없다.

받지 못하면 skip한다. 네트워크가 없다는 것과 코드가 틀렸다는 것은 다르고,
`-rs`로 도는 CI는 무엇이 왜 skip됐는지 이름으로 말한다.
"""

import urllib.error
import urllib.request
from pathlib import Path

import pytest

# arXiv:1706.03762. 저자들이 바로 이런 재사용을 위해 배포한 것이다.
PDF_URL = "https://arxiv.org/pdf/1706.03762v7"
CACHE = Path(__file__).parent / "fixtures" / "sample.pdf"


@pytest.fixture(scope="session")
def sample_pdf():
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
