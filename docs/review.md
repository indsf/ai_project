# S1 검토 결과 — 선박 의약품 재고 관리

검토 대상: [docs/task.md](docs/task.md), [docs/plan.md](docs/plan.md), [spec.md](spec.md), [decisions.md](decisions.md)

검토 일시: 2026-08-27

요약: 전반적으로 `spec.md`와 `decisions.md`는 S1 요구사항을 충족하도록 잘 작성되어 있습니다. 다만 데이터모델·API 일부 명명·제약 모순, 트랜잭션·동시성에서 명확한 보완이 필요합니다. 최종판정은 `REWORK`(아래 우선 개선사항 참조)입니다.

## 1) S1 필수 기능별 PASS/FAIL 및 근거
- **약품 카탈로그 관리:** PASS
	- 근거: `drugs` 테이블(필드 포함)과 POST/GET `/drugs` API가 명시되어 있음.
	- 주의: 입력 검증(중복 code 처리)과 검색 필터(페이징) 세부가 미기재(민감도: Minor).
- **최소 비치 기준 관리:** PASS (단, 정책 시계열 처리 모호)
	- 근거: `minimum_stock_policies` 테이블과 POST/GET `/ships/{shipId}/minimum-stock` 제공.
	- 문제점: `effective_from` 필드 존재와 `(ship_id, drug_id) unique` 제약이 동시 존재함(시계열 정책 불가). (민감도: Major)
- **재고 입고(로트 단위):** PASS
	- 근거: `batches` 테이블과 POST `/ships/{shipId}/stock/inbound` 명세가 있음.
	- 주의: `receivedAt`이 optional일 때의 기본값/서버시간 처리 미기재(민감도: Minor).
- **약품 사용(출고) — FEFO:** PASS
	- 근거: FEFO 알고리듬(`expiry_date` ASC, `received_at` ASC) 및 `/stock/use` 의사코드가 명시됨.
	- 주의: 동시성·교착(deadlock)·idempotency 경합 시나리오 설명은 있으나, 구현상 안전성 보완 필요(민감도: Major).
- **재고 현황 조회:** PASS
	- 근거: GET `/ships/{shipId}/stock` 응답에 총합·로트별 상세·isBelowMinimum 제공.
	- 주의: 조회 시 `includeExpired` 동작과 `isBelowMinimum` 계산 시점(일관성)에 대한 설명 보강 권장(민감도: Minor).
- **사용 이력 조회:** PASS
	- 근거: `usage_records`·`usage_allocations` 모델과 GET `/ships/{shipId}/usage` 정의.
	- 주의: 감사 목적의 `before_batch_available`(DB컬럼)는 API 응답에 명시되지 않음 — 감사/재연성 확보를 권장(민감도: Minor).

## 2) 데이터 모델과 API의 일관성
일반적으로 필드·엔드포인트가 일치하지만 다음 불일치/모호함이 발견되었습니다.

- 심각도: Major
	- 문제: `minimum_stock_policies`에 `effective_from`이 있으면서 `(ship_id, drug_id) unique` 제약이 존재함.
	- 근거: [spec.md]의 테이블 정의와 제약 참조.
	- 수정 방향: 정책의 시계열을 지원하려면 unique 제약을 `(ship_id, drug_id, effective_from)` 또는 time-range 모델로 바꾸거나, `effective_from`을 제거하고 단일 active-policy로 명확히 문서화.

- 심각도: Major
	- 문제: DB 무결성(음수 수량 방지) 관련 제약·원자성 업데이트가 명세에 부족함.
	- 근거: `batches.quantity_available`을 업데이트하는 의사코드는 있으나 DB CHECK/제약이나 원자적 UPDATE 예시 부재.
	- 수정 방향: DB 레벨 `CHECK (quantity_available >= 0)` 추가, 차감 업데이트를 `UPDATE ... SET quantity_available = quantity_available - :n WHERE id = :id AND quantity_available >= :n RETURNING ...` 형태로 원자화 권장.

- 심각도: Minor
	- 문제: `usage_allocations.before_batch_available`(DB) vs API의 `remainingBatchQuantity`(응답) 명명/출력 불일치.
	- 근거: 테이블 필드와 API 샘플 불일치.
	- 수정 방향: API 스키마와 DB 컬럼명을 정렬(예: 응답에 both `beforeQuantity`와 `afterQuantity` 제공) 또는 변환 규칙 문서화.

- 심각도: Minor
	- 문제: `batches.status`의 `closed` 상태 전이 규칙(언제 closed로 변경하는지)이 미정의.
	- 수정 방향: `quantity_available == 0`일 때 자동으로 `closed` 처리 등 명시.

