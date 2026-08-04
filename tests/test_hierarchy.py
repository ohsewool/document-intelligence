"""Synthetic tests for explicitly supplied document hierarchy records."""

import unittest

from document_intelligence.hierarchy import (
    DocumentHierarchy,
    DocumentReference,
    PageHierarchyReference,
    RegionHierarchyReference,
    SectionReference,
    validate_document_hierarchy,
)


class DocumentHierarchyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = DocumentReference("document-1")
        self.sections = (
            SectionReference("document-1", "intro", position=0),
            SectionReference("document-1", "methods", "intro", 0),
        )
        self.pages = (
            PageHierarchyReference("document-1", "page-1", "intro", 0),
            PageHierarchyReference("document-1", "page-2", "methods", 0),
        )
        self.regions = (
            RegionHierarchyReference("document-1", "page-1", "region-1", 0),
            RegionHierarchyReference("document-1", "page-1", "region-2", 1),
            RegionHierarchyReference("document-1", "page-2", "region-3", 0),
        )

    def test_valid_tree_is_preserved_exactly(self) -> None:
        hierarchy = validate_document_hierarchy(self.document, self.sections, self.pages, self.regions)
        self.assertEqual(hierarchy.sections, self.sections)
        self.assertEqual(hierarchy.pages, self.pages)
        self.assertEqual(hierarchy.regions, self.regions)

    def test_rejects_orphaned_page_and_region(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing parent section"):
            DocumentHierarchy(self.document, pages=(PageHierarchyReference("document-1", "page-1", "none"),))
        with self.assertRaisesRegex(ValueError, "missing parent page"):
            DocumentHierarchy(self.document, regions=(RegionHierarchyReference("document-1", "none", "region-1"),))

    def test_rejects_duplicate_identifiers_and_positions(self) -> None:
        with self.assertRaisesRegex(ValueError, "section identifiers"):
            DocumentHierarchy(self.document, (SectionReference("document-1", "one"), SectionReference("document-1", "one", position=1)))
        with self.assertRaisesRegex(ValueError, "unique positions"):
            DocumentHierarchy(self.document, (SectionReference("document-1", "one"), SectionReference("document-1", "two")))

    def test_rejects_invalid_parentage_and_document_ownership(self) -> None:
        with self.assertRaisesRegex(ValueError, "different document"):
            DocumentHierarchy(self.document, (SectionReference("document-2", "other"),))
        with self.assertRaisesRegex(ValueError, "missing parent section"):
            DocumentHierarchy(self.document, (SectionReference("document-1", "child", "missing"),))

    def test_rejects_section_cycles(self) -> None:
        with self.assertRaisesRegex(ValueError, "cycle"):
            DocumentHierarchy(
                self.document,
                (
                    SectionReference("document-1", "one", "two"),
                    SectionReference("document-1", "two", "one"),
                ),
            )


if __name__ == "__main__":
    unittest.main()
