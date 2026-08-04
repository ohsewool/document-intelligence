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
