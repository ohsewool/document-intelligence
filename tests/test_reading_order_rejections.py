"""거부 하나하나가 실제로 거부하는가.

`reading_order.py`의 85%가 실행되고 있었고, 실행되지 않는 15%는 **전부 거부
분기**였다. 잘못된 입력을 막는 `raise`가 열넷 있는데 그중 아무것도 한 번도
발동한 적이 없었다.

"표현할 수 없는 것은 거부한다"가 이 저장소의 논지다. 거부가 시험된 적이 없으면
그 논지는 코드에 적힌 문장이지 성질이 아니다 — 조건 하나가 뒤집혀 있어도 정상
입력만으로는 아무 차이가 없다. 이 프로젝트는 이미 그런 것을 만난 적이 있다:
`access.py`에 권한 헬퍼가 전부 있었고 `ledger.py`가 하나도 import하지 않았다.

전부 발동시켜 봤고 **열넷 다 동작한다.** 결함은 없었다. 그래서 이 파일은 결함을
고치는 것이 아니라, 다음에 조건이 뒤집혔을 때 알아차리게 하는 것이다.

거부 메시지까지 맞추는 이유는 따로 있다. 순수 순환(`a→b→a`)은 "종점이 정확히
하나여야 한다"로 걸린다 — 종점 검사가 먼저 돌기 때문이고, 그것도 참인 서술이다.
끊긴 순환을 가리키는 메시지는 **다른 입력**에서만 나온다(온전한 사슬 하나에 따로
도는 순환이 붙은 경우). 메시지를 안 보면 두 경로가 같은 것으로 보이고, 한쪽이
죽은 코드가 돼도 모른다.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from document_intelligence.reading_order import (  # noqa: E402
    ReadingOrder,
    ReadingOrderLink,
    RegionReference,
)

PAGES = {"p1": ["a", "b"]}
CHAIN = [ReadingOrderLink(RegionReference("p1", "a"), RegionReference("p1", "b")),
         ReadingOrderLink(RegionReference("p1", "b"))]


def ref(page: str, region: str) -> RegionReference:
    return RegionReference(page, region)


def link(page: str, region: str, *, then: tuple[str, str] | None = None) -> ReadingOrderLink:
    return ReadingOrderLink(ref(page, region), ref(*then) if then else None)


class TestAReferenceMustNameSomething:
    @pytest.mark.parametrize("page,region", [("p1", ""), ("", "a"), ("p1", None), (None, "a")])
    def test_an_empty_or_missing_identifier_is_refused(self, page, region):
        with pytest.raises(ValueError, match="non-empty string"):
            RegionReference(page, region)

    def test_a_link_needs_a_reference_not_a_string(self):
        with pytest.raises(TypeError, match="region must be a RegionReference"):
            ReadingOrderLink("p1-a")

    def test_the_next_region_too(self):
        with pytest.raises(TypeError, match="next_region must be"):
            ReadingOrderLink(ref("p1", "a"), "b")

    def test_a_terminal_link_may_have_no_next_region(self):
        """거부만 확인하면 전부 거부하는 구현도 통과한다."""
        assert ReadingOrderLink(ref("p1", "b")).next_region is None


class TestTheOwnershipMapMustBeWellFormed:
    def test_a_page_identifier_must_not_be_empty(self):
        with pytest.raises(ValueError, match="page identifiers must be non-empty"):
            ReadingOrder.validate({"": ["a"]}, CHAIN)

    def test_page_regions_must_be_iterable(self):
        with pytest.raises(TypeError, match="page regions must be iterable"):
            ReadingOrder.validate({"p1": 5}, CHAIN)

    def test_a_region_identifier_must_not_be_empty(self):
        with pytest.raises(ValueError, match="region identifiers must be non-empty"):
            ReadingOrder.validate({"p1": ["a", ""]}, CHAIN)

    def test_two_pages_cannot_share_an_identifier(self):
        """dict으로는 만들 수 없다 - 키가 이미 유일하다. `Mapping`은 만들 수 있고,
        서명은 `Mapping`을 받는다. 도달할 수 없다고 넘겼다면 이 줄은 영영 실행되지
        않는 검사로 남았을 것이다."""
        from collections.abc import Mapping

        class DuplicateKeys(Mapping):
            def __iter__(self):
                return iter(["p1", "p1"])

            def __len__(self):
                return 2

            def __getitem__(self, key):
                return ["a", "b"]

            def items(self):
                return [("p1", ["a"]), ("p1", ["b"])]

        with pytest.raises(ValueError, match="page identifiers must be unique"):
            ReadingOrder.validate(DuplicateKeys(), CHAIN)

    def test_a_page_may_not_list_the_same_region_twice(self):
        with pytest.raises(ValueError, match="unique within a page"):
            ReadingOrder.validate({"p1": ["a", "a", "b"]}, CHAIN)


class TestTheLinksMustBeWellFormed:
    def test_an_empty_reading_order_is_refused(self):
        """빈 순서는 "순서가 없다"가 아니라 "순서를 안다고 주장하면서 아무것도
        말하지 않는 것"이다."""
        with pytest.raises(ValueError, match="at least one link"):
            ReadingOrder.validate(PAGES, [])

    def test_something_that_is_not_a_link_is_refused(self):
        with pytest.raises(TypeError, match="only ReadingOrderLink"):
            ReadingOrder.validate(PAGES, ["not-a-link"])

    def test_a_reference_to_an_unknown_page_is_refused(self):
        with pytest.raises(ValueError, match="unknown page"):
            ReadingOrder.validate(PAGES, [link("p9", "a", then=("p1", "b")), link("p1", "b")])

    def test_a_region_belonging_to_another_page_is_refused(self):
        """존재하는 region 이름이라도 그 페이지의 것이 아니면 안 된다. 이름이
        맞으니 통과시키면 인용이 다른 페이지를 가리킨다."""
        with pytest.raises(ValueError, match="ownership mismatch"):
            ReadingOrder.validate({"p1": ["a"], "p2": ["b"]},
                                  [link("p1", "b", then=("p2", "b")), link("p2", "b")])


