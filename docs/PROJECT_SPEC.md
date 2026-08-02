# Project Specification: Multimodal Research Document Intelligence

## 1. Project goal

Build a reproducible evidence-centered document intelligence system for scientific and professional PDFs that preserves document layout and supports page-level and region-level evidence retrieval.

The system should make retrieved evidence inspectable against the original PDF. Page identity, region coordinates, document structure, reading order, and extraction provenance must survive parsing, indexing, retrieval, citation, and verification.

## 2. MVP

The approved MVP includes:

1. Coordinate-preserving PDF parsing.
2. OCR fallback only when necessary.
3. Document hierarchy preservation.
4. Reading-order preservation.
5. Text region extraction.
6. Table region extraction.
7. Figure and caption extraction.
8. Page image retrieval.
9. Text retrieval.
10. Hybrid retrieval.
11. Bounding-box evidence citation.
12. Page-level evidence citation.
13. Cross-page evidence support.
14. Evidence verification.

### 2.1 Evidence model

Every evidence unit must be traceable to an immutable corpus document version and include, as applicable:

- document identifier and checksum;
- one-based PDF page number;
- page dimensions and coordinate-system metadata;
- region identifier, type, and bounding box;
- hierarchy parent and reading-order position;
- extracted text or a reference to the page image/region;
- extraction method (`native` or `ocr`) and confidence/quality metadata when available; and
- parser, OCR, index, and schema versions.

The canonical bounding-box convention will be documented before implementation. It must define origin, units, axis direction, page box, rotation handling, and conversion to rendered-image coordinates.

### 2.2 Parsing and structure

The parser must preserve page boundaries and usable coordinates. It must represent document hierarchy such as document, section, subsection, page, block, region, and span when those relationships are available. Reading order must be explicit rather than inferred later from storage order.

OCR is a fallback for pages or regions where native text is absent or fails a documented extraction-quality check. The MVP is not an OCR benchmark and should not OCR every page by default.

Tables, figures, captions, and text must be distinguishable region types. Captions should retain links to their associated figure or table where the document provides sufficient evidence for that association.

### 2.3 Retrieval and citation

- **Text retrieval** ranks extracted textual evidence units.
- **Page retrieval** returns exact source page images and page identities relevant to a query.
- **Hybrid retrieval** combines text evidence with page-level evidence using a frozen, documented fusion procedure.
- **Region citations** identify document, page, region, and bounding box.
- **Page citations** identify document and page even when a reliable sub-page box is unavailable.
- **Cross-page evidence** returns an explicitly linked set of evidence units spanning two or more pages.
- **Evidence verification** checks document checksum, page existence, coordinate validity, region/page correspondence, stored provenance, and consistency between the cited evidence and the indexed artifact.

## 3. MVP datasets

- Public scientific PDFs.
- A small reproducible benchmark corpus.

Before acquisition, the corpus plan must define inclusion criteria, document count target, source and license metadata, checksum manifest, versioning, storage boundaries, annotation format, and redistribution restrictions. No dataset is downloaded or selected by this specification update.

## 4. Evaluation

Compare:

1. **Text-only retrieval:** retrieval over extracted text evidence without page-level retrieval signals.
2. **Hybrid text + page retrieval:** retrieval that combines text evidence and page-level evidence using the same corpus, query set, and relevance judgments.

Measure:

- Retrieval Recall;
- Evidence Precision;
- Citation correctness;
- Cross-page evidence accuracy; and
- Retrieval latency.

Metric definitions and a reproducible protocol appear in `docs/EXPERIMENT_PLAN.md`.

## 5. MVP acceptance criteria

The MVP is complete when the approved corpus can be processed and evaluated locally and all of the following are demonstrated:

- Every indexed document and page is tied to a stable identifier and checksum.
- Extracted text, table, figure, and caption regions retain valid page coordinates and provenance.
- The coordinate convention and transformations reproduce citations on the correct rendered page.
- Document hierarchy and explicit reading order survive storage and retrieval.
- OCR runs only for pages/regions meeting the frozen fallback rule, and its use is visible in evidence metadata.
- Page-image retrieval returns the exact page version associated with the indexed document.
- Text-only and hybrid retrieval produce ranked, verifiable evidence using the same frozen corpus and query judgments.
- Region citations resolve to valid bounding boxes inside the cited page; page citations resolve to the correct document and page.
- Cross-page cases return and verify the required multi-page evidence set.
- The verifier detects invalid document hashes, page references, coordinates, or provenance links.
- All five approved metrics are reported with definitions, raw counts or per-query values, aggregation method, sample size, and configuration version.
- A clean local setup can reproduce parsing, indexing, retrieval, citation verification, and evaluation without unnecessary distributed infrastructure.

No minimum retrieval-quality or latency threshold has been approved. Freezing numerical success thresholds before experiment execution requires approval.

## 6. Future extensions

Future extensions are not part of the MVP and require approval. Possible categories include:

- additional professional-document formats or non-PDF inputs;
- richer visual or semantic retrieval models;
- document question answering or evidence-grounded synthesis;
- interactive evidence viewers or annotation tools;
- broader corpora, multilingual evaluation, or specialized OCR studies;
- learned reranking, layout models, or model-based verification; and
- scaling or deployment beyond the local reproducible benchmark.

Listing an extension here does not approve its implementation, dependency, model, or dataset.

## 7. Out of scope

- Full document editing.
- General-purpose OCR benchmarking.
- Production document management.
- Large-scale distributed indexing.
- Commercial cloud deployment.
- End-to-end document generation.

## 8. Implementation constraints

- Prefer Python.
- Use a modular architecture.
- Keep the design understandable and reproducible for one undergraduate developer.
- Do not introduce unnecessary distributed systems.
- Keep parsing, OCR decision logic, structure representation, indexing, retrieval, citation, verification, and evaluation responsibilities separable.
- Do not begin implementation until separately approved.

## 9. Planned deliverables

- Reproducible corpus manifest and annotation/query specification.
- Coordinate-preserving document representation.
- Conditional OCR path with recorded provenance.
- Text-only and hybrid retrieval configurations.
- Page- and region-level citation records plus verification.
- Reproducible evaluation harness and documented results.

This document approves the research scope; it does not authorize implementation, downloads, or experiments.
