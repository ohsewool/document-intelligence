"""Synthetic tests for deterministic page-coordinate utilities."""

import math
import unittest

from document_intelligence.coordinates import (
    CoordinateError,
    Origin,
    PageBox,
    PageSpace,
    PdfPageTransform,
    Unit,
)


class CoordinateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.pdf_space = PageSpace(100, 200)
        self.box = PageBox(10, 20, 40, 80, self.pdf_space)

    def test_rotation_boxes(self) -> None:
        cases = {
            0: (100, 200, (10, 20, 40, 80)),
            90: (200, 100, (20, 60, 80, 90)),
            180: (100, 200, (60, 120, 90, 180)),
            270: (200, 100, (120, 10, 180, 40)),
        }
        for rotation, (width, height, values) in cases.items():
            with self.subTest(rotation=rotation):
                transformed = PdfPageTransform(100, 200, rotation).forward_box(self.box)
                self.assertEqual((transformed.space.width, transformed.space.height), (width, height))
                self.assertEqual((transformed.left, transformed.bottom, transformed.right, transformed.top), values)

    def test_forward_inverse_round_trip(self) -> None:
        for rotation in (0, 90, 180, 270):
            for origin in (Origin.BOTTOM_LEFT, Origin.TOP_LEFT):
                with self.subTest(rotation=rotation, origin=origin):
                    transform = PdfPageTransform(100, 200, rotation, origin)
                    self.assertEqual(transform.inverse_box(transform.forward_box(self.box)), self.box)
                    point = (12.5, 34.25)
                    self.assertEqual(transform.inverse_point(*transform.forward_point(*point)), point)

    def test_top_left_origin_is_explicit(self) -> None:
        transform = PdfPageTransform(100, 200, 0, Origin.TOP_LEFT)
        self.assertEqual(transform.forward_point(10, 20), (10.0, 180.0))
        self.assertEqual(transform.page_space.origin, Origin.TOP_LEFT)

    def test_units_are_explicit_and_pdf_requires_points(self) -> None:
        pixel_space = PageSpace(100, 200, Origin.TOP_LEFT, Unit.PIXEL)
        self.assertEqual(pixel_space.unit, Unit.PIXEL)
        with self.assertRaises(CoordinateError):
            PdfPageTransform(100, 200, target_unit=Unit.PIXEL)

    def test_clipping_and_boundaries(self) -> None:
        space = PageSpace(100, 200)
        self.assertEqual(PageBox(0, 0, 100, 200, space).clipped_to(), PageBox(0, 0, 100, 200, space))
        self.assertEqual(PageBox(-5, 20, 40, 250, space).clipped_to(), PageBox(0, 20, 40, 200, space))

    def test_wholly_out_of_bounds_is_rejected(self) -> None:
        space = PageSpace(100, 200)
        for values in ((-20, 1, -1, 2), (101, 1, 120, 2), (1, 201, 2, 220)):
            with self.subTest(values=values):
                with self.assertRaises(CoordinateError):
                    PageBox(*values, space).clipped_to()
        with self.assertRaises(CoordinateError):
            PdfPageTransform(100, 200).forward_box(PageBox(101, 1, 120, 2, space))

    def test_non_finite_values_are_rejected(self) -> None:
        for value in (math.inf, -math.inf, math.nan):
            with self.subTest(value=value):
                with self.assertRaises(CoordinateError):
                    PageSpace(value, 1)
                with self.assertRaises(CoordinateError):
                    PageBox(0, 0, value, 1, self.pdf_space)

    def test_invalid_dimensions_rotations_and_boxes_are_rejected(self) -> None:
        for dimensions in ((0, 1), (-1, 1), (1, 0)):
            with self.subTest(dimensions=dimensions):
                with self.assertRaises(CoordinateError):
                    PageSpace(*dimensions)
        for rotation in (-90, 45, 360, 90.0):
            with self.subTest(rotation=rotation):
                with self.assertRaises(CoordinateError):
                    PdfPageTransform(100, 200, rotation)
        with self.assertRaises(CoordinateError):
            PageBox(1, 1, 1, 2, self.pdf_space)


if __name__ == "__main__":
    unittest.main()
