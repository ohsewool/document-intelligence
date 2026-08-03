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

__all__ = [
    "BoundingBox",
    "CaptionRegion",
    "Document",
    "EvidenceCitation",
    "FigureRegion",
    "Page",
    "PageReference",
    "RegionReference",
    "TableRegion",
    "TextRegion",
]
