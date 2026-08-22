"""아무도 발동시킨 적 없는 거부들.

`reading_order.py`에는 이 검사가 이미 있다(`test_reading_order_rejections.py`).
그 파일의 머리말은 이렇게 말한다 — *"거부가 시험된 적이 없으면 그건 코드에 적힌
문장이지 성질이 아니다."* **그 감사는 한 파일에서 멈췄다.**

2026-08-22에 패키지 전체에 같은 시험을 걸었다. 문자열 메시지를 가진 `raise`
**76개를 하나씩 `pass`로 바꾸고** 매번 스위트를 돌렸다.

    잡힘            50건
    안 잡힘         23건   ← 그중 2건은 저장소가 도달 불가로 선언해둔 줄
    비종료           1건   ← 순환 검사를 지우면 `while`이 영영 돈다. 그것도 거부가 일한다는 증거다
    문법 오류        2건   ← 여러 줄 raise. 아래에서 따로 다뤘다

**진짜로 안 잡히는 것이 21건이었다.** `coordinates.py`는 13개 중 9개, `hierarchy.py`는
16개 중 9개가 지워도 초록불이었다. `reading_order.py`만 20/20이었고, 그것이 그 파일에만
감사가 있었기 때문이라는 것이 이 파일의 요점이다.

**첫 감사는 무효였다.** `--timeout=300`을 넘겼는데 이 저장소에 그 플러그인이 없어
pytest가 사용법 오류(rc=4)로 끝났고, 스크립트는 0 아닌 종료 코드를 전부 "잡힘"으로
읽어 76/76 초록을 냈다. `mutate.py`에서 고쳤던 함정을 새 하네스가 그대로 반복했다.
기준선 확인과 rc 4·5 구분을 넣고 다시 돌린 것이 위 숫자다.

여기 있는 것은 그 21건 각각을 발동시킨다. 메시지까지 맞춘다 — 맞추지 않으면 다른
검사가 먼저 걸려도 통과하고, 그 함정에는 이 저장소가 이미 한 번 빠졌다
(`test_rejects_duplicate_regions`가 유일성 검사를 지워도 통과했다).
"""

import unittest
from pathlib import Path

from document_intelligence.coordinates import (
    CoordinateError,
    Origin,
    PageBox,
    PageSpace,
    PdfPageTransform,
    Unit,
)
from document_intelligence.hierarchy import (
    DocumentHierarchy,
    DocumentReference,
    PageHierarchyReference,
    RegionHierarchyReference,
    SectionReference,
)
from document_intelligence.model import BoundingBox, Page, TextRegion


class PageSpaceRejections(unittest.TestCase):
    """`PageSpace`는 자기 단위와 원점이 무엇인지 안다고 주장한다. 문자열을 받아
    들이면 그 주장은 이후 모든 변환에서 조용히 틀린다."""

    def test_the_origin_must_be_an_origin(self) -> None:
        with self.assertRaisesRegex(CoordinateError, "origin must be an Origin"):
            PageSpace(100, 200, "bottom-left")

    def test_the_unit_must_be_a_unit(self) -> None:
        with self.assertRaisesRegex(CoordinateError, "unit must be a Unit"):
            PageSpace(100, 200, Origin.BOTTOM_LEFT, "pt")


class PageBoxRejections(unittest.TestCase):
    def setUp(self) -> None:
        self.space = PageSpace(100, 200)
        self.other = PageSpace(300, 400)

    def test_the_space_must_be_a_page_space(self) -> None:
        with self.assertRaisesRegex(CoordinateError, "space must be a PageSpace"):
            PageBox(10, 20, 40, 80, "a page")

    def test_clipping_into_a_different_space_is_refused(self) -> None:
        """다른 지면으로 자르는 것은 좌표를 옮기는 일이고, 이 타입은 옮기지
        않는다. 조용히 허용하면 인용이 다른 페이지를 가리킨다."""
        box = PageBox(10, 20, 40, 80, self.space)
        with self.assertRaisesRegex(CoordinateError, "clip space must match the box space"):
            box.clipped_to(self.other)

    def test_a_box_entirely_off_the_page_is_refused(self) -> None:
        """겹치지 않는 상자를 자르면 넓이 0이 남는다. 그것을 돌려주면 '이 자리'가
        자리가 아닌 인용이 만들어진다."""
        box = PageBox(500, 600, 700, 800, self.space)
        with self.assertRaisesRegex(CoordinateError, "wholly outside page bounds"):
            box.clipped_to()


