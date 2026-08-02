# Tasks

Only planning and environment-bootstrap work is currently auto-ready. No item below authorizes application implementation, document downloads, indexing, or experiments.

## AUTO_READY

### Repository inspection

- [ ] **A1 — Inspect and inventory the repository.** Confirm branch and working-tree state; inventory documentation and configuration; verify that no application code, PDFs, datasets, OCR/model artifacts, credentials, generated indexes, or unexpected dependencies are present. Record findings in `docs/STATUS.md`.
- [ ] **A2 — Review repository controls.** Check `.gitignore`, repository instructions, artifact boundaries, and documentation links against the approved scope and evidence-provenance requirements.

### Environment bootstrap planning

- [ ] **A3 — Specify the minimal local Python environment.** Document a candidate Python version, isolated-environment procedure, cache locations, deterministic locale/timezone handling, and verification commands. Do not install or add dependencies.
- [ ] **A4 — Define local artifact boundaries.** Plan locations and naming for source PDFs, page images, OCR artifacts, indexes, annotations, audit/provenance records, temporary files, and results. Keep datasets and generated artifacts out of Git.

### Architecture planning

- [ ] **A5 — Draft the component map.** Define responsibilities and dependency direction for parsing, OCR fallback decisions, document hierarchy, region extraction, page rendering, indexing, retrieval, hybrid fusion, citation, verification, and evaluation. Do not create functional code.
- [ ] **A6 — Define the document/evidence schema.** Specify stable identifiers, checksum provenance, page metadata, region types, hierarchy, reading order, extraction method, and version fields using synthetic examples only.
- [ ] **A7 — Define the coordinate contract.** Document origin, units, axes, page box, rotation, clipping, rounding, and transformations between PDF and rendered-page coordinates. Include validation invariants without implementing them.
- [ ] **A8 — Define OCR fallback criteria.** Propose observable native-extraction quality checks, fallback granularity, provenance fields, and safeguards against unconditional OCR. Engine selection remains approval-gated.
- [ ] **A9 — Define retrieval and verification interfaces.** Specify text, page, hybrid, cross-page, citation, and verification inputs/outputs, including ranked evidence and failure states. Do not select or implement retrieval models.

### Corpus planning

- [ ] **A10 — Draft corpus inclusion criteria.** Plan a small public-scientific-PDF benchmark with source, license/usage terms, checksum, page count, layout characteristics, and exclusion fields. Do not select or download files.
- [ ] **A11 — Draft annotation and query schemas.** Define query IDs, relevance judgments, gold pages/regions, cross-page evidence sets, annotator notes, ambiguity flags, and versioning without annotating actual PDFs.
- [ ] **A12 — Draft corpus reproducibility controls.** Specify manifest versioning, checksum validation, permitted redistribution behavior, acquisition instructions, and train/development/evaluation separation if needed.

### Experiment planning

- [ ] **A13 — Freeze metric definitions in planning form.** Review Recall, Evidence Precision, citation correctness, cross-page accuracy, and latency definitions; document cutoffs, aggregation, missing-evidence handling, and confidence reporting for later approval.
- [ ] **A14 — Draft the matched comparison protocol.** Prepare the text-only versus hybrid run matrix, environment record, warm-up policy, timing repetition plan, and version manifest without running it.
- [ ] **A15 — Draft acceptance checks.** Turn the functional and reproducibility criteria into planned assertions for coordinate validity, hierarchy, OCR provenance, citations, cross-page sets, and evidence verification.

## NEEDS_APPROVAL

- [ ] Begin any application implementation, including functional skeletons or executable pipeline code.
- [ ] Select, install, or add any dependency, parser, OCR engine, retrieval library, model, or model weight.
- [ ] Select, acquire, download, copy, redistribute, or expand the PDF benchmark corpus.
- [ ] Create indexes, render a corpus, run OCR, run retrieval, or execute experiments.
- [ ] Start any long-running or heavy job.
- [ ] Freeze numerical retrieval-quality or latency acceptance thresholds.
- [ ] Add any future extension, dataset type, document format, metric, comparison, or other scope expansion.
- [ ] Add external or paid APIs, cloud deployment, production integrations, or distributed indexing.

## BLOCKED

- None. Corpus acquisition, implementation, and experiment execution are approval-gated rather than current planning blockers.

## DONE

- [x] Initialize the controlled research repository on `main`.
- [x] Approve the Multimodal Research Document Intelligence goal, MVP, dataset category, evaluation, constraints, and out-of-scope boundaries.
- [x] Replace placeholder documentation with the approved project specification and planning controls.
