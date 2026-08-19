"""A citation into transcribed text is not the same promise as one into a text layer.

A page parsed from a PDF's own text objects reproduces what the file says. A
scanned page reproduces what a recogniser guessed. Once the words are in a
string the two are indistinguishable, and a reader following a citation into the
second kind is checking a claim against a transcription without being told.

The model is the only place that distinction can survive: it is lost at the
parser boundary otherwise. So a region records where its text came from, a
transcribed one must carry the recogniser's confidence, and a citation can be
asked which kind it rests on.

**No OCR engine is bundled here.** `transcribed` exists so a parser that does
OCR has somewhere to put what it knows - not as a claim that this library
performs recognition. Every parser wired up in this repository produces
`extracted`, and these tests build transcribed regions by hand, exactly as the
rest of the suite builds any other parser output.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from document_intelligence.model import (
    BoundingBox,
    Document,
    EvidenceCitation,
    PageReference,
    Page,
    RegionReference,
    TextRegion,
)


def box(top: float = 0.1) -> BoundingBox:
    return BoundingBox(0.1, top, 0.9, top + 0.05)


def extracted(identifier: str, top: float = 0.1) -> TextRegion:
    return TextRegion(identifier=identifier, bounding_box=box(top))


def transcribed(identifier: str, confidence: float, top: float = 0.1) -> TextRegion:
    return TextRegion(identifier=identifier, bounding_box=box(top),
                      provenance="transcribed", confidence=confidence)


def document(*regions: TextRegion, citation: EvidenceCitation | None = None) -> Document:
    page = Page(number=1, width=1.0, height=1.0, regions=tuple(regions))
    return Document(identifier="d.pdf", checksum="c" * 8, pages=(page,),
                    evidence=(citation,) if citation else ())


def cite(*region_ids: str) -> EvidenceCitation:
    return EvidenceCitation(
        identifier="claim-1",
        references=tuple(RegionReference(page_number=1, region_identifier=r)
                         for r in region_ids),
    )


class TestARegionSaysWhereItsTextCameFrom:
    def test_extraction_is_the_default(self):
        """Every parser wired up here extracts, so that is what silence means."""
        assert extracted("r1").provenance == "extracted"
        assert extracted("r1").confidence is None

    def test_a_transcription_must_carry_a_confidence(self):
        """The recogniser knew how sure it was. Dropping that on the way in
        turns a guess into a reading."""
        with pytest.raises(ValueError, match="confidence"):
            TextRegion(identifier="r1", bounding_box=box(), provenance="transcribed")

    def test_an_extraction_may_not_claim_one(self):
        """There is nothing to be confident about: it is what the file says."""
        with pytest.raises(ValueError, match="no confidence"):
            TextRegion(identifier="r1", bounding_box=box(), confidence=0.9)

    @pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), float("inf")])
    def test_a_confidence_outside_zero_to_one_is_refused(self, value):
        with pytest.raises(ValueError):
            TextRegion(identifier="r1", bounding_box=box(),
                       provenance="transcribed", confidence=value)

    def test_an_unknown_provenance_is_refused(self):
        with pytest.raises(ValueError, match="provenance"):
            TextRegion(identifier="r1", bounding_box=box(), provenance="invented")

    def test_zero_confidence_is_allowed_and_is_not_absence(self):
        """A recogniser reporting no confidence at all is information."""
        region = transcribed("r1", 0.0)
        assert region.confidence == 0.0


class TestACitationCanBeAskedWhatItRestsOn:
    def test_a_citation_into_extracted_text_says_so(self):
        citation = cite("r1")
        doc = document(extracted("r1"), citation=citation)
        assert doc.citation_provenance(citation) == "extracted"

    def test_a_citation_into_a_transcription_says_so(self):
        citation = cite("r1")
        doc = document(transcribed("r1", 0.82), citation=citation)
        assert doc.citation_provenance(citation) == "transcribed"

    def test_a_citation_resting_on_both_is_mixed(self):
        """Said plainly rather than averaged away: part of it is quotable and
        part of it is a reading."""
        citation = cite("r1", "r2")
        doc = document(extracted("r1"), transcribed("r2", 0.9, top=0.3),
                       citation=citation)
        assert doc.citation_provenance(citation) == "mixed"

    def test_a_page_level_citation_has_nothing_transcribed(self):
        page_citation = EvidenceCitation(identifier="claim-1",
                                         references=(PageReference(page_number=1),))
        doc = document(extracted("r1"), citation=page_citation)
        assert doc.citation_provenance(page_citation) == "extracted"

    def test_the_supporting_regions_are_resolvable(self):
        citation = cite("r1", "r2")
        doc = document(extracted("r1"), extracted("r2", top=0.3), citation=citation)
        assert {r.identifier for r in doc.regions_supporting(citation)} == {"r1", "r2"}


class TestConfidenceIsTheWeakestLink:
    def test_the_lowest_confidence_is_reported(self):
        """A citation is only as checkable as its least certain part."""
        citation = cite("r1", "r2")
        doc = document(transcribed("r1", 0.95), transcribed("r2", 0.41, top=0.3),
                       citation=citation)
        assert doc.lowest_confidence(citation) == 0.41

    def test_a_confident_region_cannot_hide_an_uncertain_one(self):
        """The mean of 0.99 and 0.41 reads as fine. The minimum does not."""
        citation = cite("r1", "r2")
        doc = document(transcribed("r1", 0.99), transcribed("r2", 0.41, top=0.3),
                       citation=citation)
        assert doc.lowest_confidence(citation) < 0.5

    def test_extracted_text_reports_no_confidence(self):
        citation = cite("r1")
        doc = document(extracted("r1"), citation=citation)
        assert doc.lowest_confidence(citation) is None

    def test_a_mixed_citation_reports_the_transcribed_part(self):
        citation = cite("r1", "r2")
        doc = document(extracted("r1"), transcribed("r2", 0.6, top=0.3),
                       citation=citation)
        assert doc.lowest_confidence(citation) == 0.6


class TestNothingHereClaimsToDoOCR:
    def test_the_package_bundles_no_recogniser(self):
        """`transcribed` is a place to record what a recogniser reported, not a
        claim that this library recognises anything."""
        for name in ("pytesseract", "easyocr", "paddleocr"):
            assert name not in (Path(__file__).parents[1] / "requirements.txt").read_text()

    def test_the_bundled_adapter_produces_extracted_regions(self):
        """pdfplumber reads a text layer. Labelling that output `transcribed`
        would invent an uncertainty that does not exist."""
        source = (Path(__file__).parents[1] / "adapters" / "pdfplumber_adapter.py")
        assert "transcribed" not in source.read_text(encoding="utf-8")
