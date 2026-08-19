# Document Intelligence — 파서에 의존하지 않는 문서 증거 모델

[![tests](https://github.com/ohsewool/document-intelligence/actions/workflows/tests.yml/badge.svg)](https://github.com/ohsewool/document-intelligence/actions/workflows/tests.yml)

문서에서 뽑아낸 내용이 **원문의 어디에서 왔는지**를 잃지 않고 표현하기 위한 데이터 모델. 파서를 포함하지 않으며, 어떤 파서가 만든 결과든 같은 형태로 받아 검증한다.

```bash
pip install -e .                                   # src/ 레이아웃이라 설치 없이는 import되지 않는다
python3 -m pytest tests/ -q     # 106 tests
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
reading_order.py  읽기 순서를 아는 호출자가 기록·검증하는 자리 (어댑터는 만들지 못한다 — 아래)
hierarchy.py      문서 구조(섹션·페이지·구역) 참조와 검증
```

## 관련 저장소

[`rag-profile-selector`](https://github.com/ohsewool/rag-profile-selector)가 검색 결과를 이 모델의 좌표로 되짚어 인용 정확도를 측정한다. 두 저장소를 물리적으로 합치지 않은 이유는 그쪽 `docs/ADR-001-citation-grounding.md`에 기록돼 있다.

## 실제 파서 연결

```bash
python3 -m pytest tests/ -q      # 106 tests, about 12 seconds
```

`src/document_intelligence/adapters/pdfplumber.py`가 실제 PDF를 pdfplumber로 파싱해 이 모델에 그대로 넘긴다. 이전까지 모델이 만난 좌표는 전부 이 저장소의 픽스처가 만든 것이었는데, 픽스처는 모델에 맞게 쓰이므로 "어떤 파서의 결과든 받는다"는 주장의 시험이 되지 못한다. 15페이지 논문에서 구역 724개, 거부 0건.

거부는 **값으로 분류된다** — `degenerate_box`, `outside_page`, `non_finite` 등. 모델은 열두 가지 사유를 산문으로 말하고, 호출자가 "파서가 높이 0인 줄을 냈다"와 "파서가 페이지 밖에 글자를 뒀다"에 다르게 대응하려면 그 문장을 매칭해야 했다. **이 저장소의 테스트가 실제로 그러고 있었고**, 그게 분류가 필요하다는 신호였다 — 스위트가 산문을 읽어야 안다면 모든 호출자도 그렇다.

모르는 사유는 `unclassified`로 남는다. 무해한 기본값에 접어 넣지 않는 이유는, **모델이 이 어댑터가 본 적 없는 사유로 거부했다는 뜻**이고 그게 읽는 사람이 가장 봐야 할 경우이기 때문이다.

**어댑터는 고치지 않는다.** 높이 0인 줄이나 페이지 밖으로 나간 단어가 오면 모델이 거부하고, 어댑터는 그 사실을 `skipped`로 보고한다. 조용히 좌표를 보정하면 인용이 본문이 없는 자리를 가리키게 되는데, 그게 이 모델이 막으려는 실패다.

이 과정에서 결함이 하나 나왔다. `Page`는 생성 중에 구역을 검증하므로 **잘못된 구역 하나가 페이지 전체를 무효로 만든다** — 주입 시험에서 멀쩡한 구역 98개가 함께 사라졌다. 어댑터가 구역별로 먼저 검증해 개별 거부하도록 고쳤다.

## 남은 작업

- HWP 인제스천 (별도 결정 필요)
- OCR 엔진 연결 — 모델은 전사된 텍스트를 표현할 수 있으나(아래), **이 패키지는 인식기를 포함하지 않는다.** 엔진 없이 인제스천을 만들면 만들어낼 수 없는 데이터를 위한 표현을 짓는 것이라 하지 않았다

## 라이선스

Apache License 2.0. [`LICENSE`](LICENSE) 참조.

## 순서는 읽기 순서가 아니다

어댑터가 붙이는 식별자는 `l1, l2, l3`으로 흘러서 **읽기 순서처럼 보인다.** 실제로는 **수직 위치**다. 이 논문의 2단 페이지에서는 두 단이 섞이고, 14페이지는 구역 45개에서 좌우를 **20번** 오간다. `p14-l5`는 페이지에서 다섯 번째 줄이지 사람이 다섯 번째로 읽을 것이 아니다.

**단을 추측하지 않는다.** 가장 그럴듯한 유도 — 줄 시작 x값의 최대 간격으로 나누기 — 를 이 문서로 재봤더니 **거꾸로 나온다**: 단일 단 페이지가 16.7% 간격을, 진짜 2단 페이지가 8.8%를 보인다. 그 정도로 자신 있게 틀리는 휴리스틱은 정직한 위치 순서보다 나쁘다. 위치 순서라고 들은 독자는 그걸 감안할 수 있지만, 읽기 순서라고 들은 독자는 못 한다.

`ParseResult.order_basis`가 둘 중 무엇인지 말하고, `reading_order`는 **실제 순서를 아는 호출자**가 기록하고 검증하는 자리다. 어댑터가 만들지 못하므로 배선하지 않고 내보내기만 한다.

## 전사된 텍스트는 다른 약속이다

PDF의 텍스트 객체에서 뽑은 페이지는 **파일이 말하는 것**을 재현한다. 스캔된 페이지는 **인식기가 추측한 것**을 재현한다. 단어가 문자열에 들어가고 나면 둘은 구분되지 않고, 두 번째 종류로 인용을 따라간 독자는 자기가 전사본을 상대로 주장을 확인하고 있다는 걸 듣지 못한다.

그 구분이 살아남을 수 있는 자리는 모델뿐이다 — 파서 경계에서 잃으면 영영 잃는다.

- 구역은 텍스트의 출처를 기록한다 (`extracted` / `transcribed`)
- **전사 구역은 인식기의 확신도를 반드시 지녀야 한다.** 없이 받으면 추측이 판독으로 둔갑한다
- **추출 구역은 확신도를 가질 수 없다.** 확신할 대상이 없다 — 파일이 그렇게 적혀 있는 것이다
- 인용은 `citation_provenance()`로 무엇에 기대는지 답한다. 둘 다에 걸치면 `mixed`이고, 평균으로 뭉개지 않는다
- `lowest_confidence()`는 평균이 아니라 **최솟값**이다. 인용은 가장 불확실한 부분만큼만 검증 가능하고, 평균은 확신 있는 구역이 불확실한 구역을 가리게 한다

**이 패키지는 OCR을 하지 않는다.** `transcribed`는 OCR을 하는 파서가 아는 것을 놓을 자리이지, 이 라이브러리가 인식을 한다는 주장이 아니다. 테스트 두 개가 그 선을 지킨다 — 의존성에 인식기가 없다는 것과, 번들된 어댑터가 `transcribed`를 만들지 않는다는 것.

## 함께 보기

이 저장소는 다섯 개 중 하나다. 전체 지도와 각각이 무엇을 발견했는지는 [프로필](https://github.com/ohsewool)에 있다.

- [`agent-safety-core`](https://github.com/ohsewool/agent-safety-core) — 승인과 실행의 결속 · 1회용 lease · UNKNOWN_OUTCOME
- [`modelmate`](https://github.com/ohsewool/modelmate) — 증거가 없으면 확신하지 않는 모델링 도우미
- [`rag-profile-selector`](https://github.com/ohsewool/rag-profile-selector) — 인용이 어디를 가리키는지 측정 · 한국어 법령 코퍼스
- [`mcp-gateway`](https://github.com/ohsewool/mcp-gateway) — MCP 서버 앞의 보안 프록시

### 어댑터가 최상위 `adapters`에 있었다

`adapters`는 다른 배포판도 쓰는 최상위 이름이다 — 형제 저장소 `agent-safety-core`가 하나 내보낸다. 경로에서 먼저 만나는 정규 패키지가 이기고, **경고는 없다.**

```
pip install agent-safety-core --target /tmp/asc
PYTHONPATH=/tmp/asc python3 -c "from adapters.pdfplumber_adapter import parse_pdf"
ModuleNotFoundError: No module named 'adapters.pdfplumber_adapter'
```

인용을 문서와 대조하라고 있는 라이브러리에서 **파서가 무관한 프로젝트에 조용히 대체되는 것**은 작은 문제가 아니다. 구현은 `document_intelligence.adapters.pdfplumber`로 옮겼고 — 이 배포판이 소유한 패키지 안이다 — 예전 경로는 충돌이 없는 독자를 위해 재수출로 남겼다. 가짜 `adapters` 패키지를 만들어 하위 프로세스에서 8개 테스트로 고정했다. **가짜가 정말 최상위 이름을 가져갔는지도 함께 단언한다** — 그게 없으면 충돌이 없는 환경에서 통과하면서 아무것도 증명하지 않는다.
