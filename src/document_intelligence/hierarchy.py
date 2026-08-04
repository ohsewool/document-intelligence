"""Immutable, explicitly supplied document hierarchy records.

This module validates only caller-provided identifiers and parent links.  It
does not inspect PDFs or infer structure from layout.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


def _identifier(value: str, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _position(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("position must be a non-negative integer")
    return value


@dataclass(frozen=True, slots=True)
class DocumentReference:
    """The immutable identifier of one synthetic document."""

    document_id: str

    def __post_init__(self) -> None:
        _identifier(self.document_id, "document_id")


@dataclass(frozen=True, slots=True)
class SectionReference:
    """A section owned by a document and optionally nested in another section."""

    document_id: str
    section_id: str
    parent_section_id: str | None = None
    position: int = 0

    def __post_init__(self) -> None:
        _identifier(self.document_id, "document_id")
        _identifier(self.section_id, "section_id")
        if self.parent_section_id is not None:
            _identifier(self.parent_section_id, "parent_section_id")
        _position(self.position)


@dataclass(frozen=True, slots=True)
class PageHierarchyReference:
    """A synthetic page owned by a document and parented by a section."""

    document_id: str
    page_id: str
    parent_section_id: str
    position: int = 0

    def __post_init__(self) -> None:
        _identifier(self.document_id, "document_id")
        _identifier(self.page_id, "page_id")
        _identifier(self.parent_section_id, "parent_section_id")
        _position(self.position)


@dataclass(frozen=True, slots=True)
class RegionHierarchyReference:
    """A synthetic region owned by a document page."""

    document_id: str
    page_id: str
    region_id: str
    position: int = 0

    def __post_init__(self) -> None:
        _identifier(self.document_id, "document_id")
        _identifier(self.page_id, "page_id")
        _identifier(self.region_id, "region_id")
        _position(self.position)


@dataclass(frozen=True, slots=True)
class DocumentHierarchy:
    """One validated hierarchy, retained exactly in supplied sequence order."""

    document: DocumentReference
    sections: tuple[SectionReference, ...] = ()
    pages: tuple[PageHierarchyReference, ...] = ()
    regions: tuple[RegionHierarchyReference, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.document, DocumentReference):
            raise TypeError("document must be a DocumentReference")
        for name in ("sections", "pages", "regions"):
            value = getattr(self, name)
            if not isinstance(value, tuple):
                object.__setattr__(self, name, tuple(value))
        self._validate()

    def _validate(self) -> None:
        if any(not isinstance(item, SectionReference) for item in self.sections):
            raise TypeError("sections must contain only SectionReference instances")
        if any(not isinstance(item, PageHierarchyReference) for item in self.pages):
            raise TypeError("pages must contain only PageHierarchyReference instances")
        if any(not isinstance(item, RegionHierarchyReference) for item in self.regions):
            raise TypeError("regions must contain only RegionHierarchyReference instances")

        document_id = self.document.document_id
        if any(item.document_id != document_id for item in (*self.sections, *self.pages, *self.regions)):
            raise ValueError("hierarchy reference is owned by a different document")

        section_ids = [item.section_id for item in self.sections]
        page_ids = [item.page_id for item in self.pages]
        region_keys = [(item.page_id, item.region_id) for item in self.regions]
        if len(section_ids) != len(set(section_ids)):
            raise ValueError("section identifiers must be unique within a document")
        if len(page_ids) != len(set(page_ids)):
            raise ValueError("page identifiers must be unique within a document")
        if len(region_keys) != len(set(region_keys)):
            raise ValueError("region identifiers must be unique within a page")

        sections = {item.section_id: item for item in self.sections}
        pages = set(page_ids)
        for section in self.sections:
            if section.parent_section_id is not None and section.parent_section_id not in sections:
                raise ValueError("section references a missing parent section")
        for page in self.pages:
            if page.parent_section_id not in sections:
                raise ValueError("page references a missing parent section")
        for region in self.regions:
            if region.page_id not in pages:
                raise ValueError("region references a missing parent page")

        for section in self.sections:
            seen: set[str] = set()
            current = section
            while current.parent_section_id is not None:
                if current.section_id in seen:
                    raise ValueError("section parentage contains a cycle")
                seen.add(current.section_id)
                current = sections[current.parent_section_id]

        sibling_positions: dict[tuple[str, str | None], set[int]] = {}
        for section in self.sections:
            key = ("section", section.parent_section_id)
            sibling_positions.setdefault(key, set())
            if section.position in sibling_positions[key]:
                raise ValueError("hierarchy siblings must have unique positions")
            sibling_positions[key].add(section.position)
        for page in self.pages:
            key = ("page", page.parent_section_id)
            sibling_positions.setdefault(key, set())
            if page.position in sibling_positions[key]:
                raise ValueError("hierarchy siblings must have unique positions")
            sibling_positions[key].add(page.position)
        for region in self.regions:
            key = ("region", region.page_id)
            sibling_positions.setdefault(key, set())
            if region.position in sibling_positions[key]:
                raise ValueError("hierarchy siblings must have unique positions")
            sibling_positions[key].add(region.position)

    @classmethod
    def validate(
        cls,
        document: DocumentReference,
        sections: Iterable[SectionReference] = (),
        pages: Iterable[PageHierarchyReference] = (),
        regions: Iterable[RegionHierarchyReference] = (),
    ) -> "DocumentHierarchy":
        """Validate explicitly supplied references and retain their order."""
        return cls(document, tuple(sections), tuple(pages), tuple(regions))


def validate_document_hierarchy(
    document: DocumentReference,
    sections: Iterable[SectionReference] = (),
    pages: Iterable[PageHierarchyReference] = (),
    regions: Iterable[RegionHierarchyReference] = (),
) -> DocumentHierarchy:
    """Convenience wrapper for :meth:`DocumentHierarchy.validate`."""
    return DocumentHierarchy.validate(document, sections, pages, regions)
