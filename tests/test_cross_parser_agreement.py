"""두 번째 파서를 오라클로 — 좌표가 맞다는 것을 어댑터 밖에서 확인한다.

이 저장소의 주장은 "모델은 파서가 내놓은 것을 그대로 받아 같은 방식으로 검증한다"
이고, 그 주장은 지금까지 **파서 하나로만** 시험돼 왔다. 어댑터가 좌표를 잘못
만들어도 — 예를 들어 PDF의 아래쪽 원점을 위쪽으로 뒤집는 것을 빼먹어도 — 모델은
그 좌표들이 서로 모순되지 않으니 전부 받아들인다. 자기 자신과 일관된 것과 문서의
그 자리를 가리키는 것은 다른 주장이다.

`pypdf`는 pdfplumber와 **다른 구현**이다(pdfplumber는 pdfminer 위에 있고, pdfminer를
직접 쓰면 같은 엔진을 두 번 부르는 셈이라 독립적이지 않다). 텍스트를 그리는
연산자에서 텍스트 행렬을 직접 읽어 PDF 사용자 공간의 baseline을 준다 — 아래쪽
원점이다. 그래서 두 엔진이 같은 줄을 같은 자리에 놓는지 물을 수 있다.

**pypdf로 어댑터를 하나 더 만들지는 않았다.** visitor는 시작점과 글자 크기만 주고
너비를 주지 않는다. 너비를 글자 수로 추정하면 인용이 글자가 없는 곳을 가리키게
되는데, 그건 이 모델이 막으려는 바로 그 실패다. 그래서 pypdf는 어댑터가 아니라
**검사자**로만 쓴다.

측정한 것 (15쪽 논문, pypdf 조각 1,658개):

    본문 쪽      일치율 91.7% ~ 100%     잔차 표준편차 0.04 ~  3.91 pt
    표·그림 쪽   일치율 13.6% ~ 74.8%    잔차 표준편차 14.69 ~ 50.80 pt

**첫 판은 이빨이 없었다.** "조각마다 가까운 줄이 있는가"만 물었고, 좌표를 위아래로
뒤집어도 80.7%가 통과했다 - 줄 간격이 11~14pt인 지면에서는 아무 높이나 6pt 안에
이웃이 있다. 허용치를 좁혀도 갈리지 않았다. 검사가 실패할 줄 모르는데 통과를
증거로 쓸 뻔했다.

갈리는 것은 근접이 아니라 **일관성**이다. 방향이 맞으면 두 엔진의 차이는 모든 줄에서
같은 값 - 디센더 - 이고, 뒤집히면 잔차가 줄 간격 안에서 무작위가 된다. 그래서
`TestTheCheckHasTeeth`가 뒤집은 좌표로 먼저 돌려보고, 그게 무너지는 것을 본 뒤에야
정상 결과를 신뢰한다.

표·그림 쪽의 불일치는 **허용치를 늘려 덮을 것이 아니라 밝혀야 할 한계다**: 방향이
맞는데도 두 엔진이 어디에 글자가 있는지 합의하지 못하는 지면이 있고, 그 지면으로의
인용은 본문 쪽 인용만큼 믿을 것이 못 된다. 아무것도 그렇게 말하고 있지 않았다.
"""

import statistics
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

pytest.importorskip("pdfplumber")
pypdf = pytest.importorskip("pypdf")

from document_intelligence.adapters.pdfplumber import parse_pdf  # noqa: E402

PDF = ROOT / "tests" / "fixtures" / "sample.pdf"

# 표와 어텐션 시각화가 있는 지면. 두 엔진이 갈리는 곳이고, 갈린다는 것이 결론이다.
FIGURE_PAGES = frozenset({9, 10, 13, 14, 15})

# 잰 값: 본문 쪽 최저 91.7%, 표·그림 쪽 최고 74.8%.
BODY_AGREEMENT = 0.90
FIGURE_AGREEMENT_CEILING = 0.80
# 두 좌표계의 차이는 디센더뿐이어야 한다. 중앙값 2.15pt로 측정됐다.
NEAR = 6.0

