# Decisions

## Approved decisions

### D-001: Evidence-centered architecture

The primary output is retrievable, verifiable evidence tied to the original PDF, not generated document content. Provenance must persist across parsing, indexing, retrieval, citation, and verification.

### D-002: Coordinates are first-class data

Page dimensions, rotation, coordinate convention, region geometry, and transformations are stored explicitly. A cited bounding box must map back to the correct version of the rendered source page.

### D-003: Native parsing before OCR

Attempt coordinate-preserving native PDF extraction first. Use OCR only when a frozen, documented page- or region-level fallback rule is met, and label OCR-derived evidence. The project will not optimize for general-purpose OCR benchmarking.

### D-004: Explicit structure and reading order

Represent document hierarchy and reading order as explicit, versioned relationships. Storage order alone is not a sufficient representation of reading order.

### D-005: Typed evidence regions

Represent text, table, figure, and caption as distinguishable evidence types. Preserve associations, such as figure-to-caption or table-to-caption, only when supported by document evidence and record ambiguity rather than inventing a link.

### D-006: Page and region citations

Use region-level bounding-box citations when reliable geometry exists and page-level citations when the page is the appropriate evidence unit or a reliable sub-page region is unavailable. Cross-page evidence is an explicit set of linked citations.

### D-007: Verification is separate from retrieval

Retrieval proposes evidence; a separate verification step checks document checksum, page, bounds, provenance, and artifact consistency. Retrieval score alone does not establish citation correctness.

### D-008: Two-system evaluation

Compare text-only retrieval with hybrid text-plus-page retrieval on the same frozen corpus, queries, relevance judgments, cutoffs, and metric code. Page retrieval must return the exact source page identity and image version.

### D-009: Small reproducible corpus

Use a small benchmark of public scientific PDFs with documented sources, licenses or usage terms, file checksums, inclusion criteria, and stable annotations. Corpus size should support local reproduction by one developer.

### D-010: Local modular implementation

Prefer Python and separate parsing, OCR fallback, document representation, indexing, text retrieval, page retrieval, fusion, citation, verification, and evaluation responsibilities. Avoid unnecessary distributed systems.

## Decisions requiring approval

- Start application implementation or create functional parsing, indexing, retrieval, OCR, citation, or verification code.
- Select or add any runtime/development dependency, PDF parser, OCR engine, retrieval library, model, or model weight.
- Select, acquire, download, redistribute, or materially expand the benchmark corpus.
- Use a dataset other than public scientific PDFs in the small reproducible benchmark.
- Run indexing, evaluation, experiments, or other long-running jobs.
- Freeze numerical retrieval-quality or latency success thresholds.
- Add a future extension or any capability outside the approved MVP.
- Add document types, evaluation measures, or comparisons beyond the approved scope.
- Use external APIs, paid services, cloud deployment, or production document systems.
- Introduce large-scale distributed indexing or infrastructure.

## Decision procedure

Add a proposed change to `NEEDS_APPROVAL` in `docs/TASKS.md` with rationale, alternatives, licensing/data implications, dependency and storage impact, reproducibility impact, and expected effect on the evaluation. Do not proceed until approval is explicit.
