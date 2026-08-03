"""Deterministic validation for explicitly supplied synthetic reading order.

The model deliberately operates only on page and region identifiers.  It does
not infer layout or inspect a document; callers supply every reading-order
edge explicitly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


@dataclass(frozen=True, order=True)
class RegionReference:
    """A region identity qualified by its synthetic source page identity."""

    page_id: str
    region_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.page_id, str) or not self.page_id:
            raise ValueError("page_id must be a non-empty string")
        if not isinstance(self.region_id, str) or not self.region_id:
            raise ValueError("region_id must be a non-empty string")


@dataclass(frozen=True)
class ReadingOrderLink:
    """One supplied directed adjacency, optionally terminating a sequence."""

    region: RegionReference
    next_region: RegionReference | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.region, RegionReference):
            raise TypeError("region must be a RegionReference")
        if self.next_region is not None and not isinstance(
            self.next_region, RegionReference
        ):
            raise TypeError("next_region must be a RegionReference or None")


@dataclass(frozen=True)
class ReadingOrder:
    """A validated supplied reading order, retained in caller-provided order."""

    links: tuple[ReadingOrderLink, ...]

    @classmethod
    def validate(
        cls,
        page_regions: Mapping[str, Iterable[str]],
        links: Iterable[ReadingOrderLink],
    ) -> "ReadingOrder":
        """Validate supplied links and return them unchanged in supplied order.

        ``page_regions`` is the authoritative synthetic ownership map.  A
        region reference is valid only when its page exists and that exact
        region identifier belongs to the page.  Every listed region has one
        link, target references must also be listed, and the resulting graph
        must be a single acyclic sequence.  Therefore each adjacency is
        deterministic, including adjacencies that cross page boundaries.
        """
        if not isinstance(page_regions, Mapping):
            raise TypeError("page_regions must be a mapping")

        ownership: dict[str, frozenset[str]] = {}
        all_regions: set[str] = set()
        for page_id, region_ids in page_regions.items():
            if not isinstance(page_id, str) or not page_id:
                raise ValueError("page identifiers must be non-empty strings")
            if page_id in ownership:
                raise ValueError("page identifiers must be unique")
            try:
                identifiers = tuple(region_ids)
            except TypeError as exc:
                raise TypeError("page regions must be iterable") from exc
            if any(not isinstance(region_id, str) or not region_id for region_id in identifiers):
                raise ValueError("region identifiers must be non-empty strings")
            if len(set(identifiers)) != len(identifiers):
                raise ValueError("region identifiers must be unique within a page")
            ownership[page_id] = frozenset(identifiers)
            all_regions.update(identifiers)

        supplied_links = tuple(links)
        if not supplied_links:
            raise ValueError("reading order must contain at least one link")
        if any(not isinstance(link, ReadingOrderLink) for link in supplied_links):
            raise TypeError("links must contain only ReadingOrderLink instances")

        def require_owned(reference: RegionReference) -> None:
            if reference.page_id not in ownership:
                raise ValueError("reading-order reference has an unknown page")
            if reference.region_id not in ownership[reference.page_id]:
                if reference.region_id in all_regions:
                    raise ValueError("reading-order reference has a region ownership mismatch")
                raise ValueError("reading-order reference names a missing region")

        regions = tuple(link.region for link in supplied_links)
        if len(set(regions)) != len(regions):
            raise ValueError("reading-order regions must be unique")
        for link in supplied_links:
            require_owned(link.region)
            if link.next_region is not None:
                require_owned(link.next_region)

        listed_regions = set(regions)
        for link in supplied_links:
            if link.next_region is not None and link.next_region not in listed_regions:
                raise ValueError("reading-order adjacency references an unlisted region")

        incoming: dict[RegionReference, int] = {region: 0 for region in regions}
        outgoing: dict[RegionReference, RegionReference] = {}
        terminals = 0
        for link in supplied_links:
            if link.next_region is None:
                terminals += 1
                continue
            outgoing[link.region] = link.next_region
            incoming[link.next_region] += 1
            if incoming[link.next_region] > 1:
                raise ValueError("reading-order region has multiple predecessors")
        if terminals != 1:
            raise ValueError("reading order must have exactly one terminal region")

        starts = [region for region in regions if incoming[region] == 0]
        if len(starts) != 1:
            raise ValueError("reading order must have exactly one initial region")
        visited: set[RegionReference] = set()
        current: RegionReference | None = starts[0]
        while current is not None:
            if current in visited:
                raise ValueError("reading-order adjacency contains a cycle")
            visited.add(current)
            current = outgoing.get(current)
        if len(visited) != len(regions):
            raise ValueError("reading-order adjacency contains a cycle or disconnected sequence")
        return cls(supplied_links)

    @property
    def regions(self) -> tuple[RegionReference, ...]:
        """The region-link sources in exactly the supplied order."""
        return tuple(link.region for link in self.links)


def validate_reading_order(
    page_regions: Mapping[str, Iterable[str]],
    links: Iterable[ReadingOrderLink],
) -> ReadingOrder:
    """Convenience wrapper for :meth:`ReadingOrder.validate`."""
    return ReadingOrder.validate(page_regions, links)
