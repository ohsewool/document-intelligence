"""Immutable, parser-independent document evidence data model."""

from .model import (
    BoundingBox,
    CaptionRegion,
    Document,
    EvidenceCitation,
    FigureRegion,
    Page,
    PageReference,
    RegionReference,
    TableRegion,
    TextRegion,
)
from .hierarchy import (
    DocumentHierarchy,
    DocumentReference,
    PageHierarchyReference,
    RegionHierarchyReference,
    SectionReference,
    validate_document_hierarchy,
)

__all__ = [
    "BoundingBox",
    "CaptionRegion",
    "Document",
    "DocumentHierarchy",
    "DocumentReference",
    "EvidenceCitation",
    "FigureRegion",
    "Page",
    "PageHierarchyReference",
    "PageReference",
    "RegionReference",
    "RegionHierarchyReference",
    "SectionReference",
    "TableRegion",
    "TextRegion",
    "validate_document_hierarchy",
]

# The place a caller who knows the real reading order records and validates it.
# The bundled adapter cannot produce one - it orders by vertical position and
# says so - so this is exported rather than wired in.
from .reading_order import ReadingOrder, ReadingOrderLink, validate_reading_order  # noqa: E402,F401
