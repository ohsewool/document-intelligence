# Document Intelligence — 파서에 의존하지 않는 문서 증거 모델

문서에서 뽑아낸 내용이 **원문의 어디에서 왔는지**를 잃지 않고 표현하기 위한 데이터 모델. 파서를 포함하지 않으며, 어떤 파서가 만든 결과든 같은 형태로 받아 검증한다.

```bash
python3 -m pytest tests/ -q     # 52 tests
```

## 무엇을 보장하는가

인용은 "이 주장은 문서의 이 자리로 되짚을 수 있다"는 약속이다. 모델은 그 약속 중 **검사 가능한 부분**을 강제해서, 이걸 쓰는 쪽(예: `rag-profile-selector`의 citation grounding)이 다시 확인하지 않아도 되게 한다.

- **없는 자리를 가리킬 수 없다** — 문서가 가지지 않은 페이지를 참조하는 증거는 생성 자체가 거부된다
- **하나의 사각형은 한 자리만 가리킨다** — 좌표가 두 페이지를 동시에 지목하는 인용은 거짓 약속이므로 거부
- **식별자는 재사용되지 않는다** — 페이지 번호, 페이지 내 구역 식별자, 증거 식별자 각각에 대해. 단 구역 식별자의 유일성은 페이지 단위라 모든 페이지에 `body`가 있는 것은 정상이다
- **만든 뒤에는 고칠 수 없다** — 제자리에서 다시 쓸 수 있는 증거는 증거가 아니다
- **참/거짓은 페이지 번호가 아니다** — 파이썬에서 `True == 1`이라 플래그가 인용으로 둔갑하는 경로를 막는다

좌표는 정규화(0~1) 또는 페이지 공간 중 하나로 명시되며, 페이지 크기에 대해 검증된다.

## 구성

```
model.py          BoundingBox, Region(text/table/figure/caption), Page, Document, EvidenceCitation
coordinates.py    좌표 공간 변환
reading_order.py  결정론적 읽기 순서
hierarchy.py      문서 구조(섹션·페이지·구역) 참조와 검증
```

## 관련 저장소

[`rag-profile-selector`](https://github.com/ohsewool/rag-profile-selector)가 검색 결과를 이 모델의 좌표로 되짚어 인용 정확도를 측정한다. 두 저장소를 물리적으로 합치지 않은 이유는 그쪽 `docs/ADR-001-citation-grounding.md`에 기록돼 있다.

## 남은 작업

- 실제 파서 연결 (HWP·PDF — 별도 결정 필요)
- 스캔 문서의 OCR 좌표 처리

## 라이선스

Apache License 2.0. [`LICENSE`](LICENSE) 참조.
