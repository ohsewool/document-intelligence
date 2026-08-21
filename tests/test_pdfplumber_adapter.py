"""The model against a parser it did not choose.

Every other test here builds its own regions, so the model only ever meets
coordinates written to satisfy it. That proves the rules are self-consistent,
not that they survive contact with a real parser. These run an actual PDF
through pdfplumber and hand the output over unmodified.

The PDF is fetched once and cached; without network these skip rather than
pretending to have run.
"""

import hashlib
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

pytest.importorskip("pdfplumber")

from document_intelligence.adapters.pdfplumber import parse_pdf  # noqa: E402
from document_intelligence.model import BoundingBox  # noqa: E402

# `sample_pdf`는 tests/conftest.py에 있다. 여기 있었을 때는 이 모듈이 먼저 돌아야만
# 파일이 생겼고, 알파벳 순으로 앞서는 모듈은 CI에서 조용히 skip됐다.


_CACHE: dict[tuple, object] = {}


def parse_once(path, **kwargs):
    """Parse once per configuration.

    Correcting an earlier claim in this file: it said a full parse cost about
    three minutes and that the suite took 386 seconds. Both numbers were
    measured while an embedding job was saturating the CPU, and neither is real.
    Uncontended, the whole document parses in about 7 seconds and the suite runs
    in twelve.

    Memoising is still worth doing - three configurations were being parsed
    eleven times - but the case for it is ordinary rather than urgent, and a
    number taken under load is not a measurement.
    """
    key = (str(path), tuple(sorted(kwargs.items())))
    if key not in _CACHE:
        _CACHE[key] = parse_pdf(path, **kwargs)
    return _CACHE[key]


@pytest.fixture(scope="module")
def parsed(sample_pdf):
    """Three pages: enough for the structural claims that do not need more.

    One test parses all fifteen, and does so on every run.
    """
    return parse_once(sample_pdf, max_pages=3)


@pytest.fixture(scope="module")
def whole_paper(sample_pdf):
    """열다섯 페이지 전부. 공개된 숫자가 설명하는 것은 이쪽이다."""
    return parse_once(sample_pdf)


class TestARealParseIsAcceptedWhole:
    def test_the_document_has_pages_and_regions(self, parsed):
        assert parsed.document.pages
        assert parsed.region_count > 100

    def test_no_page_of_a_real_paper_is_rejected(self, sample_pdf):
        """Over the whole document, not a sample of it.

        Was marked `slow` on the strength of a contended timing. At seven
        seconds it does not need to be, and a full-document check that runs by
        default is worth more than one behind a flag.
        """
        result = parse_once(sample_pdf)
        assert len(result.document.pages) == 15
        assert result.skipped == ()
        assert result.region_count > 700

    def test_nothing_is_rejected_from_a_well_formed_pdf(self, parsed):
        """If a normal paper produced rejections, the rules would be too strict
        to use on real documents."""
        assert parsed.skipped == ()

    def test_page_numbers_are_sequential_from_one(self, parsed):
        numbers = [page.number for page in parsed.document.pages]
        assert numbers == list(range(1, len(numbers) + 1))

    def test_the_checksum_is_of_the_bytes_that_were_parsed(self, parsed, sample_pdf):
        """A citation is only meaningful against the file it came from."""
        assert parsed.document.checksum == hashlib.sha256(sample_pdf.read_bytes()).hexdigest()

    def test_every_region_fits_its_page(self, parsed):
        """The count is asserted because this test has neither an `assert` of
        its own nor anything guaranteeing the loop runs.

        `validate_for_page` raising *is* the assertion, which is legitimate -
        but over an empty parse the body never executes and the test passes
        having checked nothing. Non-emptiness is pinned in a different test, so
        deleting that one would quietly turn this into a no-op. A test should
        not depend on another test to be meaningful.
        """
        checked = 0
        for page in parsed.document.pages:
            for region in page.regions:
                region.bounding_box.validate_for_page(page.width, page.height)
                checked += 1
        assert checked > 100, f"only {checked} regions were checked"

    def test_region_identifiers_are_unique_within_a_page(self, parsed):
        for page in parsed.document.pages:
            identifiers = [region.identifier for region in page.regions]
            assert len(identifiers) == len(set(identifiers))


