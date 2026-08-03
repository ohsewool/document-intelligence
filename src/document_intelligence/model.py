"""Small immutable data model for layout-preserving document evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from numbers import Real
from typing import Literal, TypeAlias


CoordinateSpace: TypeAlias = Literal["normalized", "page"]
RegionType: TypeAlias = Literal["text", "table", "figure", "caption"]


@dataclass(frozen=True, slots=True)
class BoundingBox:
    """An ordered rectangle in normalized (0..1) or page-space coordinates."""

    left: float
    top: float
    right: float
    bottom: float
    coordinate_space: CoordinateSpace = "normalized"

    def __post_init__(self) -> None:
        if self.coordinate_space not in ("normalized", "page"):
            raise ValueError("coordinate_space must be 'normalized' or 'page'")
        values = (self.left, self.top, self.right, self.bottom)
        if not all(isinstance(value, Real) and isfinite(value) for value in values):
            raise ValueError("bounding-box coordinates must be finite")
        if not self.left < self.right or not self.top < self.bottom:
            raise ValueError("bounding-box coordinates must be ordered")
        if self.coordinate_space == "normalized" and not (
            0 <= self.left and self.right <= 1 and 0 <= self.top and self.bottom <= 1
        ):
            raise ValueError("normalized bounding-box coordinates must be within 0..1")

    def validate_for_page(self, width: float, height: float) -> None:
        """Ensure this box is contained by a page with the given dimensions."""
        if self.coordinate_space == "page" and not (
            0 <= self.left and self.right <= width and 0 <= self.top and self.bottom <= height
        ):
            raise ValueError("page-space bounding box must be within page bounds")


@dataclass(frozen=True, slots=True)
class _Region:
    identifier: str
    bounding_box: BoundingBox
    region_type: RegionType = field(init=False)

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError("region identifier must not be empty")


@dataclass(frozen=True, slots=True)
class TextRegion(_Region):
    region_type: Literal["text"] = field(init=False, default="text")


@dataclass(frozen=True, slots=True)
class TableRegion(_Region):
    region_type: Literal["table"] = field(init=False, default="table")


@dataclass(frozen=True, slots=True)
class FigureRegion(_Region):
    region_type: Literal["figure"] = field(init=False, default="figure")


@dataclass(frozen=True, slots=True)
class CaptionRegion(_Region):
    region_type: Literal["caption"] = field(init=False, default="caption")


Region: TypeAlias = TextRegion | TableRegion | FigureRegion | CaptionRegion


@dataclass(frozen=True, slots=True)
class Page:
    number: int
    width: float
    height: float
    regions: tuple[Region, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.number, bool) or not isinstance(self.number, int) or self.number < 1:
            raise ValueError("page number must be a positive integer")
        if not all(isinstance(value, Real) and isfinite(value) and value > 0 for value in (self.width, self.height)):
            raise ValueError("page dimensions must be finite and positive")
        if not isinstance(self.regions, tuple):
            object.__setattr__(self, "regions", tuple(self.regions))
        identifiers = [region.identifier for region in self.regions]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("region identifiers must be unique within a page")
        for region in self.regions:
            region.bounding_box.validate_for_page(self.width, self.height)


@dataclass(frozen=True, slots=True)
class PageReference:
    page_number: int

    def __post_init__(self) -> None:
        if isinstance(self.page_number, bool) or not isinstance(self.page_number, int) or self.page_number < 1:
            raise ValueError("referenced page number must be a positive integer")


@dataclass(frozen=True, slots=True)
class RegionReference:
    page_number: int
    region_identifier: str

    def __post_init__(self) -> None:
        PageReference(self.page_number)
        if not self.region_identifier:
            raise ValueError("referenced region identifier must not be empty")


EvidenceTarget: TypeAlias = PageReference | RegionReference


@dataclass(frozen=True, slots=True)
class EvidenceCitation:
    identifier: str
    references: tuple[EvidenceTarget, ...]
    bounding_box: BoundingBox | None = None

    def __post_init__(self) -> None:
        if not self.identifier:
            raise ValueError("evidence citation identifier must not be empty")
        if not isinstance(self.references, tuple):
            object.__setattr__(self, "references", tuple(self.references))
        if not self.references:
            raise ValueError("evidence citation must reference at least one page or region")
        if not all(isinstance(reference, (PageReference, RegionReference)) for reference in self.references):
            raise ValueError("evidence references must be page or region references")
        if self.bounding_box is not None and len(self.references) != 1:
            raise ValueError("bounding-box evidence must have exactly one reference")


@dataclass(frozen=True, slots=True)
class Document:
    identifier: str
    checksum: str
    pages: tuple[Page, ...]
    evidence: tuple[EvidenceCitation, ...] = ()

    def __post_init__(self) -> None:
        if not self.identifier or not self.checksum:
            raise ValueError("document identifier and checksum must not be empty")
        if not isinstance(self.pages, tuple):
            object.__setattr__(self, "pages", tuple(self.pages))
        if not isinstance(self.evidence, tuple):
            object.__setattr__(self, "evidence", tuple(self.evidence))
        page_numbers = [page.number for page in self.pages]
        if len(page_numbers) != len(set(page_numbers)):
            raise ValueError("page numbers must be unique")
        evidence_ids = [citation.identifier for citation in self.evidence]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError("evidence citation identifiers must be unique")
        pages = {page.number: page for page in self.pages}
        for citation in self.evidence:
            for reference in citation.references:
                page = pages.get(reference.page_number)
                if page is None:
                    raise ValueError("evidence references a page not owned by the document")
                if isinstance(reference, RegionReference) and not any(
                    region.identifier == reference.region_identifier for region in page.regions
                ):
                    raise ValueError("evidence references a region not owned by its page")
            if citation.bounding_box is not None:
                citation.bounding_box.validate_for_page(
                    pages[citation.references[0].page_number].width,
                    pages[citation.references[0].page_number].height,
                )
