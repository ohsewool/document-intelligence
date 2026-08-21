# Tasks

<!-- historical: 프로젝트 착수 시점 -->
> **이 문서는 기록이다.** 착수 시점의 단계별 작업 목록이다. A1은 "코드·PDF·모델 산출물이 없음을 확인하라"이고, 여러 항목이 "기능 코드를 만들지 말 것"을 명시한다.
>
> 그 뒤로 달라진 것: 증거 모델과 실제 PDF 어댑터를 만들었고 테스트 153개가 돈다. 독립 파서로 좌표를 교차 검증했다.
>
> 지금 상태는 [README](../README.md)에 있다. 여기 적힌 "아직 하지 않았다"·"구현하지 말라"는
> 항목들은 **당시의 사실이자 당시의 제약**이다. 체크박스를 지금 채우면 계획을 그대로
> 따른 것처럼 보이고, 실제로 어디서 갈라졌는지가 사라진다. 그래서 고치지 않고 선언한다.
>
> 낡았다는 것이 선언이면 기록이고, 선언이 아니면 사고다.

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
