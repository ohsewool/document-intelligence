"""Deterministic tests for synthetic page-region reading order."""

import unittest

from document_intelligence.reading_order import (
    ReadingOrder,
    ReadingOrderLink,
    RegionReference,
    validate_reading_order,
)


class ReadingOrderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pages = {"page-1": ("p1-r1", "p1-r2"), "page-2": ("p2-r1",)}
        self.first = RegionReference("page-1", "p1-r1")
        self.second = RegionReference("page-1", "p1-r2")
        self.third = RegionReference("page-2", "p2-r1")

    def test_valid_within_page_sequence(self) -> None:
        order = ReadingOrder.validate(
            {"page-1": ("p1-r1", "p1-r2")},
            (ReadingOrderLink(self.first, self.second), ReadingOrderLink(self.second)),
        )
        self.assertEqual(order.regions, (self.first, self.second))

    def test_valid_cross_page_sequence(self) -> None:
        order = validate_reading_order(
            self.pages,
            (
                ReadingOrderLink(self.first, self.second),
                ReadingOrderLink(self.second, self.third),
                ReadingOrderLink(self.third),
            ),
        )
        self.assertEqual(order.links[1].next_region, self.third)

    def test_preserves_supplied_link_order(self) -> None:
        supplied = (
            ReadingOrderLink(self.second, self.third),
            ReadingOrderLink(self.first, self.second),
            ReadingOrderLink(self.third),
        )
        self.assertEqual(ReadingOrder.validate(self.pages, supplied).links, supplied)

    def test_rejects_duplicate_regions(self) -> None:
        with self.assertRaises(ValueError):
            ReadingOrder.validate(self.pages, (ReadingOrderLink(self.first), ReadingOrderLink(self.first)))

    def test_rejects_ownership_mismatch(self) -> None:
        wrong_page = RegionReference("page-2", "p1-r1")
        with self.assertRaisesRegex(ValueError, "ownership mismatch"):
            ReadingOrder.validate(self.pages, (ReadingOrderLink(wrong_page),))

    def test_rejects_broken_reference(self) -> None:
        missing = RegionReference("page-1", "missing")
        with self.assertRaisesRegex(ValueError, "missing region"):
            ReadingOrder.validate(self.pages, (ReadingOrderLink(self.first, missing),))

    def test_rejects_unlisted_adjacency_target(self) -> None:
        with self.assertRaisesRegex(ValueError, "unlisted region"):
            ReadingOrder.validate(self.pages, (ReadingOrderLink(self.first, self.second),))

    def test_rejects_cycle(self) -> None:
        with self.assertRaises(ValueError):
            ReadingOrder.validate(
                self.pages,
                (ReadingOrderLink(self.first, self.second), ReadingOrderLink(self.second, self.first)),
            )

    def test_validation_is_stable(self) -> None:
        links = (ReadingOrderLink(self.first, self.second), ReadingOrderLink(self.second))
        self.assertEqual(ReadingOrder.validate(self.pages, links), ReadingOrder.validate(self.pages, links))

    def test_rejects_strict_invalid_inputs(self) -> None:
        with self.assertRaises(TypeError):
            ReadingOrder.validate([], ())
        with self.assertRaises(ValueError):
            RegionReference("", "region")
        with self.assertRaises(TypeError):
            ReadingOrderLink(self.first, "page-1/p1-r2")


if __name__ == "__main__":
    unittest.main()