- 심각도: Minor
	- 문제: `receivedAt` optional일 때 서버 default(예: now)와 `expiryDate >= receivedAt` 검증 순서 모호.
	- 수정 방향: inbound API 명세에 `receivedAt` 기본값(서버 시간)과 validation 순서 명시.

## 3) `spec.md`와 `decisions.md`의 모순/불명확성
- 심각도: Major
	- 문제: 만료 재고만 존재하는 경우의 처리(422 vs partial(0) 반환) 정의가 `spec.md`에서 분기되어 있음; `decisions.md`의 HTTP 매핑은 422로 규정함 — 동작 일관성 필요.
	- 근거: `spec.md` TC-02(422 또는 partial 가능) vs `decisions.md` 12번 항목(422 매핑).
	- 수정 방향: 정책 확정(만료만 존재 시 422 실패로 할지, partial(0)/status=partial로 응답할지) 및 해당 케이스의 client UX/통지 방식을 decisions에 명시.

- 심각도: Major
	- 문제: `minimum_stock_policies.effective_from`의 시계열 의도(존재 목적)와 DB의 unique 제약 충돌 — decisions.md에 시계열 처리 선택 기록이 없음.
	- 수정 방향: decisions.md에서 정책 버전화(혹은 단일 policy) 선택을 명시하고 spec 에 반영.

## 4) FEFO, 만료 재고, 재고 부족 처리 검토
- FEFO 기본 설계: 타당(ORDER BY expiry_date ASC, received_at ASC). Tie-breaker로 `received_at` 사용 결정은 합리적.

- 심각도: Minor
	- 권고: `received_at`도 같은 경우(동일 타임스탬프)를 대비해 최종 tie-breaker(예: `batch.id` 또는 `batch_no`)를 명시하여 결정론적 선택 보장.

- 만료 재고: 보존 후 차감 제외 방식(결정)은 적절 — 감사 요구를 충족.

- 재고 부족(Shortage): 부분허용(B) 정책은 운영상 합리적.
	- 문제: 부분허용 시 최소비치 정책과의 상호작용(사용으로 최소비치 하회 허용 여부)이 미정의.
	- 수정 방향: 최소비치 위반 시 동작(차감 허용 vs 차단 vs 경고)을 decisions.md에 명시.

## 5) 트랜잭션과 동시성 위험
- 현재 설계(단일 트랜잭션 + `SELECT ... FOR UPDATE`)는 정합성 확보에 유리하나 다음 위험 존재:
	- 심각도: Major — **교착(Deadlock)**: 다수 배치에 걸쳐 차감할 때 트랜잭션이 서로 다른 순서로 행을 잠그면 교착이 발생 가능.
		- 수정 방향: 잠금 획득 순서를 결정론적으로 유지(예: `ORDER BY batches.id`)하거나, 가능한 경우 DB-레벨 `UPDATE ... RETURNING` 기반의 청구(atomic decrement) 패턴 사용. 교착 발생 시 재시도(backoff) 전략을 문서화.
	- 심각도: Major — **중복 idempotency 경쟁**: 동일 `requestId`를 가진 동시 요청이 race하여 두 트랜잭션이 모두 존재하지 않음을 보고 진행 후 중복 삽입 시도 가능.
		- 수정 방향: `usage_records(ship_id, request_id)` unique 제약을 활용하되, 중복키 예외를 잡아 기존 레코드를 조회하여 결과 재사용하도록 구현(예: INSERT ... ON CONFLICT DO NOTHING RETURNING / SELECT). 이 동작을 spec/decisions에 명시.
	- 심각도: Major — **음수 재고 방지**: 애플리케이션 레벨에서만 제어하면 경쟁상황에서 음수 가능.
		- 수정 방향: DB에서 `CHECK (quantity_available >= 0)` 추가 및 업데이트 시 조건절(`WHERE quantity_available >= :alloc`)로 원자적 보장.

## 6) 누락된 Edge Case (우선순위 높은 항목)
- 심각도: Major — `minimum_stock_policies` 시계열/중복 처리 규칙 미정.
- 심각도: Major — 만료재고만 존재 시의 명확한 응답 규칙(422 vs partial) 미결.
- 심각도: Major — 동시성 재시도/백오프·중복키 처리 로직(구체적 동작) 미기재.
- 심각도: Minor — `receivedAt` 기본값 및 백데이팅(과거 입고) 처리 규칙 보강 필요.
- 심각도: Minor — `batches.status` 값(`closed`) 전이 규칙 미정.
- 심각도: Minor — 동일 `expiry_date` 및 동일 `received_at` 동시성 tie-breaker 미정 (권고: `id` 사용).
- 심각도: Minor — API 응답 필드명 표준화(예: before/after 가독성), 페이징/필터링(조회 API) 상세 부족.

## 7) 과제 범위를 벗어난 설계 여부
- 결과: 특이한 범위 침범 없음. `decisions.md`의 이벤트 기반·배치 제안은 향후 개선 옵션으로 명시되어 있음(허용).

