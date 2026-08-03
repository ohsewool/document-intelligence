import unittest

from document_intelligence import (
    BoundingBox, CaptionRegion, Document, EvidenceCitation, FigureRegion,
    Page, PageReference, RegionReference, TableRegion, TextRegion,
)


class DocumentModelTests(unittest.TestCase):
    def setUp(self):
        self.page = Page(1, 600, 800, (
            TextRegion("r1", BoundingBox(0.1, 0.1, 0.5, 0.2)),
            TableRegion("r2", BoundingBox(100, 300, 500, 600, "page")),
            FigureRegion("r3", BoundingBox(0.1, 0.3, 0.8, 0.7)),
            CaptionRegion("r4", BoundingBox(0.1, 0.71, 0.8, 0.78)),
        ))

    def test_valid_construction_and_order_are_preserved(self):
        document = Document("doc", "abc", [self.page])
        self.assertEqual([r.identifier for r in document.pages[0].regions], ["r1", "r2", "r3", "r4"])
        self.assertEqual(document.pages[0].regions[1].region_type, "table")

    def test_invalid_coordinates_and_dimensions(self):
        with self.assertRaises(ValueError): BoundingBox(0, 0, 1.1, 1)
        with self.assertRaises(ValueError): BoundingBox(3, 1, 2, 4, "page")
        with self.assertRaises(ValueError): Page(1, 0, 800)
        with self.assertRaises(ValueError): Page(1, 600, 800, (TextRegion("x", BoundingBox(0, 0, 601, 2, "page")),))

    def test_duplicate_identifiers_are_rejected(self):
        with self.assertRaises(ValueError):
            Page(1, 10, 10, (TextRegion("same", BoundingBox(0, 0, 1, 1, "page")), TextRegion("same", BoundingBox(1, 1, 2, 2, "page"))))
        with self.assertRaises(ValueError): Document("d", "c", (self.page, Page(1, 1, 1)))

    def test_broken_references_are_rejected(self):
        with self.assertRaises(ValueError): Document("d", "c", (self.page,), (EvidenceCitation("e", (PageReference(2),)),))
        with self.assertRaises(ValueError): Document("d", "c", (self.page,), (EvidenceCitation("e", (RegionReference(1, "missing"),)),))

    def test_page_level_evidence(self):
        document = Document("d", "c", (self.page,), (EvidenceCitation("e", (PageReference(1),)),))
        self.assertEqual(document.evidence[0].references, (PageReference(1),))

    def test_bounding_box_evidence(self):
        evidence = EvidenceCitation("e", (RegionReference(1, "r1"),), BoundingBox(0.2, 0.1, 0.4, 0.2))
        self.assertEqual(Document("d", "c", (self.page,), (evidence,)).evidence[0].bounding_box.coordinate_space, "normalized")

    def test_cross_page_evidence(self):
        second = Page(2, 600, 800)
        evidence = EvidenceCitation("e", (PageReference(1), PageReference(2)))
        self.assertEqual(len(Document("d", "c", (self.page, second), (evidence,)).evidence[0].references), 2)


if __name__ == "__main__":
    unittest.main()
