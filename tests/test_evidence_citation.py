"""Evidence citations: the part citation grounding depends on.

A citation is a promise that a claim can be traced to a place in a document. The
model enforces the parts of that promise it can check — that the place exists,
that a box belongs to exactly one target, that identifiers are not reused — so
grounding can rely on them rather than re-checking.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from document_intelligence import (
    BoundingBox,
    Document,
    EvidenceCitation,
    Page,
    PageReference,
    RegionReference,
    TableRegion,
    TextRegion,
)


def box(top=0.1):
    return BoundingBox(left=0.1, top=top, right=0.9, bottom=top + 0.1)


def page(number=1, regions=None):
    return Page(number=number, width=612.0, height=792.0,
                regions=tuple(regions if regions is not None else
                              [TextRegion(identifier=f"p{number}-body", bounding_box=box())]))


def document(pages=None, evidence=()):
    return Document(identifier="report", checksum="c" * 64,
                    pages=tuple(pages or [page()]), evidence=tuple(evidence))


class TestReferenceValidity:
    def test_a_page_reference_needs_a_real_page_number(self):
        assert PageReference(3).page_number == 3

    @pytest.mark.parametrize("number", [0, -1])
    def test_a_non_positive_page_is_refused(self, number):
        with pytest.raises(ValueError):
            PageReference(number)

    def test_a_boolean_is_not_a_page_number(self):
        """True == 1 in Python; accepting it would let a flag become a citation."""
        with pytest.raises(ValueError):
            PageReference(True)

    def test_a_region_reference_needs_an_identifier(self):
        with pytest.raises(ValueError):
            RegionReference(1, "")

    def test_a_region_reference_carries_its_page(self):
        reference = RegionReference(2, "p2-table")
        assert reference.page_number == 2
        assert reference.region_identifier == "p2-table"


class TestCitationShape:
    def test_a_citation_needs_at_least_one_reference(self):
        """A citation that points nowhere is not a citation."""
        with pytest.raises(ValueError):
            EvidenceCitation(identifier="e1", references=())

    def test_a_citation_needs_an_identifier(self):
        with pytest.raises(ValueError):
            EvidenceCitation(identifier="", references=(PageReference(1),))

    def test_references_are_normalised_to_a_tuple(self):
        citation = EvidenceCitation(identifier="e1", references=[PageReference(1)])
        assert isinstance(citation.references, tuple)

    def test_a_citation_may_span_pages(self):
        citation = EvidenceCitation(
            identifier="e1", references=(PageReference(1), PageReference(2)))
        assert len(citation.references) == 2

    def test_only_page_and_region_references_are_accepted(self):
        with pytest.raises(ValueError):
            EvidenceCitation(identifier="e1", references=("page 1",))


class TestBoundingBoxCitations:
    def test_a_box_may_accompany_a_single_reference(self):
        citation = EvidenceCitation(
            identifier="e1", references=(RegionReference(1, "p1-body"),), bounding_box=box())
        assert citation.bounding_box == box()

    def test_a_box_cannot_describe_two_places_at_once(self):
        """One rectangle cannot be on two pages; allowing it would be a false promise."""
        with pytest.raises(ValueError):
            EvidenceCitation(
                identifier="e1",
                references=(PageReference(1), PageReference(2)),
                bounding_box=box(),
            )


class TestDocumentConsistency:
    def test_evidence_may_reference_a_page_the_document_owns(self):
        citation = EvidenceCitation(identifier="e1", references=(PageReference(1),))
        assert document(evidence=[citation]).evidence[0].identifier == "e1"

    def test_evidence_referencing_an_absent_page_is_refused(self):
        """The check grounding relies on: a citation cannot invent a location."""
        citation = EvidenceCitation(identifier="e1", references=(PageReference(9),))
        with pytest.raises(ValueError):
            document(evidence=[citation])

    def test_duplicate_citation_identifiers_are_refused(self):
        first = EvidenceCitation(identifier="e1", references=(PageReference(1),))
        second = EvidenceCitation(identifier="e1", references=(PageReference(1),))
        with pytest.raises(ValueError):
            document(evidence=[first, second])

    def test_duplicate_page_numbers_are_refused(self):
        with pytest.raises(ValueError):
            document(pages=[page(1), page(1)])

    def test_duplicate_region_identifiers_within_a_page_are_refused(self):
        with pytest.raises(ValueError):
            page(regions=[TextRegion(identifier="same", bounding_box=box(0.1)),
                          TableRegion(identifier="same", bounding_box=box(0.4))])

    def test_the_same_region_identifier_may_recur_on_another_page(self):
        """Uniqueness is per page, so `body` on every page is legitimate."""
        pages = [page(1, [TextRegion(identifier="body", bounding_box=box())]),
                 page(2, [TextRegion(identifier="body", bounding_box=box())])]
        assert len(document(pages=pages).pages) == 2

    def test_a_document_needs_an_identifier_and_checksum(self):
        with pytest.raises(ValueError):
            Document(identifier="", checksum="c" * 64, pages=(page(),))
        with pytest.raises(ValueError):
            Document(identifier="report", checksum="", pages=(page(),))


class TestImmutability:
    def test_a_citation_cannot_be_edited_after_construction(self):
        """Evidence that can be rewritten in place is not evidence."""
        citation = EvidenceCitation(identifier="e1", references=(PageReference(1),))
        with pytest.raises(Exception):
            citation.identifier = "e2"

    def test_a_region_cannot_be_moved_after_construction(self):
        region = TextRegion(identifier="p1-body", bounding_box=box())
        with pytest.raises(Exception):
            region.bounding_box = box(0.5)
