# Repository Instructions: Multimodal Research Document Intelligence

## Mission

Build a reproducible, evidence-centered document intelligence system for scientific and professional PDFs that preserves document layout and supports page-level and region-level evidence retrieval.

## Scope authority

- `docs/PROJECT_SPEC.md` is the approved scope baseline.
- The MVP is retrieval- and evidence-centered. Preserve source-document identity, page identity, geometry, hierarchy, reading order, and extraction provenance throughout the pipeline.
- Use OCR only when a documented page-level fallback rule determines that native extraction is insufficient. Always record whether content came from native parsing or OCR.
- Keep MVP, future extensions, and out-of-scope work distinct.
- Do not add capabilities, dependencies, datasets, models, services, or evaluation changes without recording them under `NEEDS_APPROVAL` in `docs/TASKS.md` and obtaining approval.

## Work controls

- Before work, read `docs/PROJECT_SPEC.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, and `docs/STATUS.md`.
- Work only on `AUTO_READY` tasks unless the user explicitly approves another item.
- Current `AUTO_READY` work is limited to inspection, planning, documentation, and environment bootstrap. It does not authorize application implementation.
- Prefer Python and a modular, local architecture understandable by one undergraduate developer.
- Do not introduce unnecessary distributed systems, cloud deployment, or production document-management infrastructure.
- Do not download PDFs, datasets, OCR/model weights, or other model artifacts without approval.
- Do not run experiments, indexing jobs, or long-running processes without approval.
- Never claim results that were not measured. `docs/RESULTS.md` must clearly distinguish planned, partial, and completed evaluations.

## Evidence and reproducibility rules

- Every extracted or retrieved evidence unit must retain the source document identifier, immutable document checksum, page number, region type, bounding box where applicable, extraction method, and pipeline version.
- Bounding boxes must use one documented coordinate convention and remain convertible back to the rendered source page.
- Page images must be derived from and linked to the exact corpus document version.
- Corpus membership, licensing/source metadata, file checksums, annotations, query sets, configuration, seeds, and environment must be versioned for evaluated runs.
- Do not edit or redistribute source PDFs beyond their permitted use.

## Current phase

The approved specification and planning framework are being established. Implementation, corpus acquisition, indexing, and experiments have not started.
