# Status

<!-- historical: 프로젝트 착수 시점 -->
> **이 문서는 기록이다.** 착수 시점의 단계 게이트 상태다 — 무엇을 아직 하지
> 않았고 다음에 무엇이 승인됐는지를 적어둔 것이다.
>
> 그 뒤로 달라진 것: 실제 PDF(arXiv 15쪽)를 pdfplumber로 파싱해 구역 724개를 모델에 통과시켰고, 독립 파서(pypdf)를 오라클로 좌표를 교차 검증했다.
>
> 지금 상태는 [README](../README.md)에 있다. 여기 적힌 "아직 하지 않았다"는 문장들은
> **당시의 사실**이고 지금은 맞지 않는다. 조용히 고치면 착수 때 무엇을 의도적으로
> 미뤘는지가 사라지므로, 고치는 대신 선언한다.
>
> 낡았다는 것이 선언이면 기록이고, 선언이 아니면 사고다.

## Current phase

**Approved specification and planning documentation.** The repository contains a controlled documentation scaffold. Application implementation, corpus selection/acquisition, parsing, OCR, indexing, retrieval, and evaluation have not started.

## Completed

- Repository initialized on `main`.
- Project goal, MVP, dataset category, evaluation comparison, metrics, implementation constraints, future extensions, and out-of-scope work documented.
- Evidence provenance, coordinate preservation, conditional OCR, hierarchy, reading order, and verification principles recorded.
- Planning/bootstrap tasks and approval boundaries defined.
- Reproducible experiment protocol and result-reporting schema defined.

## Not started

- Repository inspection and environment bootstrap planning.
- Dependency, parser, OCR, retrieval, or model selection.
- Corpus selection, download, annotation, or redistribution decisions.
- Architecture implementation or functional skeletons.
- Parsing, page rendering, OCR, indexing, retrieval, citation, or verification.
- Experiments or long-running jobs.

## Safety and artifact state

- No PDFs or datasets have been downloaded.
- No models or OCR weights have been downloaded.
- No application implementation has been written.
- No indexes, page images, OCR artifacts, or experiment results exist.
- No experiment or long-running job has been started.

## Next authorized work

Start with A1 in `docs/TASKS.md`: inspect and inventory the repository. This planning task does not authorize implementation or dataset acquisition.
