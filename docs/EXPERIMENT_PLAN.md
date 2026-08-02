# Experiment Plan

## 1. Purpose and status

Compare text-only retrieval with hybrid text-plus-page retrieval for page- and region-grounded evidence in scientific PDFs. The evaluation must measure retrieval quality, citation correctness, cross-page evidence, and latency while preserving complete provenance.

This is a planning protocol only. No corpus has been selected or downloaded, and no experiment is authorized or executed.

## 2. Evaluation systems

1. **T0 — Text-only retrieval:** rank textual evidence units extracted from the benchmark PDFs. Page images and page-level retrieval signals do not influence ranking.
2. **H1 — Hybrid text + page retrieval:** combine the T0 text evidence with page-level evidence using a frozen fusion method.

T0 and H1 must use the same corpus version, document parsing output, query set, relevance judgments, result cutoff, and evaluation code. Any model, representation, score normalization, or fusion choice must be documented and approved before implementation.

## 3. Corpus and evidence judgments

Use a small, versioned corpus of public scientific PDFs. The frozen manifest must record document ID, source, license or usage terms, retrieval date, file checksum, page count, and corpus split or evaluation role.

Each evaluation query must record:

- stable query ID and text;
- relevant document(s);
- relevant page(s);
- gold evidence region(s), including bounding boxes where reliable;
- whether complete evidence spans multiple pages;
- acceptable alternate evidence and ambiguity notes; and
- annotation schema and corpus version.

Annotation instructions must define relevance, partial overlap, duplicate regions, page-only evidence, cross-page completeness, and unanswerable or ambiguous queries. Annotation quality checks and adjudication must be planned before corpus labeling.

## 4. Reproducible protocol

### 4.1 Freeze evaluated artifacts

Before a run, record or checksum the corpus manifest, source PDFs, parsed document representation, page images, OCR outputs, indexes, query/judgment set, coordinate schema, system configurations, retrieval/fusion parameters, evaluation code, commit hash, environment lock, and run manifest. Any material change produces a new experiment version.

### 4.2 Validate evidence provenance

Before indexing, verify document checksums, page counts, page dimensions, coordinate convention, region bounds, hierarchy references, reading-order references, extraction method, and page-image linkage. Record the OCR fallback decision for every page, including the measured trigger values and selected threshold version.

### 4.3 Matched retrieval runs

Run every query through T0 and H1 using the same evaluation cutoff set, such as planned values of `k` to be approved before execution. Reset or control caches consistently. Use a fixed run order or a recorded deterministic shuffle.

For latency, define warm-up separately from measured queries and repeat each system/query measurement enough times to report stable median and 95th-percentile latency. Record hardware, operating system, Python environment, index state, cache policy, timer, and concurrency. Do not combine indexing time with query latency; report indexing separately if later approved.

### 4.4 Verify returned evidence

For every retrieved citation:

1. Resolve the document ID and verify its checksum.
2. Resolve the one-based page number and exact page image.
3. Validate bounding-box geometry and coordinate transformation when a region is cited.
4. Confirm the region belongs to the cited page and indexed document version.
5. Compare returned evidence with the frozen judgments.
6. For cross-page queries, check whether the retrieved set covers all required pages/regions.

Stop and mark the run invalid if corpus provenance, coordinate transformations, or evaluation artifacts cannot be verified.

## 5. Metric definitions

- **Retrieval Recall@k:** number of gold evidence units retrieved in the top `k` divided by the number of gold evidence units, reported per query and aggregated. Page-level and region-level recall must not be silently mixed.
- **Evidence Precision@k:** number of retrieved evidence units in the top `k` matching an accepted gold unit divided by `k` or the number returned when fewer than `k` are returned. The matching/overlap rule must be frozen.
- **Citation correctness:** citations whose document checksum, page, region identity, coordinate bounds, and evidence provenance all verify and match an acceptable judgment divided by evaluated citations. Report page-only and bounding-box citations separately.
- **Cross-page evidence accuracy:** cross-page queries for which the retrieved evidence set contains every required page/region and no citation verification failure divided by all cross-page queries. Also report partial coverage.
- **Retrieval latency:** wall-clock query latency measured under the frozen cache/concurrency policy. Report sample count, median, 95th percentile, and maximum for T0 and H1.

Report raw per-query values, numerators, denominators, aggregation method, and confidence intervals or variability summaries where suitable. Define handling for queries with no gold evidence before evaluation.

## 6. Evaluation validity and acceptance

An evaluation is reproducible and valid only when:

- T0 and H1 use the same frozen corpus, queries, judgments, cutoffs, and metric implementation;
- all source documents and derived artifacts resolve through recorded checksums and versions;
- every scored citation passes or explicitly fails the same verification procedure;
- coordinate and page-image transformations are validated before scoring;
- OCR use follows and records the frozen fallback rule;
- cross-page queries are identified before retrieval results are inspected;
- latency conditions and repetitions are recorded and comparable; and
- raw results and configuration manifests are retained so metrics can be recomputed.

The MVP evaluation is complete when all five approved metric families are reported for both systems with protocol deviations and limitations. No numerical retrieval-quality or latency threshold is currently approved; establishing those gates requires approval before the evaluated run.

## 7. Required outputs

- Frozen corpus, query, judgment, and system manifests.
- Per-query ranked retrieval output with evidence identifiers and scores.
- Citation verification outcomes and failure reasons.
- Cross-page coverage outcomes.
- Per-query latency observations and environment metadata.
- Aggregated metrics with raw counts and variability.
- Protocol deviations, limitations, and acceptance assessment in `docs/RESULTS.md`.