class PdfTransformRejections(unittest.TestCase):
    def test_pdf_dimensions_must_be_positive(self) -> None:
        with self.assertRaisesRegex(CoordinateError, "PDF dimensions must be greater than zero"):
            PdfPageTransform(0, 200, 0)

    def test_the_target_origin_must_be_an_origin(self) -> None:
        with self.assertRaisesRegex(CoordinateError, "target_origin must be an Origin"):
            PdfPageTransform(100, 200, 0, "top-left")

    def test_a_forward_box_must_be_in_unrotated_pdf_points(self) -> None:
        """이미 변환된 상자를 다시 변환하면 회전이 두 번 적용된다. 값은 나오고,
        틀린다 — 거부가 없으면 아무도 모른다."""
        transform = PdfPageTransform(100, 200, 90)
        already_rotated = PageBox(10, 20, 40, 80, transform.page_space)
        with self.assertRaisesRegex(CoordinateError, "unrotated PDF point space"):
            transform.forward_box(already_rotated)

    def test_an_inverse_box_must_be_in_this_transform_page_space(self) -> None:
        transform = PdfPageTransform(100, 200, 90)
        raw = PageBox(10, 20, 40, 80, PageSpace(100, 200, Origin.BOTTOM_LEFT, Unit.POINT))
        with self.assertRaisesRegex(CoordinateError, "this transform's page space"):
            transform.inverse_box(raw)


class HierarchyPositionRejections(unittest.TestCase):
    def test_a_position_must_be_a_non_negative_integer(self) -> None:
        with self.assertRaisesRegex(ValueError, "position must be a non-negative integer"):
            SectionReference("document-1", "intro", position=-1)

    def test_a_boolean_is_not_a_position(self) -> None:
        """`True`는 `int`의 부분형이라 `isinstance` 검사만으로는 통과한다.
        이 프로젝트가 다른 저장소에서 이미 당한 퇴화 입력이다."""
        with self.assertRaisesRegex(ValueError, "position must be a non-negative integer"):
            SectionReference("document-1", "intro", position=True)


class HierarchyTypeRejections(unittest.TestCase):
    def setUp(self) -> None:
        self.document = DocumentReference("document-1")
        self.section = SectionReference("document-1", "intro", position=0)
        self.page = PageHierarchyReference("document-1", "page-1", "intro", 0)
        self.region = RegionHierarchyReference("document-1", "page-1", "region-1", 0)

    def test_the_document_must_be_a_document_reference(self) -> None:
        with self.assertRaisesRegex(TypeError, "document must be a DocumentReference"):
            DocumentHierarchy("document-1")

    def test_sections_must_be_section_references(self) -> None:
        with self.assertRaisesRegex(TypeError, "only SectionReference"):
            DocumentHierarchy(self.document, sections=("intro",))

    def test_pages_must_be_page_references(self) -> None:
        with self.assertRaisesRegex(TypeError, "only PageHierarchyReference"):
            DocumentHierarchy(self.document, sections=(self.section,), pages=("page-1",))

    def test_regions_must_be_region_references(self) -> None:
        with self.assertRaisesRegex(TypeError, "only RegionHierarchyReference"):
            DocumentHierarchy(self.document, sections=(self.section,),
                              pages=(self.page,), regions=("region-1",))


