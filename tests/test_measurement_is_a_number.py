"""`True`가 확신도로 들어올 수 있었다.

이 모듈은 이미 `nan`과 `inf`를 어디서나 거절한다 — 이번 회차에 다른 네 저장소가
따라온 쪽이 여기다(`agent-safety-core`의 lease TTL, `mcp-gateway`의 레이트 리밋,
`rag-profile-selector`의 top-k). **`bool`만 빠져 있었다.**

`bool`은 `int`의 하위형이라 `isinstance(True, Real)`이 참이고 `True`는 `1`로 들어온다.
좌표에서는 그저 이상한 값이다. **`confidence`에서는 이 모듈이 막으려는 실패 그
자체다**: 인식기가 숫자 대신 플래그를 돌려주면 **확신함**으로 기록되고, 바로 아래
독스트링은 그 반대를 약속한다 — 인식기가 얼마나 확신했는지가 파서 경계를 넘어
살아남는다는 것. 불리언은 그것을 담지 않으며, 조용히 1.0으로 읽는 것은
**추측을 판독인 척 제시하는 것**이다.
"""

import pytest

from document_intelligence.model import BoundingBox, TextRegion

NORMAL = dict(left=0.0, top=0.0, right=1.0, bottom=1.0, coordinate_space="normalized")


@pytest.fixture
def box():
    return BoundingBox(**NORMAL)


class TestABoolIsNotAMeasurement:
    def test_bool_coordinates_are_refused(self):
        with pytest.raises(ValueError, match="finite"):
            BoundingBox(left=False, top=False, right=True, bottom=True,
                        coordinate_space="normalized")

    def test_a_single_bool_coordinate_is_refused(self):
        """넷 중 하나만 섞여도 잡혀야 한다. `all(...)`이 아니라 첫 항목만 보면
        이 검사는 절반만 동작한다."""
        with pytest.raises(ValueError, match="finite"):
            BoundingBox(left=0.0, top=0.0, right=True, bottom=1.0,
                        coordinate_space="normalized")

    def test_a_bool_confidence_is_refused(self, box):
        with pytest.raises(ValueError, match="finite"):
            TextRegion(identifier="r", bounding_box=box,
                       provenance="transcribed", confidence=True)

    def test_false_is_refused_too(self, box):
        """`False`는 0.0으로 읽혀 "전혀 확신하지 못함"이 된다 — 반대 방향의
        같은 거짓말이다."""
        with pytest.raises(ValueError, match="finite"):
            TextRegion(identifier="r", bounding_box=box,
                       provenance="transcribed", confidence=False)


class TestTheExistingRefusalsStillHold:
    @pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
    def test_non_finite_coordinates_are_refused(self, value):
        with pytest.raises(ValueError, match="finite"):
            BoundingBox(left=0.0, top=0.0, right=value, bottom=1.0,
                        coordinate_space="normalized")

    @pytest.mark.parametrize("value", [float("nan"), float("inf")])
    def test_non_finite_confidence_is_refused(self, box, value):
        with pytest.raises(ValueError, match="finite"):
            TextRegion(identifier="r", bounding_box=box,
                       provenance="transcribed", confidence=value)

    @pytest.mark.parametrize("value", [-0.001, 1.001])
    def test_confidence_outside_the_range_is_refused(self, box, value):
        with pytest.raises(ValueError, match="0..1"):
            TextRegion(identifier="r", bounding_box=box,
                       provenance="transcribed", confidence=value)

    @pytest.mark.parametrize("value", [0.0, 1.0])
    def test_the_ends_of_the_range_are_allowed(self, box, value):
        """0과 1은 경계 안이다. 배제하면 "전혀 모르겠다"와 "확실하다"를 말할 수 없다."""
        region = TextRegion(identifier="r", bounding_box=box,
                            provenance="transcribed", confidence=value)
        assert region.confidence == value


class TestTheseChecksAreNotVacuous:
    def test_a_real_confidence_still_passes(self, box):
        """전부 거절하는 검증은 전부 거절하는 것으로도 통과한다."""
        region = TextRegion(identifier="r", bounding_box=box,
                            provenance="transcribed", confidence=0.87)
        assert region.confidence == 0.87

    def test_an_int_confidence_still_passes(self, box):
        """`bool`만 배제하는 것이지 `int`를 배제하는 것이 아니다. 1은 유효한 확신도다."""
        assert TextRegion(identifier="r", bounding_box=box,
                          provenance="transcribed", confidence=1).confidence == 1

    def test_a_normal_box_still_passes(self):
        assert BoundingBox(left=0.1, top=0.1, right=0.9, bottom=0.9,
                           coordinate_space="normalized").right == 0.9

    def test_an_extracted_region_still_refuses_a_confidence(self, box):
        """이 모듈의 원래 불변식. 새 검사가 그 앞을 가로채면 메시지가 바뀐다."""
        with pytest.raises(ValueError, match="no confidence"):
            TextRegion(identifier="r", bounding_box=box,
                       provenance="extracted", confidence=0.9)
