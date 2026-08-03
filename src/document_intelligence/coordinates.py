"""Deterministic, parser-independent page-coordinate utilities.

All coordinates use a page-local Cartesian space.  The declared origin is
explicit so callers never need to infer whether ``y`` increases upward or
downward.  A transform maps PDF-space boxes into a declared page space while
accounting for the PDF page's right-angle rotation.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class CoordinateError(ValueError):
    """Raised when coordinates, dimensions, or transforms are invalid."""


class Origin(str, Enum):
    """Supported page-coordinate origins."""

    BOTTOM_LEFT = "bottom_left"
    TOP_LEFT = "top_left"


class Unit(str, Enum):
    """Supported coordinate units."""

    POINT = "point"
    PIXEL = "pixel"


def _finite(value: float, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise CoordinateError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise CoordinateError(f"{name} must be finite")
    return result


def _rotation(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value not in (0, 90, 180, 270):
        raise CoordinateError("rotation must be one of 0, 90, 180, or 270")
    return value


@dataclass(frozen=True, slots=True)
class PageSpace:
    """A bounded page-local coordinate space with an explicit convention."""

    width: float
    height: float
    origin: Origin = Origin.BOTTOM_LEFT
    unit: Unit = Unit.POINT

    def __post_init__(self) -> None:
        width = _finite(self.width, "width")
        height = _finite(self.height, "height")
        if width <= 0 or height <= 0:
            raise CoordinateError("page dimensions must be greater than zero")
        if not isinstance(self.origin, Origin):
            raise CoordinateError("origin must be an Origin")
        if not isinstance(self.unit, Unit):
            raise CoordinateError("unit must be a Unit")
        object.__setattr__(self, "width", width)
        object.__setattr__(self, "height", height)


@dataclass(frozen=True, slots=True)
class PageBox:
    """An axis-aligned box in a particular :class:`PageSpace`."""

    left: float
    bottom: float
    right: float
    top: float
    space: PageSpace

    def __post_init__(self) -> None:
        left = _finite(self.left, "left")
        bottom = _finite(self.bottom, "bottom")
        right = _finite(self.right, "right")
        top = _finite(self.top, "top")
        if not isinstance(self.space, PageSpace):
            raise CoordinateError("space must be a PageSpace")
        if right <= left or top <= bottom:
            raise CoordinateError("box must have positive width and height")
        object.__setattr__(self, "left", left)
        object.__setattr__(self, "bottom", bottom)
        object.__setattr__(self, "right", right)
        object.__setattr__(self, "top", top)

    def clipped_to(self, space: PageSpace | None = None) -> "PageBox":
        """Return this box clipped to *space*, rejecting no-overlap boxes."""
        target = self.space if space is None else space
        if target != self.space:
            raise CoordinateError("clip space must match the box space")
        left = max(self.left, 0.0)
        bottom = max(self.bottom, 0.0)
        right = min(self.right, target.width)
        top = min(self.top, target.height)
        if right <= left or top <= bottom:
            raise CoordinateError("box is wholly outside page bounds")
        return PageBox(left, bottom, right, top, target)


@dataclass(frozen=True, slots=True)
class PdfPageTransform:
    """Map unrotated PDF points into a declared page space.

    The input PDF space is measured in points from the bottom-left corner.
    ``rotation`` is clockwise, matching the PDF page rotation convention.
    The target must use points; conversion to pixels is deliberately explicit
    and outside this parser-independent utility.
    """

    pdf_width: float
    pdf_height: float
    rotation: int = 0
    target_origin: Origin = Origin.BOTTOM_LEFT
    target_unit: Unit = Unit.POINT

    def __post_init__(self) -> None:
        width = _finite(self.pdf_width, "pdf_width")
        height = _finite(self.pdf_height, "pdf_height")
        if width <= 0 or height <= 0:
            raise CoordinateError("PDF dimensions must be greater than zero")
        if not isinstance(self.target_origin, Origin):
            raise CoordinateError("target_origin must be an Origin")
        if self.target_unit is not Unit.POINT:
            raise CoordinateError("PDF transforms require point target units")
        object.__setattr__(self, "pdf_width", width)
        object.__setattr__(self, "pdf_height", height)
        object.__setattr__(self, "rotation", _rotation(self.rotation))

    @property
    def page_space(self) -> PageSpace:
        if self.rotation in (0, 180):
            width, height = self.pdf_width, self.pdf_height
        else:
            width, height = self.pdf_height, self.pdf_width
        return PageSpace(width, height, self.target_origin, self.target_unit)

    def forward_point(self, x: float, y: float) -> tuple[float, float]:
        """Map one PDF-space point into the declared page space."""
        x, y = _finite(x, "x"), _finite(y, "y")
        w, h = self.pdf_width, self.pdf_height
        if self.rotation == 0:
            tx, ty = x, y
        elif self.rotation == 90:
            tx, ty = y, w - x
        elif self.rotation == 180:
            tx, ty = w - x, h - y
        else:
            tx, ty = h - y, x
        if self.target_origin is Origin.TOP_LEFT:
            ty = self.page_space.height - ty
        return tx, ty

    def inverse_point(self, x: float, y: float) -> tuple[float, float]:
        """Map one declared page-space point back to unrotated PDF space."""
        x, y = _finite(x, "x"), _finite(y, "y")
        if self.target_origin is Origin.TOP_LEFT:
            y = self.page_space.height - y
        w, h = self.pdf_width, self.pdf_height
        if self.rotation == 0:
            return x, y
        if self.rotation == 90:
            return w - y, x
        if self.rotation == 180:
            return w - x, h - y
        return y, h - x

    def forward_box(self, box: PageBox, *, clip: bool = False) -> PageBox:
        """Map a PDF-space box into :attr:`page_space`.

        The input must be in unrotated bottom-left PDF points.  Set ``clip``
        to reject-free clip a partially overlapping box; wholly outside boxes
        are always rejected.
        """
        expected = PageSpace(self.pdf_width, self.pdf_height, Origin.BOTTOM_LEFT, Unit.POINT)
        if box.space != expected:
            raise CoordinateError("box must use the unrotated PDF point space")
        # Validate overlap even when the caller wants an unclipped result.
        # This makes a wholly out-of-bounds source box unrepresentable here.
        box.clipped_to()
        points = (
            self.forward_point(box.left, box.bottom),
            self.forward_point(box.left, box.top),
            self.forward_point(box.right, box.bottom),
            self.forward_point(box.right, box.top),
        )
        xs, ys = zip(*points)
        result = PageBox(min(xs), min(ys), max(xs), max(ys), self.page_space)
        return result.clipped_to() if clip else result

    def inverse_box(self, box: PageBox) -> PageBox:
        """Map a declared page-space box back to unrotated PDF points."""
        if box.space != self.page_space:
            raise CoordinateError("box must use this transform's page space")
        points = (
            self.inverse_point(box.left, box.bottom),
            self.inverse_point(box.left, box.top),
            self.inverse_point(box.right, box.bottom),
            self.inverse_point(box.right, box.top),
        )
        xs, ys = zip(*points)
        return PageBox(
            min(xs), min(ys), max(xs), max(ys),
            PageSpace(self.pdf_width, self.pdf_height, Origin.BOTTOM_LEFT, Unit.POINT),
        )