class HierarchyUniquenessRejections(unittest.TestCase):
    """같은 이름의 두 페이지는 인용이 어느 쪽을 가리키는지 정할 수 없게 만든다."""

    def setUp(self) -> None:
        self.document = DocumentReference("document-1")
        self.section = SectionReference("document-1", "intro", position=0)

    def test_two_pages_cannot_share_an_identifier(self) -> None:
        pages = (PageHierarchyReference("document-1", "page-1", "intro", 0),
                 PageHierarchyReference("document-1", "page-1", "intro", 1))
        with self.assertRaisesRegex(ValueError, "page identifiers must be unique within a document"):
            DocumentHierarchy(self.document, sections=(self.section,), pages=pages)

    def test_two_regions_on_a_page_cannot_share_an_identifier(self) -> None:
        pages = (PageHierarchyReference("document-1", "page-1", "intro", 0),)
        regions = (RegionHierarchyReference("document-1", "page-1", "region-1", 0),
                   RegionHierarchyReference("document-1", "page-1", "region-1", 1))
        with self.assertRaisesRegex(ValueError, "region identifiers must be unique within a page"):
            DocumentHierarchy(self.document, sections=(self.section,),
                              pages=pages, regions=regions)

    def test_two_pages_cannot_share_a_position_under_one_section(self) -> None:
        """순서를 두 개가 같이 차지하면 '세 번째 페이지'가 두 곳을 가리킨다."""
        pages = (PageHierarchyReference("document-1", "page-1", "intro", 0),
                 PageHierarchyReference("document-1", "page-2", "intro", 0))
        with self.assertRaisesRegex(ValueError, "siblings must have unique positions"):
            DocumentHierarchy(self.document, sections=(self.section,), pages=pages)

    def test_two_regions_cannot_share_a_position_on_one_page(self) -> None:
        pages = (PageHierarchyReference("document-1", "page-1", "intro", 0),)
        regions = (RegionHierarchyReference("document-1", "page-1", "region-1", 0),
                   RegionHierarchyReference("document-1", "page-1", "region-2", 0))
        with self.assertRaisesRegex(ValueError, "siblings must have unique positions"):
            DocumentHierarchy(self.document, sections=(self.section,),
                              pages=pages, regions=regions)


class ModelRejections(unittest.TestCase):
    def test_a_bounding_box_names_a_known_coordinate_space(self) -> None:
        """어느 공간인지 모르는 좌표는 숫자일 뿐이다."""
        with self.assertRaisesRegex(ValueError, "coordinate_space must be"):
            BoundingBox(0.1, 0.1, 0.5, 0.5, coordinate_space="pdf")

    def test_a_region_identifier_must_not_be_empty(self) -> None:
        with self.assertRaisesRegex(ValueError, "region identifier must not be empty"):
            TextRegion("", BoundingBox(0.1, 0.1, 0.5, 0.5))

    def test_a_page_number_must_be_a_positive_integer(self) -> None:
        with self.assertRaisesRegex(ValueError, "page number must be a positive integer"):
            Page(0, 100.0, 200.0, regions=())

    def test_a_boolean_is_not_a_page_number(self) -> None:
        with self.assertRaisesRegex(ValueError, "page number must be a positive integer"):
            Page(True, 100.0, 200.0, regions=())


class TheTwoMultiLineRejections(unittest.TestCase):
    """감사가 "문법 오류"로 남긴 둘. `raise` 줄만 `pass`로 바꾸는 변이가 여러 줄
    `raise`에서는 깨진다 — 도구의 한계이지 이 거부들에 대한 판정이 아니었다.
    손으로 발동시켜 확인한다."""

    def test_a_transcribed_region_must_carry_a_confidence(self) -> None:
        with self.assertRaisesRegex(ValueError, "transcribed region must carry"):
            TextRegion("r1", BoundingBox(0.1, 0.1, 0.5, 0.5), provenance="transcribed")

    def test_an_extracted_region_must_not_carry_one(self) -> None:
        """추출된 글자에 확신도를 붙이면 문서가 말한 것을 추정으로 바꾼다."""
        with self.assertRaisesRegex(ValueError, "extracted region has no confidence"):
            TextRegion("r1", BoundingBox(0.1, 0.1, 0.5, 0.5), confidence=0.9)


