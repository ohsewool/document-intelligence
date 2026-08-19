"""Turn a pdfplumber parse into the evidence model.

This repository's claim is that the model takes whatever a parser produced and
validates it the same way. Until now the only parser was the test fixtures,
which is not a test of that claim - fixtures are written to fit. This adapter
runs a real PDF through a real parser and hands the result to the model
unmodified, so the model's rules meet coordinates it did not choose.

The adapter deliberately does no repair. If pdfplumber emits a zero-height line
or a word extending past the page edge, that reaches the model and the model
refuses it. Silently correcting such a box would make the citation point
somewhere the text is not, which is the failure this model exists to prevent -
and it would hide, in a library that produces evidence, the fact that the input
was wrong.

    from adapters.pdfplumber_adapter import parse_pdf
    document = parse_pdf("paper.pdf")
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from document_intelligence.model import BoundingBox, Document, Page, TextRegion


ORDER_BASIS = "vertical_position"


# The model rejects for a dozen distinct reasons and says so in prose. A caller
# wanting to respond differently to "the parser emitted a zero-height line" and
# "the parser put text off the page" had to match on the message text - and the
# tests in this repository were doing exactly that, which is how the need showed
# up. The message stays; the classification is a value beside it.
_CAUSES = (
    ("degenerate_box", ("must be ordered",)),
    ("outside_page", ("within page bounds", "within 0..1")),
    ("non_finite", ("must be finite",)),
    ("bad_identifier", ("identifier must not be empty",)),
    ("duplicate_identifier", ("identifiers must be unique",)),
    ("bad_page", ("page number", "page dimensions")),
)


def classify(reason: str) -> str:
    lowered = reason.lower()
    for cause, needles in _CAUSES:
        if any(needle.lower() in lowered for needle in needles):
            return cause
    # Deliberately not "unknown_but_probably_fine": an unrecognised rejection is
    # the one a reader most needs to look at, since it means the model refused
    # for a reason this adapter has never seen.
    return "unclassified"


@dataclass(frozen=True)
class SkippedRegion:
    """A region the model refused, kept rather than dropped.

    A parser adapter that quietly discards what it cannot represent reports a
    clean document over a partial one. The count belongs in the result.
    """

    page_number: int
    identifier: str
    reason: str
    cause: str = "unclassified"


@dataclass(frozen=True)
class ParseResult:
    document: Document
    skipped: tuple[SkippedRegion, ...]
    order_basis: str = ORDER_BASIS

    @property
    def region_count(self) -> int:
        return sum(len(page.regions) for page in self.document.pages)


def _lines(page) -> list[dict]:
    """Group words into lines by their top coordinate, ordered top to bottom.

    pdfplumber gives words; a citation to a single word is too fine to be
    useful, and one to a whole page too coarse to check. Lines are the unit a
    reader can actually locate on the page.

    **This is vertical position, not reading order.** On the two-column pages of
    the sample paper the two columns interleave - page 14 alternates sides
    twenty times across forty-five regions - so `p14-l5` is the fifth line down
    the page, not the fifth thing a person would read.

    Columns are not guessed at. The obvious derivation, splitting on the largest
    gap between line start positions, was measured against this document and
    does not work: a single-column page shows a 16.7% gap and a genuinely
    two-column one shows 8.8%. A heuristic that gets those two backwards would
    produce a confident wrong ordering, which is worse than an honest positional
    one - a reader who knows the order is positional can allow for it, and one
    told it is reading order cannot.

    `ParseResult.order_basis` states which of the two this is, and
    `document_intelligence.reading_order` is where a caller who does know the
    real order records and validates it.
    """
    words = page.extract_words()
    rows: dict[int, list[dict]] = {}
    for word in words:
        # Rounding to the point: characters on one line vary by fractions from
        # font metrics, and a stricter key would split every line into several.
        rows.setdefault(round(word["top"]), []).append(word)
    return [sorted(group, key=lambda w: w["x0"]) for _, group in sorted(rows.items())]


def parse_pdf(path: str | Path, *, max_pages: int | None = None,
              coordinate_space: str = "page") -> ParseResult:
    import pdfplumber

    path = Path(path)
    # The model demands a checksum, and the right one is of the bytes actually
    # parsed. A citation into this document is only meaningful against the file
    # it was produced from; a different edition with the same name is a
    # different document.
    digest = hashlib.sha256(path.read_bytes()).hexdigest()

    pages: list[Page] = []
    skipped: list[SkippedRegion] = []

    with pdfplumber.open(str(path)) as pdf:
        for index, source in enumerate(pdf.pages, start=1):
            if max_pages is not None and index > max_pages:
                break
            regions = []
            for line_number, words in enumerate(_lines(source), start=1):
                identifier = f"p{index}-l{line_number}"
                left = min(w["x0"] for w in words)
                right = max(w["x1"] for w in words)
                top = min(w["top"] for w in words)
                bottom = max(w["bottom"] for w in words)
                if coordinate_space == "normalized":
                    left, right = left / source.width, right / source.width
                    top, bottom = top / source.height, bottom / source.height
                try:
                    box = BoundingBox(left, top, right, bottom,
                                      coordinate_space=coordinate_space)
                    # Checked here as well as by Page, because Page checks it
                    # while constructing and one bad box aborts the whole
                    # construction. A parser emitting a single malformed line
                    # would then cost every good region on that page - the
                    # first version of this adapter lost two entire pages to one
                    # injected box. Rejecting the region individually keeps the
                    # rest of the evidence.
                    box.validate_for_page(source.width, source.height)
                    regions.append(TextRegion(identifier=identifier, bounding_box=box))
                except ValueError as error:
                    skipped.append(SkippedRegion(index, identifier, str(error),
                                                 classify(str(error))))

            try:
                pages.append(Page(number=index, width=source.width,
                                  height=source.height, regions=tuple(regions)))
            except ValueError as error:
                # A page can still be refused for reasons no single region owns,
                # such as duplicate identifiers. Then the page really is
                # unrepresentable and losing it is the correct outcome.
                skipped.append(SkippedRegion(index, f"p{index}",
                                             f"page rejected: {error}",
                                             classify(str(error))))

    document = Document(identifier=path.name, checksum=digest, pages=tuple(pages))
    return ParseResult(document=document, skipped=tuple(skipped),
                       order_basis=ORDER_BASIS)