class TestTheSequenceMustBeASequence:
    def test_two_regions_cannot_share_a_successor(self):
        with pytest.raises(ValueError, match="multiple predecessors"):
            ReadingOrder.validate(
                {"p1": ["a", "b", "c"]},
                [link("p1", "a", then=("p1", "c")), link("p1", "b", then=("p1", "c")),
                 link("p1", "c")])

    def test_there_must_be_exactly_one_end(self):
        with pytest.raises(ValueError, match="exactly one terminal"):
            ReadingOrder.validate({"p1": ["a", "b"]}, [link("p1", "a"), link("p1", "b")])

    def test_a_pure_cycle_is_caught_as_having_no_end(self):
        """`a→b→a`에는 종점이 없다. 종점 검사가 먼저 돌므로 순환 메시지가 아니라
        종점 메시지가 나오고, 그것도 참인 서술이다. 메시지를 고정해두지 않으면
        아래 테스트와 같은 경로를 도는 것으로 착각하게 된다."""
        with pytest.raises(ValueError, match="exactly one terminal"):
            ReadingOrder.validate(
                {"p1": ["a", "b"]},
                [link("p1", "a", then=("p1", "b")), link("p1", "b", then=("p1", "a"))])

    def test_a_separate_cycle_beside_a_valid_chain_is_caught_as_disconnected(self):
        """온전한 사슬 하나(a→b)에 따로 도는 순환(c→d→c)이 붙은 경우. 종점은
        하나(b)이고 시작점도 하나(a)라 앞의 두 검사를 통과하고, 마지막 도달성
        검사만이 잡는다 - 이 입력이 없으면 그 줄은 실행되지 않는다."""
        with pytest.raises(ValueError, match="cycle or disconnected"):
            ReadingOrder.validate(
                {"p1": ["a", "b", "c", "d"]},
                [link("p1", "a", then=("p1", "b")), link("p1", "b"),
                 link("p1", "c", then=("p1", "d")), link("p1", "d", then=("p1", "c"))])


class TestTheValidatorStillAcceptsWhatItShould:
    """거부만 모아두면, 무엇이든 거부하는 구현이 이 파일 전체를 통과한다."""

    def test_a_simple_chain_is_accepted(self):
        assert ReadingOrder.validate(PAGES, CHAIN).regions == (ref("p1", "a"), ref("p1", "b"))

    def test_a_cross_page_chain_is_accepted(self):
        order = ReadingOrder.validate(
            {"p1": ["a"], "p2": ["b"]},
            [link("p1", "a", then=("p2", "b")), link("p2", "b")])
        assert len(order.regions) == 2

    def test_the_supplied_order_is_kept(self):
        """검증기가 순서를 다시 매기면 호출자가 아는 순서가 아니라 검증기가
        추측한 순서가 된다 - 이 모듈이 존재하지 않아도 되는 상태다."""
        order = ReadingOrder.validate(
            {"p1": ["a", "b", "c"]},
            [link("p1", "b", then=("p1", "c")), link("p1", "c"),
             link("p1", "a", then=("p1", "b"))])
        assert order.regions == (ref("p1", "b"), ref("p1", "c"), ref("p1", "a"))