class TheAuditIsRecorded(unittest.TestCase):
    """숫자를 문서에도 적어둔다. 적어두지 않으면 다음 사람은 이 파일이 왜 이만큼
    있는지 모르고, 줄여도 아무도 모른다."""

    def test_the_readme_says_what_the_audit_found(self) -> None:
        from pathlib import Path

        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
        self.assertIn("76개를 하나씩", readme)
        self.assertIn("21건", readme)


class LinesNoTestEverRan(unittest.TestCase):
    """거부 감사 뒤에 질문을 넓혔다 — **한 번도 실행되지 않는 줄이 무엇인가.**
    586줄 중 7줄이었고, 다섯 저장소 중 가장 적었다. 전부 작은 갈래지만 각각
    무언가를 말한다."""

    def test_a_list_of_regions_is_accepted_and_frozen(self) -> None:
        """서명은 튜플을 말하지만 리스트로 부르는 호출자가 있다. 받아서 얼리는
        갈래가 한 번도 지나가지 않았다 — **모델이 불변이라는 주장이 그 갈래에
        걸려 있다.**"""
        page = Page(1, 100.0, 200.0, regions=[TextRegion("r1", BoundingBox(0.1, 0.1, 0.5, 0.5))])
        self.assertIsInstance(page.regions, tuple)

    def test_a_list_of_pages_is_accepted_and_frozen(self) -> None:
        from document_intelligence.model import Document

        page = Page(1, 100.0, 200.0, regions=())
        document = Document("doc-1", "0" * 64, pages=[page], evidence=[])
        self.assertIsInstance(document.pages, tuple)
        self.assertIsInstance(document.evidence, tuple)

    def test_a_list_of_hierarchy_records_is_accepted_and_frozen(self) -> None:
        document = DocumentReference("document-1")
        section = SectionReference("document-1", "intro", position=0)
        hierarchy = DocumentHierarchy(document, sections=[section])
        self.assertIsInstance(hierarchy.sections, tuple)

    def test_a_hierarchy_identifier_must_be_a_non_empty_string(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be a non-empty string"):
            DocumentReference("")

    def test_a_coordinate_that_is_not_a_number_is_refused(self) -> None:
        """`True`는 `int`의 부분형이다. 좌표로 받으면 1.0이 되고, **플래그가
        자리로 둔갑한다** — 이 저장소가 페이지 번호에서 이미 막아둔 것과 같은 길이다."""
        with self.assertRaisesRegex(CoordinateError, "must be a finite number"):
            PageSpace(True, 200)

    def test_a_page_the_model_refuses_wholesale_is_reported_not_raised(self) -> None:
        """어댑터는 구역별로 먼저 검증한다. 그래도 **구역 하나가 소유하지 않는
        이유**로 페이지 전체가 거부될 수 있고, 그때 어댑터는 터지지 않고 `skipped`에
        적어야 한다. 그 갈래가 한 번도 지나가지 않았다.

        실제 PDF로 그 상태를 만들려면 병리적인 문서가 필요하다 — 식별자는
        `enumerate`에서 나오므로 중복될 수 없고, 남은 길은 폭이 0인 페이지다.
        그래서 **모델이 거부하는 상황 자체를 주입**한다. 여기서 확인하려는 것은
        "모델이 거부했을 때 어댑터가 무엇을 하는가"이지 모델이 언제 거부하는가가
        아니다 — 후자는 `model.py` 쪽 테스트가 본다.
        """
        import document_intelligence.adapters.pdfplumber as adapter

        original = adapter.Page

        def refusing(*args, **kwargs):
            raise ValueError("region identifiers must be unique within a page")

        adapter.Page = refusing
        try:
            result = adapter.parse_pdf(Path(__file__).resolve().parents[1]
                                       / "tests" / "fixtures" / "sample.pdf")
        finally:
            adapter.Page = original

        self.assertEqual(result.document.pages, ())
        self.assertTrue(result.skipped)
        self.assertTrue(any("page rejected" in item.reason for item in result.skipped))
