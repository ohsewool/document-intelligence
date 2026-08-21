# Results

## Result status

**No corpus has been acquired and no experiments have been run. There are no retrieval, citation, cross-page, or latency results.**

This file contains the planned reporting structure only. Metric definitions and acceptance conditions are not measured findings.

## Experiment record template

### Identification

- Experiment version:
- Commit hash:
- Date/time and timezone:
- Operator:
- Corpus and checksum-manifest version:
- Query and judgment version:
- Coordinate/evidence schema version:
- Parser/OCR/index versions:
- Python and dependency-lock versions:
- System: T0 / H1

### Reproducibility and provenance

- Public-source and license/usage metadata verified:
- Source PDF checksums verified:
- Page images linked to exact document versions:
- Coordinate transformations validated:
- Hierarchy and reading order validated:
- OCR fallback rule/version recorded:
- Run manifest and environment retained:
- Protocol deviations:

### Retrieval measurements

Report per-query values, numerator, denominator, cutoff, aggregate, sample count, and variability where applicable:

- Retrieval Recall@k:
- Evidence Precision@k:
- Page-only citation correctness:
- Bounding-box citation correctness:
- Cross-page evidence accuracy:
- Cross-page partial coverage:
- Median retrieval latency:
- 95th-percentile retrieval latency:
- Maximum retrieval latency:

### Evidence-verification failures

- Document checksum failures:
- Invalid page references:
- Invalid or mismatched bounding boxes:
- Region/page provenance failures:
- Page-image version failures:
- OCR provenance failures:
- Other failures:

### Evaluation assessment

- T0/H1 inputs and judgments matched:
- All five approved metric families reported:
- Raw results retained and recomputable:
- Reproducibility criteria satisfied:
- Overall result: COMPLETE / INVALID / INCOMPLETE

### Limitations and interpretation

- Corpus limitations:
- Annotation ambiguity:
- Parsing/OCR limitations:
- Retrieval limitations:
- Citation and cross-page limitations:
- Latency measurement limitations:
- Follow-up requiring approval:

## Current findings

**이 문장은 더 이상 사실이 아니었다.** 원래 "None. The project remains in the specification and planning phase."였고, 착수 시점에는 맞았으며 그 뒤로 고쳐지지 않았다.

이 파일에는 없다. 실제 측정은 [README](../README.md)에 있다 — 실제 PDF 15쪽에서 구역 724개·거부 0건, 독립 파서(pypdf)를 오라클로 한 좌표 교차 검증(본문 쪽 일치율 91.7~100%, 표·그림 쪽 13.6~74.8%).

아래 템플릿은 그대로 둔다 — 보고 구조를 정의하는 것이 이 파일의 나머지 역할이다.