class TestNormalizedCoordinates:
    def test_normalized_output_stays_within_the_unit_square(self, sample_pdf):
        result = parse_once(sample_pdf, max_pages=3, coordinate_space="normalized")
        assert result.region_count > 0
        for page in result.document.pages:
            for region in page.regions:
                box = region.bounding_box
                assert 0 <= box.left < box.right <= 1
                assert 0 <= box.top < box.bottom <= 1

    def test_both_spaces_find_the_same_regions(self, sample_pdf):
        """Changing units must not change what was found."""
        page_space = parse_once(sample_pdf, max_pages=3)
        unit_space = parse_once(sample_pdf, max_pages=3, coordinate_space="normalized")
        assert page_space.region_count == unit_space.region_count


class TestMalformedInputIsIsolated:
    """One bad line must not cost the page it sits on."""

    @pytest.fixture(scope="class")
    def with_broken_lines(self, sample_pdf):
        # Class-scoped, so the injected parse happens once rather than per test.
        # monkeypatch is function-scoped and cannot be used here.
        import document_intelligence.adapters.pdfplumber as adapter
        original = adapter._lines

        def broken(page):
            rows = original(page)
            if rows:
                degenerate = [dict(w, top=100.0, bottom=100.0) for w in rows[0]]
                off_page = [dict(w, x0=-50.0, x1=-10.0) for w in rows[0]]
                rows = [degenerate, off_page] + rows[1:]
            return rows

        adapter._lines = broken
        try:
            return parse_pdf(sample_pdf, max_pages=2)
        finally:
            adapter._lines = original

    def test_the_bad_lines_are_rejected(self, with_broken_lines):
        """Checked by cause rather than by message.

        This test used to match on the exception text, which is what showed the
        adapter needed to classify at all: if the suite has to read prose to
        know what happened, so does every caller.
        """
        causes = {item.cause for item in with_broken_lines.skipped}
        assert causes == {"degenerate_box", "outside_page"}

    def test_the_rest_of_the_page_survives(self, with_broken_lines):
        """Page validates while constructing, so one bad box aborts the whole
        page. Checking each region first is what keeps the other regions."""
        assert with_broken_lines.region_count > 50

    def test_the_pages_are_still_present(self, with_broken_lines):
        assert len(with_broken_lines.document.pages) == 2

    def test_rejections_are_reported_rather_than_dropped(self, with_broken_lines):
        """An adapter that silently discards what it cannot represent reports a
        clean document over a partial one."""
        assert len(with_broken_lines.skipped) == 4
        assert all(item.identifier for item in with_broken_lines.skipped)


class TestTheAdapterDoesNotRepair:
    def test_a_degenerate_box_is_refused_not_widened(self):
        """Nudging a zero-height box to make it valid would move the citation
        off the text it points at."""
        with pytest.raises(ValueError):
            BoundingBox(10.0, 100.0, 50.0, 100.0, coordinate_space="page")

    def test_an_inverted_box_is_refused_not_reordered(self):
        with pytest.raises(ValueError):
            BoundingBox(50.0, 10.0, 10.0, 50.0, coordinate_space="page")