# **근접만으로는 부족하다.** 처음에는 "pypdf 조각마다 가까운 줄이 있는가"만 봤고,
# 좌표를 위아래로 뒤집어도 80.7%가 통과했다 - 줄 간격이 11~14pt인 지면에서는
# 아무 높이나 6pt 안에 이웃이 있다. 허용치를 0.5pt까지 좁혀 봐도 갈리지 않았다
# (정상 0.0% 대 뒤집음 20.9%: 좁히면 정상까지 같이 죽는다).
#
# 갈리는 것은 근접이 아니라 **일관성**이다. 방향이 맞으면 두 엔진의 차이는 모든
# 줄에서 같은 값 - 디센더 - 이어야 하고, 뒤집히면 잔차가 줄 간격 안에서 무작위가
# 된다. 15쪽에서 잰 값:
#
#     본문 쪽, 정상    잔차 표준편차 0.04 ~ 3.91 pt
#     본문 쪽, 뒤집음  잔차 표준편차 5.43 ~ 72.21 pt
#
# 4.5는 그 사이에서 나왔다. 그림 쪽은 방향이 맞아도 14.69pt 이상이라 따로 본다.
CONSISTENT = 4.5
FIGURE_INCONSISTENCY_FLOOR = 10.0


@pytest.fixture(scope="module")
def parsed():
    if not PDF.exists():
        pytest.skip("샘플 PDF가 없다 (네트워크 없이 받은 적 없음)")
    return parse_pdf(PDF)


@pytest.fixture(scope="module")
def baselines():
    """pypdf가 본 각 지면의 baseline. 아래쪽 원점 그대로 돌려준다."""
    reader = pypdf.PdfReader(str(PDF))
    found: dict[int, list[float]] = {}
    for index, page in enumerate(reader.pages, start=1):
        rows: list[float] = []

        def visitor(text, cm, tm, font_dict, font_size, rows=rows):
            if text.strip():
                rows.append(tm[5])

        page.extract_text(visitor_text=visitor)
        found[index] = rows
    return found


def residuals(page, rows, *, flip=False) -> list[float]:
    """각 pypdf 조각과 가장 가까운 pdfplumber 줄의 차이.

    방향이 맞으면 이 값들은 전부 디센더 하나로 모여야 한다. 흩어지면 두 엔진이
    같은 줄을 같은 자리에 놓고 있지 않다는 뜻이고, 그건 어느 한쪽이 좌표를
    지어내고 있다는 뜻이다.
    """
    bottoms = [region.bounding_box.bottom for region in page.regions]
    if not bottoms or not rows:
        return []
    found = []
    for y in rows:
        target = y if flip else page.height - y
        found.append(min(bottoms, key=lambda bottom: abs(bottom - target)) - target)
    return found


def agreement(page, rows, *, flip=False) -> float:
    """pypdf 조각 중 pdfplumber가 같은 높이에 줄을 둔 비율."""
    bottoms = [region.bounding_box.bottom for region in page.regions]
    if not bottoms or not rows:
        return 0.0
    matched = 0
    for y in rows:
        target = y if flip else page.height - y
        if min(abs(bottom - target) for bottom in bottoms) <= NEAR:
            matched += 1
    return matched / len(rows)


class TestTheTwoParsersAgreeOnBodyPages:
    def test_every_body_page_agrees(self, parsed, baselines):
        """어댑터가 좌표를 지어내지 않았다는, 어댑터 밖에서 나온 증거."""
        poor = {
            page.number: round(agreement(page, baselines[page.number]), 3)
            for page in parsed.document.pages
            if page.number not in FIGURE_PAGES
            and agreement(page, baselines[page.number]) < BODY_AGREEMENT
        }
        assert not poor, f"본문 쪽인데 두 파서가 갈린다: {poor}"

    def test_most_body_pages_agree_completely(self, parsed, baselines):
        """91.7%는 최저값이고 중앙값은 100%다. 최저만 고정하면 전반적인
        악화가 최저 한 장에 가려진다."""
        rates = [agreement(page, baselines[page.number])
                 for page in parsed.document.pages if page.number not in FIGURE_PAGES]
        assert statistics.median(rates) >= 0.99

    def test_the_gap_between_the_two_is_the_same_gap_everywhere(self, parsed, baselines):
        """차이가 디센더뿐이라면 한 지면 안에서 값이 하나로 모여야 한다.

        이것이 뒤집힌 좌표를 잡아내는 성질이다. 근접은 잡지 못한다.
        """
        scattered = {
            page.number: round(statistics.pstdev(residuals(page, baselines[page.number])), 2)
            for page in parsed.document.pages
            if page.number not in FIGURE_PAGES
            and statistics.pstdev(residuals(page, baselines[page.number])) >= CONSISTENT
        }
        assert not scattered, f"두 엔진의 차이가 줄마다 다르다: {scattered}"

    def test_and_that_gap_is_the_descender_rather_than_zero(self, parsed, baselines):
        """양수이고 작아야 한다. pdfplumber의 `bottom`은 디센더를 포함하고
        pypdf의 baseline은 아니기 때문이다."""
        everything = [value for page in parsed.document.pages
                      if page.number not in FIGURE_PAGES
                      for value in residuals(page, baselines[page.number])]
        assert 0 < statistics.median(everything) < 4


