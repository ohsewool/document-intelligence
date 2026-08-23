"""샘플 PDF를 한 곳에서만 가져오고, **무엇이 건너뛰어지는지 지킨다.**

`tests/fixtures/`는 gitignore돼 있다 - 2.2MB짜리 논문을 저장소에 넣지 않는다.
그래서 각 모듈이 필요할 때 내려받는데, 그 로직이 `test_pdfplumber_adapter.py`
안에만 있었다.

교차 검증 모듈을 추가하고 나서야 문제가 드러났다. pytest는 파일을 알파벳 순으로
도는데 `test_cross_parser_agreement`가 `test_pdfplumber_adapter`보다 앞이라,
**CI에서는 파일이 아직 없어 새 테스트 10개가 조용히 skip됐다.** 로컬에서는 이미
받아둔 파일이 있어 전부 돌았고, 그래서 로컬만 보면 알 수 없었다.

한 모듈이 가진 부수효과에 다른 모듈이 기대는 구조였다. 가져오는 규칙은
`tests/sample_pdf.py`에 있고 누가 먼저 돌든 상관이 없다.

받지 못하면 skip한다. 네트워크가 없다는 것과 코드가 틀렸다는 것은 다르다.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**그런데 그 skip을 아무도 세지 않았다.**

CI에는 `Refuse a silently shrinking suite`라는 단계가 있었다. 이름이 말하는 일을
못 한다. 그것이 보는 것은 `pytest --collect-only`의 **수집 수**이고, 런타임 skip은
수집 수를 바꾸지 않는다. 2026-08-24에 재봤다.

    샘플 PDF를 못 받는 상태
      수집 수  234   ← 관문이 보는 수. 하한 67과 비교해 통과시킨다
      실행     201 passed, **32 skipped**, 1 failed

**서른둘이 조용히 빠져도 그 관문은 아무 말도 안 한다.** 하한선이 67이라는 것도
따로 문제다 — 실제 수집이 234이므로 167개가 사라져도 초록불이다. *하한선은 목록이
줄어드는 것만 보고, 목록이 현실에서 멀어지는 것은 못 본다.*

그래서 여기서 **집합으로** 지킨다. 어느 파일이 몇 개를 건너뛰는가. 정확한 일치라야
늘어나는 것도 고쳐서 줄어드는 것도 걸린다. `rag-profile-selector`가 코퍼스 skip에
대해 쓰는 것과 같은 장치이고, 같은 이유다.

`SAMPLE_PDF_MISSING_OK=1`을 주면 이 훅을 건너뛴다 — 네트워크 없는 곳에서 나머지를
돌려보고 싶을 때가 있고, 그때 이것이 방해가 되면 다음 사람이 훅을 지운다.
"""

import os

import pytest

from sample_pdf import CACHE, PDF_URL, ensure_sample_pdf  # noqa: F401

# 샘플 PDF가 있을 때 기대하는 skip 집합. **비어 있다** — 있으면 전부 돈다.
EXPECTED_SKIPS: dict[str, int] = {}

_skipped: list[tuple[str, str]] = []


@pytest.fixture(scope="session")
def sample_pdf():
    return ensure_sample_pdf()


def pytest_runtest_logreport(report):
    if report.skipped and report.when in ("setup", "call"):
        reason = ""
        if isinstance(report.longrepr, tuple) and len(report.longrepr) == 3:
            reason = report.longrepr[2]
        _skipped.append((report.nodeid.split("::")[0], reason))


def pytest_sessionfinish(session, exitstatus):
    """**돌린 것이 있을 때만 판정한다.**

    세션 훅은 내가 생각하지 않은 모드에서도 돈다 — `--collect-only`, `-k` 선택,
    파일 하나. 판정할 근거가 없는 실행에서 걸리면 그건 검사가 아니라 방해이고,
    다음 사람이 훅을 지운다. `rag-profile-selector`가 같은 훅을 쓰면서 CI에서
    바로 이것에 걸렸고, 그 경위가 그 파일에 적혀 있다.
    """
    if os.getenv("SAMPLE_PDF_MISSING_OK"):
        return
    if getattr(session.config.option, "collectonly", False):
        return
    if getattr(session.config.option, "file_or_dir", None):
        return                      # 일부만 돌렸다 — 집합을 비교할 수 없다
    if getattr(session.config.option, "keyword", None):
        return
    if not getattr(session, "testscollected", 0):
        return
    if session.testsfailed:
        return                      # 이미 빨간불이다. 이유를 하나 더 얹지 않는다

    counted: dict[str, int] = {}
    for path, _reason in _skipped:
        counted[path] = counted.get(path, 0) + 1

    if counted != EXPECTED_SKIPS:
        raise SystemExit(
            "SKIP 집합 검사 실패 —\n"
            "  건너뛴 검사의 집합이 다르다.\n"
            f"    실제: {dict(sorted(counted.items()))}\n"
            f"    기대: {dict(sorted(EXPECTED_SKIPS.items()))}\n"
            f"  샘플 PDF({CACHE.name})를 못 받으면 서른 개 넘게 조용히 빠진다.\n"
            f"  받아오는 곳: {PDF_URL}\n"
            "  네트워크 없이 나머지만 돌리려면 SAMPLE_PDF_MISSING_OK=1을 준다.")
