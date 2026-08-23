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

> **착수 단계 게이트는 소진됐다 (2026-08-21).** 위의 "Current AUTO_READY work ... does not authorize application implementation"는 착수 시점의 제약이고,
> 그때는 맞았다. 지금 이 저장소에는 증거 모델·좌표·계층·읽기 순서 구현과 실제 PDF 어댑터가 있고 테스트 233개가 돈다. 그 문장을 그대로 두면 **다음 작업이 이미
> 끝난 단계로 되돌아간다** — 형제 저장소 `rag-profile-selector`의 `AGENTS.md`가 몇 달간
> 쓰지 않는 코퍼스를 지시하고 있던 것과 같은 종류의 사고다.
>
> `docs/TASKS.md`와 `docs/STATUS.md`는 착수 계획의 **기록으로 선언**돼 있다. 지금 상태를
> 알려면 [README](README.md)와 그 문서들이 가리키는 실제 결과를 본다.
>
> **아래 안전 제약은 그대로 유효하다** — 실서비스·실계정·실크리덴셜 금지, 승인 없는
> 다운로드·장시간 작업 금지, 측정하지 않은 결과를 주장하지 않기. 소진된 것은 단계
> 게이트뿐이다.

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