# S1 검토 결과 — 선박 의약품 재고 관리 (재검토)

검토 대상: `docs/task.md`, `spec.md`, `decisions.md`

검토 일시: 2026-08-27

요약: 이전 Major 이슈(정합성·정책 불일치·동시성)가 모두 문서상으로 해소되었고, 설계는 S1 요구사항을 만족합니다. 경미한 API 필드명 불일치 등 개선 권고는 남아있지만 실행을 가로막는 결함은 없습니다.

## 1) S1 필수 기능별 판정
- 약품 카탈로그 관리: PASS — `drugs`와 관련 API가 명확히 정의됨.
- 최소 비치 기준 관리: PASS — 단일 정책(UNIQUE(ship_id, drug_id))으로 설계되어 요구를 만족함.
- 재고 입고(로트 단위): PASS — `batches` 모델과 inbound API가 적절히 정의됨; `receivedAt` 기본값(서버 UTC) 명시됨.
- 약품 사용(출고) — FEFO: PASS — FEFO 알고리듬과 결정론적 정렬(expiry, received_at, id) 및 차감/이력 로직이 명시됨.
- 재고 현황 조회: PASS — 총합·로트별 상세·`isBelowMinimum` 플래그 등 조회 요건 충족.
- 사용 이력 조회: PASS — `usage_records`와 `usage_allocations` 구조 및 조회 API가 정의됨.

## 2) 이전 Major 지적 항목의 해결 여부 (독립 검토)
- `minimum_stock_policies`의 `effective_from` vs UNIQUE(ship_id, drug_id): **해결됨** — `effective_from` 제거, 단일 정책으로 정리됨.
- `batches.quantity_available` 음수 방지(DB 제약): **해결/반영됨** — spec에 DB CHECK 권고 및 원자적 업데이트 패턴 권장 문구 추가.
- 만료 재고만 존재 시 처리(422 vs partial): **해결됨** — spec·decisions 모두 `actualQuantity == 0`인 경우 422로 실패(단, requestId 제공 시 failed 레코드 기록)로 통일.
- FEFO tie-breaker(결정론성): **해결됨** — `expiry_date ASC, received_at ASC, id ASC`로 확정.
- 동시성·idempotency 경쟁: **부분 해결(문서화됨)** — spec와 decisions에 FOR UPDATE 기반 트랜잭션, 일관된 정렬·재시도 권고, `UNIQUE(ship_id, request_id)`와 INSERT-ON-CONFLICT 패턴 권고가 포함되어 있음. 실제 구현시 재시도/백오프 정책과 deadlock 관찰 로직이 필요하나 문서 수준에서는 요구를 만족함.
- `batches.status` 컬럼: **해결됨** — 컬럼 제거, `isExpired`/`isClosed`를 유도 상태로 처리하도록 정리됨.

결론: Major 항목들은 문서 수준에서 적절히 반영·정리되었으며 추가 구현 세부(재시도 정책·deadlock 모니터링)는 개발·운영 단계에서 적용할 수 있음.

## 3) 새로운 모순 또는 범위 밖 설계 여부
- 범위 초과 요소 없음: 비동기 이벤트·자동 폐기 등은 `decisions.md`에서 향후 옵션으로만 제시되어 있으며 본 스펙의 핵심 흐름에 포함되지 않음.
- 경미한 불일치(권고 사항): API 응답의 allocation 필드명과 DB 컬럼명 간 표현 차이가 남아 있음(`usage_allocations.before_batch_available` vs API의 `remainingBatchQuantity`). 이는 문서의 소규모 정리 항목(필드명 정렬)으로 해결 가능하며 기능적 충돌은 아님.

## 4) 권장 보완(우선순위가 낮은 개선)
- API ↔ DB 필드명 정렬: `before_batch_available`와 API의 `remainingBatchQuantity`를 통일하거나 둘 다 제공하도록 명확히 표현할 것.
- 동시성 테스트 케이스 확장: deadlock 재현·idempotency 경쟁 시나리오를 GWT 테스트 목록에 추가.
- DDL 예시(선택): `CHECK (quantity_available >= 0)`과 `UNIQUE(ship_id, request_id)`을 명확히 한 SQL DDL 스니펫을 spec에 추가하면 개발자가 구현하기 더 쉬움.

## 최종 판정
- PASS

판정 근거: 모든 Major 항목이 문서상에서 해결·통일되었으며, 남은 이슈는 API 필드명 표준화나 구현 시 보완할 재시도/백오프 정책과 같은 비핵심 개선사항에 불과합니다. 따라서 현재 `spec.md`와 `decisions.md`로 S1 요구사항을 만족한다고 판단합니다.

작성자: Critical Reviewer (재검토)
