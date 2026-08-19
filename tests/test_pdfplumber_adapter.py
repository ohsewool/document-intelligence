"""The model against a parser it did not choose.

Every other test here builds its own regions, so the model only ever meets
coordinates written to satisfy it. That proves the rules are self-consistent,
not that they survive contact with a real parser. These run an actual PDF
through pdfplumber and hand the output over unmodified.

The PDF is fetched once and cached; without network these skip rather than
pretending to have run.
"""

import hashlib
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

pytest.importorskip("pdfplumber")

from adapters.pdfplumber_adapter import parse_pdf  # noqa: E402
from document_intelligence.model import BoundingBox  # noqa: E402

# arXiv:1706.03762, distributed by the authors for exactly this kind of reuse.
PDF_URL = "https://arxiv.org/pdf/1706.03762v7"
CACHE = Path(__file__).parent / "fixtures" / "sample.pdf"


@pytest.fixture(scope="module")
def sample_pdf():
    if CACHE.exists():
        return CACHE
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    try:
        request = urllib.request.Request(PDF_URL, headers={"User-Agent": "document-intelligence"})
        with urllib.request.urlopen(request, timeout=60) as response:
            CACHE.write_bytes(response.read())
    except (urllib.error.URLError, TimeoutError) as error:
        pytest.skip(f"cannot fetch the sample PDF: {error}")
    return CACHE


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
        for page in parsed.document.pages:
            for region in page.regions:
                region.bounding_box.validate_for_page(page.width, page.height)

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
        import adapters.pdfplumber_adapter as adapter
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
        reasons = " ".join(item.reason for item in with_broken_lines.skipped)
        assert "ordered" in reasons
        assert "within page bounds" in reasons

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