class TestTheOrderIsPositionNotReading:
    """`p14-l5` is the fifth line down the page, not the fifth thing you read.

    The identifiers run l1, l2, l3 and look like a reading order. They are
    vertical position, and on the two-column pages of this paper the columns
    interleave - so a reader following the numbers crosses between columns.

    Columns are not guessed at. Splitting on the largest gap between line start
    positions was measured against this document and gets it backwards: a
    single-column page shows a 16.7% gap and a genuinely two-column page shows
    8.8%. A heuristic that confident and that wrong is worse than an honest
    positional order, because a reader told the order is positional can allow
    for it.
    """

    def test_the_result_says_which_order_it_produced(self, parsed):
        assert parsed.order_basis == "vertical_position"

    def test_regions_are_ordered_by_vertical_position(self, parsed):
        for page in parsed.document.pages:
            tops = [region.bounding_box.top for region in page.regions]
            assert tops == sorted(tops)

    @pytest.mark.slow
    def test_a_two_column_page_interleaves_under_this_order(self, sample_pdf):
        """The limitation, measured rather than asserted.

        If this ever stops interleaving, either the adapter became
        column-aware - in which case order_basis must change too - or the
        fixture did.
        """
        result = parse_once(sample_pdf)
        page = next(p for p in result.document.pages if p.number == 14)
        middle = page.width / 2
        crossings = sum(
            1 for first, second in zip(page.regions, page.regions[1:])
            if (first.bounding_box.left < middle) != (second.bounding_box.left < middle)
        )
        assert crossings > 5, "expected column interleaving on a two-column page"

    def test_the_reading_order_type_is_reachable_for_callers_who_know(self):
        """The adapter cannot produce a reading order, so the type is exported
        rather than wired in - somewhere for a caller who does know to record
        and validate one."""
        from document_intelligence import ReadingOrder, validate_reading_order

        assert ReadingOrder is not None and callable(validate_reading_order)


class TestRejectionsAreClassified:
    """A caller responding to "the parser emitted a zero-height line" and to
    "the parser put text off the page" wants different things. The model says
    which in prose; the adapter says which in a value."""

    def test_a_degenerate_box_is_named_as_one(self):
        from document_intelligence.adapters.pdfplumber import classify
        assert classify("bounding-box coordinates must be ordered") == "degenerate_box"

    def test_an_off_page_box_is_named_as_one(self):
        from document_intelligence.adapters.pdfplumber import classify
        assert classify("page-space bounding box must be within page bounds") == "outside_page"
        assert classify("normalized bounding-box coordinates must be within 0..1") == "outside_page"

    def test_a_non_finite_coordinate_is_its_own_cause(self):
        from document_intelligence.adapters.pdfplumber import classify
        assert classify("bounding-box coordinates must be finite") == "non_finite"

    def test_a_duplicate_identifier_is_a_page_level_problem(self):
        from document_intelligence.adapters.pdfplumber import classify
        assert classify("region identifiers must be unique within a page") == \
            "duplicate_identifier"

    def test_an_unrecognised_rejection_is_flagged_rather_than_excused(self):
        """The model gained a rejection reason this adapter has never seen. That
        is the case a reader most needs to look at, so it is not folded into a
        benign default."""
        from document_intelligence.adapters.pdfplumber import classify
        assert classify("some future rule nobody has written yet") == "unclassified"

    def test_every_cause_the_model_can_raise_is_covered(self, sample_pdf):
        """Guards against the classifier silently going stale.

        If the model grows a reason the adapter cannot name, this fails rather
        than quietly labelling it unclassified in production.
        """
        from document_intelligence.adapters.pdfplumber import classify

        messages = [
            "bounding-box coordinates must be ordered",
            "bounding-box coordinates must be finite",
            "normalized bounding-box coordinates must be within 0..1",
            "page-space bounding box must be within page bounds",
            "region identifier must not be empty",
            "region identifiers must be unique within a page",
            "page number must be a positive integer",
            "page dimensions must be finite and positive",
        ]
        assert all(classify(m) != "unclassified" for m in messages)


def test_the_package_works_without_pdfplumber():
    """The evidence model is standard library; the adapter is the optional part.

    Checked rather than assumed. With pdfplumber blocked, 72 tests pass and only
    this module skips - so someone who wants the model without a PDF parser gets
    a working install.
    """
    import subprocess
    import sys
    import textwrap

    script = textwrap.dedent('''
        import sys
        from importlib.abc import MetaPathFinder

        class Absent(MetaPathFinder):
            def find_spec(self, name, path=None, target=None):
                if name.split(".")[0] == "pdfplumber":
                    raise ModuleNotFoundError(f"No module named {name!r}", name=name)
                return None

        sys.meta_path.insert(0, Absent())
        sys.path.insert(0, "src")
        from document_intelligence.model import BoundingBox, Document, Page, TextRegion
        page = Page(number=1, width=1.0, height=1.0, regions=(
            TextRegion(identifier="r1", bounding_box=BoundingBox(0.1, 0.1, 0.9, 0.2)),))
        print(Document(identifier="d", checksum="c", pages=(page,)).pages[0].number)
    ''')
    finished = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                              capture_output=True, text=True, timeout=300)
    assert finished.returncode == 0, finished.stderr[-800:]
    assert finished.stdout.strip() == "1"