class TestWhereTheParsersDisagreeIsRecordedNotHidden:
    """허용치를 늘려 덮을 수 있었지만, 덮으면 그림 쪽 인용이 본문 쪽 인용과
    똑같이 믿을 만해 보인다. 실제로는 두 엔진이 글자 위치조차 합의하지 못한다."""

    def test_the_figure_pages_are_inconsistent_not_merely_less_aligned(self, parsed, baselines):
        """방향이 맞는데도 잔차가 흩어진다. 두 엔진이 그 지면의 글자를 서로 다른
        줄로 묶는다는 뜻이고, 인용의 신뢰도가 본문 쪽과 다르다는 뜻이다."""
        scatter = {page.number: round(statistics.pstdev(residuals(page, baselines[page.number])), 1)
                   for page in parsed.document.pages if page.number in FIGURE_PAGES}
        assert min(scatter.values()) > FIGURE_INCONSISTENCY_FLOOR, scatter

    def test_the_figure_pages_really_do_disagree(self, parsed, baselines):
        rates = {page.number: agreement(page, baselines[page.number])
                 for page in parsed.document.pages if page.number in FIGURE_PAGES}
        assert max(rates.values()) < FIGURE_AGREEMENT_CEILING, (
            f"그림 쪽이 본문 쪽만큼 일치한다: {rates}. 한계가 사라졌다면 좋은 소식이고, "
            f"그때는 이 테스트가 아니라 문서를 고쳐야 한다."
        )

    def test_the_two_groups_do_not_overlap(self, parsed, baselines):
        """임계값 0.90과 0.80은 이 간격에서 나왔다. 겹치기 시작하면 두 숫자는
        재서 나온 값이 아니라 지어낸 값이 된다."""
        rates = {page.number: agreement(page, baselines[page.number])
                 for page in parsed.document.pages}
        body = [r for n, r in rates.items() if n not in FIGURE_PAGES]
        figure = [r for n, r in rates.items() if n in FIGURE_PAGES]
        assert min(body) > max(figure)


class TestTheCheckHasTeeth:
    """전부 일치한다는 결과는, 검사가 아무것도 비교하지 않아도 똑같이 나온다."""

    def test_a_forgotten_coordinate_flip_would_be_caught(self, parsed, baselines):
        """이 검사가 존재하는 이유. PDF는 아래쪽 원점이고 이 모델은 위쪽 원점이라
        어댑터가 뒤집기를 빼먹으면 모든 구역이 위아래로 거울상이 된다 - 그래도
        서로 모순되지 않으므로 모델은 전부 받아들이고, 인용은 조용히 엉뚱한 줄을
        가리킨다. 뒤집지 않고 맞춰보면 일치율이 무너져야 한다."""
        scatter = [statistics.pstdev(residuals(page, baselines[page.number], flip=True))
                   for page in parsed.document.pages if page.number not in FIGURE_PAGES]
        assert min(scatter) > CONSISTENT, (
            f"뒤집힌 좌표가 일관돼 보인다: 최소 표준편차 {min(scatter):.2f}pt. "
            f"근접만 보던 첫 판이 여기서 80.7%로 통과했다."
        )

    def test_both_parsers_actually_produced_something(self, parsed, baselines):
        assert sum(len(rows) for rows in baselines.values()) > 1000
        assert parsed.region_count > 700

    def test_the_two_engines_are_not_the_same_engine(self):
        """pdfminer를 직접 쓰면 pdfplumber와 같은 엔진을 두 번 부르는 것이고,
        그러면 이 파일 전체가 자기 자신과의 비교가 된다."""
        assert "pdfminer" not in sys.modules or pypdf.__name__ == "pypdf"
        assert not pypdf.__file__.endswith("pdfplumber/__init__.py")

    def test_a_page_with_no_regions_scores_zero_rather_than_one(self, parsed, baselines):
        """빈 컬렉션에서 비율을 내면 1.0이 되기 쉽고, 그러면 아무것도 못 찾은
        지면이 완벽하게 일치한 것으로 보고된다."""
        empty = type(parsed.document.pages[0])(
            number=1, width=612.0, height=792.0, regions=())
        assert agreement(empty, [700.0, 600.0]) == 0.0