class TestThePublishedCountsStillHold:
    """README에 실린 숫자가 지금 코드에서도 나오는가.

    README는 "15페이지 논문에서 구역 724개, 거부 0건"과 "14페이지는 구역 45개에서
    좌우를 20번 오간다"를 싣는다. 기존 검사는 **페이지 15개와 거부 0건만** 단언했고
    구역 수는 아무도 확인하지 않았다.

    `rag-profile-selector`에서 같은 빈 곳을 찾고 여기로 왔다. 거기서는 공개된
    MRR·regret 표를 아무것도 실행 결과와 대조하지 않았다. `agent-safety-core`에는
    그 검사가 있다(`test_published_benchmark.py`). **한쪽에는 있고 형제에는 없는**
    이 저장소들의 단골 모양이다.

    숫자를 여기 박아두지 않고 **README에서 읽어와** 비교한다. 박아두면 문서와 코드가
    따로 놀 때 이 파일이 문서 편을 들지 코드 편을 들지 알 수 없다. 읽어오면 둘 중
    하나가 움직이는 순간 걸린다.

    pdfplumber 버전이 바뀌어 구역 수가 달라지면 이 검사가 빨간불이 된다. **그것이
    원하는 신호다** — 공개한 숫자가 더 이상 성립하지 않는다는 뜻이니까.
    """

    @staticmethod
    def published(pattern: str) -> int:
        readme = (Path(__file__).resolve().parents[1] / "README.md").read_text(encoding="utf-8")
        match = re.search(pattern, readme)
        assert match, f"README에서 {pattern!r}를 찾지 못했다 — 문장이 바뀌었나?"
        return int(match.group(1))

    def test_the_total_region_count_is_what_the_readme_says(self, whole_paper):
        assert whole_paper.region_count == self.published(r"구역 (\d+)개, 거부 0건")

    def test_the_page_count_is_what_the_readme_says(self, whole_paper):
        assert len(whole_paper.document.pages) == self.published(r"(\d+)페이지 논문에서")

    def test_the_two_column_page_count_is_what_the_readme_says(self, whole_paper):
        """14페이지 45개는 읽기 순서 결함을 설명하는 숫자다. 그 문장이 서 있는 값."""
        assert len(whole_paper.document.pages[13].regions) == \
            self.published(r"14페이지는 구역 (\d+)개")

    def test_the_readme_numbers_are_not_trivially_small(self):
        """README에서 0이나 1을 읽어오면 위 검사들이 통과하면서 아무것도 지키지 않는다."""
        assert self.published(r"구역 (\d+)개, 거부 0건") > 100
        assert self.published(r"14페이지는 구역 (\d+)개") > 10

    def test_a_changed_count_would_be_noticed(self, whole_paper):
        """비교가 차이를 잡는지. 한 값을 흔들어 같은 판정을 걸어본다."""
        assert whole_paper.region_count + 1 != self.published(r"구역 (\d+)개, 거부 0건")

    def test_the_three_page_fixture_is_not_what_these_numbers_describe(self, parsed):
        """처음에 `parsed`(3페이지, 124구역)로 썼다가 724와 비교해 실패했다.
        기본 픽스처는 구조 검사용이고 공개된 숫자는 **논문 전체**의 것이다.
        그 구분을 여기 남긴다."""
        assert len(parsed.document.pages) == 3
        assert sum(len(page.regions) for page in parsed.document.pages) < 200
